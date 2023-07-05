from dataclasses import dataclass, field
from urllib.parse import urlencode, urlsplit, urlunsplit

from jsonschema import Draft202012Validator


@dataclass
class Book:
    """
    authors:
    author_sort:
    comments: in html
    cover:
    formats:
    id:
    identifiers:
    isbn:
    languages:
    last_modified:
    pubdate:
    publisher:
    rating:
    series:
    series_index:
    size:
    tags:
    template:
    timestamp:
    title:
    uuid:
    """

    authors: list[str] = field(default_factory=list)
    author_sort: str = ""
    comments: str = ""
    cover: str = ""
    formats: list[str] = field(default_factory=list)
    id: int = 0
    identifiers: dict[str, str] = field(default_factory=dict)
    isbn: str = ""
    languages: list[str] = field(default_factory=list)
    last_modified: str = ""
    pubdate: str = ""
    publisher: str = ""
    rating: int = 0
    series: str = ""
    series_index: float = 0.0
    size: int = 0
    tags: list[str] = field(default_factory=list)
    template: str = ""
    timestamp: str = ""
    title: str = ""
    uuid: str = ""

    SCHEMA = {
        "type": "object",
        "properties": {
            "authors": {"type": "array", "items": {"type": "string"}},
            "author_sort": {"type": "string"},
            "comments": {"type": "string"},
            "cover": {"type": "string"},
            "id": {"type": "integer", "minimum": 0},
            "identifiers": {"type": "object"},
            "isbn": {"type": "string"},
            "languages": {"type": "array", "items": {"type": "string"}},
            "pubdate": {"type": "string"},
            "publisher": {"type": "string"},
            "rating": {"type": "number"},
            "series": {"type": "string"},
            "series_index": {"type": "number", "minimum": 0.0},
            "size": {"type": "number"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "timestamp": {"type": "string"},
            "title": {"type": "string"},
            # not class property
            "automerge": {
                "type": "string",
                "enum": ["ignore", "overwrite", "new_record"],
            },
        },
        "additionalProperties": False,
    }
    v = Draft202012Validator(SCHEMA)

    @classmethod
    def validate(cls, instance):
        # TODO valid identifiers object must be dict(str, str)
        return sorted(cls.v.iter_errors(instance), key=str)


class PaginatedResults:
    """Paginate list of books with offset and limit.

    Fields:
        books (list[Book]): Full list of books
        start (int): Start index
        limit (int): Number of books per page
        sort (list[str]): List of sort keys
        search (list[str]): List of search terms
    """

    def __init__(
        self,
        books: list[Book],
        start: int,
        limit: int,
        sort: list[str] = None,
        search: list[str] = None,
    ):
        self.base_url = urlsplit("/books")
        self.books = books
        self.start = start
        self.limit = limit
        self.sort = sort
        self.search = search

        if len(books) < self.start:
            raise Exception(
                f"start {self.start} is larger than number of books ({len(books)})"
            )
        self.count = len(books)

    def build_query(self, start: int):
        params = {"start": start, "limit": self.limit}

        if self.sort is not None:
            params["sort"] = self.sort

        if self.search is not None:
            params["search"] = self.search

        query = urlencode(params, doseq=True)
        return urlunsplit(self.base_url._replace(query=query))

    def current_page(self):
        return self.build_query(self.start)

    def prev_page(self):
        if not self.has_prev_page():
            return ""

        prev_start = max(1, self.start - self.limit)
        return self.build_query(prev_start)

    def next_page(self):
        if not self.has_next_page():
            return ""

        return self.build_query(self.start + self.limit)

    def has_prev_page(self):
        return not (self.start == 1)

    def has_next_page(self):
        return not (self.start + self.limit > self.count)

    def todict(self):
        return {
            "books": self.books[
                (self.start - 1) : (self.start - 1 + self.limit)  # noqa
            ],
            "metadata": {
                "start": self.start,
                "limit": self.limit,
                "count": self.count,
                "self": self.current_page(),
                "prev": self.prev_page(),
                "next": self.next_page(),
            },
        }
