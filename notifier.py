import globals
import paho.mqtt.publish as publish
from datetime import datetime, timedelta
import os
import pyttsx3
from logger import log

HOSTNAME = "localhost"
notify_list = {
	'fraser': {
		'notify': False,
		'greeting': 'hello_fraser.wav'
	}, 
	'peter': {
		'notify': False,
		'greeting': 'hello_peter.wav'
	},
	'james': {
		'notify': True,
		'greeting': 'jamesishere.wav'
	}
}

class Notifier:
	last_notify = None
	cooldown = 5.0

	@classmethod
	def notify(cls, name):
		the_past = datetime.now() - timedelta(seconds=cls.cooldown)

		if cls.last_notify and the_past >= cls.last_notify:
			cls.last_notify = None

		if not cls.last_notify:
			cls.last_notify = datetime.now()

		person = notify_list.get(name)

		# Play a sound
		if person:
			if person['greeting'] is not False:
				log('NOTIFY', 'Hello ' + name)
				os.system('aplay /home/pi/nectalert/sounds/' + notify_list[name]['greeting'])
			if person['notify'] is False:
				return
		else:
			os.system('aplay /home/pi/nectalert/sounds/doorbell.wav')

		Notifier.notify_stranger()

	@staticmethod
	def notify_stranger():
		log("NOTIFY", "ANOTHER VISITOR... STAY A WHILE?")
		publish.single("home/another_visitor", "Yes", hostname=globals.HOSTNAME)

	@classmethod
	def unnotify(cls):
		publish.single("home/another_visitor", "No", hostname=globals.HOSTNAME)
