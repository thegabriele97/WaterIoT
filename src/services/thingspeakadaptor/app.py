import logging
import cherrypy
import requests

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import CatalogRequest

class ThingSpeakAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode, thingspeakapikeytemperaturewrite, thingspeakapikeytemperatureread, thingspeakapikeyhumiditywrite, thingspeakapikeyhumidityread, channelidtemperature, channelidhumidity) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)
        self._thingspeakapikeytemperaturewrite = thingspeakapikeytemperaturewrite
        self._thingspeakapikeytemperatureread = thingspeakapikeytemperatureread
        self._thingspeakapikeyhumiditywrite = thingspeakapikeyhumiditywrite
        self._thingspeakapikeyhumidityread = thingspeakapikeyhumidityread
        self._channelidtemperature = channelidtemperature
        self._channelidhumidity = channelidhumidity

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if len(path) == 0:
            return self.asjson_info("ThingSpeak Adaptor Endpoint")
        elif path[0] == "temperaturewrite":
            r = requests.get(f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeytemperaturewrite}&field1={args['temp']}")
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return self.asjson_info(None)
        elif path[0] == "humiditywrite":
            r = requests.get(f"https://api.thingspeak.com/update?api_key={self._thingspeakapikeyhumiditywrite}&field1={args['hum']}")
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return self.asjson_info(None)
        elif path[0] == "temperatureread":
            r = requests.get(f"https://api.thingspeak.com/channels/{self._channelidtemperature}/feeds.json?api_key={self._thingspeakapikeytemperatureread}&results={args['hum']}")
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return r.json()['feeds']
        elif path[0] == "humidityread":
            r = requests.get(f"https://api.thingspeak.com/channels/{self._channelidhumidity}/feeds.json?api_key={self._thingspeakapikeyhumidityread}&results={args['hum']}")
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})
            return r.json()['feeds']


class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            thingspeakapikeytemperaturewrite = os.environ['THINGSPEAKAPIKEYTEMPERATUREWRITE']
            thingspeakapikeytemperatureread = os.environ['THINGSPEAKAPIKEYTEMPERATUREREAD']
            thingspeakapikeyhumiditywrite = os.environ['THINGSPEAKAPIKEYHUMIDITYWRITE']
            thingspeakapikeyhumidityread = os.environ['THINGSPEAKAPIKEYHUMIDITYREAD']
            channelidtemperature = os.environ['CHANNELIDTEMPERATURE']
            channelidhumidity = os.environ['CHANNELIDHUMIDITY']
            self.logger.debug("thingspeak api key write set to: " + thingspeakapikeytemperaturewrite + "and thinkspeak api key read set to: " + thingspeakapikeytemperatureread)

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "ThingSpeakAdaptor", ServiceType.SERVICE)
            self.addRESTEndpoint("/")
            self.addRESTEndpoint("/temperaturewrite", [EndpointParam("temp")])
            self.addRESTEndpoint("/humiditywrite", [EndpointParam("hum")])
            self.addRESTEndpoint("/temperatureread", [EndpointParam("hum", False)])
            self.addRESTEndpoint("/humidityread", [EndpointParam("hum", False)])

            self.mount(ThingSpeakAPI(self, self._settings, thingspeakapikeytemperaturewrite, thingspeakapikeytemperatureread, thingspeakapikeyhumiditywrite, thingspeakapikeyhumidityread, channelidtemperature, channelidhumidity), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
