import sqlite3
import tkinter as tk
import sys
from tkinter import ttk, messagebox, simpledialog
from tkinter import filedialog

#Local Imports
from app.config import DB_PATH, PATHS

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
            # The first field is the internal address_id which we use as the iid
            # so it can be retrieved for edits/deletes without displaying it.
            tree.insert("", tk.END, iid=record[0], values=record[1:9])
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

# Helper to open the add/edit window. If ``address_id`` is provided the
# existing record will be loaded and updated on save.
def open_address_form(address_id=None):
    form = tk.Toplevel()
    form.title("Edit Address" if address_id else "Add New Address")

    labels = [
        "Address",
        "Latitude",
        "Longitude",
        "Start Date",
        "End Date",
        "Old Address",
        "Parent Address ID",
        "Parcel ID",
        "Geometry",
    ]
    
    entries = {}
    for idx, label_text in enumerate(labels):
        ttk.Label(form, text=label_text).grid(row=idx, column=0, padx=5, pady=5, sticky=tk.E)
        entry = ttk.Entry(form)
        entry.grid(row=idx, column=1, padx=5, pady=5, sticky=tk.W)
        entries[label_text] = entry

    if address_id:
        cursor.execute("SELECT address, lat, long, start_date, end_date, old_address, parent_address_id, parcel_id, geometry FROM Address WHERE address_id = ?", (address_id,))
        row = cursor.fetchone()
        if row:
            for key, value in zip(labels, row):
                entries[key].insert(0, value if value is not None else "")

    def save():
        values = [entries[label].get() for label in labels]
        if address_id:
            try:
                cursor.execute(
                    """
                    UPDATE Address
                       SET address=?, lat=?, long=?, start_date=?, end_date=?,
                           old_address=?, parent_address_id=?, parcel_id=?, geometry=?
                     WHERE address_id=?
                    """,
                    (*values, address_id),
                )
                connection.commit()
                messagebox.showinfo("Success", "Address updated successfully.")
                form.destroy()
                display_all_records()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            # Check if the address already exists to avoid duplicates
            cursor.execute("SELECT 1 FROM Address WHERE address = ?", (entries["Address"].get(),))
            if cursor.fetchone():
                messagebox.showerror("Error", "Address already exists in the database.")
                return
            try:
                cursor.execute(
                    """
                    INSERT INTO Address (address, lat, long, start_date, end_date, old_address,
                                        parent_address_id, parcel_id, geometry)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )
                connection.commit()
                messagebox.showinfo("Success", "Address added successfully.")
                form.destroy()
                display_all_records()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    ttk.Button(form, text="Save", command=save).grid(row=len(labels), column=0, columnspan=2, pady=10)

def add_address():
    open_address_form()        


def edit_address():
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showinfo("No Selection", "Please select an address to edit.")
        return
    # The iid of each row is the address_id
    open_address_form(int(selected_item))


# Function to delete an address
def delete_address():
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showinfo("No Selection", "Please select an address to delete.")
        return

    # Use the iid which stores the address_id
    address_id = int(selected_item)

    # Confirm the deletion
    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected address?"):
        try:
            cursor.execute("DELETE FROM Address WHERE address_id = ?", (address_id,))
            connection.commit()
            messagebox.showinfo("Success", "Address deleted successfully.")
            display_all_records()
        except Exception as e:
            messagebox.showerror("Error", str(e))

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
tree = ttk.Treeview(
    frame_tree,
    xscrollcommand=x_scrollbar.set,
    yscrollcommand=y_scrollbar.set,
    show="headings",
)
tree["columns"] = (
    "Address",
    "Latitude",
    "Longitude",
    "Start Date",
    "End Date",
    "Old Address",
    "Parent Address",
    "Parcel ID",
)

# Define readable column widths so the tree fits on screen
COLUMN_WIDTHS = {
    "Address": 300,
    "Latitude": 80,
    "Longitude": 80,
    "Start Date": 100,
    "End Date": 100,
    "Old Address": 150,
    "Parent Address": 120,
    "Parcel ID": 100,
}

for col in tree["columns"]:
    tree.heading(col, text=col)
    width = COLUMN_WIDTHS.get(col, 100)
    tree.column(col, width=width, anchor="w")

# Configure the scrollbars
x_scrollbar.config(command=tree.xview)
x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
y_scrollbar.config(command=tree.yview)
y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

tree.pack(fill=tk.BOTH, expand=True)
tree.bind("<Double-1>", lambda e: edit_address())

# Populate the tree with all records initially
display_all_records()

# Create a frame for the buttons
frame_buttons = ttk.Frame(window)
frame_buttons.pack(pady=10)

# Add button
button_add = ttk.Button(frame_buttons, text="Add Address", command=add_address)
button_add.pack(side=tk.LEFT, padx=5)

# Edit button
button_edit = ttk.Button(frame_buttons, text="Edit Address", command=edit_address)
button_edit.pack(side=tk.LEFT, padx=5)

# Delete button
button_delete = ttk.Button(frame_buttons, text="Delete Address", command=delete_address)
button_delete.pack(side=tk.LEFT, padx=5)

# Close button
button_close = ttk.Button(frame_buttons, text="Close", command=close_form)
button_close.pack(side=tk.LEFT, padx=5)

# Run the GUI event loop
window.mainloop()

# Close the database connection
connection.close()