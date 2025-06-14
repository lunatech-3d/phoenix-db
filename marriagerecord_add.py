import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys
from config import DB_PATH, PATHS
from context_menu import create_context_menu
from person_search import search_people as lookup_people

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

def pre_populate_spouse_field(person_id):
    # Fetch the person's name and other details for display
    cursor.execute("SELECT first_name, last_name, birth_date FROM People WHERE id = ?", (person_id,))
    person_info = cursor.fetchone()

    if person_info:
        formatted_info = f"{person_id}: {person_info[0]} {person_info[1]} | born - {person_info[2]}"
        combo_person1_id.set(formatted_info)  # Populate Person1 ID
    else:
        print("Person ID not found in database.")

# Function to close the form
def close_form():
    window.destroy()

def search_people(last_name_entry, person_dropdown):
    last_name = last_name_entry.get().strip()
    results = lookup_people(
        cursor,
        columns="id, first_name, middle_name, last_name, married_name, birth_date, death_date",
        last_name=last_name,
    )
    person_dropdown['values'] = [
        f"{person[0]}: {person[1]} {person[2]} | born - {person[5]}" for person in results
    ]
    
def fetch_people_data():
    cursor.execute("SELECT id, last_name, first_name, birth_date FROM People ORDER BY last_name, first_name")
    return [f"{row[0]}: {row[1]}, {row[2]} ({row[3]})" for row in cursor.fetchall()]

def add_marriage_record():
    # Extract selected person IDs from dropdown
    person1_selection = combo_person1_id.get()
    person2_selection = combo_person2_id.get()

    if not person1_selection or not person2_selection:
        messagebox.showerror("Error", "Please select both individuals for the marriage record.")
        return

    person1_id = person1_selection.split(" : ")[0]
    person2_id = person2_selection.split(" : ")[0]

    # Extract IDs from the selection
    person1_id = person1_selection.split(':')[0].strip() if person1_selection else None
    person2_id = person2_selection.split(':')[0].strip() if person2_selection else None

    # Convert the extracted IDs to integers
    try:
        person1_id = int(person1_id) if person1_id else None
        person2_id = int(person2_id) if person2_id else None
    except ValueError:
        messagebox.showerror("Error", "Invalid ID format")
        return

    print(f"Person 1 ID: {person1_id}")
    print(f"Person 2 ID: {person2_id}")

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

# Person1 Dropdown and Search
label_person1_id = ttk.Label(window, text="Spouse1 ID:")
label_person1_id.grid(row=0, column=0, padx=5, pady=5)
combo_person1_id = ttk.Combobox(window, width=40, state='readonly')
combo_person1_id.grid(row=0, column=1, padx=5, pady=5)

# Call the function if person_id_arg is provided
if person_id_arg:
    pre_populate_spouse_field(person_id_arg)
else: 
    entry_person1_search = ttk.Entry(window)
    entry_person1_search.grid(row=0, column=2, padx=5, pady=5)
    button_person1_search = ttk.Button(window, text="Search", command=lambda: search_people(entry_person1_search, combo_person1_id))
    button_person1_search.grid(row=0, column=3, padx=5, pady=5)

# Person2 Dropdown and Search
label_person2_id = ttk.Label(window, text="Spouse2 ID:")
label_person2_id.grid(row=1, column=0, padx=5, pady=5)
combo_person2_id = ttk.Combobox(window, width=40, state='readonly')
combo_person2_id.grid(row=1, column=1, padx=5, pady=5)
entry_person2_search = ttk.Entry(window)
entry_person2_search.grid(row=1, column=2, padx=5, pady=5)
button_person2_search = ttk.Button(window, text="Search", command=lambda: search_people(entry_person2_search, combo_person2_id))
button_person2_search.grid(row=1, column=3, padx=5, pady=5)

# Populate the dropdowns
people_data = fetch_people_data()
combo_person1_id['values'] = people_data
combo_person2_id['values'] = people_data

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
