import json
import logging
import re
import shlex
import shutil
import subprocess
from os import path
from typing import Any

from calibre_rest.errors import CalibreRuntimeError, ValidationError
from calibre_rest.models import Book


class CalibreWrapper:
    ADD_FLAGS = [
        "authors",
        "cover",
        "identifier",
        "isbn",
        "languages",
        "series",
        "series-index",
        "tags",
        "title",
    ]
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
        "series-index",
        "size",
        "sort",
        "tags",
        "timestamp",
        "title",
    ]

    def __init__(self, calibredb: str, lib: str, logger=None) -> None:
        """Initialize the calibredb command-line wrapper.

        Args:
        calibredb (str): Path to calibredb executable.
        lib (str): Path to calibre library on the filesystem.
        logger (logging.Logger): Custom logger object

        Raises:
        FileNotFoundError: If the calibredb executable is not valid
        FileNotFoundError: If the calibre metadata.db is not found in the given
            library path
        """

        if logger is None:
            logger = logging.getLogger(__name__)
        self.logger = logger

        executable = path.abspath(calibredb)
        if not shutil.which(executable):
            raise FileNotFoundError(f"{executable} is not a valid executable")

        if not path.exists(path.join(lib, "metadata.db")):
            raise FileNotFoundError(
                f"Failed to find Calibre database file {path.join(lib, 'metadata.db')}"
            )

        self.cdb = executable
        self.lib = lib
        self.cdb_with_lib = f"{executable} --with-library {lib}"

    def _run(self, cmd: str) -> str:
        """Execute calibredb on the command line.

        Any stderr that is returned with a zero exit code will be logged as
        warnings.

        Args:
        cmd (str): Full command string to execute. This string will be split
            appropriately with shlex.split.

        Returns:
        str: Output of command

        Raises:
        FileNotFoundError: If the command's executable is invalid.
        CalibreRuntimeError: If the command returns a non-zero exit code.
        """

        self.logger.debug(f'Running "{cmd}"')
        try:
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
            raise CalibreRuntimeError(e.cmd, e.returncode, e.stdout, e.stderr)

        if process.stderr:
            self.logger.warning(process.stderr)

        return process.stdout

    def version(self) -> str:
        """Get calibredb version."""

        cmd = f"{self.cdb} --version"
        out = self._run(cmd)

        match = re.search(re.compile(r"calibre ([\d.]+)"), out)
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
        out = self._run(cmd)

        # object_hook arg cannot be used as it results in a nested instance
        # in the identifiers dict field
        b = json.loads(out)

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
            raise ValidationError(f"limit {limit} not allowed")

        cmd = (
            f"{self.cdb_with_lib} list "
            f"--for-machine --fields=all "
            f"--limit={str(limit)}"
        )
        out = self._run(cmd)

        books = json.loads(out)
        res = []
        if len(books):
            for b in books:
                res.append(Book(**b))
        return res

    # TODO check book_path exists and is valid file
    def add(self, book_path: str, **kwargs: Any) -> list[int]:
        """Add a single book to calibre database.

        Args:
        book_path (str): Filepath to book on the filesystem.
        kwargs (Any):
            authors: Authors separated by &. For example: "John Doe & Peter Brown"
            identifiers: Prefixed with corresponding specifier. For example:
                "asin:XXXX, isbn:XXXX"
            isbn: str
            languages: Comma separated strings
            series: str
            series_index: str
            tags: Comma separated strings
            title: str

        Returns:
        int: Book ID of added book
        """

        if not path.exists(book_path):
            raise FileNotFoundError(f"Failed to find book at {book_path}")

        cmd = f"{self.cdb_with_lib} add {book_path}"
        cmd = self._handle_add_flags(cmd, kwargs)
        out = self._run(cmd)

        # TODO handle duplicates
        # WARNING: The following books were not added as they already
        # exist in the database (see --duplicates option or --automerge option):
        #   [book]

        book_ids_str = re.search(r"^Added book ids: ([0-9,]+)", out).group(1)
        book_ids = book_ids_str.split(",")

        # should add only one book (for now)
        if len(book_ids) == 1:
            return book_ids[0]

    def add_empty(self, **kwargs: Any) -> list[int]:
        """Add an empty book (with no formats) to the calibredb database

        Args:
        kwargs (Any): Similar to add()

        Returns:
        int: Book ID of added book.
        """
        cmd = f"{self.cdb_with_lib} add --empty"

        cmd = self._handle_add_flags(cmd, kwargs)
        out = self._run(cmd)

        ids_str = re.search(r"^Added book ids: ([0-9,]+)", out).group(1)
        ids = ids_str.split(",")
        if len(ids):
            return [int(i) for i in ids]
        else:
            return []

    # TODO handle when passing multiple of the same flag
    def _handle_add_flags(self, cmd: str, kwargs: Any):
        for flag in self.ADD_FLAGS:
            value = kwargs.get(flag)

            if value:
                if flag == "identifier" and type(value) is str:
                    identifiers = value.split(",")

                    # ensure valid identifier of form ABC:XXX
                    for i in identifiers:
                        if len(i.split(":")) == 2:
                            cmd += f" --{flag} {quote(i)}"
                else:
                    cmd += f" --{flag} {quote(str(value))}"

        # TODO handle unsupported flags
        # self.logger.warning(f"Unsupported flags {','.join(sorted(kwargs))}")
        return cmd

    def remove(self, ids: list[int], permanent: bool = False) -> str:
        """Remove book from calibre database.
        Fails silently  with no output if given IDs do not exist.

        Args:
        ids (list[int]): List of book IDs to remove
        permanent (bool): Do not use the builtin trash can
        """

        if not all(i >= 0 for i in ids):
            raise ValidationError(f"ids {ids} not allowed")

        cmd = f'{self.cdb_with_lib} remove {",".join(map(str, ids))}'
        if permanent:
            cmd += " --permanent"

        return self._run(cmd)

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

        return self._run(cmd)

    def remove_format(self, id: int, format: str) -> str:
        """Remove book format from an existing book with given ID.

        Args:
        id (int): Book ID
        format (str): File extension like EPUB, TXT etc.
        """

        validate_id(id)

        # TODO check format
        cmd = f"{self.cdb_with_lib} remove_format {id} {format}"
        return self._run(cmd)

    def show_metadata(self, id: int) -> str:
        """Returns XML metadata of given in calibre database.

        Args:
        id (int): Book ID
        """
        validate_id(id)

        cmd = f"{self.cdb_with_lib} show_metadata --as-opf {id}"
        return self._run(cmd)

    def set_metadata(self, id: int, metadata_path: str = None, **kwargs) -> str:
        """Set XML metadata of book with OPF file or kwargs.

        Args:
        id (int): Book ID
        metadata_path (str): Path to OPF metadata file
        kwargs (Any):
            author_sort:
            authors:
            comments:
            id:
            identifiers:
            languages:
            pubdate:
            publisher:
            rating:
            series:
            series-index:
            size:
            sort:
            tags:
            timestamp:
            title:
        """

        validate_id(id)

        cmd = f"{self.cdb_with_lib} set_metadata {id}"

        if metadata_path:
            if not path.exists(metadata_path):
                raise FileNotFoundError(f"Metadata file {metadata_path} does not exist")
            cmd += f" {metadata_path}"

        else:
            for field in self.UPDATE_FLAGS:
                value = kwargs.get(field)

                if value:
                    if field == "identifiers" and type(value) is str:
                        identifiers = value.split(",")
                        identifier_str = ""

                        # build string of form XXX:ABC,FOO:BAR
                        for i in identifiers:
                            if len(i.split(":")) == 2:
                                identifier_str += f"{quote(i)},"
                        cmd += f" --field {field}:{identifier_str.rstrip(',')}"

                    else:
                        cmd += f" --field {field}:{quote(str(value))}"

        return self._run(cmd)

    def export(self, ids: list[int]) -> str:
        """Export books from calibre database to filesystem

        ids (list[int]): List of book IDs
        """
        pass


def quote(s: str) -> str:
    s = s.strip()
    return shlex.quote(s) if " " in s else s


def validate_id(id: int) -> None:
    if id <= 0:
        raise ValidationError(f"{id} cannot be <= 0")
