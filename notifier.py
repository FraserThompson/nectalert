import globals
import paho.mqtt.publish as publish
from datetime import datetime, timedelta
import os
import pyttsx3
from logger import log

HOSTNAME = "localhost"
notify_list = {
	'fraser': {
		'greeting': 'hello_fraser.wav'
	}, 
	'peter': {
		'greeting': 'hello_peter.wav'
	},
	'james': {
		'greeting': 'jamesishere.wav'
	}
}

class Notifier:
	last_notify = None
	cooldown = 8.0

	@classmethod
	def notify(cls, name):
		the_past = datetime.now() - timedelta(seconds=cls.cooldown)

		# If five seconds has passed since last notification
		if cls.last_notify and the_past >= cls.last_notify:
			cls.last_notify = None
		elif cls.last_notify and the_past <= cls.last_notify:
			log("NOTIFY", "We already notified, not notifying for a bit.")
			return

		# Set the notify to now
		if not cls.last_notify:
			cls.last_notify = datetime.now()

		friend = notify_list.get(name)

		if friend:
			if friend['greeting'] is not False:
				Notifier.notify_friend(name, friend)
		else:
			Notifier.notify_stranger()

	# Notify with a custom greeting
	@staticmethod
	def notify_friend(name, friend):
		log('NOTIFY', 'Hello ' + name)
		publish.single("home/doorbell_greet", friend['greeting'], hostname=globals.HOSTNAME)

	
	# Notify with a doorbell sound
	@staticmethod
	def notify_stranger():
		log("NOTIFY", "ANOTHER VISITOR... STAY A WHILE?")
		publish.single("home/another_visitor", "Yes", hostname=globals.HOSTNAME)

	@staticmethod
	def notify_movement():
		log("NOTIFY", "Motion detected")
		publish.single("home/frontdoor_movement", "Yes", hostname=globals.HOSTNAME)