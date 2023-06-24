#!/usr/bin/env python3

import argparse

from calibre_rest import GunicornApp, create_app
from config import ProdConfig

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Start Gunicorn server")
    parser.add_argument("-b", "--bind", required=False, type=str, help="Bind address")
    args = parser.parse_args()

    bind = args.bind or ProdConfig.BIND_ADDRESS
    g = GunicornApp(create_app("prod"), bind=bind)
    g.run()
