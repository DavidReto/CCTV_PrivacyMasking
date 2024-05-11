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
from time import sleep
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from numpy import asarray
from datetime import datetime

def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number
    cascPath = "haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascPath)
    log.basicConfig(filename='webcam.log',level=log.INFO)
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print('Unable to load camera.')
        sleep(5)
        pass
    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    while True:
        ret, frame = video_capture.read(0)

        # Resize frame of video to 1/4 size for faster face recognition processing
        #small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_small_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
        # datetime object containing current date and time
        now = datetime.now()
        date_time = now.strftime("%d_%m_%Y_%H:%M:%S.%f")
        anexData = '/_/@/_'.encode('utf8') + str(rgb_small_frame.shape[1]).encode('utf8')  +'/_/@/_'.encode('utf8') + str(rgb_small_frame.shape[0]).encode('utf8') +'/_/@/_'.encode('utf8') + date_time.encode('utf8')  
        bytes_rgb_small_frame =  rgb_small_frame.tobytes()
        bytes_rgb_small_frame = bytes_rgb_small_frame + anexData

        client_socket.send(bytes_rgb_small_frame)  # send message
        response = client_socket.recv(2097152)  # receive response
        try:
            frameResult = Image.frombytes("RGB", (rgb_small_frame.shape[1],rgb_small_frame.shape[0]), response)
        except:
            print(response.decode())
            continue
        frameResult = np.array(frameResult)
        frameResult = cv2.cvtColor(frameResult, cv2.COLOR_BGR2RGB)
        
        cv2.imshow('Video', frameResult)
        if cv2.waitKey(1) == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()