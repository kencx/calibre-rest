import os
import threading

import pytest
from werkzeug.serving import make_server

from calibre_rest import create_app


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

        @self.app.route("/alive", methods=["GET"])
        def alive():
            return "True"

    def start(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.thread.join()


@pytest.fixture(scope="session")
def setup():
    """Setup test suite."""
    server = MockServer()
    prepare_testdata(library=server.app.config["LIBRARY_PATH"])

    server.start()
    yield server

    # cleanup()
    server.stop()


def prepare_testdata(library):
    """Prepare test data:

    * check metadata.db file in empty library
    * test.txt file
    * small.epub file
    """
    if not os.path.exists(os.path.join(library, "metadata.db")):
        raise FileNotFoundError("Library not initialized!")
