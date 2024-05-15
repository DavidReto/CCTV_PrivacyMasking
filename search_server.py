import cv2
import datetime as dt
import numpy as np
import os
import math
import face_recognition
import re
import socket
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from numpy import asarray
from datetime import datetime

def checkstartformat(startdate:str):
    if "." in startdate:
        startbreakformat = "."
    elif "-" in startdate:
        startbreakformat = "-"
    elif "/" in startdate:
        startbreakformat = "/"
    return startbreakformat
def checkendformat(enddate:str):
    if "." in enddate:
        endbreakformat = "."
    elif "-" in enddate:
        endbreakformat = "-"
    elif "/" in enddate:
        endbreakformat = "/"
    return endbreakformat
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
    data = conn.recv(2097152) 
    testlist:list = data.split('/_/@/_'.encode('utf-8'))
    enddate:str = testlist.pop(-1).decode('utf-8')
    startdate:str = testlist.pop(-1).decode('utf-8')
    frame_height:int = int(testlist.pop(-1).decode('utf-8'))
    frame_width:int = int(testlist.pop(-1).decode('utf-8'))
    image = b''.join(testlist)
    try:
        Frame = Image.frombytes("RGB", (frame_width,frame_height), image)
    except:
        conn.send("Something went wrong, it appears that the data you sent isn't an image.".encode())
    frameServer = np.array(Frame)
    frameServer.setflags(write=1)
    try:
        sample_face_encoding = face_recognition.face_encodings(frameServer)[0]
    except:
        conn.send("Our Program can't seem to detect a face in the image you provided, please provide a more clear sample".encode())

    liststart:list = startdate.split(checkstartformat(startdate))
    listend:list = enddate.split(checkendformat(enddate))
    startday:int = int(liststart[0])
    startmonth:int = int(liststart[1])
    endday:int = int(listend[0])
    endmonth:int = int(listend[1])
    monthdictID:dict = {}
    framecount = 0
    for month in os.listdir('faces'):
        daydictID:dict = {}
        try:
            if (int(month) >= startmonth and int(month) <= endmonth): 
                if month == 'blacklist':
                    ...
                elif startmonth == endmonth:
                    for day in os.listdir(f'faces/{month}'):
                        if int(day) >= startday and int(day) <= endday:
                            for image in os.listdir(f"faces/{month}/{day}"):
                                matches = []
                                matches.append(False)
                                face_image = face_recognition.load_image_file(f"faces/{month}/{day}/{image}")
                                try:
                                    saved_face_encoding = face_recognition.face_encodings(face_image)[0]
                                    ls_face_encodings=[]
                                    ls_face_encodings.append(saved_face_encoding)
                                    matches = face_recognition.compare_faces(ls_face_encodings, sample_face_encoding,tolerance=0.7)
                                except:
                                    print("The Image either does't contain a face or the code can't identify one") 
                                if matches[0]== True:
                                    daydictID[image[7:-4]] = day                           
                else:
                    if int(month) == startmonth:
                        for day in os.listdir(f'faces/{month}'):
                            if int(day) >= startday:
                                for image in os.listdir(f"faces/{month}/{day}"):
                                    matches = []
                                    matches.append(False)
                                    face_image = face_recognition.load_image_file(f"faces/{month}/{day}/{image}")
                                    try:
                                        saved_face_encoding = face_recognition.face_encodings(face_image)[0]
                                        ls_face_encodings=[]
                                        ls_face_encodings.append(saved_face_encoding)
                                        matches = face_recognition.compare_faces(ls_face_encodings, sample_face_encoding,tolerance=0.5)
                                    except:
                                        print("The Image either does't contain a face or the code can't identify one") 
                                    if matches[0]== True:
                                        daydictID[image[7:-4]] = day
                    elif int(month) == endmonth:
                        for day in os.listdir(f'faces/{month}'):
                            if int(day) <= endday:
                                for image in os.listdir(f"faces/{month}/{day}"):
                                    matches = []
                                    matches.append(False)
                                    face_image = face_recognition.load_image_file(f"faces/{month}/{day}/{image}")
                                    try:
                                        saved_face_encoding = face_recognition.face_encodings(face_image)[0]
                                        ls_face_encodings=[]
                                        ls_face_encodings.append(saved_face_encoding)
                                        matches = face_recognition.compare_faces(ls_face_encodings, sample_face_encoding,tolerance=0.5)
                                    except:
                                        print("The Image either does't contain a face or the code can't identify one") 
                                    if matches[0]== True:
                                        daydictID[image[7:-4]] = day
                    else:
                        for day in os.listdir(f'faces/{month}'):
                            for image in os.listdir(f"faces/{month}/{day}"):
                                matches = []
                                matches.append(False)
                                face_image = face_recognition.load_image_file(f"faces/{month}/{day}/{image}")
                                try:
                                    saved_face_encoding = face_recognition.face_encodings(face_image)[0]
                                    ls_face_encodings=[]
                                    ls_face_encodings.append(saved_face_encoding)
                                    matches = face_recognition.compare_faces(ls_face_encodings, sample_face_encoding,tolerance=0.5)
                                except:
                                    print("The Image either does't contain a face or the code can't identify one") 
                                if matches[0] == True:
                                    daydictID[image[7:-4]] = day
            monthdictID[month] = daydictID
        except:
           ...
    #Here we start to retrieve the keys from the log files so we can then apply them on the videos
    permonthdict:dict = {}
    for month in os.listdir('KDInfo'):
        try:
            if monthdictID[month]: 
                daycount:int = 1
                perdaydict: dict = {}
                for day in os.listdir(f'KDInfo/{month}'):
                    pervideodict: dict = {}
                    day in monthdictID[month].values()
                    if day in monthdictID[month].values():
                        for file in os.listdir(f"KDInfo/{month}/{day}"):
                            f = open(f"KDInfo/{month}/{day}/{file}", "rb")
                            logname = file.replace('KDInfo', 'footage')
                            logname = logname.replace('txt', 'avi')
                            lines = f.readlines()
                            perframedict: dict = {}
                            framecount: int = 1
                            for line in lines:
                                try:
                                    lineData = line.split(b"@")
                                    faces = lineData[1].split(b"\_/")
                                    del faces[-1]
                                    perfacedict: dict = {}
                                    facecount: int = 1
                                    for data in faces:
                                        infodata = data.split(b"|")
                                        perfacedict[facecount] = {
                                                            "key": infodata[1],
                                                            "iv": infodata[2],
                                                            "location": infodata[0]
                                                    }
                                        facecount += 1
                                except:
                                    perfacedict[0] = {}
                                perframedict[framecount] = perfacedict
                                framecount +=1
                            pervideodict[logname] = perframedict
                    perdaydict[daycount] = pervideodict
                    daycount += 1
            else:
                perfacedict: dict = {}
                perframedict: dict = {}
                pervideodict: dict = {}
                perdaydict:dict = {}
                perfacedict[f'frame_1'] = {
                                    "key": "",
                                    "iv": "",
                                    "location": ""
                            }
                perframedict[0] = perfacedict
                pervideodict[0] = perframedict
                perdaydict[0] = pervideodict
        except:
            perfacedict: dict = {}
            perfacedict[f'frame_1'] = {
                                    "key": "",
                                    "iv": "",
                                    "location": ""
                            }
            perframedict[0] = perfacedict
            pervideodict[0] = perframedict
            perdaydict[0] = pervideodict
        permonthdict[month] = perdaydict
    for month in os.listdir('footage'):
        if monthdictID[month]: 
            for day in os.listdir(f'footage/{month}'):
                if day in monthdictID[month].values():
                    for file in os.listdir(f"footage/{month}/{day}"):
                        videodic = permonthdict[month][int(day)][file]
                        vidcap = cv2.VideoCapture(f"footage/{month}/{day}/{file}")
                        success,imageframe = vidcap.read()
                        print(type(imageframe))
                        count = 0
                        while success:
                            framedict: dict =  videodic[count+1]
                            check = framedict.get(1, False)
                            if check :
                                for x in framedict:
                                    dimensons:str =  framedict[x]['location'].decode('utf-8')
                                    loclist: list = dimensons.split(".")
                                    top: int = int(loclist[0])
                                    bottom: int = int(loclist[1])
                                    left: int = int(loclist[2])
                                    right: int = int(loclist[3])
                                    key:bytes = framedict[x]['key']
                                    iv:bytes = framedict[x]['iv']
                                    image_data = imageframe[top:bottom, left:right]
                                    cv2.imwrite("face_before_%d.jpg" % count, image_data)
                                    image_data = image_data.tobytes()
                                    decrypt_cipher = AES.new(key, AES.MODE_CFB, iv)
                                    decryptImage = decrypt_cipher.decrypt(image_data)
                                    img = Image.frombytes("RGB", (right-left,bottom-top), decryptImage)
                                    img = np.array(img)
                                    cv2.imwrite("face_after_%d.jpg" % count, img)
                                    imageframe[top:bottom, left:right] = img
                            cv2.imwrite("frame%d.jpg" % count, imageframe)     # save frame as JPEG file      
                            success,imageframe = vidcap.read()
                            count += 1
                        
        

            

if __name__ == '__main__':
    server_program()