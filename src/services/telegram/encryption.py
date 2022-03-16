# Import bcrypt:
import bcrypt 
import json

data = {
    'hashed' : '',
    'ids' : []
    }

def setPassword():
    data = {
    'hashed' : '',
    'ids' : []
    }
    password = "Polito22"
    password = password.encode('utf-8')     # Encode password into a readable utf-8 byte code: 
    data['hashed'] = bcrypt.hashpw(password, bcrypt.gensalt()).decode('ascii')     # Hash the ecoded password and generate a salt: 
    with open('data.json', 'w') as json_file:
        json.dump(data, json_file)

def checkPassword(check):
    with open('data.json', 'r') as f:
        data = json.load(f)
    # Encode the authenticating password as well:
    check = check.encode('utf-8') 
    # Use conditions to compare the authenticating password with the stored one:
    if bcrypt.checkpw(check, data['hashed'].encode('utf-8')):
        return True
    else:
        return False

def changePassword(old,new):
    with open('data.json', 'r') as f:
        data = json.load(f)
    old = old.encode('utf-8')
    if bcrypt.checkpw(old,data['hashed'].encode('utf-8')):
        new = new.encode('utf-8')
        data = {
                'hashed' : '',
                'ids' : []
                }
        data['hashed'] = bcrypt.hashpw(new, bcrypt.gensalt()).decode('ascii')
        with open('data.json', 'w') as json_file:
            json.dump(data, json_file)
        return True
    else :
        return False

def addID(new):
    with open('data.json', 'r') as f:
        data = json.load(f)
    if new not in data["ids"] :
        data['ids'].append(new)
        with open('data.json', 'w') as json_file:
            json.dump(data, json_file)
        return True
    else:
        return False

def checkID(check):
    with open('data.json', 'r') as f:
        data = json.load(f)
    if check not in data["ids"] :
        return False
    else:
        return True


    