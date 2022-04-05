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

        # TODO: temporary
        self._catreq.subscribeMQTT("ArduinoDevConn", "/+/switch")
        self._catreq.callbackOnTopic("ArduinoDevConn", "/+/switch", self.onMessageReceive)

        # Subscribe to arduino device connector mqtt topic
        self._catreq.subscribeMQTT("RaspberryDevConn", "/+/airhumidity")
        self._catreq.callbackOnTopic("RaspberryDevConn", "/+/airhumidity", self.onMessageReceiveAirHumidity)
        self._catreq.subscribeMQTT("RaspberryDevConn", "/+/airtemperature")
        self._catreq.callbackOnTopic("RaspberryDevConn", "/+/airtemperature", self.onMessageReceiveAirTemperature)
        self._catreq.subscribeMQTT("RaspberryDevConn", "/+/terrainhumidity")
        self._catreq.callbackOnTopic("RaspberryDevConn", "/+/terrainhumidity", self.onMessageReceiveTerrainHumidity)

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
                return self.asjson_error({"response": r.json()})
            return r.json()["feeds"]

        return self.asjson_error("Not found", 404)

    def POST(self, *path, **args):

        if len(path) > 0:
            if path[0] == "temperature":
                # Write the air temperature to the ThingSpeak channel
                r = requests.get(
                    f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeytemperaturewrite}&field1={args['temp']}"
                )
                if r.status_code != 200:
                    return self.asjson_error({"response": r.json()})

                value = {"value": args['temp']}
                self._catreq.publishMQTT("ThingSpeakAdaptor", "/airtemp", json.dumps(value))
                return self.asjson_info("ok", 201)

            elif path[0] == "humidity":
                # Write the air humidity to the ThingSpeak channel
                r = requests.get(
                    f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeyhumiditywrite}&field1={args['hum']}"
                )
                if r.status_code != 200:
                    return self.asjson_error({"response": r.json()})

                value = {"value": args['hum']}
                self._catreq.publishMQTT("ThingSpeakAdaptor", "/airhum", json.dumps(value))
                return self.asjson_info("ok", 201)

            elif path[0] == "soil":
                # Write the soil humidity to the ThingSpeak channel
                r = requests.get(
                    f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeysoilwrite}&field1={args['soil']}"
                )

                if r.status_code != 200:
                    return self.asjson_error({"response": r.json()})

                value = {"value": args['soil']}
                self._catreq.publishMQTT("ThingSpeakAdaptor", "/soilhum", json.dumps(value))
                return self.asjson_info("ok", 201)

        return self.asjson_error("not found", 404)


    def onMessageReceiveAirHumidity(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        
        payl = json.loads(msg.payload.decode("utf-8"))
        self.logger.debug(payl)

        # TODO: field for timestamp and device id #############
        r = requests.get(
            f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeyhumiditywrite}&field1={payl['v']}"
        )

        if r.status_code != 200:
            self.logger.warning(f"Error writing air humidity to ThingSpeak ({r.status_code}): {r.json()}")

        value = {"value": payl["v"]}
        self._catreq.publishMQTT("ThingSpeakAdaptor", "/airhum", json.dumps(value))
        # self._catreq.reqREST("ThingSpeakAdaptor", f"/humidity?hum={msg.payload}", "POST")

    def onMessageReceiveAirTemperature(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        payl = json.loads(msg.payload.decode("utf-8"))
        self.logger.debug(payl)

        r = requests.get(
            f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeytemperaturewrite}&field1={payl['v']}"
        )

        if r.status_code != 200:
            self.logger.warning(f"Error writing air temperature to ThingSpeak ({r.status_code}): {r.json()}")

        value = {"value": payl['v']}
        self._catreq.publishMQTT("ThingSpeakAdaptor", "/airtemp", json.dumps(value))
        # self._catreq.reqREST("ThingSpeakAdaptor", f"/temperature?temp={msg.payload}", "POST")

    def onMessageReceiveTerrainHumidity(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        payl = json.loads(msg.payload.decode("utf-8"))
        self.logger.debug(payl)

        r = requests.get(
            f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeysoilwrite}&field1={payl['v']}"
        )

        if r.status_code != 200:
            self.logger.warning(f"Error writing soil humidity to ThingSpeak ({r.status_code}): {r.json()}")

        value = {"value": payl['v']}
        self._catreq.publishMQTT("ThingSpeakAdaptor", "/soilhum", json.dumps(value))
        # self._catreq.reqREST("ThingSpeakAdaptor", f"/soil?soil={msg.payload}", "POST")


    # TODO: to remove
    def onMessageReceive(self, paho_mqtt , userdata, msg:mqtt.MQTTMessage):
        self.logger.debug(f"{msg.topic}: {msg.payload}")


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
            self.addRESTEndpoint("/temperature", [EndpointParam("temp")])
            self.addRESTEndpoint("/humidity", [EndpointParam("hum")])
            self.addRESTEndpoint("/soil", [EndpointParam("soil")])
            self.addRESTEndpoint("/temperature", [EndpointParam("results", required=False)])
            self.addRESTEndpoint("/humidity", [EndpointParam("results", required=False)])
            self.addRESTEndpoint("/soil", [EndpointParam("results", required=False)])

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
