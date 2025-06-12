import tkinter as tk
from tkinter import ttk
import sys
from config import DB_PATH
import sqlite3

# Connect to the database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()
connection_open = True

# Function to handle event submission
def submit_event():
    event_type = event_type_var.get()
    date = date_entry.get()
    location = location_entry.get()
    description = description_entry.get("1.0", "end-1c")
    source = source_entry.get()
    notes = notes_entry.get("1.0", "end-1c")

    # Insert event into Events table
    cursor.execute("INSERT INTO Events (type, date, location, description, source, notes) VALUES (?, ?, ?, ?, ?, ?)",
              (event_type, date, location, description, source, notes))
    connection.commit()

    # Get the ID of the last inserted event
    event_id = cursor.lastrowid

    # Insert event attributes into EventAttributes table
    for attr_name, attr_value in additional_attributes.items():
        cursor.execute("INSERT INTO EventAttributes (event_id, attribute_name, attribute_value) VALUES (?, ?, ?)",
                  (event_id, attr_name, attr_value))
    connection.commit()

    # Clear the entry fields after submission
    event_type_var.set('')
    date_entry.delete(0, 'end')
    location_entry.delete(0, 'end')
    description_entry.delete("1.0", "end")
    source_entry.delete(0, 'end')
    notes_entry.delete("1.0", "end")

# Create the main Tkinter window
root = tk.Tk()
root.title("Add Event")

# Event Type
event_type_label = ttk.Label(root, text="Event Type:")
event_type_label.grid(row=0, column=0, padx=5, pady=5)
event_type_var = tk.StringVar()
event_type_combobox = ttk.Combobox(root, textvariable=event_type_var, values=["Awards", "Community Service", "Leadership Roles"])  # Add more options as needed
event_type_combobox.grid(row=0, column=1, padx=5, pady=5)

# Date
date_label = ttk.Label(root, text="Date:")
date_label.grid(row=1, column=0, padx=5, pady=5)
date_entry = ttk.Entry(root)
date_entry.grid(row=1, column=1, padx=5, pady=5)

# Location
location_label = ttk.Label(root, text="Location:")
location_label.grid(row=2, column=0, padx=5, pady=5)
location_entry = ttk.Entry(root)
location_entry.grid(row=2, column=1, padx=5, pady=5)

# Description
description_label = ttk.Label(root, text="Description:")
description_label.grid(row=3, column=0, padx=5, pady=5)
description_entry = tk.Text(root, height=5, width=30)
description_entry.grid(row=3, column=1, padx=5, pady=5)

# Source
source_label = ttk.Label(root, text="Source:")
source_label.grid(row=4, column=0, padx=5, pady=5)
source_entry = ttk.Entry(root)
source_entry.grid(row=4, column=1, padx=5, pady=5)

# Notes
notes_label = ttk.Label(root, text="Notes:")
notes_label.grid(row=5, column=0, padx=5, pady=5)
notes_entry = tk.Text(root, height=5, width=30)
notes_entry.grid(row=5, column=1, padx=5, pady=5)

# Additional Attributes (Add more attributes as needed)
additional_attributes = {
    "Attribute1": "",
    "Attribute2": ""
}

# Submit Button
submit_button = ttk.Button(root, text="Submit", command=submit_event)
submit_button.grid(row=6, column=0, columnspan=2, padx=5, pady=10, sticky="ew")

# Start the Tkinter event loop
root.mainloop()