import face_recognition
import sys
import os
import pickle
import numpy as np
import cv2

images_dir = './embeddings/input_images'

data = pickle.loads(open('./embeddings/encodings.pickle', "rb").read())
known_face_encodings = data['known_face_encodings']
known_face_names = data['known_face_names']

def detect_faces(image):
    name = "Unknown"
    frame = None
    location = None

    small_frame = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)

    face_locations = face_recognition.face_locations(small_frame)
    face_encodings = face_recognition.face_encodings(small_frame, face_locations)

    for i, face_encoding in enumerate(face_encodings):
      matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
      name = "Unknown"
      face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
      best_match_index = np.argmin(face_distances)

      location = face_locations[i]

      if matches[best_match_index]:
        name = known_face_names[best_match_index]
        # As soon as we have someone stop looking
        break

    (top * 2, right * 2, bottom * 2, left * 2) = location

    frame = image[top:bottom, left:right].copy()
    return name, frame, location

if len(sys.argv) > 0:
  if (len(sys.argv) > 1):
    image = face_recognition.load_image_file(sys.argv[1])
    name, frame, location = detect_faces(image)
    print(name)
    print(location)