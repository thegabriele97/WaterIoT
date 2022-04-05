# Import bcrypt:
import bcrypt 
import json

from common.SettingsManager import SettingsManager
from common.JSONManager import JSONManager

class Encryption:

    def __init__(self) -> None:
        self._data = JSONManager(SettingsManager.relfile2abs("data.json"), structure_mod_allowed=True)

    def setPassword(self):

        data = {
            'hashed' : '',
            'ids' : []
        }

        password = "Polito22"
        password = password.encode('utf-8')     # Encode password into a readable utf-8 byte code: 
        data['hashed'] = bcrypt.hashpw(password, bcrypt.gensalt()).decode('ascii')     # Hash the ecoded password and generate a salt: 
        self._data.set('/', data)

    def checkPassword(self, check):
        data = self._data.get('/')
        # Encode the authenticating password as well:
        check = check.encode('utf-8') 
        # Use conditions to compare the authenticating password with the stored one:
        return bcrypt.checkpw(check, data['hashed'].encode('utf-8'))

    def changePassword(self, old, new):
        data = self._data.get('/')
        old = old.encode('utf-8')

        if bcrypt.checkpw(old,data['hashed'].encode('utf-8')):
            new = new.encode('utf-8')
            data = {
                'hashed' : '',
                'ids' : []
            }
            data['hashed'] = bcrypt.hashpw(new, bcrypt.gensalt()).decode('ascii')
            self._data.set('/', data)
            return True

        return False

    def addID(self, new):

        data = self._data.get('/')
        if new not in data["ids"] :
            data['ids'].append(new)
            self._data.set("/", data)
            return True

        return False

    def checkID(self, check):
        data = self._data.get('/')
        return check in data["ids"]

    def getIDs(self):
        data = self._data.get('/')
        return data["ids"]
