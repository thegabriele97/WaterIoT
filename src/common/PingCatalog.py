
import logging
import requests

from common.Service import *
from common.WIOThread import WIOThread

class PingCatalog:

    def __init__(self, service: Service, catalogHost: str, catalogPort: int, ping_time_ms: int, logger: logging) -> None:

        self._service = service
        self._catalogHost = catalogHost
        self._catalogPort = catalogPort
        self._ping_time_ms = ping_time_ms        
        self._logger = logger

        self._th = WIOThread(target=self._thread_pinger, name="PingCatalog: Thread Pinger")

    def _thread_pinger(self):
        self._logger.info("Catalog Pinger started")

        time.sleep(0.5)
        while not self._th.is_stop_requested:

            self._logger.debug(f"Sending ping to Catalog {self._catalogHost}:{self._catalogPort}")

            try:
                r = requests.put(f"http://{self._catalogHost}:{self._catalogPort}/catalog/services", json=self._service.toDict())

                if r.status_code != 200:
                    r.raise_for_status()
            except Exception as e:
                self._logger.error(f"Unable to send ping: {str(e)}")

            self._th.wait(self._ping_time_ms / 1e3)

    def run(self):
        self._th.run()

    def stop(self):
        self._th.stop()
        self._logger.info("Catalog Pinger stopped")

