import sqlite3
import tkinter as tk
from tkinter import ttk, font, messagebox, filedialog, Button, Toplevel
import sys
import os
import webbrowser
import re
from datetime import datetime
import subprocess
from PIL import Image, ImageTk
from context_menu import create_context_menu
from config import DB_PATH

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
        elif widget.winfo_children():  # Recursively apply to child containers
            apply_context_menu_to_all_entries(widget)
# Function to close the form

def close_form():
    window.destroy()

# Function to add a new record to the database
def add_record():
    first_name = entry_first_name.get().strip()
    middle_name = entry_middle_name.get().strip()
    last_name = entry_last_name.get().strip()
    title = entry_title.get().strip()
    nick_name = entry_nick_name.get().strip()
    married_name = entry_married_name.get().strip()
    #father = int(entry_father.get().strip()) if entry_father.get().strip() else None
    #mother = int(entry_mother.get().strip()) if entry_mother.get().strip() else None
    birth_date = entry_birth_date.get().strip()
    birth_location = entry_birth_location.get().strip()
    death_date = entry_death_date.get().strip()
    death_location = entry_death_location.get().strip()
    death_cause = entry_death_cause.get().strip()
    obit_link = entry_obit_link.get().strip()
    buried_date = entry_buried_date.get().strip()
    buried_location = entry_buried_location.get().strip()
    buried_notes = entry_buried_notes.get().strip()
    buried_source = entry_buried_source.get().strip()
    buried_link = entry_buried_link.get().strip()
    buried_block = entry_buried_block.get().strip()
    buried_tour_link = entry_buried_tour_link.get().strip()
    business = entry_business.get().strip()
    occupation = entry_occupation.get().strip()
    bio = entry_bio.get().strip()
    notes = entry_notes.get().strip()

    # Insert the record into the database
    insert_query = "INSERT INTO People (first_name, middle_name, last_name, title, nick_name, married_name, " \
               "birth_date, birth_location, death_date, death_location, death_cause, " \
               "obit_link, buried_date, buried_location, buried_notes, buried_source, buried_link, " \
               "buried_block, buried_tour_link, business, occupation, bio, notes) " \
               "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"


    data = (first_name, middle_name, last_name, title, nick_name, married_name, 
            birth_date, birth_location, death_date, death_location, death_cause, obit_link, buried_date, buried_location,
            buried_notes, buried_source, buried_link, buried_block, buried_tour_link, business, occupation, bio, notes)

    print(data)
    data = tuple("" if value == "" else value for value in data)

    try:
        cursor.execute(insert_query, data)
        connection.commit()
    except Exception as e:
        print ("SQL Error: ",e)

# Retrieve the generated ID
    generated_id = cursor.lastrowid

    # Update the record with the generated ID
    update_query = f"UPDATE People SET id = ? WHERE rowid = ?"
    update_data = (generated_id, generated_id)

    cursor.execute(update_query, update_data)
    connection.commit()
    
    messagebox.showinfo("Success", "Record added successfully.")

    # Clear the form fields
    entry_first_name.delete(0, tk.END)
    entry_middle_name.delete(0, tk.END)
    entry_last_name.delete(0, tk.END)
    entry_title.delete(0, tk.END)
    entry_nick_name.delete(0, tk.END)
    entry_married_name.delete(0, tk.END)
    # entry_father.delete(0, tk.END)
    # entry_mother.delete(0, tk.END)
    entry_birth_date.delete(0, tk.END)
    entry_birth_location.delete(0, tk.END)
    entry_death_date.delete(0, tk.END)
    entry_death_location.delete(0, tk.END)
    entry_death_cause.delete(0, tk.END)
    entry_obit_link.delete(0, tk.END)
    entry_buried_date.delete(0, tk.END)
    entry_buried_location.delete(0, tk.END)
    entry_buried_notes.delete(0, tk.END)
    entry_buried_source.delete(0, tk.END)
    entry_buried_block.delete(0, tk.END)
    entry_buried_tour_link.delete(0, tk.END)
    entry_business.delete(0, tk.END)
    entry_occupation.delete(0, tk.END)
    entry_bio.delete(0, tk.END)
    entry_notes.delete(0, tk.END)

# Create the GUI window
window = tk.Tk()
window.title("Add Record")

# Set the window size and position
window_width = 800
window_height = 500
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Create a frame for the form fields
frame_form = ttk.Frame(window)
frame_form.grid(row=0, column=1, rowspan=3)

