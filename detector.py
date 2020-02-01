#!/usr/bin/env python3
import globals
from datetime import datetime
import numpy as np
import imutils
import freenect
import cv2
import pickle
import frame_convert2
from threading import Thread, Lock
from logger import log
from notifier import Notifier

MOTION_SIZE_THRESHOLD = 2000
MOTION_FRAMES_THRESHOLD = 8
MOTION_DELTA_THRESHOLD = 5
FACE_RECOGNITION_PROBABILITY = 0.6
FACE_DETECTION_PROBABILITY = 0.6

SNAPSHOT_DIR = '/share/'

# Various third party models for face detection
detector = cv2.dnn.readNetFromTensorflow("lib/opencv_face_detector_uint8.pb", "lib/opencv_face_detector.pbtxt")
embedder = cv2.dnn.readNetFromTorch('lib/openface.nn4.small2.v1.t7')
face_cascade = cv2.CascadeClassifier('lib/haarcascade_frontalface_default.xml')

# Our trained face recognition model
recognizer = pickle.loads(open('./recognizer.pickle', "rb").read())
labels = pickle.loads(open('./labels.pickle', "rb").read())

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
			name = False
			# if there is motion look for faces and save images
			if motion is True:
				for frame_obj in cls.motion_frames:
					for movement in frame_obj['motion_boxes']:
						(x, y, w, h) = cv2.boundingRect(movement)
						try:
							cv2.rectangle(frame_obj['frame'], (x, y), (x+w, y+h), (0, 255, 0), 2)
						except TypeError:
							log('DETECTOR', 'Error drawing rectangle, continuing')
						cv2.imwrite(SNAPSHOT_DIR+pretty_time()+'_motion.jpg', frame_obj['frame'])

				faces = cls.detect_faces()

				if len(faces) == 0:
					log('DETECTOR', 'No faces.')
				else:
					log('DETECTOR', 'Found ' + str(len(faces)) + ' faces.')
					for face in faces:
						if globals.OFFLINE_MODE:
							cv2.imshow('Face', face['frame'])
						name = Detector.recognize_face(face['frame'])
						if name is not None:
							try:
								cv2.putText(face['frame'], name, (0, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
							except TypeError:
								log('DETECTOR', 'Error drawing text, continuing')
							cv2.imwrite(SNAPSHOT_DIR+pretty_time()+'_face.jpg', face['frame'])
							break
						cv2.imwrite(SNAPSHOT_DIR+pretty_time()+'_face.jpg', face['frame'])

				cls.motion_frames = []

			if name is False:
				Notifier.unnotify()
			else:
				Notifier.notify(name)

	@classmethod
	def update_frame(cls, frame):
		Detector.frame = frame

	# Finds faces in a frame
	# Params: Frame to look for faces in, confidence threshold from 0 to 1 (optional)
	# Returns: An array of face objects if faces are found
	@classmethod
	def detect_faces(cls):
		log('DETECTOR', 'Detecting faces in the last '+str(MOTION_FRAMES_THRESHOLD)+' frames...')
		faces = []
		for frame_obj in cls.motion_frames:
			frame_copy = frame_obj['frame'].copy()
			frame_copy = imutils.resize(frame_copy, width=600)
			(h, w) = frame_copy.shape[:2]

			blob = cv2.dnn.blobFromImage(cv2.resize(frame_copy, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0), swapRB=False, crop=False)

			detector.setInput(blob)
			detections = detector.forward()

			for i in range(detections.shape[2]):

				confidence = detections[0, 0, i, 2]

				if confidence > FACE_DETECTION_PROBABILITY:
					box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
					(startX, startY, endX, endY) = box.astype("int")

					face = frame_copy[startY:endY, startX:endX]
					(fH, fW) = face.shape[:2]

					if fW > 20 and fH > 20:
						faces.append({'frame': face, 'startX': startX, 'startY': startY, 'endX': endX, 'endY': endY})
		return faces

	# Recognizes any known faces in a frame
	# Params: Cropped face frame, full video frame to write their name on
	# Returns: The name of the person found or None if we couldn't reliably identify them
	@staticmethod
	def recognize_face(face):
		log('DETECTOR', 'Attempting face recognition...')
		faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255, (96, 96), (0, 0, 0), swapRB=True, crop=False)
		embedder.setInput(faceBlob)
		vec = embedder.forward()

		preds = recognizer.predict_proba(vec)[0]
		j = np.argmax(preds)
		proba = preds[j]

		name = labels.classes_[j]
		text = "{}: {:.2f}%".format(name, proba * 100)
		log('DETECTOR', 'Recognized ' + text)

		if proba > FACE_RECOGNITION_PROBABILITY:
			return name
		else:
			return None

	# [Not used] inferior but faster method for face detection
	@staticmethod
	def detect_faces_cascade(frame):
		frame_copy = frame.copy()
		faces = face_cascade.detectMultiScale(frame_copy, 1.1, 4)

		for (x, y, w, h) in faces:
			cv2.rectangle(frame_copy, (x, y), (x+w, y+h), (0, 255, 0), 2)

		return frame_copy, faces

	# Blurs and grayscales a frame
	# Params: Frame
	@staticmethod
	def blur_and_gray(frame):
		output = imutils.resize(frame, width=500)
		output = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
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
	# Params: Frame
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
