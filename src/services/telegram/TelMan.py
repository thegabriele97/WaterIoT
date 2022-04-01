import telepot
import time
from telepot.loop import MessageLoop
from telepot.namedtuple import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
import json
import requests
import logging
from encryption import Encryption
from common.CatalogRequest import *
from common.WIOThread import WIOThread
from SuperTelepotBot import SuperTelepotBot

class MyBot:
   
    def __init__(self, token, logger, catreq, settings):
        # Local token
        self.catreq = catreq
        self.logger : logging.Logger = logger
        self.tokenBot=token
        self._update_id = None
        self._settings = settings
        self._encr = Encryption()
        #Catalog token
        #self.tokenBot=requests.get("http://catalogIP/telegram_token").json()["telegramToken"]
        self.bot = SuperTelepotBot(self.tokenBot)
        self.bot.setCommands(self._settings.telegram.commands.toDict())

        self._bot_th = WIOThread(target=self._handler_bot_th, name="Telegram Bot Handler")
        self._bot_th.run()

    def _handler_bot_th(self):

        while not self._bot_th.is_stop_requested:
            
            response = None
            try:
                response = self.bot.getUpdates(offset=self._update_id); # getting all last messages from last poll
            except:
                self.logger.exception("Bad exception occurred! Stopping Telegram Bot Handler..")
                while not self._bot_th.is_stop_requested:
                    self._bot_th.wait(60)

                continue

            for resp in response:
                self._update_id = resp["update_id"] + 1

                try:
                    self.on_chat_message(resp["message"]) # for each new message, call on_chat_message
                except Exception as e:
                    self.logger.exception(f"Exception occurred while handling a Telegram message: {str(e)}")

            self._bot_th.wait(self._settings.telegram.poll_time)


    def on_chat_message(self,msg):

        content_type, chat_type ,chat_ID = telepot.glance(msg)
        if "location" in msg :
            if not self._encr.checkID(chat_ID) :
                self.bot.sendMessage(chat_ID, "Unsubscribed user. Please insert the password using /psw <password> command", reply_markup=ReplyKeyboardRemove())
            else:    
                self.catreq.reqREST("DeviceConfig","/configs?path=/system/location/lat",RequestType.PUT,{"v": float(msg["location"]["latitude"])})
                self.catreq.reqREST("DeviceConfig","/configs?path=/system/location/lon",RequestType.PUT,{"v": float(msg["location"]["longitude"])})
                self.bot.sendMessage(chat_ID, "location set properly", reply_markup=ReplyKeyboardRemove())
        elif "text" in msg:
            message=msg["text"]
            if message.split()[0]=="/psw":
                if len(message.split()) == 1:
                    self.bot.sendMessage(chat_ID, "No password. Please, write a password after the command.", reply_markup=ReplyKeyboardRemove())
                else :
                    if self._encr.checkPassword(message.split()[1]):
                        self._encr.addID(chat_ID) # for some reason it return the id twice from getupdate
                        self.bot.sendMessage(chat_ID, "Correct password. The user is now subscribed and can access the functionality.", reply_markup=ReplyKeyboardRemove())
                    else :
                        self.bot.sendMessage(chat_ID, "Wrond password", reply_markup=ReplyKeyboardRemove())
            elif not self._encr.checkID(chat_ID) :
                self.bot.sendMessage(chat_ID, "Unsubscribed user. Please insert the password using /psw <password> command", reply_markup=ReplyKeyboardRemove())
            else:
                if message.split()[0] == "/config":
                    if len(message.split()) != 3:
                        self.bot.sendMessage(chat_ID, "No parameter. Please select one sensor (<temp>,<airhum>,<soilhum>) as first parameter and a value as second", reply_markup=ReplyKeyboardRemove())
                    elif message.split()[1] not in ["temp", "airhum","soilhum"]:
                        self.bot.sendMessage(chat_ID, "Wrong parameter. Please select one sensor(<temp>,<airhum>,<soilhum>) as first parameter and a value as second", reply_markup=ReplyKeyboardRemove())
                    else:
                        try: # verify if the value is an integer
                            self.catreq.reqREST("DeviceConfig",f"/configs?path=/sensors/{message.split()[1]}/sampleperiod",RequestType.PUT,{"v": int(message.split()[2])})
                        except ValueError:
                            self.bot.sendMessage(chat_ID,"Please insert an integer value", reply_markup=ReplyKeyboardRemove())
                elif message.split()[0] == "/pos" :
                    if len(message.split()) != 3:
                        self.bot.sendMessage(chat_ID, " No latitute and longitude values inserted.")
                    else:
                        try: # verify if the value is an integer
                            self.catreq.reqREST("DeviceConfig","/configs?path=/system/location/lat",RequestType.PUT,{"v": float(message.split()[1])})
                            self.catreq.reqREST("DeviceConfig","/configs?path=/system/location/lon",RequestType.PUT,{"v": float(message.split()[2])})
                        except ValueError:
                            self.bot.sendMessage(chat_ID,"Please insert numerical values", reply_markup=ReplyKeyboardRemove())
                elif message == "/start" or message == "/help":
                    self.bot.sendMessage(chat_id=chat_ID, parse_mode="MarkdownV2", reply_markup=ReplyKeyboardRemove(), text=(
                "Hello\\!\n"
                "Here the commands:\n"
                "*/psw <password\\>* \\- Subscribe the user\n"
                "*/switch <on/off\\>* \\- Turn on or off the irrigator\n"
                "*/getairt* \\- Retrive temperature of the air\n"
                "*/getairu*  \\- Retrive umidity of the air\n"
                "*/getsoilu* \\- Retrive umidity of the soil\n"
                "*/pos/* \\- Sets latitude and longitude where retrive weather forecasting\n"
                "*/config* \\(<temp\\>\\|<airhum\\>\\|<soilhum\\>\\) <value\\> \\- Config the sensors: sets the period of sampling of the sensors\n"))
                elif message == "/getairt":
                    self.bot.sendMessage(chat_ID,"You will get air temperature", reply_markup=ReplyKeyboardRemove())
                    self.bot.sendMessage(chat_ID,self.catreq.reqREST("RaspberryDevConn","/airtemperature"), reply_markup=ReplyKeyboardRemove())
                elif message == "/getairu":
                    self.bot.sendMessage(chat_ID,"You will get air umidity", reply_markup=ReplyKeyboardRemove())
                    self.bot.sendMessage(chat_ID,self.catreq.reqREST("RaspberryDevConn","/airhumidity"), reply_markup=ReplyKeyboardRemove())
                elif message == "/getsoilu":
                    self.bot.sendMessage(chat_ID,"You will get soil umidity")
                    self.bot.sendMessage(chat_ID,self.catreq.reqREST("RaspberryDevConn","/terrainhumidity"), reply_markup=ReplyKeyboardRemove())
                elif message.split()[0]=="/switch":
                    if len(message.split()) == 1:
                        self.bot.sendMessage(chat_id=chat_ID,
                            text="No parameter. Please, use '/switch on' or '/switch off'.", 
                            reply_markup=ReplyKeyboardMarkup(
                                keyboard=[[KeyboardButton(text="/switch on"), KeyboardButton(text="/switch off")]],
                                resize_keyboard=True))
                    elif message.split()[1].lower() == "on":
                        r = self.catreq.reqREST("ArduinoDevConn","/switch?state=on")
                        if not r.status or r.code_response != 200:
                            self.bot.sendMessage(chat_ID, f"Error: code {r.code_response} - {r.json_response}", reply_markup=ReplyKeyboardRemove())
                        else:
                            self.bot.sendMessage(chat_ID, "You started irrigation", reply_markup=ReplyKeyboardRemove())
                    elif message.split()[1].lower() == "off":
                        r = self.catreq.reqREST("ArduinoDevConn","/switch?state=off")
                        if not r.status or r.code_response != 200:
                            self.bot.sendMessage(chat_ID, f"Error: code {r.code_response} - {r.json_response}", reply_markup=ReplyKeyboardRemove())
                        else:
                            self.bot.sendMessage(chat_ID, "You stopped irrigation", reply_markup=ReplyKeyboardRemove())
                    else:
                        self.bot.sendMessage(chat_ID, "Wrong parameter. Please, use 'on' or 'off'.", reply_markup=ReplyKeyboardRemove())
                else:
                    #self.bot.sendMessage(chat_ID, "Wrong command. Please type /help to know the list of available commands", reply_markup=ReplyKeyboardRemove())
                    self.bot.sendMessage(chat_ID, msg, reply_markup=ReplyKeyboardRemove())

        
