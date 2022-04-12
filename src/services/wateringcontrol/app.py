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
        status, json_response, code_response = self._catreq.reqREST("ThingSpeakAdaptor", "/humidity?results=10")
        if status == True and code_response == 200:
            self.logger.debug(f"ThingSpeakAdaptor response: {json_response}")
            self._lastTimestamp = float(json_response["feeds"][-1]["field3"])

            # check if the two timestamps are different, that means that you need to push the value to thingspeak
            if self._lastTimestamp != float(msg.payload["t"]):
                r = requests.get(
                    f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeyhumiditywrite}&field1={msg.payload['v']}&field2={msg.payload['i']}&field3={msg.payload['t']}"
                )
        else:
            self.logger.debug("Error making the request to ThingSpeakAdaptor")
        
        status, json_response, code_response = self._catreq.reqREST("ThingSpeakAdaptor", "/humidity?results=10")
        if status == True and code_response == 200:
            for element in json_response["feeds"]:
                sum += element["field1"]
            self._avgAirHum = sum / len(json_response["feeds"])
            self._asdrubale()
    
    def onAirTemperature(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        payl = json.loads(msg.payload.decode("utf-8"))
        self.logger.debug(f"Air temperature: {payl}")
        status, json_response, code_response = self._catreq.reqREST("ThingSpeakAdaptor", "/temperature?results=10")
        if status == True and code_response == 200:
            self.logger.debug(f"ThingSpeakAdaptor response: {json_response}")
            self._lastTimestamp = float(json_response["feeds"][-1]["field3"])

            # check if the two timestamps are different, that means that you need to push the value to thingspeak
            if self._lastTimestamp != float(msg.payload["t"]):
                r = requests.get(
                    f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeytemperaturewrite}&field1={msg.payload['v']}&field2={msg.payload['i']}&field3={msg.payload['t']}"
                )
        else:
            self.logger.debug("Error making the request to ThingSpeakAdaptor")
        
        status, json_response, code_response = self._catreq.reqREST("ThingSpeakAdaptor", "/temperature?results=10")
        if status == True and code_response == 200:
            for element in json_response["feeds"]:
                sum += element["field1"]
            self._avgAirTemp = sum / len(json_response["feeds"])
            self._asdrubale()

    def onTerrainHumidity(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        payl = json.loads(msg.payload.decode("utf-8"))
        self.logger.debug(f"Terrain humidity: {payl}")
        status, json_response, code_response = self._catreq.reqREST("ThingSpeakAdaptor", "/soil?results=10")
        if status == True and code_response == 200:
            self.logger.debug(f"ThingSpeakAdaptor response: {json_response}")
            self._lastTimestamp = float(json_response["feeds"][-1]["field3"])

            # check if the two timestamps are different, that means that you need to push the value to thingspeak
            if self._lastTimestamp != float(msg.payload["t"]):
                r = requests.get(
                    f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeysoilwrite}&field1={msg.payload['v']}&field2={msg.payload['i']}&field3={msg.payload['t']}"
                )
        else:
            self.logger.debug("Error making the request to ThingSpeakAdaptor")

        status, json_response, code_response = self._catreq.reqREST("ThingSpeakAdaptor", "/soil?results=10")
        if status == True and code_response == 200:
            for element in json_response["feeds"]:
                sum += element["field1"]
            self._avgSoilHum = sum / len(json_response["feeds"])
            self._asdrubale()

    def _asdrubale(self):


        # get all important thresholds

        self._airtemp_threshold_max = self._catreq.reqREST("DeviceConfig", "/configs?path=/watering/thresholds/temp").json_response["max"]
        self._airtemp_threshold_min = self._catreq.reqREST("DeviceConfig", "/configs?path=/watering/thresholds/temp").json_response["min"]
        self._airhum_threshold_max = self._catreq.reqREST("DeviceConfig", "/configs?path=/watering/thresholds/hum").json_response["max"]
        self._airhum_threshold_min = self._catreq.reqREST("DeviceConfig", "/configs?path=/watering/thresholds/hum").json_response["min"]
        self._soilhum_threshold_max = self._catreq.reqREST("DeviceConfig", "/configs?path=/watering/thresholds/soil").json_response["max"]
        self._soilhum_threshold_min = self._catreq.reqREST("DeviceConfig", "/configs?path=/watering/thresholds/soil").json_response["min"]

        # logic for the watering control

        if self._avgAirTemp == -1 or self._avgAirHum == -1 or self._avgSoilHum == -1:
            return

        if self._avgSoilHum > self._soilhum_threshold_max:
            self.logger.debug("Soil humidity is too high, watering is not needed")
            r = self._catreq.reqREST("ArduinoDevConn", "/switch?state=off")
            if r.status == True and r.code_response == 200:
                self.logger.debug("Switched off the watering")
            return

        if self._avgSoilHum < self._soilhum_threshold_min:
            self.logger.debug("Soil humidity is too low, watering is needed")
            # TODO: check the current weather
            r = self._catreq.reqREST("ArduinoDevConn", "/switch?state=on")
            if r.status == True and r.code_response == 200:
                self.logger.debug("Switched on the watering")
            return
        # if self._lastTerrainHum < self._terrainhum_threshold:
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
            # TODO: pass the api keys to write to the channels
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