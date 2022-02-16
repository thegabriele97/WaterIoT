import logging
import json

class RESTBase:
    exposed = True

    def __init__(self, upperRESTSrvcApp: object, indent_lvl: int) -> None:
        self._upperRESTSrvcApp = upperRESTSrvcApp;

    def asjson(self, data: dict):
        return json.dumps(data, indent=4)

    def asjson_error(self, data):
        return json.dumps({"error": data}, indent=4)
    
    def asjson_info(self, data):
        return json.dumps({"info": data}, indent=4)

    @property
    def logger(self) -> logging.Logger:
        return self._getattribute("logger");

    def _getattribute(self, name: str):
        return getattr(self._upperRESTSrvcApp, name)