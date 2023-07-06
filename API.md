# API

All endpoints are wrappers for `calibredb`
[subcommands](https://manual.calibre-ebook.com/generated/en/calibredb.html).

* [GET Book](#get-book)
* [GET Books](#get-books)
* [POST Book](#post-book)
* [POST Empty Book](#post-empty-book)
* [PUT Book](#put-book)
* [DELETE Book](#delete-book)

<h3 id="get-book">GET <code>/books/{id}</code></h3>

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
    * `books` - A single book object

```json
{
    "books": {
        "author_sort": "Tchaikovsky, Adrian",
        "authors": "Adrian Tchaikovsky",
        "cover": "/books/Adrian Tchaikovsky/Children of Time (1)/cover.jpg",
        "formats": [
            "/books/Adrian Tchaikovsky/Children of Time (1)/Children of Time - Adrian Tchaikovsky.epub"
        ],
        "id": 1,
        "identifiers": {
            "isbn10": "1447273281"
        },
        "isbn": "9781447273288",
        "languages": ["eng"],
        "last_modified": "2023-05-16T06:19:44+00:00",
        "pubdate": "2015-06-04T00:00:00+00:00",
        "publisher": "Tor Books",
        "series": "Children of Time",
        "series_index": 1.0,
        "size": 518137,
        "tags": [
            "Science Fiction",
            "Aliens",
            "Uplift",
            "First Contact"
        ],
        "template": "TEMPLATE ERROR 'NoneType' object has no attribute 'startswith'",
        "timestamp": "2022-10-28T07:43:27+00:00",
        "title": "Children of Time",
        "uuid": "89076f50-09a9-4384-867a-4e58491f7f22"
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

<h3 id="get-books">GET <code>/books/</code></h3>

<details>

<summary>
Returns JSON data of multiple books.
</summary>

#### Request

* Methods: `GET`
* Headers: `Accept: application/json`

##### Query Parameters

* `start` (optional) - Offset index for pagination, defaults to 1.
* `limit` (optional) - Limit on the number of results to return, defaults to 20.

```bash
# page 2 of results
$ curl localhost:5000/books?start=11&limit=10
```

* `sort` (optional) - Sort results by given field, defaults to ascending `id`.
  Supports descending sort by prepending with hyphen `-`.

```bash
# sort by descending id
$ curl localhost:5000/books?sort=-id

# sort by descending title and tags
$ curl localhost:5000/books?sort=-title&sort=tags
```

* `search` (optional) - Search query string that supports [Calibre's search
  interface](https://manual.calibre-ebook.com/en/gui.html#the-search-interface).
  <!-- For more advanced search queries, refer to `POST /books/search` -->

```bash
# simple title search
$ curl localhost:5000/books?search=title:foobar

# equality search for the tag "fiction"
$ curl --get --data-urlencode "search=tags:=fiction" localhost:5000/books
```

See examples for more.

#### Responses

##### Success

* Code: `200 OK`
* Content:
    * `books`: List of books returned
    * `metadata`:
        * `count`: Total count of all results (unpaginated)
        * `self`: Current page's query
        * `prev`: Previous page's query
        * `next`: Next page's query

```json
{
    "books": [
        {
            "author_sort": "Tchaikovsky, Adrian",
            "authors": "Adrian Tchaikovsky",
            "cover": "/books/Adrian Tchaikovsky/Children of Time (1)/cover.jpg",
            "formats": [
                "/books/Adrian Tchaikovsky/Children of Time (1)/Children of Time - Adrian Tchaikovsky.epub"
            ],
            "id": 1,
            "identifiers": {
                "isbn10": "1447273281"
            },
            "isbn": "9781447273288",
            "languages": ["eng"],
            "last_modified": "2023-05-16T06:19:44+00:00",
            "pubdate": "2015-06-04T00:00:00+00:00",
            "publisher": "Tor Books",
            "series": "Children of Time",
            "series_index": 1.0,
            "size": 518137,
            "tags": [
                "Science Fiction",
                "Aliens",
                "Uplift",
                "First Contact"
            ],
            "template": "TEMPLATE ERROR 'NoneType' object has no attribute 'startswith'",
            "timestamp": "2022-10-28T07:43:27+00:00",
            "title": "Children of Time",
            "uuid": "89076f50-09a9-4384-867a-4e58491f7f22"
        }
    ],
    "metadata": {
        "start": 1,
        "limit": 10,
        "count": 100,
        "self": "/books?start=1&limit=10&search=title:~^foo",
        "prev": "",
        "next": "/books?start=11&limit=10&search=title:~^foo"
    }
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

* Condition: `start` is more than number of returned results
* Code: `400 Bad Request`
* Content:

```json
{
    "error": "400 Bad Request: 100 is larger than number of books 5"
}
```

<details>

<summary>
    Examples
</summary>
<br>

Curl

```bash
# search for tags fiction and title foo
$ curl localhost:5000/books?search=tags:fiction&search=title:foo

# boolean search
$ curl --get --data-urlencode "search=title:'foo or bar'" localhost:5000/books

# regex
$ curl --get --data-urlencode "search=title:~^foo.*bar$" localhost:5000/books
```

Python

```python
import requests

params = {"search": "title: 'foo or bar'"}
# or
params = {"search": "title:~^foo.*bar$"}

resp = requests.get("localhost:5000/books", params=params)
```

</details>
<br>

[Return to top](#)
</details>

<h3 id="post-book">POST <code>/books/</code></h3>

<details>

<summary>
    Create book(s) with file(s) and JSON data
</summary>

#### Request

* Methods: `POST`
* Headers: `Content-Type: multipart/form-data`
* Data: File(s) and optional JSON data

##### File

* File must have a [valid ebook
  extension](https://manual.calibre-ebook.com/faq.html#what-formats-does-calibre-support-conversion-to-from).
* Filename cannot start with hyphen `-`.
* Multiple files are supported.

>**NOTE**: When POST-ing multiple files with JSON data, all new entries will be
>created with same metadata. This will fail unless `automerge=new_record` is
>included.

##### JSON Data

* The following keys are supported:

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
>library as a result of using `automerge=new_record`, and we add another
>instance of the same file with `automerge=overwrite`, the new file would
>overwrite ALL existing entries with the same file in the library.

#### Responses

##### Success

* Code: `201 CREATED`
* Content:
    * `id`: List of ids of added or overwritten book(s).

```json
{
    "id": ["2"]
}
```

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
# single file
$ curl -X POST -H "Content-Type:multipart/form-data" --form "file=@foo.epub" http://localhost:5000/books

# multiple files
$ curl -X POST --H "Content-Type: multipart/form-data" --form "file=@bar.epub" --form "file=@foo.epub" http://localhost:5000/books

# file and JSON data
$ curl -X POST --H "Content-Type: multipart/form-data" --form "data=data.json" --form "file=@foo.epub" http://localhost:5000/books
```

Python
```python
import requests

# single file
files = {"file": open("foo.epub", "rb")}

# multiple files (file key does not matter)
files = [
    ("file", open("test.txt", "rb")),
    ("other", open("foo.txt", "rb")),
]

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

<h3 id="post-empty-book">POST <code>/books/empty</code></h3>
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
    * `id`: List of ids of added or overwritten book(s).

```json
{
    "id": ["2"]
}
```

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

<h3 id="put-book">PUT <code>/books/{id}</code></h3>

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
    * `books` - Updated book object

```json
{
    "books": {
        "author_sort": "Tchaikovsky, Adrian",
        "authors": "Adrian Tchaikovsky",
        "cover": "/books/Adrian Tchaikovsky/Children of Time (1)/cover.jpg",
        "formats": [
            "/books/Adrian Tchaikovsky/Children of Time (1)/Children of Time - Adrian Tchaikovsky.epub"
        ],
        "id": 1,
        "identifiers": {
            "isbn10": "1447273281"
        },
        "isbn": "9781447273288",
        "languages": ["eng"],
        "last_modified": "2023-05-16T06:19:44+00:00",
        "pubdate": "2015-06-04T00:00:00+00:00",
        "publisher": "Tor Books",
        "series": "Children of Time",
        "series_index": 1.0,
        "size": 518137,
        "tags": [
            "Science Fiction",
            "Aliens",
            "Uplift",
            "First Contact"
        ],
        "template": "TEMPLATE ERROR 'NoneType' object has no attribute 'startswith'",
        "timestamp": "2022-10-28T07:43:27+00:00",
        "title": "Children of Time",
        "uuid": "89076f50-09a9-4384-867a-4e58491f7f22"
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

<h3 id="delete-book">DELETE <code>/books/{id}</code></h3>

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
