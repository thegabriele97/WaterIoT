import telepot
import time
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton ,InlineQueryResultArticle, InputTextMessageContent
from REST_interface import *
import json
import requests

def start_irr():
    pass
def stop_irr():
    pass

class MyBot:
    

    def __init__(self,token):
    # Local token
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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                   [InlineKeyboardButton(text='Start Irrigation', callback_data='start')],
                   [InlineKeyboardButton(text='Stop Irrigation', callback_data='stop')]
               ])
        self.bot.sendMessage(self.chat_ID, 'Seleziona uno dei seguenti comandi', reply_markup=keyboard)
        #self.bot.sendMessage(chat_ID,text="You sent:\n"+message)# send a message on the chat
    
    def on_callback_query(self,msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        print('Callback Query:', query_id, from_id, query_data)
        if(query_data == "start"):
            self.bot.sendMessage(self.chat_ID,text="You started irrigation")# send a message on the chat
            start_irr()
        if(query_data == "stop"): 
            self.bot.sendMessage(self.chat_ID,text="You stopped irrigation")
            stop_irr()
        #if(query_data == "close"):

        #self.bot.answerCallbackQuery(query_id, text='Got it')
