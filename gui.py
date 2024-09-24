import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.title("Player Entry Screen")

root.geometry("1200x600")


num_players_per_team = 4 

team1_name_vars = []
team1_equipment_id_vars = []
team2_name_vars = []
team2_equipment_id_vars = []


def start_game(event=None):
    messagebox.showinfo("Start", "Starting the game...")


def retrieve_player_data():
    for i in range(num_players_per_team):
        player_name = team1_name_vars[i].get()
        equipment_id = team1_equipment_id_vars[i].get()
        print(f"Team 1 Player {i+1}: Name = {player_name}, Equipment ID = {equipment_id}")
    
    for i in range(num_players_per_team):
        player_name = team2_name_vars[i].get()
        equipment_id = team2_name_vars[i].get()
        print(f"Team 2 Player {i+1}: Name = {player_name}, Equipment ID = {equipment_id}")


def clear_entries(event=None):
    for i in range(num_players_per_team):
        team1_name_vars[i].set("")
        team1_equipment_id_vars[i].set("")
        team2_name_vars[i].set("")
        team2_equipment_id_vars[i].set("")


tk.Label(root, text="Team 1", font=("Arial", 16)).grid(row=0, column=0, columnspan=4)

for i in range(num_players_per_team):
    player_name_var = tk.StringVar()
    equipment_id_var = tk.StringVar()

    team1_name_vars.append(player_name_var)
    team1_equipment_id_vars.append(equipment_id_var)

    tk.Label(root, text=f"Player {i+1} Name:").grid(row=i+1, column=0, sticky="e")
    tk.Entry(root, textvariable=player_name_var).grid(row=i+1, column=1)

    tk.Label(root, text=f"Equipment ID:").grid(row=i+1, column=2, sticky="e")
    tk.Entry(root, textvariable=equipment_id_var).grid(row=i+1, column=3)

tk.Label(root, text="Team 2", font=("Arial", 16)).grid(row=0, column=4, columnspan=4)

for i in range(num_players_per_team):
    player_name_var = tk.StringVar()
    equipment_id_var = tk.StringVar()

    team2_name_vars.append(player_name_var)
    team2_equipment_id_vars.append(equipment_id_var)

    tk.Label(root, text=f"Player {i+1} Name:").grid(row=i+1, column=4, sticky="e")
    tk.Entry(root, textvariable=player_name_var).grid(row=i+1, column=5)

    tk.Label(root, text=f"Equipment ID:").grid(row=i+1, column=6, sticky="e")
    tk.Entry(root, textvariable=equipment_id_var).grid(row=i+1, column=7)

tk.Button(root, text="Submit Player Data", command=retrieve_player_data).grid(row=num_players_per_team+1, column=0, columnspan=4)
tk.Button(root, text="Clear Entries", command=clear_entries).grid(row=num_players_per_team+1, column=4, columnspan=4)

root.bind('<F5>', start_game)
root.bind('<F12>', clear_entries)

root.mainloop()
