
from threading import Thread, Event

class WIOThread:

    def __init__(self, target, name: str = None) -> None:
        
        self._evtstop = Event()
        self._evtstart = Event()
        self._th = Thread(target=self._thread_fnc, name=name)
        self._target = target

    def _thread_fnc(self):

        self._evtstart.set()
        while not self._evtstop.is_set():
            self._target()

    def run(self):
        self._evtstop.clear()
        self._evtstart.clear()
        self._th.start()

    def stop(self):

        if not self._evtstart.is_set():
            return

        self._evtstop.set()
        self._th.join()

    def wait(self, delay_seconds):
        self._evtstop.wait(delay_seconds)

    @property
    def is_stop_requested(self) -> bool:
        return self._evtstop.is_set()
