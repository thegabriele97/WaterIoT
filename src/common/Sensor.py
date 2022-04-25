
import time


class Sensor:

    def __init__(self, name, value, unit, devid):
        self._name = name
        self._value = value
        self._unit = unit
        self._devid = devid

    @property
    def JSON(self):

        return {
            "n": self._name,
            "u": self._unit,
            "v": self._value,
            "t": time.time(),
            "i": self._devid
        }