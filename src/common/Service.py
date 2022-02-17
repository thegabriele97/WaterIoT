import copy
import time

from enum import Enum
from common.Endpoint import *

class ServiceType(Enum):
    SERVICE = 1
    DEVICE  = 2

class ServiceSubType(Enum):
    RASPBERRY = 1


class Service:
    def __init__(self, name: str, stype: ServiceType, host: str = None, port: int = None, subtype: ServiceSubType = None) -> None:
        self.name = name
        self.stype = stype
        self.subtype = subtype
        self.host = host
        self.port = port
        self.timestamp = time.time() 
        self.endpoints = {
            EndpointType.MQTT.name: {},
            EndpointType.REST.name: {}
        }

        if not (stype == ServiceType.SERVICE != subtype is None):
            raise ValueError("type and subtype error")

    def addEndpoint(self, endpoint: Endpoint):

        if self.stype == ServiceType.SERVICE and endpoint.subType is not EndpointTypeSub.GENERAL:
            raise ValueError(f"A {ServiceType.SERVICE} endpoint can't be of a subtype different from {EndpointTypeSub.GENERAL}")

        if endpoint.uri is None or len(endpoint.uri) <= 0 or (endpoint.endpointType == EndpointType.REST and endpoint.uri[0] != '/'):
            raise ValueError("uri is not valid")

        if endpoint.endpointType == EndpointType.REST and (self.host is None or self.port is None):
            raise ValueError("Host and Port not specified for REST endpoints")

        self.endpoints[endpoint.endpointType.name][endpoint.uri] = endpoint

    def toDict(self):
        
        d = copy.deepcopy(self.__dict__)
        d["stype"] = d["stype"].name
        d["subtype"] = d["subtype"].name if isinstance(d["subtype"], ServiceSubType) else None
        d["endpoints"][EndpointType.REST.name] = {
            "host": self.host,
            "port": self.port,
            "list": [e.toDict(True) for e in d["endpoints"][EndpointType.REST.name].values()]
        }

        d.pop("host")
        d.pop("port")

        return d
