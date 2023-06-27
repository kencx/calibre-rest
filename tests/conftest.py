import os

import pytest

from calibre_rest.calibre import CalibreWrapper
from config import TestConfig


@pytest.fixture()
def calibre():
    test_config = TestConfig()
    calibredb = test_config.get("calibredb")
    library = test_config.get("library")

    if os.path.exists(calibredb) and os.path.exists(library):
        return CalibreWrapper(calibredb, library)
    else:
        pytest.skip("calibredb not installed")
