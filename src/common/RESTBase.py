import logging
import json

import cherrypy

class RESTBase:
    exposed = True

    def __init__(self, upperRESTSrvcApp: object, indent_lvl: int) -> None:
        self._upperRESTSrvcApp = upperRESTSrvcApp;

    def asjson(self, data: dict, statuscode: int = 200):
        cherrypy.response.status = statuscode
        return data

    def asjson_error(self, data, statuscode: int = 400):
        cherrypy.response.status = statuscode
        return {"error": data}
    
    def asjson_info(self, data, statuscode: int = 200):
        cherrypy.response.status = statuscode
        return {"info": data}

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):
        return self.asjson_error("bad request", 405)

    @cherrypy.tools.json_out()
    def POST(self, *path, **args):
        return self.asjson_error("bad request", 405)

    @cherrypy.tools.json_out()
    def PUT(self, *path, **args):
        return self.asjson_error("bad request", 405)

    @cherrypy.tools.json_out()
    def DELETE(self, *path, **args):
        return self.asjson_error("bad request", 405)

    @property
    def logger(self) -> logging.Logger:
        return self._getattribute("logger");

    def _getattribute(self, name: str):
        return getattr(self._upperRESTSrvcApp, name)