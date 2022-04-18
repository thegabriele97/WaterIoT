import logging
import cherrypy

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.JSONManager import JSONManager

class WateringDatabaseAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._dbmngr = JSONManager(SettingsManager.relfile2abs("database.json"))

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if len(path) == 0:
            
            # return all
            return self.asjson(self._dbmngr.get("/"))

        elif len(path) == 1:
            if path[0] == "getByName":
                
                if not "name" in args:
                    return self.asjson_error("Missing parameter 'name'", 400)

                search = [i for i in self._dbmngr.get("/items") if i["name"] == args["name"]]
                if len(search) == 0:
                    return self.asjson_error(f"Item {args['name']} not found", 404)
                
                return self.asjson({"item": search[0]})

        return self.asjson_error("Not found", 404)

    @cherrypy.tools.json_out()
    def POST(self, *path, **args):

        if len(path) == 0:

            body = json.loads(cherrypy.request.body.read())
            res = self._check_body_correctness(body)
            if not res:
                return res

            lst = self._dbmngr.get("/items")
            for i in lst:
                if i["name"] == body["name"]:
                    return self.asjson_error("Item already exists", 409)

            lst.append(body)
            self._dbmngr.set("/items", lst)
            return self.asjson_info("Item added", 201) 

        return self.asjson_error("Not found", 404)

    @cherrypy.tools.json_out()
    def PUT(self, *path, **args):

        if len(path) == 0:

            body = json.loads(cherrypy.request.body.read())
            res = self._check_body_correctness(body)
            if not res:
                return res

            lst = self._dbmngr.get("/items")
            for i in lst:
                if i["name"] == body["name"]:
                    lst.remove(i)
                    lst.append(body)
                    self._dbmngr.set("/items", lst)
                    return self.asjson_info("Item updated", 200)

            return self.asjson_error("Item not found", 404)

        return self.asjson_error("Not found", 404)

    @cherrypy.tools.json_out()
    def DELETE(self, *path, **args):

        if len(path) == 1:
            if path[0] == "getByName":

                if not "name" in args:
                    return self.asjson_error("Missing parameter 'name'", 400)

                search = [i for i in self._dbmngr.get("/items") if i["name"] == args["name"]]
                if len(search) == 0:
                    return self.asjson_error(f"Item {args['name']} not found", 404)
                
                lst = self._dbmngr.get("/items")
                lst.remove(search[0])
                self._dbmngr.set("/items", lst)
                return self.asjson_info("Item deleted", 200)

        return self.asjson_error("Not found", 404)

    def _check_body_correctness(self, body):

        # check body correctness
        if not "name" in body:
            return self.asjson_error("Missing 'name'", 400)

        if not "thresholds" in body:
            return self.asjson_error("Missing 'thresholds'", 400)

        if not "temp" in body["thresholds"]:
            return self.asjson_error("Missing 'temp' in 'thresholds'", 400)

        if not "airhum" in body["thresholds"]:
            return self.asjson_error("Missing 'airhum' in 'thresholds'", 400)

        if not "soilhum" in body["thresholds"]:
            return self.asjson_error("Missing 'soilhum' in 'thresholds'", 400)
        
        if not "min" in body["thresholds"]["temp"] or not "max" in body["thresholds"]["temp"]:
            return self.asjson_error("Missing 'min' or 'max' in 'thresholds/temp'", 400)

        if not "min" in body["thresholds"]["airhum"] or not "max" in body["thresholds"]["airhum"]:
            return self.asjson_error("Missing 'min' or 'max' in 'thresholds/airhum'", 400)

        if not "min" in body["thresholds"]["soilhum"] or not "max" in body["thresholds"]["soilhum"]:
            return self.asjson_error("Missing 'min' or 'max' in 'thresholds/soilhum'", 400)

        return True

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.INFO)

        try:

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "WateringDatabase", ServiceType.SERVICE)
            self.addRESTEndpoint("/")
            self.addRESTEndpoint("/getByName", [EndpointParam("name")])

            self.mount(WateringDatabaseAPI(self, self._settings), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
