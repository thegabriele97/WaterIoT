
from copy import deepcopy


class LinkItem:

    def __init__(self, name: str, arduinos: list[int] = None, raspberrys: list[int] = None) -> None:
        self._name = name
        self._arduinos = arduinos
        self._raspberrys = raspberrys

    @property
    def name(self) -> str:
        return self._name

    @property
    def arduinos(self) -> list[int]:
        return deepcopy(self._arduinos)

    @property
    def raspberrys(self) -> list[int]:
        return deepcopy(self._raspberrys)

