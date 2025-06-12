import tkinter as tk
from tkinter import ttk
import sqlite3
import subprocess
import sys
from config import DB_PATH, PATHS

# Connect to the database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Define initial sort column and order
current_sort_column = ""
sort_order = {}

# Create a variable to store the current sort column
current_sort_column = None

def search_by_last_name():
    last_name = entry_last_name.get().strip()
    married_name = entry_last_name.get().strip()
    query = f"SELECT People.first_name, People.middle_name, People.last_name, People.married_name, Address.address, ResHistory.start_date, ResHistory.end_date ResHistory.notes FROM People INNER JOIN ResHistory ON People.id = ResHistory.owner_id INNER JOIN Address ON ResHistory.address_id = Address.address_id WHERE People.last_name LIKE '{last_name}%' Or People.married_name LIKE '{married_name}%' ORDER BY People.last_name"
    cursor.execute(query)
    records = cursor.fetchall()
    tree.delete(*tree.get_children())
    for record in records:
        tree.insert("", tk.END, values=record)

# Create a dictionary to keep track of sort order for each column
sort_order = {
    "First Name": True,
    "Middle Name": True,
    "Last Name": True,
    "Married Name": True,
    "Address": True,
    "Start Date": True,
    "End Date": True,
    "Notes": True
}

def edit_resident():
    print("Edit me goes here")

def delete_resident():
    print("Edit me goes here")

def add_resident():
    subprocess.run(["python", "addresident.py"])

def on_column_header_double_click(column):
    global current_sort_column
    global sort_order

    # Check if the column is already sorted in ascending order
    if column == current_sort_column and sort_order[column] == "ASC":
        ascending = False
    else:
        ascending = True

    # Store the current sort column and order
    current_sort_column = column
    sort_order[column] = "ASC" if ascending else "DESC"

    # Clear the treeview
    tree.delete(*tree.get_children())

    query = f"""SELECT 
                People.first_name AS [First Name], 
                People.middle_name AS [Middle Name], 
                People.last_name AS [Last Name],
                People.married_name AS [Married Name], 
                Address.address AS [Address], 
                ResHistory.start_date AS [Res Start Date],
                ResHistory.end_date AS [Res End Date]
                ResHistory.notes AS [Notes]
            FROM People 
            INNER JOIN ResHistory ON People.id = ResHistory.owner_id 
            INNER JOIN Address ON ResHistory.address_id = Address.address_id 
            ORDER BY {field_mapping[column]} {'ASC' if ascending else 'DESC'}"""

    cursor.execute(query)
    records = cursor.fetchall()

    # Insert the sorted records into the treeview
    for record in records:
        tree.insert("", tk.END, values=record)


# Start the layout of the GUI Interface
window = tk.Tk()
window.title("Resident Records")

window_width = 1200
window_height = 600
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

frame_main = ttk.Frame(window)
frame_main.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

frame = ttk.Frame(frame_main)
frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

tree = ttk.Treeview(frame, columns=("First Name", "Middle Name", "Last Name", "Married Name", "Address", "Start Date", "End Date", "Notes"), show="headings")

tree.heading("First Name", text="First Name", command=lambda: on_column_header_double_click("First Name"))
tree.heading("Middle Name", text="Middle Name", command=lambda: on_column_header_double_click("Middle Name"))
tree.heading("Last Name", text="Last Name", command=lambda: on_column_header_double_click("Last Name"))
tree.heading("Married Name", text="Married Name", command=lambda: on_column_header_double_click("Married Name"))
tree.heading("Address", text="Address", command=lambda: on_column_header_double_click("Address"))
tree.heading("Start Date", text="Res Start Date", command=lambda: on_column_header_double_click("Start Date"))
tree.heading("End Date", text="Res End Date", command=lambda: on_column_header_double_click("End Date"))
tree.heading("Notes", text="Notes", command=lambda: on_column_header_double_click("Notes"))

tree.column("First Name", width=100)
tree.column("Middle Name", width=100)
tree.column("Last Name", width=100)
tree.column("Married Name", width=100)
tree.column("Address", width=200)
tree.column("Start Date", width=80)
tree.column("End Date", width=80)
tree.column("Notes", width=300)

cursor.execute("SELECT People.first_name, People.middle_name, People.last_name, People.married_name, Address.address, ResHistory.start_date, ResHistory.end_date, ResHistory.notes FROM People INNER JOIN ResHistory ON People.id = ResHistory.owner_id INNER JOIN Address ON ResHistory.address_id = Address.address_id")
resident_records = cursor.fetchall()

for record in resident_records:
    first_name, middle_name, last_name, married_name, address, start_date, end_date, notes = record
    tree.insert("", tk.END, values=(first_name, middle_name, last_name, married_name, address, start_date, end_date, notes))

tree.pack(side=tk.LEFT, padx=10, pady=10)

frame_buttons = ttk.Frame(frame_main)
frame_buttons.pack(side=tk.RIGHT, pady=10, padx=(0, 10))

add_resident_button = ttk.Button(frame_buttons, text="Add Resident", command=add_resident)
add_resident_button.pack(pady=5)

edit_resident_button = ttk.Button(frame_buttons, text="Edit", command=edit_resident)
edit_resident_button.pack(pady=5)

delete_resident_button = ttk.Button(frame_buttons, text="Delete", command=delete_resident)
delete_resident_button.pack(pady=5)

frame_main.columnconfigure(0, weight=9)
frame_main.columnconfigure(1, weight=1)

window.mainloop()

connection.close()
