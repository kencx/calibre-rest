from http import HTTPStatus

import requests

host = "http://localhost:5000"


def test_version(setup):
    resp = requests.get(f"{host}/health")

    assert resp.status_code == HTTPStatus.OK
