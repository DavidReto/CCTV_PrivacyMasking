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

# Generates a video from a list of images and saves them to disk
def generate_video(images:list, now): 
    date_time: str = now.strftime("%H_%M_%S")
    monthVal: str  = now.strftime("%m")
    dayVal: str  = now.strftime("%d")
    # Set up the path for saving video frames
    vidPath = f'C:\\Users\\david\\Documents\\GitProjects\\CCTV_PrivacyMasking\\footage\\{monthVal}\\{dayVal}' # make sure to use your folder 
    video_name = f'footage_{date_time}'
    os.chdir(vidPath) 
    os.mkdir(f'C:\\Users\\david\\Documents\\GitProjects\\CCTV_PrivacyMasking\\footage\\{monthVal}\\{dayVal}\\{video_name}')
    counter = 1
    # Save each image as a PNG in the video folder
    for image in images: 
        image = np.array(image)
        image = image[:, :, ::-1].copy() 
        image = Image.fromarray(image)
        image.save(f"C:\\Users\\david\\Documents\\GitProjects\\CCTV_PrivacyMasking\\footage\\{monthVal}\\{dayVal}\\{video_name}\\{counter}.png")
        counter += 1
    # Release OpenCV windows
    cv2.destroyAllWindows()   # releasing the video generated 

# Main server function: receives frames, processes faces, and sends results back to client
def server_program():
    # Get the hostname and set up the server socket
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # get instance
    server_socket.bind((host, port))  # bind host address and port together
    server_socket.listen(1)  # listen for a single client
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))
    # Initialize lists for face data
    face_locations, face_encodings, blacklist_face_encodings, blacklist_face_names, record_face_encodings, images = ([] for i in range(6))
    pattern = re.compile(r"record_(\d+)\.png")
    counter_file: int = 0
    counter_temp_foot: int = 0
    now = datetime.now()
    monthVal: str = now.strftime("%m")
    dayVal: str = now.strftime("%d")
    current_path = os.getcwd()
    # Load known faces from folders
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
    while True:
        # Receive data from client
        now = datetime.now()
        preciseTime = now.strftime("%H_%M_%S_")
        monthVal = now.strftime("%m")
        dayVal = now.strftime("%d")
        data = conn.recv(2097152)
        if not data:
            # If data is not received, break
            break
        # Split received data into image and metadata
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
        # Detect faces and compute encodings
        face_locations = face_recognition.face_locations(frameServer)
        face_encodings = face_recognition.face_encodings(frameServer, face_locations)
        face_names: list = []
        face_keys: list = []
        face_ivs: list = []
        face_id: list = []
        i: int = 0   
        for face_encoding in face_encodings:
            # Compare with blacklist and record encodings
            blacklist = face_recognition.compare_faces(blacklist_face_encodings, face_encoding,tolerance=0.65)
            record = face_recognition.compare_faces(record_face_encodings, face_encoding,tolerance=0.65)
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
                with open(f"faces/{monthVal}/{dayVal}/record_{record_BMI + 1}.png", "rb") as f:
                    for chunk in iter(lambda: f.read(), b''):
                        testlist = chunk.split(b'/_/@/_')
                    key = testlist[-2]
                    iv = testlist[-1]
                face_names.append(f'{name} ({confidence})')
                face_keys.append(key)
                face_ivs.append(iv)
            else:
                # New face: generate key/iv, crop, and save
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
        # Display the results and encrypt unknown faces
        block_size: int = 16
        extrabyte: int = 0
        keyfacedata: str = ''
        for (top, right, bottom, left), name, key, iv in zip(face_locations, face_names, face_keys, face_ivs):
            if name == 'Unknown (???)':
                # Save face locations, keys, and IVs for each face
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
                # Draw rectangle and label for known faces
                cv2.rectangle(frameServer, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frameServer, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                cv2.putText(frameServer, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
        # Save the processed frame and send it back to the client
        footageFrame = Image.fromarray(frameServer)
        images.append(footageFrame)
        counter_temp_foot += 1
        frameServer.tobytes()
        conn.send(frameServer)  # send data to the client
        anexInfo = preciseTime + '@' + keyfacedata
        file = open(f'C:\\Users\\david\\Documents\\GitProjects\\CCTV_PrivacyMasking\\KDInfo\\{monthVal}\\{dayVal}\\tempInfo.txt', 'a')
        file.write(anexInfo + "\n")
        file.close() 
    # After loop: save logs, clean up, and generate video
    conn.close()  # close the connection
    now = datetime.now()
    date_time: str = now.strftime("%H_%M_%S")
    source_file =  open(f'C:\\Users\\david\\Documents\\GitProjects\\CCTV_PrivacyMasking\\KDInfo\\{monthVal}\\{dayVal}\\tempInfo.txt', 'rb')
    destination_file = open(f'C:\\Users\\david\\Documents\\GitProjects\\CCTV_PrivacyMasking\\KDInfo\\{monthVal}\\{dayVal}\\KDInfo_{date_time}.txt', 'wb')
    shutil.copyfileobj(source_file, destination_file)
    source_file.close()
    destination_file.close()
    os.remove(f'C:\\Users\\david\\Documents\\GitProjects\\CCTV_PrivacyMasking\\KDInfo\\{monthVal}\\{dayVal}\\tempInfo.txt')
    generate_video(images ,now)
    
# TODO: Add a check for month transitions in video recording
# TODO: Improve naming convention for blacklisted faces
if __name__ == '__main__':
    server_program()




