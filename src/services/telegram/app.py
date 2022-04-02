import logging
import cherrypy

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import CatalogRequest
from TelMan import MyBot

class TelegramAdaptorAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp: WIOTRestApp, settings: SettingsNode, telegramkey) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)
        self._bot = MyBot(telegramkey, self.logger, self._catreq, settings)
        upperRESTSrvcApp.subsribe_evt_stop(self._bot._bot_th.stop)

    @cherrypy.tools.json_out()
    def GET(self, *path, **args): # /sendMessage?text=<message> where message is the string that is going to be printed on tel chat 

        if len(path)>0 and path[0] == "sendMessage":
            try:
                if not "text" in args: # check correct HTTP argument
                    return self.asjson_error("Missing text argument",400)
                
                cnt = 0
                for id in self._bot._encr.getIDs():
                    self.logger.debug(id)
                    try:
                        self._bot.bot.sendMessage(id,args["text"])
                        cnt += 1
                    except Exception as e:
                        self.logger.warn("Error sending message to user %s: %s" % (id, e))

                return self.asjson({"n": cnt})

            except Exception as e:
                self.logger.error(f"Error occurred in sending message: {str(e)}") # exception rised if is sent a message
                return self.asjson_error(f"Server error",500)                         # on chat ( chat_id is retrived)
            
        return self.asjson_error("Invalid request",404)

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.DEBUG)

        try:

            telegrammapkey = os.environ['TELEGRAMAPAPIKEY']
            self.logger.debug("Telegram api key set to: " + telegrammapkey)

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "TelegramAdaptor", ServiceType.SERVICE)
            self.addRESTEndpoint("/sendMessage", [EndpointParam("text", True)])

            self.mount(TelegramAdaptorAPI(self, self._settings, telegrammapkey), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
