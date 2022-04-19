from datetime import datetime, timedelta
import json
import re
from xmlrpc.client import DateTime
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import logging
from common.Links import Links
from encryption import Encryption
from common.CatalogRequest import *
from common.WIOThread import WIOThread
from common.Utils import Utils
from SuperTelepotBot import SuperTelepotBot

class MyBot:
   
    def __init__(self, token, logger, catreq, settings):
        # Local token
        self.catreq : CatalogRequest = catreq
        self.logger : logging.Logger = logger
        self.tokenBot=token
        self._update_id = None
        self._settings = settings
        self._encr = Encryption()
        self._required_loc = False
        self._setlinks_create_waitname = False
        #Catalog token
        #self.tokenBot=requests.get("http://catalogIP/telegram_token").json()["telegramToken"]
        self.bot = SuperTelepotBot(self.tokenBot)
        self.bot.setCommands(self._settings.telegram.commands.toDict())

        r = self.catreq.reqREST("DeviceConfig", "/configs?path=/system/timezone/actual")
        if not r.status or r.code_response != 200:
            raise Exception(f"Error while requesting data from the DeviceConfig {r.code_response}: {r.json_response}")

        self._timezone = r.json_response["v"]
        self.catreq.subscribeMQTT("DeviceConfig", "/conf/system/timezone/actual")
        self.catreq.callbackOnTopic("DeviceConfig", "/conf/system/timezone/actual", self._timezone_cb)

        self._bot_th = WIOThread(target=self._handler_bot_th, name="Telegram Bot Handler")
        self._bot_th.run()

    def _timezone_cb(self, paho_mqtt, userdata, msg: mqtt.MQTTMessage):
        try:
            payl = json.loads(msg.payload.decode("utf-8"))
            self._timezone = payl["v"]
        except Exception as e:
            self.logger.critical(f"Exception occurred while handling a timezone MQTT update: {str(e)}")

    def _handler_bot_th(self):

        while not self._bot_th.is_stop_requested:
            
            response = None
            try:
                response = self.bot.getUpdates(offset=self._update_id); # getting all last messages from last poll
                # self.logger.debug(f"Telegram Bot: getUpdates response: {response}")
            except:
                self.logger.exception("Bad exception occurred! Stopping Telegram Bot Handler..")
                while not self._bot_th.is_stop_requested:
                    self._bot_th.wait(60)

                continue

            for resp in response:
                self._update_id = resp["update_id"] + 1

                try:
                    if "callback_query" in resp.keys():
                        self.on_query(resp["callback_query"])
                    else:
                        self.on_chat_message(resp["message"]) # for each new message, call on_chat_message
                except Exception as e:
                    self.logger.exception(f"Exception occurred while handling a Telegram message: {str(e)}")

            self._bot_th.wait(self._settings.telegram.poll_time)

    def on_query(self, query):
        
        name = query["data"][len("setlinks:"):]
        msgid = telepot.message_identifier(query["message"])

        self.logger.debug(f"Telegram Bot: on_query data: {query['data']}")
        self._setlinks_create_waitname = False
        self._setdatabase_create_waitdata = False

        # regex match for setlinks:{name}:back
        regx0 = re.compile(r"^setlinks:(?P<name>\w+):back$")
        # regex match for setlinks:{name}:remlink
        regx1 = re.compile(r"^setlinks:(?P<name>\w+):remlink$")
        # regex match for setlinks:{name}:remlink:{from}
        regx2 = re.compile(r"^setlinks:(?P<name>\w+):remlink:(?P<from>\w+)$")
        # regex match for setlinks:{name}:remlink:{from}:{to}
        regx3 = re.compile(r"^setlinks:(?P<name>\w+):remlink:(?P<from>\w+):(?P<to>\w+)$")
        # regex match for setlinks:{name}:addlink
        regx4 = re.compile(r"^setlinks:(?P<name>\w+):addlink$")
        # regex match for setlinks:{name}:addlink:{from}
        regx5 = re.compile(r"^setlinks:(?P<name>\w+):addlink:(?P<from>\w+)$")
        # regex match for setlinks:{name}:addlink:{from}:{to}
        regx6 = re.compile(r"^setlinks:(?P<name>\w+):addlink:(?P<from>\w+):(?P<to>\w+)$")
        # regex match for setlinks:{name}:delete
        regx7 = re.compile(r"^setlinks:(?P<name>\w+):delete$")
        # regex match for setlinks_create
        regx8 = re.compile(r"^setlinks_create$")
        # regex match for setdatabase:{name}
        regx9 = re.compile(r"^setdatabase:(?P<name>\w+)$")
        # regex match for setdatabase:{name}:back
        regx10 = re.compile(r"^setdatabase:(?P<name>\w+):back$")
        # regex match for setdatabase:{name}:apply
        regx11 = re.compile(r"^setdatabase:(?P<name>\w+):apply$")
        # regex match for setdabase_create
        regx12 = re.compile(r"^setdatabase_create$")
        # regex match for setdatabase:{name}:delete
        regx13 = re.compile(r"^setdatabase:(?P<name>\w+):delete$")
        # regex match for setdevice:{devid}
        regx14 = re.compile(r"^setdevice:(?P<devid>\w+)$")
        # regex match for setdevice:{devid}:refresh
        regx15 = re.compile(r"^setdevice:(?P<devid>\w+):refresh$")
        # regex match for status:refresh:{pagenum}
        regx16 = re.compile(r"^status:refresh:(?P<pagenum>\d+)$")
        # regex match for status:next:{pagenum}
        regx17 = re.compile(r"^status:next:(?P<pagenum>\d+)$")
        # regex match for status:prev:{pagenum}
        regx18 = re.compile(r"^status:prev:(?P<pagenum>[+-]?\d+)$")

        if regx1.match(query["data"]):

            name = regx1.match(query["data"]).group("name")
            r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list")
            if not r.status or r.code_response != 200:
                self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                return

            links = Links(r.json_response["v"])

            msg = ""
            msg += "<b>🔗 Link</b>:\n"

            l = [l for l in links.data if l.name == name][0]
            msg += f"   <i>{l.name}</i>\n"
            msg += f"      <b><pre>FROM: {l.raspberrys}</pre></b>\n"

            kboard_inner = self._gen_kboard("🔗 ", l.raspberrys, lambda x: f"setlinks:{name}:remlink:{x}", InlineKeyboardButton)
            kboard_inner.append([InlineKeyboardButton(text="⬅️Back", callback_data=f"setlinks:{name}")]) 
            kboard = InlineKeyboardMarkup(inline_keyboard=kboard_inner)
            self.bot.editMessageText(msgid, msg, parse_mode="HTML", reply_markup=kboard)

        elif regx2.match(query["data"]):

            name = regx2.match(query["data"]).group("name")
            from_ = regx2.match(query["data"]).group("from")
            r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list")
            if not r.status or r.code_response != 200:
                self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                return

            links = Links(r.json_response["v"])

            msg = ""
            msg += "<b>🔗 Link</b>:\n"

            l = [l for l in links.data if l.name == name][0]
            msg += f"   <i>{l.name}</i>\n"
            msg += f"      <b><pre>  TO: {l.arduinos}</pre></b>\n"

            kboard_inner = self._gen_kboard(f"🔗 {from_} ➡️ ", l.arduinos, lambda x: f"setlinks:{name}:remlink:{from_}:{x}", InlineKeyboardButton)
            kboard_inner.append([InlineKeyboardButton(text="⬅️ Back", callback_data=f"setlinks:{name}")])
            kboard = InlineKeyboardMarkup(inline_keyboard=kboard_inner)
            self.bot.editMessageText(msgid, msg, parse_mode="HTML", reply_markup=kboard)

        elif regx3.match(query["data"]):

            name = regx3.match(query["data"]).group("name")
            from_ = regx3.match(query["data"]).group("from")
            to_ = regx3.match(query["data"]).group("to")

            r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list")
            if not r.status or r.code_response != 200:
                self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                return

            links = Links(r.json_response["v"])

            try:
                links.removeLink(name, from_, to_)
                r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list", datarequest={"v": links.toDict()}, reqt = RequestType.PUT)
                if not r.status or r.code_response != 200:
                    self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                    self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                    return

            except Exception as e:
                self.bot.answerCallbackQuery(query["id"], f"Error while removing link: {str(e)}")
                self.logger.error(f"Error while removing link: {str(e)}")
                return

            self._setlinks_msglist(msgid=msgid)
            self.bot.answerCallbackQuery(query["id"], f"Link removed from {name}: {from_} ➡️ {to_}")

        elif regx4.match(query["data"]):

            name = regx4.match(query["data"]).group("name")
            ids = self.catreq.reqDeviceIdsList("RaspberryDevConn")

            kboard_inner = self._gen_kboard("🔗 ", ids, lambda x: f"setlinks:{name}:addlink:{x}", InlineKeyboardButton)
            kboard_inner.append([InlineKeyboardButton(text="⬅️ Back", callback_data=f"setlinks:{name}")])
            kboard = InlineKeyboardMarkup(inline_keyboard=kboard_inner)
            self.bot.editMessageText(msgid, query["message"]["text"], parse_mode="HTML", reply_markup=kboard)
        
        elif regx5.match(query["data"]):

            name = regx5.match(query["data"]).group("name")
            from_ = regx5.match(query["data"]).group("from")
            ids = self.catreq.reqDeviceIdsList("ArduinoDevConn")
            
            kboard_inner = self._gen_kboard(f"🔗 {from_} ➡️ ", ids, lambda x: f"setlinks:{name}:addlink:{from_}:{x}", InlineKeyboardButton)
            kboard_inner.append([InlineKeyboardButton(text="⬅️ Back", callback_data=f"setlinks:{name}")])
            kboard = InlineKeyboardMarkup(inline_keyboard=kboard_inner)
            self.bot.editMessageText(msgid, query["message"]["text"], parse_mode="HTML", reply_markup=kboard)

        elif regx6.match(query["data"]):

            name = regx6.match(query["data"]).group("name")
            from_ = regx6.match(query["data"]).group("from")
            to_ = regx6.match(query["data"]).group("to")

            r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list")
            if not r.status or r.code_response != 200:
                self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                return
            
            try:
                links = Links(r.json_response["v"])
                links.addLink(name, from_, to_)
                r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list", datarequest={"v": links.toDict()}, reqt = RequestType.PUT)
                if not r.status or r.code_response != 200:
                    self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                    self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                    return
            except Exception as e:
                self.bot.answerCallbackQuery(query["id"], f"Error while adding link: {str(e)}")
                self.logger.error(f"Error while adding link: {str(e)}")
                return

            self._setlinks_msglist(msgid=msgid)
            self.bot.answerCallbackQuery(query["id"], f"Link added from {name}: {from_} ➡️ {to_}")

        elif regx7.match(query["data"]):

            name = regx7.match(query["data"]).group("name")

            r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list")
            if not r.status or r.code_response != 200:
                self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                return

            try:
                links = Links(r.json_response["v"])
                links.removeLink(name)
                r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list", datarequest={"v": links.toDict()}, reqt = RequestType.PUT)
                if not r.status or r.code_response != 200:
                    self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                    self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                    return
            except Exception as e:
                self.bot.answerCallbackQuery(query["id"], f"Error while removing link: {str(e)}")
                self.logger.error(f"Error while removing link: {str(e)}")
                return

            self._setlinks_msglist(msgid=msgid)
            self.bot.answerCallbackQuery(query["id"], f"Link Group {name} removed")

        elif regx0.match(query["data"]):

            self._setlinks_msglist(msgid=msgid)

        # regex match for setlinks:{name}
        elif query["data"].startswith("setlinks:"):

            r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list")
            if not r.status or r.code_response != 200:
                self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                return

            links = Links(r.json_response["v"])

            msg = ""
            msg += "<b>🔗 Link</b>:\n"

            for l in [l for l in links.data if l.name == name]:
                msg += f"   <i>{l.name}</i>\n"
                msg += f"      <pre>FROM: {l.raspberrys}</pre>\n"
                msg += f"      <pre>  TO: {l.arduinos}</pre>\n"
            kboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="❌ Delete", callback_data=f"setlinks:{name}:delete"),
                    InlineKeyboardButton(text="➕ Add Link", callback_data=f"setlinks:{name}:addlink"),
                    InlineKeyboardButton(text="❌ Remove Link", callback_data=f"setlinks:{name}:remlink")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Back", callback_data=f"setlinks:{name}:back")
                ]
            ])
            self.bot.editMessageText(msgid, msg, reply_markup=kboard, parse_mode="HTML")
            # self.logger.debug(f"Telegram Bot: setlinks: {name}")
            # self.bot.answerCallbackQuery(query["id"], text="Подождите, идет поиск привязки...")
        elif regx8.match(query["data"]):
            
            kboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="⬅️ Back", callback_data=f"setlinks:nd:back")
                ]
            ])

            self.bot.editMessageText(msgid, "Please, send the name of the new link group...", parse_mode="HTML", reply_markup=kboard)
            self._setlinks_create_waitname = True
            self._setlinks_create_msgid = msgid
        elif regx9.match(query["data"]):
            name = regx9.match(query["data"]).group("name")

            r = self.catreq.reqREST("WateringDatabase", f"/getByName?name={name}")
            if not r.status or r.code_response != 200:
                self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                return

            item = r.json_response["item"]
            msg = ""
            msg += "<b>💾 Database</b>:\n"
            msg += f"   <i>{item['name']}</i>\n"
            msg += f"         <pre>Air humidity</pre>\n"                   
            msg += f"         <pre>            max: {item['thresholds']['airhum']['max']:.2f}%</pre>\n"
            msg += f"         <pre>            min: {item['thresholds']['airhum']['min']:.2f}%</pre>\n"
            msg += f"         <pre>Air temperature:</pre>\n"
            msg += f"         <pre>            max: {item['thresholds']['temp']['max']:.2f}°C</pre>\n"
            msg += f"         <pre>            min: {item['thresholds']['temp']['min']:.2f}°C</pre>\n"
            msg += f"         <pre>Soil humidity  :</pre>\n"
            msg += f"         <pre>            max: {item['thresholds']['soilhum']['max']:.2f}%</pre>\n"
            msg += f"         <pre>            min: {item['thresholds']['soilhum']['min']:.2f}%</pre>\n"

            kboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="☑️ Apply", callback_data=f"setdatabase:{name}:apply"),
                    InlineKeyboardButton(text="❌ Delete", callback_data=f"setdatabase:{name}:delete")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Back", callback_data=f"setdatabase:{name}:back")
                ]
            ])

            self.bot.editMessageText(msgid, msg, parse_mode="HTML", reply_markup=kboard)

        elif regx10.match(query["data"]):

            self._setdatabase_msglist(msgid=msgid)

        elif regx11.match(query["data"]):

            name = regx11.match(query["data"]).group("name")

            r = self.catreq.reqREST("WateringDatabase", f"/getByName?name={name}")
            if not r.status or r.code_response != 200:
                self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                return
            
            item = r.json_response["item"]
            self.logger.debug(f"item = {item}")
            self.logger.debug(f"item['thresholds'] = {item['thresholds']}")
            r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/thresholds", reqt=RequestType.PUT, datarequest=item["thresholds"])
            if not r.status or r.code_response != 200:
                self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                return

            self._setdatabase_msglist(msgid=msgid)
            self.bot.answerCallbackQuery(query["id"], text="Thresholds updated")
        elif regx12.match(query["data"]):

            kboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="⬅️ Back", callback_data=f"setdatabase:nd:back")
                ]
            ])

            msg = "Please, send the new database record\nFormat must be:\n<pre>"
            msg += "name\n"
            msg += "airhum_max\n"
            msg += "airhum_min\n"
            msg += "temp_max\n"
            msg += "temp_min\n"
            msg += "soilhum_max\n"
            msg += "soilhum_min\n"
            msg += "</pre>"
            self.bot.editMessageText(msgid, msg, parse_mode="HTML", reply_markup=kboard)
            self._setdatabase_create_waitdata = True
            self._setlinks_create_msgid = msgid
        elif regx13.match(query["data"]):

            name = regx13.match(query["data"]).group("name")

            r = self.catreq.reqREST("WateringDatabase", f"/getByName?name={name}", reqt=RequestType.DELETE)
            if not r.status or r.code_response != 200:
                self.bot.answerCallbackQuery(query["id"], f"Error from the DeviceConfig {r.code_response}")
                self.logger.error(f"Error from the DeviceConfig {r.code_response}: {r.json_response}")
                return

            self._setdatabase_msglist(msgid=msgid)
            self.bot.answerCallbackQuery(query["id"], text=f"Database Item <b>{name}</b> deleted")

        elif regx14.match(query["data"]):

            devid = regx14.match(query["data"]).group("devid")
            self._setreadings_msglist(msgid=msgid, devid=devid)

        elif regx15.match(query["data"]):

            devid = regx15.match(query["data"]).group("devid")
            self._setreadings_msglist(msgid=msgid, devid=devid)

        elif regx16.match(query["data"]) or regx17.match(query["data"]) or regx18.match(query["data"]):

            matcher = regx16 if regx16.match(query["data"]) else regx17 if regx17.match(query["data"]) else regx18
            pagenum = matcher.match(query["data"]).group("pagenum")
            self._setstatus_msglist(msgid=msgid, pagenum=pagenum)


    def on_chat_message(self,msg):

        content_type, chat_type, chat_ID = telepot.glance(msg)

        if "text" in msg:
            self.logger.info(f"New text from {chat_ID}: {msg['text']}")

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
                    if not(len(message.split()) == 4 or len(message.split()) == 3):
                        self.bot.sendMessage(chat_ID, "No parameter. Please select one sensor (<temp>,<airhum>,<soilhum>) as first parameter and a value (expressed in millisecond) as second", reply_markup=ReplyKeyboardRemove())
                    elif message.split()[1] not in ["temp", "airhum","soilhum"]:
                        self.bot.sendMessage(chat_ID, "Wrong parameter. Please select one sensor(<temp>,<airhum>,<soilhum>) as first parameter and a value (expressed in millisecond) as second", reply_markup=ReplyKeyboardRemove())
                    else:
                        try: # verify if the value is an integer
                            status,json_response,code_response = self.catreq.reqREST("DeviceConfig",f"/configs?path=/sensors/{message.split()[1]}/sampleperiod",RequestType.PUT,{"v": int(message.split()[2])})
                            if code_response == 200 :
                                self.bot.sendMessage(chat_ID, "Sample time set properly.", reply_markup=ReplyKeyboardRemove())
                            else:
                                self.bot.sendMessage(chat_ID, "An error occour. ", reply_markup=ReplyKeyboardRemove())
                        except ValueError:
                            if message.split()[2] not in ["min","max"]:
                                self.bot.sendMessage(chat_ID,"Please insert an integer value or min/max to set the watering range", reply_markup=ReplyKeyboardRemove())
                            else:
                                try: #verify number insertion
                                    status,json_response,code_response = self.catreq.reqREST("DeviceConfig",f"/configs?path=/watering/thresholds/{message.split()[1]}/{message.split()[2]}",RequestType.PUT,{"v": float(message.split()[3])})
                                    if code_response == 200 :
                                        self.bot.sendMessage(chat_ID, "Bound set properly.", reply_markup=ReplyKeyboardRemove())
                                    else:
                                        self.bot.sendMessage(chat_ID, "An error occour. ", reply_markup=ReplyKeyboardRemove())
                                except ValueError:
                                    self.bot.sendMessage(chat_ID,"Please insert an numerical", reply_markup=ReplyKeyboardRemove())
                elif message.split()[0] == "/pos" :
                    if len(message.split()) != 3:
                        self.bot.sendMessage(chat_ID, "Please, send your location...", reply_markup=ReplyKeyboardRemove())
                        self._required_loc = True
                    else:
                        try: # verify if the value is a float
                            r = self._set_location_dc(message.split()[1],message.split()[2])
                            self.bot.sendMessage(chat_ID, self._set_pos_msg(res=r), reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                        except ValueError:
                            self.bot.sendMessage(chat_ID,"Please insert numerical values", reply_markup=ReplyKeyboardRemove())
                elif message == "/start" or message == "/help":
                    msg = "Hello!\n"
                    msg += "Here are the commands\n"
                    msg += "/psw &#60;password&#62; - Subscribe the user:\n"
                    msg += "airhum_max\n"
                    msg += "airhum_min\n"
                    msg += "temp_max\n"
                    msg += "temp_min\n"
                    msg += "soilhum_max\n"
                    msg += "soilhum_min\n"
                
                    self.bot.sendMessage(chat_ID, msg, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
                elif message.split()[0] == "/getairt" or message.split()[0] == "/getairu" or message.split()[0] == "/getsoilu":

                    devid = None
                    if len(message.split()) > 1:
                        try:
                            devid = int(message.split()[1])
                        except ValueError:
                            self.bot.sendMessage(chat_ID,"Please insert an integer value", reply_markup=ReplyKeyboardRemove())
                            return

                    ids = self.catreq.reqDeviceIdsList("RaspberryDevConn")

                    if devid is None and len(ids) > 0:
                        if len(ids) == 1:
                            devid = ids[0]
                        else:

                            kboard = [[]]
                            row = 0
                            for i in range(0, len(ids)):

                                kboard[row].append(KeyboardButton(text=f"{message.split()[0]} {ids[i]}"))
                                if (i + 1) % 3 == 0:
                                    kboard.append([])
                                    row += 1

                            self.bot.sendMessage(chat_id=chat_ID, text="No device id selected. Please use the right one", reply_markup=ReplyKeyboardMarkup(keyboard=kboard, resize_keyboard=True))
                            return

                    r = self.bot.sendMessage(chat_ID,"You will get the result ASAP...", reply_markup=ReplyKeyboardRemove())

                    epoint = "/airtemperature" if message.split()[0] == "/getairt" else "/airhumidity" if message.split()[0] == "/getairu" else "/terrainhumidity"
                    done, resp, code = self.catreq.reqREST("RaspberryDevConn", epoint, devid=devid)
                    if not done or code != 200:
                        self.bot.deleteMessage(telepot.message_identifier(r))
                        self.bot.sendMessage(chat_ID, f"Error while requesting data {code}: {resp}", reply_markup=ReplyKeyboardRemove())
                        return

                    (a, b, c, devid) = (resp if epoint == "/airhumidity" else None, resp if epoint == "/airtemperature" else None, resp if epoint == "/terrainhumidity" else None, devid)
                    msg = self._setreadings_prepmsg(a, b, c, devid, exclusive=True)
                    self.bot.deleteMessage(telepot.message_identifier(r))
                    self.bot.sendMessage(chat_ID, msg, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                elif message.split()[0]=="/switch":
                    if len(message.split()) == 1:
                        self.bot.sendMessage(chat_id=chat_ID,
                            text="No parameter. Please, use '/switch on' or '/switch off'.", 
                            reply_markup=ReplyKeyboardMarkup(
                                keyboard=[[KeyboardButton(text="/switch on"), KeyboardButton(text="/switch off")]],
                                resize_keyboard=True))
                    elif message.split()[1].lower() == "on" or message.split()[1].lower() == "off":

                        ids = self.catreq.reqDeviceIdsList("ArduinoDevConn")
                        self.logger.debug("ids: %s", ids)
                        devids = [None]

                        if len(ids) > 1:
                            # there are more then one device connected
                            if len(message.split()) < 3:
                                kboard = [[KeyboardButton(text=f"/switch {message.split()[1].lower()} all")], []]
                                row = 1
                                for i in range(0, len(ids)):

                                    kboard[row].append(KeyboardButton(text=f"/switch {message.split()[1].lower()} {ids[i]}"))
                                    if (i + 1) % 3 == 0:
                                        kboard.append([])
                                        row += 1

                                self.bot.sendMessage(chat_ID, "No device id selected. Please use the right one", reply_markup=ReplyKeyboardMarkup(keyboard=kboard, resize_keyboard=True))
                                return
                            else:
                                try:
                                    devids = [int(message.split()[2])]
                                except ValueError:
                                    devids = ids

                        msg = "Result: \n<pre>"
                        for devid in devids:
                            msg += f"   #{devid}: "
                            r = self.catreq.reqREST("ArduinoDevConn", f"/switch?state={message.split()[1].lower()}", devid=devid)
                            if not r.status or r.code_response != 200:
                                msg += f"OFF"
                            else:
                                msg += f" ON"

                            msg += "\n"

                        msg += "</pre>"
                        self.bot.sendMessage(chat_ID, msg, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

                    else:
                        self.bot.sendMessage(chat_ID, "Wrong parameter. Please, use 'on' or 'off'.", reply_markup=ReplyKeyboardRemove())               
                elif message.split()[0]=="/status":
                    
                    self._setstatus_msglist(chat_ID=chat_ID)
                    
                elif message.split()[0] == "/links":

                    self._setlinks_msglist(chat_ID=chat_ID)

                elif message.split()[0] == "/database":

                    self._setdatabase_msglist(chat_ID=chat_ID)

                elif message.split()[0] == "/readings":

                    self._setreadings_msglist(chat_ID=chat_ID)

                else:

                    if self._setlinks_create_waitname:
                        self._setlinks_create_waitname = False
                        
                        r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list")
                        if not r.status or r.code_response != 200:
                            self.bot.sendMessage(chat_ID, f"Error while requesting data from the DeviceConfig {r.code}: {r.response}", reply_markup=ReplyKeyboardRemove())
                            return

                        links = Links(r.json_response["v"])
                        links.createLink("".join(message.split())) # remove all spaces

                        # PUT request on DeviceConfig
                        r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list", reqt=RequestType.PUT, datarequest={"v": links.toDict()})
                        if not r.status or r.code_response != 200:
                            self.bot.sendMessage(chat_ID, f"Error while updating data on the DeviceConfig {r.code_response}: {r.json_response}", reply_markup=ReplyKeyboardRemove())
                            return

                        # this messageid (the one with the name)
                        thismsgid = telepot.message_identifier(msg)

                        # deleting this message
                        self.bot.deleteMessage(thismsgid)
                        # updating the original message with the list of links
                        self._setlinks_msglist(msgid=self._setlinks_create_msgid)

                        return
                    elif self._setdatabase_create_waitdata:
                        self._setdatabase_create_waitdata = False
                        
                        r = self.catreq.reqREST("WateringDatabase", "/", reqt=RequestType.POST, datarequest={
                            "name": "".join(message.split("\n")[0].split()),
                            "thresholds": {
                                "temp": {
                                    "max": float(message.split()[3]),
                                    "min": float(message.split()[4])
                                },
                                "airhum": {
                                    "max": float(message.split()[1]),
                                    "min": float(message.split()[2])
                                },
                                "soilhum": {
                                    "max": float(message.split()[5]),
                                    "min": float(message.split()[6])
                                }
                            }
                        })

                        if not r.status or r.code_response != 201:
                            self.bot.sendMessage(chat_ID, f"Error while updating data on the WateringDatabase {r.code_response}: {r.json_response}", reply_markup=ReplyKeyboardRemove())
                            return
                        
                        # this messageid (the one with the name)
                        thismsgid = telepot.message_identifier(msg)

                        # deleting this message
                        self.bot.deleteMessage(thismsgid)
                        # updating the original message with the list of links
                        self._setdatabase_msglist(msgid=self._setlinks_create_msgid)

                        return

                    self.bot.sendMessage(chat_ID, "Wrong command. Please type /help to know the list of available commands", reply_markup=ReplyKeyboardRemove())
                    # self.bot.sendMessage(chat_ID, msg, reply_markup=ReplyKeyboardRemove())

                self._setlinks_create_waitname = False
                self._setdatabase_create_waitdata = False

        elif "location" in msg:

            if self._required_loc:

                r = self._set_location_dc(msg["location"]["latitude"], msg["location"]["longitude"])
                self.bot.sendMessage(chat_ID, self._set_pos_msg(res=r), reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                self._required_loc = False
        
            else:
                self.bot.sendMessage(chat_ID, "Wrong command. Please type /help to know the list of available commands", reply_markup=ReplyKeyboardRemove())

    def _gen_kboard(self, msg, items, callback_data_fnc, generator, n_x_row = 3):
        kboard = [[]]
        row = 0
        for i in range(0, len(items)):

            kboard[row].append(generator(text=f"{msg if msg is not None else ''}{items[i]}", callback_data=f"{callback_data_fnc(items[i])}"))
            if (i + 1) % n_x_row == 0:
                kboard.append([])
                row += 1

        return kboard

    def _setlinks_msglist(self, chat_ID = None, msgid = None):

        r = self.catreq.reqREST("DeviceConfig", "/configs?path=/watering/links/list")
        if not r.status or r.code_response != 200:
            self.bot.sendMessage(chat_ID, f"Error while requesting data from the DeviceConfig {r.code_response}: {r.json_response}", reply_markup=ReplyKeyboardRemove())
            return

        links = Links(r.json_response["v"])

        msg = ""
        msg += "<b>🔗 Links</b>:\n"

        for l in links.data:
            msg += f"   <i>{l.name}</i>\n"
            msg += f"      <pre>FROM: {l.raspberrys}</pre>\n"
            msg += f"      <pre>  TO: {l.arduinos}</pre>\n"

        kboard_inner = self._gen_kboard("🔗 ", [l.name for l in links.data], lambda x: f"setlinks:{x}", InlineKeyboardButton, 3)
        kboard_inner.append([InlineKeyboardButton(text="➕ Create", callback_data="setlinks_create")])
        kboard = InlineKeyboardMarkup(inline_keyboard=kboard_inner)

        if chat_ID is not None:
            self.bot.sendMessage(chat_ID, msg, reply_markup=kboard, parse_mode="HTML")
        elif msgid is not None:
            self.bot.editMessageText(msgid, msg, parse_mode="HTML", reply_markup=kboard)

    def _setdatabase_msglist(self, chat_ID = None, msgid = None):

        r = self.catreq.reqREST("WateringDatabase", "/")
        if not r.status or r.code_response != 200:
            self.bot.sendMessage(chat_ID, f"Error while requesting data from the WateringDatabase {r.code_response}: {r.code_response}", reply_markup=ReplyKeyboardRemove())
            return

        items = list(r.json_response["items"])

        msg = ""
        msg += "<b>💾 Database</b>:\n"

        for i in range(0, len(items)):
            msg += f"   <i>{items[i]['name']}</i>\n"
            msg += f"         <pre>Air humidity   :</pre>\n"                   
            msg += f"         <pre>            max: {items[i]['thresholds']['airhum']['max']:.2f}%</pre>\n"
            msg += f"         <pre>            min: {items[i]['thresholds']['airhum']['min']:.2f}%</pre>\n"
            msg += f"         <pre>Air temperature:</pre>\n"
            msg += f"         <pre>            max: {items[i]['thresholds']['temp']['max']:.2f}°C</pre>\n"
            msg += f"         <pre>            min: {items[i]['thresholds']['temp']['min']:.2f}°C</pre>\n"
            msg += f"         <pre>Soil humidity  :</pre>\n"
            msg += f"         <pre>            max: {items[i]['thresholds']['soilhum']['max']:.2f}%</pre>\n"
            msg += f"         <pre>            min: {items[i]['thresholds']['soilhum']['min']:.2f}%</pre>\n"

        kboard_inner = self._gen_kboard("💾 ", [i["name"] for i in items], lambda x: f"setdatabase:{x}", InlineKeyboardButton)
        kboard_inner.append([InlineKeyboardButton(text="➕ Create", callback_data="setdatabase_create")])
        kboard = InlineKeyboardMarkup(inline_keyboard=kboard_inner)

        if chat_ID is not None:
            self.bot.sendMessage(chat_ID, msg, reply_markup=kboard, parse_mode="HTML")
        elif msgid is not None:
            self.bot.editMessageText(msgid, msg, parse_mode="HTML", reply_markup=kboard)

    def _setreadings_msglist(self, chat_ID = None, msgid = None, devid = None):

        ids = self.catreq.reqDeviceIdsList("RaspberryDevConn")
        devid = None if len(ids) == 0 else ids[0] if devid is None else int(devid)

        kboard_inner = self._gen_kboard("🖥️ Device ", ids, lambda x: f"setdevice:{x}", InlineKeyboardButton, 2)
        kboard_inner.append([InlineKeyboardButton(text="🔄 Refresh", callback_data=f"setdevice:{devid}:refresh")])
        kboard = InlineKeyboardMarkup(inline_keyboard=kboard_inner)

        a = b = c = None

        if msgid is not None:
            self.bot.editMessageText(msgid, self._setreadings_prepmsg(devid=devid), reply_markup=kboard, parse_mode="HTML")

        r0 = self.catreq.reqREST("RaspberryDevConn", "/airhumidity", devid=devid)
        time.sleep(1)
        if r0.status and r0.code_response == 200:
            a = r0.json_response

        if msgid is not None:
            self.bot.editMessageText(msgid, self._setreadings_prepmsg(a, b, c, devid=devid), reply_markup=kboard, parse_mode="HTML")

        r1 = self.catreq.reqREST("RaspberryDevConn", "/airtemperature", devid=devid)
        time.sleep(0.5)
        if r0.status and r0.code_response == 200:
            b = r1.json_response

        if msgid is not None:
            self.bot.editMessageText(msgid, self._setreadings_prepmsg(a, b, c, devid=devid), reply_markup=kboard, parse_mode="HTML")

        r2 = self.catreq.reqREST("RaspberryDevConn", "/terrainhumidity", devid=devid)
        time.sleep(0.4)
        if r0.status and r0.code_response == 200:
            c = r2.json_response
        
        msg = self._setreadings_prepmsg(a, b, c, devid=devid)
        if a is None or b is None or c is None:
            msg += "\n\n<b>🔄 An error occurred while loading some data. Please, retry!</b>"

        if chat_ID is not None:
            self.bot.sendMessage(chat_ID, msg, reply_markup=kboard, parse_mode="HTML")
        elif msgid is not None:
            self.bot.editMessageText(msgid, msg, reply_markup=kboard, parse_mode="HTML")
    

    def _setreadings_prepmsg(self, airhum = None, airtemp = None, soilhum = None, devid = "ND", exclusive = False):

        dt0 = Utils.get_user_dt_woffset(airhum["t"], self._timezone) if airhum is not None else "..."
        dt1 = Utils.get_user_dt_woffset(airtemp["t"], self._timezone) if airtemp is not None else "..."
        dt2 = Utils.get_user_dt_woffset(soilhum["t"], self._timezone) if soilhum is not None else "..."

        msg = ""
        msg += f"<b>📊 Readings <i>(dev #{devid})</i></b>:\n"

        if not (airhum is None and exclusive):
            msg += f"   <i>Air humidity   :</i>\n"
            msg += f"<pre>"
            msg += f'      🖥️ sensor: {airhum["n"] if airhum is not None else "..."}\n'
            msg += f'      🕟 time  : {dt0}\n'
            msg += f'      📟 value : {airhum["v"] if airhum is not None else ".."}{airhum["u"] if airhum is not None else "."}\n'
            msg += f"</pre>"

        if not (airtemp is None and exclusive):
            msg += f"   <i>Air temperature: </i>\n"
            msg += f"<pre>"
            msg += f'      🖥️ sensor: {airtemp["n"] if airtemp is not None else "..."}\n'
            msg += f'      🕟 time  : {dt1}\n'
            msg += f'      📟 value : {airtemp["v"] if airtemp is not None else ".."}{airtemp["u"] if airtemp is not None else "."}\n'
            msg += f"</pre>"

        if not (soilhum is None and exclusive):
            msg += f"   <i>Soil humidity  : </i>\n"
            msg += f"<pre>"
            msg += f'      🖥️ sensor: {soilhum["n"] if soilhum is not None else "..."}\n'
            msg += f'      🕟 time  : {dt2}\n'
            msg += f'      📟 value : {soilhum["v"] if soilhum is not None else ".."}{soilhum["u"] if soilhum is not None else "."}\n'
            msg += f"</pre>"

        return msg    

    def _setstatus_msglist(self, chat_ID = None, msgid = None, pagenum: int = 0):

        pagenum_max = 4
        pagenum = (pagenum_max-1 if int(pagenum) < 0 else int(pagenum)) % pagenum_max

        kboard_inner = [
            [
                InlineKeyboardButton(text="⬅️️ Prev", callback_data=f"status:prev:{pagenum-1}"),
                InlineKeyboardButton(text="➡️️ Next", callback_data=f"status:next:{pagenum+1}")
            ],
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data=f"status:refresh:{pagenum}"),
            ]
        ]

        kboard = InlineKeyboardMarkup(inline_keyboard=kboard_inner)
        msg = f"<b>📊 Status (page #{(pagenum+1)}/{pagenum_max})</b>:\n\n"

        if msgid is not None:
            self.bot.editMessageText(msgid, f"{msg}Loading...", parse_mode="HTML")
            time.sleep(0.5)

        if pagenum == 0:
            ss = self.catreq.reqAllServices()

            if len(ss["online"]) > 0:
                msg += "<b>✅ online</b>:\n"
                for s in sorted(ss["online"], key=lambda x: x["name"]):
                    id_str = f" ({s['deviceid']}) " if s["deviceid"] is not None else ""
                    msg += f"   🛸 <pre>{s['name']}{id_str}</pre>\n"

            if len(ss["offline"]) > 0:
                msg += "\n<b>❌ offline</b>:\n"
                for s in sorted(ss["offline"], key=lambda x: x["name"]):
                    id_str = f" ({s['deviceid']}) " if s["deviceid"] is not None else ""
                    msg += f"   🚑 <pre>{s['name']}{id_str}</pre>\n"

        elif pagenum == 1:
            done, resp, code = self.catreq.reqREST("WateringControl", "/status")
            if not done or code != 200:
                if chat_ID is not None:
                    self.bot.sendMessage(chat_ID, f"Error while requesting data from the WateringControl {code}: {resp}", reply_markup=kboard)
                elif msgid is not None:
                    self.bot.editMessageText(msgid, f"Error while requesting data from the WateringControl {code}: {resp}", reply_markup=kboard)
                return

            dt_lastnorm = Utils.get_user_dt_woffset(resp['telegram']['last_sent_msg_timestamp'], self._timezone) if resp['telegram']['last_sent_msg_timestamp'] != -1 else "never"
            dt_nextnorm = Utils.get_user_dt_woffset(resp['telegram']['last_sent_msg_timestamp'] + resp["telegram"]["min_time_between_messages"], self._timezone) if resp['telegram']['last_sent_msg_timestamp'] != -1 else "ASAP"
            dt_lastcrit = Utils.get_user_dt_woffset(resp['telegram']['last_sent_msgcrit_timestamp'], self._timezone) if resp['telegram']['last_sent_msgcrit_timestamp'] != -1 else "never"
            dt_nextcrit = Utils.get_user_dt_woffset(resp['telegram']['last_sent_msgcrit_timestamp'] + resp["telegram"]["min_time_between_messages_crit"], self._timezone) if resp['telegram']['last_sent_msgcrit_timestamp'] != -1 else "ASAP"

            ah = resp["asdrubale"]["averages"]["air_humidity"]
            at = resp["asdrubale"]["averages"]["air_temperature"]
            sh = resp["asdrubale"]["averages"]["soil_humidity"]
            ah_max = resp["asdrubale"]["thresholds"]["air_humidity"]["max"]
            ah_min = resp["asdrubale"]["thresholds"]["air_humidity"]["min"]
            at_max = resp["asdrubale"]["thresholds"]["air_temperature"]["max"]
            at_min = resp["asdrubale"]["thresholds"]["air_temperature"]["min"]
            sh_max = resp["asdrubale"]["thresholds"]["soil_humidity"]["max"]
            sh_min = resp["asdrubale"]["thresholds"]["soil_humidity"]["min"]

            msg += "<b>💧 Watering Control</b>:\n"
            if not bool(resp["enabled"]):
                msg += f"   ❌ <b>Watering is disabled</b>\n"
            else:
                msg += f"   <b>🔔 Notification status:</b>\n"
                msg += f"      <pre>Last normal  : {dt_lastnorm}</pre>\n"
                msg += f"      <pre>Next normal  : {dt_nextnorm}</pre>\n"
                msg += f"      <pre>Last Critical: {dt_lastcrit}</pre>\n"
                msg += f"      <pre>Next Critical: {dt_nextcrit}</pre>\n"
                msg += "\n"
                msg += f"   <b>🧭 Location</b>:\n"
                msg += f"      <pre>Latitude : {resp['location']['lat']}</pre>\n"
                msg += f"      <pre>Longitude: {resp['location']['lon']}</pre>\n"
                msg += "\n"
                msg += f"   <b>🌱 Watering Algorithm status</b>:\n"
                msg += f"      <pre>Last readings: </pre>\n"
                msg += f"         <pre>Air humidity   : {str(f'{ah:.2f}%') if ah != -1 else 'NaN'}</pre>\n"                   
                msg += f"         <pre>            max: {ah_max:.2f}%</pre>\n"
                msg += f"         <pre>            min: {ah_min:.2f}%</pre>\n"
                msg += f"         <pre>Air temperature: {str(f'{at:.2f}°C') if at != -1 else 'NaN'}</pre>\n"
                msg += f"         <pre>            max: {at_max:.2f}°C</pre>\n"
                msg += f"         <pre>            min: {at_min:.2f}°C</pre>\n"
                msg += f"         <pre>Soil humidity  : {str(f'{sh:.2f}%') if sh != -1 else 'NaN'}</pre>\n"
                msg += f"         <pre>            max: {sh_max:.2f}%</pre>\n"
                msg += f"         <pre>            min: {sh_min:.2f}%</pre>\n"

        elif pagenum == 2:
            # sensors sample period page
            r = self.catreq.reqREST("DeviceConfig", "/configs?path=/sensors")
            if not r.status or r.code_response != 200:
                if chat_ID is not None:
                    self.bot.sendMessage(chat_ID, f"Error while requesting data from the DeviceConfig {r.code_response}: {r.json_response}", reply_markup=kboard)
                elif msgid is not None:
                    self.bot.editMessageText(msgid, f"Error while requesting data from the DeviceConfig {r.code_response}: {r.json_response}", reply_markup=kboard)
                return
            
            msg += "<b>🔧 Settings</b>:\n"
            msg += "   <b>🌱 Sensors</b>:\n"
            msg += f"      <pre>Sampling Period:</pre>\n"
            max_len = 0
            for k in r.json_response:
                max_len = max(max_len, len(str(k)))

            for n, p in r.json_response.items():
                msg += f"         <pre>{str(n).ljust(max_len)}: {(p['sampleperiod']/1000):.2f} s</pre>\n"

            # location and timezone page
            msg += "\n"
            msg += "   <b>🧭 Location</b>:\n"
            r = self.catreq.reqREST("DeviceConfig", "/configs?path=/system/")
            if not r.status or r.code_response != 200:
                if chat_ID is not None:
                    self.bot.sendMessage(chat_ID, f"Error while requesting data from the DeviceConfig {r.code_response}: {r.json_response}", reply_markup=kboard)
                elif msgid is not None:
                    self.bot.editMessageText(msgid, f"Error while requesting data from the DeviceConfig {r.code_response}: {r.json_response}", reply_markup=kboard)
                return

            msg += f"      <pre>Latitude : {r.json_response['location']['lat']}</pre>\n"
            msg += f"      <pre>Longitude: {r.json_response['location']['lon']}</pre>\n"
            msg += f"      <pre>Timezone : {r.json_response['timezone']['actual']}</pre>\n"

        elif pagenum == 3:
            # system resource page
            try:
                sysinfo = self.catreq.reqSysInfo()
            except Exception as e:
                if chat_ID is not None:
                    self.bot.sendMessage(chat_ID, f"Error while requesting data from the DeviceConfig: {e}", reply_markup=kboard)
                elif msgid is not None:
                    self.bot.editMessageText(msgid, f"Error while requesting data from the DeviceConfig: {e}", reply_markup=kboard)
                return

            msg += "<b>🖥️ System</b>:\n"
            msg += f"   <pre>CPU:</pre>\n"
            msg += f"      <pre>Freq : {int(sysinfo['cpu']['freq'][0])} MHz</pre>\n"
            msg += f"      <pre>Cores: {sysinfo['cpu']['count']}</pre>\n"
            msg += f"      <pre>Usage: {sysinfo['cpu']['percent']}%</pre>\n"

            msg += f"   <pre>RAM:</pre>\n"
            msg += f"      <pre>Total: {Utils.convert_size(sysinfo['ram']['total'])}</pre>\n"
            msg += f"      <pre>Used : {Utils.convert_size(sysinfo['ram']['used'])}</pre>\n"
            msg += f"      <pre>Free : {Utils.convert_size(sysinfo['ram']['free'])}</pre>\n"
            msg += f"      <pre>Usage: {sysinfo['ram']['percent']}%</pre>\n"
            msg += f"   <pre>Disk:</pre>\n"
            msg += f"      <pre>Total: {Utils.convert_size(sysinfo['disk']['total'])}</pre>\n"
            msg += f"      <pre>Used : {Utils.convert_size(sysinfo['disk']['used'])}</pre>\n"
            msg += f"      <pre>Free : {Utils.convert_size(sysinfo['disk']['free'])}</pre>\n"
            msg += f"      <pre>Usage: {sysinfo['disk']['percent']}%</pre>\n"
            msg += f"   <pre>Network:</pre>\n"
            msg += f"      <pre>Received: {Utils.convert_size(sysinfo['network']['bytes_recv'])}</pre>\n"
            msg += f"      <pre>Sent    : {Utils.convert_size(sysinfo['network']['bytes_sent'])}</pre>\n"
            msg += f"   <pre>Uptime:</pre>\n"
            msg += f"      <pre>Elapsed: {timedelta(seconds=sysinfo['uptime'])}</pre>\n"


        msg += "\n"
        msg += f"Updated at: <pre>{Utils.get_user_dt_woffset(time.time(), self._timezone, '%d-%m-%Y %H:%M:%S.%f')}</pre>"

        if chat_ID is not None:
            self.bot.sendMessage(chat_ID, msg, reply_markup=kboard, parse_mode="HTML")
        elif msgid is not None:
            self.bot.editMessageText(msgid, msg, reply_markup=kboard, parse_mode="HTML")

    def _set_location_dc(self, lat, lon): 

        lat = float(lat)
        lon = float(lon)

        # request timezone info
        try:
            url = f"http://api.geonames.org/timezoneJSON?lat={lat}&lng={lon}&username=gabriele97"
            r = requests.get(url)
        except:
            self.logger.error(f"Error while requesting timezone info from geonames.org")

        # parse response
        set_tz = r is not None and r.status_code == 200
        if set_tz:
            resp = r.json()
            set_tz = "timezoneId" in resp

        # set timezone if possible
        set_tz_final = None
        r1 = None
        if set_tz:
            set_tz_final = resp["timezoneId"]
            r = self.catreq.reqREST("DeviceConfig", "/configs?path=/system/timezone/actual", reqt=RequestType.PUT, datarequest={"v": set_tz_final})
            set_tz_final = None if not r.status or r.code_response != 200 else set_tz_final
        else:
            # set the default one
            r1 = self.catreq.reqREST("DeviceConfig", "/configs?path=/system/timezone/default")

            if not r1.status or r1.code_response != 200:
                self.logger.error(f"Error while retrieving the default timezone")
            else:
                r = self.catreq.reqREST("DeviceConfig", "/configs?path=/system/timezone/actual", reqt=RequestType.PUT, datarequest=r1.json_response)

        # set location
        set_loc_final = {"lat": lat, "lon": lon}
        r = self.catreq.reqREST("DeviceConfig", "/configs?path=/system/location", reqt=RequestType.PUT, datarequest=set_loc_final)
        if not r.status or r.code_response != 200:
            set_loc_final = None

        return (set_tz_final, set_loc_final, set_tz, r1)
        

    def _set_pos_msg(self, res):

        self.logger.debug(f"_set_pos_msg: {res}")

        msg = ""
        msg += "<b>🧭 Location </b>:\n"
        msg += f"   <pre>Latitude : {res[1]['lat']}</pre>\n"
        msg += f"   <pre>Longitude: {res[1]['lon']}</pre>\n"
        msg += f"   <pre>Timezone : {res[0] if res[0] is not None else 'Error setting up it' if res[2] else f'Default to ' + res[3].json_response['v']}</pre>\n"

        return msg

    def _doreq_orerror(self, text, chat_ID = None, msgid = None, kboard = None):

        if chat_ID is not None:
            self.bot.sendMessage(chat_ID, text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
        elif msgid is not None:
            self.bot.editMessageText(msgid, text, parse_mode="HTML", reply_markup=kboard)
