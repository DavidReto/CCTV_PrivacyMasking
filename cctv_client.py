import cv2
import datetime as dt
import logging as log
import numpy as np
import socket
from time import sleep
from PIL import Image
from datetime import datetime

# Main client function to capture webcam frames and communicate with the server
def client_program():
    # Get the local machine name (assuming server and client run on the same PC)
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number
    cascPath = "haarcascade_frontalface_default.xml"  # Path to Haar cascade for face detection (not used in this script)
    faceCascade = cv2.CascadeClassifier(cascPath)  # Load the face cascade (not used below)
    # Set up logging to a file
    log.basicConfig(filename='webcam.log',level=log.INFO)
    # Open the default webcam (device 0)
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print('Unable to load camera.')
        sleep(5)
        pass
    # Create a socket object for client
    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    while True:
        # Capture a single frame from the webcam
        ret, frame = video_capture.read(0)
        # Resize frame of video to 1/4 size for faster face recognition processing (commented out)
        #small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR color (OpenCV default) to RGB color
        rgb_small_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
        # Get current date and time for timestamping
        now = datetime.now()
        date_time = now.strftime("%d_%m_%Y_%H:%M:%S.%f")
        # Prepare metadata: width, height, and timestamp, separated by a custom delimiter
        anexData = '/_/@/_'.encode('utf8') + str(rgb_small_frame.shape[1]).encode('utf8')  +'/_/@/_'.encode('utf8') + str(rgb_small_frame.shape[0]).encode('utf8') +'/_/@/_'.encode('utf8') + date_time.encode('utf8')  
        # Convert the RGB frame to bytes
        bytes_rgb_small_frame =  rgb_small_frame.tobytes()
        # Append metadata to the frame bytes
        bytes_rgb_small_frame = bytes_rgb_small_frame + anexData
        # Record the time before sending
        now = datetime.now()
        before = now.strftime("%S.%f")
        # Send the frame (with metadata) to the server
        client_socket.send(bytes_rgb_small_frame)  # send message
        # Wait for the server's response (processed frame or message)
        response = client_socket.recv(2097152)  # receive response
        # Record the time after receiving
        now = datetime.now()
        after = now.strftime("%S.%f")
        # Calculate the round-trip delay
        delay = float(after)-float(before)
        
        print(str(delay))  # Print the delay for monitoring
        try:
            # Try to reconstruct the image from the server's response
            frameResult = Image.frombytes("RGB", (rgb_small_frame.shape[1],rgb_small_frame.shape[0]), response)
            frameResult = np.array(frameResult)
            # Convert back to BGR for OpenCV display
            frameResult = cv2.cvtColor(frameResult, cv2.COLOR_BGR2RGB)
            
            # Show the processed frame in a window
            cv2.imshow('Video', frameResult)
        except:
            # If the response is not an image, print the message
            print(response.decode())
            continue
        
        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) == ord('q'):
            break

    # Release resources and close windows/sockets
    video_capture.release()
    cv2.destroyAllWindows()
    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()