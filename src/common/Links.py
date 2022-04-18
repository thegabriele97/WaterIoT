
from copy import deepcopy
from common.LinkItem import LinkItem

class Links:

    def __init__(self, data: list = None) -> None:

        if data is not None:
            # check type correctness
            if not isinstance(data, list):
                raise TypeError("data must be a list of LinkItem")
            
            if not all("name" in item.keys() and item["name"] is not None and isinstance(item["name"], str) for item in data):
                raise TypeError("data must be a list of LinkItem with non-empty name as str")

            if not all("arduinos" in item.keys() and item["arduinos"] is not None and isinstance(item["arduinos"], list) for item in data):
                raise TypeError("data must be a list of LinkItem with list of device ids named arduinos")

            if not all("raspberrys" in item.keys() and item["raspberrys"] is not None and isinstance(item["raspberrys"], list) for item in data):
                raise TypeError("data must be a list of LinkItem with list of device ids named raspberrys")

        self._data = [LinkItem(e["name"], e["arduinos"], e["raspberrys"]) for e in data] if data is not None else []

    def getAllArduinosLinksFromRaspberryId(self, id: int) -> set[int]:

        b = set()
        for e in [link.arduinos for link in self._data if id in link.raspberrys]:
            print(f"e: {e}")
            for i in e:
                b.add(i)

        return b

    def removeLink(self, name: str, raspberry: int = None, arduino: int = None):

        if raspberry is None and arduino is None:
            for i, e in enumerate(self._data):
                if e.name == name:
                    self._data.pop(i)
                    return

            raise Exception(f"LinkItem.removeLink: {name} not found")

        raspberry = int(raspberry)
        arduino = int(arduino)

        for i, e in enumerate(self._data):
            if e.name == name:

                # if (len(e.raspberrys) == 1 and len(e.arduinos) > 1) or (len(e.raspberrys) > 1 and len(e.arduinos) == 1):
                    # raise ValueError(f"Link {name} has a one-to-many relation. You can't remove a device from it.")

                e.removeLink(raspberry, arduino)
                return

    def addLink(self, name: str, raspberry: int, arduino: int):

        raspberry = int(raspberry)
        arduino = int(arduino)

        for i, e in enumerate(self._data):
            if e.name == name:
                e.addLink(raspberry, arduino)
                return

    def createLink(self, name: str):
            
            for i, e in enumerate(self._data):
                if e.name == name:
                    return
    
            self._data.append(LinkItem(name))

    def toDict(self):
        return [e.toDict() for e in self._data]

    @property
    def data(self) -> list[LinkItem]:
        return deepcopy(self._data)
