import json
import os
import zipfile
from enum import IntEnum
from http import HTTPStatus
from io import BytesIO

import pytest
import requests
from conftest import TEST_LIBRARY_PATH


@pytest.fixture()
def test_txt():
    """Factory fixture for file payload.

    Args:
        filename (str): Filename for test.txt
    """

    def _test_txt(filename):
        return {
            "file": (
                filename,
                open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb"),
                "application/octet-stream",
            )
        }

    return _test_txt


@pytest.fixture()
def seed_book(url, test_txt):
    """Add one book to database and delete on cleanup."""
    id = post(f"{url}/books", HTTPStatus.CREATED, files=test_txt("test.txt"))
    yield id[0]
    delete(url, id[0])


@pytest.fixture()
def seed_books(url, test_txt):
    """Add multiple books to database and delete on cleanup."""
    files = [("file", (f"foo{str(i)}.txt", f"hello {str(i)}")) for i in range(1, 6)]
    ids = post(f"{url}/books", HTTPStatus.CREATED, files=files)
    yield ids
    resp = requests.delete(f"{url}/books", params={"id": ",".join(ids)})
    assert resp.status_code == HTTPStatus.OK


def test_version(url):
    resp = requests.get(f"{url}/health")
    assert resp.status_code == HTTPStatus.OK


def test_get_invalid_id(url):
    check_error(
        "GET",
        f"{url}/books/0",
        HTTPStatus.BAD_REQUEST,
        "cannot be <= 0",
    )


def test_get_404(url):
    check_error(
        "GET",
        f"{url}/books/1000",
        HTTPStatus.NOT_FOUND,
        "does not exist",
    )


def test_get_book(url, seed_book):
    id = seed_book
    get(
        url,
        id,
        HTTPStatus.OK,
        {"title": "test", "authors": "Unknown", "id": int(id)},
    )


def test_delete_invalid_id(url):
    check_error(
        "DELETE",
        f"{url}/books/0",
        HTTPStatus.BAD_REQUEST,
        "cannot be <= 0",
    )


def test_delete(url, seed_book):
    id = seed_book
    delete(url, id)
    check_error(
        "GET",
        f"{url}/books/{id}",
        HTTPStatus.NOT_FOUND,
        "does not exist",
    )


def test_delete_multiple(url, seed_books):
    resp = requests.delete(f"{url}/books", params={"id": ",".join(seed_books)})
    assert resp.status_code == HTTPStatus.OK

    get_resp = requests.get(f"{url}/books")
    assert get_resp.status_code == HTTPStatus.NO_CONTENT


def test_get_books_empty(url):
    resp = requests.get(f"{url}/books")

    assert resp.status_code == HTTPStatus.NO_CONTENT
    assert resp.content == bytes()


def test_get_books_basic(url, seed_books):
    resp = requests.get(f"{url}/books")

    assert resp.status_code == HTTPStatus.OK
    assert len(resp.json()["books"]) == 5

    metadata = resp.json()["metadata"]
    assert metadata["start"] == 1
    assert metadata["limit"] == 20
    assert metadata["prev"] == ""
    assert metadata["next"] == ""
    assert metadata["self"] == "/books?start=1&limit=20"


def test_get_books_high_start(url, seed_book):
    """Tests that 400 error is returned if start query param is larger than
    number of returned books.
    """
    seed_book
    resp = requests.get(f"{url}/books?start=5")

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "start 5 is larger than number of books" in resp.json()["error"]


def test_get_books_pagination(url, seed_books):
    resp = requests.get(f"{url}/books?start=2&limit=2")
    assert resp.status_code == HTTPStatus.OK

    books = resp.json()["books"]
    assert len(books) == 2
    assert books[0]["title"] == "foo2"
    assert books[1]["title"] == "foo3"

    metadata = resp.json()["metadata"]
    assert metadata["self"] == "/books?start=2&limit=2"
    assert metadata["prev"] == "/books?start=1&limit=2"
    assert metadata["next"] == "/books?start=4&limit=2"


def test_get_books_sort(url, seed_books):
    resp = requests.get(f"{url}/books?limit=2&sort=title")
    assert resp.status_code == HTTPStatus.OK

    books = resp.json()["books"]
    assert len(books) == 2
    assert books[0]["title"] == "foo1"
    assert books[1]["title"] == "foo2"


def test_get_books_sort_multiple(url, seed_books):
    resp = requests.get(f"{url}/books?limit=2&sort=-title&sort=id")
    assert resp.status_code == HTTPStatus.OK

    books = resp.json()["books"]
    assert len(books) == 2
    assert books[0]["title"] == "foo5"
    assert books[1]["title"] == "foo4"


