import os

basedir = os.path.abspath(os.path.dirname(__file__))
# LOG = ["debug", "info", "error"]


class Config:
    TESTING = True
    CALIBREDB_PATH = os.environ.get("CALIBREDB_PATH", "./calibre-bin/calibredb")
    LIBRARY_PATH = os.environ.get("CALIBRE_LIBRARY", "./library")
    LOG_LEVEL = os.environ.get("CALIBRE_LOG", "INFO")


class DevConfig(Config):
    LOG_LEVEL = "DEBUG"


class ProdConfig(Config):
    TESTING = False


config_map = {
    "dev": DevConfig,
    "prod": ProdConfig,
    "default": DevConfig,
}
