import logging
from statistics import mean
import cherrypy
import paho.mqtt.client as mqtt

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import *
from common.Links import *

class WateringControlAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)

        try:
            self._enable = True

            self._avgAirHum = {}
            self._avgAirTemp = {}
            self._avgSoilHum = {}

            self._lat = 0
            self._lon = 0

            self._last_sent_msg_timestamp = -1
            self._last_sent_msgcrit_timestamp = -1

            r = self._catreq.reqREST("DeviceConfig", "/configs?path=/watering/enable")
            if r.status and r.code_response == 200:
                self._enable = bool(r.json_response["v"])
            else:
                self.logger.error(f"Error getting the enable status from the DeviceConfig ({r.code_response}): {r.json_response}")

            r = self._catreq.reqREST("DeviceConfig", "/configs?path=/watering/min_time_between_messages_sec")
            if r.status and r.code_response == 200:
                self._min_time_between_messages = int(r.json_response["norm"])
                self._min_time_between_messages_crit = int(r.json_response["crit"])
            else:
                raise Exception(f"Error getting the min time between messages from the DeviceConfig ({r.code_response}): {r.json_response}")

            r = self._catreq.reqREST("DeviceConfig", "/configs?path=/watering/thresholds")
            if r.status and r.code_response == 200:
                self._airtemp_threshold_max = r.json_response["temp"]["max"]
                self._airtemp_threshold_min = r.json_response["temp"]["min"]
                self._airhum_threshold_max = r.json_response["airhum"]["max"]
                self._airhum_threshold_min = r.json_response["airhum"]["min"]
                self._soilhum_threshold_max = r.json_response["soilhum"]["max"]
                self._soilhum_threshold_min = r.json_response["soilhum"]["min"]
            else:
                raise Exception(f"Error getting the thresholds from the DeviceConfig ({r.code_response}): {r.json_response}")
            
            r = self._catreq.reqREST("DeviceConfig", "/configs?path=/system/location")
            if r.status and r.code_response == 200:
                self._lat = r.json_response["lat"]
                self._lon = r.json_response["lon"]
            else:
                raise Exception(f"Error getting the location from the DeviceConfig ({r.code_response}): {r.json_response}")

            r = self._catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list")
            if r.status and r.code_response == 200:
                self.logger.debug(f"Links: {r.json_response['v']}")
                self._links = Links(r.json_response["v"])
            else:
                raise Exception(f"Error getting the links from the DeviceConfig ({r.code_response}): {r.json_response}")

            self._catreq.subscribeMQTT("DeviceConfig", "/conf/system/location/lat")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/system/location/lat", self.onLatitude)
            self._catreq.subscribeMQTT("DeviceConfig", "/conf/system/location/lon")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/system/location/lon", self.onLongitude)

            self._catreq.subscribeMQTT("DeviceConfig", "/conf/watering/thresholds/temp/min")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/watering/thresholds/temp/min", self.onMinTemp)
            self._catreq.subscribeMQTT("DeviceConfig", "/conf/watering/thresholds/temp/max")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/watering/thresholds/temp/max", self.onMaxTemp)
            self._catreq.subscribeMQTT("DeviceConfig", "/conf/watering/thresholds/airhum/min")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/watering/thresholds/airhum/min", self.onMinAirHum)
            self._catreq.subscribeMQTT("DeviceConfig", "/conf/watering/thresholds/airhum/max")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/watering/thresholds/airhum/max", self.onMaxAirHum)
            self._catreq.subscribeMQTT("DeviceConfig", "/conf/watering/thresholds/soilhum/min")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/watering/thresholds/soilhum/min", self.onMinSoilHum)
            self._catreq.subscribeMQTT("DeviceConfig", "/conf/watering/thresholds/soilhum/max")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/watering/thresholds/soilhum/max", self.onMaxSoilHum)

            self._catreq.subscribeMQTT("DeviceConfig", "/conf/watering/min_time_between_messages_sec/crit")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/watering/min_time_between_messages_sec/crit", self.onMinTimeBetweenMessagesSecCrit)
            self._catreq.subscribeMQTT("DeviceConfig", "/conf/watering/min_time_between_messages_sec/norm")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/watering/min_time_between_messages_sec/norm", self.onMinTimeBetweenMessagesSecNorm)

            self._catreq.subscribeMQTT("DeviceConfig", "/conf/watering/enable")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/watering/enable", self.onEnable)

            self._catreq.subscribeMQTT("DeviceConfig", "/conf/watering/links/list")
            self._catreq.callbackOnTopic("DeviceConfig", "/conf/watering/links/list", self.onLinks)

            self._catreq.subscribeMQTT("RaspberryDevConn", "/+/airhumidity")
            self._catreq.callbackOnTopic("RaspberryDevConn", "/+/airhumidity", self.onAirHumidity)
            self._catreq.subscribeMQTT("RaspberryDevConn", "/+/airtemperature")
            self._catreq.callbackOnTopic("RaspberryDevConn", "/+/airtemperature", self.onAirTemperature)
            self._catreq.subscribeMQTT("RaspberryDevConn", "/+/terrainhumidity")
            self._catreq.callbackOnTopic("RaspberryDevConn", "/+/terrainhumidity", self.onTerrainHumidity)

        except Exception as e:

            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in Watering Initialization (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False

            self.logger.critical(f"Exception in Watering Initialization (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)
            raise e

    
    @cherrypy.tools.json_out()
    def GET(self, *path, **args):
        
        if len(path) == 0:
            return self.asjson_info("WateringControl endpoint!")
        else:
            if path[0] == "status":
                return self.asjson({
                    "asdrubale": {
                        "averages": {
                            "air_humidity": mean(self._avgAirHum.values()) if len(self._avgAirHum) > 0 else -1,
                            "air_temperature": mean(self._avgAirTemp.values()) if len(self._avgAirTemp) > 0 else -1,
                            "soil_humidity": mean(self._avgSoilHum.values()) if len(self._avgSoilHum) > 0 else -1,
                        },
                        "thresholds": {
                            "air_temperature": {
                                "max": self._airtemp_threshold_max,
                                "min": self._airtemp_threshold_min
                            },
                            "air_humidity": {
                                "max": self._airhum_threshold_max,
                                "min": self._airhum_threshold_min
                            },
                            "soil_humidity": {
                                "max": self._soilhum_threshold_max,
                                "min": self._soilhum_threshold_min
                            }
                        }
                    },
                    "location": {
                        "lat": self._lat,
                        "lon": self._lon
                    },
                    "telegram": {
                        "last_sent_msg_timestamp": self._last_sent_msg_timestamp,
                        "last_sent_msgcrit_timestamp": self._last_sent_msgcrit_timestamp,
                        "min_time_between_messages": self._min_time_between_messages,
                        "min_time_between_messages_crit": self._min_time_between_messages_crit
                    },
                    "enabled": self._enable
                })

        return self.asjson_error("Not found", 404)


    def onAirHumidity(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Air humidity: {payl}")

            status, json_response, code_response = self._catreq.reqREST("ThingSpeakAdaptor", f"/humidity?results=10&devid={payl['i']}")
            if status == True and code_response == 200:
                self.logger.debug(f"ThingSpeakAdaptor response: {json_response}")

                elements = [{"field1": element["field1"], "field2": element["field2"], "field3": element["field3"]} for element in json_response]
                lastTimestamp = float(sorted(elements, key=lambda x: x["field3"])[-1]["field3"])

                # check if the two timestamps are different, that means that the
                # received value has not been pushed to thingspeak yet
                if float(payl["t"]) > lastTimestamp:
                    elements = [*elements, {"field1": payl["v"], "field2": payl["i"], "field3": payl["t"]}]

                self.logger.debug(f"Elements: {elements}")
                self._avgAirHum[payl['i']] = mean([float(element["field1"]) for element in elements])

            else:
                self.logger.debug("Error making the request to ThingSpeakAdaptor")
            
            self._asdrubale(devid=payl['i'])
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onAirHumidity (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False

            self.logger.critical(f"Exception in onAirHumidity (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)

    
    def onAirTemperature(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Air temperature: {payl}")

            status, json_response, code_response = self._catreq.reqREST("ThingSpeakAdaptor", f"/temperature?results=10&devid={payl['i']}")
            if status == True and code_response == 200:
                self.logger.debug(f"ThingSpeakAdaptor response: {json_response}")

                elements = [{"field1": element["field1"], "field2": element["field2"], "field3": element["field3"]} for element in json_response]
                lastTimestamp = float(sorted(elements, key=lambda x: x["field3"])[-1]["field3"])

                # check if the two timestamps are different, that means that the
                # received value has not been pushed to thingspeak yet
                if float(payl["t"]) > lastTimestamp:
                    elements = [*elements, {"field1": payl["v"], "field2": payl["i"], "field3": payl["t"]}]

                self.logger.debug(f"Elements: {elements}")
                self._avgAirTemp[payl['i']] = mean([float(element["field1"]) for element in elements])
            
            else:
                self.logger.debug("Error making the request to ThingSpeakAdaptor")
            
            self._asdrubale(devid=payl['i'])
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onAirTemperature (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False

            self.logger.critical(f"Exception in onAirTemperature (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)

    def onTerrainHumidity(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Terrain humidity: {payl}")

            status, json_response, code_response = self._catreq.reqREST("ThingSpeakAdaptor", f"/soil?results=10&devid={payl['i']}")
            if status == True and code_response == 200:
                self.logger.debug(f"ThingSpeakAdaptor response: {json_response}")

                elements = [{"field1": element["field1"], "field2": element["field2"], "field3": element["field3"]} for element in json_response]
                lastTimestamp = float(sorted(elements, key=lambda x: x["field3"])[-1]["field3"])

                # check if the two timestamps are different, that means that the
                # received value has not been pushed to thingspeak yet
                if float(payl["t"]) > lastTimestamp:
                    elements = [*elements, {"field1": payl["v"], "field2": payl["i"], "field3": payl["t"]}]

                self.logger.debug(f"Elements: {elements}")
                self._avgSoilHum[payl['i']] = mean([float(element["field1"]) for element in elements])
            
            else:
                self.logger.debug("Error making the request to ThingSpeakAdaptor")
            
            self._asdrubale(devid=payl['i'])
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onTerrainHumidity (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False

            self.logger.critical(f"Exception in onTerrainHumidity (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)

    def onLinks(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Links: {payl}")
            self._links = Links(payl["v"])
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onLinks (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False

            self.logger.critical(f"Exception in onLinks (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)

    def onLatitude(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Latitude: {payl}")
            self._lat = payl["v"]
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onLatitude (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False
    
            self.logger.critical(f"Exception in onLatitude (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)
    
    def onLongitude(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Longitude: {payl}")
            self._lon = payl["v"]
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onLongitude (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False
    
            self.logger.critical(f"Exception in onLongitude (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)

    def onMinTemp(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
            
        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Min temperature: {payl}")
            self._airtemp_threshold_min = payl["v"]
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onMinTemp (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False
    
            self.logger.critical(f"Exception in onMinTemp (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)
    
    def onMaxTemp(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
                
        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Max temperature: {payl}")
            self._airtemp_threshold_max = payl["v"]
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onMaxTemp (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False
    
            self.logger.critical(f"Exception in onMaxTemp (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)

    def onMinAirHum(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
                    
        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Min air humidity: {payl}")
            self._airhum_threshold_min = payl["v"]
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onMinAirHum (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False
    
            self.logger.critical(f"Exception in onMinAirHum (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)

    def onMaxAirHum(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Max air humidity: {payl}")
            self._airhum_threshold_max = payl["v"]
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onMaxAirHum (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False
    
            self.logger.critical(f"Exception in onMaxAirHum (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)

    def onMinSoilHum(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Min soil humidity: {payl}")
            self._soilhum_threshold_min = payl["v"]
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onMinSoilHum (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False
    
            self.logger.critical(f"Exception in onMinSoilHum (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)


    def onMaxSoilHum(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Max soil humidity: {payl}")
            self._soilhum_threshold_max = payl["v"]
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onMaxSoilHum (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False
    
            self.logger.critical(f"Exception in onMaxSoilHum (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)


    def onMinTimeBetweenMessagesSecCrit(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Min time between messages (critical): {payl}")
            self._minTimeBetweenMessagesSecCrit = payl["v"]
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onMinTimeBetweenMessagesSecCrit (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False
    
            self.logger.critical(f"Exception in onMinTimeBetweenMessagesSecCrit (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)


    def onMinTimeBetweenMessagesSecNorm(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Min time between messages (normal): {payl}")
            self._minTimeBetweenMessagesSecNorm = payl["v"]
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onMinTimeBetweenMessagesSecNorm (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False
    
            self.logger.critical(f"Exception in onMinTimeBetweenMessagesSecNorm (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)
 

    def onEnable(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):

        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self.logger.debug(f"Enable: {payl}")
            self._enable = payl["v"]
            self._asdrubale()
        except Exception as e:
            sent = True
            try:
                r = self._catreq.reqREST("TelegramAdaptor", f"/sendMessage?text=Critical error in onEnable (system /status could be compromised): {str(e)}")
                if not r.status or r.code_response != 200:
                    raise Exception()
            except:
                sent = False
    
            self.logger.critical(f"Exception in onEnable (sent on telegram: {'yes' if sent else 'no'}): {str(e)}", exc_info=True)


    def _asdrubale(self, devid: int = None):

        if not self._enable:
            return

        if devid is None:
            a = self._avgAirHum.keys()
            b = self._avgSoilHum.keys()
            c = self._avgAirTemp.keys()

            d = [x for x in b if x in a]
            for did in [x for x in c if x in d]:
                self._asdrubale(did)

            return

        avgAirTemp = self._avgAirTemp.get(devid, -1)
        avgAirHum = self._avgAirHum.get(devid, -1)
        avgSoilHum = self._avgSoilHum.get(devid, -1)
        self.logger.debug(f"Executing the ASDRUBALE algorithm for raspi #{devid}: avgAirTemp: {avgAirTemp}, avgAirHum: {avgAirHum}, avgSoilHum: {avgSoilHum}")

        try:
            # logic for the watering control
            entered = False
            if avgAirTemp == -1 or avgAirHum == -1 or avgSoilHum == -1:
                return

            if self._avgSoilHum[devid] > self._soilhum_threshold_max:
                entered = True
                self.logger.debug("Soil humidity is too high, watering is not needed")
                self._toggle_switch(on=False, devid=devid)

            if self._avgSoilHum[devid] < self._soilhum_threshold_min:
                entered = True
                self.logger.debug("Soil humidity is too low, watering is needed")
                r = self._catreq.reqREST("OpenWeatherAdaptor", f"/currentweather?lat={self._lat}&lon={self._lon}")
                if r.status == True and r.code_response == 200:
                    if r.json_response["weather"][0]["main"] in {"Rain", "Snow", "Thunderstorm", "Drizzle"} and self._avgSoilHum > self._soilhum_threshold_max:
                        self.logger.debug("It is raining, watering is not needed")
                        self._toggle_switch(on=False, devid=devid)
                    else:
                        r = self._catreq.reqREST("OpenWeatherAdaptor", f"/forecastweather?lat={self._lat}&lon={self._lon}")
                        if r.status == True and r.code_response == 200:
                            if r.json_response["hourly"][5]["weather"][0]["main"] in {"Rain", "Snow", "Thunderstorm", "Drizzle"}:
                                self.logger.debug("It will rain, watering is not needed")
                                self._toggle_switch(on=False, devid=devid)
                            else:
                                if self._avgAirTemp[devid] > self._airtemp_threshold_max and self._avgAirHum[devid] < self._airhum_threshold_min:
                                    self.logger.debug("It is too hot, watering is needed")
                                    self._toggle_switch(on=True, devid=devid)
                                else:
                                    if self._last_sent_msgcrit_timestamp == -1 or time.time() - self._last_sent_msgcrit_timestamp > self._min_time_between_messages_crit:
                                        r = self._catreq.reqREST("TelegramAdaptor", "/sendMessage?text=Hey, the situation is critical. Do you want to /switch on the irrigation?")
                                        if r.status == True and r.code_response == 200:
                                            self.logger.debug("Sent the message to Telegram")
                                            self._last_sent_msgcrit_timestamp = time.time()
                                        else:
                                            raise Exception(f"Error contacting the Telegram Adaptor to send a message ({r.code_response}): {r.json_response}")
                        else:
                            raise Exception(f"Error while getting the forecast from the OpenWeatherAdaptor ({r.code_response}): {r.json_response}")
                else:
                    raise Exception(f"Error while getting the forecast from the OpenWeatherAdaptor ({r.code_response}): {r.json_response}")

            if not entered:
                if self._avgSoilHum[devid] < mean([self._soilhum_threshold_min, self._soilhum_threshold_max]):
                    self.logger.debug("Soil humidity is in the range, ask the user what to do")
                    if self._last_sent_msg_timestamp == -1 or time.time() - self._last_sent_msg_timestamp > self._min_time_between_messages:
                        r = self._catreq.reqREST("TelegramAdaptor", "/sendMessage?text=Hey, the situation is pretty normal (see /status for more details). Do you want to /switch on the irrigation?")
                        if r.status == True and r.code_response == 200:
                            self.logger.debug("Sent the message to Telegram")
                            self._last_sent_msg_timestamp = time.time()
                        else:
                            raise Exception(f"Error contacting the Telegram Adaptor to send a message ({r.code_response}): {r.json_response}")

        except Exception as e:
            self.logger.error(f"Error executing the ASDRUBALE algorithm: {str(e)}", exc_info=True)
            raise e 

    def _toggle_switch(self, on: bool, devid: int):

        for id in self._links.getAllArduinosLinksFromRaspberryId(devid):
            r = self._catreq.reqREST("ArduinoDevConn", f"/switch?state={'on' if on else 'off'}", devid=id)
            if r.status == True and r.code_response == 200:
                self.logger.debug(f"Toggled the switch for Arduino Device Connector #{id}")
            else:
                raise Exception(f"Error contacting the Arduino Device Connector #{devid} ({r.code_response}): {r.json_response}")



class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:
            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "WateringControl", ServiceType.SERVICE)

            self.addRESTEndpoint("/status")

            self.mount(WateringControlAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()