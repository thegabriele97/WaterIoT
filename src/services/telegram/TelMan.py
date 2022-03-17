import telepot
import time
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton ,InlineQueryResultArticle, InputTextMessageContent
import json
import requests
from encryption import *

class MyBot:
   
    def __init__(self,token,logger,catreq):
    # Local token
        self.catreq = catreq
        self.logger = logger
        self.chat_ID = ""
        self.tokenBot=token
    #Catalog token
    #self.tokenBot=requests.get("http://catalogIP/telegram_token").json()["telegramToken"]
        self.bot=telepot.Bot(self.tokenBot)
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread() # take as input the bot to wich listen the message and the handler of the message

    def on_chat_message(self,msg):
        content_type, chat_type ,self.chat_ID = telepot.glance(msg)
        message=msg['text']
        with open('data.json', 'r') as f:
            data = json.load(f)
        id = self.chat_ID, self.bot.getUpdates()[0]["message"]["from"]["id"]
        if message.split()[0]=="/psw":
                if len(message.split()) == 1:
                    self.bot.sendMessage(self.chat_ID,"No password. Please, write a password after the command.")
                else :
                    if checkPassword(message.split()[1]):
                        addID(str(id[0])) # for some reason it return the id twice from getupdate
                        self.bot.sendMessage(self.chat_ID,"Correct password. The user is now subscribed and can access the functionality.")
                    else :
                        self.bot.sendMessage(self.chat_ID,"Wrond password")
        elif not checkID(str(id[0])) :
            self.bot.sendMessage(self.chat_ID,"Unsubscribed user. Please insert the password using /psw <password> command")
        else:
            
            if message == "/start":
                self.bot.sendMessage(self.chat_ID,"Hello!\n Here the commands:\n /psw <password> - Subscribe the user. \n /switch <on/off> - Turn on or off the irrigator \n/getairt - Retrive temperature of the air\n/getairu  - Retrive umidity of the air\n/getsoilu - Retrive umidity of the soil")
            elif message == "/getairt":
                self.bot.sendMessage(self.chat_ID,"You will get air temperature")
                #self.catreq.reqREST("RaspberryDevConn","RaspberryDevConn/airtemperature")
            elif message == "/getairu":
                self.bot.sendMessage(self.chat_ID,"You will get air umidity")
                #self.catreq.reqREST("RaspberryDevConn","RaspberryDevConn/airhumidity")
            elif message == "/getsoilu":
                self.bot.sendMessage(self.chat_ID,"You will get soil umidity")
                #self.catreq.reqREST("RaspberryDevConn","RaspberryDevConn/terrainhumidity")
            elif message.split()[0]=="/switch":
                if len(message.split()) == 1:
                    self.bot.sendMessage(self.chat_ID,"No parameter. Please, use '/switch on' or '/switch off'.")
                elif message.split()[1].lower() == "on":
                    self.bot.sendMessage(self.chat_ID,"You started irrigation")
                    self.catreq.reqREST("ArduinoDevConn","ArduinoDevConn/switch?state='on'")
                elif message.split()[1].lower() == "off":
                    self.bot.sendMessage(self.chat_ID,"You stopped irrigation")
                    self.catreq.reqREST("ArduinoDevConn","ArduinoDevConn/switch?state='off'")
                else:
                    self.bot.sendMessage(self.chat_ID,"Wrong parameter. Please, use 'on' or 'off'.")
            else:
                self.bot.sendMessage(self.chat_ID,"Wrong command. Please use one on the list")
        
        #self.bot.sendMessage(chat_ID,text="You sent:\n"+message)# send a message on the chat
    
   # def on_callback_query(self,msg):
    #    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        #used to debug
        #self._logger.debug(f'Callback Query: {query_id}, {from_id}, {query_data}') 
     #   if(query_data == "start"):
       #     self.bot.sendMessage(self.chat_ID,text="You started irrigation")# send a message on the chat
      #  if(query_data == "stop"): 
        #    self.bot.sendMessage(self.chat_ID,text="You stopped irrigation")

        #if(query_data == "close"):

        #self.bot.answerCallbackQuery(query_id, text='Got it')
