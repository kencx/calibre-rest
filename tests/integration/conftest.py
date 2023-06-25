import os
import shlex
import subprocess
import threading

import pytest
from werkzeug.serving import make_server

from calibre_rest import create_app
from config import TestConfig

TEST_CALIBREDB_PATH = os.path.abspath(TestConfig.CALIBREDB_PATH)
TEST_LIBRARY_PATH = os.path.abspath(TestConfig.LIBRARY_PATH)


class MockServer:
    """A development werkzeug server is started in test mode to serve API
    requests. It is initialized with a empty Calibre library.

    Upon completion (success or failure), the existing library is cloned to
    create a new empty library. The old library is deleted and replaced with the
    new empty library for future runs.

    Source: https://gist.github.com/eruvanos/f6f62edb368a20aaa880e12976620db8
    """

    def __init__(self, port=5000):
        self.thread = None
        self.app = create_app("test")
        self.server = make_server("localhost", port, app=self.app)

    def start(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.thread.join()


@pytest.fixture(scope="session")
def setup(prepare_test_library):
    """Setup test suite and teardown after."""

    server = MockServer()
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope="session")
def prepare_test_library(tmp_path_factory):
    """Prepare test library and test data."""

    library = tmp_path_factory.mktemp("library")
    out, err = calibredb_clone(TEST_LIBRARY_PATH, library)

    if not os.path.exists(os.path.join(library, "metadata.db")):
        raise FileNotFoundError("Library not initialized!")

    test_file = os.path.join(TEST_LIBRARY_PATH, "test.txt")
    if not os.path.exists(test_file):
        with open(test_file, "w") as file:
            file.write("hello world!")


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
