import os
import re
import shlex
import subprocess
import threading
from urllib.parse import urlparse

import pytest
from werkzeug.serving import make_server

from calibre_rest import create_app
from config import TestConfig

TEST_CALIBREDB_PATH = os.environ.get("CALIBRE_REST_TEST_PATH", "./calibre/calibredb")
TEST_LIBRARY_PATH = os.environ.get(
    "CALIBRE_REST_TEST_LIBRARY", "./tests/integration/testdata"
)
TEST_BIND_ADDR = os.environ.get("CALIBRE_REST_TEST_ADDR", "localhost:5000")


class MockServer:
    """A development werkzeug server is started in test mode to serve API
    requests. It is initialized with a empty Calibre library.

    Upon completion (success or failure), the existing library is cloned to
    create a new empty library. The old library is deleted and replaced with the
    new empty library for future runs.

    Source: https://gist.github.com/eruvanos/f6f62edb368a20aaa880e12976620db8
    """

    def __init__(self, library):
        self.thread = None

        # urlparse only recognizes netloc if prepended with "//"
        self.bind_addr = TEST_BIND_ADDR
        if re.match(r"^https?://", self.bind_addr) is None:
            self.bind_addr = "http://" + self.bind_addr

        url = urlparse(self.bind_addr, scheme="http")
        self.app = create_app(
            TestConfig(
                calibredb=TEST_CALIBREDB_PATH, library=library, bind_addr=url.netloc
            )
        )
        self.server = make_server(url.hostname, url.port, app=self.app)

    def start(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.thread.join()


@pytest.fixture(scope="session")
def setup(tmp_path_factory, autouse=True):
    """Setup test suite and teardown after."""

    library = tmp_path_factory.mktemp("library")
    out, err = calibredb_clone(TEST_LIBRARY_PATH, library)

    if not os.path.exists(os.path.join(library, "metadata.db")):
        raise FileNotFoundError("Library not initialized!")

    test_file = os.path.join(TEST_LIBRARY_PATH, "test.txt")
    if not os.path.exists(test_file):
        with open(test_file, "w") as file:
            file.write("hello world!")

    # if not os.path.exists(TEST_LIBRARY_PATH / "foo.epub"):
    #     raise FileNotFoundError("foo.epub not present!")

    server = MockServer(library=library)
    server.start()
    yield server
    server.stop()


@pytest.fixture()
def url(setup):
    """Return server URL"""
    return setup.bind_addr


def calibredb_clone(library, new_library) -> (str, str):
    """Clone calibre library."""

    cmd = f"{TEST_CALIBREDB_PATH} --with-library {library} clone {new_library}"

    try:
        process = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            check=True,
            text=True,
            encoding="utf-8",
            env=None,
            timeout=None,
        )
    except FileNotFoundError as err:
        raise FileNotFoundError(f"Executable could not be found.\n\n{err}") from err

    return process.stdout, process.stderr
