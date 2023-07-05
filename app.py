#!/usr/bin/env python3

import argparse

from calibre_rest import GunicornApp, __version__, create_app
from config import DevConfig, ProdConfig

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Start calibre-rest server")
    parser.add_argument(
        "-d",
        "--dev",
        required=False,
        action="store_true",
        help="Start in dev/debug mode",
    )
    parser.add_argument(
        "-c",
        "--calibre",
        required=False,
        type=str,
        help="Path to calibre binary directory",
    )
    parser.add_argument(
        "-l", "--library", required=False, type=str, help="Path to calibre library"
    )
    parser.add_argument(
        "-u", "--username", required=False, type=str, help="Calibre library username"
    )
    parser.add_argument(
        "-p", "--password", required=False, type=str, help="Calibre library password"
    )
    parser.add_argument(
        "-g",
        "--log-level",
        default="INFO",
        choices=DevConfig.LOG_LEVELS,
        required=False,
        type=str,
        dest="log_level",
        help="Log level",
    )
    parser.add_argument(
        "-b", "--bind", required=False, type=str, help="Bind address HOST:PORT"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"v{__version__}",
        help="Print version",
    )
    args = parser.parse_args()

    if args.dev:
        app_config = DevConfig(
            calibredb=args.calibre,
            library=args.library,
            bind_addr=args.bind,
            username=args.username,
            password=args.password,
            log_level=args.log_level,
        )
        app = create_app(app_config)
        app.run()

    else:
        app_config = ProdConfig(
            calibredb=args.calibre,
            library=args.library,
            bind_addr=args.bind,
            username=args.username,
            password=args.password,
            log_level=args.log_level,
        )
        g = GunicornApp(app_config)
        g.run()
