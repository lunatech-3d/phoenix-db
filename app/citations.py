import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys
import subprocess

#Local Imports
from app.config import DB_PATH, PATHS

def fetch_sources():
    """ Fetches source titles and ids from the database for the dropdown """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT title FROM Sources")  # Fetching only titles
    sources = cur.fetchall()
    conn.close()
    return sources

def update_sources_dropdown():
    """ Updates the dropdown menu with available sources """
    sources = fetch_sources()
    source_var.set('')  # Clear the current selection
    source_dropdown['values'] = [source[0] for source in sources]  # Set only titles

def manage_sources():
    """Launch the external sources.py script."""
    subprocess.run([sys.executable, str("app".sources)])


def add_citation():
    """ Opens a form to add a new citation """
    citation_window = tk.Toplevel(window)
    citation_window.title("Add Citation")

    # Dropdown for selecting source
    tk.Label(citation_window, text="Source:").grid(row=0, column=0)
    source_var = tk.StringVar(citation_window)
    source_choices = fetch_sources()
    source_dropdown = ttk.Combobox(citation_window, textvariable=source_var, values=[f"{source[1]} (ID: {source[0]})" for source in source_choices])
    source_dropdown.grid(row=0, column=1)

    citation_window.mainloop()

def open_source_management():
    """ Opens the source management form """
    # This can link to the existing source management functionality

# Main application window setup
window = tk.Tk()
window.title("Source Citation Management")
window.geometry("800x600")  # Setting the initial size of the window

# Configure grid expansion for more control over widget spacing
window.grid_columnconfigure(0, weight=1)
window.grid_rowconfigure(0, weight=0)  # Less weight to header rows
window.grid_rowconfigure(1, weight=0)
window.grid_rowconfigure(2, weight=0)
window.grid_rowconfigure(3, weight=0)
window.grid_rowconfigure(4, weight=0)
window.grid_rowconfigure(5, weight=0)

# Dropdown for selecting source
source_var = tk.StringVar(window)
source_label = ttk.Label(window, text="Sources")
source_label.grid(row=0, column=0, sticky="e", padx=10, pady=5)
source_dropdown = ttk.Combobox(window, textvariable=source_var, width=50)
source_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

# Button to navigate to source management
manage_sources_button = ttk.Button(window, text="Manage Sources", command=manage_sources)
manage_sources_button.grid(row=0, column=2, padx=10, pady=10)
# Ensure dropdown is populated on form load

# Button to update sources from dropdown
refresh_button = ttk.Button(window, text="Refresh Sources", command=update_sources_dropdown)
refresh_button.grid(row=0, column=3, padx=10, pady=5, sticky="ew")  # Using 'sticky' to expand the button to the width of the grid column

# Citation detail entry fields
detail_label = ttk.Label(window, text="Detail:")
detail_label.grid(row=1, column=0, sticky="e", padx=10, pady=5)
detail_entry = ttk.Entry(window, width=70)
detail_entry.grid(row=1, column=1, sticky="we", columnspan=2, padx=10, pady=5)

date_label = ttk.Label(window, text="Citation Date:")
date_label.grid(row=2, column=0, sticky="e", padx=10, pady=5)
date_entry = ttk.Entry(window, width=70)
date_entry.grid(row=2, column=1, sticky="we", columnspan=2, padx=10, pady=5)

transcription_label = ttk.Label(window, text="Transcription:")
transcription_label.grid(row=3, column=0, sticky="e", padx=10, pady=5)
transcription_entry = ttk.Entry(window, width=70)
transcription_entry.grid(row=3, column=1, sticky="we", columnspan=2, padx=10, pady=5)

other_info_label = ttk.Label(window, text="Other Info:")
other_info_label.grid(row=4, column=0, sticky="e", padx=10, pady=5)
other_info_entry = ttk.Entry(window, width=70)
other_info_entry.grid(row=4, column=1, sticky="we", columnspan=2, padx=10, pady=5)

web_address_label = ttk.Label(window, text="Web Address:")
web_address_label.grid(row=5, column=0, sticky="e", padx=10, pady=5)
web_address_entry = ttk.Entry(window, width=70)
web_address_entry.grid(row=5, column=1, sticky="we", columnspan=2, padx=10, pady=5)

# Frame for checkboxes
checkbox_frame = ttk.LabelFrame(window, text="Fields to Tag Citation")
checkbox_frame.grid(row=6, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
checkbox_frame.grid_columnconfigure(0, weight=1)
checkbox_frame.grid_columnconfigure(1, weight=1)
checkbox_frame.grid_columnconfigure(2, weight=1)

# Dictionary to hold checkbox variables
checkbox_vars = {}

# List of fields from the People table
people_fields = ["first_name", "middle_name", "last_name", "title", "nick_name", 
                 "married_name", "married_to", "father", "mother", "birth_date", 
                 "birth_location", "death_date", "death_location", "death_cause", 
                 "buried_date", "buried_location", "buried_notes", "buried_source", 
                 "marriage_date", "marriage_location", "business", "obit_link", 
                 "occupation", "bio", "notes", "buried_link"]

# Generate checkboxes
for i, field in enumerate(people_fields):
    var = tk.BooleanVar()
    checkbox = ttk.Checkbutton(checkbox_frame, text=field.replace("_", " ").title(), variable=var)
    checkbox.grid(row=i // 3, column=i % 3, sticky="w")  # Arrange checkboxes in 3 columns
    checkbox_vars[field] = var  # Store variable to check state later

update_sources_dropdown()

window.mainloop()