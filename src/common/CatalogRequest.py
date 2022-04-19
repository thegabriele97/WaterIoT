from collections import namedtuple
import logging
import requests
import paho.mqtt.client as mqtt
import time

from requests.adapters import Retry, HTTPAdapter
from enum import Enum

from common.SettingsNode import SettingsNode
from common.Service import EndpointType

class RequestType(Enum):
    GET    = 1
    POST   = 2
    PUT    = 3
    DELETE = 4
    HEAD   = 5

class CatalogRequest:

    def __init__(self, logger: logging, settings: SettingsNode, on_connect = None, on_msg_recv = None) -> None:
        self._logger = logger
        self._settings = settings
        self._catalogURL = f"http://{self._settings.catalog.host}:{self._settings.catalog.port}"
        self._on_connect = on_connect
        self._on_msg_recv = on_msg_recv

        self._reqcache = {}
        self._mqttclient = mqtt.Client()
        self._mqttclient.enable_logger(self._logger)

        self._s = requests.Session()
        retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[ 500, 502, 503, 504 ])
        self._s.mount('http://', HTTPAdapter(max_retries=retries))

        self._mqttclient_connected = False


    def publishMQTT(self, service: str, path:str, payload, devid: int = None):
        if path[0] != '/':
            raise ValueError("Path must begin with a '/'")

        if not self._check_mqtt_endpoint(service, path, devid):
            raise ValueError(f"Trying to publish in a non published topic on the catalog for {service}")

        ap = f"/{devid}" if devid is not None and not path.startswith("/+") else ""
        self._mqttclient.publish(f"/{service}{ap}{path}", payload)
        self._logger.debug(f"MQTT published to /{service}{ap}{path}: {payload}")

    def subscribeMQTT(self, service: str, path: str, devid: int = None):

        if path[0] != '/':
            raise ValueError("Path must begin with a '/'")

        if not self._check_mqtt_endpoint(service, path, devid):
            raise ValueError(f"Trying to subscribe in a non published topic on the catalog for {service}")

        ap = f"/{devid}" if devid is not None and not path.startswith("/+") else ""
        self._mqttclient.subscribe(f"/{service}{ap}{path}")
        self._logger.debug(f"MQTT subscribed to /{service}{ap}{path}")

    def callbackOnTopic(self, service: str, path: str, callback, devid: int = None):

        if path[0] != '/':
            raise ValueError("Path must begin with a '/'")

        if not self._check_mqtt_endpoint(service, path, devid):
            raise ValueError(f"Trying to interact with a non published topic on the catalog for {service}")

        ap = f"/{devid}" if devid is not None and not path.startswith("/+") else ""
        self._mqttclient.message_callback_add(f"/{service}{ap}{path}", callback)

    def _check_mqtt_endpoint(self, service: str, path: str, devid: int = None):

        if not self._mqttclient_connected:
            self._mqttclient_connect()

        service = service.lower()
        rpath = f"{self._catalogURL}/catalog/services/{service}"
        self._logger.debug(f"Requesting MQTT ({path}, dev #{devid}) service info @ {rpath}")

        r = None
        for _ in range(0, 10):
            r = requests.get(url=rpath)
            if r.status_code == 404:
                time.sleep(0.5)
            elif r.status_code != 200:
                r.raise_for_status()
            else:
                break

        if r.status_code == 404 or r == None:
            raise Exception(f"{rpath} return status code 404")

        # checking if we are dealing with a multiple device
        if "services" in r.json():
            epoints_raw = [list(s["service"]["endpoints"][EndpointType.MQTT.name]) for s in r.json()["services"]]
            epoints_raw = [item for sublist in epoints_raw for item in sublist]
        else:
            epoints_raw = r.json()["service"]["endpoints"][EndpointType.MQTT.name]

        # if not r.json()["online"]:
        #     raise Exception(f"Service {service} is not online")
            
        ap = f"/{devid}" if devid is not None and not path.startswith("/+") else ""
        epoint = [e for e in epoints_raw if mqtt.topic_matches_sub(f"/{service}{ap}{path}", e["uri"])]

        return len(epoint) > 0

    def reqREST(self, service: str, path: str, reqt: RequestType = RequestType.GET, datarequest = None, devid: int = None, retry_on_fail_count: int = 3):
        """
        path must include absolute path with params
        ie. /calculator/sum?a=2&b=3
        """

        b1 = b2 = b3 = b4 = False
        jsonresp = None
        coderesp = None

        RetType = namedtuple("RetType", "status json_response code_response")
        CacheType = namedtuple("CacheType", "header response")
        service = service.lower()

        try:
            rpath = f"{self._catalogURL}/catalog/services/{service}" if devid is None else f"{self._catalogURL}/catalog/services/{service}?devid={devid}"
            self._logger.debug(f"Requesting REST service info @ {self._catalogURL}/catalog/services/{service}")

            if rpath in self._reqcache.keys():
                r = self._do_req(RequestType.HEAD, rpath)
                coderesp = r.status_code

                if r.status_code != 200:
                    r.raise_for_status()

                lastmodified = r.headers["Last-Modified"]
                expires = r.headers["Expires"]
                cache = (service, CacheType(self._reqcache[rpath][0], self._reqcache[rpath][1]))

                if expires != '0' and lastmodified == cache[1].header["Last-Modified"]:
                    self._logger.debug(f"Using cache for service {service}")
                    jsonresp = cache[1].response

            if jsonresp is None:

                r = self._do_req(RequestType.GET, rpath)
                jsonresp = r.json()
                coderesp = r.status_code

                if r.status_code != 200:
                    r.raise_for_status()

                self._reqcache[rpath] = CacheType(r.headers, r.json())

            data: dict = jsonresp
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

            self._logger.debug(f"Requesting service endpoint: {reqt.name} http://{host}:{str(port)}{path}")

            url = f"http://{host}:{str(port)}{path}"
            r = self._do_req(reqt, url, datarequest, max=4, doraise=False)
            b4 = True

            jsonresp = r.json()
            coderesp = r.status_code
            
        except Exception as e:
            self._logger.error(f"Catalog request error: {str(e)}")
        
        finally:
            self._logger.debug(f"Service {b1}. Endpoint {b2}. Params {b3}. Reachable {b4}")

            if (not b1 or not b2 or not b3 or not b4) and retry_on_fail_count > 0:
                self._logger.warning(f"Retrying request to service {service}:{path} ...")
                time.sleep(1)
                return self.reqREST(service, path, reqt, datarequest, devid, retry_on_fail_count - 1)

            return RetType(b1 and b2 and b3 and b4, jsonresp, coderesp)

    def reqDeviceIdsList(self, service: str) -> list[int]:
        """
        Returns a list of device ids for the given service
        """
        service = service.lower()
        rpath = f"{self._catalogURL}/catalog/services/{service}/ids"

        r = None
        for _ in range(0, 10):
            r = requests.get(url=rpath)
            if r.status_code == 404:
                time.sleep(0.5)
            elif r.status_code != 200:
                r.raise_for_status()
            else:
                break

        return r.json()["ids"]

    def reqDeviceServices(self, service: str):
        """
        Returns a list of services for the given device
        """
        service = service.lower()
        rpath = f"{self._catalogURL}/catalog/services/{service}"

        r = None
        for _ in range(0, 10):
            r = requests.get(url=rpath)
            if r.status_code == 404:
                time.sleep(0.5)
            elif r.status_code != 200:
                r.raise_for_status()
            else:
                break

        return r.json()["services"]

    def reqAllServices(self) -> dict[str, list]:
        """
        Returns a list of all services
        """

        r1 = requests.get(url=f"{self._catalogURL}/catalog/services")
        if r1.status_code != 200:
            r1.raise_for_status()

        r2 = requests.get(url=f"{self._catalogURL}/catalog/services/expired")
        if r2.status_code != 200:
            r2.raise_for_status()

        return {"online": r1.json()["services"], "offline": r2.json()["services"]}

    def reqSysInfo(self) -> dict:
        """
        Returns the system information
        """
        r = requests.get(url=f"{self._catalogURL}/catalog/sysinfo")
        if r.status_code != 200:
            r.raise_for_status()

        return r.json()

    def _do_req(self, meth: RequestType, path: str, data = None, max : int = 10, doraise: bool = True):
        """
        Internal method to perform a request to a service
        """

        r = None
        for i in range(0, max):

            if i > 0:
                time.sleep(0.5)
                self._logger.warning(f"Retrying request to {path}, #{i+1}...")

            try:
                r = self._s.request(meth.name, path, json=data)
            except:
                continue

            if r.status_code == 404:
                continue
            elif r.status_code not in [200, 201, 202]:
                if doraise:
                    r.raise_for_status()
                else:
                    return r
            else:
                return r

        if r is not None:
            r.raise_for_status()
        else:
            raise Exception(f"Request to {path} failed. Maybe timeout?")

        return r

    def _cb_on_connect(self, mqtt: mqtt.Client, userdata, flags, rc):
        self._logger.info(f"Connected to MQTT broker {mqtt._host}:{mqtt._port}")
        if self._on_connect is not None:
            self._on_connect(mqtt, userdata, flags, rc)

    def _cb_on_msg_recv(self, mqtt: mqtt.Client, udata, msg : mqtt.MQTTMessage):
        self._logger.debug(f"Received MQTT message on {msg.topic}: {msg.payload}")
        if self._on_msg_recv is not None:
            self._on_msg_recv(mqtt, udata, msg)

    def _mqttclient_connect(self):
        r = self._s.get(f"{self._catalogURL}/catalog/mqttbroker", timeout=15)
        if not r.json()["connected"]:
            raise Exception("Catalog's MQTT Broker is not connected!")

        broker = r.json()["broker"]
        self._mqttclient.on_connect = self._cb_on_connect
        self._mqttclient.on_message = self._cb_on_msg_recv

        while 1:
            try:
                self._mqttclient.connect(broker["host"], broker["port"])
                break
            except Exception as e:
                self._logger.warning(f"MQTT connection failed to {broker['host']}:{broker['port']}: {e}. Trying again...")
                time.sleep(0.5)
                continue

        self._mqttclient.loop_start()
        self._mqttclient_connected = True

