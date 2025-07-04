import sqlite3
import tkinter as tk
import sys
from tkinter import ttk, messagebox
from tkinter import filedialog

#Local Imports
from app.config import PATHS, DB_PATH

# Connect to the database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Function to close the form
def close_form():
    if messagebox.askquestion("Close Form", "Are you sure you want to close the form?") == "yes":
        window.destroy()

# Function to populate the tree with address data
def populate_tree(records):
    tree.delete(*tree.get_children())  # Clear existing records in the tree

    for record in records:
        try:
            # Insert the record into the treeview
            tree.insert("", tk.END, values=record)
        except Exception as e:
            print(f"Failed to insert record {record}: {e}")  # Error handling

# Function to display all records
def display_records(query, parameters=[]):
    cursor.execute(query, parameters)
    records = cursor.fetchall()
    populate_tree(records)

# Function to search for addresses
def search_addresses():
    address = entry_address.get().strip()
    if not address:
        messagebox.showinfo("No Input", "Please enter an address to search.")
        return

    query = "SELECT * FROM Address WHERE address LIKE ?"
    parameters = [f"%{address}%"]
    display_records(query, parameters)

# Function to clear search fields
def clear_search_fields():
    entry_address.delete(0, tk.END)
    display_all_records()

# Function to display all records
def display_all_records():
    query = "SELECT * FROM Address"
    display_records(query)

# Create the GUI window
window = tk.Tk()
window.title("Address Management")

# Set the window size and position
window_width = 1200
window_height = 600
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Create a frame for the search controls
frame_search = ttk.Frame(window)
frame_search.pack(pady=10)

# Address entry
label_address = ttk.Label(frame_search, text="Address:")
label_address.grid(row=0, column=0, padx=5, pady=5)
entry_address = ttk.Entry(frame_search)
entry_address.grid(row=0, column=1, padx=5, pady=5)

# Search button
button_search = ttk.Button(frame_search, text="Search", command=search_addresses)
button_search.grid(row=0, column=2, padx=5, pady=5)

# Clear button
button_clear = ttk.Button(frame_search, text="Clear", command=clear_search_fields)
button_clear.grid(row=0, column=3, padx=5, pady=5)

# Create a frame for the treeview
frame_tree = ttk.Frame(window)
frame_tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a horizontal scrollbar
x_scrollbar = ttk.Scrollbar(frame_tree, orient=tk.HORIZONTAL)

# Create a vertical scrollbar
y_scrollbar = ttk.Scrollbar(frame_tree)

# Create a treeview to display the records
tree = ttk.Treeview(frame_tree, xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set, show='headings')
tree["columns"] = ("ID", "Address", "Latitude", "Longitude", "Start Date", "End Date", "Old Address", "Parent Address", "Parcel ID")

# Define the headings and columns
for col in tree["columns"]:
    tree.heading(col, text=col)
    tree.column(col, anchor="w")

# Configure the scrollbars
x_scrollbar.config(command=tree.xview)
x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
y_scrollbar.config(command=tree.yview)
y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

tree.pack(fill=tk.BOTH, expand=True)

# Populate the tree with all records initially
display_all_records()

# Create a frame for the buttons
frame_buttons = ttk.Frame(window)
frame_buttons.pack(pady=10)

# Add button
button_add = ttk.Button(frame_buttons, text="Add Address", command=lambda: messagebox.showinfo("Info", "Add address functionality to be implemented"))
button_add.pack(side=tk.LEFT, padx=5)

# Delete button
button_delete = ttk.Button(frame_buttons, text="Delete Address", command=lambda: messagebox.showinfo("Info", "Delete address functionality to be implemented"))
button_delete.pack(side=tk.LEFT, padx=5)

# Close button
button_close = ttk.Button(frame_buttons, text="Close", command=close_form)
button_close.pack(side=tk.LEFT, padx=5)

# Run the GUI event loop
window.mainloop()

# Close the database connection
connection.close()
