import cv2
import socket
import pickle
import struct

# === Configuration ===
SERVER_IP = '0.0.0.0'  # Replace with your server IP
PORT = 25565

# === Create socket and connect ===
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

# === OpenCV Video Capture ===
cap = cv2.VideoCapture(0)  # 0 = default webcam. Replace with RTSP stream if needed

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Serialize frame
        data = pickle.dumps(frame)

        # Pack message with a header (message size)
        message = struct.pack("", len(data)) + data

        # Send to server
        client_socket.sendall(message)

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    cap.release()
    client_socket.close()