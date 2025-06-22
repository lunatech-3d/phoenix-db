import sqlite3
import tkinter as tk
import sys
from .config import DB_PATH, PATHS
from tkinter import ttk, messagebox

# Connect to the database
try:
    connection = sqlite3.connect('Phoenix.db')
    cursor = connection.cursor()
except sqlite3.Error as e:
    print("Database connection error:", e)
    sys.exit(1)

# Function to load organizations from the database and populate the Treeview
def load_organizations():
    try:
        # Clear existing items in the Treeview
        org_treeview.delete(*org_treeview.get_children())

        # Fetch organizations from the database
        cursor.execute("SELECT * FROM Org")
        organizations = cursor.fetchall()

        # Populate the Treeview with organization data
        for org in organizations:
            org_treeview.insert("", "end", values=org)

        # Enable/disable Edit and Delete buttons based on the number of records
        if organizations:
            button_edit_org.config(state="normal")
            button_delete_org.config(state="normal")
        else:
            button_edit_org.config(state="disabled")
            button_delete_org.config(state="disabled")
    except sqlite3.Error as e:
        print("Error loading organizations:", e)

# Function to add organization to the database
def add_organization_window():
    add_window = tk.Toplevel(root)
    add_window.title("Add Organization")

    # Organization Name
    label_org_name = ttk.Label(add_window, text="Organization Name:")
    label_org_name.grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_org_name = ttk.Entry(add_window)
    entry_org_name.grid(row=0, column=1, padx=5, pady=5)

    # Organization Description
    label_org_desc = ttk.Label(add_window, text="Organization Description:")
    label_org_desc.grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_org_desc = ttk.Entry(add_window)
    entry_org_desc.grid(row=1, column=1, padx=5, pady=5)

    # Organization Type
    label_org_type = ttk.Label(add_window, text="Organization Type:")
    label_org_type.grid(row=2, column=0, padx=5, pady=5, sticky="e")
    combo_org_type = ttk.Combobox(add_window, state="readonly")
    combo_org_type.grid(row=2, column=1, padx=5, pady=5)

    # Populate organization types from CustomLists
    try:
        cursor.execute("SELECT list_values FROM CustomLists WHERE list_name = 'org_types'")
        org_types = cursor.fetchone()
        if org_types:
            org_types = org_types[0].split(',')
            combo_org_type['values'] = org_types
    except sqlite3.Error as e:
        print("Error fetching organization types:", e)

    # Function to add organization
    def add_organization():
        org_name = entry_org_name.get().strip()
        org_desc = entry_org_desc.get().strip()
        org_type = combo_org_type.get()

        # Check for empty fields
        if not org_name or not org_desc or not org_type:
            messagebox.showerror("Error", "Please fill out all fields.")
            return

        try:
            # Insert organization into the database
            cursor.execute("INSERT INTO Org (org_name, org_desc, org_type) VALUES (?, ?, ?)", (org_name, org_desc, org_type))
            connection.commit()
            print("Organization added successfully!")
            load_organizations()
            add_window.destroy()
        except sqlite3.Error as e:
            print("Error adding organization:", e)
            messagebox.showerror("Error", "Failed to add organization.")

    # Button to add organization
    button_add_org = ttk.Button(add_window, text="Add Organization", command=add_organization)
    button_add_org.grid(row=3, column=1, padx=5, pady=5, sticky="e")

