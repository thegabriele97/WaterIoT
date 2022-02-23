import logging
import json

class RESTBase:
    exposed = True

    def __init__(self, upperRESTSrvcApp: object, indent_lvl: int) -> None:
        self._upperRESTSrvcApp = upperRESTSrvcApp;

    def asjson(self, data: dict):
        return data

    def asjson_error(self, data):
        return {"error": data}
    
    def asjson_info(self, data):
        return {"info": data}

    @property
    def logger(self) -> logging.Logger:
        return self._getattribute("logger");

    def _getattribute(self, name: str):
        return getattr(self._upperRESTSrvcApp, name)