#!/usr/bin/env python3
import globals
import threading
import cv2
import time
import freenect
from logger import log
from flask import Response
from flask import request
from flask import Flask
from flask import render_template

from camera import Camera

app = Flask(__name__)

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/video_feed")
def video_feed():
	capture = Camera()
	#time.sleep(6)
	return Response(generate(capture, "video"), mimetype = "multipart/x-mixed-replace; boundary=frame")

# Used to serve up frames to the web server
def generate(capture, type="video"):
	while True:
		outputFrame = capture.read()

		if outputFrame is None:
			continue

		(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

		if not flag:
			continue

		yield(b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

#app.run(host="smell.today", port=8069, debug=True, threaded=True, use_reloader=False, ssl_context=('/etc/letsencrypt/live/smell.today/fullchain.pem', '/etc/letsencrypt/live/smell.today/privkey.pem'))

# Can be used to adjust tilt
def set_led_and_tilt(dev, ctx):
	freenect.set_led(dev, 2)
	freenect.set_tilt_degs(dev, -10)
	time.sleep(3)
	raise freenect.Kill

#freenect.runloop(body=set_led_and_tilt)

# starts the wsgi server
if not globals.OFFLINE_MODE and __name__ == "__main__":
	app.run(use_reloader=False)

if globals.OFFLINE_MODE:
	Camera()
