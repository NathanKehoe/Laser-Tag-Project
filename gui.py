import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import threading
import socket
import psycopg2
import os
import logging
import time
from database import connect, check_for_player, add_player, remove_player
from config import DB_NAME, DB_USER, DB_HOST, DB_PORT, BROADCAST_PORT, SERVER_PORT
import random
import pygame
import queue
from threading import Event

# Initialize pygame mixer for music playback
pygame.mixer.init()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define fonts
LARGE_FONT = ("Arial", 20)
MEDIUM_FONT = ("Arial", 15)
SMALL_FONT = ("Arial", 14)

# Song directory
SONG_DIRECTORY = "assets/music"
song_files = [f for f in os.listdir(SONG_DIRECTORY) if f.endswith('.mp3')]

# Global variables
root = None
red_team_players = []
green_team_players = []
countdown_running = True
event_queue = queue.Queue()  # Create a global event queue
red_team_score_label = None  # Declare global variables for team score labels
green_team_score_label = None
server_stop_event = Event()  # Initialize threading.Event for server stop
broadcast_allowed_event = Event()  # Initialize threading.Event for broadcasting control
broadcast_allowed_event.set()  # Initially allow broadcasting

class Player:
    def __init__(self, player_id, player_name, score, equipment_id=None):
        self.player_id = player_id
        self.original_name = player_name  # Keep the original name
        self.player_name = player_name
        self.score = score
        self.equipment_id = equipment_id
        self.label = None  # Store the player's label
        self.base_hits = 0  # Initialize base hits

    def add_base_hit(self):
        self.base_hits += 1
        # Add 'B' once per base hit
        self.player_name = f"{self.original_name} {'B' * self.base_hits}"
        if self.label:
            self.label.config(text=f"{self.player_name}  {self.score}")

    def __str__(self):
        return f"Player ID: {self.player_id}, Name: {self.player_name}, Score: {self.score}, Equipment ID: {self.equipment_id}"

    def update_equipment_id(self, new_equipment_id):
        self.equipment_id = new_equipment_id

    def get(self, attribute, default=None):
        return getattr(self, attribute, default)

# Play background music on an endless loop
def play_background_music():
    if not song_files:
        logging.warning("No songs found in the directory.")
        return

    while True:
        song_path = os.path.join(SONG_DIRECTORY, random.choice(song_files))
        pygame.mixer.music.load(song_path)
        pygame.mixer.music.play()
        logging.info(f"Playing background song: {song_path}")

        # Wait for the song to finish before loading a new one
        while pygame.mixer.music.get_busy():
            time.sleep(1)  # Check every second if the song has finished

# Play background music on a separate thread
def start_background_music_thread():
    """Start a separate thread to play background music."""
    music_thread = threading.Thread(target=play_background_music)
    music_thread.daemon = True  # Ensures thread closes when main program exits
    music_thread.start()

def broadcast_game_start():
    global broadcast_socket
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        while broadcast_allowed_event.is_set():
            broadcast_socket.sendto(b'202', ('127.0.0.1', BROADCAST_PORT))
            time.sleep(1)  # Delay between broadcasts
    except Exception as e:
        logging.error(f"Error during broadcasting: {e}")
    finally:
        broadcast_socket.close()
        logging.info("Broadcast socket closed. Game start signal sent (202)")

def broadcast_game_end():
    broadcast_allowed_event.clear()  # Stop broadcasting
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    for _ in range(3):
        broadcast_socket.sendto(b'221', ('127.0.0.1', BROADCAST_PORT))
        time.sleep(0.5)
    broadcast_socket.close()
    logging.info("Game end signal sent (221)")

