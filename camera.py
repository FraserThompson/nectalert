#!/usr/bin/env python3
import globals
import time
import sys
from datetime import datetime
import numpy as np
import imutils
from threading import Thread, Lock
from logger import log
import freenect
import cv2
import frame_convert2
from detector import Detector

class Camera:
	read_lock = Lock()
	thread = None
	running = False
	frame = None
	outputFrame = None

	def __init__(self):
		if Camera.thread is None:
			self.start()

		# Setup our windows if we want them
		if globals.OFFLINE_MODE:
			cv2.namedWindow('Video')
			cv2.namedWindow('Face')
			print('Press ESC in window to stop')

	@classmethod
	def stop(cls):
		log('CAMERA', 'Stopping camera...')
		Camera.running = False

	def start(self):
		log('CAMERA', 'Starting camera...')
		Camera.running = True
		Camera.thread = Thread(target=self.video_thread, args=())
		Camera.thread.start()

	def read(self):
		with Camera.read_lock:
			return Camera.outputFrame

	@staticmethod
	def is_night():
		now = datetime.now()
		today_sunset = now.replace(hour=21, minute=30, second=0, microsecond=0)
		return now >= today_sunset

	# Returns true if the frame is pretty dark
	@staticmethod
	def is_dark(frame):
		new_frame = Detector.blur_and_gray(frame.copy())
		total_pixels = np.size(new_frame)
		hist = cv2.calcHist([new_frame], [0], None, [256], [0, 256])
		dark_pixels = np.sum(hist[:30])
		if dark_pixels/total_pixels > 0.6:
			return True
		return False

	# Returns stuff which is within the distance
	@staticmethod
	def get_depth():
		current_depth = 1000
		threshold = 400
		depth, timestamp = freenect.sync_get_depth(0, freenect.DEPTH_MM)
		depth = 255 * np.logical_and(depth >= current_depth - threshold,
                                 depth <= current_depth + threshold)
		return depth.astype(np.uint8)


	# Returns a frame from the camera depending on the mode
	@staticmethod
	def get_video(mode, i = 0):
		if i == 3:
			log('CAMERA', 'Could not get video, does your kinect work?')
			sys.exit(1)
		try:
			if mode == "night":
				return Camera.get_ir()
			else:
				return Camera.get_rgb()
		except TypeError:
			log('CAMERA', 'Failed to get video frame, attempt ' + str(i))
			time.sleep(5)
			return Camera.get_video(mode, i + 1)

	# Returns a 10 bit RGB frame from the IR camera
	@staticmethod
	def get_ir():
		array,_ = freenect.sync_get_video(0, freenect.VIDEO_IR_10BIT)
		return cv2.cvtColor(frame_convert2.pretty_depth_cv(array), cv2.COLOR_GRAY2RGB)

	# Returns a 10 bit RGB frame from the normal camera
	@staticmethod 
	def get_rgb():
		return frame_convert2.video_cv(freenect.sync_get_video()[0])

	# Gets frames, detects faces
	@classmethod
	def video_thread(cls):
		detectorer = Detector()
		while Camera.running:
			Camera.frame = cls.get_video(Camera.is_night())

			if globals.OFFLINE_MODE:
				cv2.imshow('Depth', depth)

			detectorer.update_frame(Camera.frame)

			with Camera.read_lock:
				Camera.outputFrame = Camera.frame

				if globals.OFFLINE_MODE:
					cv2.imshow('Video', Camera.outputFrame)
	
		if Camera.running is False:
			log('CAMERA', 'Camera stopped.')
			return
