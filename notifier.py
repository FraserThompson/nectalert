import paho.mqtt.publish as publish
from datetime import datetime, timedelta
import os
import pyttsx3
from logger import log

HOSTNAME = "localhost"
residents_list = ['jimothy']

class Notifier:
	last_notify = None
	cooldown = 5.0

	@classmethod
	def notify(cls, name):
		if name in residents_list:
			log('NOTIFY', 'Hello ' + name)
			os.system('aplay /home/pi/nectalert/sounds/hello_' + name + '.wav')
			return

		the_past = datetime.now() - timedelta(seconds=cls.cooldown)

		if cls.last_notify and the_past >= cls.last_notify:
			cls.last_notify = None

		if not cls.last_notify:
			cls.last_notify = datetime.now()
			log("NOTIFY", "ANOTHER VISITOR... STAY A WHILE?")
			publish.single("home/another_visitor", "Yes", hostname=HOSTNAME)
			os.system('aplay /home/pi/nectalert/sounds/doorbell.wav')

	@classmethod
	def unnotify(cls):
		publish.single("home/another_visitor", "No", hostname=HOSTNAME)
