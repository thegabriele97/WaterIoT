from collections import namedtuple
from datetime import datetime
import logging
from multiprocessing.sharedctypes import Value
import socket
import cherrypy
import json

import psutil
import paho.mqtt.client as mqtt

from common.RESTBase import RESTBase
from common.RESTServiceApp import RESTServiceApp
from common.SettingsManager import SettingsManager
from common.SettingsNode import SettingsNode
from common.Service import *
from common.Endpoint import *
from common.HttpDate import Httpdate
from ServiceManager import ServiceManager

class CatalogAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp: RESTServiceApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, settings.getattrORdef('indent_level', 4))
        self._settings = settings

        self._serviceManager = ServiceManager(settings, self.logger)
        upperRESTSrvcApp.subsribe_evt_stop(self._serviceManager.stop_watchdog)

        self._mqttclient = mqtt.Client()
        self._mqtt_broker_idx = -1
        self._mqtt_connectbroker()
        self._serviceManager.run_watchdog()

        x = Service("name", ServiceType.SERVICE, "127.0.0.1", 8080)
        x.addEndpoint(Endpoint("/", EndpointType.REST))
        x.addEndpoint(Endpoint("/getit", EndpointType.REST, params=[EndpointParam("what")]))
        self._serviceManager.add_service(x)

    def _mqtt_connectbroker(self):
        self._mqtt_broker_idx = -1;
        for idx, broker in enumerate(self._settings.mqttbrokers):
            try:
                self._mqttclient.connect(broker.host, broker.port)
                self._mqttclient.loop(timeout=5)
            except:
                pass

            if self._mqttclient.is_connected():
                self._mqtt_broker_idx = idx
                break

        if not self._mqttclient.is_connected():
            self.logger.warn("Unable to connect to any MQTT broker!")

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if len(path) <= 0:
            return self.asjson_info("Catalog API endpoint!")
        elif path[0] == "SysInfo".lower():
            return self.asjson({
                "cpu_perc": psutil.cpu_percent(),
                "ram_perc": psutil.virtual_memory()[2]
            })
        elif path[0] == "MQTTBroker".lower():

            if not self._mqttclient.is_connected():
                self._mqtt_connectbroker()

            conn = True if self._mqtt_broker_idx >= 0 else False

            return self.asjson({
                "connected": conn,
                "broker": self._settings.mqttbrokers[self._mqtt_broker_idx].toDict() if conn else None
            })

        elif path[0] == "services":

            if "type" in args:
                # /catalog/services?type={service,device}&subtype={arduino,raspberry}
                try:
                    stype = ServiceType.value_of(str(args["type"]).upper())
                except ValueError:
                    return self.asjson_error("Invalid service type", 400)

                sers = [s for s in self._serviceManager.services.values() if s.stype == stype]
                if "subtype" in args:
                    try:
                        subtype = ServiceSubType.value_of(str(args["subtype"]).upper())
                    except ValueError:
                        return self.asjson_error("Invalid service subtype", 400)

                    return self.asjson({"services": [s.toDict() for s in sers if s.subtype == subtype]})

                # /catalog/services?type={service,device}
                else:
                    return self.asjson({"services": [s.toDict() for s in sers]})

            # /catalog/services/expired
            elif len(path) == 2 and path[1] == "expired":
                return self.asjson({"services": [s.toDict() for s in self._serviceManager.dead_services.values()]})
            elif len(path) > 1:
                # /catalog/services/service_name
                if len(path) == 2 and (path[1] in self._serviceManager.services.keys() or path[1] in self._serviceManager.dead_services.keys()):
                    online = path[1] in self._serviceManager.services.keys()
                    tos = self._serviceManager.services if online else self._serviceManager.dead_services

                    sum = Httpdate.from_timestamp(tos[path[1]].timestamp + self._settings.watchdog.expire_sec)
                    cherrypy.response.headers["Expires"] = sum if online else 0
                    cherrypy.response.headers["Last-Modified"] = Httpdate.from_timestamp(tos[path[1]].timestamp)

                    return self.asjson({
                        "online": online,
                        "service": tos[path[1]].toDict()
                    })

            else:
                # /catalog/services
                return self.asjson({"services": [s.toDict() for s in self._serviceManager.services.values()]})

        return self.asjson_error("invalid request", 404)

    @cherrypy.tools.json_out()
    def POST(self, *path, **args):
        body = json.loads(cherrypy.request.body.read())

        if len(path) == 1:
            if path[0] == "services":

                s = Service.fromDict(body, cherrypy.request.remote.ip)
                if s.name in self._serviceManager.services.keys():
                    return self.asjson_error("Forbidden: the service already exists", 403)

                self._serviceManager.add_service(s)
                return self.asjson_info(f"Service {s.name} created", 201)

        return self.asjson_error("invalid request", 404)

    @cherrypy.tools.json_out()
    def PUT(self, *path, **args):
        body = json.loads(cherrypy.request.body.read())

        if len(path) == 1:
            if path[0] == "services":

                s = Service.fromDict(body, cherrypy.request.remote.ip)
                self._serviceManager.add_service(s)
                return self.asjson_info(f"Service {s.name} updated")

        return self.asjson_error("invalid request", 404)


class App(RESTServiceApp):
    def __init__(self) -> None:
        super().__init__(log_stdout_level=logging.INFO)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.mount("/catalog", CatalogAPI(self, self._settings), self.conf)
            self.loop(port=self._settings.rest_server.port, host=self._settings.rest_server.host)

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
