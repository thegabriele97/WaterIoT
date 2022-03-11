import telepot
import time
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton ,InlineQueryResultArticle, InputTextMessageContent
import json
import requests

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
        MessageLoop(self.bot, {'chat': self.on_chat_message,
                  'callback_query': self.on_callback_query}).run_as_thread() # take as input the bot to wich listen the message and the handler of the message

    def on_chat_message(self,msg):
        content_type, chat_type ,self.chat_ID = telepot.glance(msg)
        message=msg['text']
        self.bot.sendMessage(self.chat_ID, message)
        if message == "/start":
            self.bot.sendMessage(self.chat_ID,"Hello!\n Here the commands:\n /switch <on/off> - Turn on or off the irrigator \n/getTemperatureAir - Retrive temperature of the air\n/getUmidityAir - Retrive umidity of the air\n/getUmiditySoil - Retrive umidity of the soil")
        if message == "/switch" :
            self.bot.sendMessage(self.chat_ID, message)

            keyboard = InlineKeyboardMarkup(inline_keyboard=[               # show buttons on telegram chat
                   [InlineKeyboardButton(text='Start Irrigation', callback_data='start')],
                   [InlineKeyboardButton(text='Stop Irrigation', callback_data='stop')]
               ])
            self.bot.sendMessage(self.chat_ID, 'Seleziona uno dei seguenti comandi', reply_markup=keyboard) # send message on telegram chat
           
        #self.bot.sendMessage(chat_ID,text="You sent:\n"+message)# send a message on the chat
    
    def on_callback_query(self,msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        #used to debug
        #self._logger.debug(f'Callback Query: {query_id}, {from_id}, {query_data}') 
        if(query_data == "start"):
            self.bot.sendMessage(self.chat_ID,text="You started irrigation")# send a message on the chat
            self.catreq.reqREST("ArduinoDevConn","ArduinoDevConn/switch?state='on'")
        if(query_data == "stop"): 
            self.bot.sendMessage(self.chat_ID,text="You stopped irrigation")
            self.catreq.reqREST("ArduinoDevConn","ArduinoDevConn/switch?state='off'")

        #if(query_data == "close"):

        #self.bot.answerCallbackQuery(query_id, text='Got it')