def test_get_books_search_basic(url, seed_books):
    resp = requests.get(f"{url}/books?search=title:foo1")
    assert resp.status_code == HTTPStatus.OK

    books = resp.json()["books"]
    assert len(books) == 1
    assert books[0]["title"] == "foo1"


def test_get_books_search_multiple(url, seed_books):
    resp = requests.get(f"{url}/books?search=title:foo1&search=authors:bar")
    assert resp.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.parametrize(
    "params, count",
    (
        pytest.param({"search": "title:foo1 or foo2"}, 2, id="bool"),
        pytest.param({"search": "title:~^foo\\d"}, 5, id="regex"),
    ),
)
def test_get_books_search_advanced(url, seed_books, params, count):
    resp = requests.get(f"{url}/books", params=params)
    assert resp.status_code == HTTPStatus.OK

    assert len(resp.json()["books"]) == count


def test_add_empty_wrong_media_type(url):
    check_error(
        "POST",
        f"{url}/books/empty",
        HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        "Only application/json allowed",
        headers={"Content-Type": "application/xml"},
    )


def test_add_empty_invalid_data(url):
    headers = {"Content-Type": "application/json"}
    payload = {"title": 1}
    resp = requests.post(f"{url}/books/empty", json=payload, headers=headers)

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "1 is not of type 'string'" in resp.json()["errors"][0]["title"]


def test_add_empty_no_data(url):
    headers = {"Content-Type": "application/json"}
    id = post(f"{url}/books/empty", HTTPStatus.CREATED, headers=headers)[0]
    get(
        url,
        id,
        HTTPStatus.OK,
        {"title": "Unknown"},
    )


@pytest.mark.parametrize(
    "payload, key, expected",
    (
        pytest.param({"title": "foo"}, "title", "foo", id="simple"),
        pytest.param({}, "title", "Unknown", id="no data"),
        pytest.param(
            {"tags": ["foo", "bar"]},
            "tags",
            ["foo", "bar"],
            id="list",
        ),
        pytest.param(
            {"identifiers": {"foo": "abcd", "bar": "1234"}},
            "identifiers",
            {"foo": "abcd", "bar": "1234"},
            id="identifiers",
        ),
    ),
)
def test_add_empty_valid(url, payload, key, expected):
    headers = {"Content-Type": "application/json"}
    id = post(
        f"{url}/books/empty",
        HTTPStatus.CREATED,
        json=payload,
        headers=headers,
    )[0]
    get(
        url,
        id,
        HTTPStatus.OK,
        {key: expected},
    )


def test_add_book_no_file(url):
    check_error(
        "POST",
        f"{url}/books",
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "No file(s) provided",
        headers={"Content-Type": "multipart/form-data"},
    )


def test_add_book_wrong_media_type(url):
    check_error(
        "POST",
        f"{url}/books",
        HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        "Only multipart/form-data allowed",
        headers={"Content-Type": "application/xml"},
    )


@pytest.mark.parametrize(
    "filename",
    (
        pytest.param("test.abc", id="invalid extension"),
        pytest.param("-test.txt", id="leading hyphen"),
    ),
)
def test_add_book_invalid_filename(url, test_txt, filename):
    check_error(
        "POST",
        f"{url}/books",
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "Invalid filename",
        files=test_txt(filename),
    )


