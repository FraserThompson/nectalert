#!/usr/bin/env python3
import face_recognition
import sys
import os
import pickle
import numpy as np
import cv2

images_dir = './embeddings/input_images'

def register_face(names):

  known_face_encodings = []
  known_face_names = []

  for name in names:
    for dirpath, dirnames, files in os.walk(images_dir + '/' + name):
      for filename in files:
        print('Processing ' + filename + ' of ' + name)
        image = face_recognition.load_image_file(images_dir+'/'+name+'/'+filename)
        face_encoding = face_recognition.face_encodings(image)
        if face_encoding:
          print("Found a face")
          known_face_encodings.append(face_encoding[0])
          known_face_names.append(name)
  
  print("Chur, dumping "+str(len(known_face_encodings))+" faces to disk...")
  f = open('./embeddings/encodings.pickle', "wb")
  f.write(pickle.dumps({'known_face_encodings': known_face_encodings, 'known_face_names': known_face_names}))
  f.close()

if len(sys.argv) > 0:
    register_face(sys.argv[1:])