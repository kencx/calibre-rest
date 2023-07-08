import json
import logging
import re
import shlex
import shutil
import subprocess
import threading
from os import path

from calibre_rest.errors import (
    CalibreConcurrencyError,
    CalibreRuntimeError,
    ExistingItemError,
)
from calibre_rest.models import Book


class CalibreWrapper:
    # Flags for calibredb add subcommand. The keys represent the attributes
    # while the values represent their flags
    ADD_FLAGS = {
        "authors": "authors",
        "cover": "cover",
        "identifiers": "identifier",
        "isbn": "isbn",
        "languages": "languages",
        "series": "series",
        "series_index": "series-index",
        "tags": "tags",
        "title": "title",
    }
    UPDATE_FLAGS = [
        "author_sort",
        "authors",
        "comments",
        "id",
        "identifiers",
        "languages",
        "pubdate",
        "publisher",
        "rating",
        "series",
        "series_index",
        "size",
        "tags",
        "timestamp",
        "title",
    ]
    SORT_BY_KEYS = [
        "author_sort",
        "authors",
        "comments",
        "cover",
        "formats",
        "id",
        "identifiers",
        "isbn",
        "languages",
        "last_modified",
        "pubdate",
        "publisher",
        "rating",
        "series",
        "series_index",
        "size",
        "tags",
        "template",
        "timestamp",
        "title",
        "uuid",
    ]
    ALLOWED_FILE_EXTENSIONS = (
        ".azw",
        ".azw3",
        ".azw4",
        ".cbz",
        ".cbr",
        ".cb7",
        ".cbc",
        ".chm",
        ".djvu",
        ".docx",
        ".epub",
        ".fb2",
        ".fbz",
        ".html",
        ".htmlz",
        ".lit",
        ".lrf",
        ".mobi",
        ".odt",
        ".pdf",
        ".prc",
        ".pdb",
        ".pml",
        ".rb",
        ".rtf",
        ".snb",
        ".tcr",
        ".txt",
        ".txtz",
    )
    AUTOMERGE_VALID_VALUES = ["overwrite", "new_record", "ignore"]

    CONCURRENCY_ERR_REGEX = re.compile(r"^Another calibre program.*is running.")
    CALIBRE_VERSION_REGEX = re.compile(r"calibre ([\d.]+)")
    BOOK_ADDED_REGEX = re.compile(r"^Added book ids: ([0-9, ]+)")
    BOOK_MERGED_REGEX = re.compile(r"^Merged book ids: ([0-9, ]+)")
    BOOK_IGNORED_REGEX = re.compile(
        r"^The following books were not added as they already exist.*"
    )

    def __init__(
        self,
        calibredb: str,
        lib: str,
        username: str = "",
        password: str = "",
        logger: logging.Logger = None,
    ) -> None:
        """Initialize the calibredb command-line wrapper.

        To verify the executable and library paths, use check().

        Args:
            calibredb (str): Path to calibredb executable.
            lib (str): Path to calibre library on the filesystem.
            username (str): calibre server username
            password (str): calibre server password
            logger (logging.Logger): Custom logger object
        """
        if logger is None:
            logger = logging.getLogger(__name__)
        self.logger = logger

        self.cdb = path.abspath(calibredb)
        self.lib = path.abspath(lib)
        self.cdb_with_lib = f"{self.cdb} --with-library {self.lib}"

        if username != "" and password != "":
            self.cdb_with_lib += f" --username {username} --password {password}"

        # It is safer to limit calibredb to running one operation at any given
        # time. Any concurrent requests will result in calibre complaining.
        self.mutex = threading.Lock()

    def check(self) -> None:
        """Check that wrapper's executable and library exists.

        This is decoupled from the class' initialization to allow for easier
        testing.

        Raises:
            FileNotFoundError: If the calibredb executable is not valid or
                metadata.db is not found in the given library path
        """
        if not shutil.which(self.cdb):
            raise FileNotFoundError(f"{self.cdb} is not a valid executable")

        if not path.exists(path.join(self.lib, "metadata.db")):
            raise FileNotFoundError(
                f"Failed to find Calibre database file {path.join(self.lib, 'metadata.db')}"
            )

    def _run(self, cmd: str) -> (str, str):
        """Execute calibredb on the command line.

        Any stderr that is returned with a zero exit code will also be logged as
        a warning.

        Args:
            cmd (str): Full command string to execute. This string will be split
                appropriately with shlex.split.

        Returns:
            str: Stdout of command
            str: Stderr of command

        Raises:
            FileNotFoundError: The command's executable is invalid.
            CalibreRuntimeError: The command returns a non-zero exit code.
            CalibreConcurrencyError: Calibre detects another Calibre program to
                be running.
        """
        self.logger.debug(f'Running "{cmd}"')
        try:
            self.mutex.acquire()

            process = subprocess.run(
                shlex.split(cmd),
                capture_output=True,
                check=True,
                text=True,
                encoding="utf-8",
                env=None,
                timeout=None,
            )
        except FileNotFoundError as err:
            raise FileNotFoundError(f"Executable could not be found.\n\n{err}") from err

        except subprocess.CalledProcessError as e:
            match = re.search(self.CONCURRENCY_ERR_REGEX, e.stderr)
            if match is not None:
                raise CalibreConcurrencyError(e.cmd, e.returncode)
            else:
                raise CalibreRuntimeError(e.cmd, e.returncode, e.stdout, e.stderr)

        finally:
            self.mutex.release()

        if process.stderr:
            self.logger.warning(process.stderr)

        return process.stdout, process.stderr

    def version(self) -> str:
        """Get calibredb version.

        Returns:
            str: calibredb version
        """

        cmd = f"{self.cdb} --version"
        out, _ = self._run(cmd)

        match = re.search(self.CALIBRE_VERSION_REGEX, out)
        if match is not None:
            return match.group(1)
        else:
            self.logger.error("failed to parse calibredb version")

    def get_book(self, id: int) -> Book:
        """Get book from calibre database.

        Args:
            id (int): Book ID

        Returns:
            Book: Book object
        """
        validate_id(id)

        cmd = (
            f"{self.cdb_with_lib} list "
            f"--for-machine --fields=all "
            f"--search=id:{id} --limit=1"
        )
        out, _ = self._run(cmd)

        # object_hook arg cannot be used as it results in a nested instance
        # in the identifiers dict field
        try:
            b = json.loads(out)
        except json.JSONDecodeError as exc:
            self.logger.error(f"Error decoding JSON: {exc}\n\n{out}")
            return

        # "calibredb list" returns a list, regardless of the limit or number of
        # results. This command should return only 1 element, but we check just
        # in case.
        if len(b) == 1:
            return Book(**b[0])

    def get_books(
        self,
        sort: list[str] = None,
        search: list[str] = None,
        all: bool = False,
    ) -> list[Book]:
        """Get a list of (sorted and filtered) books from the calibre database.

        A maximum limit of 5000 is set on the total number of results. This limit
        was introduced as calibredb does not natively support offset or cursor
        pagination for its results. If a user should require more results than
        the maximum limit, they can opt to ignore the limit by passing the
        all=True argument or narrow their search with appropriate filters.

         Args:
             sort (list[str]): List of sort keys to sort results by
             search (str): List of search terms
             all (bool): Return all results of filtered query.

         Returns:
             list[Book]: List of books
        """
        max_limit = "all"
        if not all:
            max_limit = "5000"

        cmd = (
            f"{self.cdb_with_lib} list "
            f"--for-machine --fields=all "
            f"--limit={max_limit}"
        )

        cmd = self._handle_sort(cmd, sort)
        cmd = self._handle_search(cmd, search)

        out, _ = self._run(cmd)

        books = json.loads(out)
        if not len(books):
            return []

        return [Book(**b) for b in books]

    def _handle_sort(self, cmd: str, sort: list[str]) -> str:
        """Handle sort.

        Defaults to ascending sort, unless a `-` is prepended to ANY sort keys.
        Sort keys that are not supported are dropped with a warning.

        Args:
            cmd (str): Command string to run
            sort (list[str]): List of sort keys

        Returns:
            str: Command string with sort flags
        """
        if sort is None or not len(sort):
            # default to ascending
            cmd += " --ascending"
            return cmd

        # filter for unsupported sort keys
        safe_sort = [x for x in sort if x.removeprefix("-") in self.SORT_BY_KEYS]
        unsafe_sort = [x for x in sort if x not in safe_sort]
        if len(unsafe_sort):
            self.logger.warning(
                f"The following sort keys are not supported and will be ignored: "
                f"\"{', '.join(unsafe_sort)}\"."
            )

        descending = any(map(lambda x: x.startswith("-"), safe_sort))
        if not descending:
            cmd += " --ascending"

        if len(safe_sort):
            safe_sort = [x.removeprefix("-") for x in safe_sort]
            safe_sort = ",".join(safe_sort)
            cmd += f" --sort-by={safe_sort}"

        return cmd

    def _handle_search(self, cmd: str, search: list[str]) -> str:
        if search is None or not len(search):
            return cmd

        cmd += f' --search "{" ".join(search)}"'
        return cmd

    def add_multiple(
        self, book_paths: list[str], book: Book = None, automerge: str = "ignore"
    ) -> list[int]:
        """Add multiple books to the calibredb database.

         Args:
             book_paths (list[str]): List of book file paths to upload. A list of
                 supported file extensions is given by self.ALLOWED_FILE_EXTENSIONS.
                 Filenames cannot begin with a hyphen.
             book (Book): Optional book instance with additional metadata.
             automerge (str): Modifies the behaviour of calibredb when a book is
             found to already exist in the library. Accepts one of the following:
                 - ignore (default): Ignore the duplicate and return a 409 Conflict
                 error. This will not add any new records or files.
                 - overwrite: Overwrite the existing file with the new file, leaving
                 only a single record.
                 - new_record Create a new record entirely. This will result in two
                 different records.

             If the same file is uploaded with different JSON metadata, a new
             record will be created, regardless of the value given to
             `automerge`.

             If the same file exists across multiple different entries in the
             same library, as a result of using `automerge=new_record`, and we
             add another instance of the same file with `automerge=overwrite`,
             the new file would overwrite ALL existing entries with the same file
             in the library.

        Returns:
             list[int]: List of IDs of added/merged book(s).
        """
        if len(book_paths) == 1:
            return self.add_one(book_paths[0], book, automerge)

        if any(map(lambda x: not path.exists(x), book_paths)):
            raise FileNotFoundError(f"Failed to find book at {book_paths}")

        cmd = f"{self.cdb_with_lib} add {' '.join(book_paths)}"
        return self._run_add(cmd, book, automerge)

    def add_one(
        self, book_path: str, book: Book = None, automerge: str = "ignore"
    ) -> list[int]:
        """Add a single book to calibre database.

        Args:
            book_path (str): Book file path to upload. A list of supported file
                extensions is given by self.ALLOWED_FILE_EXTENSIONS. Filenames
                cannot begin with a hyphen.
            book (Book): Optional book instance with additional metadata.
            automerge (str): Modifies the behaviour of calibredb when a book is
            found to already exist in the library. Accepts one of the following:
                - ignore (default): Ignore the duplicate and return a 409 Conflict
                error. This will not add any new records or files.
                - overwrite: Overwrite the existing file with the new file, leaving
                only a single record.
                - new_record Create a new record entirely. This will result in two
                different records.

            If the same file is uploaded with different JSON metadata, a new
            record will be created, regardless of the value given to
            `automerge`.

            If the same file exists across multiple different entries in the
            same library, as a result of using `automerge=new_record`, and we
            add another instance of the same file with `automerge=overwrite`,
            the new file would overwrite ALL existing entries with the same file
            in the library.

        Returns:
            list[int]: List of IDs of added/merged book(s). While this function
                serves to add only one book, there are instances when multiple book
                IDs can be returned when the added book is merged with multiple
                existing books.
        """
        if not path.exists(book_path):
            raise FileNotFoundError(f"Failed to find book at {book_path}")

        cmd = f"{self.cdb_with_lib} add {book_path}"

        return self._run_add(cmd, book, automerge)

    def add_one_empty(self, book: Book = None, automerge: str = "ignore") -> list[int]:
        """Add one empty book (with no formats) to the calibredb database.

        Args:
            book (Book): Optional book instance.
            automerge (str): Defaults to "ignore".

        Returns:
            list[int]: List of IDs of added/merged book(s). While this function
                serves to add only one book, there are instances when multiple book
                IDs can be returned when the added book is merged with multiple
                existing books.
        """
        cmd = f"{self.cdb_with_lib} add --empty"
        return self._run_add(cmd, book, automerge)

    def _run_add(
        self, cmd: str, book: Book = None, automerge: str = "ignore"
    ) -> list[int]:
        """Run calibredb add subcommand for all add_* methods.

        This parses the result of the subcommand and determines the correct type
        of response to return.

        Args:
            cmd (str): Command string to run.
            book (Book): Optional book instance with metadata.
            automerge (str): Defaults to "ignore".

        Returns:
            list[int]: List of IDs of added/merged books.

        Raises:
            ExistingItemError: Book to be added already exists.
            Exception: Unforeseen error when adding book.
        """
        if automerge in self.AUTOMERGE_VALID_VALUES:
            cmd += f" --automerge={automerge}"
        else:
            logging.warning(
                f'automerge value "{automerge}" not supported. '
                f'Using "--automerge ignore".'
            )
            cmd += " --automerge=ignore"

        cmd = self._handle_add_flags(cmd, book)
        out, stderr = self._run(cmd)

        book_ignored_match = re.search(self.BOOK_IGNORED_REGEX, stderr)
        if book_ignored_match is not None:
            out = out.strip("\n ")
            logging.info(f"Books {out} already exist. Ignoring...")
            raise ExistingItemError(
                f"Book {out} already exists. Include automerge=overwrite to overwrite."
            )

        book_merged_match = re.search(self.BOOK_MERGED_REGEX, out)
        if book_merged_match is not None:
            book_ids_str = book_merged_match.group(1)
            book_ids = book_ids_str.split(", ")

            if len(book_ids) < 1:
                self.logger.error("No books were merged, something went wrong...")
                self.logger.error(
                    f"COMMAND: {cmd}\n\nSTDOUT:\n{out}\nSTDERR:\n{stderr}"
                )
                raise Exception("No books were merged, something went wrong...")
            else:
                return book_ids

        book_added_match = re.search(self.BOOK_ADDED_REGEX, out)
        if book_added_match is not None:
            book_ids_str = book_added_match.group(1)
            book_ids = book_ids_str.split(", ")

            if len(book_ids) < 1:
                self.logger.error("No books were added, something went wrong...")
                self.logger.error(
                    f"COMMAND: {cmd}\n\nSTDOUT:\n{out}\nSTDERR:\n{stderr}"
                )
                raise Exception("No books were added, something went wrong...")
            else:
                return book_ids

        self.logger.error(
            "Could not parse calibredb add output, something went wrong..."
        )
        self.logger.error(f"COMMAND: {cmd}\n\nSTDOUT:\n{out}\nSTDERR:\n{stderr}")
        raise Exception("Could not parse calibredb add output, something went wrong...")

    def _handle_add_flags(self, cmd: str, book: Book = None) -> str:
        """Build flags for add_* methods.

        Args:
            cmd (string): Original command string.
            book (Book): Optional book instance. All author values will be joined
                with the " & " separator. All other list values will be joined with the
                "," separator. All identifiers pairs will be turned into the form
                "abc:123,foo:bar".

        Returns:
            string: Full command string with flags.
        """
        if book is None:
            return cmd

        for flag in self.ADD_FLAGS:
            value = getattr(book, flag)
            if value:
                flag_name = self.ADD_FLAGS[flag]

                if flag == "identifiers":
                    for k, v in value.items():
                        # ensure valid form of ABC:XXX
                        identifier = f"{k}:{v}"
                        cmd += f" --{flag_name} {quote(identifier)}"
                    break

                elif isinstance(value, list):
                    if flag == "authors":
                        value = join_list(value, " & ")
                    else:
                        value = join_list(value, ",")

                cmd += f" --{flag_name} {quote(str(value))}"
        return cmd

    def remove(self, ids: list[int], permanent: bool = False) -> str:
        """Remove book from calibre database.

        Fails silently with no output if given IDs do not exist.

        Args:
            ids (list[int]): List of book IDs to remove
            permanent (bool): Delete permanently, i.e. do not use the builtin
                trash can

        Returns:
            str: Stdout of command, which is usually empty.
        """
        if not all(i >= 0 for i in ids):
            raise ValueError(f"{ids=} not allowed")

        cmd = f'{self.cdb_with_lib} remove {",".join(map(str, ids))}'
        if permanent:
            cmd += " --permanent"

        out, _ = self._run(cmd)
        return out

    def add_format(
        self, id: int, replace: bool = False, data_file: bool = False
    ) -> str:
        """Add a book format to an existing book in the calibre database.

        Args:
            id (int): Book ID
            replace (bool): Replace file if format already exists in book
            data_file (bool):
        """
        validate_id(id)

        cmd = f"{self.cdb_with_lib} add_format {id}"
        if replace:
            cmd += " --dont-replace"
        if data_file:
            cmd += " --as-extra-data-file"

        out, _ = self._run(cmd)
        return out

    def remove_format(self, id: int, format: str) -> str:
        """Remove book format from an existing book with given ID.

        Args:
            id (int): Book ID
            format (str): File extension like EPUB, TXT etc.
        """
        validate_id(id)

        # TODO check format
        cmd = f"{self.cdb_with_lib} remove_format {id} {format}"
        out, _ = self._run(cmd)
        return out

    def show_metadata(self, id: int) -> str:
        """Returns XML metadata of given in calibre database.

        Args:
            id (int): Book ID
        """
        validate_id(id)

        cmd = f"{self.cdb_with_lib} show_metadata --as-opf {id}"
        out, _ = self._run(cmd)
        return out

    def set_metadata(
        self, id: int, book: Book = None, metadata_path: str = None
    ) -> int:
        """Set XML metadata of book with OPF file or kwargs.

        Args:
            id (int): Book ID
            book (Book): Optional Book instance
            metadata_path (str): Path to OPF metadata file

        Returns:
            int: ID of updated book. If -1, book does not exist.

        Raises:
            ValueError: No data given to update book.
        """
        validate_id(id)

        # check if book exists
        if self.get_book(id) is None:
            return -1

        cmd = f"{self.cdb_with_lib} set_metadata {id}"

        if metadata_path:
            if not path.exists(metadata_path):
                raise FileNotFoundError(f"Metadata file {metadata_path} does not exist")
            cmd += f" {metadata_path}"

        elif book is not None:
            cmd = self._handle_update_flags(cmd, book)
        else:
            raise ValueError("No metadata given for update")

        # Difficult to check for error. Best way is for user to check entry.
        self._run(cmd)
        return id

    def _handle_update_flags(self, cmd: str, book: Book = None) -> str:
        """Build flags for set_metadata.

        Args:
            cmd (string): Original command string.
            book (Book): Optional book instance. All author values will be joined
                with the " & " separator. All other list values will be joined with the
                "," separator. All identifiers pairs will be turned into the form
                "abc:123,foo:bar".

        Returns:
            str: Full command string with flags
        """
        if book is None:
            return cmd

        for field in self.UPDATE_FLAGS:
            value = getattr(book, field)

            if value:
                if field == "identifiers":
                    # format: --field identifiers:XXX:ABC,foo:bar
                    strs = []
                    for k, v in value.items():
                        identifier_str = f"{k}:{v}"
                        strs.append(identifier_str)
                    cmd += f" --field {field}:{quote(join_list(strs, ','))}"
                    break

                elif isinstance(value, list):
                    if field == "authors":
                        # format: --field "authors:Foo Bar & Bar Baz"
                        value = join_list(value, " & ")
                    else:
                        value = join_list(value, ",")

                value = quote(f"{field}:{value}")
                cmd += f" --field {value}"
        return cmd

    def export(
        self, ids: list[int], exports_dir: str = "/exports", formats: list[str] = None
    ) -> None:
        """Export books from calibre database to filesystem.

        Args:
            ids (list[int]): List of book IDs
            exports_dir (str): Directory to export all files to
            formats (list[str]): List of formats to export for given id

        Raises:
            KeyError: when any id does not exist
        """
        for id in ids:
            validate_id(id)

        cmd = f"{self.cdb_with_lib} export --dont-write-opf --dont-save-cover --single-dir"

        if exports_dir != "":
            cmd += f" --to-dir={exports_dir}"

        # NOTE: if format does not exist, there is no error
        if formats is not None:
            cmd += f" --formats {','.join(formats)}"

        cmd += f' {",".join([str(i) for i in ids])}'

        try:
            self._run(cmd)
        except CalibreRuntimeError as e:
            match = re.search(r"No book with id .* present", e.stderr)
            if match is not None:
                raise KeyError(match.group(0)) from e
            else:
                raise CalibreRuntimeError from e


def join_list(lst: list, sep: str) -> str:
    lst = list(map(str.strip, lst))
    return sep.join(lst)


def quote(s: str) -> str:
    s = s.strip()
    return shlex.quote(s) if " " in s else s


def validate_id(id: int) -> None:
    if id <= 0:
        raise ValueError(f"Value {id=} cannot be <= 0")
