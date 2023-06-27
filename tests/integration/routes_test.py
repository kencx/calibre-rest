from http import HTTPStatus

import pytest
import requests


def test_version(setup):
    resp = requests.get(f"{setup.bind_addr}/health")

    assert resp.status_code == HTTPStatus.OK


def test_get_invalid_id(setup):
    resp = requests.get(f"{setup.bind_addr}/books/0")

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "cannot be <= 0" in resp.json()["error"]


def test_get_404(setup):
    resp = requests.get(f"{setup.bind_addr}/books/1000")

    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert "does not exist" in resp.json()["error"]


def test_delete_invalid_id(setup):
    resp = requests.delete(f"{setup.bind_addr}/books/0")

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "cannot be <= 0" in resp.json()["error"]


def test_post_no_data(setup):
    headers = {"Content-Type": "multipart/form-data"}
    resp = requests.post(f"{setup.bind_addr}/books", headers=headers)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "No file provided" in resp.json()["error"]


def test_post_wrong_media_type(setup):
    headers = {"Content-Type": "application/xml"}
    resp = requests.post(f"{setup.bind_addr}/books", headers=headers)

    assert resp.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert (
        "Only multipart/form-data and application/json allowed" in resp.json()["error"]
    )


def test_post_empty_wrong_media_type(setup):
    headers = {"Content-Type": "application/xml"}
    resp = requests.post(f"{setup.bind_addr}/books/empty", headers=headers)

    assert resp.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert "Only application/json allowed" in resp.json()["error"]


def test_post_empty_invalid_data(setup):
    headers = {"Content-Type": "application/json"}
    payload = {"title": 1}
    resp = requests.post(
        f"{setup.bind_addr}/books/empty", json=payload, headers=headers
    )

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
def test_post_empty_valid(setup, payload, key, expected):
    headers = {"Content-Type": "application/json"}
    post_resp = requests.post(
        f"{setup.bind_addr}/books/empty", json=payload, headers=headers
    )

    assert post_resp.status_code == HTTPStatus.CREATED

    added_id = post_resp.json()["added_id"]
    get_resp = requests.get(f"{setup.bind_addr}/books/{added_id}")

    assert get_resp.status_code == HTTPStatus.OK
    assert get_resp.json()["books"]["id"] == int(added_id)
    assert get_resp.json()["books"][key] == expected

    delete_resp = requests.delete(f"{setup.bind_addr}/books/{added_id}")

    assert delete_resp.status_code == HTTPStatus.OK
