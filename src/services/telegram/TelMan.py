from datetime import datetime
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

        self._bot_th = WIOThread(target=self._handler_bot_th, name="Telegram Bot Handler")
        self._bot_th.run()

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

            kboard_inner = self._gen_kboard(None, l.raspberrys, lambda x: f"setlinks:{name}:remlink:{x}", InlineKeyboardButton)
            kboard_inner.append([InlineKeyboardButton(text="Back", callback_data=f"setlinks:{name}")])
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

            kboard_inner = self._gen_kboard(f"{from_} ➡️ ", l.arduinos, lambda x: f"setlinks:{name}:remlink:{from_}:{x}", InlineKeyboardButton)
            kboard_inner.append([InlineKeyboardButton(text="Back", callback_data=f"setlinks:{name}")])
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

            kboard_inner = self._gen_kboard(None, ids, lambda x: f"setlinks:{name}:addlink:{x}", InlineKeyboardButton)
            kboard_inner.append([InlineKeyboardButton(text="Back", callback_data=f"setlinks:{name}")])
            kboard = InlineKeyboardMarkup(inline_keyboard=kboard_inner)
            self.bot.editMessageText(msgid, query["message"]["text"], parse_mode="HTML", reply_markup=kboard)
        
        elif regx5.match(query["data"]):

            name = regx5.match(query["data"]).group("name")
            from_ = regx5.match(query["data"]).group("from")
            ids = self.catreq.reqDeviceIdsList("ArduinoDevConn")
            
            kboard_inner = self._gen_kboard(f"{from_} ➡️ ", ids, lambda x: f"setlinks:{name}:addlink:{from_}:{x}", InlineKeyboardButton)
            kboard_inner.append([InlineKeyboardButton(text="Back", callback_data=f"setlinks:{name}")])
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
                    InlineKeyboardButton(text="Delete", callback_data=f"setlinks:{name}:delete"),
                    InlineKeyboardButton(text="Add Link", callback_data=f"setlinks:{name}:addlink"),
                    InlineKeyboardButton(text="Remove Link", callback_data=f"setlinks:{name}:remlink")
                ],
                [
                    InlineKeyboardButton(text="Back", callback_data=f"setlinks:{name}:back")
                ]
            ])
            self.bot.editMessageText(msgid, msg, reply_markup=kboard, parse_mode="HTML")
            # self.logger.debug(f"Telegram Bot: setlinks: {name}")
            # self.bot.answerCallbackQuery(query["id"], text="Подождите, идет поиск привязки...")
        elif regx8.match(query["data"]):
            
            kboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Back", callback_data=f"setlinks:nd:back")
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
                    InlineKeyboardButton(text="Apply", callback_data=f"setdatabase:{name}:apply"),
                    InlineKeyboardButton(text="Delete", callback_data=f"setdatabase:{name}:delete")
                ],
                [
                    InlineKeyboardButton(text="Back", callback_data=f"setdatabase:{name}:back")
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
                    InlineKeyboardButton(text="Back", callback_data=f"setdatabase:nd:back")
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
                        self.bot.sendMessage(chat_ID, "No parameter. Please select one sensor (<temp>,<airhum>,<soilhum>) as first parameter and a value as second", reply_markup=ReplyKeyboardRemove())
                    elif message.split()[1] not in ["temp", "airhum","soilhum"]:
                        self.bot.sendMessage(chat_ID, "Wrong parameter. Please select one sensor(<temp>,<airhum>,<soilhum>) as first parameter and a value as second", reply_markup=ReplyKeyboardRemove())
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
                "*/status* \\- Get the actual system status\n"
                "*/switch <on/off\\>* \\- Turn on or off the irrigator\n"
                "*/getairt* \\- Retrive temperature of the air\n"
                "*/getairu*  \\- Retrive umidity of the air\n"
                "*/getsoilu* \\- Retrive umidity of the soil\n"
                "*/pos* \\- Sets latitude and longitude where retrive weather forecasting\n"
                "*/config* \\(<temp\\>\\|<airhum\\>\\|<soilhum\\>\\) <value\\> \\- Config the sensors: sets the period of sampling of the sensors\n"
                "*/config* \\(<temp\\>\\|<airhum\\>\\|<soilhum\\>\\) \\(<min\\>\\|<max\\>\\) <value\\> \\- Config the watering: sets the temperature and moisture bounds in which turn on or off the watering system\n"))

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

                    dt = datetime.fromtimestamp(resp["t"]).strftime("%d-%m-%Y %H:%M:%S")

                    msg  = '<pre>'
                    msg += f'🖥️ sensor: {resp["n"]}\n'
                    msg += f'🔢 dev # : {resp["i"]}\n'
                    msg += f'🕟 time  : {dt}\n'
                    msg += f'📟 value : {resp["v"]}{resp["u"]}'
                    msg += '</pre>'

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

                        msg = "Result: <pre>"
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
                    
                    msg = ""
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

                    self.bot.sendMessage(chat_ID, msg, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                    
                    msg = ""
                    done, resp, code = self.catreq.reqREST("WateringControl", "/status")
                    if not done or code != 200:
                        self.bot.sendMessage(chat_ID, f"Error while requesting data from the WateringControl {code}: {resp}", reply_markup=ReplyKeyboardRemove())
                        return

                    dt_lastnorm = datetime.fromtimestamp(resp['telegram']['last_sent_msg_timestamp']).strftime("%d-%m-%Y %H:%M:%S") if resp['telegram']['last_sent_msg_timestamp'] != -1 else "never"
                    dt_nextnorm = datetime.fromtimestamp(resp['telegram']['last_sent_msg_timestamp'] + resp["telegram"]["min_time_between_messages"]).strftime("%d-%m-%Y %H:%M:%S") if resp['telegram']['last_sent_msg_timestamp'] != -1 else "ASAP"
                    dt_lastcrit = datetime.fromtimestamp(resp['telegram']['last_sent_msgcrit_timestamp']).strftime("%d-%m-%Y %H:%M:%S") if resp['telegram']['last_sent_msgcrit_timestamp'] != -1 else "never"
                    dt_nextcrit = datetime.fromtimestamp(resp['telegram']['last_sent_msgcrit_timestamp'] + resp["telegram"]["min_time_between_messages_crit"]).strftime("%d-%m-%Y %H:%M:%S") if resp['telegram']['last_sent_msgcrit_timestamp'] != -1 else "ASAP"

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

                    self.bot.sendMessage(chat_ID, msg, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                
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
                status, json_response_0, code_response1 = self.catreq.reqREST("DeviceConfig","/configs?path=/system/location/lat",RequestType.PUT,{"v": float(msg["location"]["latitude"])})
                status, json_response_1, code_response2 = self.catreq.reqREST("DeviceConfig","/configs?path=/system/location/lon",RequestType.PUT,{"v": float(msg["location"]["longitude"])})
                if code_response1 == 200 and code_response2 == 200 :
                    self.bot.sendMessage(chat_ID, "Location set properly!", reply_markup=ReplyKeyboardRemove())
                else:
                    self.bot.sendMessage(chat_ID, f"An error occourred:\nlat:\n{json_response_0}\n\nlon:\n{json_response_1}", reply_markup=ReplyKeyboardRemove())

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

        kboard_inner = self._gen_kboard(None, [l.name for l in links.data], lambda x: f"setlinks:{x}", InlineKeyboardButton, 2)
        kboard_inner.append([InlineKeyboardButton(text="create", callback_data="setlinks_create")])
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

        kboard_inner = self._gen_kboard(None, [i["name"] for i in items], lambda x: f"setdatabase:{x}", InlineKeyboardButton)
        kboard_inner.append([InlineKeyboardButton(text="create", callback_data="setdatabase_create")])
        kboard = InlineKeyboardMarkup(inline_keyboard=kboard_inner)

        if chat_ID is not None:
            self.bot.sendMessage(chat_ID, msg, reply_markup=kboard, parse_mode="HTML")
        elif msgid is not None:
            self.bot.editMessageText(msgid, msg, parse_mode="HTML", reply_markup=kboard)

    def _setreadings_msglist(self, chat_ID = None, msgid = None, devid = None):

        ids = self.catreq.reqDeviceIdsList("RaspberryDevConn")
        devid = None if len(ids) == 0 else ids[0] if devid is None else int(devid)

        kboard_inner = self._gen_kboard("Device ", ids, lambda x: f"setdevice:{x}", InlineKeyboardButton)
        kboard_inner.append([InlineKeyboardButton(text="refresh", callback_data=f"setdevice:{devid}:refresh")])
        kboard = InlineKeyboardMarkup(inline_keyboard=kboard_inner)

        a = b = c = None

        r0 = self.catreq.reqREST("RaspberryDevConn", "/airhumidity", devid=devid)
        if not r0.status or r0.code_response != 200:
            self.bot.sendMessage(chat_ID, f"Error while requesting data {r0.code_response}: {r0.json_response}", reply_markup=ReplyKeyboardRemove())
        else:
            a = r0.json_response

        r1 = self.catreq.reqREST("RaspberryDevConn", "/airtemperature", devid=devid)
        if not r1.status or r1.code_response != 200:
            self.bot.sendMessage(chat_ID, f"Error while requesting data {r1.code_response}: {r1.json_response}", reply_markup=ReplyKeyboardRemove())
        else:
            b = r1.json_response

        r2 = self.catreq.reqREST("RaspberryDevConn", "/terrainhumidity", devid=devid)
        if not r2.status or r2.code_response != 200:
            self.bot.sendMessage(chat_ID, f"Error while requesting data {r2.code_response}: {r2.json_response}", reply_markup=ReplyKeyboardRemove())
        else:
            c = r2.json_response
        
        msg = self._setreadings_prepmsg(a, b, c, devid=devid)
        if chat_ID is not None:
            self.bot.sendMessage(chat_ID, msg, reply_markup=kboard, parse_mode="HTML")
        elif msgid is not None:
            self.bot.editMessageText(msgid, msg, reply_markup=kboard, parse_mode="HTML")
    

    def _setreadings_prepmsg(self, airhum = None, airtemp = None, soilhum = None, devid = "ND"):

        dt0 = datetime.fromtimestamp(airhum["t"]).strftime("%d-%m-%Y %H:%M:%S") if airhum is not None else "..."
        dt1 = datetime.fromtimestamp(airtemp["t"]).strftime("%d-%m-%Y %H:%M:%S") if airtemp is not None else "..."
        dt2 = datetime.fromtimestamp(soilhum["t"]).strftime("%d-%m-%Y %H:%M:%S") if soilhum is not None else "..."

        msg = ""
        msg += f"<b>📊 Readings <i>(dev #{devid})</i></b>:\n"
        msg += f"   <i>Air humidity   :</i>\n"
        msg += f"<pre>"
        msg += f'      🖥️ sensor: {airhum["n"] if airhum is not None else "..."}\n'
        msg += f'      🕟 time  : {dt0}\n'
        msg += f'      📟 value : {airhum["v"] if airhum is not None else ".."}{airhum["u"] if airhum is not None else "."}\n'
        msg += f"</pre>"
        msg += f"   <i>Air temperature: </i>\n"
        msg += f"<pre>"
        msg += f'      🖥️ sensor: {airtemp["n"] if airtemp is not None else "..."}\n'
        msg += f'      🕟 time  : {dt1}\n'
        msg += f'      📟 value : {airtemp["v"] if airtemp is not None else ".."}{airtemp["u"] if airtemp is not None else "."}\n'
        msg += f"</pre>"
        msg += f"   <i>Soil humidity  : </i>\n"
        msg += f"<pre>"
        msg += f'      🖥️ sensor: {soilhum["n"] if soilhum is not None else "..."}\n'
        msg += f'      🕟 time  : {dt2}\n'
        msg += f'      📟 value : {soilhum["v"] if soilhum is not None else ".."}{soilhum["u"] if soilhum is not None else "."}\n'
        msg += f"</pre>"

        return msg    

