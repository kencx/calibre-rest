import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    TESTING = False
    CALIBREDB_PATH = os.environ.get("CALIBRE_REST_PATH", "/opt/calibre/calibredb")
    LIBRARY_PATH = os.environ.get("CALIBRE_REST_LIBRARY", "./library")
    CALIBREDB_USERNAME = os.environ.get("CALIBRE_REST_USERNAME", "")
    CALIBREDB_PASSWORD = os.environ.get("CALIBRE_REST_PASSWORD", "")
    LOG_LEVEL = os.environ.get("CALIBRE_REST_LOG_LEVEL", "INFO")
    BIND_ADDRESS = os.environ.get("CALIBRE_REST_ADDR", "localhost:5000")


class DevConfig(Config):
    LOG_LEVEL = "DEBUG"


class TestConfig(Config):
    TESTING = True
    CALIBREDB_PATH = os.environ.get("CALIBRE_REST_TEST_PATH", "./calibre/calibredb")
    LIBRARY_PATH = os.environ.get("CALIBRE_REST_TEST_LIBRARY", "./library")
    BIND_ADDRESS = os.environ.get("CALIBRE_REST_ADDR", "0.0.0.0:5000")


class ProdConfig(Config):
    pass


config_map = {
    "dev": DevConfig,
    "test": TestConfig,
    "prod": ProdConfig,
    "default": DevConfig,
}
