import logging
import cherrypy

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import *

class CalculatorAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if len(path) == 1 and path[0] == "sum":
            return self.asjson({"r": int(args["a"]) + int(args["b"]) + int(args.get("c", 0))})

        self._catreq.reqREST("arduinodevconn", "/switch?state=on", devid=0)
        r = self._catreq.reqREST("calculator", "/sum?a=2&b=3")
        self._catreq.reqREST("calculator", "/sum?a=2&b=3", RequestType.POST)
        self._catreq.publishMQTT("calculator", "/calcs", json.dumps({"d": r}))

        return self.asjson({"d": r})

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.INFO)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "Calculator", ServiceType.SERVICE)
            self.addRESTEndpoint("/")
            self.addRESTEndpoint("/sum", (EndpointParam("a"), EndpointParam("b"), EndpointParam("c", False)))
            self.addMQTTEndpoint("/calcs", "publishing dummy data")


            self.mount(CalculatorAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
