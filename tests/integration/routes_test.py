from http import HTTPStatus

import requests

host = "http://localhost:5000"


def test_version(setup):
    resp = requests.get(f"{host}/health")

    assert resp.status_code == HTTPStatus.OK


def test_get_invalid_id(setup):
    resp = requests.get(f"{host}/books/0")

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "cannot be <= 0" in resp.json()["error"]


def test_get_404(setup):
    resp = requests.get(f"{host}/books/1000")

    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert "does not exist" in resp.json()["error"]


def test_delete_invalid_id(setup):
    resp = requests.delete(f"{host}/books/0")

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "cannot be <= 0" in resp.json()["error"]


def test_post_no_data(setup):
    headers = {"Content-Type": "multipart/form-data"}
    resp = requests.post(f"{host}/books", headers=headers)

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "No file provided" in resp.json()["error"]


def test_post_wrong_media_type(setup):
    headers = {"Content-Type": "application/xml"}
    resp = requests.post(f"{host}/books", headers=headers)

    assert resp.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert (
        "Only multipart/form-data and application/json allowed" in resp.json()["error"]
    )


def test_post_empty_wrong_media_type(setup):
    headers = {"Content-Type": "application/xml"}
    resp = requests.post(f"{host}/books/empty", headers=headers)

    assert resp.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert "Only application/json allowed" in resp.json()["error"]


def test_post_empty_invalid_data(setup):
    headers = {"Content-Type": "application/json"}
    payload = {"title": 1}
    resp = requests.post(f"{host}/books/empty", json=payload, headers=headers)

    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "1 is not of type 'string'" in resp.json()["errors"][0]["title"]
