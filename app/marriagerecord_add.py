import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys

#Local Imports
from app.config import DB_PATH, PATHS
from app.context_menu import create_context_menu
from app.person_linkage import person_search_popup

# Connect to the database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

def get_custom_list(list_name):
    cursor.execute("SELECT list_values FROM CustomLists WHERE list_name = ?", (list_name,))
    result = cursor.fetchone()
    if result:
        return result[0].split('|')  # Splitting using the pipe delimiter
    else:
        return []

def apply_context_menu_to_all_entries(container):
    for widget in container.winfo_children():
        if isinstance(widget, ttk.Entry):
            create_context_menu(widget)
        elif widget.winfo_children():
            apply_context_menu_to_all_entries(widget)  # Recursively apply to child containers

# Check if an ID is passed as a command-line argument
person_id_arg = None
if len(sys.argv) > 1:
    try:
        person_id_arg = int(sys.argv[1])
    except ValueError:
        print("Invalid ID passed as argument.")

spouse1_id = None
spouse2_id = None

def set_spouse1_id(pid):
    global spouse1_id
    if pid is None:
        spouse1_display.config(text="(none)")
        spouse1_id = None
        return
    cursor.execute(
        "SELECT first_name, middle_name, last_name, married_name FROM People WHERE id = ?",
        (pid,),
    )
    row = cursor.fetchone()
    if row:
        name_parts = [row[0], row[1], row[2]]
        name = " ".join(p for p in name_parts if p)
        if row[3]:
            name += f" ({row[3]})"
        spouse1_display.config(text=name)
        spouse1_id = pid
    else:
        spouse1_display.config(text="(not found)")
        spouse1_id = None

def set_spouse2_id(pid):
    global spouse2_id
    if pid is None:
        spouse2_display.config(text="(none)")
        spouse2_id = None
        return
    cursor.execute(
        "SELECT first_name, middle_name, last_name, married_name FROM People WHERE id = ?",
        (pid,),
    )
    row = cursor.fetchone()
    if row:
        name_parts = [row[0], row[1], row[2]]
        name = " ".join(p for p in name_parts if p)
        if row[3]:
            name += f" ({row[3]})"
        spouse2_display.config(text=name)
        spouse2_id = pid
    else:
        spouse2_display.config(text="(not found)")
        spouse2_id = None

def pre_populate_spouse_field(person_id):
    set_spouse1_id(person_id)

# Function to close the form
def close_form():
    window.destroy()


def add_marriage_record():
    
    person1_id = spouse1_id
    person2_id = spouse2_id

    if not person1_id or not person2_id:
        messagebox.showerror("Error", "Please select both individuals for the marriage record.")
        return

    # Validate person IDs
    for person_id in [person1_id, person2_id]:
        cursor.execute("SELECT COUNT(*) FROM People WHERE id = ?", (person_id,))
        if cursor.fetchone()[0] == 0:
            messagebox.showerror("Error", f"Person ID {person_id} not found in People table.")
            return

    # Check for existing marriage record
    cursor.execute("SELECT COUNT(*) FROM Marriages WHERE (person1_id = ? AND person2_id = ?) OR (person1_id = ? AND person2_id = ?)",
             
              (person1_id, person2_id, person2_id, person1_id))
    if cursor.fetchone()[0] > 0:
        messagebox.showerror("Error", "Marriage record already exists for these individuals.")
        return

    marriage_date = entry_marriage_date.get().strip()
    marriage_end_date = entry_marriage_end_date.get().strip()
    marriage_location = entry_marriage_location.get().strip()
    marriage_note = entry_marriage_note.get().strip()
    marriage_link = entry_marriage_link.get().strip()

    # Data insertion
    try:
        cursor.execute("INSERT INTO Marriages (person1_id, person2_id, m_date, m_end_date, m_location, m_note, m_link) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (person1_id, person2_id, marriage_date, marriage_end_date, marriage_location, marriage_note, marriage_link))
        connection.commit()
        messagebox.showinfo("Success", "Marriage record added successfully.")
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

    # Close the database connection
    connection.close()

# Create the main window
window = tk.Tk()
window.title("Add Marriage Record")

# Set the window size and position
window_width = 800
window_height = 350
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Spouse 1 selection
label_person1_id = ttk.Label(window, text="Spouse 1:")
label_person1_id.grid(row=0, column=0, padx=5, pady=5, sticky="e")
spouse1_frame = ttk.Frame(window)
spouse1_frame.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="w")
spouse1_display = ttk.Label(spouse1_frame, text="(none)", width=40, relief="sunken", anchor="w")
spouse1_display.pack(side="left", padx=(0,5))
if person_id_arg is None:
    ttk.Button(spouse1_frame, text="Lookup", command=lambda: person_search_popup(set_spouse1_id)).pack(side="left")
    ttk.Button(spouse1_frame, text="Clear", command=lambda: set_spouse1_id(None)).pack(side="left")
