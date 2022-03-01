import logging
import json

import cherrypy

class RESTBase:
    exposed = True

    def __init__(self, upperRESTSrvcApp: object, indent_lvl: int) -> None:
        self._upperRESTSrvcApp = upperRESTSrvcApp;

    def asjson(self, data: dict):
        return data

    def asjson_error(self, data):
        return {"error": data}
    
    def asjson_info(self, data):
        return {"info": data}

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):
        cherrypy.response.status = 400
        return self.asjson_error("bad request")

    @cherrypy.tools.json_out()
    def POST(self, *path, **args):
        cherrypy.response.status = 400
        return self.asjson_error("bad request")

    @cherrypy.tools.json_out()
    def PUT(self, *path, **args):
        cherrypy.response.status = 400
        return self.asjson_error("bad request")

    @cherrypy.tools.json_out()
    def DELETE(self, *path, **args):
        cherrypy.response.status = 400
        return self.asjson_error("bad request")

    @property
    def logger(self) -> logging.Logger:
        return self._getattribute("logger");

    def _getattribute(self, name: str):
        return getattr(self._upperRESTSrvcApp, name)