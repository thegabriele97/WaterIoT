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

        s = requests.Session()
        retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[ 500, 502, 503, 504 ])
        s.mount('http://', HTTPAdapter(max_retries=retries))

        r = s.get(f"{self._catalogURL}/catalog/mqttbroker", timeout=15)
        if not r.json()["connected"]:
            raise Exception("Catalog's MQTT Broker is not connected!")

        broker = r.json()["broker"]
        self._mqttclient.on_connect = self._cb_on_connect
        self._mqttclient.on_message = self._cb_on_msg_recv

        self._mqttclient.connect(broker["host"], broker["port"])
        self._mqttclient.loop_start()


    def publishMQTT(self, service: str, path:str, payload):
        if path[0] != '/':
            raise ValueError("Path must begin with a '/'")

        if not self._check_mqtt_endpoint(service, path):
            raise ValueError(f"Trying to publish in a non published topic on the catalog for {service}")

        self._mqttclient.publish(f"/{service}{path}", payload)
        self._logger.debug(f"MQTT published to /{service}{path}: {payload}")

    def subscribeMQTT(self, service: str, path: str):

        if path[0] != '/':
            raise ValueError("Path must begin with a '/'")

        if not self._check_mqtt_endpoint(service, path):
            raise ValueError(f"Trying to subscribe in a non published topic on the catalog for {service}")

        self._mqttclient.subscribe(f"/{service}{path}")
        self._logger.debug(f"MQTT subscribed to /{service}{path}")

    def callbackOnTopic(self, service: str, path: str, callback):

        if path[0] != '/':
            raise ValueError("Path must begin with a '/'")

        if not self._check_mqtt_endpoint(service, path):
            raise ValueError(f"Trying to interact with a non published topic on the catalog for {service}")

        self._mqttclient.message_callback_add(f"/{service}{path}", callback)

    def _check_mqtt_endpoint(self, service: str, path: str):

        service = service.lower()
        self._logger.debug(f"Requesting MQTT service info @ {self._catalogURL}/catalog/services/{service}")

        r = None
        for _ in range(0, 10):
            r = requests.get(url=f"{self._catalogURL}/catalog/services/{service}")
            if r.status_code == 404:
                time.sleep(0.5)
            elif r.status_code != 200:
                r.raise_for_status()
            else:
                break

        if r.status_code == 404 or r == None:
            raise Exception(f"{self._catalogURL}/catalog/services/{service} return status code 404")

        if not r.json()["online"]:
            raise Exception(f"Service {service} is not online")
            
        epoints_raw = r.json()["service"]["endpoints"][EndpointType.MQTT.name]        
        epoint = [e for e in epoints_raw if mqtt.topic_matches_sub(f"/{service}{path}", e["uri"])]

        return len(epoint) == 1

    def reqREST(self, service: str, path: str, reqt: RequestType = RequestType.GET, datarequest = None):
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
        CacheType = namedtuple("CacheType", "header response")
        service = service.lower()

        try:
            self._logger.debug(f"Requesting REST service info @ {self._catalogURL}/catalog/services/{service}")

            if service in self._reqcache.keys():
                r = requests.head(url=f"{self._catalogURL}/catalog/services/{service}")
                coderesp = r.status_code

                if r.status_code != 200:
                    r.raise_for_status()

                lastmodified = r.headers["Last-Modified"]
                expires = r.headers["Expires"]
                cache = (service, CacheType(self._reqcache[service][0], self._reqcache[service][1]))

                if expires != '0' and lastmodified == cache[1].header["Last-Modified"]:
                    self._logger.debug(f"Using cache for service {service}")
                    jsonresp = cache[1].response

            if jsonresp is None:
                r = requests.get(url=f"{self._catalogURL}/catalog/services/{service}")
                jsonresp = r.json()
                coderesp = r.status_code

                if r.status_code != 200:
                    r.raise_for_status()

                self._reqcache[service] = CacheType(r.headers, r.json())

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
            if reqt == RequestType.GET:
                r = requests.get(url=url, json=datarequest)
            elif reqt == RequestType.POST:
                r = requests.post(url=url, json=datarequest)
            elif reqt == RequestType.PUT:
                r = requests.put(url=url, json=datarequest)
            elif reqt == RequestType.DELETE:
                r = requests.delete(url=url, json=datarequest)

            jsonresp = r.json()
            coderesp = r.status_code
            
        except Exception as e:
            self._logger.error(f"Catalog request error: {str(e)}")
        
        finally:
            self._logger.debug(f"Service {b1}. Endpoint {b2}. Params {b3}")
            return RetType(b1 and b2 and b3, jsonresp, coderesp)

    def _cb_on_connect(self, mqtt: mqtt.Client, userdata, flags, rc):
        self._logger.info(f"Connected to MQTT broker {mqtt._host}:{mqtt._port}")
        if self._on_connect is not None:
            self._on_connect(mqtt, userdata, flags, rc)

    def _cb_on_msg_recv(self, mqtt: mqtt.Client, udata, msg : mqtt.MQTTMessage):
        self._logger.debug(f"Received MQTT message on {msg.topic}: {msg.payload}")
        if self._on_msg_recv is not None:
            self._on_msg_recv(mqtt, udata, msg)