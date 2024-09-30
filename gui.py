import tkinter as tk
from PIL import Image, ImageTk
import threading
import socket

# Splash screen function
def show_splash_screen():
    splash_root = tk.Tk()
    splash_root.overrideredirect(True)
    splash_root.geometry("1200x600+100+50")  # Set the same size as the player entry screen

    splash_image = Image.open("assets/splash_image.png")
    splash_image = splash_image.resize((1200, 600), Image.Resampling.LANCZOS)  # Adjust image size

    splash_photo = ImageTk.PhotoImage(splash_image)
    splash_label = tk.Label(splash_root, image=splash_photo)
    splash_label.pack()

    def show_main_screen():
        splash_root.destroy()
        main_screen()

    splash_root.after(3000, show_main_screen)  # Display for 3 seconds
    splash_root.mainloop()

# Main screen function
def main_screen():
    root = tk.Tk()
    root.title("Entry Terminal")
    root.geometry("1200x700")
    root.configure(bg="black")

    # Creating frames for Red Team and Green Team
    red_team_frame = tk.Frame(root, bg="#500000", bd=2, relief="ridge", width=580, height=480)
    red_team_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    green_team_frame = tk.Frame(root, bg="#004d00", bd=2, relief="ridge", width=580, height=480)
    green_team_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    # Team Labels
    tk.Label(red_team_frame, text="RED TEAM", font=("Arial", 14, "bold"), bg="#500000", fg="white").grid(row=0, column=0, columnspan=4)
    tk.Label(green_team_frame, text="GREEN TEAM", font=("Arial", 14, "bold"), bg="#004d00", fg="white").grid(row=0, column=0, columnspan=4)

    # Player entry slots for both teams
    num_players = 18

    for i in range(num_players):
        tk.Label(red_team_frame, text=f"{i+1}", bg="#500000", fg="white", width=2, anchor="e").grid(row=i+1, column=0, sticky="e")
        tk.Checkbutton(red_team_frame, bg="#500000").grid(row=i+1, column=1, sticky="e")
        tk.Entry(red_team_frame, width=20).grid(row=i+1, column=2, padx=5)

        tk.Label(green_team_frame, text=f"{i+1}", bg="#004d00", fg="white", width=2, anchor="e").grid(row=i+1, column=0, sticky="e")
        tk.Checkbutton(green_team_frame, bg="#004d00").grid(row=i+1, column=1, sticky="e")
        tk.Entry(green_team_frame, width=20).grid(row=i+1, column=2, padx=5)

    # Game mode label at the bottom
    game_mode_label = tk.Label(root, text="Game Mode: Standard public mode", font=("Arial", 12), bg="black", fg="white")
    game_mode_label.grid(row=1, column=0, columnspan=2)

    # Control buttons
    button_frame = tk.Frame(root, bg="black")
    button_frame.grid(row=2, column=0, columnspan=2, pady=10)

    button_texts = ["F1 Edit Game", "F2 Game Parameters", "F3 Start Game", "F5 Preferred Games", 
                    "F7 View Game", "F8 View Game", "F10 Flick Sync", "F12 Clear Game"]

    for i, text in enumerate(button_texts):
        tk.Button(button_frame, text=text, width=15, font=("Arial", 10), bg="black", fg="green").grid(row=0, column=i, padx=5, pady=5)

    # Instruction label
    instructions = tk.Label(root, text="<Del> to Delete Player, <Ins> to Manually Insert, or edit codename", font=("Arial", 10), bg="black", fg="white")
    instructions.grid(row=3, column=0, columnspan=2)

    root.mainloop()

# Server function
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

# Function to start the server in a separate thread
def start_server():
    server_thread = threading.Thread(target=server)
    server_thread.daemon = True  # Daemonize the thread to exit when the main program exits
    server_thread.start()

if __name__ == "__main__":
    # Start the server thread
    start_server()

    # Show the splash screen, which will eventually lead to the main screen
    show_splash_screen()
