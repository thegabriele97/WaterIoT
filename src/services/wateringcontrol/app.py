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
        self._catreq.subscribeMQTT("RaspberryDevConn", "/+/airhumidity")
        self._catreq.callbackOnTopic("RaspberryDevConn", "/+/airhumidity", self.onAirHumidity)
        self._catreq.subscribeMQTT("RaspberryDevConn", "/+/airtemperature")
        self._catreq.callbackOnTopic("RaspberryDevConn", "/+/airtemperature", self.onAirTemperature)
        self._catreq.subscribeMQTT("RaspberryDevConn", "/+/terrainhumidity")
        self._catreq.callbackOnTopic("RaspberryDevConn", "/+/terrainhumidity", self.onTerrainHumidity)

        self._lastAirTemp = -1
        self._lastAirHum = -1
        self._lastTerrainHum = -1
        self._terrainhum_threshold = 30 # taken from deviceconfig


    def onAirHumidity(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        payl = json.loads(msg.payload.decode("utf-8"))
        self.logger.debug(f"Air humidity: {payl}")
        self._lastAirHum = float(payl["v"])
        self._asdrubale()
    
    def onAirTemperature(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        payl = json.loads(msg.payload.decode("utf-8"))
        self.logger.debug(f"Air temperature: {payl}")
        r = self._catreq.reqREST("ThingSpeakAdaptor", "/temperature?results=10")
        # TODO: r[-1]["t"] = float(msg.payload["t"])
        # TODO: self._lastAirTemp = avg([*r.response, float(msg.payload["v"])])
        self._asdrubale()

    def onTerrainHumidity(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        payl = json.loads(msg.payload.decode("utf-8"))
        self.logger.debug(f"Terrain humidity: {payl}")
        self._lastAirTemp = float(payl["v"])
        self._asdrubale()

    def _asdrubale(self):

        if self._lastAirTemp == -1 or self._lastAirHum == -1 or self._lastTerrainHum == -1:
            return

        # if terrainhum > threshold:
            # stop watering (if activated)

        if self._lastTerrainHum < self._terrainhum_threshold:
            # check current weather
            # if (it's raining) and humidity of the air is high:
            #   Stop Watering (if activated) 
            # else:
            #   # get forecast (4h)
            #   # if it will rain:
            #   #   Stop Watering (if activated) 
            #   # else:
            #   #   # get actual temperature
            #   #   # if temperature is greater then the threshold and temperature humidity is lower then the threshold:
            #           Trigger Watering (all ARDUINOs)
                        # get ids
                        # reqrest("arduinodevconn", "/switch?state=on", devid=id)
            #   #   # else:
            #           Ask him what to do

            pass

        # if nothing is done in previous if:
            # if terrainhum less then (20+60)/2 (average thresholds):
                # send a message to the user (telegram) asking what he wants to do
    
        pass

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

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