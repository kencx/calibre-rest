from dataclasses import dataclass, field

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
            "formats": {"type": "array", "items": {"type": "string"}},
            "id": {"type": "integer", "minimum": 0},
            "identifiers": {"type": "object"},
            "isbn": {"type": "string"},
            "languages": {"type": "array", "items": {"type": "string"}},
            "last_modified": {"type": "string"},
            "pubdate": {"type": "string"},
            "publisher": {"type": "string"},
            "rating": {"type": "number"},
            "series": {"type": "string"},
            "series_index": {"type": "number", "minimum": 0.0},
            "size": {"type": "number"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "template": {"type": "string"},
            "timestamp": {"type": "string"},
            "title": {"type": "string"},
            "uuid": {"type": "string"},
        },
    }
    v = Draft202012Validator(SCHEMA)

    @classmethod
    def validate(self, instance):
        # TODO valid identifiers object must be dict(str, str)
        # TODO handle redundant data fields
        return sorted(self.v.iter_errors(instance), key=str)


class PaginatedResults:
    """
    Fields:
    books (list[Book]): List of books

    {
        "books": [...]
        "metadata": {
            "total_count": 200
            "limit": 10
            "self": "/books?limit=10&after_id=0"
            "prev": ""
            "next": "/books?limit=10&after_id=10"
        }
    }
    """

    def __init__(self, books: list[Book], total_count: int, limit: int):
        self.books = books
        self.total_count = total_count
        self.limit = limit
        self.before_id = -1
        self.after_id = 0

    def current_page(self):
        pass

    def prev_page(self):
        if not self.has_prev_page():
            return ""

        return f"/books?limit={self.limit}&before_id={self.after_id - self.limit}"

    def next_page(self):
        if not self.has_next_page():
            return ""

        return f"/books?limit={self.limit}&after_id={self.limit + self.after_id}"

    def has_prev_page(self):
        return self.before_id < 0

    def has_next_page(self):
        return not (self.limit + self.after_id > self.total_count)

    def todict(self):
        return {
            "books": self.books,
            "metadata": {
                "total_count": self.total_count,
                "limit": self.limit,
                "self": f"{self.current_page()}",
                "prev": f"{self.prev_page()}",
                "next": f"{self.next_page()}",
            },
        }
