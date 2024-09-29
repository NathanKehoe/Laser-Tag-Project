import socket

def client():
    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Server address
    server_address = ('localhost', 7501)  # Change to server IP if needed

    # Prompt for player ID
    player_id = input("Enter your player ID (2 digits): ")
    
    # Send player ID to server
    client_socket.sendto(player_id.encode(), server_address)
    print(f"Sent Player ID: {player_id}")

    # Wait for a response from the server
    data, _ = client_socket.recvfrom(1024)
    print(f"Received response: {data.decode()}")

    # Prompt for equipment ID
    equipment_id = input("Enter your equipment ID (2 digits): ")
    
    # Send equipment ID to server
    client_socket.sendto(equipment_id.encode(), server_address)
    print(f"Sent Equipment ID: {equipment_id}")

    # Wait for a response from the server
    data, _ = client_socket.recvfrom(1024)
    print(f"Received response: {data.decode()}")

    # Close the socket
    client_socket.close()

if __name__ == "__main__":
    client()