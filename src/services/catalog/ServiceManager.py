import copy
import logging

from threading import Lock
from time import sleep, time

from common.SettingsNode import SettingsNode
from common.Service import Service
from common.WIOThread import WIOThread

class ServiceManager:

    def __init__(self, settings: SettingsNode, logger: logging) -> None:
        self._settings = settings
        self._logger = logger
        self._services = dict[str, Service]()
        self._dead_services = dict[str, Service]()
        self._lock = Lock()

        self._th1 = WIOThread(target=self._thread_cleaner, name="ServiceManager: Thread Cleaner")

    def _thread_cleaner(self):

        self._logger.info("Catalog Watchdog started")

        sleep(0.5)
        while not self._th1.is_stop_requested:
            self._lock.acquire()
            tm = time()

            for s in copy.deepcopy(self._services).values():
                self._logger.debug(f"Watchdog: checking {s.name}")
                if tm - s.timestamp >= self._settings.watchdog.expire_sec:
                    dead = self._services.pop(s.name)
                    self._dead_services[dead.name] = dead
                    self._logger.warn(f"Service {s.name} expired")

            self._lock.release()
            self._th1.wait(self._settings.watchdog.timeout_ms / 1e3)

    def run_watchdog(self):
        self._th1.run()

    def stop_watchdog(self):
        self._th1.stop()
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

