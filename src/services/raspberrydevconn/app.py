import io
import sys
import logging
import cherrypy
import paho.mqtt.client as mqtt
import smbus

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import *
from common.WIOThread import WIOThread


class RaspberryDevConnAPI(RESTBase):
    def __init__(self, upperRESTSrvcApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)

        # start the connection with the board. If the board is not connected instance a dummy device
        try:
            self.logger.debug(f"ENV ONRASPBERRY = {str(os.environ['ONRASPBERRY'])}")
            self._onrpi = str(os.environ["ONRASPBERRY"]) == "1"
        except KeyError:
            self._onrpi = False

        if self._onrpi:
            import Adafruit_DHT

            # setup connection to arduino
            self._bus = smbus.SMBus(settings.arduino.i2c_dev)
            self._ard_i2c_addr = int(settings.arduino.i2c_addr, 0)

            # setup connection to DHT11
            self.sensor = Adafruit_DHT.DHT11
            self.logger.debug(type(self.sensor))
            self.pin = "4"
            self.logger.debug(type(self.pin))
            humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
            if humidity is not None and temperature is not None:
                self.logger.debug("Sensor connected correcly")
            else:
                self.logger.warning("Sensor not connected")
            pass

        if not self._onrpi:
            self.logger.warning(
                "Raspberry not found or error as occurred while Arduino init. Running as dummy device!"
            )

        # Initialize the thread for managing the read of the parameters
        self._th = WIOThread(target=self._airhumidity, name="Air Humidity Thread")
        self._th1 = WIOThread(
            target=self._airtemperature, name="Air Temperature Thread"
        )
        self._th2 = WIOThread(
            target=self._terrainhumidity, name="Terrain Humidity Thread"
        )
        upperRESTSrvcApp.subsribe_evt_stop(self._th.stop)
        upperRESTSrvcApp.subsribe_evt_stop(self._th1.stop)
        upperRESTSrvcApp.subsribe_evt_stop(self._th2.stop)

        # Retrieve, by doing a GET request to the device config, the value of the sampleperiod of the parameters
        self.wait_air_temp = (
            self._catreq.reqREST(
                "DeviceConfig", "/configs?path=/sensors/temp/sampleperiod"
            ).json_response["v"]
            / 1000
        )
        self.wait_air_hum = (
            self._catreq.reqREST(
                "DeviceConfig", "/configs?path=/sensors/airhum/sampleperiod"
            ).json_response["v"]
            / 1000
        )
        self.wait_soil_hum = (
            self._catreq.reqREST(
                "DeviceConfig", "/configs?path=/sensors/soilhum/sampleperiod"
            ).json_response["v"]
            / 1000
        )

        # Subscribe to mqtt topics where the data of the sampleperiod will be published and declare the function that will be executed when a value is published
        self._catreq.subscribeMQTT("DeviceConfig", "/conf/sensors/temp/sampleperiod")
        self._catreq.callbackOnTopic(
            "DeviceConfig", "/conf/sensors/temp/sampleperiod", self.onMessageReceiveTemp
        )
        self._catreq.subscribeMQTT("DeviceConfig", "/conf/sensors/airhum/sampleperiod")
        self._catreq.callbackOnTopic(
            "DeviceConfig",
            "/conf/sensors/airhum/sampleperiod",
            self.onMessageReceiveAirhum,
        )
        self._catreq.subscribeMQTT("DeviceConfig", "/conf/sensors/soilhum/sampleperiod")
        self._catreq.callbackOnTopic(
            "DeviceConfig",
            "/conf/sensors/soilhum/sampleperiod",
            self.onMessageReceiveSoilhum,
        )

        # Start the threads
        self._th.run()
        self._th1.run()
        self._th2.run()

    # function of the threads
    def _airhumidity(self):
        while not self._th.is_stop_requested:
            self.humidity = 50
            
            if self._onrpi:
                self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)

            self._catreq.publishMQTT(
                "RaspberryDevConn", "/airhumidity", self.asjson(self.humidity)
            )
            self._th.wait(self.wait_air_hum)

    # function of the threads
    def _airtemperature(self):
        while not self._th1.is_stop_requested:
            self.temperature = 25
            
            if self._onrpi:
                self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
            
            self._catreq.publishMQTT(
                "RaspberryDevConn", "/airtemperature", self.asjson(self.temperature)
            )
            self._th1.wait(self.wait_air_temp)

    # function of the threads
    def _terrainhumidity(self):
        while not self._th2.is_stop_requested:

            # set a default value of 20 in case you are not connected to the board
            data = 20

            # if you are on the rpi, ask arduino for the value of the soil humidity
            if self._onrpi:
                data = self._bus.read_word_data(self._ard_i2c_addr, 5)
                mask = 0x3FF
                data = data & mask

            self._catreq.publishMQTT(
                "RaspberryDevConn", "/terrainhumidity", self.asjson(data)
            )

            self._th2.wait(self.wait_soil_hum)

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):
        if len(path) == 0:
            return self.asjson_info("Raspberry Device Connector Endpoint")
        elif path[0] == "airhumidity":
            self.humidity = 50
            if self._onrpi:
                self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
            return self.asjson(self.humidity)
        elif path[0] == "airtemperature":
            self.temperature = 25
            if self._onrpi:
                self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
            return self.asjson(self.temperature)
        elif path[0] == "terrainhumidity":

            # set a default value of 20 in case you are not connected to the board
            data = 20

            # if you are on the rpi, ask arduino for the value of the soil humidity
            if self._onrpi:
                data = self._bus.read_word_data(self._ard_i2c_addr, 5)
                mask = 0x3FF
                data = data & mask

            return self.asjson(data)

        return self.asjson("error")

    # function for the callback of the mqtt topic when a new value for the sampleperiod of the temperature is received
    def onMessageReceiveTemp(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        string = msg.payload.decode("ascii")
        json_string = json.loads(string)
        self.wait_air_temp = json_string["v"] / 1000
        self.logger.debug(self.wait_air_temp)
        self._th1.restart()

    # function for the callback of the mqtt topic when a new value for the sampleperiod of the air humidity is received
    def onMessageReceiveAirhum(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        string = msg.payload.decode("ascii")
        json_string = json.loads(string)
        self.wait_air_hum = json_string["v"] / 1000
        self.logger.debug(self.wait_air_hum)
        self._th.restart()

    # function for the callback of the mqtt topic when a new value for the sampleperiod of the soil humidity is received
    def onMessageReceiveSoilhum(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        string = msg.payload.decode("ascii")
        json_string = json.loads(string)
        self.wait_soil_hum = json_string["v"] / 1000
        self.logger.debug(self.wait_soil_hum)
        self._th2.restart()



class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            # open the json file with the configuration of the devices
            self._settings = SettingsManager.json2obj(
                SettingsManager.relfile2abs("settings.json"), self.logger
            )
            self.create(
                self._settings,
                "RaspberryDevConn",
                ServiceType.DEVICE,
                ServiceSubType.RASPBERRY,
            )

            # Add all the necessary endpoints both for REST and MQTT
            self.addRESTEndpoint("/")
            self.addRESTEndpoint(
                "/airhumidity", endpointTypeSub=EndpointTypeSub.RESOURCE
            )
            self.addRESTEndpoint(
                "/airtemperature", endpointTypeSub=EndpointTypeSub.RESOURCE
            )
            self.addRESTEndpoint(
                "/terrainhumidity", endpointTypeSub=EndpointTypeSub.RESOURCE
            )
            self.addMQTTEndpoint(
                "/airhumidity", "data of the air humidity from the DHT11"
            )
            self.addMQTTEndpoint(
                "/airtemperature", "data of the air temperature from the DHT11"
            )
            self.addMQTTEndpoint(
                "/terrainhumidity",
                "dafa of the terrain humidity from the arduino board",
            )

            self.mount(RaspberryDevConnAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