def test_add_book_invalid_data(url, test_txt):
    payload = {"title": 1}
    resp = requests.post(
        f"{url}/books", files=test_txt("test.txt"), data={"data": json.dumps(payload)}
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "1 is not of type 'string'" in resp.json()["errors"][0]["title"]


def test_add_book_invalid_key(url, test_txt):
    payload = {"title": "foo", "random": "value"}
    resp = requests.post(
        f"{url}/books", files=test_txt("test.txt"), data={"data": json.dumps(payload)}
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "'random' was unexpected" in resp.json()["errors"][0]["key"]


def test_add_book_invalid_data_multiple(url, test_txt):
    payload = {"title": 1, "series_index": "string", "random": "value"}
    resp = requests.post(
        f"{url}/books", files=test_txt("test.txt"), data={"data": json.dumps(payload)}
    )
    errors = resp.json()["errors"]

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "'string' is not of type 'number'" in errors[0]["series_index"]
    assert "1 is not of type 'string'" in errors[1]["title"]
    assert "'random' was unexpected" in errors[2]["key"]


def test_add_book_file_data(url, test_txt):
    # The client's payload must be serialized into JSON and wrapped in a dict
    # with the "data" key. This allows Flask to access it as form data with the
    # correct key. The "json" argument cannot be used as it will attempt to set
    # the Content-Type as "application/json", causing Flask's request.form to be
    # empty.

    payload = {"title": "foo", "authors": ["John Doe"]}
    added_id = post(
        f"{url}/books",
        HTTPStatus.CREATED,
        files=test_txt("test.txt"),
        data={"data": json.dumps(payload)},
    )[0]
    get(url, added_id, HTTPStatus.OK, {"title": "foo", "authors": "John Doe"})
    delete(url, added_id)


def test_add_book_multiple_files(url):
    files = [
        ("file", open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb")),
        ("other", ("bar.txt", "foobar")),
    ]
    payload = {"title": "bar", "automerge": "new_record"}
    added_ids = post(
        f"{url}/books",
        HTTPStatus.CREATED,
        files=files,
        data={"data": json.dumps(payload)},
    )

    for i in added_ids:
        get(url, i, HTTPStatus.OK, {"title": "bar", "id": int(i)})
        delete(url, i)


def test_add_book_automerge_invalid_value(url, test_txt):
    payload = {"automerge": "invalid value"}
    resp = requests.post(
        f"{url}/books", files=test_txt("test.txt"), data={"data": json.dumps(payload)}
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert (
        "'invalid value' is not one of ['ignore', 'overwrite', 'new_record']"
        in resp.json()["errors"][0]["automerge"]
    )


@pytest.mark.parametrize(
    "payload",
    (
        pytest.param({}, id="no payload"),
        pytest.param({"automerge": "ignore"}, id="explicit ignore"),
    ),
)
def test_add_book_automerge_ignore(url, payload, test_txt, seed_book):
    """Tests that the existing book should not be overwritten and no new
    entries are created.
    """
    check_error(
        "POST",
        f"{url}/books",
        HTTPStatus.CONFLICT,
        "already exists",
        files=test_txt("test.txt"),
        data={"data": json.dumps(payload)},
    )


def test_add_book_ignore_new(url, test_txt, seed_book):
    """Tests that the new book should not be ignored, but a new
    entry is created, even though automerge=ignore. This is because new metadata
    was added, causing a new entry to be created.
    """
    added_id = seed_book

    payload = {"automerge": "ignore", "title": "foo"}
    added_id2 = post(
        f"{url}/books",
        HTTPStatus.CREATED,
        files=test_txt("test.txt"),
        data={"data": json.dumps(payload)},
    )[0]
    assert added_id != added_id2

    delete(url, added_id2)


def test_add_book_automerge_overwrite(url, test_txt, seed_book):
    """Tests that the newly added book is merged with the existing book
    because automerge=overwrite is passed.
    """
    added_id = seed_book

    payload = {"automerge": "overwrite"}
    added_id2 = post(
        f"{url}/books",
        HTTPStatus.CREATED,
        files=test_txt("test.txt"),
        data={"data": json.dumps(payload)},
    )[0]
    assert added_id2 == added_id

    get(url, added_id, HTTPStatus.OK, {"title": "test"})


def test_add_book_overwrite_new(url, test_txt, seed_book):
    """Tests that the new book should not be overwrite the existing, but a new
    entry is created, even though automerge=overwrite. This is because new metadata
    was added, causing a new entry to be created.
    """
    added_id = seed_book

    payload = {"automerge": "overwrite", "title": "foo"}
    added_id2 = post(
        f"{url}/books",
        HTTPStatus.CREATED,
        files=test_txt("test.txt"),
        data={"data": json.dumps(payload)},
    )[0]
    assert added_id2 != added_id

    get(url, added_id, HTTPStatus.OK, {"title": "test"})
    get(url, added_id2, HTTPStatus.OK, {"title": "foo"})
    delete(url, added_id2)


def test_add_book_new_record(url, test_txt, seed_book):
    """Tests that the existing book is created as a new entry because
    automerge=new_record was passed.
    """
    added_id = seed_book

    payload = {"automerge": "new_record"}
    added_id2 = post(
        f"{url}/books",
        HTTPStatus.CREATED,
        files=test_txt("test.txt"),
        data={"data": json.dumps(payload)},
    )[0]
    assert added_id2 != added_id

    get(url, added_id, HTTPStatus.OK, {"title": "test"})
    get(url, added_id2, HTTPStatus.OK, {"title": "test"})
    delete(url, added_id2)


def test_add_book_overwrite_multiple(url, test_txt, seed_book):
    """Tests that when multiple entries of the same book exist in the library,
    trying to add another with automerge=overwrite will overwrite all entries.
    """
    added_id = seed_book

    payload = {"automerge": "new_record"}
    added_id2 = post(
        f"{url}/books",
        HTTPStatus.CREATED,
        files=test_txt("test.txt"),
        data={"data": json.dumps(payload)},
    )[0]
    assert added_id2 != added_id

    payload = {"automerge": "overwrite"}
    added_id3 = post(
        f"{url}/books",
        HTTPStatus.CREATED,
        files=test_txt("test.txt"),
        data={"data": json.dumps(payload)},
    )
    assert len(added_id3) == 2
    assert added_id2 in added_id3
    assert added_id in added_id3

    delete(url, added_id2)


def test_add_book_existing_with_diff_name(url, seed_book, test_txt):
    """Tests that adding the same file with a different name results in a
    new entry.
    """
    added_id = seed_book

    # add the same file but with different name
    added_id2 = post(f"{url}/books", HTTPStatus.CREATED, files=test_txt("test2.txt"))[0]
    assert added_id != added_id2

    get(url, added_id, HTTPStatus.OK)
    get(url, added_id2, HTTPStatus.OK)
    delete(url, added_id2)


def test_update_book_wrong_media_type(url):
    headers = {"Content-Type": "application/xml"}
    check_error(
        "PUT",
        f"{url}/books/1",
        HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        "Only application/json allowed",
        headers=headers,
    )


def test_update_book_invalid_id(url):
    check_error(
        "PUT",
        f"{url}/books/0",
        HTTPStatus.BAD_REQUEST,
        "cannot be <= 0",
        json={"title": "foo"},
    )


def test_update_book_not_exist(url):
    check_error(
        "PUT",
        f"{url}/books/1000",
        HTTPStatus.NOT_FOUND,
        "does not exist",
        json={"title": "foo"},
    )


def test_update_book_no_data(url, seed_book):
    id = seed_book
    check_error(
        "PUT",
        f"{url}/books/{id}",
        HTTPStatus.BAD_REQUEST,
        "No data provided",
        json={},
    )


def test_update_book_invalid_data(url, seed_book):
    id = seed_book
    payload = {"title": 1}
    resp = requests.put(f"{url}/books/{id}", json=payload)

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "1 is not of type 'string'" in resp.json()["errors"][0]["title"]


def test_update_book_invalid_key(url, seed_book):
    id = seed_book

    payload = {"title": "foo", "random": "value"}
    resp = requests.put(f"{url}/books/{id}", json=payload)

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "'random' was unexpected" in resp.json()["errors"][0]["key"]


def test_update_book_valid_data(url, seed_book):
    id = seed_book

    payload = {"title": "new title", "tags": ["foo", "bar"]}
    book = put(url, id, HTTPStatus.OK, json=payload)

    assert book["id"] == int(id)
    assert book["title"] == "new title"
    assert book["tags"] == ["foo", "bar"]


def test_export_book_invalid_id(url):
    check_error(
        "GET",
        f"{url}/export/0",
        HTTPStatus.BAD_REQUEST,
        "cannot be <= 0",
    )


def test_export_book_not_exists(url):
    check_error(
        "GET",
        f"{url}/export/10",
        HTTPStatus.NOT_FOUND,
        "No book with id",
    )


def test_export_book(url, seed_book):
    resp = requests.get(f"{url}/export/{seed_book}", stream=True)
    assert resp.status_code == HTTPStatus.OK
    assert resp.text == "hello world!\n"


def test_export_books(url, seed_books):
    resp = requests.get(
        f"{url}/export", params={"id": ",".join(seed_books)}, stream=True
    )
    assert resp.status_code == HTTPStatus.OK

    z = zipfile.ZipFile(BytesIO(resp.content))
    for i in range(len(z.namelist())):
        assert f"foo{i+1}" in z.namelist()[i]


def get(url: str, id: int | str, code: IntEnum, mappings: dict = None):
    resp = requests.get(f"{url}/books/{id}")
    assert resp.status_code == code

    data = resp.json()
    assert data["books"]["id"] == int(id)
    if mappings is not None:
        for k, v in mappings.items():
            assert data["books"][k] == v


def post(url: str, code: IntEnum, **kwargs):
    resp = requests.post(url, **kwargs)
    assert resp.status_code == code
    return resp.json()["id"]


def put(url: str, id: int, code: IntEnum, **kwargs):
    resp = requests.put(f"{url}/books/{id}", **kwargs)
    assert resp.status_code == code
    return resp.json()["books"]


def delete(url: str, id: int):
    resp = requests.delete(f"{url}/books/{id}")
    assert resp.status_code == HTTPStatus.OK


def check_error(method: str, url: str, code: IntEnum, err_message: str, **kwargs):
    resp = requests.request(method, url, **kwargs)
    assert resp.status_code == code
    assert err_message in resp.json()["error"]
