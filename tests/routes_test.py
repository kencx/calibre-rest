from http import HTTPStatus


def test_version(app, client):
    app.mock_response("/health", {"version": "calibredb"})

    resp = client.get("/health")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json["version"]


def test_get_book(app, client):
    id = 1
    app.mock_response(f"/books/{str(id)}", {"book": "hello"})

    resp = client.get(f"/books/{str(id)}")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json["book"] == "hello"


def test_get_books(app, client):
    app.mock_response("/books")
    client.get("/books")


def test_add_book(app, client):
    app.mock_response("/books/empty", data={"book": "hello"}, methods=("POST",))
    client.post("/books", json={"book": "hello"})


def test_add_empty_book(app, client):
    app.mock_response("/books/empty", data={"book": "hello"}, methods=("POST",))
    client.post("/books/empty", json={"book": "hello"})


def test_update_book(app, client):
    id = 1
    app.mock_response(f"/books/{str(id)}", methods=("PUT",))
    client.put(f"/books/{str(id)}")


def test_delete_book(app, client):
    id = 1
    app.mock_response(f"/books/{str(id)}", methods=("DELETE",))
    client.delete(f"/books/{str(id)}")
