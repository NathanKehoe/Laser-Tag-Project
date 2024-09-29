import socket

def server():
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('127.0.0.1', 7501))
    print("Server is listening on port 7501...")

    while True:
        data, addr = server_socket.recvfrom(1024)  # Buffer size is 1024 bytes
        print(f"Received from {addr}: {data.decode()}")
        
        # Optionally send a response back to the client
        response = f"Received: {data.decode()}"
        server_socket.sendto(response.encode(), addr)

if __name__ == "__main__":
    server()