def show_splash_screen():
    splash_root = tk.Tk()
    splash_root.overrideredirect(True)
    # splash_root.geometry("1280x720+0+0")  # Fullscreen
    screen_width = splash_root.winfo_screenwidth()
    screen_height = splash_root.winfo_screenheight()
    splash_root.geometry(f"{screen_width}x{screen_height}+0+0")

    try:
        splash_image = Image.open("assets/splash_image.png")
        splash_image = splash_image.resize((1920, 1080), Image.LANCZOS)
        splash_photo = ImageTk.PhotoImage(splash_image)
        splash_label = tk.Label(splash_root, image=splash_photo)
        splash_label.pack()
    except Exception as e:
        logging.error(f"Error loading splash image: {e}")
        splash_label = tk.Label(splash_root, text="Welcome to the Game!", font=("Arial", 48))
        splash_label.pack(pady=200)

    def show_main_screen():
        splash_root.destroy()
        main_screen()

    splash_root.after(3000, show_main_screen)  # Display for 3 seconds
    splash_root.mainloop()

def main_screen():
    global root
    if 'root' in globals() and root and root.winfo_exists():
        root.deiconify()
        return
    root = tk.Tk()
    root.title("Entry Terminal")
    root.geometry("1280x720")
    root.configure(bg="black")
    root.attributes("-fullscreen", True)

    # Add binding to close the application when Esc is pressed
    root.bind("<Escape>", lambda event: root.destroy())

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Configure grid weights
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    # Lists to hold references to Entry widgets
    red_team_id_entries = []
    red_team_name_entries = []
    green_team_id_entries = []
    green_team_name_entries = []

    # Label for instruction to press Esc to exit
    esc_instruction_label = tk.Label(root, text="Press Esc to exit the game", font=("Arial", 16), bg="black", fg="white")
    esc_instruction_label.grid(row=4, column=0, columnspan=2, pady=10)

    def print_players():
        logging.info(f"Red Team Players: {red_team_players}")
        logging.info(f"Green Team Players: {green_team_players}")

    def start_game():
        root.withdraw()
        start_server()  # Start the server when the game starts
        third_screen()

    def third_screen():
        global red_team_score_label, green_team_score_label
        third_root = tk.Toplevel(root)
        third_root.title("Player Action Screen")
        third_root.geometry("1280x720")
        third_root.configure(bg="black")

        # Configure grid weights for layout structure
        third_root.grid_columnconfigure(0, weight=1)
        third_root.grid_columnconfigure(1, weight=2)  # Event area gets more space
        third_root.grid_columnconfigure(2, weight=1)
        third_root.grid_rowconfigure(0, weight=1)
        third_root.grid_rowconfigure(1, weight=0)

        # Back to Entry Screen button
        def return_to_main():
            server_stop_event.set()
            broadcast_game_end()  # Stop broadcasting and send end signal
            third_root.destroy()
            root.deiconify()

        tk.Button(third_root, text="Back to Entry Screen", font=("Arial", 18), command=return_to_main).grid(row=1, column=1, pady=20)

        # Red Team Frame
        red_team_frame = tk.Frame(third_root, bg="#500000", bd=2, relief="ridge")
        red_team_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Event Log Frame (center frame for events)
        event_frame = tk.Frame(third_root, bg="black", bd=2, relief="ridge")
        event_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Green Team Frame
        green_team_frame = tk.Frame(third_root, bg="#004d00", bd=2, relief="ridge")
        green_team_frame.grid(row=0, column=2, padx=20, pady=20, sticky="nsew")

        # Red Team Label and Player List
        tk.Label(red_team_frame, text="Red Team", font=("Arial", 36, "bold"), bg="#500000", fg="white").pack(pady=20)
        for player in red_team_players:
            name = player.get("player_name", "Unknown")
            player_label = tk.Label(red_team_frame, text=f"{name}  {player.score}", font=("Arial", 24), bg="#500000", fg="white")
            player_label.pack(pady=5)
            player.label = player_label  # Store the label reference
        red_team_score_label = tk.Label(red_team_frame, text="0", font=("Arial", 48, "bold"), bg="#500000", fg="white")
        red_team_score_label.pack(side="bottom", pady=20)

        # Green Team Label and Player List
        tk.Label(green_team_frame, text="Green Team", font=("Arial", 36, "bold"), bg="#004d00", fg="white").pack(pady=20)
        for player in green_team_players:
            name = player.get("player_name", "Unknown")
            player_label = tk.Label(green_team_frame, text=f"{name}  {player.score}", font=("Arial", 24), bg="#004d00", fg="white")
            player_label.pack(pady=5)
            player.label = player_label  # Store the label reference
        green_team_score_label = tk.Label(green_team_frame, text="0", font=("Arial", 48, "bold"), bg="#004d00", fg="white")
        green_team_score_label.pack(side="bottom", pady=20)

        # Event Log Title in the Center
        tk.Label(event_frame, text="EVENT LOG", font=("Arial", 36, "bold"), bg="black", fg="white").pack(pady=20)

        # Event Log Area (Scrollable Text)
        event_text = tk.Text(event_frame, wrap="word", font=("Arial", 24), bg="black", fg="white", height=15)
        event_text.pack(fill="both", expand=True, padx=10, pady=10)
        scrollbar = tk.Scrollbar(event_text, command=event_text.yview)
        event_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Function to add events to the log
        def add_event(event_message):
            if event_text.winfo_exists():  # Check if the widget still exists
                event_text.insert("end", f"{event_message}\n")
                event_text.see("end")  # Scroll to the latest event

        # Function to find a player by ID
        def find_player_by_id(player_id):
            for player in red_team_players + green_team_players:
                if player.player_id == player_id:
                    return player
            return None

        # Function to process the event queue
        def process_event_queue():
            while not event_queue.empty():
                event = event_queue.get()
                if event[0] == 'hit':
                    attacker_id = event[1]
                    target_id = event[2]
                    attacker = find_player_by_id(attacker_id)
                    target = find_player_by_id(target_id)
                    if attacker and target:
                        add_event(f"Player {attacker.player_name} hit Player {target.player_name}")
                        add_points_to_player(attacker_id, 10)
                elif event[0] == 'base_capture':
                    attacker_id = event[1]
                    base_name = event[2]
                    attacker = find_player_by_id(attacker_id)
                    if attacker:
                        add_event(f"Player {attacker.player_name} captured {base_name}")
                        add_points_to_player(attacker_id, 100)
                        attacker.add_base_hit()
                        # Display the "B" in the event log
                        add_event(f"Player {attacker.player_name} has a 'B'. Total B's: {attacker.base_hits}")
                        if attacker.base_hits >= 3:
                            add_event(f"Player {attacker.player_name} has reached 3 base hits. Ending game.")
                            broadcast_game_end()
                            server_stop_event.set()
                            third_root.destroy()
                            root.deiconify()
            # Schedule the next call to this function only if the window still exists
            if not server_stop_event.is_set() and third_root.winfo_exists():
                third_root.after(100, process_event_queue)

        # Start processing the event queue
        process_event_queue()

        # 30-Second Countdown with Images
        countdown_label = tk.Label(event_frame, bg="black")
        countdown_label.pack(pady=20)

        def start_initial_countdown(count=30):
            if count > 0:
                image_filename = f"{count}.png"
                image_path = os.path.join("assets", "countdown_images", image_filename)
                try:
                    img = Image.open(image_path)
                    img = img.resize((200, 200), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    countdown_label.config(image=photo)
                    countdown_label.image = photo  # Keep a reference
                except Exception as e:
                    logging.error(f"Error loading image {image_path}: {e}")
                    countdown_label.config(text=f"{count}", font=("Arial", 48, "bold"), fg="white")

                third_root.after(1000, start_initial_countdown, count - 1)
            else:
                countdown_label.config(image="", text="")  # Clear countdown
                global countdown_running
                countdown_running = True  # Start broadcasting
                threading.Thread(target=broadcast_game_start, daemon=True).start()
                # Start the simulation thread **after** the countdown ends
                simulation_thread = threading.Thread(target=simulate_base_captures, daemon=True)
                simulation_thread.start()
                start_game_countdown(360)  # Start the main game timer after countdown

        # Function to simulate additional base captures
        def simulate_base_captures():
            while not server_stop_event.is_set():
                time.sleep(10)  # Wait for 10 seconds
                # Randomly choose a team and player
                team = random.choice(['Red', 'Green'])
                if team == 'Red' and red_team_players:
                    player = random.choice(red_team_players)
                    base_name = 'Red Base'
                    event_queue.put(('base_capture', player.player_id, base_name))
                elif team == 'Green' and green_team_players:
                    player = random.choice(green_team_players)
                    base_name = 'Green Base'
                    event_queue.put(('base_capture', player.player_id, base_name))

        # Main Game Timer (6 minutes)
        timer_frame = tk.Frame(event_frame, bg="black")
        timer_frame.pack(pady=20)
        time_remaining_label = tk.Label(timer_frame, text="Time Remaining:", font=("Arial", 36, "bold"), bg="black", fg="white")
        time_remaining_label.pack()
        timer_label = tk.Label(timer_frame, text="6:00", font=("Arial", 48, "bold"), bg="black", fg="white")
        timer_label.pack()

        def start_game_countdown(count):
            minutes, seconds = divmod(count, 60)
            timer_label.config(text=f"{minutes}:{seconds:02d}")
            if count > 0:
                third_root.after(1000, start_game_countdown, count - 1)
            else:
                broadcast_game_end()
                server_stop_event.set()
                third_root.destroy()
                root.deiconify()

        # Start the 30-second countdown with images
        start_initial_countdown()
        third_root.mainloop()

    def save_player_data(team, player_id_entry, name_entry, player_array, parent_window):
        player_id = player_id_entry.get().strip()
        player_name = name_entry.get().strip()
        score = 0

        if player_id and player_name:
            if player_id.isdigit():
                player_id = int(player_id)
            else:
                print("Invalid player ID.")
                return

            player = Player(player_id, player_name, score)
            player_array.append(player)
            print(f"Player added to {team}: {player}")

            equipment_id = simpledialog.askstring('Equipment ID', 'What is the equipment ID for the entered player?', parent=parent_window)
            if equipment_id:
                player.update_equipment_id(equipment_id)
                sock.sendto(equipment_id.encode('utf-8'), ('<broadcast>', 7501))
                print(f"Broadcasting equipment ID: {equipment_id}")
                name_entry.delete(0, tk.END)
                name_entry.insert(0, player_name)
            else:
                print("No equipment ID provided; broadcasting skipped.")

        elif player_id:
            player_name = check_for_player(player_id)

            if not player_name:
                print(f"Player not found under ID {player_id}.")
                player_name = simpledialog.askstring('Player Name', f"What would you like your Player Name to be for ID {player_id}?", parent=parent_window)

            if player_name:
                player = Player(int(player_id), player_name, score)

                equipment_id = simpledialog.askstring('Equipment ID', 'What is the equipment ID for the entered player?', parent=parent_window)

                if equipment_id:
                    player.update_equipment_id(equipment_id)
                    sock.sendto(equipment_id.encode('utf-8'), ('<broadcast>', 7501))
                    print(f"Broadcasting equipment ID: {equipment_id}")
                    name_entry.delete(0, tk.END)
                    name_entry.insert(0, player_name)
                else:
                    print("No equipment ID provided; broadcasting skipped.")
            else:
                print("Player name not provided; player not added.")

        else:
            messagebox.showerror("Input Error", "Both fields (ID and Name) must be filled!")

    # Create frames for Red Team and Green Team
    red_team_frame = tk.Frame(root, bg="#500000", bd=2, relief="ridge")
    red_team_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
    root.grid_columnconfigure(0, weight=1)

    green_team_frame = tk.Frame(root, bg="#004d00", bd=2, relief="ridge")
    green_team_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
    root.grid_columnconfigure(1, weight=1)

    # Configure grid weights for team frames
    for i in range(0, 20):  # Adjust as necessary
        red_team_frame.grid_rowconfigure(i, weight=1)
        green_team_frame.grid_rowconfigure(i, weight=1)
    for i in range(4):
        red_team_frame.grid_columnconfigure(i, weight=1)
        green_team_frame.grid_columnconfigure(i, weight=1)

    # Team Labels
    tk.Label(red_team_frame, text="RED TEAM", font=LARGE_FONT, bg="#500000", fg="white").grid(row=0, column=0, columnspan=4, pady=10, ipady=20)
    tk.Label(green_team_frame, text="GREEN TEAM", font=LARGE_FONT, bg="#004d00", fg="white").grid(row=0, column=0, columnspan=4, pady=10, ipady=20)

    # Add column headers
    tk.Label(red_team_frame, text="No.", font=MEDIUM_FONT, bg="#500000", fg="white", width=5).grid(row=1, column=0, ipady=10)
    tk.Label(red_team_frame, text="ID", font=MEDIUM_FONT, bg="#500000", fg="white").grid(row=1, column=1)
    tk.Label(red_team_frame, text="Name", font=MEDIUM_FONT, bg="#500000", fg="white").grid(row=1, column=2)

    tk.Label(green_team_frame, text="No.", font=MEDIUM_FONT, bg="#004d00", fg="white", width=5).grid(row=1, column=0, ipady=10)
    tk.Label(green_team_frame, text="ID", font=MEDIUM_FONT, bg="#004d00", fg="white").grid(row=1, column=1)
    tk.Label(green_team_frame, text="Name", font=MEDIUM_FONT, bg="#004d00", fg="white").grid(row=1, column=2)

    num_players = 18

    for i in range(num_players):
        row_num = i + 2  # Adjusted row index to account for team label and headers

        # Red Team
        tk.Label(red_team_frame, text=f"{i+1}", font=MEDIUM_FONT, bg="#500000", fg="white", width=5, anchor="e").grid(row=row_num, column=0, sticky="e")
        red_player_id_entry = tk.Entry(red_team_frame, width=15, font=MEDIUM_FONT)
        red_player_id_entry.grid(row=row_num, column=1, padx=10, pady=5, sticky="ew")
        red_team_id_entries.append(red_player_id_entry)

        red_name_entry = tk.Entry(red_team_frame, width=20, font=MEDIUM_FONT)
        red_name_entry.grid(row=row_num, column=2, padx=10, pady=5, sticky="ew")
        red_team_name_entries.append(red_name_entry)

        tk.Button(
            red_team_frame, text="Save", font=MEDIUM_FONT, bg="gray", fg="black", width=10,
            command=lambda entry_id=red_player_id_entry, entry_name=red_name_entry:
            save_player_data('Red', entry_id, entry_name, red_team_players, root)
        ).grid(row=row_num, column=3, padx=10, pady=5)

        # Green Team
        tk.Label(green_team_frame, text=f"{i+1}", font=MEDIUM_FONT, bg="#004d00", fg="white", width=5, anchor="e").grid(row=row_num, column=0, sticky="e")
        green_player_id_entry = tk.Entry(green_team_frame, width=15, font=MEDIUM_FONT)
        green_player_id_entry.grid(row=row_num, column=1, padx=10, pady=5, sticky="ew")
        green_team_id_entries.append(green_player_id_entry)

        green_name_entry = tk.Entry(green_team_frame, width=20, font=MEDIUM_FONT)
        green_name_entry.grid(row=row_num, column=2, padx=10, pady=5, sticky="ew")
        green_team_name_entries.append(green_name_entry)

        tk.Button(
            green_team_frame, text="Save", font=MEDIUM_FONT, bg="gray", fg="black", width=10,
            command=lambda entry_id=green_player_id_entry, entry_name=green_name_entry:
            save_player_data('Green', entry_id, entry_name, green_team_players, root)
        ).grid(row=row_num, column=3, padx=10, pady=5)

    game_mode_label = tk.Label(root, text="Game Mode: Standard public mode", font=MEDIUM_FONT, bg="black", fg="white")
    game_mode_label.grid(row=1, column=0, columnspan=2, pady=10)

    button_frame = tk.Frame(root, bg="black")
    button_frame.grid(row=2, column=0, columnspan=2, pady=10)
    root.grid_rowconfigure(2, weight=0)

    def clear_all_player_data():
        for entry in red_team_id_entries + red_team_name_entries + green_team_id_entries + green_team_name_entries:
            entry.delete(0, tk.END)
        red_team_players.clear()
        green_team_players.clear()
        logging.info("All player entries have been cleared.")

    button_texts = [
        ("F1 Print Players", print_players),
        ("F3 Start Game", start_game),
        ("F12 Clear Game", clear_all_player_data),
    ]

    def bind_keys(root_widget, key_command_pairs):
        for key, command in key_command_pairs:
            root_widget.bind(key, lambda event, cmd=command: cmd())

    key_command_pairs = [
        ('<F1>', print_players),
        ('<F3>', start_game),
        ('<F12>', clear_all_player_data),
    ]

    bind_keys(root, key_command_pairs)

    for i, (text, command) in enumerate(button_texts):
        tk.Button(button_frame, text=text, width=20, font=MEDIUM_FONT, bg="black", fg="green", command=command).grid(row=0, column=i, padx=10, pady=5)

    instructions = tk.Label(root, text="Use F1, F2, F3, etc. to navigate", font=MEDIUM_FONT, bg="black", fg="white")
    instructions.grid(row=3, column=0, columnspan=2, pady=10)

    root.mainloop()

def server():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind(('127.0.0.1', SERVER_PORT))
        server_socket.settimeout(1.0)  # Set timeout to 1 second
        logging.info(f"Server is listening on port {SERVER_PORT}...")

        client_addresses = set()  # Keep track of client addresses

        while not server_stop_event.is_set():
            try:
                data, addr = server_socket.recvfrom(1024)
                client_addresses.add(addr)  # Add client address to the set
                message = data.decode('utf-8')

                if ':' in message:
                    attacker_id_str, target_id_str = message.split(':')
                    if attacker_id_str.isdigit() and target_id_str.isdigit():
                        attacker_id = int(attacker_id_str)
                        target_id = int(target_id_str)

                        if target_id == 43 or target_id == 53:
                            # Base capture events
                            base_name = 'Green Base' if target_id == 43 else 'Red Base'
                            event_queue.put(('base_capture', attacker_id, base_name))
                        else:
                            # Hit events
                            attacker_exists = any(player.player_id == attacker_id for player in (red_team_players + green_team_players))
                            target_exists = any(player.player_id == target_id for player in (red_team_players + green_team_players))

                            if attacker_exists and target_exists:
                                event_queue.put(('hit', attacker_id, target_id))
                            else:
                                print("Unknown player IDs")
                else:
                    print("Invalid message format")

                # Send an acknowledgment back to the client
                server_socket.sendto(b'ACK', addr)
            except socket.timeout:
                # Timeout occurred, check the stop event
                continue

        # After the loop exits, send '221' multiple times to all client addresses
        for client_addr in client_addresses:
            for _ in range(3):  # Send the signal 3 times
                server_socket.sendto(b'221', client_addr)
                logging.info(f"Sent game end signal to {client_addr}")
                time.sleep(0.5)  # Optional delay between signals

    except Exception as e:
        logging.error(f"Server error: {e}")
    finally:
        server_socket.close()

def add_points_to_player(player_id, points, badge=None):
    for player in red_team_players + green_team_players:
        if player.player_id == player_id:
            player.score += points
            if badge:
                player.player_name = f"{badge} {player.player_name}"
            # Update player's label
            if player.label and player.label.winfo_exists():
                player.label.config(text=f"{player.player_name}  {player.score}")
            # Update team score
            team = "Red" if player in red_team_players else "Green"
            update_team_score_display(team)
            return

def update_team_score_display(team):
    if team == "Red":
        total_score = sum(player.score for player in red_team_players)
        if red_team_score_label and red_team_score_label.winfo_exists():
            red_team_score_label.config(text=str(total_score))
    elif team == "Green":
        total_score = sum(player.score for player in green_team_players)
        if green_team_score_label and green_team_score_label.winfo_exists():
            green_team_score_label.config(text=str(total_score))

def start_server():
    server_stop_event.clear()
    server_thread = threading.Thread(target=server)
    server_thread.daemon = True
    server_thread.start()

if __name__ == "__main__":
    start_background_music_thread()
    show_splash_screen()
