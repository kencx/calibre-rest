from flask import abort
from flask import current_app as app
from flask import jsonify, request
from werkzeug.http import HTTP_STATUS_CODES

calibredb = app.config["CALIBREDB"]


@app.route("/health")
def version():
    return jsonify({"version": calibredb.version()[0]})


@app.route("/books/<int:id>")
def get_book(id):
    if id <= 0:
        bad_request(f"id {id} not supported")

    book = calibredb.get_book(id)
    if not book:
        abort(404, description="Resource not found")

    return jsonify(book)


# list with sort, filter search, pagination
@app.route("/books")
def get_books():
    pass


@app.route("/books", methods=["POST"])
def add_book():
    pass


@app.route("/books/empty", methods=["POST"])
def add_empty_book():
    pass


@app.route("/books/<int:id>", methods=["PUT"])
def update_book(id):
    if id <= 0:
        bad_request(f"id {id} not supported")

    data = request.get_json() or {}
    calibredb.set_metadata(id, None, data)


@app.route("/books/<int:id>", methods=["DELETE"])
def delete_book(id):
    if id <= 0:
        bad_request(f"id {id} not supported")

    calibredb.remove([id])


# export
@app.route("/export/<int:id>")
def export_book(id):
    pass


# export --all
@app.route("/export")
def export_books():
    pass


def error_response(status_code, message=None):
    resp = {"error": HTTP_STATUS_CODES.get(status_code, "Unknown Error")}
    if message:
        resp["message"] = message

    resp = jsonify(resp)
    resp.status_code = status_code
    return resp


@app.errorhandler(400)
def bad_request(message):
    return jsonify(error=str(message)), 400


@app.errorhandler(404)
def resource_not_found(message):
    return jsonify(error=str(message)), 404
