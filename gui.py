import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import threading
import socket
import psycopg2
import os

DB_NAME = "postgres"
DB_USER = "postgres"  
DB_PASSWORD = "password"  
DB_HOST = "localhost" 
DB_PORT = "5432"  

broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
broadcast_address = '255.255.255.255'
broadcast_port = 7500

def connect():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None
    
def check_for_player(player_id):
    conn = connect()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT codename FROM players WHERE id = %s;", (player_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return result[0]  # Return the codename if found
        else:
            return False  # Return False if not found
    except psycopg2.Error as e:
        print(f"Error querying the database: {e}")
        return False

# Add a new player to the database
def add_player(player_id, codename):
    conn = connect()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO players (id, codename) VALUES (%s, %s);", (player_id, codename))
        conn.commit()
        cursor.close()
        conn.close()
        return True  # Player added successfully
    except psycopg2.Error as e:
        print(f"Error inserting into the database: {e}")
        return False

# Remove a player from the database
def remove_player(player_id):
    conn = connect()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM players WHERE id = %s;", (player_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True  # Player removed successfully
    except psycopg2.Error as e:
        print(f"Error deleting from the database: {e}")
        return False

# Function to handle when a player ID is entered
def on_player_id_enter(event, player_id_entry, codename_entry):
    player_id = player_id_entry.get().strip()

    if player_id:
        # Check if player exists
        codename = check_for_player(player_id)
        if codename:
            codename_entry.delete(0, tk.END)
            codename_entry.insert(0, codename)
        else:
            # Prompt to add the player if not found
            add_new = messagebox.askyesno("Player Not Found", "Player ID not found. Would you like to add a new player?")
            if add_new:
                new_codename = simpledialog.askstring("New Player", "Enter codename for new player:")
                if new_codename:
                    add_player(player_id, new_codename)
                    codename_entry.delete(0, tk.END)
                    codename_entry.insert(0, new_codename)

