class CalibreRuntimeError(Exception):
    """Raise when calibredb command line execution returns a non-zero exit code"""

    def __init__(self, cmd, exit_code, stdout, stderr):
        self.cmd = cmd
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

        message = f"{cmd} exited with status {exit_code}.\n\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"

        super().__init__(message)


class NoItemsError(Exception):
    pass
