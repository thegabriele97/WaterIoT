import logging
import cherrypy
import paho.mqtt.client as mqtt
import requests

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import *

class OpenWeatherAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)
        self._catreq.subscribeMQTT("RaspberryDevConn", "/airhumidity")
        self._catreq.callbackOnTopic("/airhumidity", self.onAirHumidity)
        self._catreq.subscribeMQTT("RaspberryDevConn", "/airtemperature")
        self._catreq.callbackOnTopic("/airtemperature", self.onAirTemperature)
        self._catreq.subscribeMQTT("RaspberryDevConn", "/terrainhumidity")
        self._catreq.callbackOnTopic("/terrainhumidity", self.onTerrainHumidity)

    def onAirHumidity(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        self.logger.info("Air humidity: " + str(msg.payload))
    
    def onAirTemperature(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        self.logger.info("Air temperature: " + str(msg.payload))

    def onTerrainHumidity(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        self.logger.info("Terrain humidity: " + str(msg.payload))

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.INFO)

        try:
            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "WateringControl", ServiceType.SERVICE)
            self.mount(OpenWeatherAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()


# Useful LOC:
'''
    self._catreq.publishMQTT("ArduinoDevConn", "/switch", json.dumps(r), devid=self._devid)
    self._catreq.reqREST("OpenWeatherAdaptor", "/currentweather", {"lat": "52.5", "lon": "13.4"})
    self._catreq.reqREST("OpenWeatherAdaptor", "/forecastweather", {"lat": "52.5", "lon": "13.4"})
    self._catreq.reqREST("ThingSpeakAdaptor", "/temperature")
    self._catreq.reqREST("ThingSpeakAdaptor", "/humidity")
    self._catreq.reqREST("ThingSpeakAdaptor", "/soil")
'''