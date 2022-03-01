import io
import logging
import cherrypy

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import *

class ArduinoDevConnAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)

        self._onrpi = False
        try:
            with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
                if 'raspberry pi' in m.read().lower(): 
                    self._onrpi = True
        except Exception: 
            pass

        if self._onrpi:
            # setup connection to arduino
            pass

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if len(path) > 0:
            if path[0] == "switch":

                if not "state" in args:
                    cherrypy.response.status = 400
                    return self.asjson_error("Missing state argument")

                state = str(args["state"]).lower()
                if state != "on" and state != "off":
                    cherrypy.response.status = 400
                    return self.asjson_error("Valid states are: {on, off}")

                st = "on" if state == "on" else "off"
                self.logger.info(f"Arduino: switching {st}")

                # Do things
                is_on = st == "on" # to change w raspberry

                return self.asjson({"is_on": is_on})

        cherrypy.response.status = 404
        return self.asjson_error("invalid request")

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.INFO)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "ArduinoDevConn", ServiceType.DEVICE, ServiceSubType.ARDUINO)
            self.addRESTEndpoint("/switch", [EndpointParam("state")])

            self.mount(ArduinoDevConnAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
