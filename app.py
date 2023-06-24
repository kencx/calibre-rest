#!/usr/bin/env python3

import argparse

from gunicorn.app.base import BaseApplication

from calibre_rest import create_app
from config import ProdConfig


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Start Gunicorn server")
    parser.add_argument("-b", "--bind", required=False, type=str, help="Bind address")
    args = parser.parse_args()

    bind = args.bind or ProdConfig.BIND_ADDRESS
    g = GunicornApp(create_app("prod"), bind=bind)
    g.run()
