
import logging
import requests

from common.Service import *
from threading import Thread, Event

class PingCatalog:

    def __init__(self, service: Service, catalogHost: str, catalogPort: int, ping_time_ms: int, logger: logging) -> None:

        self._service = service
        self._catalogHost = catalogHost
        self._catalogPort = catalogPort
        self._ping_time_ms = ping_time_ms        
        self._logger = logger

        self._th1_evtstop = Event()
        self._th1_evtstart = Event()
        self._th1 = Thread(target=self._thread_pinger, name="PingCatalog: Thread Pinger")

    def _thread_pinger(self):
        self._logger.info("Catalog Pinger started")
        self._th1_evtstart.set()

        time.sleep(0.5)
        while not self._th1_evtstop.is_set():

            self._logger.debug(f"Sending ping to Catalog {self._catalogHost}:{self._catalogPort}")

            try:
                r = requests.put(f"http://{self._catalogHost}:{self._catalogPort}/catalog/services", json=self._service.toDict())

                if r.status_code != 200:
                    r.raise_for_status()
            except Exception as e:
                self._logger.error(f"Unable to send ping: {str(e)}")

            self._th1_evtstop.wait(self._ping_time_ms / 1e3)

    def run(self):
        self._th1_evtstop.clear()
        self._th1_evtstart.clear()
        self._th1.start()

    def stop(self):

        if not self._th1_evtstart.is_set():
            return

        self._th1_evtstop.set()
        self._th1.join()
        self._logger.info("Catalog Pinger stopped")

