from collections import namedtuple
import logging
from tempfile import NamedTemporaryFile
import requests

from common.SettingsNode import SettingsNode
from common.Service import EndpointType

class CatalogRequest:

    def __init__(self, logger: logging, settings: SettingsNode) -> None:
        self._logger = logger
        self._settings = settings
        self._catalogURL = f"http://{self._settings.catalog.host}:{self._settings.catalog.port}"


    def reqREST(self, service: str, path: str):
        """
        path must include absolute path with params
        ie. /calculator/sum?a=2&b=3
        """

        b1 = False
        b2 = False
        b3 = False
        jsonresp = None
        coderesp = None

        RetType = namedtuple("RetType", "status json_response code_response")

        try:
            self._logger.debug(f"Requesting service info @ {self._catalogURL}/catalog/services/{service}")
            r = requests.get(url=f"{self._catalogURL}/catalog/services/{service}")
            jsonresp = r.json()
            coderesp = r.status_code

            if r.status_code != 200:
                r.raise_for_status()

            data: dict = r.json()
            if not data["online"]:
                raise Exception(f"Service {service} is not online")

            host = dict(data["service"]["endpoints"][EndpointType.REST.name]).get("host", None)
            port = dict(data["service"]["endpoints"][EndpointType.REST.name]).get("port", None)

            if host is None or port is None:
                raise Exception("Service Host or Port not available from catalog")

            b1 = True
            lists_raw = data["service"]["endpoints"][EndpointType.REST.name]["list"]
            endpoint = [v for v in lists_raw if v["uri"] == path.split('?')[0]]
            endpoint = endpoint[0] if len(endpoint) > 0 else None
            if endpoint is None:
                raise Exception(f"Endpoint {path.split('?')[0]} not listed by the Service")

            b2 = True
            Param = namedtuple("Params", "required used")
            params_path = path.split('?')[1].split('&') if len(path.split('?')) > 1 else []
            params_path = {v[0]: v[1] for v in [v.split("=") for v in params_path]}
            params = {v["name"]: Param(v["required"], v["name"] in params_path) for v in endpoint["params"]}

            for pn, psr in params.items():
                if psr.required and not psr.used:
                    raise Exception(f"Some required params are not included in the request: {pn}")

            b3 = True
            if path[0] != '/':
                raise Exception(f"The specified path doesn't start with a '/'")

            self._logger.debug(f"Requesting service endpoint @ http://{host}:{str(port)}{path}")
            r = requests.get(url=f"http://{host}:{str(port)}{path}")
            jsonresp = r.json()
            coderesp = r.status_code
            
        except Exception as e:
            self._logger.error(f"Catalog request error: {str(e)}")
        
        finally:
            self._logger.debug(f"Service {b1}. Endpoint {b2}. Params {b3}")
            return RetType(b1 and b2 and b3, jsonresp, coderesp)

