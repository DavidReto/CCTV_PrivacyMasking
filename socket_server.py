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
import socket
import shutil
from time import sleep
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from numpy import asarray
from datetime import datetime
from natsort import os_sorted

def face_confidence(face_distance:float, face_match_threshold=0.6) -> str:
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > face_match_threshold:
        return str(round(linear_val * 100, 2)) + '%'
    else:
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2)) + '%'

def generate_video(images:list): 
    now = datetime.now()
    date_time: str = now.strftime("%H_%M_%S")
    monthVal: str  = now.strftime("%m")
    dayVal: str  = now.strftime("%m")
    #tempPath = f'C:\\Users\\david\\Documents\\GitProjects\\FYP\\footage\\{monthVal}\\tempframe' 
    vidPath = f'C:\\Users\\david\\Documents\\GitProjects\\FYP\\footage\\{monthVal}\\{dayVal}' # make sure to use your folder 
    video_name = f'footage_{date_time}.avi'
    os.chdir(vidPath) 
  
    frame =  np.array(images[0])
    frame = frame[:, :, ::-1].copy() 
  
    # setting the frame width, height width 
    # the width, height of first image 
    height, width, layers = frame.shape 
  
    video = cv2.VideoWriter(video_name, 0, 5, (width, height))  
  
    # Appending the images to the video one by one 
    for image in images: 
        image = np.array(image)
        image = image[:, :, ::-1].copy() 
        video.write(image)  
      
    # Deallocating memories taken for window creation 
    cv2.destroyAllWindows()  
    video.release()  # releasing the video generated 

