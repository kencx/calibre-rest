import json
import os
from enum import IntEnum
from http import HTTPStatus

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
    """Add book to database and delete on cleanup."""
    id = post(f"{url}/books", HTTPStatus.CREATED, files=test_txt("test.txt"))
    yield id
    delete(url, id)


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


def test_add_empty_wrong_media_type(url):
    check_error(
        "POST",
        f"{url}/books/empty",
        HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        "Only application/json allowed",
        headers={"Content-Type": "application/xml"},
    )


def test_add_empty_no_data(url):
    check_error(
        "POST",
        f"{url}/books/empty",
        HTTPStatus.BAD_REQUEST,
        "No data provided",
        headers={"Content-Type": "application/json"},
    )


def test_add_empty_invalid_data(url):
    headers = {"Content-Type": "application/json"}
    payload = {"title": 1}
    resp = requests.post(f"{url}/books/empty", json=payload, headers=headers)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "1 is not of type 'string'" in resp.json()["errors"][0]["title"]


@pytest.mark.parametrize(
    "payload, key, expected",
    (
        ({"title": "foo"}, "title", "foo"),
        ({}, "title", "Unknown"),
        ({"tags": ["foo", "bar"]}, "tags", ["foo", "bar"]),
        (
            {"identifiers": {"foo": "abcd", "bar": "1234"}},
            "identifiers",
            {"foo": "abcd", "bar": "1234"},
        ),
    ),
    ids=["simple", "no data", "list", "identifiers"],
)
def test_add_empty_valid(url, payload, key, expected):
    headers = {"Content-Type": "application/json"}
    id = post(f"{url}/books/empty", HTTPStatus.CREATED, json=payload, headers=headers)
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
        HTTPStatus.BAD_REQUEST,
        "No file provided",
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
    ("test.abc", "-test.txt"),
    ids=["extension", "hyphen"],
)
def test_add_book_invalid_filename(url, test_txt, filename):
    check_error(
        "POST",
        f"{url}/books",
        HTTPStatus.BAD_REQUEST,
        "Invalid filename",
        files=test_txt(filename),
    )


def test_add_book_invalid_data(url, test_txt):
    payload = {"title": 1}
    resp = requests.post(
        f"{url}/books", files=test_txt("test.txt"), data={"data": json.dumps(payload)}
    )

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "1 is not of type 'string'" in resp.json()["errors"][0]["title"]


def test_add_book_invalid_key(url, test_txt):
    payload = {"title": "foo", "random": "value"}
    resp = requests.post(
        f"{url}/books", files=test_txt("test.txt"), data={"data": json.dumps(payload)}
    )

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "'random' was unexpected" in resp.json()["errors"][0]["key"]


def test_add_book_invalid_data_multiple(url, test_txt):
    payload = {"title": 1, "series_index": "string", "random": "value"}
    resp = requests.post(
        f"{url}/books", files=test_txt("test.txt"), data={"data": json.dumps(payload)}
    )
    errors = resp.json()["errors"]

    assert resp.status_code == HTTPStatus.BAD_REQUEST
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
    )
    get(url, added_id, HTTPStatus.OK, {"title": "foo", "authors": "John Doe"})
    delete(url, added_id)


def test_add_book_automerge_invalid_value(url, test_txt):
    payload = {"automerge": "invalid value"}
    resp = requests.post(
        f"{url}/books", files=test_txt("test.txt"), data={"data": json.dumps(payload)}
    )

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert (
        "'invalid value' is not one of ['ignore', 'overwrite', 'new_record']"
        in resp.json()["errors"][0]["automerge"]
    )


@pytest.mark.parametrize(
    "payload",
    (
        {},
        {"automerge": "ignore"},
    ),
    ids=["no payload", "explicit ignore"],
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
    )
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
    )
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
    )
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
    )
    assert added_id2 != added_id

    get(url, added_id, HTTPStatus.OK, {"title": "test"})
    get(url, added_id2, HTTPStatus.OK, {"title": "test"})
    delete(url, added_id2)


def test_add_book_existing_with_diff_name(url, seed_book, test_txt):
    """Tests that adding the same file with a different name results in a
    new entry.
    """
    added_id = seed_book

    # add the same file but with different name
    added_id2 = post(f"{url}/books", HTTPStatus.CREATED, files=test_txt("test2.txt"))
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

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "1 is not of type 'string'" in resp.json()["errors"][0]["title"]


def test_update_book_invalid_key(url, seed_book):
    id = seed_book

    payload = {"title": "foo", "random": "value"}
    resp = requests.put(f"{url}/books/{id}", json=payload)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "'random' was unexpected" in resp.json()["errors"][0]["key"]


def test_update_book_valid_data(url, seed_book):
    id = seed_book

    payload = {"title": "new title", "tags": ["foo", "bar"]}
    book = put(url, id, HTTPStatus.OK, json=payload)

    assert book["id"] == int(id)
    assert book["title"] == "new title"
    assert book["tags"] == ["foo", "bar"]


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
