import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox

# Connect to the database
conn = sqlite3.connect('phoenix.db')
c = conn.cursor()

# Function to close the form
def close_form():
    window.destroy()

# Function to open the edit form for a selected business record
def edit_record():
    selected_item = tree.focus()
    if selected_item:
        biz_id = tree.item(selected_item)['values'][0]
        c.execute("SELECT * FROM Biz WHERE biz_id = ?", (biz_id,))
        record = c.fetchone()
        if record:
            open_edit_form(record)
        else:
            messagebox.showerror("Error", "Failed to retrieve the selected record.")
    else:
        messagebox.showerror("Error", "No record selected.")

# Function to open the form for adding a new business record
def add_record():
    open_edit_form()

# Function to save the changes made in the edit form
def save_changes():
    biz_id = entry_id.get()
    biz_name = entry_name.get()
    start_date = entry_start_date.get()
    end_date = entry_end_date.get()
    description = entry_description.get()
    category = entry_category.get()
    owner_id = entry_owner_id.get()
    address_id = entry_address_id.get()

    if biz_id:
        # Update existing record
        c.execute("UPDATE Business SET biz_name=?, start_date=?, end_date=?, description=?, category=?, owner_id=?, address_id=? WHERE biz_id=?", (biz_name, start_date, end_date, description, category, owner_id, address_id, biz_id))
        messagebox.showinfo("Success", "Record updated successfully.")
    else:
        # Insert new record
        c.execute("INSERT INTO Business (biz_name, start_date, end_date, description, category, owner_id, address_id) VALUES (?, ?, ?, ?, ?, ?, ?)", (biz_name, start_date, end_date, description, category, owner_id, address_id))
        messagebox.showinfo("Success", "Record added successfully.")

    conn.commit()
    close_edit_form()

# Function to open the edit form with the selected record's details
def open_edit_form(record=None):
    global edit_form
    edit_form = tk.Toplevel(window)
    edit_form.title("Edit Business Record")

    # Label and Entry widgets for each field
    label_id = ttk.Label(edit_form, text="ID:")
    label_id.grid(row=0, column=0, padx=5, pady=5)
    entry_id = ttk.Entry(edit_form)
    entry_id.grid(row=0, column=1, padx=5, pady=5)

    label_name = ttk.Label(edit_form, text="Name:")
    label_name.grid(row=1, column=0, padx=5, pady=5)
    entry_name = ttk.Entry(edit_form)
    entry_name.grid(row=1, column=1, padx=5, pady=5)

    label_start_date = ttk.Label(edit_form, text="Start Date:")
    label_start_date.grid(row=2, column=0, padx=5, pady=5)
    entry_start_date = ttk.Entry(edit_form)
    entry_start_date.grid(row=2, column=1, padx=5, pady=5)

    label_end_date = ttk.Label(edit_form, text="End Date:")
    label_end_date.grid(row=3, column=0, padx=5, pady=5)
    entry_end_date = ttk.Entry(edit_form)
    entry_end_date.grid(row=3, column=1, padx=5, pady=5)

    label_description = ttk.Label(edit_form, text="Description:")
    label_description.grid(row=4, column=0, padx=5, pady=5)
    entry_description = ttk.Entry(edit_form)
    entry_description.grid(row=4, column=1, padx=5, pady=5)

    label_category = ttk.Label(edit_form, text="Category:")
    label_category.grid(row=5, column=0, padx=5, pady=5)
    entry_category = ttk.Entry(edit_form)
    entry_category.grid(row=5, column=1, padx=5, pady=5)

    label_owner_id = ttk.Label(edit_form, text="Owner ID:")
    label_owner_id.grid(row=6, column=0, padx=5, pady=5)
    entry_owner_id = ttk.Entry(edit_form)
    entry_owner_id.grid(row=6, column=1, padx=5, pady=5)

    label_address_id = ttk.Label(edit_form, text="Address ID:")
    label_address_id.grid(row=7, column=0, padx=5, pady=5)
    entry_address_id = ttk.Entry(edit_form)
    entry_address_id.grid(row=7, column=1, padx=5, pady=5)

    # Populate the fields with the record details, if available
    if record:
        entry_id.insert(0, record[0])
        entry_name.insert(0, record[1])
        entry_start_date.insert(0, record[2])
        entry_end_date.insert(0, record[3])
        entry_description.insert(0, record[4])
        entry_category.insert(0, record[5])
        entry_owner_id.insert(0, record[6])
        entry_address_id.insert(0, record[7])

    # Save button
    save_button = ttk.Button(edit_form, text="Save Changes", command=save_changes)
    save_button.grid(row=8, column=0, columnspan=2, padx=5, pady=10)

# Create the GUI window
window = tk.Tk()
window.title("Business Records")

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

# Create a treeview to display the business records
tree = ttk.Treeview(frame_tree)
tree["columns"] = ("ID", "Name", "Start Date", "End Date", "Description", "Category", "Owner ID", "Address ID")
tree.heading("#0", text="ID", anchor="w")
tree.column("#0", width=50, anchor="w")
tree.heading("ID", text="ID", anchor="w")
tree.column("ID", width=50, anchor="w")
tree.heading("Name", text="Name", anchor="w")
tree.column("Name", width=200, anchor="w")
tree.heading("Start Date", text="Start Date", anchor="w")
tree.column("Start Date", width=100, anchor="w")
tree.heading("End Date", text="End Date", anchor="w")
tree.column("End Date", width=100, anchor="w")
tree.heading("Description", text="Description", anchor="w")
tree.column("Description", width=200, anchor="w")
tree.heading("Category", text="Category", anchor="w")
tree.column("Category", width=150, anchor="w")
tree.heading("Owner ID", text="Owner ID", anchor="w")
tree.column("Owner ID", width=100, anchor="w")
tree.heading("Address ID", text="Address ID", anchor="w")
tree.column("Address ID", width=100, anchor="w")

# Fetch all records from the Business table
c.execute("SELECT * FROM Biz")
records = c.fetchall()

# Insert the records into the treeview
for record in records:
    tree.insert("", tk.END, values=record)

# Bind double-click event on a treeview item to open the edit form
tree.bind("<Double-1>", lambda event: edit_record())

# Create a frame for the buttons
frame_buttons = ttk.Frame(window)
frame_buttons.pack(pady=10)

# Add Biz button
button_add = ttk.Button(frame_buttons, text="Add Biz", command=add_record)
button_add.pack(side=tk.LEFT, padx=5)

# Close button
button_close = ttk.Button(frame_buttons, text="Close", command=close_form)
button_close.pack(side=tk.LEFT, padx=5)

# Pack the treeview
tree.pack(fill=tk.BOTH, expand=True)

# Run the GUI event loop
window.mainloop()

# Close the connection
conn.close()
