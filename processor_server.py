import cv2
import datetime as dt
import numpy as np
import shutil
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

def face_confidence(face_distance:float, face_match_threshold=0.6) -> str:
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)

    if face_distance > face_match_threshold:
        return str(round(linear_val * 100, 2)) + '%'
    else:
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2)) + '%'

def generate_video(images:list, now, key,iv,face_locations1): 
    date_time: str = now.strftime("%H_%M_%S")
    monthVal: str  = now.strftime("%m")
    dayVal: str  = now.strftime("%d")
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
    counter =0
    for image in images: 
        top = face_locations1[counter][0][0]
        right = face_locations1[counter][0][1]
        bottom = face_locations1[counter][0][2]
        left = face_locations1[counter][0][3]
        image = np.array(image)
        print(type(image))
        image_data = image[top:bottom, left:right]
        image_data = image_data.tobytes()
        decrypt_cipher = AES.new(key, AES.MODE_CFB, iv)
        decryptImage = decrypt_cipher.decrypt(image_data)
        img = Image.frombytes("RGB", (right-left,bottom-top), decryptImage)
        image[top:bottom, left:right] = img
        image1 = image[:, :, ::-1].copy() 
        video.write(image1) 
        counter +=1 
    # Deallocating memories taken for window creation 
    cv2.destroyAllWindows()  
    video.release() 

def server_program():
    # get the hostname
    keys=[]
    ivs=[]
    locations=[]
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # get instance
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together
    # configure how many client the server can listen simultaneously
    server_socket.listen(1)
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))
    face_locations, face_encodings, blacklist_face_encodings, blacklist_face_names, record_face_encodings, images = ([] for i in range(6))
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
    face_locations1 = []                      
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        now = datetime.now()
        preciseTime = now.strftime("%H_%M_%S_")
        monthVal = now.strftime("%m")
        dayVal = now.strftime("%d")
        data = conn.recv(2097152)
        if not data:
            # if data is not received break
            break
        #Server would start here 
        testlist = data.split('/_/@/_'.encode('utf-8'))
        timestamp = testlist.pop(-1)
        frame_height = int(testlist.pop(-1).decode('utf-8'))
        frame_width = int(testlist.pop(-1).decode('utf-8'))
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
        face_id: list = []
        i: int = 0   
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            blacklist = face_recognition.compare_faces(blacklist_face_encodings, face_encoding,tolerance=0.7)
            record = face_recognition.compare_faces(record_face_encodings, face_encoding,tolerance=0.7)
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
                height = box[2]-box[0]
                width = box[1]-box[3]
                #takes location values from (LEFT,TOP,RIGHT,BOTTOM)
                image = image.crop((box[3] -(width* 25/100), box[0]-(height* 25/100) , box[1]+(width* 25/100) , box[2]+(height* 25/100))) 
                key = get_random_bytes(16) 
                iv = get_random_bytes(16) 
                keyform = '/_/@/_'.encode('utf-8') + key + '/_/@/_'.encode('utf-8') + iv
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
        keyfacedata: bytes = b''
        for (top, right, bottom, left), name, key, iv in zip(face_locations, face_names, face_keys, face_ivs):
            if name == 'Unknown (???)':
                face_locations1.append(face_locations)
                #Saves the the locations of the faces in a string as top bottom left right, as well as the keys and iv for each one
                keyfacedata += (str(top) +'.'+ str(bottom) +'.'+ str(left) +'.'+ str(right)).encode('utf-8') + '|'.encode('utf-8') + key + '|'.encode('utf-8') + iv + '\_/'.encode('utf-8')
                cipher = AES.new(key, AES.MODE_CFB)
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
        counter_temp_foot += 1
        frameServer.tobytes()
        conn.send(frameServer)  # send data to the client
        anexInfo = preciseTime.encode('utf-8') + '@'.encode('utf-8') + keyfacedata
        file = open(f'C:\\Users\\david\\Documents\\GitProjects\\FYP\\KDInfo\\{monthVal}\\{dayVal}\\tempInfo.txt', 'ab')
        file.write(anexInfo + b"\n") 
        file.close() 
    conn.close()  # close the connection
    now = datetime.now()
    date_time: str = now.strftime("%H_%M_%S")
    source_file =  open(f'C:\\Users\\david\\Documents\\GitProjects\\FYP\\KDInfo\\{monthVal}\\{dayVal}\\tempInfo.txt', 'rb')
    destination_file = open(f'C:\\Users\\david\\Documents\\GitProjects\\FYP\\KDInfo\\{monthVal}\\{dayVal}\\KDInfo_{date_time}.txt', 'wb')
    shutil.copyfileobj(source_file, destination_file)
    source_file.close()
    destination_file.close()
    os.remove(f'C:\\Users\\david\\Documents\\GitProjects\\FYP\\KDInfo\\{monthVal}\\{dayVal}\\tempInfo.txt')
    generate_video(images ,now, key , iv , face_locations1)
    

#TODO add a check in case the video records the transition from one month to the next so that they get recorded in both
#TODO make it so that the naming convention for the blacklisted faces is "PersonName_DateTheyWereBlacklisted"
if __name__ == '__main__':
    server_program()