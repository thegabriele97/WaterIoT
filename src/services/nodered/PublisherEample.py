from myMQTT import *
import time
import json
import random
class LedManager:
	def __init__(self, clientID, topic,broker,port):
		self.topic=topic
		self.__message={'client': clientID,'n':'switch','value':None, 'timestamp':'','unit':"bool"}

		self.client=MyMQTT(clientID,broker,port,None)


	def start (self):
		self.client.start()

	def stop (self):
		self.client.stop()

	def publish(self):
		message=self.__message
		message['timestamp']=str(time.time())
		message['value']=random.random()*20
		self.client.myPublish(self.topic,message)
		print("published "+str(message['value']))



if __name__ == "__main__":
	conf=json.load(open("settingsMQTT.json"))
	broker=conf["broker"]
	port=conf["port"]
	ledManager = LedManager("WaterIoTPublish","WaterIoT/led",broker,port)
	ledManager.client.start()
	time.sleep(2)
	print('Welcome to the client to switch on/off the lamp\n')
	done=False
	while not done:
		ledManager.publish()
		time.sleep(3)
	ledManager.client.stop()   


