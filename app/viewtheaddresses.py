import sqlite3
import tkinter as tk
import sys
from app.config import DB_PATH, PATHS
from tkinter import ttk

# Connect to the database
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Function to close the form
def close_form():
    window.destroy()

# Create the GUI window
window = tk.Tk()
window.title("Address Records")

# Set the window size and position
window_width = 800
window_height = 600
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Create a frame for the treeview
frame_tree = ttk.Frame(window)
frame_tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a horizontal scrollbar
x_scrollbar = ttk.Scrollbar(frame_tree, orient=tk.HORIZONTAL)

# Create a vertical scrollbar
y_scrollbar = ttk.Scrollbar(frame_tree)

# Create a treeview to display the records
tree = ttk.Treeview(frame_tree, xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
tree["columns"] = ("id", "address", "latitude", "longitude", "start_date", "end_date", "old_address", "parent_address_id", "parcel_id", "geometry")
tree.heading("#0", text="ID", anchor="w")
tree.column("#0", width=50, anchor="w")
tree.heading("id", text="ID", anchor="w")
tree.column("id", width=50, anchor="w")
tree.heading("address", text="Address", anchor="w")
tree.column("address", width=100, anchor="w")
tree.heading("latitude", text="Latitude", anchor="w")
tree.column("latitude", width=100, anchor="w")
tree.heading("longitude", text="Longitude", anchor="w")
tree.column("longitude", width=100, anchor="w")
tree.heading("start_date", text="Start Date", anchor="w")
tree.column("start_date", width=100, anchor="w")
tree.heading("end_date", text="End Date", anchor="w")
tree.column("end_date", width=100, anchor="w")
tree.heading("old_address", text="Old Address", anchor="w")
tree.column("old_address", width=150, anchor="w")
tree.heading("parent_address_id", text="Parent Address ID", anchor="w")
tree.column("parent_address_id", width=100, anchor="w")
tree.heading("parcel_id", text="Parcel ID", anchor="w")
tree.column("parcel_id", width=150, anchor="w")
tree.heading("geometry", text="Geometry", anchor="w")
tree.column("geometry", width=150, anchor="w")

# Retrieve all records from the address table
c.execute("SELECT * FROM address")
records = c.fetchall()

# Insert the records into the treeview
for record in records:
    address_id, address, latitude, longitude, start_date, start_date_precision, end_date, end_date_precision, old_address, parent_address_id, parcel_id, geometry = record
    tree.insert("", tk.END, values=(address_id, address, latitude, longitude, start_date, end_date, old_address, parent_address_id, parcel_id, geometry))

# Create a frame for the buttons
frame_buttons = ttk.Frame(window)
frame_buttons.pack(pady=10)

# Close button
button_close = ttk.Button(frame_buttons, text="Close", command=close_form)
button_close.pack(side=tk.LEFT, padx=5)

# Pack the treeview and scrollbars
tree.pack(fill=tk.BOTH, expand=True)
x_scrollbar.config(command=tree.xview)
x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
y_scrollbar.config(command=tree.yview)
y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Run the GUI event loop
window.mainloop()

# Close the connection
conn.close()
