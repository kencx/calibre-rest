# calibre-rest

calibre-rest wraps
[calibredb](https://manual.calibre-ebook.com/generated/en/calibredb.html) to
provide a simple REST API server for your [Calibre](https://calibre-ebook.com/)
library.

### Disclaimer
- calibre-rest is in pre-alpha and subject to bugs and breaking changes. Please
use it at your own risk.
- This project has been tested on `amd64` Linux systems with Calibre 6.21 only.
- Contributions for testing and support on other OS platforms and Calibre versions
are greatly welcome.

calibre-rest is built with Flask and Gunicorn. See [API.md](API.md) for
documentation on all API endpoints.

## Install

calibre-rest requires the following dependencies:

- A Calibre library on the local filesystem or served by a [Calibre content
  server](https://manual.calibre-ebook.com/generated/en/calibre-server.html)
- Python >3.7 but Python 3.11 is recommended.
- The `calibre` binary with the `calibredb` executable.
- Calibre's system dependencies (on Linux):

```
$ apt-get install xdg-utils, xz-utils, libopengl0, libegl1
```

The latter two are only relevant if you wish to run calibre-rest directly on
your local machine.

### Docker

Docker is the recommended method to run calibre-rest. We ship two
images:

- `kencx/calibre_rest:[version]-app` packaged without the calibre binary
- `kencx/calibre_rest:[version]-calibre` packaged with the calibre binary

The former image assumes you have an existing Calibre binary installation on
your local machine, server or Docker container (how else did you run Calibre
previously?). The binary's directory must be bind mounted to the running
container:

```yaml
version: '3.6'
services:
  calibre_rest:
    image: ghcr.io/kencx/calibre_rest:0.1.0-app
    environment:
      - "CALIBRE_REST_LIBRARY=/library"
    ports:
      - 8080:80
    volumes:
      - "/opt/calibre:/opt/calibre"
      - "./library:/library"
```

Or when paired with an existing
[linuxserver/docker-calibre](https://github.com/linuxserver/docker-calibre)
instance:

```yml
version: '3.6'
services:
  calibre:
    image: lscr.io/linuxserver/calibre
    volumes:
      - "./calibre:/opt/calibre"
      - "./library:/library"

  calibre_rest:
    image: ghcr.io/kencx/calibre_rest:0.1.0-app
    environment:
      - "CALIBRE_REST_LIBRARY=/library"
    ports:
      - 8080:80
    volumes:
      - "./calibre:/opt/calibre"
      - "./library:/library"
```

Otherwise, the larger `kencx/calibre_rest:[version]-calibre` image ships with
its own Calibre binary and only requires access to your existing Calibre
library directory.

### Build from Source

To run calibre-rest on your local machine, Calibre and its dependencies must be installed:

```console
# clone the repository
$ git clone git@github.com:kencx/calibre_rest.git
$ cd calibre_rest && python3 -m venv .venv

# install Python dependencies
$ source .venv/bin/activate
$ python3 -m pip install -r requirements.txt

# install calibre
$ apt-get install xdg-utils, xz-utils, libopengl0, libegl1
$ wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sudo sh /dev/stdin
```

## Usage

Run the server with Docker:

```console
$ docker run \
    -v "/opt/calibre:/opt/calibre" \
    -v "./library:/library" \
    -p 8080:80 \
    -e "CALIBRE_REST_LIBRARY=/library" \
    ghcr.io/kencx/calibre_rest:0.1.0-app
```

or with [docker-compose](docker-compose.yml):

```console
$ docker compose up -d app
```

or directly on your local machine:

```console
$ python3 ./app.py -h

usage: app.py [options]

Options:
  -h, --help         show this help message and exit
  -d, --dev          Start in dev/debug mode
  -c, --calibre      Path to calibre binary directory
  -l, --library      Path to calibre library
  -u, --username     Calibre library username
  -p, --password     Calibre library password
  -b, --bind         Bind address HOST:PORT
  -g, --log-level    Log level
  -v, --version      Print version
```

calibre-rest can access any local Calibre libraries or remote [Calibre content
server](https://manual.calibre-ebook.com/generated/en/calibre-server.html)
instances.

For the latter, authentication must be enabled and configured.
For more information, refer to the [calibredb
documentation](https://manual.calibre-ebook.com/generated/en/calibredb.html).

### Configuration

The server can be configured with the following environment variables.

| Env Variable    | Description    | Type    | Default    |
|---------------- | --------------- | --------------- | --------------- |
| `CALIBRE_REST_PATH`    | Path to `calibredb` executable    | string | `/opt/calibre/calibredb` |
| `CALIBRE_REST_LIBRARY` | Path to calibre library   | string   | `./library`   |
| `CALIBRE_REST_USERNAME` | Calibre library username  | string  |  |
| `CALIBRE_REST_PASSWORD` | Calibre library password   | string  |  |
| `CALIBRE_REST_LOG_LEVEL` | Log Level | string  | `INFO`   |
| `CALIBRE_REST_ADDR` | Server bind address | string   | `localhost:5000` |

If running directly on your local machine, we can also use flags:

```console
$ ./app.py --bind localhost:5000
```

## Development

calibre-rest is built with Python 3.11 and Flask. Calibre should be installed to
facilitate testing.

To contribute, clone the repository and [build from source](#build-from-source).

```console
# install all dev dependencies
$ make pip.install

# run the dev server
$ make run.dev

# run tests
$ make test
```

## Roadmap

- [x] Support remote libraries
- [ ] Pagination
- [ ] TLS support
- [ ] Feature parity with `calibredb`
- [ ] S3 support
