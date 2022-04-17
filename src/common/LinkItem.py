
from copy import deepcopy


class LinkItem:

    def __init__(self, name: str, arduinos: list[int] = None, raspberrys: list[int] = None) -> None:
        self._name = name
        self._arduinos = arduinos
        self._raspberrys = raspberrys

    def removeLink(self, raspberry: int, arduino: int):

        # check one to many relation
        if len(self._raspberrys) == 1 and len(self._arduinos) > 1:
            self._arduinos.remove(arduino)
            return
        elif len(self._raspberrys) > 1 and len(self._arduinos) == 1:
            self._raspberrys.remove(raspberry)
            return

        if raspberry in self._raspberrys and arduino in self._arduinos:
            self._raspberrys.remove(raspberry)
            self._arduinos.remove(arduino)
            return

        raise Exception(f"LinkItem.removeLink: {raspberry} {arduino} not found")

    def addLink(self, raspberry: int, arduino: int):

        # check if link already exists
        if raspberry in self._raspberrys and arduino in self._arduinos:
            raise Exception(f"LinkItem.addLink: {raspberry} {arduino} already exists")

        # check if one side of the link already exists in the LinkItem
        if raspberry in self._raspberrys:
            self._arduinos.append(arduino)
            return
        elif arduino in self._arduinos:
            self._raspberrys.append(raspberry)
            return

        # create link
        self._raspberrys.append(raspberry)
        self._arduinos.append(arduino)

    def toDict(self):
        return {
            "name": self._name,
            "arduinos": self._arduinos,
            "raspberrys": self._raspberrys
        }

    @property
    def name(self) -> str:
        return self._name

    @property
    def arduinos(self) -> list[int]:
        return deepcopy(self._arduinos)

    @property
    def raspberrys(self) -> list[int]:
        return deepcopy(self._raspberrys)

