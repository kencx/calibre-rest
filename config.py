import logging
import os


class Config:
    LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]

    __config = {
        "calibredb": os.environ.get("CALIBRE_REST_PATH", "/opt/calibre/calibredb"),
        "library": os.environ.get("CALIBRE_REST_LIBRARY", "/library"),
        "bind_addr": os.environ.get("CALIBRE_REST_ADDR", "localhost:5000"),
        "username": os.environ.get("CALIBRE_REST_USERNAME", ""),
        "password": os.environ.get("CALIBRE_REST_PASSWORD", ""),
        "log_level": os.environ.get("CALIBRE_REST_LOG_LEVEL", "INFO"),
        "debug": False,
        "testing": False,
    }
    __setters = [
        "calibredb",
        "library",
        "bind_addr",
        "username",
        "password",
        "log_level",
        "debug",
        "testing",
    ]

    @staticmethod
    def config():
        return Config.__config

    @staticmethod
    def get(key):
        return Config.__config[key]

    @staticmethod
    def set(key, value):
        if key in Config.__setters:
            if key == "log_level":
                if value not in Config.LOG_LEVELS:
                    logging.warning(
                        f'Log level "{value}" not supported. Setting log level to "INFO"'
                    )
                    Config.__config[key] = "INFO"
                    return

            Config.__config[key] = value
        else:
            raise NameError(f'Key "{key}" not accepted in Config')


class DevConfig(Config):
    def __init__(
        self,
        calibredb=None,
        library=None,
        bind_addr=None,
        username=None,
        password=None,
        log_level=None,
    ):
        for k, v in locals().items():
            if v is not None and k != "self":
                Config.set(k, v)

        Config.set("log_level", os.environ.get("CALIBRE_REST_LOG_LEVEL", "DEBUG"))
        Config.set("debug", True)


class TestConfig(Config):
    def __init__(self, calibredb=None, library=None, bind_addr=None):
        for k, v in locals().items():
            if v is not None and k != "self":
                Config.set(k, v)

        Config.set("testing", True)


class ProdConfig(Config):
    def __init__(
        self,
        calibredb=None,
        library=None,
        bind_addr=None,
        username=None,
        password=None,
        log_level=None,
    ):
        for k, v in locals().items():
            if v is not None and k != "self":
                Config.set(k, v)
