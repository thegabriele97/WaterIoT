import logging
import cherrypy
import requests
import paho.mqtt.client as mqtt

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import CatalogRequest


class ThingSpeakAPI(RESTBase):
    def __init__(
        self,
        upperRESTSrvcApp,
        settings: SettingsNode,
        thingspeakapikeytemperaturewrite,
        thingspeakapikeytemperatureread,
        thingspeakapikeyhumiditywrite,
        thingspeakapikeyhumidityread,
        channelidtemperature,
        channelidhumidity,
    ) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)
        self._catreq.subscribeMQTT("ArduinoDevConn", "/+/switch")
        self._catreq.callbackOnTopic("ArduinoDevConn", "/+/switch", self.onMessageReceive)
        self._thingspeakapikeytemperaturewrite = thingspeakapikeytemperaturewrite
        self._thingspeakapikeytemperatureread = thingspeakapikeytemperatureread
        self._thingspeakapikeyhumiditywrite = thingspeakapikeyhumiditywrite
        self._thingspeakapikeyhumidityread = thingspeakapikeyhumidityread
        self._channelidtemperature = channelidtemperature
        self._channelidhumidity = channelidhumidity

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):
        if len(path) == 0:
            return self.asjson_info("ThingSpeak Adaptor Endpoint")
        elif path[0] == "temperature":
            if len(args) > 0:
                r = requests.get(
                f"https://api.thingspeak.com/channels/{self._channelidtemperature}/feeds.json?api_key={self._thingspeakapikeytemperatureread}&results={args['results']}"
                )
            else:
                r = requests.get(
                f"https://api.thingspeak.com/channels/{self._channelidtemperature}/feeds.json?api_key={self._thingspeakapikeytemperatureread}"
                )
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return r.json()["feeds"]
        elif path[0] == "humidity":
            if len(args) > 0:
                r = requests.get(
                f"https://api.thingspeak.com/channels/{self._channelidhumidity}/feeds.json?api_key={self._thingspeakapikeyhumidityread}&results={args['results']}"
                )
            else:
                r = requests.get(
                f"https://api.thingspeak.com/channels/{self._channelidhumidity}/feeds.json?api_key={self._thingspeakapikeyhumidityread}"
                )
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return r.json()["feeds"]

    def POST(self, *path, **args):

        if len(path) == 0:
            return self.asjson_info("ThingSpeak Adaptor Endpoint")
        elif path[0] == "temperature":
            r = requests.get(
                f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeytemperaturewrite}&field1={args['temp']}"
            )
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return self.asjson_info(None)
        elif path[0] == "humidity":
            r = requests.get(
                f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeyhumiditywrite}&field1={args['hum']}"
            )
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return self.asjson_info(None)

    def onMessageReceive(self, paho_mqtt , userdata, msg:mqtt.MQTTMessage):
        self.logger.debug(f"{msg.topic}: {msg.payload}")
        #TODO: wait for rpi device connector to knwo hwo the data are sent

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            thingspeakapikeytemperaturewrite = os.environ[
                "THINGSPEAKAPIKEYTEMPERATUREWRITE"
            ]
            thingspeakapikeytemperatureread = os.environ[
                "THINGSPEAKAPIKEYTEMPERATUREREAD"
            ]
            thingspeakapikeyhumiditywrite = os.environ["THINGSPEAKAPIKEYHUMIDITYWRITE"]
            thingspeakapikeyhumidityread = os.environ["THINGSPEAKAPIKEYHUMIDITYREAD"]
            channelidtemperature = os.environ["CHANNELIDTEMPERATURE"]
            channelidhumidity = os.environ["CHANNELIDHUMIDITY"]
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
            self.addRESTEndpoint("/")
            self.addRESTEndpoint("/temperature", [EndpointParam("temp")])
            self.addRESTEndpoint("/humidity", [EndpointParam("hum")])
            self.addRESTEndpoint("/temperature", [EndpointParam("results")])
            self.addRESTEndpoint("/humidity", [EndpointParam("results")])
            self.addRESTEndpoint("/temperature")
            self.addRESTEndpoint("/humidity")

            self.mount(
                ThingSpeakAPI(
                    self,
                    self._settings,
                    thingspeakapikeytemperaturewrite,
                    thingspeakapikeytemperatureread,
                    thingspeakapikeyhumiditywrite,
                    thingspeakapikeyhumidityread,
                    channelidtemperature,
                    channelidhumidity,
                ),
                self.conf,
            )
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
