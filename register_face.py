#!/usr/bin/env python3

## Generations recognization data for one single face by taking five images of it.
## Then it needs to be fed into train_model.py to train the model.

import uuid
import numpy as np
import imutils
import time
import pickle
import freenect
import cv2
import frame_convert2
import os
import sys

detector = cv2.dnn.readNetFromTensorflow("lib/opencv_face_detector_uint8.pb", "lib/opencv_face_detector.pbtxt")
embedder = cv2.dnn.readNetFromTorch('lib/openface.nn4.small2.v1.t7')
images_dir = './embeddings/input_images'

class RegisterFace:
	@staticmethod
	def get_video():
		return frame_convert2.video_cv(freenect.sync_get_video()[0])

	@staticmethod
	def detect_faces(frame):
		return_face = None

		frame_copy = frame.copy()
		frame_copy = imutils.resize(frame_copy, width=600)
		(h, w) = frame_copy.shape[:2]

		blob = cv2.dnn.blobFromImage(cv2.resize(frame_copy, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0), swapRB=False, crop=False)

		detector.setInput(blob)
		detections = detector.forward()

		for i in range(detections.shape[2]):
			confidence = detections[0, 0, i, 2]
			if confidence > 0.7:
				box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
				(startX, startY, endX, endY) = box.astype("int")

				face = frame_copy[startY:endY, startX:endX]
				(fH, fW) = face.shape[:2]

				if fW > 20 and fH > 20:
					return_face = face
		
		return return_face

	@staticmethod
	def generate_embeddings(face):
		print("Reticulating splines...")
		faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255, (96, 96), (0, 0, 0), swapRB=True, crop=False)
		embedder.setInput(faceBlob)
		vec = embedder.forward()
		return vec.flatten()

	@staticmethod
	def take_a_photo(path):
		video_frame = RegisterFace.get_video()
		face_frame = RegisterFace.detect_faces(video_frame)
		if face_frame is not None:
			cv2.imwrite(path + '/' + str(uuid.uuid4()) + '.jpg', face_frame)

	@staticmethod
	def process_images(name):
		knownEmbeddings = []
		knownLabels = []
		for dirpath, dirnames, files in os.walk(images_dir + '/' + name):
			for image in files:
				print('Processing ' + image + ' of ' + name)
				thing = cv2.imread(images_dir+'/'+name+'/'+image)
				thing = imutils.resize(thing, width=600)
				face = RegisterFace.detect_faces(thing)
				if face is not None:
					embeddings = RegisterFace.generate_embeddings(face)
					knownLabels.append(name)
					knownEmbeddings.append(embeddings)
			break
		print("Chur, dumping "+str(len(knownEmbeddings))+" embeddings to disk...")
		f = open('./embeddings/'+name+'.pickle', "wb")
		f.write(pickle.dumps({'embeddings': knownEmbeddings, 'names': knownLabels}))
		f.close()

	def __init__(self, photos_to_take=0, name=None):
		if name is not None and photos_to_take > 0:
			print('Taking '+str(photos_to_take)+' photos of '+name)
			os.system('aplay /home/pi/nectalert/sounds/beep.wav')
			for i in range(0, photos_to_take):
				print('Strike a pose for photo ' + str(i))
				time.sleep(1)
				RegisterFace.take_a_photo(images_dir + '/' + name)
			os.system('aplay /home/pi/nectalert/sounds/beep.wav')
		print('Processing faces...')
		if name is None:
			for dirpath, dirnames, files in os.walk(images_dir):
				for dirname in dirnames:
					RegisterFace.process_images(dirname)
		else:
			RegisterFace.process_images(name)
		print("Done! You should run train_model.py now.")

if len(sys.argv) > 1:
	RegisterFace(name=sys.argv[1])