import logging
from weakref import KeyedRef
import cherrypy
from numpy import isin

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
                if "path" not in args:
                    return self.asjson_error("Path not specified")
                
                try:
                    d = self.asjson(self._confsmngr.get(f"/{str(args['path'][1:])}"))
                    if isinstance(d, dict):
                        return self.asjson(d)
                    else:
                        return self.asjson({"v": d})
                except KeyError:
                    return self.asjson_error("Not found", 404)

        return self.asjson_error("request error", 404)

    @cherrypy.tools.json_out()
    def PUT(self, *path, **args):

        if len(path) > 0:
            if path[0] == "configs":

                if "path" not in args:
                    return self.asjson_error("Path not specified")

                p = f"/{str(args['path'][1:])}"
                body = json.loads(cherrypy.request.body.read())
                try:
                    self._confsmngr.set(p, body["v"])

                    d = self.asjson(self._confsmngr.get(p))
                    
                    if isinstance(d, dict):
                        r = d
                    else:
                        r = {"v": d}
                    
                    self._catreq.publishMQTT("DeviceConfig", f"/conf{p}", json.dumps(r))
                    return self.asjson(r)

                except ValueError as e:
                    return self.asjson_error(f"Unable to update: {str(e)}")
                except KeyError:
                    return self.asjson_error("Not found", 404)

        return self.asjson_error("request error", 404)


class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.INFO)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "DeviceConfig", ServiceType.SERVICE)
            self.addRESTEndpoint("/configs", [EndpointParam("path")])
            self.addMQTTEndpoint("/conf/sensors/temp/sampleperiod", "Publish new value of sensors/temp/sampleperiod configuration when it changes")
            self.addMQTTEndpoint("/conf/sensors/airhum/sampleperiod", "Publish new value of sensors/airhum/sampleperiod configuration when it changes")
            self.addMQTTEndpoint("/conf/sensors/soilhum/sampleperiod", "Publish new value of sensors/soilhum/sampleperiod configuration when it changes")

            self.mount(DeviceConfigAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
