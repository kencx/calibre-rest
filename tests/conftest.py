import os

import pytest

from calibre_rest.calibre import CalibreWrapper
from config import config_map


@pytest.fixture()
def calibre():
    test_config = config_map["test"]

    if os.path.exists(test_config.CALIBREDB_PATH) and os.path.exists(
        test_config.LIBRARY_PATH
    ):
        return CalibreWrapper(test_config.CALIBREDB_PATH, test_config.LIBRARY_PATH)
    else:
        pytest.skip("calibredb not installed")
