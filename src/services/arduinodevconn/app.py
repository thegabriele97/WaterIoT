import io
import logging
import cherrypy
import smbus

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import *

class ArduinoDevConnAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)

        try:
            self.logger.debug(f"ENV ONRASPBERRY = {str(os.environ['ONRASPBERRY'])}")
            self._onrpi = str(os.environ["ONRASPBERRY"]) == "1"
        except KeyError:
            self._onrpi = False

        if self._onrpi:
            # setup connection to arduino
            self._bus = smbus.SMBus(settings.arduino.i2c_dev)
            self._ard_i2c_addr = int(settings.arduino.i2c_addr, 0)

            pass

        if not self._onrpi:
            self.logger.warning("Raspberry not found or error as occurred while Arduino init. Running as dummy device!")

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if len(path) > 0:
            if path[0] == "switch":

                if not "state" in args:
                    cherrypy.response.status = 400
                    return self.asjson_error("Missing state argument")

                st = str(args["state"]).lower()
                if st != "on" and st != "off":
                    cherrypy.response.status = 400
                    return self.asjson_error("Valid states are: {on, off}")

                self.logger.info(f"Arduino: switching {st}")

                if self._onrpi:
                    self._bus.write_byte_data(self._ard_i2c_addr, 0, 1 if st == "on" else 0)

                is_on = st == "on" # to change w raspberry
                r = {"is_on": is_on}
                self._catreq.publishMQTT("ArduinoDevConn", "/switch", json.dumps(r))

                return self.asjson(r)

        cherrypy.response.status = 404
        return self.asjson_error("invalid request")

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.INFO)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "ArduinoDevConn", ServiceType.DEVICE, ServiceSubType.ARDUINO)
            self.addRESTEndpoint("/switch", [EndpointParam("state")])
            self.addMQTTEndpoint("/switch", "updates on switch status")

            self.mount(ArduinoDevConnAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
