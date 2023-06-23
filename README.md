# calibre_rest

`calibre_rest` is an unofficial REST API wrapper for
[Calibre](https://calibre-ebook.com/). It combines the features of
[calibredb](https://manual.calibre-ebook.com/generated/en/calibredb.html) and
[calibre-server](https://manual.calibre-ebook.com/generated/en/calibre-server.html)
to provide a machine-readable interface for your Calibre library.

### Disclaimer
- calibre_rest is in pre-alpha and subject to bugs and breaking changes. Please
use it at your own risk.
- `calibre_rest` has been tested on the `amd64` Linux with Calibre 6.21 only.
- Contributions for testing and support on other OS platforms and Calibre versions
are greatly welcome.

## Install

`calibre_rest` wraps the `calibredb` executable to run subcommands on an
existing Calibre library. As such, the server requires access to an existing
`calibredb` executable on the local machine or a Docker container.

### Docker

Docker is the recommended method of running `calibre_rest`. We ship two
different images:

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

When paired with an existing
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

Otherwise, the larger `kencx/calibre_rest:[version]-calibre` image ships with its own Calibre
binary and you simply need to bind mount your existing Calibre library
directory.

### Build from Source

To run `calibre_rest` on your local machine, Calibre must be installed:

```console
# clone the repository
$ git clone git@github.com:kencx/calibre_rest.git
$ cd calibre_rest && python3 -m venv .venv

# install Python dependencies
$ source .venv/bin/activate
$ python3 -m pip install -r requirements.txt

# install calibre
$ wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sudo sh /dev/stdin
```

Start the server with env variables:

```console
$ export CALIBRE_REST_PATH=/opt/calibre/calibredb
$ export CALIBRE_REST_LIBRARY=/path/to/library
$ make run
```

## Usage

`calibre_rest` can access any local Calibre libraries or remote Calibre content
server instances. For the latter, authentication must be enabled and configured.
For more information, refer to the [calibredb
documentation](https://manual.calibre-ebook.com/generated/en/calibredb.html).

See [API.md](API.md) for reference.

## Development

`calibre_rest` is built with Python 3.11 and Flask.

Clone the repository and [build from source](#build-from-source).

Run the dev server:

```console
$ make run.dev
$ make test
```

## Roadmap

- [x] Support remote libraries
- [ ] Pagination
- [ ] TLS support
- [ ] Feature parity with `calibredb`
- [ ] S3 support
