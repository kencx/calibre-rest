import json
import tempfile
from os import path

from flask import abort
from flask import current_app as app
from flask import jsonify, make_response, request
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

from calibre_rest.errors import ValidationError
from calibre_rest.models import Book

calibredb = app.config["CALIBREDB"]


@app.route("/health")
def version():
    return response(200, jsonify(version=calibredb.version()))


@app.route("/books/<int:id>")
def get_book(id):
    book = calibredb.get_book(id)
    if not book:
        abort(404, f"book {id} does not exist")

    return response(200, jsonify(books=book))


# TODO list with sort, filter search, pagination
@app.route("/books")
def get_books():
    per_page = request.args.get("per_page")

    if per_page:
        books = calibredb.get_books(limit=int(per_page))
    else:
        books = calibredb.get_books()

    if not len(books):
        return response(204, jsonify(books=[]))

    return response(200, jsonify(books=books))


@app.route("/books", methods=["POST"])
def add_book():
    """method: POST
    headers:
        Content-Type: enctype=multipart/form-data
    data:
        file: /path/to/file
        data: Optional JSON data
    """

    if "file" not in request.files:
        abort(400, "No files")

    file = request.files["file"]
    if file and file.filename == "":
        abort(400, "No file provided")

    if not allowed_file(file.filename):
        abort(400, "File extension not allowed")

    # save file to a temporary location for upload
    tempdir = tempfile.gettempdir()
    tempfilepath = path.join(tempdir, secure_filename(file.filename))
    file.save(tempfilepath)

    if not path.isfile(tempfilepath):
        abort(500)

    # extract optional json data
    data = request.form.get("data")
    book = {}

    if data is not None:
        json_data = json.loads(data)

        # TODO Validate schema and init Book object
        book = Book(**json_data).serialize()

    id = calibredb.add(tempfilepath, **book)
    return response(201, jsonify(added_id=id))


@app.route("/books/empty", methods=["POST"])
def add_empty_book():
    """method: POST
    headers:
        Content-Type: application/json
    """
    # validate input

    id = calibredb.add_empty()
    return response(201, jsonify(id=id))


@app.route("/books/<int:id>", methods=["PUT"])
def update_book(id):
    """method: POST
    headers:
        Content-Type: application/json
    """
    # validate input

    data = request.get_json() or {}
    calibredb.set_metadata(id, None, data)


@app.route("/books/<int:id>", methods=["DELETE"])
def delete_book(id):
    # calibredb remove does not return any useful output
    calibredb.remove([id])

    # check if book still exists
    book = calibredb.get_book(id)
    if book:
        abort(500, f"book {id} was not deleted")

    return response(200, "")


# export
@app.route("/export/<int:id>")
def export_book(id):
    pass


# export --all
@app.route("/export")
def export_books():
    pass


@app.errorhandler(HTTPException)
def handle_http_error(e):
    return jsonify(error=str(e)), e.code


# TODO Input data validation:
#  - multiple validation errors
#  - missing required data
#  - redundant data fields
#  - JSON parse error
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify(error=str(e)), e.code


@app.errorhandler(TimeoutError)
def handle_timeout_error(e):
    return jsonify(error=str(e)), 500


def response(status_code, data, headers={"Content-Type": "application/json"}):
    response = make_response(data, status_code)

    for k, v in headers.items():
        response.headers[k] = v

    return response


def allowed_file(filename: str) -> bool:
    return True