else:
    set_spouse1_id(person_id_arg)

# Pre-populate if a person ID was provided
if person_id_arg:
    pre_populate_spouse_field(person_id_arg)

# Spouse 2 selection
label_person2_id = ttk.Label(window, text="Spouse 2:")
label_person2_id.grid(row=1, column=0, padx=5, pady=5, sticky="e")
spouse2_frame = ttk.Frame(window)
spouse2_frame.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="w")
spouse2_display = ttk.Label(spouse2_frame, text="(none)", width=40, relief="sunken", anchor="w")
spouse2_display.pack(side="left", padx=(0,5))
ttk.Button(spouse2_frame, text="Lookup", command=lambda: person_search_popup(set_spouse2_id)).pack(side="left")
ttk.Button(spouse2_frame, text="Clear", command=lambda: set_spouse2_id(None)).pack(side="left")

# Separator on the form
separator = ttk.Separator(window, orient='horizontal')
separator.grid(row=2, columnspan=6, pady=10, sticky='ew')

# Marriage Date
label_marriage_date = ttk.Label(window, text="Marriage Date (MM-DD-YYYY):")
label_marriage_date.grid(row=3, column=0, padx=5, pady=5)
entry_marriage_date = ttk.Entry(window)
entry_marriage_date.grid(row=3, column=1, padx=5, pady=5)

# Marriage End Date
label_marriage_end_date = ttk.Label(window, text="Marriage End Date (if applicable):")
label_marriage_end_date.grid(row=4, column=0, padx=5, pady=5)
entry_marriage_end_date = ttk.Entry(window)
entry_marriage_end_date.grid(row=4, column=1, padx=5, pady=5)

# Marriage Location
label_marriage_location = ttk.Label(window, text="Marriage Location:")
label_marriage_location.grid(row=5, column=0, padx=5, pady=5)
entry_marriage_location = ttk.Entry(window, width=40)
entry_marriage_location.grid(row=5, column=1, padx=5, pady=5)

# Fetching and setting custom locations
custom_locations = get_custom_list('custom_locations')
create_context_menu(entry_marriage_location, custom_locations)  # Assuming you have a function to handle this

# Marriage Note
label_marriage_note = ttk.Label(window, text="Marriage Note:")
label_marriage_note.grid(row=6, column=0, padx=5, pady=5)
entry_marriage_note = ttk.Entry(window, width=40)
entry_marriage_note.grid(row=6, column=1, padx=5, pady=5)

# Marriage Link
label_marriage_link = ttk.Label(window, text="Marriage Link:")
label_marriage_link.grid(row=7, column=0, padx=5, pady=5)
entry_marriage_link = ttk.Entry(window, width=40)
entry_marriage_link.grid(row=7, column=1, padx=5, pady=5)

# Apply context menus to all entry fields
apply_context_menu_to_all_entries(window)
my_custom_locations = get_custom_list('custom_locations')
create_context_menu(entry_marriage_location, my_custom_locations)  # Assuming you have a function to handle this


# Separator on the form
separator = ttk.Separator(window, orient='horizontal')
separator.grid(row=8, columnspan=6, pady=10, sticky='ew')

# Create a frame for the buttons
frame_buttons = ttk.Frame(window)
frame_buttons.grid(row=9, column=1, pady=10, sticky="nsew")

# Add Record Button
button_add_record = ttk.Button(frame_buttons, text="Add Record", command=add_marriage_record)
button_add_record.grid(row=0, column=0, padx=5)
button_close = ttk.Button(frame_buttons, text="Close", command=close_form)
button_close.grid(row=0, column=1, padx=5)

# Run the window
window.mainloop()

#Close the database connection
connection.close()
