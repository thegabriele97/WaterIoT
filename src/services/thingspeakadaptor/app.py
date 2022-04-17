import enum
import logging
from queue import Queue
import cherrypy
import requests
import paho.mqtt.client as mqtt

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import CatalogRequest
from common.WIOThread import WIOThread

class ThingSpeakAPI(RESTBase):
    def __init__(
        self,
        upperRESTSrvcApp,
        settings: SettingsNode,
        thingspeakapikeytemperaturewrite,
        thingspeakapikeytemperatureread,
        thingspeakapikeyhumiditywrite,
        thingspeakapikeyhumidityread,
        thingspeakapikeysoilwrite,
        thingspeakapikeysoilread,
        channelidtemperature,
        channelidhumidity,
        channelidsoil,
    ) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings, on_msg_recv=self._onMessageReceive)

        # Subscribe to raspberry device connector mqtt topic
        self._catreq.subscribeMQTT("RaspberryDevConn", "/+/airhumidity")
        self._catreq.subscribeMQTT("RaspberryDevConn", "/+/airtemperature")
        self._catreq.subscribeMQTT("RaspberryDevConn", "/+/terrainhumidity")

        # Set the API keys
        self._thingspeakapikeytemperaturewrite = thingspeakapikeytemperaturewrite
        self._thingspeakapikeytemperatureread = thingspeakapikeytemperatureread
        self._thingspeakapikeyhumiditywrite = thingspeakapikeyhumiditywrite
        self._thingspeakapikeyhumidityread = thingspeakapikeyhumidityread
        self._thingspeakapikeysoilwrite = thingspeakapikeysoilwrite
        self._thingspeakapikeysoilread = thingspeakapikeysoilread
        self._channelidtemperature = channelidtemperature
        self._channelidhumidity = channelidhumidity
        self._channelidsoil = channelidsoil

        self._publishqueue = Queue(0)
        self._publishthread = WIOThread(name="ThingSpeakPublishThread", target=self._publishThreadHandler)

        upperRESTSrvcApp.subsribe_evt_stop(self._publishthread.stop)
        self._publishthread.run()

    def _publishThreadHandler(self):
        
        while not self._publishthread.is_stop_requested:
            try:
                msg = self._publishqueue.get(block=True)
                payl = json.loads(msg.payload.decode("utf-8"))
                self.logger.debug(payl)

                if msg.topic.endswith("/airhumidity"):
                    api_key = self._thingspeakapikeyhumiditywrite
                    pub_topic = "/airhum"
                elif msg.topic.endswith("/airtemperature"):
                    api_key = self._thingspeakapikeytemperaturewrite
                    pub_topic = "/airtemp"
                elif msg.topic.endswith("/terrainhumidity"):
                    api_key = self._thingspeakapikeysoilwrite
                    pub_topic = "/soilhum"

                r = requests.get(f"https://api.thingspeak.com/update?api_key={api_key}&field1={payl['v']}&field2={payl['i']}&field3={payl['t']}")

                if r.status_code != 200:
                    self.logger.warning(f"Error writing air humidity to ThingSpeak ({r.status_code}): {r.json()}")

                value = {
                    "v": payl["v"], 
                    "i": payl["i"]
                }

                self._catreq.publishMQTT("ThingSpeakAdaptor", pub_topic, json.dumps(value))
                self._publishthread.wait(15.5)
            except Exception as e:
                self.logger.critical(f"Error publishing to ThingSpeak: {e}", exc_info=True)

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):
        if len(path) == 0:
            return self.asjson_info("ThingSpeak Adaptor Endpoint")
        elif path[0] == "temperature":
            if "devid" not in args and "results" in args:
                # Get the last value of the air temperature for all devices
                r = requests.get(
                    f"https://api.thingspeak.com/channels/{self._channelidtemperature}/feeds.json?api_key={self._thingspeakapikeytemperatureread}&results={args['results']}"
                )
            else:
                # Get all values of the air temperature for all devices
                r = requests.get(f"https://api.thingspeak.com/channels/{self._channelidtemperature}/feeds.json?api_key={self._thingspeakapikeytemperatureread}")

            if r.status_code != 200:
                return self.asjson_error({"response": r.json()})

            res = r.json()["feeds"]
            if "devid" in args:
                # Get the last value of the air temperature for a specific device
                res = [r for r in res if r["field2"] == args["devid"]]
                if "results" in args:
                    res = res[-int(args["results"]):]

            return res
        elif path[0] == "humidity":
            if "devid" not in args and "results" in args:
                # Get the last value of the air humidity for all devices
                r = requests.get(
                    f"https://api.thingspeak.com/channels/{self._channelidhumidity}/feeds.json?api_key={self._thingspeakapikeyhumidityread}&results={args['results']}"
                )
            else:
                # Get all values of the air humidity for all devices
                r = requests.get(f"https://api.thingspeak.com/channels/{self._channelidhumidity}/feeds.json?api_key={self._thingspeakapikeyhumidityread}")

            if r.status_code != 200:
                return self.asjson_error({"response": r.json()})

            res = r.json()["feeds"]
            if "devid" in args:
                # Get the last value of the air temperature for a specific device
                res = [r for r in res if r["field2"] == args["devid"]]
                if "results" in args:
                    res = res[-int(args["results"]):]

            return res
        elif path[0] == "soil":
            if "devid" not in args and "results" in args:
                # Get the last value of the soil humidity for all devices
                r = requests.get(
                    f"https://api.thingspeak.com/channels/{self._channelidsoil}/feeds.json?api_key={self._thingspeakapikeysoilread}&results={args['results']}"
                )
            else:
                # Get all values of the soil humidity for all devices
                r = requests.get(
                    f"https://api.thingspeak.com/channels/{self._channelidsoil}/feeds.json?api_key={self._thingspeakapikeysoilread}"
                )
            if r.status_code != 200:
                return self.asjson_error({"response": r.json()})

            res = r.json()["feeds"]
            if "devid" in args:
                # Get the last value of the air temperature for a specific device
                res = [r for r in res if r["field2"] == args["devid"]]
                if "results" in args:
                    res = res[-int(args["results"]):]

            return res

        return self.asjson_error("Not found", 404)

    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(self, *path, **args):

        if len(path) > 0:
            if path[0] == "feeds":

                # check if request body is in the correct format
                body = json.loads(cherrypy.request.body.read())
                if "v" not in body or "i" not in body or "t" not in body or "n" not in body:
                    return self.asjson_error("Invalid request body", 400)

                # send the air temperature to the queue
                self._publishqueue.put(json.dumps(body))
                return self.asjson_info("OK", 202) # 202 Accepted

        return self.asjson_error("not found", 404)

    def _onMessageReceive(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        self._publishqueue.put(msg, block=True)

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            # Get all the keys from the environment variables
            thingspeakapikeytemperaturewrite = os.environ[
                "THINGSPEAKAPIKEYTEMPERATUREWRITE"
            ]
            thingspeakapikeytemperatureread = os.environ[
                "THINGSPEAKAPIKEYTEMPERATUREREAD"
            ]
            thingspeakapikeyhumiditywrite = os.environ["THINGSPEAKAPIKEYHUMIDITYWRITE"]
            thingspeakapikeyhumidityread = os.environ["THINGSPEAKAPIKEYHUMIDITYREAD"]
            thingspeakapikeysoilwrite = os.environ["THINGSPEAKAPIKEYSOILWRITE"]
            thingpseakapikeysoilread = os.environ["THINGSPEAKAPIKEYSOILREAD"]
            channelidtemperature = os.environ["CHANNELIDTEMPERATURE"]
            channelidhumidity = os.environ["CHANNELIDHUMIDITY"]
            channelidsoil = os.environ["CHANNELIDSOIL"]
            self.logger.debug(
                "thingspeak api key write set to: "
                + thingspeakapikeytemperaturewrite
                + "and thinkspeak api key read set to: "
                + thingspeakapikeytemperatureread
            )

            self._settings = SettingsManager.json2obj(
                SettingsManager.relfile2abs("settings.json"), self.logger
            )
            self.create(self._settings, "ThingSpeakAdaptor", ServiceType.SERVICE)

            self.addRESTEndpoint("/temperature", [EndpointParam("results", required=False), EndpointParam("devid", required=False)])
            self.addRESTEndpoint("/humidity", [EndpointParam("results", required=False), EndpointParam("devid", required=False)])
            self.addRESTEndpoint("/soil", [EndpointParam("results", required=False), EndpointParam("devid", required=False)])
            self.addRESTEndpoint("/feeds")

            self.addMQTTEndpoint("/airtemp", "updates on air temperature sampling")
            self.addMQTTEndpoint("/airhum", "updates on air humidity sampling")
            self.addMQTTEndpoint("/soilhum", "updates switch soil humidity sampling")

            self.mount(
                ThingSpeakAPI(
                    self,
                    self._settings,
                    thingspeakapikeytemperaturewrite,
                    thingspeakapikeytemperatureread,
                    thingspeakapikeyhumiditywrite,
                    thingspeakapikeyhumidityread,
                    thingspeakapikeysoilwrite,
                    thingpseakapikeysoilread,
                    channelidtemperature,
                    channelidhumidity,
                    channelidsoil,
                ),
                self.conf,
            )
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
