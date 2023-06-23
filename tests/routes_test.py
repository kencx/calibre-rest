from http import HTTPStatus


def test_version(app, client):
    app.mock_response("/health", {"version": "calibredb"})

    resp = client.get("/health")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json["version"]
