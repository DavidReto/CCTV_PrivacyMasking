import socket, threading, pickle, struct, cv2

def handle_client(conn, addr, camera_id):
    print(f"Camera {camera_id} connected from {addr}")
    data = b""
    payload_size = struct.calcsize("Q")

    while True:
        try:
            while len(data) < payload_size:
                packet = conn.recv(4096)
                if not packet:
                    raise ConnectionResetError
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            while len(data) < msg_size:
                data += conn.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]

            frame = pickle.loads(frame_data)

            # Display each camera in a different window
            cv2.imshow(f"Camera {camera_id}", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except Exception as e:
            print(f"❌ Lost connection with Camera {camera_id}: {e}")
            break

    conn.close()
    cv2.destroyWindow(f"Camera {camera_id}")

def start_server(host='0.0.0.0', port=25565):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("Server ready for camera streams...")

    camera_id = 0
    while True:
        conn, addr = server_socket.accept()
        camera_id += 1
        thread = threading.Thread(target=handle_client, args=(conn, addr, camera_id))
        thread.start()

start_server()