# Create the notebook (tabbed interface)
notebook =ttk.Notebook(frame_form)
notebook.grid(row=0, column=0, sticky="nsew")

frame_newperson = ttk.Frame(notebook)
notebook.add(frame_newperson, text="New Person")

# First Name entry
label_first_name = ttk.Label(frame_newperson, text="First Name:")
label_first_name.grid(row=0, column=0, padx=5, pady=5)
entry_first_name = ttk.Entry(frame_newperson)
entry_first_name.grid(row=0, column=1, padx=5, pady=5)

# Middle Name entry
label_middle_name = ttk.Label(frame_newperson, text="Middle Name:")
label_middle_name.grid(row=0, column=2, padx=5, pady=5)
entry_middle_name = ttk.Entry(frame_newperson)
entry_middle_name.grid(row=0, column=3, padx=5, pady=5)

# Last Name entry
label_last_name = ttk.Label(frame_newperson, text="Last Name:")
label_last_name.grid(row=0, column=4, padx=5, pady=5)
entry_last_name = ttk.Entry(frame_newperson)
entry_last_name.grid(row=0, column=5, padx=5, pady=5)

# Title entry
label_title = ttk.Label(frame_newperson, text="Title:")
label_title.grid(row=1, column=0, padx=5, pady=5)
entry_title = ttk.Entry(frame_newperson)
entry_title.grid(row=1, column=1, padx=5, pady=5)

# Nick Name entry
label_nick_name = ttk.Label(frame_newperson, text="Nick Name:")
label_nick_name.grid(row=1, column=2, padx=5, pady=5)
entry_nick_name = ttk.Entry(frame_newperson)
entry_nick_name.grid(row=1, column=3, padx=5, pady=5)

# Married Name entry
label_married_name = ttk.Label(frame_newperson, text="Married Name:")
label_married_name.grid(row=1, column=4, padx=5, pady=5)
entry_married_name = ttk.Entry(frame_newperson)
entry_married_name.grid(row=1, column=5, padx=5, pady=5)

# Separator on the form
separator = ttk.Separator(frame_newperson, orient='horizontal')
separator.grid(row=2, columnspan=6, pady=10, sticky='ew')

# Father entry
# label_father = ttk.Label(frame_newperson, text="Father:")
# label_father.grid(row=3, column=2, padx=5, pady=5)
# entry_father = ttk.Entry(frame_newperson)
# entry_father.grid(row=3, column=3, padx=5, pady=5)

# Mother entry
# label_mother = ttk.Label(frame_newperson, text="Mother:")
# label_mother.grid(row=3, column=4, padx=5, pady=5)
# entry_mother = ttk.Entry(frame_newperson)
# entry_mother.grid(row=3, column=5, padx=5, pady=5)

# Birth Date entry
label_birth_date = ttk.Label(frame_newperson, text="Birth Date:")
label_birth_date.grid(row=4, column=0, padx=5, pady=5)
entry_birth_date = ttk.Entry(frame_newperson)
entry_birth_date.grid(row=4, column=1, padx=5, pady=5)

# Birth Location entry
label_birth_location = ttk.Label(frame_newperson, text="Birth Location:")
label_birth_location.grid(row=4, column=2, padx=5, pady=5)
entry_birth_location = ttk.Entry(frame_newperson)
entry_birth_location.grid(row=4, column=3, padx=5, pady=5)

# Death Date entry
label_death_date = ttk.Label(frame_newperson, text="Death Date:")
label_death_date.grid(row=5, column=0, padx=5, pady=5)
entry_death_date = ttk.Entry(frame_newperson)
entry_death_date.grid(row=5, column=1, padx=5, pady=5)

# Death Location entry
label_death_location = ttk.Label(frame_newperson, text="Death Location:")
label_death_location.grid(row=5, column=2, padx=5, pady=5)
entry_death_location = ttk.Entry(frame_newperson)
entry_death_location.grid(row=5, column=3, padx=5, pady=5)

# Death Cause entry
label_death_cause = ttk.Label(frame_newperson, text="Death Cause:")
label_death_cause.grid(row=6, column=0, padx=5, pady=5)
entry_death_cause = ttk.Entry(frame_newperson)
entry_death_cause.grid(row=6, column=1, padx=5, pady=5)

# Obituary Link entry
label_obit_link = ttk.Label(frame_newperson, text="Obituary Link:")
label_obit_link.grid(row=6, column=2, padx=5, pady=5)
entry_obit_link = ttk.Entry(frame_newperson)
entry_obit_link.grid(row=6, column=3, padx=5, pady=5)

