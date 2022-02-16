import logging
import cherrypy

import psutil

from common.RESTBase import RESTBase
from common.RESTServiceApp import RESTServiceApp
from common.SettingsManager import SettingsManager
from common.SettingsNode import SettingsNode

class CatalogAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, settings.getattrORdef('indent_level', 4))

    def GET(self, *path, **args):

        if len(path) <= 0:
            return self.asjson_info("Catalog API endpoint!")
        elif path[0] == "getSysInfo".lower():
            return self.asjson({
                "cpu_perc": psutil.cpu_percent(),
                "ram_perc": psutil.virtual_memory()[2]
            })
        else:
            cherrypy.response.status = 404
            return self.asjson_error("invalid request")


class App(RESTServiceApp):
    def __init__(self) -> None:
        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"))
            self.mount("/catalog", CatalogAPI(self, self._settings), self.conf)
            self.loop(port=self._settings.rest_server.port, host=self._settings.rest_server.host)

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
