import json
import logging
import re
import shlex
import shutil
import subprocess
import sys
from os import path
from typing import Any

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

    def __init__(self, calibredb: str, lib: str):
        executable = path.abspath(calibredb)

        if not shutil.which(executable):
            error(f"{executable} is not a valid executable")

        if not path.isdir(lib) and not path.exists(lib):
            error(f"{lib} is not a valid directory")

        if not path.exists(path.join(lib, "metadata.db")):
            error(
                f"Failed to find Calibre database file {path.join(lib, 'metadata.db')}"
            )

        self.cdb = executable
        self.lib = lib
        self.cdb_with_lib = f"{executable} --with-library {lib}"

    @staticmethod
    def _run(cmd: str) -> (str, str):
        logging.debug(f'Running "{cmd}"')
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
            error(f"Executable could not be found\n{err}")
        except subprocess.CalledProcessError as err:
            error(f"Returned exit code {err.returncode}\n{err}")
        except TimeoutError as err:
            error(f"Process timed out\n{err}")

        return process.stdout, process.stderr

    def version(self):
        cmd = f"{self.cdb} --version"
        return self._run(cmd)

    # Get book with given id
    def get_book(self, id: int):
        if id <= 0:
            error(f"id {id} not allowed")

        cmd = (
            f"{self.cdb_with_lib} list "
            f"--for-machine --fields=all "
            f"--search=id:{id} --limit=1"
        )

        out, err = self._run(cmd)

        if err:
            error(err)

        if out:
            # object_hook cannot be used as it will result in a nested instance
            # in the identifiers dict field
            json_book = json.loads(out)
            if len(json_book) == 1:
                return Book(**json_book[0])

    # List all books
    # TODO sort and filter
    def get_books(self, limit: int):
        if limit <= 0:
            error(f"limit {limit} not allowed")

        cmd = f"{self.cdb_with_lib} list --for-machine --fields=all"

        if limit:
            cmd += f" --limit={str(limit)}"

        return self._run(cmd)

    # Add book with given file path
    # TODO check book_path exists and is valid file
    def add(self, book_path: str, **kwargs: Any) -> list[int]:
        """
        book_path: File path to book
        **kwargs:
            authors: Authors separated by &. For example: "John Doe & Peter Brown"
            identifiers: Prefixed with corresponding specifier. For example:
                "asin:XXXX, isbn:XXXX"
            isbn: str
            languages: Comma separated strings
            series: str
            series_index: str
            tags: Comma separated strings
            title: str

        Returns list[int] of book IDs
        """

        if not path.exists(book_path):
            error(f"Failed to find book at {book_path}")

        cmd = f"{self.cdb_with_lib} add {book_path}"
        cmd = self._handle_add_flags(cmd, kwargs)
        out, err = self._run(cmd)

        if err:
            error(err)

        if out:
            book_ids_str = re.search(r"^Added book ids: ([0-9,]+)", out).group(1)
            book_ids = book_ids_str.split(",")
            return book_ids

    # Add an empty book (with no formats)
    def add_empty(self, **kwargs: Any):
        cmd = f"{self.cdb_with_lib} add --empty"

        cmd = self._handle_add_flags(cmd, kwargs)
        out, err = self._run(cmd)

        if err:
            error(err)

        if out:
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
        # logging.info(f"Unsupported flags {','.join(sorted(kwargs))}")
        return cmd

    # Remove book with id.
    # Does not return output or err if ids do not exist
    def remove(self, ids: list[int], permanent: bool = False):
        if not all(i >= 0 for i in ids):
            error(f"ids {ids} not allowed")

        cmd = f'{self.cdb_with_lib} remove {",".join(map(str, ids))}'

        if permanent:
            cmd += " --permanent"

        return self._run(cmd)

    # Add book format to existing book id
    def add_format(self, id: int, replace: bool = False, data_file: bool = False):
        if id <= 0:
            error(f"id {id} not allowed")

        cmd = f"{self.cdb_with_lib} add_format {id}"

        if replace:
            cmd += " --dont-replace"

        if data_file:
            cmd += " --as-extra-data-file"

        return self._run(cmd)

    # Remove book format from existing book.
    # Format must be a file extension like EPUB, TXT etc.
    def remove_format(self, id: int, format: str):
        if id <= 0:
            error(f"id {id} not allowed")

        # TODO check format
        cmd = f"{self.cdb_with_lib} remove_format {id} {format}"
        return self._run(cmd)

    # Returns XML metadata of given book id
    def show_metadata(self, id: int) -> str:
        if id <= 0:
            error(f"id {id} not allowed")

        cmd = f"{self.cdb_with_lib} show_metadata --as-opf {id}"
        return self._run(cmd)

    # Set XML metadata of given book id from given OPF file or flags
    def set_metadata(self, id: int, metadata_path: str = None, **kwargs):
        """
        id: book ID to set metadata
        metadata_path (Optional): Path to OPF metadata file
        **kwargs:
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

        if id <= 0:
            error(f"id {id} not allowed")

        cmd = f"{self.cdb_with_lib} set_metadata {id}"

        if metadata_path:
            if not path.exists(metadata_path):
                error(f"Metadata file {metadata_path} does not exist")
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

    # Export books with given ids to directory
    def export(self, ids: list[int]):
        pass


def quote(s: str) -> str:
    s = s.strip()
    return shlex.quote(s) if " " in s else s


def error(message, exit_code=1):
    logging.error(message)
    sys.exit(exit_code)