# Buried Date entry
label_buried_date = ttk.Label(frame_newperson, text="Buried Date:")
label_buried_date.grid(row=7, column=0, padx=5, pady=5)
entry_buried_date = ttk.Entry(frame_newperson)
entry_buried_date.grid(row=7, column=1, padx=5, pady=5)

# Buried Location entry
label_buried_location = ttk.Label(frame_newperson, text="Buried Location:")
label_buried_location.grid(row=7, column=2, padx=5, pady=5)
entry_buried_location = ttk.Entry(frame_newperson)
entry_buried_location.grid(row=7, column=3, padx=5, pady=5)

# Buried Block entry (new field)
label_buried_block = ttk.Label(frame_newperson, text="Buried Block:")
label_buried_block.grid(row=7, column=4, padx=5, pady=5)
entry_buried_block = ttk.Entry(frame_newperson)
entry_buried_block.grid(row=7, column=5, padx=5, pady=5)

# Buried Notes entry
label_buried_notes = ttk.Label(frame_newperson, text="Buried Notes:")
label_buried_notes.grid(row=8, column=0, padx=5, pady=5)
entry_buried_notes = ttk.Entry(frame_newperson)
entry_buried_notes.grid(row=8, column=1, padx=5, pady=5)

# Buried Source entry
label_buried_source = ttk.Label(frame_newperson, text="Buried Source:")
label_buried_source.grid(row=8, column=2, padx=5, pady=5)
entry_buried_source = ttk.Entry(frame_newperson)
entry_buried_source.grid(row=8, column=3, padx=5, pady=5)

# Buried Link entry
label_buried_link = ttk.Label(frame_newperson, text="Buried Link:")
label_buried_link.grid(row=9, column=0, padx=5, pady=5)
entry_buried_link = ttk.Entry(frame_newperson)
entry_buried_link.grid(row=9, column=1, padx=5, pady=5)

# Buried Tour Link entry (new field)
label_buried_tour_link = ttk.Label(frame_newperson, text="Buried Tour Link:")
label_buried_tour_link.grid(row=9, column=2, padx=5, pady=5)
entry_buried_tour_link = ttk.Entry(frame_newperson)
entry_buried_tour_link.grid(row=9, column=3, padx=5, pady=5)

# Separator on the form
separator = ttk.Separator(frame_newperson, orient='horizontal')
separator.grid(row=10,columnspan=6, pady=10, sticky='ew')

# Business entry
label_business = ttk.Label(frame_newperson, text="Business:")
label_business.grid(row=11, column=0, padx=5, pady=5)
entry_business = ttk.Entry(frame_newperson)
entry_business.grid(row=11, column=1, padx=5, pady=5)

# Occupation entry
label_occupation = ttk.Label(frame_newperson, text="Occupation:")
label_occupation.grid(row=12, column=0, padx=5, pady=5)
entry_occupation = ttk.Entry(frame_newperson)
entry_occupation.grid(row=12, column=1, padx=5, pady=5)

#Bio entry
label_bio = ttk.Label(frame_newperson, text="Bio:")
label_bio.grid(row=13, column=0, padx=5, pady=5)
entry_bio = ttk.Entry(frame_newperson)
entry_bio.grid(row=13, column=1, padx=5, pady=5)

#Notes entry
label_notes = ttk.Label(frame_newperson, text="Notes:")
label_notes.grid(row=14, column=0, padx=5, pady=5)
entry_notes = ttk.Entry(frame_newperson)
entry_notes.grid(row=14, column=1, padx=5, pady=5)

apply_context_menu_to_all_entries(frame_newperson)

# Create a frame for the buttons
frame_buttons = ttk.Frame(frame_newperson)
frame_buttons.grid(row=15, columnspan=2, pady=10)  # Adjust row and columnspan as needed

# Add Button
button_add = ttk.Button(frame_buttons, text="Add", command=add_record)
button_add.grid(row=0, column=0, padx=5)

# Close Button
button_close = ttk.Button(frame_buttons, text="Close", command=close_form)
button_close.grid(row=0, column=1, padx=5)

my_custom_locations = get_custom_list('custom_locations')
my_custom_cemeteries = get_custom_list('custom_cemeteries')
create_context_menu(entry_birth_location, my_custom_locations)
create_context_menu(entry_death_location, my_custom_locations)
# create_context_menu(entry_marriage_location, my_custom_locations)
create_context_menu(entry_buried_location, my_custom_cemeteries)

# Run the GUI window
window.mainloop()

# Close the database connection
connection.close()
