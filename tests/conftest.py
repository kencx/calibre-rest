import os
from uuid import uuid4

import pytest
from flask import Flask, jsonify

from calibre_rest import create_app
from calibre_rest.calibre import CalibreWrapper
from config import config_map


# https://gist.github.com/eruvanos/f6f62edb368a20aaa880e12976620db8
class MockServer:
    """Flask server wrapper to mock JSON responses in various endpoints"""

    def __init__(self, app: Flask):
        self.app = app

    def _add_callback_response(self, url: str, callback, methods=("GET",)):
        # unique name
        callback.__name__ = str(uuid4())
        self.app.add_url_rule(url, view_func=callback, methods=methods)

    def mock_response(self, url: str, data: dict = None, methods=("GET",)):
        def callback():
            if data:
                return jsonify(data)

        self._add_callback_response(url, callback, methods=methods)

    def test_client(self):
        return self.app.test_client()


@pytest.fixture()
def calibre():
    test_config = config_map["test"]

    if os.path.exists(test_config.CALIBREDB_PATH) and os.path.exists(
        test_config.LIBRARY_PATH
    ):
        return CalibreWrapper(test_config.CALIBREDB_PATH, test_config.LIBRARY_PATH)
    else:
        pytest.skip("calibredb not installed")


@pytest.fixture()
def app():
    app = create_app("test")
    yield MockServer(app)


@pytest.fixture()
def client(app):
    return app.test_client()
