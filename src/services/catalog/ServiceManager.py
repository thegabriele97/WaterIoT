import copy
import logging

from threading import Thread, Lock, Event
from time import sleep, time

from common.SettingsNode import SettingsNode
from common.Service import Service

class ServiceManager:

    def __init__(self, settings: SettingsNode, logger: logging) -> None:
        self._settings = settings
        self._logger = logger
        self._services = dict[str, Service]()
        self._dead_services = dict[str, Service]()
        self._lock = Lock()
        self._th1_evtstop = Event()

        self._th1 = Thread(target=self._thread_cleaner, name="ServiceManager: Thread Cleaner")

    def _thread_cleaner(self):

        self._logger.info("Catalog Watchdog started")

        while not self._th1_evtstop.is_set():
            sleep(self._settings.watchdog.timeout_ms / 1e3)
            self._lock.acquire()
            tm = time()

            for s in copy.deepcopy(self._services).values():
                self._logger.debug(f"Watchdog: checking {s.name}")
                if tm - s.timestamp >= self._settings.watchdog.expire_sec:
                    dead = self._services.pop(s.name)
                    self._dead_services[dead.name] = dead
                    self._logger.info(f"Service {s.name} expired")

            self._lock.release()

    def run_watchdog(self):
        self._th1_evtstop.clear()
        self._th1.start()

    def stop_watchdog(self):
        self._th1_evtstop.set()
        self._th1.join()
        self._logger.info("Catalog Watchdog stopped")

    def add_service(self, service: Service):
        self._lock.acquire()
        self._dead_services.pop(service.name, None)
        self._services[service.name] = service
        service.updateTimestamp()
        self._lock.release()

    @property
    def services(self):
        self._lock.acquire()
        l = copy.deepcopy(self._services)
        self._lock.release()

        return l

    @property
    def dead_services(self):
        self._lock.acquire()
        l = copy.deepcopy(self._dead_services)
        self._lock.release()

        return l