#def ask_for_equipment():




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
    global root
    if 'root' in globals() and root.winfo_exists():
        root.deiconify()
        return
    root = tk.Tk()
    root.title("Entry Terminal")
    root.geometry("1200x700")
    root.configure(bg="black")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Creating frames for Red Team and Green Team
    red_team_players = []
    green_team_players = []

    # Lists to hold references to Entry widgets
    red_team_id_entries = []
    red_team_name_entries = []
    green_team_id_entries = []
    green_team_name_entries = []

    def print_players():
        print(f"Red Team Players: {red_team_players}")
        print(f"Green Team Players: {green_team_players}")

    def start_game():
        root.withdraw()
        third_screen()
    
    def third_screen():
        # Create a new window (Toplevel)
        third_root = tk.Toplevel(root)
        third_root.title('Player Action Screen')
        third_root.geometry("1200x700")
        third_root.configure(bg="black")

        # Function to return to the main screen
        def return_to_main():
            third_root.destroy()
            root.deiconify()

        # Back button
        tk.Button(third_root, text="Back to Main Screen", command=return_to_main).pack(pady=10)

        # Create a frame to hold the countdown image
        countdown_frame = tk.Frame(third_root, bg="black")
        countdown_frame.pack(side=tk.TOP, fill=tk.X)

        # Create a label to display the countdown images
        countdown_label = tk.Label(countdown_frame, bg="black")
        countdown_label.pack(pady=10)

        # Get the absolute path to the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Path to the countdown images
        countdown_images_path = os.path.join(script_dir, 'assets', 'countdown_images')

        # Function to start the countdown
        def start_countdown(count=31):
            if count > 0:
                # Load the image corresponding to the current count
                image_filename = f"{count-1}.png"  # Images are named 0.png to 29.png
                image_path = os.path.join(countdown_images_path, image_filename)
                try:
                    img = Image.open(image_path)
                    img = img.resize((200, 100), Image.LANCZOS)  # Resize image to a smaller size
                    photo = ImageTk.PhotoImage(img)
                    countdown_label.config(image=photo)
                    countdown_label.image = photo  # Keep a reference
                except Exception as e:
                    print(f"Error loading image {image_path}: {e}")

                # Schedule the next update after 1 second (1000 milliseconds)
                third_root.after(1000, start_countdown, count-1)
            else:
                # Countdown finished
                print("Countdown completed!")

        # Start the countdown
        start_countdown()

        # Create frames for each team below the countdown
        teams_frame = tk.Frame(third_root, bg="black")
        teams_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Frame for Red Team
        frame_a = tk.Frame(teams_frame, bg="#500000", bd=2, relief="ridge")
        frame_a.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame for Green Team
        frame_b = tk.Frame(teams_frame, bg="#004d00", bd=2, relief="ridge")
        frame_b.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Team Labels
        tk.Label(frame_a, text="RED TEAM", font=("Arial", 14, "bold"), bg="#500000", fg="white").pack(pady=5)
        tk.Label(frame_b, text="GREEN TEAM", font=("Arial", 14, "bold"), bg="#004d00", fg="white").pack(pady=5)

        # Function to display team names
        def display_team_names():
            # Display names for Team A
            for player in red_team_players:
                name = player['name']
                label = tk.Label(frame_a, text=name, bg="#500000", font=("Arial", 16))
                label.pack(pady=5)

            # Display names for Team B
            for player in green_team_players:
                name = player['name']
                label = tk.Label(frame_b, text=name, bg="#000000", font=("Arial", 16))
                label.pack(pady=5)

        # Call the function to display names
        display_team_names()

        # Start the main loop for the third_root window
        third_root.mainloop()

    # Function to save player data
    def save_player_data(team, player_id_entry, name_entry, player_array):
        player_id = player_id_entry.get().strip()
        player_name = name_entry.get().strip()

        if player_id and player_name:
            player_data = {'id': player_id, 'name': player_name}
            player_array.append(player_data)
            print(f"Player added to {team}: {player_data}")
        elif player_id:
            player_data = {'id': player_id}
            player_name = check_for_player(player_id)
            if not player_name:
                print("Player not found under ID, " + str(player_id))
                player_name = simpledialog.askstring('player_name', 'What would you like your Player Name?')
                if player_name:
                    player_data = {'id': player_id, 'name': player_name}
                    player_array.append(player_data)
                    name_entry.delete(0, tk.END)
                    name_entry.insert(0, player_name)
            else:
                print("Here is the name of the player for ID " + str(player_id) + ", " + str(player_name))
                player_data = {'id': player_id, 'name': player_name}
                player_array.append(player_data)
                name_entry.delete(0, tk.END)
                name_entry.insert(0, player_name)

                equipment_id = simpledialog.askstring('equipment_id', 'What is the equipment ID for the entered player?')
                if equipment_id:  # Check if an equipment ID was provided
                    sock.sendto(equipment_id.encode('utf-8'), ('<broadcast>', 7501))
                    print(f"Broadcasting equipment ID: {equipment_id}")
                else:
                    print("No equipment ID provided; broadcasting skipped.")
        else:
            messagebox.showerror("Input Error", "Both fields (ID and Name) must be filled!")

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
        # Red Team
        tk.Label(red_team_frame, text=f"{i+1}", bg="#500000", fg="white", width=2, anchor="e").grid(row=i+1, column=0, sticky="e")
        red_player_id_entry = tk.Entry(red_team_frame, width=10)
        red_player_id_entry.grid(row=i+1, column=1, padx=5)
        red_team_id_entries.append(red_player_id_entry)  # Store reference

        red_name_entry = tk.Entry(red_team_frame, width=15)
        red_name_entry.grid(row=i+1, column=2, padx=5)
        red_team_name_entries.append(red_name_entry)  # Store reference

        tk.Button(red_team_frame, text="Save", bg="gray", fg="black",
                  command=lambda red_player_id_entry=red_player_id_entry, red_name_entry=red_name_entry:
                  save_player_data('Red', red_player_id_entry, red_name_entry, red_team_players)).grid(row=i+1, column=3, padx=5)

        # Green Team
        tk.Label(green_team_frame, text=f"{i+1}", bg="#004d00", fg="white", width=2, anchor="e").grid(row=i+1, column=0, sticky="e")
        green_player_id_entry = tk.Entry(green_team_frame, width=10)
        green_player_id_entry.grid(row=i+1, column=1, padx=5)
        green_team_id_entries.append(green_player_id_entry)  # Store reference

        green_name_entry = tk.Entry(green_team_frame, width=15)
        green_name_entry.grid(row=i+1, column=2, padx=5)
        green_team_name_entries.append(green_name_entry)  # Store reference

        tk.Button(green_team_frame, text="Save", bg="gray", fg="black",
                  command=lambda green_player_id_entry=green_player_id_entry, green_name_entry=green_name_entry:
                  save_player_data('Green', green_player_id_entry, green_name_entry, green_team_players)).grid(row=i+1, column=3, padx=5)

    # Game mode label at the bottom
    game_mode_label = tk.Label(root, text="Game Mode: Standard public mode", font=("Arial", 12), bg="black", fg="white")
    game_mode_label.grid(row=1, column=0, columnspan=2)

    # Control buttons
    button_frame = tk.Frame(root, bg="black")
    button_frame.grid(row=2, column=0, columnspan=2, pady=10)

    # Function to clear all player data
    def clear_all_player_data():
        # Clear Entry fields for Red Team
        for entry in red_team_id_entries + red_team_name_entries:
            entry.delete(0, tk.END)
        # Clear Entry fields for Green Team
        for entry in green_team_id_entries + green_team_name_entries:
            entry.delete(0, tk.END)
        # Clear the player data lists
        red_team_players.clear()
        green_team_players.clear()
        print("All player entries have been cleared from the lists.")

        # Print the lists to confirm they are empty
        print(f"Red Team Players: {red_team_players}")
        print(f"Green Team Players: {green_team_players}")

    # Define button texts and commands
    button_texts = [
        ("F1 Print Players", print_players),  # Placeholder function
        ("F2 Game Parameters", lambda: print("Game Parameters function to be implemented")),  # Placeholder function
        ("F3 Start Game", start_game),  # Call start_game function
        ("F5 Preferred Games", lambda: print("Preferred Games function to be implemented")),  # Placeholder function
        ("F7 View Game", lambda: print("View Game function to be implemented")),  # Placeholder function
        ("F8 View Game", lambda: print("View Game function to be implemented")),  # Placeholder function
        ("F10 Flick Sync", lambda: print("Flick Sync function to be implemented")),  # Placeholder function
        ("F12 Clear Game", clear_all_player_data),  # Bind to the clear_all_player_data function
    ]

    # Creating buttons with customized properties
    for i, (text, command) in enumerate(button_texts):
        tk.Button(button_frame, text=text, width=15, font=("Arial", 10), bg="black", fg="green", command=command).grid(row=0, column=i, padx=5, pady=5)

    # Instruction label
    instructions = tk.Label(root, text="Use F1, F2, F3, etc. to navigate", font=("Arial", 10), bg="black", fg="white")
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

def listen_for_broadcasts():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_socket.bind(('', 7501))  # Bind to all interfaces on port 7501

    print("Listening for broadcasts on port 7501...")

    while True:
        data, addr = listen_socket.recvfrom(1024)  # Buffer size is 1024 bytes
        print(f"Received broadcast from {addr}: {data.decode('utf-8')}")

# Function to start the broadcast listener in a separate thread
def start_broadcast_listener():
    listener_thread = threading.Thread(target=listen_for_broadcasts)
    listener_thread.daemon = True  # Daemonize the thread
    listener_thread.start()

if __name__ == "__main__":
    # Start the server thread
    start_server()
    start_broadcast_listener()
    connect()
    # Show the splash screen, which will eventually lead to the main screen
    show_splash_screen()
