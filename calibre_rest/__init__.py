import logging

from flask import Flask

from calibre_rest.calibre import CalibreWrapper
from config import config_map


def create_app(config_name="default"):
    app = Flask(__name__)

    cfg = app.config
    cfg.from_object(config_map[config_name])
    # cfg.from_envvar("CALIBRE_REST_CONFIG")

    # attach gunicorn handlers if exist
    flog = app.logger
    gunicorn_handlers = logging.getLogger("gunicorn").handlers
    flog.handlers.extend(gunicorn_handlers)
    flog.setLevel(cfg["LOG_LEVEL"])

    try:
        cfg["CALIBREDB"] = CalibreWrapper(
            app.config["CALIBREDB_PATH"], app.config["LIBRARY_PATH"], flog
        )
    except FileNotFoundError as exc:
        # exit immediately if fail to initialize wrapper object
        raise SystemExit(exc)

    with app.app_context():
        import calibre_rest.routes

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
