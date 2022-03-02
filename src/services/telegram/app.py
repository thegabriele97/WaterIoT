import logging
import cherrypy

from common.WIOTRestApp import *
from common.SettingsManager import *
from common.SettingsNode import *
from common.RESTBase import RESTBase
from common.CatalogRequest import CatalogRequest
from TelMan import MyBot

class TelegramAdaptorAPI(RESTBase):

    def __init__(self, upperRESTSrvcApp, settings: SettingsNode, telegramkey) -> None:
        super().__init__(upperRESTSrvcApp, 0)
        self._catreq = CatalogRequest(self.logger, settings)
        self._bot = MyBot(telegramkey)

    @cherrypy.tools.json_out()
    def GET(self, *path, **args):

        if path[0] == "sendMessage":
            print("branch taken")
            a = self._bot.bot.sendMessage(self._bot.chat_ID,args["text"])

        # r = self._catreq.reqREST("openweatheradaptor", "/currentweather?as=2")

        return a

class App(WIOTRestApp):
    def __init__(self) -> None:

        super().__init__(log_stdout_level=logging.INFO)

        try:

            telegrammapkey = os.environ['TELEGRAMAPAPIKEY']
            self.logger.debug("Telegram api key set to: " + telegrammapkey)

            self._settings = SettingsManager.json2obj(SettingsManager.relfile2abs("settings.json"), self.logger)
            self.create(self._settings, "TelegramAdaptor", ServiceType.SERVICE)
            self.addRESTEndpoint("/turnON", [EndpointParam("a", True)])

            self.mount(TelegramAdaptorAPI(self, self._settings, telegrammapkey), self.conf)
            self.loop()

        except Exception as e:
            self.logger.exception(str(e))


if __name__ == "__main__":
    App()
