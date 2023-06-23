import os

basedir = os.path.abspath(os.path.dirname(__file__))
# LOG = ["debug", "info", "error"]


class Config:
    TESTING = False
    CALIBREDB_PATH = os.environ.get("CALIBREDB_PATH", "/opt/calibre/calibredb")
    LIBRARY_PATH = os.environ.get("CALIBRE_LIBRARY", "./library")
    LOG_LEVEL = os.environ.get("CALIBRE_LOG", "INFO")


class DevConfig(Config):
    LOG_LEVEL = "DEBUG"


class TestConfig(Config):
    TESTING = True
    CALIBREDB_PATH = os.environ.get("CALIBREDB_TEST_PATH", "./calibre/calibredb")
    LIBRARY_PATH = os.environ.get("CALIBRE_TEST_LIBRARY", "./library")


class ProdConfig(Config):
    pass


config_map = {
    "dev": DevConfig,
    "test": TestConfig,
    "prod": ProdConfig,
    "default": DevConfig,
}
