import logging
import inspect
import os
from collections import namedtuple

import cherrypy

from common.RESTBase import RESTBase
from common.ServiceApp import ServiceApp

class RESTServiceApp(ServiceApp):

    def __init__(self, log_stdout_level: int = logging.INFO, log_filename: str = None) -> None:
        super().__init__(log_stdout_level, log_filename)

    def mounts(self, mounts: dict[str, tuple[RESTBase, dict]]):
        for k, v in mounts:
            mnt = self.mount_tuple(v)
            self.mount(k, mnt.root, mnt.config)

    def mount(self, path: str, root: RESTBase, conf: dict):
            self.logger.info(f"CherryPy tree mounting {type(root)} @ '{path}'")
            cherrypy.tree.mount(root, path, conf)

    def loop(self, port: int, host: str):
        cherrypy.config.update({
            'server.socket_port': port,
            'server.socket_host': '0.0.0.0'
        })
        
        class CustomHandler(cherrypy._cplogging.logging.Handler):

            def __init__(self, thelogger: logging.Logger) -> None:
                super().__init__(logging.NOTSET)
                self._logger = thelogger;

            def emit(self, record: logging.LogRecord):
                msg_host = record.msg.split('-')[0] 
                if msg_host == record.msg:
                    msg_host = ""

                msg = f"{msg_host}{record.msg.split('] ')[-1]} {record.exc_info}"
                self._logger.log(level=record.levelno, msg=msg, exc_info=record.exc_info, stack_info=record.stack_info)

        access_log = cherrypy.log.access_log
        for handler in tuple(access_log.handlers):
            access_log.removeHandler(handler)
        
        cherrypy.log.access_log.setLevel(logging.NOTSET)
        cherrypy.log.access_log.addHandler(CustomHandler(self.logger))

        error_log = cherrypy.log.error_log
        for handler in tuple(error_log.handlers):
            error_log.removeHandler(handler)

        # cherrypy.log.error_log.setLevel(logging.NOTSET)
        cherrypy.log.error_log.addHandler(CustomHandler(self.logger))

        if hasattr(cherrypy.engine, 'signal_handler'):
            cherrypy.engine.signal_handler.subscribe()

        cherrypy.engine.start()
        cherrypy.engine.block()

    @property
    def conf(self):
        return {
            '/': {
                'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
                'tools.staticdir.root': os.path.abspath('/'.join(inspect.stack()[1].filename.split('/')[0:-1]))
            },
        }

    @property
    def mount_tuple():
        return namedtuple("mount_tuple", ['root', 'config'])

