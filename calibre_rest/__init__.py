import logging

from flask import Flask

from calibre_rest.calibre import CalibreWrapper
from config import config_map

LOG_FORMAT = "%(asctime)s %(name)s - %(levelname)s - %(message)s"


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
