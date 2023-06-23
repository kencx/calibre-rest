# API

All endpoints are wrappers for `calibredb`
[subcommands](https://manual.calibre-ebook.com/generated/en/calibredb.html).

* [Get Book](#get-book)
* [Create Book](#create-book)
* [Update Book](#update-book)
* [Delete Book](#delete-book)

### Get Book

<details>

<summary>
    GET <code>/books/{id}</code>
</summary>
<br>
Returns JSON data of a single book.

### Request

* Methods: `GET`
* Parameters: `id > 0 (integer)`
* Headers: `Accept: application/json`

### Responses

#### Success

* Code: `200 OK`
* Content:

```json
{
    "books": {
        "authors": "John Doe",
        "title": "foobar"
    }
}
```

#### Error

* Code: `404 Not Found`
* Content:

```json
{
    "error": "404 Not Found: book 1 does not exist",
}
```

### Example

```console
$ curl localhost:5000/books/1
```
[Return to top](#)
</details>

### Get Books

<details>

<summary>
    GET <code>/books</code>
</summary>
<br>
Returns JSON data of multiple books.

### Request

* Methods: `GET`
* Parameters:
    - `before_id`
    - `after_id`
    - `per_page`
    - `sort`
    - `search`

* Headers: `Accept: application/json`

### Responses

#### Success

* Code: `200 OK`
* Content:

```json
{
    "books": [
        {
            "authors": "John Doe",
            "title": "foobar"
        }
    ]
}
```

* Code: `204 No Content`
* Content:

```json
{
    "books": []
}
```

#### Error

### Example

```console
$ curl localhost:5000/books
```
[Return to top](#)
</details>

### Create Book

<details>

<summary>
    POST <code>/books</code>
</summary>
<br>
Create book with file and/or JSON data.

### Request

#### File Only

* Methods: `POST`
* Headers: `Content-Type: multipart/form-data`
* Data: `form: file=@file`

**File**

* [Valid ebook
  extension](https://manual.calibre-ebook.com/faq.html#what-formats-does-calibre-support-conversion-to-from).
* Filename cannot start with hyphen `-`.

#### File and JSON Data

* Methods: `POST`
* Headers: `Content-Type: multipart/form-data`
* Data: `form: file=@file data=data.json`

```json
{
    "automerge": "[ignore|overwrite|new_record]"
}
```

**Automerge**

* ignore (default) - Ignore when existing book found, returning a 409 Conflict error.
* overwrite - Overwrite existing book.
* new_record - Creates a new record.

### Responses

#### Success

* Code: `201 OK`
* Content:

```json
{
    "added_id": "2"
}
```

The `id` of the added book.

#### Error

* Condition: Incorrect headers
* Code: `415 Unsupported Media Type`
* Content:

```json
{
    "error": "Unsupported Media Type: Only multipart/form-data and application/json allowed"
}
```

* Condition: File data failed validation, e.g. Filename not supported
* Code: `400 Bad Request`
* Content:

```json
{
    "error": "400 Bad Request: Invalid filename (foo.abc)"
}
```

* Condition: JSON data failed validation
* Code: `400 Bad Request`
* Content:

```json
{
    "errors": [
        {"languages": "1 is not of type string"},
        {"series_index": "-2 is less than the minimum of 0.0"}
    ]
}
```

* Condition: Book already exists
* Code: `409 Conflict`
* Content:

```json
{
    "error": "Book /tmp/foo.epub already exists. Include automerge=overwrite to overwrite."
}
```

### Example

```console
# file only
$ curl -X POST -H "Content-Type:multipart/form-data" --form "file=@foo.epub" http://localhost:5000/books

# file and JSON data
$ curl -X POST --H "Content-Type: multipart/form-data" --form "data=data.json" --form "file=@foo.epub" http://localhost:5000/books
```
[Return to top](#)
</details>

<details>

<summary>
    POST <code>/books/empty</code>
</summary>
<br>
Create empty book with JSON data.

### Request

* Methods: `POST`
* Headers: `Content-Type: application/json`
* Data: `data.json`

```json
{
    "automerge": "[ignore|overwrite|new_record]"
}
```

**Automerge**

* ignore (default) - Ignore when existing book found, returning a 409 Conflict error.
* overwrite - Overwrite existing book.
* new_record - Creates a new record.

### Responses

#### Success

* Code: `201 OK`
* Content:

```json
{
    "added_id": "2"
}
```

The `id` of the added book.

#### Error

* Condition: Incorrect headers
* Code: `415 Unsupported Media Type`
* Content:

```json
{
    "error": "Unsupported Media Type: Only application/json allowed"
}
```

* Condition: JSON data failed validation
* Code: `400 Bad Request`
* Content:

```json
{
    "errors": [
        {"languages": "1 is not of type string"},
        {"series_index": "-2 is less than the minimum of 0.0"}
    ]
}
```

* Condition: Book already exists
* Code: `409 Conflict`
* Content:

```json
{
    "error": "Book already exists. Include automerge=overwrite to overwrite."
}
```

### Example

```console
# file only
$ curl -X POST -H "application/json" --data-binary=@foo.json http://localhost:5000/books/empty
```
[Return to top](#)
</details>

### Update Book

<details>

<summary>
    PUT <code>/books/{id}</code>
</summary>
<br>
Update book with file or JSON data.

### Request

#### File Only

* Methods: `PUT`
* Parameters: `id > 0 (integer)`
* Headers: `Content-Type: multipart/form-data`
* Data: `form: file=@file`

#### JSON Data

* Methods: `PUT`
* Parameters: `id > 0 (integer)`
* Headers: `Content-Type: application/json`
* Data: `data.json`

### Responses

#### Success

* Code: `200 OK`
* Content:

```json
{
    "books": {
        "title": "foobar"
    }
}
```

#### Error

* Condition: JSON data failed validation
* Code: `400 Bad Request`
* Content:

```json
{
    "errors": [
        {"languages": "1 is not of type string"},
        {"series_index": "-2 is less than the minimum of 0.0"}
    ]
}
```

* Condition: File data failed validation, e.g. Filename not supported
* Code: `400 Bad Request`
* Content:

```json
{
    "error": "400 Bad Request: Invalid filename (foo.abc)"
}
```

### Example

```console
# file only
$ curl -X PUT -H "Content-Type:multipart/form-data" --form "file=@foo.epub" http://localhost:5000/books

# JSON data
$ curl -X PUT --H "Content-Type: application/json" --data-binary=@data.json http://localhost:5000/books
```
[Return to top](#)
</details>

### Delete Book

<details>

<summary>
    DELETE <code>/books/{id}</code>
</summary>
<br>
Delete book with id.

### Request

* Methods: `DELETE`
* Parameters: `id > 0 (integer)`
* Headers: `Accept: application/json`

### Responses

#### Success

* Code: `200 OK`
* Data: Empty response

#### Error

### Example

```console
$ curl -X DELETE http://localhost:5000/books/1
```

[Return to top](#)
</details>
