import logging
import cherrypy

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

        if len(path) <= 0:
            return self.asjson_info("Device Config API endpoint!")
        else:

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

                except KeyError:
                    return self.asjson_error("Wrong requst body")
                except Exception as e:
                    return self.asjson_error(f"Unable to update: {str(e)}")

        return self.asjson_error("request error", 404)


class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.INFO)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "DeviceConfig", ServiceType.SERVICE)
            self.addRESTEndpoint("/configs", [EndpointParam("path")])

            with open(SettingsManager.relfile2abs("confs.json")) as fp:
                keys = self._rec_dict(json.load(fp))
                for k in keys:
                    self.addMQTTEndpoint(f"/conf{k}", f"Publish new value of {k} configuration when it changes")

            self.mount(DeviceConfigAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))

    def _rec_dict(self, d: dict, path: str = "") -> list[str]:

        ret = []
        for k, v in d.items():

            p = f"{path}/{k}"
            if isinstance(v, dict):
                ret = [*ret, *self._rec_dict(v, p)]
            else:
                ret.append(p)
            
        return ret


if __name__ == "__main__":
    App()
