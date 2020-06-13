#!/usr/bin/env python3
import globals
from datetime import datetime
import paho.mqtt.publish as publish
import numpy as np
import imutils
import freenect
import cv2
import pickle
from threading import Thread, Lock
from logger import log
from notifier import Notifier

import face_recognition

data = pickle.loads(open('./embeddings/encodings.pickle', "rb").read())
known_face_encodings = data['known_face_encodings']
known_face_names = data['known_face_names']

MOTION_SIZE_THRESHOLD = 600 # higher means it will detect bigger movements and not smaller ones
MOTION_FRAMES_THRESHOLD = 3 # number of frames where motion is detected before it starts looking for faces
MOTION_DELTA_THRESHOLD = 15 # higher means it will detect bigger movements and not smaller ones

SNAPSHOT_DIR = '/share/'

def pretty_time():
	return datetime.today().strftime('%Y-%m-%d %H_%M_%S')

if globals.OFFLINE_MODE:
	cv2.namedWindow('Movement')

class Detector:
	average = None
	motion_frames = []
	thread = None
	running = False
	frame = None

	def __init__(self):
		if Detector.thread is None:
			self.start()

	def start(self):
		log('DETECTOR', 'Starting detector...')
		Detector.running = True
		Detector.thread = Thread(target=self.detection_thread, args=())
		Detector.thread.start()

	def stop(self):
		Detector.running = False

	# the main detection thread
	@classmethod
	def detection_thread(cls):
		while Detector.running:
			motion = cls.detect_motion()
			full_frame = None
			face_frame = None
			name = "Unknown"

			# if there is motion look for faces and save images
			if motion is True:
				Notifier.notify_movement()
				face_frame, name, full_frame = cls.detect_faces()

				if face_frame is None:
					log('DETECTOR', 'No faces.')
				else:
					log('DETECTOR', 'Found ' + name)
					if globals.OFFLINE_MODE:
						cv2.imshow('Face', face_frame)

				for frame_obj in cls.motion_frames:
					for movement in frame_obj['motion_boxes']:
						cv2.imwrite(SNAPSHOT_DIR+pretty_time()+'_motion.jpg', frame_obj['frame'])

				cls.motion_frames = []

			if face_frame is not None:
				Notifier.notify(name)
				cv2.imwrite(SNAPSHOT_DIR+pretty_time()+'_face.jpg', full_frame)

	@classmethod
	def update_frame(cls, frame):
		Detector.frame = frame

	# Finds faces in a frame
	# Returns: The cropped face (or none), the name of the face (or none, or "unknown"), the full frame with the face highlighted (or none)
	@classmethod
	def detect_faces(cls):
		log('DETECTOR', 'Detecting faces in the last '+str(MOTION_FRAMES_THRESHOLD)+' frames...')
		name = "Unknown"
		face_frame = None
		full_frame = None
		location = None

		for frame_obj in cls.motion_frames:
			small_frame = cv2.resize(frame_obj['frame'], (0, 0), fx=0.5, fy=0.5)
			rgb_small_frame = small_frame[:, :, ::-1]

			face_locations = face_recognition.face_locations(rgb_small_frame)
			face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

			for i, face_encoding in enumerate(face_encodings):
				matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
				name = "Unknown"
				face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
				best_match_index = np.argmin(face_distances)

				location = face_locations[i]
				full_frame = frame_obj['frame'].copy()

				if matches[best_match_index]:
					name = known_face_names[best_match_index]
					# As soon as we have someone stop looking
					break

		# Cut out the face
		if location is not None:
			(top, right, bottom, left) = location
			top *= 2
			right *= 2
			bottom *= 2
			left *= 2

			# Draw a box around the face
			cv2.rectangle(full_frame, (left, top), (right, bottom), (0, 0, 255), 2)

			# Draw a label with a name below the face
			cv2.rectangle(full_frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
			font = cv2.FONT_HERSHEY_DUPLEX
			cv2.putText(full_frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

			face_frame = full_frame[top:bottom, left:right].copy()

		return face_frame, name, full_frame

	# Blurs and grayscales a frame
	# Params: Frame
	@staticmethod
	def blur_and_gray(frame):
		output = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		output = cv2.GaussianBlur(output, (21, 21), 0)
		return output

	# Finds big contour boxes in a frame
	# Params: Input frame to look at
	# Returns: List of boxes it found
	@staticmethod
	def find_boxes(frame):
		cnts = cv2.findContours(frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		return list(filter(lambda c: cv2.contourArea(c) > MOTION_SIZE_THRESHOLD, cnts))

	# Detects motion in the stream
	# Params: List of frames it found motion in if it did
	@classmethod
	def detect_motion(cls):
		if cls.frame is None:
			return False

		current_frame_gray = Detector.blur_and_gray(cls.frame.copy())

		if cls.average is None:
			cls.average = current_frame_gray.copy().astype("float")

		cls.average = cv2.accumulateWeighted(current_frame_gray, cls.average, 0.5)
		frameDelta = cv2.absdiff(current_frame_gray, cv2.convertScaleAbs(cls.average))
		thresh = cv2.threshold(frameDelta, MOTION_DELTA_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
		thresh = cv2.dilate(thresh, None, iterations=2)

		if globals.OFFLINE_MODE:
			cv2.imshow('Movement', thresh)

		motion_boxes = Detector.find_boxes(thresh)

		if len(motion_boxes) > 0:
			cls.motion_frames.append({'frame': cls.frame, 'motion_boxes': motion_boxes})
		else:
			cls.motion_frames = []

		if len(cls.motion_frames) > MOTION_FRAMES_THRESHOLD:
			return True
		else:
			return False
