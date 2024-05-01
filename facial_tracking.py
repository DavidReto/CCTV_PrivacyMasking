import cv2
import sys
import logging as log
import datetime as dt
from time import sleep
import numpy as np
import os
import math
import face_recognition

def face_confidence(face_distance, face_match_threshold=0.6):
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > face_match_threshold:
        return str(round(linear_val * 100, 2)) + '%'
    else:
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2)) + '%'

def run_recognition():
    cascPath = "haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascPath)
    log.basicConfig(filename='webcam.log',level=log.INFO)
    video_capture = cv2.VideoCapture(0)
    # key = np.random.randint(0, 256, size=999999, dtype=np.uint8)



    # def xor_encrypt_decrypt(image, key):
    #     image_np = np.array(image)
    #     key_np = np.array(key)
        
    #     key_np = np.resize(key_np, image_np.shape)
        
    #     result = np.bitwise_xor(image_np, key_np)
    #     return result

    if not video_capture.isOpened():
        print('Unable to load camera.')
        sleep(5)
        pass

    while True:
        ret, frame = video_capture.read(0)
        # Only process every other frame of video to save time
    
        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            confidence = '???'

            # Calculate the shortest distance to face
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                confidence = face_confidence(face_distances[best_match_index])

            face_names.append(f'{name} ({confidence})')

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Create the frame with the name
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)


        # Display the resulting frame
        cv2.imshow('Video', frame)


        if cv2.waitKey(1) == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


face_locations = []
face_encodings = []
face_names = []
known_face_encodings = []
known_face_names = []
process_current_frame = True

for image in os.listdir('faces'):
    face_image = face_recognition.load_image_file(f"faces/{image}")
    face_encoding = face_recognition.face_encodings(face_image)[0]

    known_face_encodings.append(face_encoding)
    known_face_names.append(image)
print(known_face_names)

run_recognition()




