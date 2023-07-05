import pytest

from calibre_rest.models import Book, PaginatedResults


@pytest.fixture(scope="module")
def books():
    return [
        Book(title="foo"),
        Book(title="bar"),
        Book(title="bar"),
        Book(title="four"),
        Book(title="five"),
    ]


@pytest.mark.parametrize(
    "start, limit, count, prev, next",
    (
        pytest.param(1, 2, 2, "", "/books?start=3&limit=2", id="first page"),
        pytest.param(
            2, 3, 3, "/books?start=1&limit=3", "/books?start=5&limit=3", id="prev page"
        ),
        pytest.param(4, 3, 2, "/books?start=1&limit=3", "", id="next page"),
        pytest.param(5, 2, 1, "/books?start=3&limit=2", "", id="last page"),
    ),
)
def test_pagination_paging(books, start, limit, count, prev, next):
    res = PaginatedResults(books, start, limit)
    assert res.current_page() == f"/books?start={start}&limit={limit}"
    assert res.prev_page() == prev
    assert res.next_page() == next

    d = res.todict()
    assert len(d["books"]) == count
    assert d["metadata"]["start"] == start
    assert d["metadata"]["limit"] == limit
    assert d["metadata"]["count"] == len(books)


@pytest.mark.parametrize(
    "sort, expected",
    (
        pytest.param(["title"], "/books?start=1&limit=2&sort=title", id="single"),
        pytest.param(
            ["title", "authors"],
            "/books?start=1&limit=2&sort=title&sort=authors",
            id="multiple",
        ),
        pytest.param([], "/books?start=1&limit=2", id="empty"),
    ),
)
def test_build_query_sort(books, sort, expected):
    res = PaginatedResults(books, 1, 2, sort=sort)
    assert res.build_query(1) == expected


@pytest.mark.parametrize(
    "search, expected",
    (
        pytest.param(["foobar"], "/books?start=1&limit=2&search=foobar", id="valid"),
        pytest.param(
            ["foo", "bar"],
            "/books?start=1&limit=2&search=foo&search=bar",
            id="multiple",
        ),
        pytest.param([], "/books?start=1&limit=2", id="empty"),
    ),
)
def test_build_query_search(books, search, expected):
    res = PaginatedResults(books, 1, 2, search=search)
    assert res.build_query(1) == expected


def test_pagination(books):
    res = PaginatedResults(books, 1, 2, sort=["authors"], search="foobar")
    assert res.current_page() == "/books?start=1&limit=2&sort=authors&search=foobar"
    assert res.prev_page() == ""
    assert res.next_page() == "/books?start=3&limit=2&sort=authors&search=foobar"
