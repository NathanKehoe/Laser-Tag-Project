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
# import for music
import pygame

# Initialize pygame mixer for music playback
pygame.mixer.init()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define fonts
LARGE_FONT = ("Arial", 24)
MEDIUM_FONT = ("Arial", 18)
SMALL_FONT = ("Arial", 14)

# song directory
SONG_DIRECTORY = "assets/music"
song_files = [f for f in os.listdir(SONG_DIRECTORY) if f.endswith('.mp3')]

# Global variables
root = None
red_team_players = []
green_team_players = []
countdown_running = True


class Player:
        def __init__(self, player_id, player_name, score, equipment_id=None):
            self.player_id = player_id
            self.player_name = player_name
            self.score = score
            self.equipment_id = equipment_id

        def __str__(self):
            return f"Player ID: {self.player_id}, Name: {self.player_name}, Score: {self.score}, Equipment ID: {self.equipment_id}"

        def update_equipment_id(self, new_equipment_id):
            self.equipment_id = new_equipment_id

        def get(self, attribute, default=None):
            return getattr(self, attribute, default)
    
broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# play background music on endless loop
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

# play background music on separate thread
def start_background_music_thread():
    """Start a separate thread to play background music."""
    music_thread = threading.Thread(target=play_background_music)
    music_thread.daemon = True  # Ensures thread closes when main program exits
    music_thread.start()

# Maybe move these to another file
def broadcast_game_start():
    try:
        while countdown_running:
            broadcast_socket.sendto(b'202', ('127.0.0.1', BROADCAST_PORT))
            time.sleep(0.5)  # Delay between broadcasts
    except Exception as e:
        logging.error(f"Error during broadcasting: {e}")
    finally:
        broadcast_socket.close()
        logging.info("Broadcast socket closed. Game start signal sent (202)")



def broadcast_game_end():
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
    splash_root.geometry("1280x720+0+0")  # Fullscreen

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

    # Add binding to close the application when Esc is pressed
    root.bind("<Escape>", lambda event: root.destroy())

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Configure grid weights
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    # Creating frames for Red Team and Green Team
    

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
        third_screen()
        
        

    def third_screen():
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
            third_root.destroy()
            root.deiconify()
            broadcast_game_end()

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
            tk.Label(red_team_frame, text=f"{name}  0", font=("Arial", 24), bg="#500000", fg="white").pack(pady=5)
        red_team_score = tk.Label(red_team_frame, text="0", font=("Arial", 48, "bold"), bg="#500000", fg="white")
        red_team_score.pack(side="bottom", pady=20)

        # Green Team Label and Player List
        tk.Label(green_team_frame, text="Green Team", font=("Arial", 36, "bold"), bg="#004d00", fg="white").pack(pady=20)
        for player in green_team_players:
            name = player.get("player_name", "Unknown")
            tk.Label(green_team_frame, text=f"{name}  0", font=("Arial", 24), bg="#004d00", fg="white").pack(pady=5)
        green_team_score = tk.Label(green_team_frame, text="0", font=("Arial", 48, "bold"), bg="#004d00", fg="white")
        green_team_score.pack(side="bottom", pady=20)

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
            event_text.insert("end", f"{event_message}\n")
            event_text.see("end")  # Scroll to the latest event

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
                start_game_countdown(360)  # Start the main game timer after countdown

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


        # Start the 30-second countdown with images
        start_initial_countdown()
        third_root.mainloop()



    


# Now, you can refactor your function to use the Player class
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
    tk.Label(red_team_frame, text="RED TEAM", font=LARGE_FONT, bg="#500000", fg="white").grid(row=0, column=0, columnspan=4, pady=10)
    tk.Label(green_team_frame, text="GREEN TEAM", font=LARGE_FONT, bg="#004d00", fg="white").grid(row=0, column=0, columnspan=4, pady=10)

    # Add column headers
    tk.Label(red_team_frame, text="No.", font=MEDIUM_FONT, bg="#500000", fg="white", width=5).grid(row=1, column=0)
    tk.Label(red_team_frame, text="ID", font=MEDIUM_FONT, bg="#500000", fg="white").grid(row=1, column=1)
    tk.Label(red_team_frame, text="Name", font=MEDIUM_FONT, bg="#500000", fg="white").grid(row=1, column=2)

    tk.Label(green_team_frame, text="No.", font=MEDIUM_FONT, bg="#004d00", fg="white", width=5).grid(row=1, column=0)
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
        logging.info(f"Server is listening on port {SERVER_PORT}...")

        while True:
            data, addr = server_socket.recvfrom(1024)
            message = data.decode('utf-8')
        
            if ':' in message:
                attacker_id, target_id = message.split(':')
                if attacker_id.isdigit() and target_id.isdigit():
                    attacker_id = int(attacker_id)
                    target_id = int(target_id)

                    if target_id == 43 or target_id == 53:
                        if target_id == 43:
                            add_points_to_player(attacker_id, 100, "B")  # Red player captures green base
                        elif target_id == 53:
                            add_points_to_player(attacker_id, 100, "B")  # Green player captures red base

                    attacker_exists = any(player.player_id == attacker_id for player in (red_team_players + green_team_players))
                    
                    target_exists = any(player.player_id == target_id for player in (red_team_players + green_team_players))
                    
                    if attacker_exists and target_exists:
                        attacker = next(player for player in (red_team_players + green_team_players) if player.player_id == attacker_id)
                        target = next(player for player in (red_team_players + green_team_players) if player.player_id == target_id)
                        action_message = f"Player {attacker.player_name} hit Player {target.player_name}"
                        print(action_message)
                        
                        response_id = process_action(attacker_id, target_id)
                        print(f"Response ID: {response_id}")
                    else:
                        print("Base Hit")


                        

    except Exception as e:
        logging.error(f"Server error: {e}")
    finally:
        server_socket.close()

        
def process_action(attacker_id, target_id):
    add_points_to_player(attacker_id, 10) 
    return target_id


# Updating the team score display for either the Red or Green team
def update_team_score_display(team):
    if team == "Red":
        total_score = sum(player.get("score",0) for player in red_team_players)
        #red_team_score.config(text=str(total_score))
        print(f"Team {team} {total_score}")
    elif team == "Green":
        total_score = sum(player.get("score", 0) for player in green_team_players)
        #green_team_score.config(text=str(total_score))
        print(f"Team {team} {total_score}")



# Adding points to a player based on their ID and updating their badge if needed
def add_points_to_player(player_id, points, badge=None):
    # Update score for red team player if found
    for player in red_team_players:
        if player.player_id == player_id:
            player.score = player.get('score', 0) + points
            if badge:
                player.player_name = f"{badge}{player.player_name}"
            update_team_score_display("Red")
            return

    # Update score for green team player if found
    for player in green_team_players:
        if player.player_id == player_id:
            player.score = player.get('score', 0) + points
            if badge:
                player.player_name = f"{badge} {player.player_name}"
            update_team_score_display("Green")
            return



def start_server():
    server_thread = threading.Thread(target=server)
    server_thread.daemon = True
    server_thread.start()



if __name__ == "__main__":
    start_background_music_thread()
    start_server()
    show_splash_screen()