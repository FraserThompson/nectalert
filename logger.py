from datetime import datetime

def log(type, message):
	print(str(datetime.now()) + ' ' + type + ': ' + message)
