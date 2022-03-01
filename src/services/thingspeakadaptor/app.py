import logging
import cherrypy
import requests

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import CatalogRequest

class ThingSpeakAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode, thingspeakapikeywrite, thingspeakapikeyread) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)
        self._thingspeakapikeywrite = thingspeakapikeywrite
        self._thingspeakapikeyread = thingspeakapikeyread

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if len(path) == 0:
            return self.asjson_info("ThingSpeak Adaptor Endpoint")
        elif path[0] == "temperaturewrite":
            r = requests.get(f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeywrite}&field1={args['temp']}")
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return self.asjson_info(None)
        elif path[0] == "humiditywrite":
            r = requests.get(url)

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            thinkspeakapikeywrite = os.environ['THINGSPEAKAPIKEYTEMPERATUREWRITE']
            thinkspeakapikeyread = os.environ['THINGSPEAKAPIKEYTEMPERATUREREAD']
            self.logger.debug("thingspeak api key write set to: " + thinkspeakapikeywrite + "and thinkspeak api key read set to: " + thinkspeakapikeyread)

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "ThingSpeakAdaptor", ServiceType.SERVICE)
            self.addRESTEndpoint("/")
            self.addRESTEndpoint("/temperaturewrite", [EndpointParam("temp")])

            self.mount(ThingSpeakAPI(self, self._settings, thinkspeakapikeywrite, thinkspeakapikeyread), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
