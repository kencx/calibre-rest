import json
import os
from enum import IntEnum
from http import HTTPStatus

import pytest
import requests
from conftest import TEST_LIBRARY_PATH


def test_version(url):
    resp = requests.get(f"{url}/health")
    assert resp.status_code == HTTPStatus.OK


def test_get_invalid_id(url):
    get_error(
        f"{url}/books/0",
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "cannot be <= 0",
    )


def test_get_404(url):
    get_error(
        f"{url}/books/1000",
        HTTPStatus.NOT_FOUND,
        "does not exist",
    )


def test_delete_invalid_id(url):
    resp = requests.delete(f"{url}/books/0")

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "cannot be <= 0" in resp.json()["error"]


def test_add_empty_wrong_media_type(url):
    headers = {"Content-Type": "application/xml"}
    resp = requests.post(f"{url}/books/empty", headers=headers)

    assert resp.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert "Only application/json allowed" in resp.json()["error"]


def test_add_empty_invalid_data(url):
    headers = {"Content-Type": "application/json"}
    payload = {"title": 1}
    resp = requests.post(f"{url}/books/empty", json=payload, headers=headers)

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
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
    post_resp = requests.post(f"{url}/books/empty", json=payload, headers=headers)

    assert post_resp.status_code == HTTPStatus.CREATED

    added_id = post_resp.json()["added_id"]
    get_check(
        url,
        added_id,
        HTTPStatus.OK,
        {key: expected},
    )


def test_add_book_no_file(url):
    headers = {"Content-Type": "multipart/form-data"}
    resp = requests.post(f"{url}/books", headers=headers)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "No file provided" in resp.json()["error"]


def test_add_book_wrong_media_type(url):
    headers = {"Content-Type": "application/xml"}
    resp = requests.post(f"{url}/books", headers=headers)

    assert resp.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert (
        "Only multipart/form-data and application/json allowed" in resp.json()["error"]
    )


@pytest.mark.parametrize(
    "filename",
    ("test.abc", "-test.txt"),
    ids=["extension", "hyphen"],
)
def test_add_book_invalid_filename(url, filename):
    files = {
        "file": (
            filename,
            open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb"),
            "application/octet-stream",
        )
    }
    post_resp = requests.post(f"{url}/books", files=files)

    assert post_resp.status_code == HTTPStatus.BAD_REQUEST
    assert "Invalid filename" in post_resp.json()["error"]


