from flask import Flask

from calibre import CalibreWrapper
from config import config_map


def create_app(config_name="default"):
    app = Flask(__name__)

    cfg = app.config
    cfg.from_object(config_map[config_name])
    # cfg.from_envvar("CALIBRE_REST_CONFIG")

    cfg["CALIBREDB"] = CalibreWrapper(
        app.config["CALIBREDB_PATH"], app.config["LIBRARY_PATH"]
    )

    with app.app_context():
        import routes

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
