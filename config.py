import os

basedir = os.path.abspath(os.path.dirname(__file__))
# LOG = ["debug", "info", "error"]


class Config:
    TESTING = False
    CALIBREDB_PATH = os.environ.get("CALIBRE_REST_PATH", "/opt/calibre/calibredb")
    LIBRARY_PATH = os.environ.get("CALIBRE_REST_LIBRARY", "./library")
    CALIBREDB_USERNAME = os.environ.get("CALIBRE_REST_USERNAME", "")
    CALIBREDB_PASSWORD = os.environ.get("CALIBRE_REST_PASSWORD", "")
    LOG_LEVEL = os.environ.get("CALIBRE_REST_LOG_LEVEL", "INFO")


class DevConfig(Config):
    LOG_LEVEL = "DEBUG"


class TestConfig(Config):
    TESTING = True
    CALIBREDB_PATH = os.environ.get("CALIBRE_REST_TEST_PATH", "./calibre/calibredb")
    LIBRARY_PATH = os.environ.get("CALIBRE_REST_TEST_LIBRARY", "./library")


class ProdConfig(Config):
    pass


config_map = {
    "dev": DevConfig,
    "test": TestConfig,
    "prod": ProdConfig,
    "default": DevConfig,
}