def server_program():
    # get the hostname
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together
    # configure how many client the server can listen simultaneously
    server_socket.listen(1)
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))
    face_locations, face_encodings, blacklist_face_encodings, blacklist_face_names, record_face_encodings, record_face_names, images = ([] for i in range(7))
    pattern = re.compile(r"record_(\d+)\.png")
    counter_file: int = 0
    counter_temp_foot: int = 0
    now = datetime.now()
    monthVal: str = now.strftime("%m")
    dayVal: str = now.strftime("%d")
    current_path = os.getcwd()
    for month in os.listdir('faces'):
        if month == monthVal:
            for day in os.listdir(f'faces/{month}'):
                if day == dayVal:
                    for image in os.listdir(f"faces/{month}/{day}"):
                        face_image = face_recognition.load_image_file(f"faces/{month}/{day}/{image}")
                        try:
                            face_encoding = face_recognition.face_encodings(face_image)[0]
                            match = pattern.match(image)
                            if match:
                                counter_file += 1
                                record_face_encodings.append(face_encoding)
                                record_face_names.append(image)
                        except:
                            print("The Image either does't contain a face or the code can't identify one")
        elif month == 'blacklist':  
            for image in os.listdir(f"faces/{month}"):   
                face_image = face_recognition.load_image_file(f"faces/{month}/{image}")  
                try:
                    face_encoding = face_recognition.face_encodings(face_image)[0]
                    blacklist_face_encodings.append(face_encoding)
                    blacklist_face_names.append(image)
                except:
                    print("The Image either does't contain a face or the code can't identify one")                            
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        now = datetime.now()
        preciseTime = now.strftime("%d-%H_%M_%S_")
        monthVal = now.strftime("%m")
        dayVal = now.strftime("%d")
        data = conn.recv(2097152)
        if not data:
            # if data is not received break
            break
        #Server would start here 
        testlist = data.split('/_/@/_'.encode('utf8'))
        timestamp = testlist.pop(-1)
        frame_height = int(testlist.pop(-1).decode('utf8'))
        frame_width = int(testlist.pop(-1).decode('utf8'))
        image = b''.join(testlist)
        try:
            TimeFrame = Image.frombytes("RGB", (frame_width,frame_height), image)
        except:
            conn.send("This object doesn't seem to be an image and was blocked for security reasons".encode())
            continue

        frameServer = np.array(TimeFrame)
        frameServer.setflags(write=1)

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(frameServer)
        face_encodings = face_recognition.face_encodings(frameServer, face_locations)

        face_names: list = []
        face_keys: list = []
        face_ivs: list = []
        i: int = 0   
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            blacklist = face_recognition.compare_faces(blacklist_face_encodings, face_encoding)
            record = face_recognition.compare_faces(record_face_encodings, face_encoding)
            name: str = "Unknown"
            confidence: str = '???'

            # Calculate the shortest distance to Blacklist face
            blacklist_face_distances = face_recognition.face_distance(blacklist_face_encodings, face_encoding)
            # Calculate the best match index for Blacklist faces
            blacklist_BMI = np.argmin(blacklist_face_distances)

            # Calculate the shortest distance to record face
            record_face_distances = face_recognition.face_distance(record_face_encodings, face_encoding)
            # Calculate the best match index for record faces
            record_BMI = np.argmin(record_face_distances)

            if blacklist[blacklist_BMI]:
                name = blacklist_face_names[blacklist_BMI]
                confidence = face_confidence(blacklist_face_distances[blacklist_BMI])
                face_names.append(f'{name} ({confidence})')
                face_keys.append(b'')
                face_ivs.append(b'')
            elif record[record_BMI]:
                '''this is where we will check for people who already exist but aren't blacklisted'''
                #I have to get the image name and
                with open(f"faces/{monthVal}/{dayVal}/record_{record_BMI + 1}.png", "rb") as f:
                    for chunk in iter(lambda: f.read(), b''):
                        testlist = chunk.split(b'/_/@/_')
                    key = testlist[-2]
                    iv = testlist[-1]
                face_names.append(f'{name} ({confidence})')
                face_keys.append(key)
                face_ivs.append(iv)
            else:
                '''this is where we will generate a new key for each person in case they don't exist yet'''
                image = Image.fromarray(frameServer)
                box = face_locations[i]
                image = image.crop((box[0], box[3]-box[3]* 40/100, box[2]+box[2]* 5/100, box[1]))     
                key = get_random_bytes(16) 
                iv = get_random_bytes(16) 
                keyform = '/_/@/_'.encode('utf8') + key + '/_/@/_'.encode('utf8') + iv
                counter_file += 1
                image.save(f"faces/{monthVal}/{dayVal}/record_{counter_file}.png") 
                with open(f"faces/{monthVal}/{dayVal}/record_{counter_file}.png", "ab") as f: 
                    f.write(keyform)
                face_names.append(f'{name} ({confidence})')
                face_keys.append(key)
                face_ivs.append(iv)
            i += 1

        # Display the results
        block_size: int = 16
        extrabyte: int = 0
        keyfacedata: str = ''
        for (top, right, bottom, left), name, key, iv in zip(face_locations, face_names, face_keys, face_ivs):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            #top *= 4
            #right *= 4
            #bottom *= 4
            #left *= 4
            if name == 'Unknown (???)':
                #Saves the the locations of the faces in a string as top bottom left right, as well as the keys and iv for each one
                keyfacedata += str(top) +'.'+ str(bottom) +'.'+ str(left) +'.'+ str(right) + '|' + str(key) + '|' + str(iv) + '\_/'
                cipher = AES.new(key, AES.MODE_CFB, iv)
                image_data = frameServer[top:bottom, left:right]
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
                frameServer[top:bottom, left:right] = img
            else:
                cv2.rectangle(frameServer, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frameServer, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                cv2.putText(frameServer, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
        footageFrame = Image.fromarray(frameServer)
        images.append(footageFrame)
        #footageFrame.save(f"footage/{monthVal}/tempframe/temp_foot_{counter_temp_foot}.png")
        counter_temp_foot += 1
        frameServer.tobytes()
        conn.send(frameServer)  # send data to the client
        anexInfo = preciseTime + '|' + keyfacedata
        file = open(f'C:\\Users\\david\\Documents\\GitProjects\\FYP\\KDInfo\\{monthVal}\\{dayVal}\\tempInfo.txt', 'a')
        file.write(anexInfo + "\n")
        file.close() 
    conn.close()  # close the connection
    generate_video(images)
    

#TODO add a check in case the video records the transition from one month to the next so that they get recorded in both
#TODO when coding the part to check if the face is recognised add a functionaliity so that depending on whether the cops have a month, a day or an hour we can scope it down by checking if the file format containts day and hour and if it does only check files with the same hour in the folder for that day, this way it's faster to check
if __name__ == '__main__':
    server_program()