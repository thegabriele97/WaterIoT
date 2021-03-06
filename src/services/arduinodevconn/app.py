import io
import logging
import cherrypy
import smbus

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import *
from common.Sensor import Sensor

class ArduinoDevConnAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)
        self._devid = settings.getattrORdef("deviceid", 0)

        try:
            self.logger.debug(f"ENV ONRASPBERRY = {str(os.environ['ONRASPBERRY'])}")
            self._onrpi = str(os.environ["ONRASPBERRY"]) == "1"
        except KeyError:
            self._onrpi = False

        if self._onrpi:
            # setup connection to arduino
            self._bus = smbus.SMBus(settings.arduino.i2c_dev)
            self._ard_i2c_addr = int(settings.arduino.i2c_addr, 0)

        if not self._onrpi:
            self.logger.warning("Raspberry not found or error as occurred while Arduino init. Running as dummy device!")

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if len(path) <= 0:
            return self.asjson_info("Arduino Device Connector API endpoint!")
        else:
            if path[0] == "switch":

                if not "state" in args:
                    return self.asjson_error("Missing state argument", 400)

                st = str(args["state"]).lower()
                if st != "on" and st != "off":
                    return self.asjson_error("Valid states are: {on, off}", 400)

                self.logger.info(f"Arduino: switching {st}")

                if self._onrpi:
                    self._bus.write_byte_data(self._ard_i2c_addr, 0, 1 if st == "on" else 0)

                is_on = st == "on" # to change w raspberry

                r = Sensor("ardsw", is_on, None, self._devid).JSON
                self._catreq.publishMQTT("ArduinoDevConn", "/switch", json.dumps(r), devid=self._devid)

                return self.asjson(r)

        return self.asjson_error("invalid request", 404)

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "ArduinoDevConn", ServiceType.DEVICE, ServiceSubType.ARDUINO, devid=self._settings.getattrORdef("deviceid", 0))
            self.addRESTEndpoint("/switch", [EndpointParam("state")])
            self.addMQTTEndpoint("/switch", "updates on switch status")

            self.mount(ArduinoDevConnAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
