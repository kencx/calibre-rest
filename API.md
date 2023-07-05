# API

All endpoints are wrappers for `calibredb`
[subcommands](https://manual.calibre-ebook.com/generated/en/calibredb.html).

* [Get Book](#get-book)
* [Create Book](#create-book)
* [Update Book](#update-book)
* [Delete Book](#delete-book)

### GET <code>/books/{id}</code>

<details>

<summary>
Returns JSON data of a single book
</summary>

#### Request

* Methods: `GET`
* Parameters: `id > 0`
* Headers: `Accept: application/json`

#### Responses

##### Success

* Code: `200 OK`
* Content:

```json
{
    "books": {
        "author_sort": "Doe, John",
        "authors": "John Doe",
        "formats": [
            "/library/John Doe/foo (1)/foo - John Doe.txt"
        ],
        "id": 1,
        "identifiers": {},
        "isbn": "",
        "languages": [],
        "last_modified": "2023-06-30T13:45:49+00:00",
        "pubdate": "0101-01-01T00:00:00+00:00",
        "series_index": 1.0,
        "size": 10,
        "tags": [],
        "template": "TEMPLATE ERROR 'NoneType' object has no attribute 'startswith'",
        "timestamp": "2023-06-30T13:45:49+00:00",
        "title": "foo",
        "uuid": "4cba90c5-ea7b-43d2-adf8-092f45ed1ff5"
    }
}
```

##### Error

* Code: `404 Not Found`
* Content:

```json
{
    "error": "404 Not Found: book 1 does not exist"
}
```

* Code: `400 Bad Request`
* Content:

```json
{
    "error": "400 Bad Request: id cannot be <= 0"
}
```

<details>
<summary>
    Examples
</summary>
<br>

Curl
```console
$ curl localhost:5000/books/1
```

Python
```python
import requests

resp = requests.get("localhost:5000/books/1")
```
</details>

<br>

[Return to top](#)
</details>

### GET <code>/books</code>

<details>

<summary>
Returns JSON data of multiple books.
</summary>

### Request

* Methods: `GET`
* Parameters:
    - `before_id`
    - `after_id`
    - `per_page`
    - `sort`
    - `search`

* Headers: `Accept: application/json`

#### Responses

##### Success

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

##### Error

<details>

<summary>
    Examples
</summary>
<br>

Curl

```console
$ curl localhost:5000/books
```

</details>
<br>

[Return to top](#)
</details>

### POST <code>/books</code>

<details>

<summary>
    Create book with file and JSON data
</summary>

#### Request

##### File Only

* Methods: `POST`
* Headers: `Content-Type: multipart/form-data`
* Data:
    * A file with a [valid ebook
      extension](https://manual.calibre-ebook.com/faq.html#what-formats-does-calibre-support-conversion-to-from).
      Filename cannot start with hyphen `-`.

##### File and JSON Data

* Methods: `POST`
* Headers: `Content-Type: multipart/form-data`
* Data:
    * A file with a valid ebook extension. Filename cannot start with hyphen
      `-`.
    * JSON data with the following OPTIONAL keys:

```json
{
    "authors": "[array of strings]",
    "cover": "[string]",
    "identifiers": "[object of key-value strings]",
    "isbn": "[string]",
    "languages": "[array of strings]",
    "series": "[string]",
    "series_index": "float >= 0",
    "tags": "[array of strings]",
    "title": "[string]",
    "automerge": "[ignore|overwrite|new_record]"
}
```

**Automerge**

The `automerge` key modifies the behaviour of calibredb when a book is found to
already exist in the library.

* `automerge=ignore` (default): Ignore the duplicate and return a 409 Conflict
  error. This will not add any new records or files.
* `automerge=overwrite`: Overwrite the existing file with the new file, leaving
  only a single record.
* `automerge=new_record` Create a new record entirely. This will result in two
  different records.

>**NOTE**: If the same file is uploaded with different JSON metadata,
>a new record will be created, regardless of the value given to `automerge`.

>**NOTE**: If the same file exists across multiple different entries in the same
>library, as a result of using `automerge=new_record`, and we add another
>instance of the same file with `automerge=overwrite`, the new file would
>overwrite ALL existing entries with the same file in the library.

#### Responses

##### Success

* Code: `201 CREATED`
* Content:

```json
{
    "id": ["2"]
}
```

The `id` of the added or overwritten books.

##### Error

* Condition: Incorrect headers
* Code: `415 Unsupported Media Type`
* Content:

```json
{
    "error": "Unsupported Media Type: Only multipart/form-data allowed"
}
```

* Condition: File data failed validation, e.g. Filename not supported
* Code: `422 Unprocessable Entity`
* Content:

```json
{
    "error": "400 Bad Request: Invalid filename (foo.abc)"
}
```

* Condition: JSON data failed validation
* Code: `422 Unprocessable Entity`
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

<details>
<summary>
    Examples
</summary>
<br>

Curl

```console
# file only
$ curl -X POST -H "Content-Type:multipart/form-data" --form "file=@foo.epub" http://localhost:5000/books

# file and JSON data
$ curl -X POST --H "Content-Type: multipart/form-data" --form "data=data.json" --form "file=@foo.epub" http://localhost:5000/books
```

Python
```python
import requests

files = {"file": open("foo.epub", "rb")}
payload = {
    "authors": ["John Doe", "Ben Adams"],
    "identifiers": {"isbn": "abcd1234", "asin": "foobar123"},
    "title": "foo",
}

# The (optional) payload must be serialized into JSON and wrapped in a dict
# with the "data" key. This allows Flask to access it as form data with the
# correct key. The "json" argument cannot be used as it will attempt to set
# the Content-Type as "application/json", causing Flask's request.form to
# be empty.
resp = requests.post(
    "localhost:5000/books",
    files=files,
    data={"data": json.dumps(payload)},
)
```
</details>
<br>

[Return to top](#)
</details>

### POST <code>/books/empty</code>
<details>

<summary>
    Create empty book with JSON data.
</summary>

#### Request

* Methods: `POST`
* Headers: `Content-Type: multipart/form-data`
* Data:
    * JSON data with the following OPTIONAL keys:

```json
{
    "authors": "[array of strings]",
    "cover": "[string]",
    "identifiers": "[object of key-value strings]",
    "isbn": "[string]",
    "languages": "[array of strings]",
    "series": "[string]",
    "series_index": "float >= 0",
    "tags": "[array of strings]",
    "title": "[string]",
    "automerge": "[ignore|overwrite|new_record]"
}
```

**Automerge**

The `automerge` key modifies the behaviour of calibredb when a book is found to
already exist in the library.

* `automerge=ignore` (default): Ignore the duplicate and return a 409 Conflict
  error. This will not add any new records or files.
* `automerge=overwrite`: Overwrite the existing file with the new file, leaving
  only a single record.
* `automerge=new_record` Create a new record entirely. This will result in two
  different records.

>**NOTE**: If the same file is uploaded with different JSON metadata,
>a new record will be created, regardless of the value given to `automerge`.

#### Responses

##### Success

* Code: `201 CREATED`
* Content:

```json
{
    "id": ["2"]
}
```

The `id` of the added or overwritten books.

##### Error

* Condition: Incorrect headers
* Code: `415 Unsupported Media Type`
* Content:

```json
{
    "error": "Unsupported Media Type: Only application/json allowed"
}
```

* Condition: JSON data failed validation
* Code: `422 Unprocessable Entity`
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

<details>
<summary>
    Examples
</summary>
<br>

Curl

```console
# file only
$ curl -X POST -H "application/json" --data-binary=@foo.json http://localhost:5000/books/empty
```

Python
```python
import requests
payload = {
    "authors": ["John Doe", "Ben Adams"],
    "identifiers": {"isbn": "abcd1234", "asin": "foobar123"},
    "title": "foo",
}
resp = requests.post("localhost:5000/books/empty", json=payload)
```
</details>
<br>

[Return to top](#)
</details>

### PUT <code>/books/{id}</code>

<details>

<summary>
    Update book with JSON data
</summary>

#### Request

* Methods: `PUT`
* Parameters: `id > 0`
* Headers: `Content-Type: application/json`
* Data:
    * JSON data with the following OPTIONAL keys:

```json
{
    "authors": "[array of strings]",
    "author_sort": "[string]",
    "comments": "[string]",
    "id": "integer >= 0",
    "identifiers": "[object of key-value strings]",
    "isbn": "[string]",
    "languages": "[array of strings]",
    "pubdate": "[string]",
    "publisher": "[string]",
    "rating": "[string]",
    "series": "[string]",
    "series_index": "float >= 0",
    "size": "integer >= 0",
    "tags": "[array of strings]",
    "timestamp": "[string]",
    "title": "[string]"
}
```
>It is not recommended to modify the id and timestamp of the book.

#### Responses

##### Success

* Code: `200 OK`
* Content:

```json
{
    "books": {
        "author_sort": "Doe, John",
        "authors": "John Doe",
        "formats": [
            "/library/John Doe/foo (1)/foo - John Doe.txt"
        ],
        "id": 1,
        "identifiers": {},
        "isbn": "",
        "languages": [],
        "last_modified": "2023-06-30T13:45:49+00:00",
        "pubdate": "0101-01-01T00:00:00+00:00",
        "series_index": 1.0,
        "size": 10,
        "tags": [],
        "template": "TEMPLATE ERROR 'NoneType' object has no attribute 'startswith'",
        "timestamp": "2023-06-30T13:45:49+00:00",
        "title": "foo",
        "uuid": "4cba90c5-ea7b-43d2-adf8-092f45ed1ff5"
    }
}
```

##### Error

* Condition: Book does not exist
* Code: `404 Not Found`
* Content:

```json
{
    "error": "404 Not Found: book 1 does not exist"
}
```

* Condition: id is invalid
* Code: `400 Bad Request`
* Content:

```json
{
    "error": "400 Bad Request: id cannot be <= 0"
}
```


* Condition: JSON data failed validation
* Code: `422 Unprocessable Entity`
* Content:

```json
{
    "errors": [
        {"languages": "1 is not of type string"},
        {"series_index": "-2 is less than the minimum of 0.0"}
    ]
}
```

<details>
<summary>
    Examples
</summary>
<br>

Curl
```console
$ curl -X PUT --H "Content-Type: application/json" --data-binary=@data.json http://localhost:5000/books/1
```

Python
```python
import requests

payload = {
    "authors": ["John Doe", "Ben Adams"],
    "identifiers": {"isbn": "abcd1234", "asin": "foobar123"},
    "title": "foo",
}
resp = requests.put("localhost:5000/books/1", json=payload)
```
</details>
<br>

[Return to top](#)
</details>

### DELETE <code>/books/{id}</code>

<details>

<summary>
    Delete book with id
</summary>

#### Request

* Methods: `DELETE`
* Parameters: `id > 0`

#### Responses

##### Success

* Code: `200 OK`
* Data: Empty response

##### Error

* Condition: id is invalid
* Code: `400 Bad Request`
* Content:

```json
{
    "error": "400 Bad Request: id cannot be <= 0"
}
```

* Condition: Book was not deleted
* Code: `500 Internal Server Error`
* Content:

```json
{
    "error": "500 Internal Server Error: book 1 was not deleted"
}
```

<details>
<summary>
    Examples
</summary>
<br>

Curl

```console
$ curl -X DELETE http://localhost:5000/books/1
```

Python

```python
import requests

resp = requests.delete("localhost:5000/books/1")
```
</details>
<br>

[Return to top](#)
</details>
