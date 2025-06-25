import cv2
import sys
import logging as log
import datetime as dt
import numpy as np
import os
import math
import face_recognition
import threading
import re
from time import sleep
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from numpy import asarray
from datetime import datetime

# Calculates a confidence score for face recognition matches
# Returns a string percentage based on the face distance and threshold
def face_confidence(face_distance:float, face_match_threshold=0.6) -> str:
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > face_match_threshold:
        return str(round(linear_val * 100, 2)) + '%'
    else:
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2)) + '%'

# Thread function: Continuously captures frames and extracts face encodings
# Uses barriers to synchronize with other threads
def run_recognition() -> None:
    while True:
        global ret, frame, face_encodings, face_locations, rgb_small_frame
        ret, frame = video_capture.read(0)  
        # Resize frame of video to 1/4 size for faster face recognition processing (commented out)
        #small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        # Convert the image from BGR color (OpenCV) to RGB (face_recognition)
        rgb_small_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Apply steganography to embed timestamp in the image
        bytes_rgb_small_frame =  rgb_small_frame.tobytes() + byte_date_time
        # Get current date and time
        now = datetime.now()
        date_time = now.strftime("%d_%m_%Y_%H:%M:%S.%f")
        byte_date_time = '/_/@/_'.encode('utf8') + date_time.encode('utf8')  
        TimeFrame = Image.frombytes("RGB", (rgb_small_frame.shape[1],rgb_small_frame.shape[0]), bytes_rgb_small_frame)
        # Detect faces and compute encodings
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        print('barrier 1:run recon')
        barrier1.wait()
        print('barrier 3:run recon')
        barrier3.wait() 

# Thread function: Matches detected faces to known faces, manages keys/IVs, and updates records
def matches() -> None:
    global face_names ,face_keys ,face_ivs ,counter_file, face_encodings
    while True: 
        face_names= []
        face_keys = []
        face_ivs = []
        i: int = 0   
        print('barrier 1:match')
        barrier1.wait()
        for face_encoding in face_encodings:
            # Compare with blacklist and record encodings
            blacklist = face_recognition.compare_faces(blacklist_face_encodings, face_encoding)
            record = face_recognition.compare_faces(record_face_encodings, face_encoding)
            name: str = "Unknown"
            confidence: str = '???'
            # Calculate distances and best match indices
            blacklist_face_distances = face_recognition.face_distance(blacklist_face_encodings, face_encoding)
            blacklist_BMI = np.argmin(blacklist_face_distances)
            record_face_distances = face_recognition.face_distance(record_face_encodings, face_encoding)
            record_BMI = np.argmin(record_face_distances)
            if blacklist[blacklist_BMI]:
                # If face is blacklisted, append info
                name = blacklist_face_names[blacklist_BMI]
                confidence = face_confidence(blacklist_face_distances[blacklist_BMI])
                face_names.append(f'{name} ({confidence})')
                face_keys.append(b'')
                face_ivs.append(b'')
            elif record[record_BMI]:
                # If face is in record, retrieve key/iv from file
                with open(f"faces/record/record_{counter_file}.png", "rb") as f:
                    for chunk in iter(lambda: f.read(), b''):
                        chunklist = chunk.split(b'/_/@/_')
                    key = chunklist[-2]
                    iv = chunklist[-1]
                face_names.append(f'{name} ({confidence})')
                face_keys.append(key)
                face_ivs.append(iv)
            else:
                # New face: generate key/iv, crop, and save
                image = Image.fromarray(rgb_small_frame)
                box = face_locations[i]
                height = box[2]-box[0]
                width = box[1]-box[3]
                # Crop with padding
                image = image.crop((box[3] -(width* 25/100), box[0]-(height* 25/100) , box[1]+(width* 25/100) , box[2]+(height* 25/100)))     
                key = get_random_bytes(16) 
                iv = get_random_bytes(16) 
                keyform = '/_/@/_'.encode('utf8') + key + '/_/@/_'.encode('utf8') + iv
                counter_file += 1
                image.save(f"faces/record/record_{counter_file}.png") 
                with open(f"faces/record/record_{counter_file}.png", "ab") as f: 
                    f.write(keyform)
                face_names.append(f'{name} ({confidence})')
                face_keys.append(key)
                face_ivs.append(iv)
            i += 1
        print('barrier 2:matches')
        barrier2.wait()
        print('barrier 3:matches')
        barrier3.wait() 

# Thread function: Displays the video with overlays and encrypted faces
def display() -> None:
    while True:
        print('barrier 2:display')
        barrier2.wait() 
        # Display the results
        block_size = 16
        extrabyte = 0
        for (top, right, bottom, left), name, key, iv in zip(face_locations, face_names, face_keys, face_ivs):
            # If face is unknown, encrypt the region
            if name == 'Unknown (???)':
                cipher = AES.new(key, AES.MODE_CFB, iv)
                image_data = frame[top:bottom, left:right]
                image_data = image_data.tobytes()  
                remainder = len(image_data) % block_size
                if remainder:
                    image_data += b' ' * (block_size - remainder)
                    extrabyte = (block_size - remainder)
                    extrabyte = -abs(extrabyte)
                encrypted_image_data = cipher.encrypt(image_data)
                if extrabyte:
                    encrypted_image_data = encrypted_image_data[:extrabyte]
                img = Image.frombytes("RGB", (right-left,bottom-top), encrypted_image_data)
                frame[top:bottom, left:right] = img
            else:
                # Draw rectangle and label for known faces
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
        # Show the resulting frame
        cv2.imshow('Video', frame)
        cv2.waitKey(5)
        print('barrier 3:display')
        print('------------------------------------------------------')
        barrier3.wait()

# Thread and barrier setup for parallel face recognition, matching, and display
t0 = threading.Thread(target=run_recognition)
t1 = threading.Thread(target=matches)
t2 = threading.Thread(target=display)
barrier1 = threading.Barrier(2)
barrier2 = threading.Barrier(2)
barrier3 = threading.Barrier(3)

# Load face detection model and set up logging
cascPath: str = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascPath)
log.basicConfig(filename='webcam.log',level=log.INFO)
video_capture = cv2.VideoCapture(0,cv2.CAP_DSHOW)
# key = np.random.randint(0, 256, size=999999, dtype=np.uint8)

global face_locations, face_encodings, blacklist_face_encodings, blacklist_face_names, record_face_encodings, record_face_names
face_locations, face_encodings, blacklist_face_encodings, blacklist_face_names, record_face_encodings, record_face_names = ([] for i in range(6))
process_current_frame: bool = True
pattern = re.compile(r"record_(\d+)\.png")
global counter_file
counter_file = 0
# Load known faces from folders and initialize counters
for folder in os.listdir('faces'):
    for image in os.listdir(f"faces/{folder}"):
        face_image = face_recognition.load_image_file(f"faces/{folder}/{image}")
        try:
            face_encoding = face_recognition.face_encodings(face_image)[0]
        except:
            print("The Image either does't contain a face or the code can't identify one")
        if folder == 'blacklist':
            blacklist_face_encodings.append(face_encoding)
            blacklist_face_names.append(image)
        elif folder =='record':
            match = pattern.match(image)
            if match:
                counter_file += 1
            record_face_encodings.append(face_encoding)
            record_face_names.append(image)
# Start threads for recognition, matching, and display
t0.start()
if not video_capture.isOpened():
    print('Unable to load camera.')
    sleep(5)
    pass
t1.start()
t2.start()

# Main loop: waits for 'q' key to exit and release resources
while True:
    if cv2.waitKey(1) == ord('q'):
        video_capture.release()
        cv2.destroyAllWindows()






