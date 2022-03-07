import logging
import cherrypy
import requests

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import CatalogRequest

class OpenWeatherAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode, openweatherkey) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)
        self._openweathersecret = openweatherkey

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if len(path) == 0:
            return self.asjson_info("OpenWeather Adaptor Endpoint")
        elif path[0] == "currentweather":
            r = requests.get(f"http://api.openweathermap.org/data/2.5/weather?lat={args['lat']}&lon={args['lon']}&units=metric&appid={self._openweathersecret}")
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})

            return self.asjson({
                "temp": r.json()["main"]["temp"],
                "pressure": r.json()["main"]["pressure"],
                "humidity": r.json()["main"]["humidity"],
                "weather": r.json()["weather"]
            })
        elif path[0] == "forecastweather":
            r = requests.get(f"http://api.openweathermap.org/data/2.5/onecall?exclude=minutely,current,alerts,daily&lat={args['lat']}&lon={args['lon']}&units=metric&appid={self._openweathersecret}")
            if r.status_code != 200:
                cherrypy.response.status = 400
                return self.asjson_error({"response": r.json()})

            return self.asjson({
                "hourly": [
                    {
                        "timestamp": v["dt"],
                        "temp": v["temp"],
                        "pressure": v["pressure"],
                        "humidity": v["humidity"],
                        "weather": v["weather"]
                    } for v in r.json()["hourly"]
                ]
            })

        cherrypy.response.status = 404
        return self.asjson_error("invalid request")

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            openweatermapkey = os.environ['OPENWETHERMAPAPIKEY']
            self.logger.debug("openweathermap.com api key set to: " + openweatermapkey)

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "OpenWeatherAdaptor", ServiceType.SERVICE)
            self.addRESTEndpoint("/")
            self.addRESTEndpoint("/currentweather", (EndpointParam("lat"), EndpointParam("lon")))
            self.addRESTEndpoint("/forecastweather", (EndpointParam("lat"), EndpointParam("lon")))

            self.mount(OpenWeatherAPI(self, self._settings, openweatermapkey), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
