import logging
import cherrypy

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import *
from common.JSONManager import JSONManager

class DeviceConfigAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)
        self._confsmngr = JSONManager(SettingsManager.relfile2abs("confs.json"))

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if len(path) > 0:
            if path[0] == "configs":
                return self.asjson(self._confsmngr.get("/"))

        return self.asjson_error("request error", 404)

    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(self, *path, **args):

        if len(path) > 0:
            if path[0] == "configs":
                pass

        return self.asjson_error("request error", 404)


class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.INFO)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "DeviceConfig", ServiceType.SERVICE)
            self.addRESTEndpoint("/configs")
            self.addMQTTEndpoint("/conf/sensors/temp/sampleperiod", "Publish new value of sensors/temp/sampleperiod configuration when it changes")
            self.addMQTTEndpoint("/conf/sensors/airhum/sampleperiod", "Publish new value of sensors/temp/sampleperiod configuration when it changes")
            self.addMQTTEndpoint("/conf/sensors/soilhum/sampleperiod", "Publish new value of sensors/temp/sampleperiod configuration when it changes")

            self.mount(DeviceConfigAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
