import logging
from signal import SIGTERM, signal
import sys
import time

from common.ServiceApp import ServiceApp

class App(ServiceApp):
    def __init__(self) -> None:
        super().__init__(log_stdout_level=logging.INFO, log_filename="out.log")

        self.logger.info("Init!")

        signal(SIGTERM, lambda: sys.exit(0))
        while 1:
            time.sleep(1)


if __name__ == "__main__":
    App()
