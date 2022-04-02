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
        thingspeakapikeysoilwrite,
        thingspeakapikeysoilread,
        channelidtemperature,
        channelidhumidity,
        channelidsoil,
    ) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)

        # Subscribe to arduino device connector mqtt topic
        self._catreq.subscribeMQTT("ArduinoDevConn", "/switch")
        self._catreq.callbackOnTopic("ArduinoDevConn", "/switch", self.onMessageReceive)

        # Set the API keys
        self._thingspeakapikeytemperaturewrite = thingspeakapikeytemperaturewrite
        self._thingspeakapikeytemperatureread = thingspeakapikeytemperatureread
        self._thingspeakapikeyhumiditywrite = thingspeakapikeyhumiditywrite
        self._thingspeakapikeyhumidityread = thingspeakapikeyhumidityread
        self._thingspeakapikeysoilwrite = thingspeakapikeysoilwrite
        self._thingspeakapikeysoilread = thingspeakapikeysoilread
        self._channelidtemperature = channelidtemperature
        self._channelidhumidity = channelidhumidity

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):
        if len(path) == 0:
            return self.asjson_info("ThingSpeak Adaptor Endpoint")
        elif path[0] == "temperature":
            if len(args) > 0:
                # Get the last value of the air temperature
                r = requests.get(
                    f"https://api.thingspeak.com/channels/{self._channelidtemperature}/feeds.json?api_key={self._thingspeakapikeytemperatureread}&results={args['results']}"
                )
            else:
                # Get all values of the air temperature
                r = requests.get(
                    f"https://api.thingspeak.com/channels/{self._channelidtemperature}/feeds.json?api_key={self._thingspeakapikeytemperatureread}"
                )
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return r.json()["feeds"]
        elif path[0] == "humidity":
            if len(args) > 0:
                # Get the last value of the air himidity
                r = requests.get(
                    f"https://api.thingspeak.com/channels/{self._channelidhumidity}/feeds.json?api_key={self._thingspeakapikeyhumidityread}&results={args['results']}"
                )
            else:
                # Get all values of the air humidity
                r = requests.get(
                    f"https://api.thingspeak.com/channels/{self._channelidhumidity}/feeds.json?api_key={self._thingspeakapikeyhumidityread}"
                )
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return r.json()["feeds"]
        elif path[0] == "soil":
            if len(args) > 0:
                # Get the last value of the soil humidity
                r = requests.get(
                f"https://api.thingspeak.com/channels/{self._channelidsoil}/feeds.json?api_key={self._thingspeakapikeysoilread}&results={args['results']}"
                )
            else:
                # Get all values of the soil humidity
                r = requests.get(
                f"https://api.thingspeak.com/channels/{self._channelidsoil}/feeds.json?api_key={self._thingspeakapikeysoilread}"
                )
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return r.json()["feeds"]

    def POST(self, *path, **args):

        if len(path) == 0:
            return self.asjson_info("ThingSpeak Adaptor Endpoint")
        elif path[0] == "temperature":
            # Write the air temperature to the ThingSpeak channel
            r = requests.get(
                f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeytemperaturewrite}&field1={args['temp']}"
            )
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})

            value = {"value": args['temp']}
            self._catreq.publishMQTT("ThingSpeakAdaptor", "/airtemp", json.dumps(value))
            
            return self.asjson_info(None)
        elif path[0] == "humidity":
            # Write the air humidity to the ThingSpeak channel
            r = requests.get(
                f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeyhumiditywrite}&field1={args['hum']}"
            )
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})

            value = {"value": args['hum']}
            self._catreq.publishMQTT("ThingSpeakAdaptor", "/airhum", json.dumps(value))
            return self.asjson_info(None)
        elif path[0] == "soil":
            # Write the soil humidity to the ThingSpeak channel
            r = requests.get(
                f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeysoilwrite}&field1={args['soil']}"
            )
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return self.asjson_info(None)


    def onMessageReceive(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        self.logger.debug(msg.payload)
        # TODO: wait for rpi device connector to knwo how the data are sent


class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            # Get all the keys from the environment variables
            thingspeakapikeytemperaturewrite = os.environ["THINGSPEAKAPIKEYTEMPERATUREWRITE"]
            thingspeakapikeytemperatureread = os.environ["THINGSPEAKAPIKEYTEMPERATUREREAD"]
            thingspeakapikeyhumiditywrite = os.environ["THINGSPEAKAPIKEYHUMIDITYWRITE"]
            thingspeakapikeyhumidityread = os.environ["THINGSPEAKAPIKEYHUMIDITYREAD"]
            thingspeakapikeysoilwrite=os.environ["THINGSPEAKAPIKEYSOILWRITE"]
            thingpseakapikeysoilread=os.environ["THINGSPEAKAPIKEYSOILREAD"]
            channelidtemperature = os.environ["CHANNELIDTEMPERATURE"]
            channelidhumidity = os.environ["CHANNELIDHUMIDITY"]
            channelidsoil=os.environ["CHANNELIDSOIL"]
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

            # Add all necessary endpoints
            self.addRESTEndpoint("/")
            self.addRESTEndpoint("/temperature", [EndpointParam("temp")])
            self.addRESTEndpoint("/humidity", [EndpointParam("hum")])
            self.addRESTEndpoint("/temperature", [EndpointParam("results")])
            self.addRESTEndpoint("/humidity", [EndpointParam("results")])
            self.addRESTEndpoint("/temperature")
            self.addRESTEndpoint("/humidity")
            self.addMQTTEndpoint("/airtemp", "updates on switc")
            self.addMQTTEndpoint("/airhum", "updates on  status")
            self.addMQTTEndpoint("/soilhum", "updates switch status")

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
