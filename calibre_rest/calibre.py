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
    BOOK_ADDED_REGEX = re.compile(r"^Added book ids: ([0-9,]+)")
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
        # time. More than one concurrent requests will result in calibre complaining.
        self.mutex = threading.Lock()

    def check(self) -> None:
        """Check wrapper's executable and library exists. This is decoupled from
        the class' initialization to allow for easier testing.

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
        FileNotFoundError: If the command's executable is invalid.
        CalibreRuntimeError: If the command returns a non-zero exit code.
        CalibreConcurrencyError: If Calibre detects another Calibre program to
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
        """Get calibredb version."""

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
        # results.
        if len(b) == 1:
            return Book(**b[0])

    # TODO sort and filter
    def get_books(self, limit: int = 10) -> list[Book]:
        """Get list of books from calibre database.

        Args:
        limit (int): Limit on total number of results

        Returns:
        list[Book]: List of books
        """
        if limit <= 0:
            raise ValueError(f"limit {limit} not allowed")

        cmd = (
            f"{self.cdb_with_lib} list "
            f"--for-machine --fields=all "
            f"--limit={str(limit)}"
        )
        out, _ = self._run(cmd)

        books = json.loads(out)
        res = []
        if len(books):
            for b in books:
                res.append(Book(**b))
        return res

    def add_one(
        self, book_path: str, book: Book = None, automerge: str = "ignore"
    ) -> int:
        """Add a single book to calibre database.

        Args:
        book_path (str): Filepath to book on the filesystem. Filenames cannot
        begin with a hyphen.
        book (Book): Optional book instance
        automerge (str): Accepts one of the following:
            ignore: Duplicate formats are discarded (default)
            overwrite: Duplicate formats are overwritten with newly added files
            new_record: Duplicate formats are placed into new book record

        Returns:
        int: Book ID of added book
        """
        if not path.exists(book_path):
            raise FileNotFoundError(f"Failed to find book at {book_path}")

        cmd = f"{self.cdb_with_lib} add {book_path}"

        if automerge in self.AUTOMERGE_VALID_VALUES:
            cmd += f" --automerge={automerge}"
        else:
            logging.warning(
                f'automerge value "{automerge}" not supported. '
                f'Using "--automerge ignore".'
            )
            cmd += " --automerge=ignore"

        return self._run_add(cmd, book)

    def add_one_empty(self, book: Book = None) -> int:
        """Add one empty book (with no formats) to the calibredb database.

        Args:
        book (Book): Optional book instance

        Returns:
        int: Book ID of added book.
        """
        cmd = f"{self.cdb_with_lib} add --empty"
        return self._run_add(cmd, book)

    def _run_add(self, cmd: str, book: Book = None) -> int:
        """Run calibredb add subcommand for all add_* methods. This parses the
        result of the subcommand and determines the correct type of response to
        give.

         When an existing book is added, we can modify the behaviour with the
         "automerge" flag:
            - "automerge=ignore": Ignore the duplicate. This will not add any
              new files and only the original remains. If the new book is given
              different metadata through the any of the fields flags, a new
              entry will be created, similar to "automerge=new_record".
            - "automerge=overwrite": Overwrite the existing with the duplicate.
              If the metadata is exactly the same, this will overwrite the
              existing with the new file, resulting in only a single file. If
              the new book is given different metadata through the any of the
              fields flags, a new entry will be created, similar to
              "automerge=new_record".
            - "automerge=new_record" Create a new record entirely. This will
              resulting in two different entries, regardless of their metadata
              are similar.

        Args:
        cmd (str): Command string to run
        book (Book): Optional book instance

        Returns:
        int: Book ID of added book.

        Raises:
        ExistingItemError: If books to be added already exists and
        automerge="ignore".
        Exception: If books added that were not ignored or merged, due to
        unforeseen error.
        """
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
            logging.info("Books merged")
            book_ids_str = book_merged_match.group(1)
            book_ids = book_ids_str.split(", ")

            # return merged book
            if len(book_ids) == 1:
                return book_ids[0]

        book_added_match = re.search(self.BOOK_ADDED_REGEX, out)
        if book_added_match is None:
            logging.warning(f'No books added after running "{cmd}"')
            raise Exception(
                "No books were added because something went wrong. Please look at logs to troubleshoot."
            )

        book_ids_str = book_added_match.group(1)
        book_ids = book_ids_str.split(",")

        # should add only one book
        if len(book_ids) == 1:
            return book_ids[0]

    def _handle_add_flags(self, cmd: str, book: Book = None):
        """Build flags for add_* methods.

        Args:
        cmd (string): Command string to append flags to
        book (Book): Optional book instance. All author values will be joined
        with the " & " separator. All other list values will be joined with the
        "," separator. All identifiers pairs will be turned into the form
        "abc:123,foo:bar".

        Returns:
        string: Full command string with flags
        """
        if book is None:
            return cmd

        for flag in self.ADD_FLAGS.keys():
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
        Fails silently  with no output if given IDs do not exist.

        Args:
        ids (list[int]): List of book IDs to remove
        permanent (bool): Do not use the builtin trash can
        """
        if not all(i >= 0 for i in ids):
            raise ValueError(f"ids {ids} not allowed")

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
    ) -> str:
        """Set XML metadata of book with OPF file or kwargs.

        Args:
        id (int): Book ID
        book (Book): Optional Book instance
        metadata_path (str): Path to OPF metadata file
        """
        validate_id(id)

        cmd = f"{self.cdb_with_lib} set_metadata {id}"

        if metadata_path:
            if not path.exists(metadata_path):
                raise FileNotFoundError(f"Metadata file {metadata_path} does not exist")
            cmd += f" {metadata_path}"

        elif book is not None:
            self._handle_update_flags(cmd, book)

        out, _ = self._run(cmd)
        return out

    def _handle_update_flags(self, cmd: str, book: Book = None) -> str:
        """Build flags for set_metadata

        Args:
        cmd (string): Command string to append flags to
        book (Book): Optional book instance. All author values will be joined
        with the " & " separator. All other list values will be joined with the
        "," separator. All identifiers pairs will be turned into the form
        "abc:123,foo:bar".

        Returns:
        string: Full command string with flags
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

    def export(self, ids: list[int]) -> str:
        """Export books from calibre database to filesystem

        ids (list[int]): List of book IDs
        """
        pass


def join_list(lst: list, sep: str) -> str:
    lst = list(map(str.strip, lst))
    return sep.join(lst)


def quote(s: str) -> str:
    s = s.strip()
    return shlex.quote(s) if " " in s else s


def validate_id(id: int) -> None:
    if id <= 0:
        raise ValueError(f"Value {id} cannot be <= 0")
