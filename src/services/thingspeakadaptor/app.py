import logging
import cherrypy
import requests

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import CatalogRequest

class ThingSpeakAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode, thingspeakkey) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)
        self._thingspeakkey = thingspeakkey

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if len(path) == 0:
            return self.asjson_info("ThingSpeak Adaptor Endpoint")

        cherrypy.response.status = 404
        return self.asjson_error("invalid request")

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            thinkspeakmapkey = os.environ['THINGSPEAKAPIKEY']
            self.logger.debug("thingspeak api key set to: " + thinkspeakmapkey)

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "ThingSpeakAdaptor", ServiceType.SERVICE)
            self.addRESTEndpoint("/")

            self.mount(ThingSpeakAPI(self, self._settings, thinkspeakmapkey), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
