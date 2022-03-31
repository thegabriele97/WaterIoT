
from threading import Thread, Event

class WIOThread:

    def __init__(self, target, name: str = None) -> None:
        
        self._evtrestart = Event()
        self._evtcompletestop = Event()
        self._evtstart = Event()
        self._th = Thread(target=self._thread_fnc, name=name)
        self._target = target

    def _thread_fnc(self):

        while not self._evtcompletestop.is_set():

            self._evtrestart.clear()
            self._evtstart.set()

            while not self._evtrestart.is_set():
                self._target()

    def restart(self):

        if not self._evtstart.is_set():
            return

        self._evtstart.clear()
        self._evtrestart.set()
        self._evtstart.wait()

    def run(self):
        self._evtrestart.clear()
        self._evtcompletestop.clear()
        self._evtstart.clear()

        self._th.start()
        self._evtstart.wait()

    def stop(self):

        if not self._evtstart.is_set():
            return

        self._evtcompletestop.set()
        self._evtrestart.set()
        self._th.join()

    def wait(self, delay_seconds):
        self._evtrestart.wait(delay_seconds)

    @property
    def is_stop_requested(self) -> bool:
        return self._evtrestart.is_set()
