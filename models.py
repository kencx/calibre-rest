from dataclasses import asdict, dataclass, field


@dataclass
class Book:
    """
    authors: Multiple authors separated by &
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

    authors: str = ""
    author_sort: str = ""
    comments: str = ""
    cover: str = ""
    formats: str = ""
    id: int = 0
    identifiers: dict[str, str] = field(default_factory=dict)
    isbn: str = ""
    languages: list[str] = field(default_factory=list)
    last_modified: str = ""
    pubdate: str = ""
    publisher: str = ""
    rating: str = ""
    series: str = ""
    series_index: float = 0.0
    size: str = ""
    tags: list[str] = field(default_factory=list)
    template: str = ""
    timestamp: str = ""
    title: str = ""
    uuid: str = ""

    def serialize(self):
        return asdict(self)


class PaginatedResult:
    def __init__(self):
        pass

    def to_collection_dict(self):
        pass
