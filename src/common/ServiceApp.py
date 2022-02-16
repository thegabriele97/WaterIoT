import logging
from signal import SIGTERM, signal
import sys

class ServiceApp:

    # _formatstr: str = "%(asctime)s - %(app_name)s- %(levelname)s - %(message)s"
    _formatstr: str = "{asctime} {filename:>20s}:{lineno} {levelname:>8s}: {message}"
    _extra = {'app_name':'Super App'}

    def __init__(self, log_stdout_level: int = logging.INFO, log_filename: str = None) -> None:

        class CustomFormatter(logging.Formatter):

            grey = "\x1b[38;20m"
            yellow = "\x1b[33;20m"
            red = "\x1b[31;20m"
            bold_red = "\x1b[31;1m"
            reset = "\x1b[0m"
            format = self._formatstr

            FORMATS = {
                logging.DEBUG: grey + format + reset,
                logging.INFO: grey + format + reset,
                logging.WARNING: yellow + format + reset,
                logging.ERROR: red + format + reset,
                logging.CRITICAL: bold_red + format + reset
            }

            def format(self, record):
                log_fmt = self.FORMATS.get(record.levelno)
                formatter = logging.Formatter(log_fmt, style='{')
                return formatter.format(record)

        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)

        self._c_handler = logging.StreamHandler(stream=sys.stdout)
        self._c_handler.setLevel(log_stdout_level)
        self._c_handler.setFormatter(CustomFormatter())
        self._logger.addHandler(self._c_handler)

        if log_filename is not None:
            self._f_handler = logging.FileHandler(filename=log_filename)
            self._f_handler.setLevel(logging.NOTSET)
            self._f_handler.setFormatter(logging.Formatter(self._formatstr, style='{'))
            self._logger.addHandler(self._f_handler)


    @property
    def logger(self) -> logging.Logger:
        return self._logger
