import sqlite3
import tkinter as tk
import sys
from config import DB_PATH, PATHS
from tkinter import ttk, messagebox
import webbrowser
import subprocess


# Connect to the database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Fetch potential matches from the StagingFindAGrave table
def fetch_potential_matches():
    cursor.execute("""
        SELECT s.buried_link AS staging_link, s.first_name AS staging_first, s.middle_name AS staging_middle, s.last_name AS staging_last,
               p.id AS people_id, p.first_name AS people_first, p.middle_name AS people_middle, p.last_name AS people_last, 
               p.buried_link AS people_link, p.birth_date, p.death_date
        FROM StagingFindAGrave s
        LEFT JOIN People p ON s.first_name = p.first_name AND s.last_name = p.last_name
        WHERE p.buried_location LIKE 'Riverside Cemetery%' AND (p.buried_link IS NULL OR p.buried_link = '')
    """)
    return cursor.fetchall()

# Update the buried_link in the People table
def update_buried_link(staging_link, person_id):
    cursor.execute("UPDATE People SET buried_link = ? WHERE id = ?", (staging_link, person_id))
    connection.commit()

# Create the matching interface
def create_matching_interface():
    matches = fetch_potential_matches()
    
    # Set
    root = tk.Tk()
    root.title("FindAGrave Matching Interface")
    # root.geometry("1200x600")

    # Frame for the treeview
    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True)

    # Treeview for displaying matches
    columns = ("Staging Buried Link", "Staging First Name", "Staging Middle Name", "Staging Last Name", 
               "People ID", "People First Name", "People Middle Name", "People Last Name", 
               "People Buried Link", "People Birth Date", "People Death Date")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    # Customize column widths based on your preference
    tree.column("Staging Buried Link", width=200)
    tree.column("Staging First Name", width=100)
    tree.column("Staging Middle Name", width=100)
    tree.column("Staging Last Name", width=100)
    tree.column("People ID", width=50)
    tree.column("People First Name", width=100)
    tree.column("People Middle Name", width=100)
    tree.column("People Last Name", width=100)
    tree.column("People Buried Link", width=200)
    tree.column("People Birth Date", width=100)
    tree.column("People Death Date", width=100)

    # Add a vertical scrollbar to the treeview
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    tree.pack(fill="both", expand=True)

    # Function to sort columns
    def sort_column(col, reverse):
        data = [(tree.set(child, col), child) for child in tree.get_children('')]
        data.sort(reverse=reverse)
        for index, (_, child) in enumerate(data):
            tree.move(child, '', index)
        tree.heading(col, command=lambda: sort_column(col, not reverse))

    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: sort_column(c, False))

    # Function to open URL on double-click
    def open_url(event):
        item = tree.identify_row(event.y)
        if item:
            col = tree.identify_column(event.x)
            if col == '#1':  # Staging Buried Link is the first column
                url = tree.item(item, "values")[0]
                webbrowser.open(url)
            elif col == '#5':  # People ID is the fifth column
                person_id = tree.item(item, "values")[4]
                subprocess.run(["python", "editme.py", str(person_id)])

    tree.bind("<Double-1>", open_url)

    # Populate the tree with matches
    for match in matches:
        tree.insert('', 'end', values=match)

    # Frame for buttons
    button_frame = ttk.Frame(root)
    button_frame.pack(fill="x", pady=10)

    # Update button
    def on_update():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a record to update.")
            return
        item_values = tree.item(selected_item[0], "values")
        staging_link = item_values[0]
        person_id = item_values[4]
        update_buried_link(staging_link, person_id)
        tree.delete(selected_item[0])

    update_button = ttk.Button(button_frame, text="Update Record", command=on_update)
    update_button.pack(side="left", padx=5)

    # Skip button
    def on_skip():
        selected_item = tree.selection()
        if selected_item:
            tree.delete(selected_item[0])

    skip_button = ttk.Button(button_frame, text="Skip Record", command=on_skip)
    skip_button.pack(side="left", padx=5)

    # Run the Tkinter event loop
    root.mainloop()

# Run the interface
create_matching_interface()
