import copy
from enum import Enum

class EndpointType(Enum):
    MQTT = 1
    REST = 2

class EndpointTypeSub(Enum):
    GENERAL  = 1
    RESOURCE = 2

class EndpointParam:

    def __init__(self, name: str, required: bool = True) -> None:
        self.name = name
        self.required = required

    def toDict(self):
        return self.__dict__

class Endpoint:

    def __init__(self, uri: str, endpointType: EndpointType, subType: EndpointTypeSub = EndpointTypeSub.GENERAL, params: list[EndpointParam] = []) -> None:
        self.uri = uri
        self.endpointType = endpointType
        self.subType = subType
        self.params = params

    def toDict(self, remType: bool):

        d = copy.deepcopy(self.__dict__)
        d["endpointType"] = self.endpointType.name
        d["subType"] = self.subType.name
        d["params"] = [e.toDict() for e in d["params"]]

        if remType:
            d.pop("endpointType")

        return d