def test_add_book_invalid_data(url):
    files = {
        "file": (
            "test.txt",
            open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb"),
            "application/octet-stream",
        )
    }
    payload = {"title": 1}
    resp = requests.post(
        f"{url}/books", files=files, data={"data": json.dumps(payload)}
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "1 is not of type 'string'" in resp.json()["errors"][0]["title"]


def test_add_book_invalid_key(url):
    files = {
        "file": (
            "test.txt",
            open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb"),
            "application/octet-stream",
        )
    }
    payload = {"title": "foo", "random": "value"}
    resp = requests.post(
        f"{url}/books", files=files, data={"data": json.dumps(payload)}
    )

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "unexpected keyword argument 'random'" in resp.json()["error"]


def test_add_book_file_data(url):
    files = {
        "file": (
            "test.txt",
            open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb"),
            "application/octet-stream",
        )
    }
    payload = {"title": "foo", "authors": ["John Doe"]}

    # The payload must be serialized into JSON and wrapped in a dict with the
    # "data" key. This allows Flask to access it as form data with the correct
    # key. The "json" argument cannot be used as it will attempt to set the
    # Content-Type as "application/json", causing Flask's request.form to be
    # empty.
    post_resp = requests.post(
        f"{url}/books", files=files, data={"data": json.dumps(payload)}
    )

    assert post_resp.status_code == HTTPStatus.CREATED
    added_id = post_resp.json()["added_id"]
    get_check(url, added_id, HTTPStatus.OK, {"title": "foo", "authors": "John Doe"})
    delete_check(url, added_id)


@pytest.mark.parametrize(
    "payload",
    (
        {},
        {"automerge": "ignore"},
    ),
    ids=["no payload", "explicit ignore"],
)
def test_add_book_existing_no_overwrite(url, payload):
    """This tests that the existing book should not be overwritten and no new
    entries are created.
    """
    files = {
        "file": (
            "test.txt",
            open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb"),
            "application/octet-stream",
        )
    }
    post_resp = requests.post(
        f"{url}/books", files=files, data={"data": json.dumps(payload)}
    )
    assert post_resp.status_code == HTTPStatus.CREATED
    added_id = post_resp.json()["added_id"]

    post_resp2 = requests.post(f"{url}/books", files=files)
    assert post_resp2.status_code == HTTPStatus.CONFLICT
    assert "already exists" in post_resp2.json()["error"]

    delete_check(url, added_id)


def test_add_book_existing_overwrite(url):
    """This tests that the existing book should not be overwritten, but a new
    entry is created, even though automerge=ignore. This is because new metadata
    was added, causing a new entry to be created.
    """
    files = {
        "file": (
            "test.txt",
            open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb"),
            "application/octet-stream",
        )
    }
    payload = {"automerge": "ignore", "title": "foo"}

    post_resp = requests.post(
        f"{url}/books", files=files, data={"data": json.dumps(payload)}
    )
    assert post_resp.status_code == HTTPStatus.CREATED
    added_id = post_resp.json()["added_id"]

    post_resp2 = requests.post(f"{url}/books", files=files)
    assert post_resp2.status_code == HTTPStatus.CREATED
    added_id2 = post_resp2.json()["added_id"]
    assert added_id != added_id2

    delete_check(url, added_id)
    delete_check(url, added_id2)


def test_add_book_existing_overwrite_merge(url):
    """This tests that the newly added book is merged with the existing book
    because automerge=overwrite is passed.
    """
    files = {
        "file": (
            "test.txt",
            open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb"),
            "application/octet-stream",
        )
    }
    payload = {"automerge": "overwrite"}

    post_resp = requests.post(f"{url}/books", files=files)
    assert post_resp.status_code == HTTPStatus.CREATED
    added_id = post_resp.json()["added_id"]

    post_resp2 = requests.post(
        f"{url}/books", files=files, data={"data": json.dumps(payload)}
    )
    assert post_resp2.status_code == HTTPStatus.CREATED
    added_id2 = post_resp2.json()["added_id"]
    assert added_id2 == added_id

    get_check(url, added_id, HTTPStatus.OK, {"title": "test"})
    delete_check(url, added_id)


def test_add_book_existing_overwrite_new(url):
    """This tests that the newly added book is created as a new entry because
    additional metadata was added.
    """
    files = {
        "file": (
            "test.txt",
            open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb"),
            "application/octet-stream",
        )
    }
    payload = {"automerge": "overwrite", "title": "foo"}

    post_resp = requests.post(f"{url}/books", files=files)
    assert post_resp.status_code == HTTPStatus.CREATED
    added_id = post_resp.json()["added_id"]

    post_resp2 = requests.post(
        f"{url}/books", files=files, data={"data": json.dumps(payload)}
    )
    assert post_resp2.status_code == HTTPStatus.CREATED
    added_id2 = post_resp2.json()["added_id"]
    assert added_id2 != added_id

    get_check(url, added_id, HTTPStatus.OK, {"title": "test"})
    get_check(url, added_id2, HTTPStatus.OK, {"title": "foo"})
    delete_check(url, added_id)
    delete_check(url, added_id2)


def test_add_book_existing_with_diff_name(url):
    """This tests that adding the same file with a different name results in a
    new entry.
    """
    files = {
        "file": (
            "test.txt",
            open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb"),
            "application/octet-stream",
        )
    }

    post_resp = requests.post(f"{url}/books", files=files)
    assert post_resp.status_code == HTTPStatus.CREATED
    added_id = post_resp.json()["added_id"]

    # add the same file but with different name
    files = {
        "file": (
            "test2.txt",
            open(os.path.join(TEST_LIBRARY_PATH, "test.txt"), "rb"),
            "application/octet-stream",
        )
    }

    post_resp2 = requests.post(f"{url}/books", files=files)
    assert post_resp2.status_code == HTTPStatus.CREATED
    added_id2 = post_resp2.json()["added_id"]

    assert added_id != added_id2

    get_check(url, added_id, HTTPStatus.OK, {})
    get_check(url, added_id2, HTTPStatus.OK, {})
    delete_check(url, added_id)
    delete_check(url, added_id2)


def get_error(url, code, err_message):
    resp = requests.get(url)
    assert resp.status_code == code
    assert err_message in resp.json()["error"]


def get_check(url: str, id: int | str, code: IntEnum, mappings: dict):
    resp = requests.get(f"{url}/books/{id}")
    assert resp.status_code == code

    data = resp.json()
    assert data["books"]["id"] == int(id)
    for k, v in mappings.items():
        assert data["books"][k] == v


def delete_check(url: str, id: int):
    resp = requests.delete(f"{url}/books/{id}")
    assert resp.status_code == HTTPStatus.OK
