#!/usr/bin/env python2

## Trains the model with the gubbins spat forth from register_face.py (run that first)

from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
import sys
import os
import cv2
import pickle
import numpy as np
import imutils

detector = cv2.dnn.readNetFromTensorflow("lib/opencv_face_detector_uint8.pb", "lib/opencv_face_detector.pbtxt")
embedder = cv2.dnn.readNetFromTorch('lib/openface.nn4.small2.v1.t7')

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

def recognize_face(face, recognizer, labels):
	name = None
	faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255, (96, 96), (0, 0, 0), swapRB=True, crop=False)
	embedder.setInput(faceBlob)
	vec = embedder.forward()

	preds = recognizer.predict_proba(vec)[0]
	j = np.argmax(preds)
	proba = preds[j]

	name = None
	text = None

	name = labels.classes_[j]

	return name, proba


def TrainModel(test=False):
	
	recognizer = SVC(C=1.0, kernel="linear", probability=True)

	embeddings = []
	names = []

	for dirpath, dirnames, files in os.walk('./embeddings'):
		for embedding in files:
			data = pickle.loads(open('./embeddings/'+embedding, "rb").read())
			embeddings += data['embeddings']
			names += data['names']
		break

	print("Loading face embeddings...")

	le = LabelEncoder()
	labels_encoded = le.fit_transform(names)

	print("Training model...")
	recognizer.fit(embeddings, labels_encoded)

	if test is not False:
		print("Cool. Testing it...")

		test_results = {}

		unique_names = set(data['names'])
		unique_names = list(unique_names)

		for name in unique_names:
			print('Testing: ' + name)
			if name not in test_results.keys():
				test_results[name] = {'success': 0, 'fail': 0}

			recognized_name = None
			images = './embeddings/input_images/'+name

			for dirpath, dirnames, files in os.walk(images):
				for imagefile in files:
					image = cv2.imread(images+"/"+imagefile)
					face = detect_faces(image)

					if face is None:
						print("Found no faces in " + imagefile)
						continue
					
					recognized_name, proba = recognize_face(face, recognizer, le)
					text = "{}: {:.2f}%".format(recognized_name, proba * 100)
					print(text)

					if recognized_name is not None and recognized_name == name and proba > 0.6:
						test_results[name]['success'] += 1
					else:
						test_results[name]['fail'] += 1
		print(test_results)
	
	print('Done training, writing to disk...')
	f = open('./recognizer.pickle', "wb")
	f.write(pickle.dumps(recognizer))
	f.close()

	f = open('./labels.pickle', "wb")
	f.write(pickle.dumps(le))
	f.close()

if len(sys.argv) > 1:
	TrainModel()