import io
import logging
import cherrypy

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
        self._th = WIOThread(target=self._airhumidity, name="Air Humidity Thread")
        self._th1 = WIOThread(target=self._airtemperature, name="Air Temperature Thread")
        self._th2 = WIOThread(target=self._terrainhumidity, name="Terrain Humidity Thread")
        upperRESTSrvcApp.subsribe_evt_stop(self._th.stop)
        upperRESTSrvcApp.subsribe_evt_stop(self._th1.stop)
        upperRESTSrvcApp.subsribe_evt_stop(self._th2.stop)
        self._th.run()
        self._th1.run()
        self._th2.run()

    def _airhumidity(self):
        while not self._th.is_stop_requested:
            self._th.wait(5)                                                   
            self._catreq.publishMQTT("RaspberryDevConn", "/airhumidity", "airhumiditypayload")
    
    def _airtemperature(self):
        while not self._th.is_stop_requested:
            self._th.wait(5)                                                   
            self._catreq.publishMQTT("RaspberryDevConn", "/airtemperature", "airtemperaturepayload")
        
    def _terrainhumidity(self):
        while not self._th.is_stop_requested:
            self._th.wait(5)                                                   
            self._catreq.publishMQTT("RaspberryDevConn", "/terrainhumidity", "terrainhumiditypayload")

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):
        if len(path) == 0:
            return self.asjson_info("Raspberry Device Connector Endpoint")
        elif path[0] == "airhumidity":
            return self.asjson("airhumidityvalue")
        elif path[0] == "airtemperature":
            return self.asjson("airtemperature")
        elif path[0] == "terrainhumidity":
            return self.asjson("terrainhumidity")
        return self.asjson("error")

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.INFO)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "RaspberryDevConn", ServiceType.DEVICE, ServiceSubType.RASPBERRY)
            self.addRESTEndpoint("/")
            self.addRESTEndpoint("/airhumidity", [EndpointParam("state")])
            self.addRESTEndpoint("/airtemperature", [EndpointParam("state")])
            self.addRESTEndpoint("/terrainhumidity", [EndpointParam("state")])
            self.addMQTTEndpoint("/airhumidity", "data of the air humidity from the DHT11")
            self.addMQTTEndpoint("/airtemperature", "data of the air temperature from the DHT11")
            self.addMQTTEndpoint("/terrainhumidity", "dafa of the terrain humidity from the arduino board")

            self.mount(RaspberryDevConnAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
