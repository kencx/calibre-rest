import logging

from flask import Flask
from gunicorn.app.base import BaseApplication

from calibre_rest.calibre import CalibreWrapper
from config import config_map

__version__ = "0.1.0"

LOG_FORMAT = "%(asctime)s %(name)s - %(levelname)s - %(message)s"


class GunicornApp(BaseApplication):
    defaults = {
        "bind": "localhost:5000",
        # calibredb supports only one operation at any single time. Increasing
        # the number of workers would result in concurrent execution errors.
        "workers": 1,
        "backlog": 100,
        "worker_class": "sync",
        "timeout": 30,
        "keepalive": 2,
        "spew": False,
        "daemon": False,
        "raw_env": [],
        "pidfile": "/tmp/gunicorn_vm_api.pid",
        "umask": 755,
        "user": 1000,
        "group": 1000,
        "tmp_upload_directory": None,
        # Log errors to stdout
        "error_log": "-",
        "access_log": "-",
    }

    def __init__(self, app, **kwargs):
        self.options = {**self.defaults, **kwargs}
        self.app = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.app


def create_app(config_name="default"):
    app = Flask(__name__)

    cfg = app.config
    cfg.from_object(config_map[config_name])

    # attach gunicorn handlers if exist
    flog = app.logger
    gunicorn_handlers = logging.getLogger("gunicorn").handlers
    flog.handlers.extend(gunicorn_handlers)
    flog.setLevel(cfg["LOG_LEVEL"])

    try:
        cdb = CalibreWrapper(
            app.config["CALIBREDB_PATH"],
            app.config["LIBRARY_PATH"],
            app.config["CALIBREDB_USERNAME"],
            app.config["CALIBREDB_PASSWORD"],
            flog,
        )
        cdb.check()
        cfg["CALIBREDB"] = cdb
    except FileNotFoundError as exc:
        # exit immediately if fail to initialize wrapper object
        raise SystemExit(exc)

    with app.app_context():
        import calibre_rest.routes  # noqa: F401

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
