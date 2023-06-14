#!/usr/bin/env python3

import configparser
import logging
import shutil
import subprocess


class Config:
    def __init__(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)

        self.cdb = config.get("default", "calibredb_path", fallback="calibredb")
        self.library = config.get("default", "library_path")


class Calibre:
    def __init__(self, calibredb_path, library_path):
        if not shutil.which(calibredb_path):
            print("calibredb not installed!")
            exit(1)

        self.cdb = calibredb_path
        self.library = library_path
        self.cdb_with_library = [calibredb_path, "--with-library", library_path]

    def _run(self, cmd):
        logging.debug(f"Running \"{' '.join(cmd)}\"")
        subprocess.run(cmd)

    def version(self):
        self._run(self.cdb.append("--version"))

    def list(self, limit):
        cmd = self.cdb_with_library + ["list", "--for-machine"]

        # TODO int or string?
        if limit:
            cmd += ["--limit", str(limit)]

        self._run(cmd)

    def add(self):
        pass

    def remove(self, ids, permanent=False):
        cmd = self.cdb.append("remove")
        if permanent:
            cmd.append("--permanent")

        self.run(cmd.append(",".join(map(str, ids))))

    # TODO xml/opf to json
    def show_metadata(self, id):
        pass

    def export(self):
        pass


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")

    config = Config("config.ini")
    c = Calibre(config.cdb, config.library)
    c.list(3)