# Function to edit organization in the database
def edit_organization_window():
    selected_item = org_treeview.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select an organization to edit.")
        return

    edit_window = tk.Toplevel(root)
    edit_window.title("Edit Organization")

    org_id = org_treeview.item(selected_item, "values")[0]

    # Fetch organization details
    cursor.execute("SELECT org_name, org_desc, org_type FROM Org WHERE org_id=?", (org_id,))
    org_details = cursor.fetchone()

    if org_details:
        org_name, org_desc, org_type = org_details

        # Organization Name
        label_org_name = ttk.Label(edit_window, text="Organization Name:")
        label_org_name.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        entry_org_name = ttk.Entry(edit_window)
        entry_org_name.insert(0, org_name)
        entry_org_name.grid(row=0, column=1, padx=5, pady=5)

        # Organization Description
        label_org_desc = ttk.Label(edit_window, text="Organization Description:")
        label_org_desc.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        entry_org_desc = ttk.Entry(edit_window)
        entry_org_desc.insert(0, org_desc)
        entry_org_desc.grid(row=1, column=1, padx=5, pady=5)

        # Organization Type
        label_org_type = ttk.Label(edit_window, text="Organization Type:")
        label_org_type.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        combo_org_type = ttk.Combobox(edit_window, state="readonly")
        combo_org_type.grid(row=2, column=1, padx=5, pady=5)

        # Populate organization types from CustomLists
        try:
            cursor.execute("SELECT list_values FROM CustomLists WHERE list_name = 'org_types'")
            org_types = cursor.fetchone()
            if org_types:
                org_types = org_types[0].split(',')
                combo_org_type['values'] = org_types
                combo_org_type.set(org_type)
        except sqlite3.Error as e:
            print("Error fetching organization types:", e)

        # Function to update organization
        def update_organization():
            new_org_name = entry_org_name.get().strip()
            new_org_desc = entry_org_desc.get().strip()
            new_org_type = combo_org_type.get()

            # Check for empty fields
            if not new_org_name or not new_org_desc or not new_org_type:
                messagebox.showerror("Error", "Please fill out all fields.")
                return

            try:
                # Update organization in the database
                cursor.execute("UPDATE Org SET org_name=?, org_desc=?, org_type=? WHERE org_id=?", (new_org_name, new_org_desc, new_org_type, org_id))
                connection.commit()
                print("Organization updated successfully!")
                load_organizations()
                edit_window.destroy()
            except sqlite3.Error as e:
                print("Error updating organization:", e)
                messagebox.showerror("Error", "Failed to update organization.")

        # Button to update organization
        button_update_org = ttk.Button(edit_window, text="Update Organization", command=update_organization)
        button_update_org.grid(row=3, column=1, padx=5, pady=5, sticky="e")
    else:
        messagebox.showerror("Error", "Failed to fetch organization details.")

# Function to delete organization from the database
def delete_organization():
    selected_item = org_treeview.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select an organization to delete.")
        return

    org_id = org_treeview.item(selected_item, "values")[0]

    try:
        # Delete organization from the database
        cursor.execute("DELETE FROM Org WHERE org_id=?", (org_id,))
        connection.commit()
        print("Organization deleted successfully!")
        load_organizations()
    except sqlite3.Error as e:
        print("Error deleting organization:", e)
        messagebox.showerror("Error", "Failed to delete organization.")

# Create the main Tkinter window
root = tk.Tk()
root.title("Manage Organizations")

# Frame for organization list
frame_org_list = ttk.LabelFrame(root, text="Organization List")
frame_org_list.pack(padx=10, pady=10, fill="both", expand=True)

# Treeview to display organizations
org_treeview = ttk.Treeview(frame_org_list, columns=("Organization ID", "Name", "Description", "Type"), show='headings')
org_treeview.heading("Organization ID", text="Org ID")
org_treeview.heading("Name", text="Name")
org_treeview.heading("Description", text="Description")
org_treeview.heading("Type", text="Type")
org_treeview.column("Organization ID", width=50)  # Set the column width of "Org ID" to 10
org_treeview.pack(side="left", fill="both", expand=True)
org_treeview.pack(side="left", fill="both", expand=True)

# Scrollbar for the Treeview
scrollbar = ttk.Scrollbar(frame_org_list, orient="vertical", command=org_treeview.yview)
scrollbar.pack(side="right", fill="y")
org_treeview.configure(yscrollcommand=scrollbar.set)

# Button to add organization
button_add_org = ttk.Button(root, text="Add Organization", command=add_organization_window)
button_add_org.pack(pady=5)

# Button to edit organization
button_edit_org = ttk.Button(root, text="Edit Organization", command=edit_organization_window, state="disabled")
button_edit_org.pack(pady=5)

# Button to delete organization
button_delete_org = ttk.Button(root, text="Delete Organization", command=delete_organization, state="disabled")
button_delete_org.pack(pady=5)

# Load organizations when the GUI starts
load_organizations()

# Start the Tkinter event loop
root.mainloop()
