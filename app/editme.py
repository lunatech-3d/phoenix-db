import sys
import folium
import geopandas as gpd
import os
import pandas as pd
import re
import requests
import subprocess
import sqlite3
import argparse
import tkinter as tk
from tkinter import ttk, font, messagebox, simpledialog, filedialog, Button, Toplevel
import traceback  # Import the traceback module for error handling
import urllib.parse  # Import the urllib.parse module for URL encoding
import webbrowser
from bs4 import BeautifulSoup
from shapely.geometry import Polygon
from folium.plugins import TimestampedGeoJson
from datetime import datetime
from PIL import Image, ImageTk

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#Local imports from the app package
from app.add_deed_dialog import AddDeedDialog
from app.edit_deed_dialog import EditDeedDialog
from app.person_linkage import open_person_linkage_popup
from app.bio_editor import create_embedded_bio_editor
from app.obituary_editor import create_embedded_obituary_editor
from app.life_events_editor import create_embedded_life_events
from app.config import DB_PATH, PATHS, USER_PREFS
from app.editbiz import EditBusinessForm
from app.education import open_add_education_window
from app.tab_launcher import launch_tab

from app.family_linkage import open_family_linkage_window  # Importing family linkage module

from app.findagrave_agent_direct import (
    findagrave_direct_search,
    show_findagrave_picker,
    clean_location_for_findagrave
)

from app.census_records import (
    initialize_census_section,
    load_census_records,
    add_census_record,
    edit_census_record,
    save_census_record,
    delete_census_record
)
from app.tax_records import (
    initialize_tax_section,
    load_tax_records,
    add_tax_record,
    edit_tax_record,
    save_tax_record,
    delete_tax_record
)
from app.legal_notices import (
    initialize_legal_notice_section,
    load_legal_notices,
    add_legal_notice,
    edit_legal_notice,
    delete_legal_notice
)
from app.deeds import (
    initialize_deed_section,
    load_deed_records,
    add_deed_record,
    edit_deed_record,
    delete_deed_record    
)

from app.context_menu import create_context_menu
from app.date_utils import (
    parse_date_input,
    format_date_for_display,
    add_date_format_menu,
    date_sort_key,
)
from app.map_control import MapController
from app.user_prefs import load_tab_prefs

parser = argparse.ArgumentParser(description="Edit a person or add a new one")
parser.add_argument("id", nargs="?", help="Person ID or related person ID")
parser.add_argument("--new-child", action="store_true", help="Add a new child")
parser.add_argument("--new-father", action="store_true", help="Add a new father")
parser.add_argument("--new-mother", action="store_true", help="Add a new mother")
parser.add_argument("--new-person", action="store_true", help="Add a new person")
args = parser.parse_args()

if args.new_child:
    params = []
    if args.new_father and args.id:
        params.extend(["--father", str(args.id)])
    elif args.new_mother and args.id:
        params.extend(["--mother", str(args.id)])
    launch_tab("addme", *params)
    sys.exit(0)
elif args.new_father and args.id:
    launch_tab("addme", "--father", str(args.id))
    sys.exit(0)
elif args.new_mother and args.id:
    launch_tab("addme", "--mother", str(args.id))
    sys.exit(0)
elif args.new_person:
    launch_tab("addme")
    sys.exit(0)


# Connect to the database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()
connection_open = True

# Create a single instance of MapController
#map_controller = MapController()

spouse_list = []
global related_people_tree
global status_symbol
related_people_tree = None

def open_link(url):
    if url:
        webbrowser.open(url, new=2)
    else:
        messagebox.showinfo("Information", "No URL provided.")

def convert_to_sortable_date(date_str):
    if not date_str:
        return None

    if isinstance(date_str, int):
        return f"{date_str:04d}-01-01"

    date_str = date_str.strip()

    # Try different formats, and log unrecognized formats for diagnostics
    try:
        return datetime.strptime(date_str, "%m-%d-%Y").strftime("%Y-%m-%d")
    except ValueError:
        pass

    try:
        return datetime.strptime(date_str, "%m-%Y").strftime("%Y-%m-01")
    except ValueError:
        pass

    try:
        return datetime.strptime(date_str, "%Y").strftime("%Y-01-01")
    except ValueError:
        pass

    # Log or print to identify what's causing issues
    print(f"Unrecognized date format: {date_str}")
    return None

def format_date(date_str):
    """Format date string for display."""
    if not date_str:
        return ""

    # Convert the input to a with conn:
    if isinstance(date_str, int):
        date_str = str(date_str)

    # Handle full date format
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%m-%d-%Y")
    except ValueError:
        pass

    # Handle year-month format
    try:
        return datetime.strptime(date_str, "%Y-%m").strftime("%b %Y")
    except ValueError:
        pass

    # For other formats or plain year, return as is
    return date_str

def remove_selected_child():
    selected = children_tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a child to remove.")
        return

    item = children_tree.item(selected[0])
    child_id = item['values'][0]
    child_name = f"{item['values'][1]} {item['values'][2]} {item['values'][3]}".strip()

    cursor.execute("SELECT first_name, middle_name, last_name FROM People WHERE id = ?", (record_id,))
    parent_record = cursor.fetchone()
    parent_name = " ".join(filter(None, parent_record)) if parent_record else "this parent"

    confirm = messagebox.askyesno(
        "Confirm Unlink",
        f"Are you sure you want to remove {child_name} as a child of {parent_name}?"
    )
    if not confirm:
        return

    try:
        cursor.execute("UPDATE People SET father = NULL, mother = NULL WHERE id = ?", (child_id,))
        connection.commit()
        messagebox.showinfo("Unlinked", f"{child_name} is no longer linked to {parent_name}.")
        if has_spouses:
            update_children_tree_on_spouse_selection(None)
        else:
            display_children()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to remove child: {e}")

def update_remove_button_state(event=None):
    has_items = len(children_tree.get_children()) > 0
    has_selection = bool(children_tree.selection())
    if has_items and has_selection:
        button_remove_child.config(state='normal')
    else:
        button_remove_child.config(state='disabled')


def get_custom_list(list_name):
    cursor.execute("SELECT list_values FROM CustomLists WHERE list_name = ?", (list_name,))
    result = cursor.fetchone()
    if result:
        return result[0].split('|')  # Splitting using the pipe delimiter
    else:
        return []

# Function to close the form
def close_form():
    window.destroy()

# Where close_connection is a function defined as:
def close_connection():
    global connection_open
    if connection_open:
        connection.close()
        connection_open = False
    window.destroy() # Close the form    

# Give the User the ability to use a right-mouse-click to access content on the clipboard
def apply_context_menu_to_all_entries(container):
    for widget in container.winfo_children():
        if isinstance(widget, ttk.Entry):
            create_context_menu(widget)
        elif widget.winfo_children():
            apply_context_menu_to_all_entries(widget)  # Recursively apply to child containers

# Function to add a Residence Record for the current person
def add_residence_rec(event=None):
    selected_item = tree.focus()
    record_id = tree.item(selected_item)['values'][0]
    launch_tab("addresident", str(record_id))
    
def update_spouse_name(person_id):
    # Query the Marriages table for the current person's spouse(s) along with birth and death dates
    cursor.execute("""
        SELECT P.first_name, P.middle_name, P.last_name, P.birth_date, P.death_date
        FROM People P
        JOIN Marriages M ON P.id = M.person1_id OR P.id = M.person2_id
        WHERE (M.person1_id = ? OR M.person2_id = ?) AND P.id != ?
        """, (person_id, person_id, person_id))

    spouses = cursor.fetchall()

    # Handle multiple spouses (just taking the first spouse for simplicity)
    if spouses:
        # Extract the details
        first_name, middle_name, last_name, birth_date, death_date = spouses[0]
        # Construct the name part
        name_parts = [first_name, middle_name, last_name]
        full_name = ' '.join(name for name in name_parts if name)
        # Construct the birth and death date parts if available
        date_details = []
        if birth_date:
            date_details.append(f"(born: {birth_date}")
        if death_date:
            date_details.append(f"  died: {death_date})")
        # Combine name and date details
        if date_details:
            spouse_details_str = f"{full_name} - {' '.join(date_details)}"
        else:
            spouse_details_str = full_name
    else:
        spouse_details_str = ''

    # Update the label text
    label_married_to_name.config(text=spouse_details_str)

def update_father_name():
    father_id = father_var.get()
    father_details_str = ''  # Initialize the variable with a default value
    if father_id.isdigit():
        query = f"SELECT first_name, middle_name, last_name, birth_date, death_date FROM People WHERE id = {father_id}"
        cursor.execute(query)
        father_details = cursor.fetchone()
        if father_details is not None:
            # Extract the details
            first_name, middle_name, last_name, birth_date, death_date = father_details
            # Construct the name part
            name_parts = [first_name, middle_name, last_name]
            full_name = ' '.join([name for name in name_parts if name is not None])
            # Construct the birth and death date parts if available
            date_details = []
            if birth_date:
                date_details.append(f"(born: {birth_date}")
            if death_date:
                date_details.append(f"  died: {death_date})")
            # Combine name and date details
            if date_details:
                father_details_str = f"{full_name} - {' '.join(date_details)}"
            else:
                father_details_str = full_name

    label_father_name.config(text=father_details_str)

def update_mother_name():
    mother_id = mother_var.get()
    mother_details_str = ''  # Initialize the variable with a default value
    if mother_id.isdigit():
        query = f"SELECT first_name, middle_name, last_name, birth_date, death_date FROM People WHERE id = {mother_id}"
        cursor.execute(query)
        mother_details = cursor.fetchone()
        if mother_details is not None:
            # Extract the details
            first_name, middle_name, last_name, birth_date, death_date = mother_details
            # Construct the name part
            name_parts = [first_name, middle_name, last_name]
            full_name = ' '.join([name for name in name_parts if name is not None])
            # Construct the birth and death date parts if available
            date_details = []
            if birth_date:
                date_details.append(f"(born: {birth_date}")
            if death_date:
                date_details.append(f"  died: {death_date})")
            # Combine name and date details
            if date_details:
                mother_details_str = f"{full_name} - {' '.join(date_details)}"
            else:
                mother_details_str = full_name

    label_mother_name.config(text=mother_details_str)


def open_spouse_record(event=None):
    spouse_id = entry_married_to.get()
    if spouse_id.isdigit():
        window.destroy()
        launch_tab("editme", str(spouse_id))

def open_father_record(event=None):
    father_id = father_var.get()
    if father_id.isdigit():
        window.destroy()
        launch_tab("editme", str(father_id))

def open_mother_record(event=None):
    mother_id = mother_var.get()
    if mother_id.isdigit():
        window.destroy()
        launch_tab("editme", str(mother_id))

def refresh_father_var():
    cursor.execute("SELECT father FROM People WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    father_var.set(row[0] if row and row[0] is not None else "")
    update_father_name()

def refresh_mother_var():
    cursor.execute("SELECT mother FROM People WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    mother_var.set(row[0] if row and row[0] is not None else "")
    update_mother_name()

def refresh_parent_vars():
    """Refresh both father and mother fields."""
    refresh_father_var()
    refresh_mother_var()

def open_spouse_record():
    selected_spouse_info = spouse_dropdown.get()
    if selected_spouse_info:
        spouse_id = selected_spouse_info.split(':')[0].strip()
        if spouse_id.isdigit():
            window.destroy()
            launch_tab("editme", str(spouse_id))
            
def open_child_record(event=None):
    # Get the selected item from the Treeview
    selected_item = children_tree.focus()
    record_id = children_tree.item(selected_item)['values'][0]  # Assuming the first value is the ID
    window.destroy()
    launch_tab("editme", str(record_id))        

# Function to update the record in the database
def update_record():
    record_id_local = entry_id_var.get().strip()

    # Retrieve the record from the database
    query = f"SELECT * FROM People WHERE id = {record_id_local}"
    cursor.execute(query)
    record = cursor.fetchone()

    # If the record exists, update its fields with the form data
    if record:
        update_query = f"UPDATE People SET " \
                       f"first_name = ?, middle_name = ?, last_name = ?, " \
                       f"title = ?, nick_name = ?, married_name = ?, " \
                       f"father = ?, mother = ?, birth_date = ?, birth_location = ?, " \
                       f"death_date = ?, death_location = ?, death_cause = ?, " \
                       f"buried_date = ?, buried_location = ?, buried_notes = ?, buried_source = ?, " \
                       f"business = ?, " \
                       f"occupation = ?, notes = ?, buried_link =?, buried_block =?, " \
                       f"buried_tour_link = ? WHERE id = {record_id_local}"

        data = (
            entry_first_name.get(),
            entry_middle_name.get(),
            entry_last_name.get(),
            entry_title.get(),
            entry_nick_name.get(),
            entry_married_name.get(),
            father_var.get(),
            mother_var.get(),
            entry_birth_date.get(),
            entry_birth_location.get(),
            entry_death_date.get(),
            entry_death_location.get(),
            entry_death_cause.get(),
            entry_buried_date.get(),
            entry_buried_location.get(),
            entry_buried_notes.get(),
            entry_buried_source.get(),
            entry_business.get(),
            entry_occupation.get(),
            entry_notes.get(),
            entry_buried_link.get(),
            entry_buried_block.get(),
            entry_cem_tour_link.get()
        )

        cursor.execute(update_query, data)
        connection.commit()
        
        messagebox.showinfo("Success", "Record updated successfully.")
    else:
        messagebox.showerror("Error", "Record not found.")
    #update_spouse_name(person_record[0])
    #update_father_name()

# Retrieve the record ID passed as a command-line argument
record_id = args.id

# Retrieve the record from the database
query = f"SELECT id, first_name, middle_name, last_name, title, nick_name, married_name, father, mother, " \
        f"birth_date, birth_location, death_date, death_location, death_cause, buried_date, buried_location, " \
        f"buried_notes, buried_source, business, occupation, bio, notes, buried_link, buried_block, " \
        f"buried_tour_link FROM People WHERE id = {record_id}"
cursor.execute(query)
person_record = cursor.fetchone()
#print("Fetched Person Record:", person_record)


# Retrieve the photo from the database
query = f"SELECT image_path FROM Photos WHERE person_id = {record_id}"
cursor.execute(query)
photo_record = cursor.fetchone()
image_path = photo_record[0] if photo_record else None

query = f"SELECT * FROM Photos WHERE person_id = {record_id}"
cursor.execute(query)
record = cursor.fetchone()


def display_image(frame_photo, image_path, add_photo_button):
    if image_path is not None:
        if os.path.isfile(image_path):
            img = Image.open(image_path)
            # Calculate the ratio to keep aspect ratio
            ratio = 250.0 / img.height
            
            # Calculate the width using the same ratio
            width = int(img.width * ratio)
            
            # Resize the image
            img = img.resize((width, 250), Image.LANCZOS)
            img = ImageTk.PhotoImage(img)
            
            add_photo_button.grid_remove()  # This is how you "hide" widgets in tkinter

            # If an image exists, add it to the GUI
            img_label = ttk.Label(frame_photo, image=img)
            img_label.image = img  # keep a reference to the image
            img_label.grid(row=0, column=0)
        else:
            error_label = ttk.Label(frame_photo, text="No image found")
            error_label.grid(row=0, column=0)
    else:
        # Show the 'Add Photo' button if no image path exists in the database
        add_photo_button.grid(row=0, column=2)


def resize_image(input_image_path, size):
    original_image = Image.open(input_image_path)
    width, height = original_image.size
    if height > size:
        ratio = size/height
        new_width = int(width * ratio)
        resized_image = original_image.resize((new_width, size), Image.ANTIALIAS)
        resized_image.save(input_image_path)

        
def add_a_photo():
    image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.png;*.tif")])
    if image_path:
        # Extract just the filename
        filename = os.path.basename(image_path)

        # Define the relative path where your images are expected to be located
        relative_path = f"assets/pics/thumb/{filename}"

        # Store only the relative path in the database
        query = """
            INSERT INTO Photos (person_id, image_path)
            VALUES (?, ?)
        """
        try:
            cursor.execute(query, (record_id, relative_path))
            connection.commit()
            messagebox.showinfo("Success", "The photo was successfully added to the database.")
            display_image(frame_photo, relative_path, add_photo_button)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while writing to the database: {str(e)}")
    else:
        messagebox.showinfo("No File Selected", "No file was selected. Please try again.")


def open_add_menu(event=None):
    """Display a menu of actions to add related information."""
    menu = tk.Menu(window, tearoff=0)
    menu.add_command(
        label="Add Education",
        command=lambda: open_add_education_window(record_id, connection),
    )
    menu.add_command(
        label="Add Deed",
        command=lambda: AddDeedDialog(window, record_id),
    )
    if event:
        menu.tk_popup(event.x_root, event.y_root)
    else:
        x = add_info_btn.winfo_rootx()
        y = add_info_btn.winfo_rooty() + add_info_btn.winfo_height()
        menu.tk_popup(x, y)

def open_photo_menu(event=None):
    """Display a dynamic menu for the photo area."""
    prefs = load_tab_prefs()
    menu = tk.Menu(window, tearoff=0)

    def launch(module, args=None):
        args = args or []
        subprocess.Popen([sys.executable, "-m", module, *args])

    # Records submenu example
    if prefs.get("records"):
        records_menu = tk.Menu(menu, tearoff=0)
        census_args = [
            str(record_id),
            person_record[1] or "",
            person_record[2] or "",
            person_record[3] or "",
            person_record[6] or "",
        ]
        records_menu.add_command(
            label="Census",
            command=lambda: launch("app.addcensus", census_args),
        )
        records_menu.add_command(
            label="Deeds",
            command=lambda: launch("app.add_deed_dialog"),
        )
        menu.add_cascade(label="Records", menu=records_menu)

    tab_modules = {
        "family": [("Family Tree", "app.buildatree")],
        "residence": [("Add Residence", "app.addresident")],
        "education": [("Add Education", "app.education")],
        "business": [("Businesses", "app.business")],
        "orgs": [("Organizations", "app.orgs")],
        "media": [("Map Viewer", "app.map_viewer")],
        "sources": [("Sources", "app.sources")],
    }

    for tab, items in tab_modules.items():
        if prefs.get(tab):
            for label, module in items:
                menu.add_command(label=label, command=lambda m=module: launch(m))

    if event:
        menu.tk_popup(event.x_root, event.y_root)
    else:
        x = photo_menu_btn.winfo_rootx()
        y = photo_menu_btn.winfo_rooty() + photo_menu_btn.winfo_height()
        menu.tk_popup(x, y)


def add_a_spouse():
    launch_tab("marriagerecord_add", wait=True)

# -------------------------------   
# START OF THE ORGS TAB CODE
# -------------------------------

def create_orgs_tab(notebook, person_id):
    
    # Add the Organizations tab
    frame_orgs = ttk.Frame(notebook)
    notebook.add(frame_orgs, text='Orgs')

    # Create a table (treeview) for the records
    columns = ("membership_id", "Organization", "Role", "Start Date", "End Date", "Notes")
    table = ttk.Treeview(frame_orgs, columns=columns, show='headings', height=8)

    table.heading("Organization", text="Organization")
    table.heading("Role", text="Role")
    table.heading("Start Date", text="Start Date")
    table.heading("End Date", text="End Date")
    table.heading("Notes", text="Notes")

    # Define column widths
    table.column("membership_id", width=0, stretch=False)
    table.column("Organization", width=250)
    table.column("Role", width=200)
    table.column("Start Date", width=100)
    table.column("End Date", width=100)
    table.column("Notes", width=600)

    table.pack(anchor='w',fill='y', expand=False, padx=5, pady=5)

    # Add a frame for buttons
    button_frame = ttk.Frame(frame_orgs)
    button_frame.pack(fill='x', padx=5, pady=(0, 10))

    def launch_add_membership(person_id, refresh_callback):
        print(f"Launching members.py with person_id={person_id}")
        launch_tab("members", "--for-person", str(person_id), wait=True)
        print("Returned from subprocess — refreshing memberships")
        refresh_callback()

    ttk.Button(button_frame, text="Add Membership",
           command=lambda: launch_add_membership(person_id, refresh_org_memberships)).pack(side="left", padx=5)

    # Query the database for Organization and Membership records
    query = f"""
        SELECT Membership.id, Org.org_name, Membership.start_date, Membership.end_date, Membership.role, Membership.notes
        FROM Membership
        JOIN Org ON Membership.org_id = Org.org_id
        WHERE Membership.person_id = {person_id}
        ORDER BY Org.org_name, Membership.start_date
    """
    cursor.execute(query)
    records = cursor.fetchall()

    
    def launch_edit_membership(refresh_callback):
        selected = table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a membership to edit.")
            return
        membership_id = table.focus()
        launch_tab("members", "--edit-membership", str(membership_id), wait=True)
        refresh_callback()

    btn_edit = ttk.Button(button_frame, text="Edit Membership",
                      command=lambda: launch_edit_membership(refresh_org_memberships))
    btn_edit.pack(side="left", padx=5)

    def launch_delete_membership(refresh_callback):
        selected = table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a membership to delete.")
            return
        membership_id = table.focus()
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this membership?")
        if confirm:
            cursor.execute("DELETE FROM Membership WHERE id = ?", (membership_id,))
            connection.commit()
            refresh_callback()

    btn_delete = ttk.Button(button_frame, text="Delete Membership",
                        command=lambda: launch_delete_membership(refresh_org_memberships))
    btn_delete.pack(side="left", padx=5)

    for record in records:
        membership_id = record[0]
        org_name = record[1]
        start_date = record[2]
        end_date = record[3]
        role = record[4] or ""
        notes = record[5] or ""
        table.insert('', 'end', iid=str(membership_id), values=(membership_id, org_name, role, start_date, end_date, notes or ""))

    if not records:
        btn_edit["state"] = "disabled"
        btn_delete["state"] = "disabled"

    # Add a vertical scrollbar to the table
    scrollbar = ttk.Scrollbar(frame_orgs, orient='vertical', command=table.yview)
    scrollbar.pack(side='right', fill='y')
    table.configure(yscrollcommand=scrollbar.set)

    # Event to handle double-click on an item
    def on_item_double_click(event):
        selected_id = table.focus()  # Get the 'iid' of the selected item, which is the membership_id
        # Call the function to open the edit window, passing the membership_id
        launch_tab("members", "--edit-membership", str(selected_id), wait=True)
        refresh_org_memberships()

    table.bind("<Double-1>", on_item_double_click)  # Bind double-click event

    def refresh_org_memberships():
        table.delete(*table.get_children())  # Clear table
        cursor.execute(query)  # Re-execute same query
        refreshed_records = cursor.fetchall()
        for record in refreshed_records:
            membership_id = record[0]
            org_name = record[1]
            start_date = record[2]
            end_date = record[3]
            role = record[4]
            notes = record[5]
            table.insert('', 'end', iid=str(membership_id), values=(membership_id, org_name, role, start_date, end_date, notes))

        if len(refreshed_records) == 0:
            btn_edit["state"] = "disabled"
            btn_delete["state"] = "disabled"
        else:
            btn_edit["state"] = "normal"
            btn_delete["state"] = "normal"

# -------------------------------
# START OF THE INSTITUTION TAB CODE
# -------------------------------

institution_tab_frame = None
institution_tree = None
_institution_notebook = None
_institution_person_id = None

# Helper functions to check if a person has data for specific tabs. These are
# used so tabs are displayed when data exists even if the user's default
# preference is to hide the tab.

def has_family_data(pid):
    """Return True if the person has any recorded family relationships."""
    cursor.execute(
        "SELECT father, mother, married_to FROM People WHERE id=?",
        (pid,),
    )
    row = cursor.fetchone()
    if row and any(row):
        return True
    cursor.execute(
        "SELECT 1 FROM People WHERE father=? OR mother=? LIMIT 1",
        (pid, pid),
    )
    return cursor.fetchone() is not None


def has_residence_data(pid):
    cursor.execute(
        "SELECT 1 FROM ResHistory WHERE person_id=? LIMIT 1",
        (pid,),
    )
    return cursor.fetchone() is not None


def has_education_data(pid):
    cursor.execute(
        "SELECT 1 FROM Education WHERE person_id=? LIMIT 1",
        (pid,),
    )
    return cursor.fetchone() is not None


def has_business_data(pid):
    cursor.execute(
        "SELECT 1 FROM BizOwnership WHERE person_id=? LIMIT 1",
        (pid,),
    )
    if cursor.fetchone():
        return True
    cursor.execute(
        "SELECT 1 FROM BizEmployment WHERE person_id=? LIMIT 1",
        (pid,),
    )
    return cursor.fetchone() is not None


def has_records_data(pid):
    checks = [
        ("SELECT 1 FROM Census WHERE person_id=? LIMIT 1", (pid,)),
        ("SELECT 1 FROM Tax_Records WHERE people_id=? LIMIT 1", (pid,)),
        ("SELECT 1 FROM LegalNoticeParties WHERE person_id=? LIMIT 1", (pid,)),
        ("SELECT 1 FROM DeedParties WHERE person_id=? LIMIT 1", (pid,)),
    ]
    for q, params in checks:
        cursor.execute(q, params)
        if cursor.fetchone():
            return True
    return False


def has_orgs_data(pid):
    cursor.execute(
        "SELECT 1 FROM Membership WHERE person_id=? LIMIT 1",
        (pid,),
    )
    return cursor.fetchone() is not None


def has_media_data(pid):
    cursor.execute(
        "SELECT 1 FROM MediaPerson WHERE person_id=? LIMIT 1",
        (pid,),
    )
    return cursor.fetchone() is not None


def has_institution_data(pid):
    cursor.execute(
        "SELECT 1 FROM Inst_Staff WHERE person_id=? UNION SELECT 1 FROM Inst_GroupMember WHERE person_id=? UNION SELECT 1 FROM Inst_Event WHERE person_id=? LIMIT 1",
        (pid, pid, pid),
    )
    return cursor.fetchone() is not None

def refresh_institution_tab():
    global institution_tab_frame, institution_tree
    if _institution_notebook is None or _institution_person_id is None:
        return
    cursor.execute(
        """
        SELECT a.inst_affiliation_id, i.inst_name, a.inst_affiliation_role,
               a.inst_affiliation_start_date, a.inst_affiliation_end_date,
               a.inst_affiliation_notes
          FROM Inst_Affiliation a
          JOIN Institution i ON a.inst_id = i.inst_id
         WHERE a.person_id = ?
         ORDER BY a.inst_affiliation_start_date
        """,
        (_institution_person_id,),
    )
    rows = cursor.fetchall()

    if institution_tab_frame is None:
        if rows:
            create_institution_tab(_institution_notebook, _institution_person_id)
        return

    institution_tree.delete(*institution_tree.get_children())
    for row in rows:
        institution_tree.insert("", "end", values=row)

    if not rows and institution_tab_frame is not None:
        idx = _institution_notebook.index(institution_tab_frame)
        _institution_notebook.forget(idx)
        institution_tab_frame = None

def create_institution_tab(notebook, person_id):
    global institution_tab_frame, institution_tree, _institution_notebook, _institution_person_id
    _institution_notebook = notebook
    _institution_person_id = person_id
    if institution_tab_frame is not None:
        return institution_tab_frame

    frame = ttk.Frame(notebook)
    institution_tab_frame = frame
    notebook.add(frame, text="Institutions")

    columns = ("affil_id", "Institution", "Role", "Start", "End", "Notes")
    institution_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
    for col in columns:
        institution_tree.heading(col, text=col)
        width = 80 if col in ("Start", "End") else 150
        if col == "affil_id":
            width = 0
        institution_tree.column(col, width=width, anchor="w", stretch=(col != "affil_id"))
    institution_tree.pack(fill="both", expand=True, padx=5, pady=5)

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x", padx=5, pady=5)

    def add_affiliation():
        inst_id = simpledialog.askinteger("Institution ID", "Enter Institution ID:")
        if inst_id is None:
            return
        role = simpledialog.askstring("Role", "Enter role (optional):")
        cursor.execute(
            "INSERT INTO Inst_Affiliation (inst_id, person_id, inst_affiliation_role) VALUES (?, ?, ?)",
            (inst_id, person_id, role),
        )
        connection.commit()
        refresh_institution_tab()

    def delete_affiliation():
        selected = institution_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record to delete.")
            return
        affil_id = institution_tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm Delete", "Delete selected affiliation?"):
            cursor.execute(
                "DELETE FROM Inst_Affiliation WHERE inst_affiliation_id=?",
                (affil_id,),
            )
            connection.commit()
            refresh_institution_tab()

    ttk.Button(btn_frame, text="Add", command=add_affiliation).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Delete", command=delete_affiliation).pack(side="left", padx=5)

    refresh_institution_tab()
    return frame

# -------------------------------   
# START OF THE RECORDS TAB CODE
# -------------------------------

# Functions for the Tax records

def view_geojson_map(event, tax_tree, person_id):
    """Handle double-click on tax record to view map"""
    region = tax_tree.identify('region', event.x, event.y)
    column = tax_tree.identify_column(event.x)
    if region != 'cell' or column != '#2':  # Check if click is in Map column
        return
    
    item = tax_tree.selection()[0]
    values = tax_tree.item(item)['values']
    
    # Check if Map column has globe icon
    if values[1] != '🌎':  # Index 1 is the Map column
        return

    try:
        record_id = values[0]  # Hidden record_id
        map_controller.logger.info(f"Attempting to display tax property for record_id: {record_id}")
        
        # Make sure map is showing
        map_controller.activate_map()
        
        # Add this property to the map
        success = map_controller.display_tax_property(record_id)
        
        if not success:
            messagebox.showerror("Error", "Could not display property on map")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to display map: {e}")
        print(f"Error details: {str(e)}", flush=True)


def on_double_click(event, map_controller):
    """Handle double-click on tax tree to display property on map"""
    tree = event.widget
    item = tree.identify('item', event.x, event.y)
    column = tree.identify_column(event.x)
    
    if item and column == '#2':  # #2 is the Map column (after hidden record_id)
        values = tree.item(item)['values']
        
        # Check if there is a map icon, indicating the presence of GeoJSON data
        if values[1] == '🌎':
            record_id = values[0]  # The hidden record_id in the first column
            
            # Display property on the map and activate the map in the browser
            if map_controller.display_tax_property(record_id):
                map_controller.activate_map()
            else:
                print(f"Failed to display property for record_id: {record_id}")


def format_legal_description(section, quarter, quarter_quarter, half, acres, desc_text):
    """Format legal description for display
    
    Args:
        section (str): Section number
        quarter (str): Quarter section designation
        quarter_quarter (str): Quarter of quarter designation
        half (str): Half designation
        acres (float): Number of acres
        desc_text (str): Full description text if available
        
    Returns:
        str: Formatted description string
    """
    if desc_text:
        return desc_text
        
    parts = []
    if acres:
        parts.append(f"{float(acres):.2f} acres")
    if half:
        parts.append(half)
    if quarter_quarter:
        parts.append(quarter_quarter)
    if quarter:
        parts.append(quarter)
    if section:
        parts.append(f"Section {section}")
        
    return " of ".join(parts) if parts else ""

# ----------------------------------------
# Now Create the Business Tab for everything
# ---------------------------------------- 

def create_business_tab(notebook, person_id):

    connection = sqlite3.connect("phoenix.db")
    cursor = connection.cursor()

    frame_biz = ttk.Frame(notebook)
    notebook.add(frame_biz, text='Business Roles')
 
    #
    # OWNERSHIP TREE
    #

    owner_frame = ttk.LabelFrame(frame_biz, text="Business Ownership")
    owner_frame.pack(fill='x', padx=10, pady=5)

    columns = (
        "biz_ownership_id", "biz_name", "ownership_type", "title",
        "start_date", "end_date", "notes"
    )
    owner_tree = ttk.Treeview(owner_frame, columns=columns, show='headings', height=6)

    for col in columns:
        owner_tree.heading(col, text=col.replace("_", " ").title())
        width = 0 if col == "biz_ownership_id" else 100
        if col == "notes":
            width = 250
        elif col == "biz_name":
            width = 180
        owner_tree.column(col, width=width, anchor="w", stretch=(col != "biz_ownership_id"))

    owner_tree.pack(fill='x', padx=5, pady=(5, 0))

    # Buttons container
    owner_button_frame = ttk.Frame(owner_frame)
    owner_button_frame.pack(fill='x', padx=5, pady=5)

    def refresh_ownerships():
        owner_tree.delete(*owner_tree.get_children())
        cursor.execute("""
            SELECT 
                o.biz_ownership_id, 
                b.biz_name, 
                o.ownership_type, 
                o.title,
                o.start_date, 
                o.start_date_precision,
                o.end_date, 
                o.end_date_precision,
                o.notes
            FROM BizOwnership o
            JOIN Biz b ON o.biz_id = b.biz_id
            WHERE o.person_id = ?
            ORDER BY o.start_date
        """, (person_id,))
        for row in cursor.fetchall():
            (
                ownership_id, biz_name, ownership_type, title,
                start_date, start_prec, end_date, end_prec, notes
            ) = row

            start_fmt = format_date_for_display(start_date, start_prec)
            end_fmt = format_date_for_display(end_date, end_prec)

            owner_tree.insert('', 'end', iid=str(ownership_id), values=(
                ownership_id, biz_name, ownership_type, title,
                start_fmt, end_fmt, notes
            ))

    def launch_add_ownership():
        launch_tab("biz_ownership", "--for-person", str(person_id), wait=True)
        refresh_ownerships()

    def launch_edit_ownership():
        selected = owner_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an owner record to edit.")
            return
        ownership_id = owner_tree.item(selected[0])["values"][0]
        launch_tab("biz_ownership", "--edit-ownership", str(ownership_id), wait=True)
        refresh_ownerships()

    def launch_delete_ownership():
        selected = owner_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an owner record to delete.")
            return
        ownership_id = owner_tree.item(selected[0])["values"][0]
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this ownership record?")
        if confirm:
            cursor.execute("DELETE FROM BizOwnership WHERE biz_ownership_id = ?", (ownership_id,))
            connection.commit()
            refresh_ownerships()

    # Action buttons
    ttk.Button(owner_button_frame, text="Add Ownership", command=launch_add_ownership).pack(side="left", padx=5)
    ttk.Button(owner_button_frame, text="Edit Ownership", command=launch_edit_ownership).pack(side="left", padx=5)
    ttk.Button(owner_button_frame, text="Delete Ownership", command=launch_delete_ownership).pack(side="left", padx=5)

    refresh_ownerships()


    #
    # --- EMPLOYMENT TREE ---
    #
    employee_frame = ttk.LabelFrame(frame_biz, text="Employment History")
    employee_frame.pack(fill='x', padx=10, pady=5)

    emp_columns = (
        "biz_employment_id", "biz_name", "job_title",
        "start_date", "end_date", "notes", "url"
    )
    employee_tree = ttk.Treeview(employee_frame, columns=emp_columns, show='headings', height=6)

    for col in emp_columns:
        employee_tree.heading(col, text=col.replace("_", " ").title())
        width = 0 if col == "biz_employment_id" else 100
        if col == "notes":
            width = 250
        elif col == "biz_name":
            width = 180
        employee_tree.column(col, width=width, anchor="w", stretch=(col != "biz_employment_id"))

    employee_tree.pack(fill='x', padx=5, pady=(5, 0))

    # Buttons container
    employee_button_frame = ttk.Frame(employee_frame)
    employee_button_frame.pack(fill='x', padx=5, pady=5)

    def refresh_employments():
        employee_tree.delete(*employee_tree.get_children())
        cursor.execute("""
            SELECT 
                e.id,           -- primary key of employment record
                e.biz_id,       -- foreign key to Biz table
                b.biz_name,
                e.job_title,
                e.start_date,
                e.start_date_precision,
                e.end_date,
                e.end_date_precision,
                e.notes,
                e.url
            FROM BizEmployment e
            JOIN Biz b ON e.biz_id = b.biz_id
            WHERE e.person_id = ?
            ORDER BY e.start_date
        """, (person_id,))
        
        for row in cursor.fetchall():
            (
                emp_id, biz_id, biz_name, job_title,
                start_date, start_prec, end_date, end_prec, notes, url
            ) = row

            start_fmt = format_date_for_display(start_date, start_prec)
            end_fmt = format_date_for_display(end_date, end_prec)

            # Store emp_id as Treeview ID; don't show biz_id (internal use only)
            employee_tree.insert('', 'end', iid=str(emp_id), values=(
                emp_id, biz_name, job_title, start_fmt, end_fmt, notes, url
            ))

    def launch_add_employment():
        launch_tab("biz_employees", "--for-person", str(person_id), wait=True)
        refresh_employments()

    def launch_edit_employment():
        selected = employee_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an employment record to edit.")
            return
        emp_id = employee_tree.item(selected[0])["values"][0]
        launch_tab("biz_employees", "--edit-employment", str(emp_id), wait=True)
        refresh_employments()

    def launch_delete_employment():
        selected = employee_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an employment record to delete.")
            return
        emp_id = employee_tree.item(selected[0])["values"][0]
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this employment record?")
        if confirm:
            cursor.execute("DELETE FROM BizEmployment WHERE id = ?", (emp_id,))
            connection.commit()
            refresh_employments()

    # Action buttons
    ttk.Button(employee_button_frame, text="Add Employment", command=launch_add_employment).pack(side="left", padx=5)
    ttk.Button(employee_button_frame, text="Edit Employment", command=launch_edit_employment).pack(side="left", padx=5)
    ttk.Button(employee_button_frame, text="Delete Employment", command=launch_delete_employment).pack(side="left", padx=5)

    refresh_employments()



# ----------------------------------------
# Now Create the Records Tab for everything
# ----------------------------------------
    
def create_records_tab(notebook, person_id):
    """Create the Records tab with separate trees for Census and Tax records"""
    frame_records = ttk.Frame(notebook)
    notebook.add(frame_records, text='Records')

    #Create and load the tree for Census records
    census_tree = initialize_census_section(frame_records, connection, person_id)
    tax_tree = initialize_tax_section(frame_records, connection, person_id)
    legal_notice_tree = initialize_legal_notice_section(frame_records, connection, person_id)
    deed_tree = initialize_deed_section(frame_records, connection, person_id)
    
           
    # Load initial records
    load_census_records(cursor, census_tree, person_id)
    load_tax_records(cursor, tax_tree, person_id)
    load_legal_notices(cursor, legal_notice_tree, person_id)
    load_deed_records(cursor, deed_tree, person_id)   

    return frame_records
        

# -------------------------------   
# START OF THE FAMILY TAB CODE
# -------------------------------

def create_family_tab(notebook, person_id):

    # Add the Family tab
    frame_family = ttk.Frame(notebook)
    notebook.add(frame_family, text='Family Trees')
    
    # Create a frame for the buttons
    frame_buttons = ttk.Frame(frame_family)
    frame_buttons.grid(column=0, row=0, sticky='ns')
    
    # Create a frame for the tree display
    frame_tree = ttk.Frame(frame_family)
    frame_tree.grid(column=1, row=0, sticky='nsew')

    # Create a new grid frame
    grid_frame = ttk.Frame(frame_tree)

    def prepare_for_tree(frame_tree, tree_text):
        nonlocal grid_frame
        #    the text widget from the grid if it's currently displayed
        if tree_text.winfo_ismapped():
            # Clear the text in the tree_text widget
            tree_text.delete("1.0", "end")
            tree_text.grid_remove()

        # Destroy the grid frame if it exists
        if grid_frame is not None and grid_frame.winfo_exists():
            grid_frame.destroy()
            grid_frame = None

    # Add the buttons to the buttons frame
    #button_immediate_tree = ttk.Button(frame_buttons, text="Immediate Family", 
    #       command=lambda: [prepare_for_tree(frame_tree, tree_text), build_immediate_tree(person_id, cursor, frame_tree)])

    #button_immediate_tree.pack(fill='x', padx=5, pady=5)  # fill the x direction, add some padding

    button_descendent_tree = ttk.Button(frame_buttons, text="Descendent Tree", 
            command=lambda: [prepare_for_tree(frame_tree, tree_text), build_family_tree(person_id, cursor, tree_text), tree_text.grid(row=0, column=0, sticky='nsew')])

    button_descendent_tree.pack(fill='x', padx=5, pady=5)  # fill the x direction, add some padding

    button_ancestor_tree = ttk.Button(frame_buttons, text="Ancestor Tree", 
    command=lambda: [prepare_for_tree(frame_tree, tree_text), build_ancestor_tree(person_id, cursor, tree_text), tree_text.grid(row=0, column=0, sticky='nsew')])

    button_ancestor_tree.pack(fill='x', padx=5, pady=5)  # fill the x direction, add some padding

    # Add a text widget to display the tree in the tree frame
    tree_text = tk.Text(frame_tree, width=80, height=40)
    tree_text.grid(row=0, column=0, sticky='nsew')  # fill both directions, allow widget to expand

    connection = sqlite3.connect('phoenix.db')
    cursor = connection.cursor()

    # Custom function to parse various date formats
    def parse_date(date_str):
        if not date_str:
            return (0, 0, 0)  # Default for unknown dates
        
        # Try parsing full date format
        try:
            return datetime.strptime(date_str, "%d-%m-%Y").timetuple()[:3]
        except ValueError:
            pass

        # Try parsing year and month format
        try:
            return datetime.strptime(date_str, "%B %Y").timetuple()[:2] + (0,)
        except ValueError:
            pass

        # Extract year only
        match = re.search(r'\b(1[5-9]\d\d|20[0-1]\d|202[0-3])\b', date_str)
        if match:
            return (int(match.group()), 0, 0)

        return (0, 0, 0)

    # Function to recursively fetch and build the family tree
    def build_family_tree(person_id, cursor, tree_text, indent="", is_last_child=False):
                
        prepare_for_tree(frame_tree, tree_text)

        # Retrieve the information of the person
        cursor.execute(
            "SELECT id, first_name, middle_name, last_name, birth_date, birth_location, death_date, death_location FROM People WHERE id = ?",
            (person_id,),
        )
        person_info = cursor.fetchone()

        if person_info:
            id_, first_name, middle_name, last_name, birth_date, birth_location, death_date, death_location = person_info

            # Prepare the name line
            name_line = indent
            if is_last_child:
                name_line += "└─ "
            else:
                name_line += "├─ "
            name_line += f"{first_name} {middle_name or ''} {last_name}"
            tree_text.insert(tk.END, name_line + "\n")

            # Prepare the details lines
            details_lines = []
            details_lines.append(indent + "   ├─ Birthdate: " + (birth_date if birth_date is not None else ''))
            details_lines.append(indent + "   │  Birthplace: " + (birth_location if birth_location is not None else ''))
            details_lines.append(indent + "   ├─ Death date: " + (death_date if death_date is not None else ''))
            details_lines.append(indent + "   │  Death place: " + (death_location if death_location is not None else ''))

            if married_to:
                # Retrieve the information of the spouse
                cursor.execute(
                    "SELECT first_name, middle_name, last_name, birth_date, birth_location, death_date, death_location FROM People WHERE id = ?",
                    (married_to,),
                )
                spouse_info = cursor.fetchone()
                if spouse_info:
                    spouse_first_name, spouse_middle_name, spouse_last_name, spouse_birth_date, spouse_birth_location, spouse_death_date, spouse_death_location = spouse_info

                    details_lines.append(indent + "   │")
                    details_lines.append(indent + "   │===Spouse: " + (spouse_first_name if spouse_first_name is not None else '') + " " + (spouse_middle_name if spouse_middle_name is not None else '') + " " + (spouse_last_name if spouse_last_name is not None else ''))
                    details_lines.append(indent + "   │   Spouse Birthdate: " + (spouse_birth_date if spouse_birth_date is not None else ''))
                    details_lines.append(indent + "   │   Spouse Birthplace: " + (spouse_birth_location if spouse_birth_location is not None else ''))
                    details_lines.append(indent + "   │   Spouse Death date: " + (spouse_death_date if spouse_death_date is not None else ''))
                    details_lines.append(indent + "   │   Spouse Death place: " + (spouse_death_location if spouse_death_location is not None else ''))

            # Insert the details lines into the tree
            for line in details_lines:
                tree_text.insert(tk.END, line + "\n")

            tree_text.insert(tk.END, "\n")  # Add a blank line

            # Retrieve the children of the person
            cursor.execute(
                "SELECT id, birth_date FROM People WHERE father = ? OR mother = ?",
                (person_id, person_id),
            )
            children = cursor.fetchall()

            # Sort children by birth date using the custom parse_date function
            children.sort(key=lambda x: parse_date(x[1]))  # Using index 1 for birth_date

            # Build the family tree for each child
            for index, child in enumerate(children, start=1):
                child_id = child[0]  # child_id is now the first element of the tuple
                is_last_child = index == len(children)
                build_family_tree(child_id, cursor, tree_text, indent + "   │", is_last_child)

    
    # Function to recursively fetch and build the ancestor tree
    def build_ancestor_tree(person_id, cursor, tree_text, indent="", is_last_child=False):
        
        prepare_for_tree(frame_tree, tree_text)
        
        # Retrieve the information of the person
        cursor.execute(
            "SELECT id, first_name, middle_name, last_name, birth_date, birth_location, death_date, death_location, father, mother FROM People WHERE id = ?",
            (person_id,),
        )
        person_info = cursor.fetchone()

        if person_info:
            id_, first_name, middle_name, last_name, birth_date, birth_location, death_date, death_location, father, mother = person_info

            # Prepare the name line
            name_line = indent
            if is_last_child:
                name_line += "└─ "
            else:
                name_line += "├─ "
            name_line += f"{first_name} {middle_name or ''} {last_name}"
            tree_text.insert(tk.END, name_line + "\n")

            # Prepare the details lines
            details_lines = []
            details_lines.append(indent + "   ├─ Birthdate: " + (birth_date if birth_date is not None else ''))
            details_lines.append(indent + "   │  Birthplace: " + (birth_location if birth_location is not None else ''))
            details_lines.append(indent + "   ├─ Death date: " + (death_date if death_date is not None else ''))
            details_lines.append(indent + "   │  Death place: " + (death_location if death_location is not None else ''))

            if married_to:
                # Retrieve the information of the spouse
                cursor.execute(
                    "SELECT first_name, middle_name, last_name, birth_date, birth_location, death_date, death_location FROM People WHERE id = ?",
                    (married_to,),
                )
                spouse_info = cursor.fetchone()
                if spouse_info:
                    spouse_first_name, spouse_middle_name, spouse_last_name, spouse_birth_date, spouse_birth_location, spouse_death_date, spouse_death_location = spouse_info

                    details_lines.append(indent + "   │")
                    details_lines.append(indent + "   │===Spouse: " + (spouse_first_name if spouse_first_name is not None else '') + " " + (spouse_middle_name if spouse_middle_name is not None else '') + " " + (spouse_last_name if spouse_last_name is not None else ''))
                    details_lines.append(indent + "   │   Spouse Birthdate: " + (spouse_birth_date if spouse_birth_date is not None else ''))
                    details_lines.append(indent + "   │   Spouse Birthplace: " + (spouse_birth_location if spouse_birth_location is not None else ''))
                    details_lines.append(indent + "   │   Spouse Death date: " + (spouse_death_date if spouse_death_date is not None else ''))
                    details_lines.append(indent + "   │   Spouse Death place: " + (spouse_death_location if spouse_death_location is not None else ''))

            # Insert the details lines into the tree
            for line in details_lines:
                tree_text.insert(tk.END, line + "\n")

            tree_text.insert(tk.END, "\n")  # Add a blank line

            # Retrieve the parents of the person
            parents = [(father, 'Father'), (mother, 'Mother')]

            # Build the ancestor tree for each parent
            for index, parent in enumerate(parents, start=1):
                parent_id = parent[0]
                parent_label = parent[1]
                is_last_child = index == len(parents)
                if parent_id is not None:
                    tree_text.insert(tk.END, indent + f"---{parent_label}---\n")
                    build_ancestor_tree(parent_id, cursor, tree_text, indent + "   │", is_last_child)
    
    # Close the connection when the notebook is closed
    notebook.winfo_toplevel().protocol("WM_DELETE_WINDOW", close_connection)

    # Function to fetch and build the immediate family grid
    def build_immediate_tree(person_id, cursor, frame_tree):
        prepare_for_tree(frame_tree, tree_text)
        
        # Create a new canvas and a vertical scrollbar for scrolling
        canvas = tk.Canvas(frame_tree)
        scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        nonlocal grid_frame
        
        # Create a new grid frame and clear it
        grid_frame = ttk.Frame(canvas)
        for widget in grid_frame.winfo_children():
            widget.destroy()

        # Add the grid frame to the canvas
        canvas.create_window((0,0), window=grid_frame, anchor="nw")

        # Configure the grid frame's size to update the scroll region
        grid_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))

        # Pack the canvas and the scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        cursor.execute(
            "SELECT father, mother, married_to FROM People WHERE id = ?",
            (person_id,),
        )
        person_info = cursor.fetchone()
        father_id, mother_id, spouse_id = person_info

        # Fetch the person's father
        cursor.execute(
            """SELECT People.id, People.first_name, People.middle_name, People.last_name, 
            People.title, People.birth_date, People.death_date, Photos.image_path 
            FROM People 
            LEFT JOIN Photos ON People.id = Photos.person_id
            WHERE People.id = ?""",
            (father_id,)
        )
        father_info = cursor.fetchone()

        # Fetch the person's mother
        cursor.execute(
            """SELECT People.id, People.first_name, People.middle_name, People.last_name, 
            People.title, People.birth_date, People.death_date, Photos.image_path 
            FROM People 
            LEFT JOIN Photos ON People.id = Photos.person_id
            WHERE People.id = ?""",
            (mother_id,),
        )
        mother_info = cursor.fetchone()

        # Fetch the person's spouse
        cursor.execute(
            """SELECT People.id, People.first_name, People.middle_name, People.last_name, 
            People.title, People.birth_date, People.death_date, Photos.image_path 
            FROM People 
            LEFT JOIN Photos ON People.id = Photos.person_id
            WHERE People.id = ?""",
            (spouse_id,),
        )
        spouse_info = cursor.fetchone()

        # Fetch the person's children
        cursor.execute(
            """SELECT People.id, People.first_name, People.middle_name, People.last_name, 
            People.title, People.birth_date, People.death_date, Photos.image_path 
            FROM People 
            LEFT JOIN Photos ON People.id = Photos.person_id
            WHERE People.father = ? OR People.mother = ? 
            ORDER BY People.birth_date ASC""",
            (person_id, person_id),
        )
        children_info = cursor.fetchall()

        # Add a function to create a new row in the grid
        def add_grid_row(frame, info, row, is_separator=False,photo_height=100):
            if is_separator:
                separator = ttk.Frame(frame, height=2, relief='groove')
                separator.grid(row=row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)  

            elif info is not None:
                id_, first_name, middle_name, last_name, title, birth_date, death_date, image_path = info
                info_text = f"{first_name} {middle_name or ''} {last_name}\nBirth: {birth_date or ''}\nDeath: {death_date or ''}"

                # Add the image, if it exists
                if image_path is not None and os.path.isfile(image_path):
                    image = Image.open(image_path)
                    wpercent = (photo_height / float(image.size[1]))
                    width_size = int((float(image.size[0]) * float(wpercent)))
                    image = image.resize((width_size, photo_height), Image.ANTIALIAS)
                    photo = ImageTk.PhotoImage(image)
                    photo_label = tk.Label(frame, image=photo)
                    photo_label.image = photo  # keep a reference to the image
                    photo_label.grid(row=row, column=0)

                # Add the text
                text_label = tk.Label(frame, text=info_text)
                text_label.grid(row=row, column=1)

        # Add the family members to the grid
        add_grid_row(grid_frame, father_info, 0)
        add_grid_row(grid_frame, mother_info, 1)
        add_grid_row(grid_frame, None, 2, is_separator=True)
        add_grid_row(grid_frame, spouse_info, 3)
        add_grid_row(grid_frame, None, 4, is_separator=True)
        for i, child_info in enumerate(children_info, start=5):
            add_grid_row(grid_frame, child_info, i)

def show_related_people(media_tree, show_related_button):
    # Clear existing data in the related people treeview
    for i in related_people_tree.get_children():
        related_people_tree.delete(i)

    selected_item = media_tree.selection()
    media_id = media_tree.item(selected_item, 'values')[0]  # Assuming ID is the 1st column

    # Query the MediaPerson table for related people
    cursor.execute("SELECT person_id FROM MediaPerson WHERE media_id = ?", (media_id,))
    related_people_ids = cursor.fetchall()

    # Check if there are related people
    if related_people_ids and len(related_people_ids) > 1:  # Adjust this condition as needed
        # Show the Show Related button and tree
        show_related_button.pack()
        related_people_tree.pack()
        related_people_tree.bind("<Double-1>", open_person_record)


        # Populate the treeview with related people
        for pid_tuple in related_people_ids:
            pid = pid_tuple[0]
            cursor.execute("SELECT id, first_name, middle_name, last_name, married_name, title, nick_name FROM People WHERE id = ?", (pid,))
            person_info = cursor.fetchone()
            if person_info:
                # Combine name fields
                full_name = ' '.join(filter(None, person_info[1:7]))
                related_people_tree.insert('', 'end', values=(person_info[0], full_name))
    else:
        # Hide the Show Related button and tree
        show_related_button.pack_forget()
        related_people_tree.pack_forget()

def open_person_record(event):
    # Get the selected item
    selected_item = related_people_tree.selection()[0]
    person_id = related_people_tree.item(selected_item, 'values')[0]  # Assuming ID is the 1st column
    
    # Open the editme.py script with the person's ID
    launch_tab("editme", str(person_id))

# -------------------------------   
# START OF THE MEDIA TAB CODE
# -------------------------------

def create_media_tab(notebook, person_id):
    # Query the Media table for media items related to the person
    cursor.execute("SELECT id, description, media_type, url, title, date_created, author, tags, access FROM Media JOIN MediaPerson ON Media.id = MediaPerson.media_id WHERE MediaPerson.person_id = ?", (person_id,))
    media_records = cursor.fetchall()

    # If no media records are found, don't create the tab
    if not media_records:
        return

    # Add the Media tab
    frame_media = ttk.Frame(notebook)
    notebook.add(frame_media, text='Media')

    has_related_people = False
    for record in media_records:
        media_id = record[0]
        cursor.execute("SELECT COUNT(*) FROM MediaPerson WHERE media_id = ? AND person_id != ?", (media_id, person_id))
        count = cursor.fetchone()[0]
        if count > 1:
            has_related_people = True
            break

    # Create a tree view for the media records
    media_tree = ttk.Treeview(frame_media, columns=("ID", "Description", "Type", "URL", "Title", "Date Created", "Author", "Tags", "Access"), show='headings', height=10)
    media_tree.heading("ID", text="ID")
    media_tree.column("ID", width=50)
    media_tree.heading("Description", text="Description")
    media_tree.column("Description", width=150)
    media_tree.heading("Type", text="Type")
    media_tree.column("Type", width=100)
    media_tree.heading("URL", text="URL")
    media_tree.column("URL", width=200)
    media_tree.heading("Title", text="Title")
    media_tree.column("Title", width=150)
    media_tree.heading("Date Created", text="Date Created")
    media_tree.column("Date Created", width=75)
    media_tree.heading("Author", text="Author")
    media_tree.column("Author", width=100)
    media_tree.heading("Tags", text="Tags")
    media_tree.column("Tags", width=100)
    media_tree.heading("Access", text="Access")
    media_tree.column("Access", width=75)
    media_tree.pack(fill='both', expand=True, padx=5, pady=5)

    # Insert the data into the tree view
    for record in media_records:
        media_tree.insert('', 'end', values=record)

    # Bind double-click event to open media URL
    media_tree.bind('<Double-1>', lambda event: open_media_url(event, media_tree))

    # Initially hide the Show Related button and Related People Treeview
    global show_related_button, related_people_tree
    show_related_button = ttk.Button(frame_media, text="Show Related", command=lambda: show_related_people(media_tree))
    related_people_tree = ttk.Treeview(frame_media, columns=("ID", "Name"), show='headings')

    # Show Related button and Related People Treeview
    if has_related_people:
        show_related_button = ttk.Button(frame_media, text="Show Related People", command=lambda: show_related_people(media_tree))
        #show_related_button.pack(pady=5)

        related_people_tree = ttk.Treeview(frame_media, columns=("ID", "Name"), show='headings')

        # Related People Treeview
        related_people_tree = ttk.Treeview(frame_media, columns=("ID", "Name"), show='headings')
        related_people_tree.heading("ID", text="ID")
        related_people_tree.column("ID", width=50, stretch=tk.NO)
        related_people_tree.heading("Name", text="Name")
        related_people_tree.column("Name", width=150, stretch=tk.NO)
        #related_people_tree.pack(side='top', fill='x', padx=5, pady=5)

        # Bind double-click event to open media URL
        media_tree.bind('<Double-1>', lambda event: open_media_url(event, media_tree))
        media_tree.bind('<<TreeviewSelect>>', lambda event: show_related_people(media_tree, show_related_button))
        # Separator on the form
        media_sep = ttk.Separator(frame_media, orient='horizontal')
        media_sep.pack(fill='x', pady=10)

def open_media_url(event, tree):
    selected_item = tree.selection()[0]
    media_url = tree.item(selected_item, 'values')[3]  # Assuming URL is the 4th column
    webbrowser.open(media_url)

# -------------------------------   
# START OF THE EDUCATION TAB CODE
# -------------------------------

def create_education_tab(notebook, id):
    cursor = connection.cursor()
    cursor.execute("SELECT school_name, record_year, degree, position, notes, field_of_study FROM Education WHERE person_id = ?", (id,))
    records = cursor.fetchall()

    # If there are records for the person in the Education table
    if records:
        # Add the Education tab
        frame_education = ttk.Frame(notebook)
        notebook.add(frame_education, text='Education/Career')

        # Create a tree view and add it to the frame
        tree = ttk.Treeview(frame_education, columns=[i[0] for i in cursor.description], show='headings', height=12)
        tree.pack(fill=tk.BOTH, expand=True)

        # Configure the tree view columns
        for column in tree['columns']:
            tree.heading(column, text=column)

        # Adjust the width of the columns
        tree.column('school_name', width=150)
        tree.heading('school_name', text='School')
        tree.column('record_year', width=50)
        tree.heading('record_year', text= 'Year')
        tree.column('notes', width=300)
        tree.column('position', width=150)

        for column in ['degree', 'field_of_study']:
            tree.column(column, width=100)

        # Insert the data into the tree view
        for record in records:
            tree.insert('', 'end', values=[item if item else '' for item in record])

    cursor.close()

def on_item_double_click(event, person_id):
    
    launch_tab("mapsections2", str(record_id))
  
def map_it_action(tree):
    # Define the action for the "Map It" button
    selected_item = tree.selection()
    if selected_item:
        # Extract the address or other relevant data
        address = tree.item(selected_item, 'values')[0]
        # Implement the mapping functionality here
        print(f"Map location: {address}")  # Placeholder action

# -------------------------------   
# START OF THE RESIDENCE TAB CODE
# -------------------------------

# Define the function to fetch all existing addresses from the Address table
def get_all_addresses():
    cursor.execute("SELECT address FROM Address")
    return [row[0] for row in cursor.fetchall()]

def get_all_sources():
    cursor.execute("SELECT title FROM Sources")
    sources = [row[0] for row in cursor.fetchall()]
    sources.insert(0, "No Source")  # Add "No Source" as the first option
    return sources

def create_residence_tab(notebook, person_id):
    
    selected_residence = [None]

    # Function to open the family linkage window
    def on_restree_double_click(event):
        tree = event.widget
        item = tree.identify('item', event.x, event.y)
        if item:
            values = tree.item(item, 'values')
            if values:
                family_member_id = values[0]
                open_family_linkage_window(int(family_member_id), residence_id)

    def link_family_members():
        print(f"Into the link function and the selected res id is {selected_residence[0]}", flush=True)
        if selected_residence[0]:
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Please select a residence record.")
                return
            
            item = tree.item(selected_item[0])
            res_history_id = item['values'][0]
            residence_id = item['values'][1]
            
            print(f"Extracted residence_id: {residence_id}", flush=True)
            
            if residence_id != selected_residence[0]:
                print(f"Warning: selected_residence_id ({selected_residence[0]}) doesn't match extracted residence_id ({residence_id})", flush=True)
            
            open_family_linkage_window(
                person_id=person_id,
                residence_id=residence_id
            )
        else:
            messagebox.showerror("Error", "No residence selected. Please select a residence to link family members.")
    
    def on_treeview_select(event):
        
        selected_item = tree.selection()
        selected_item = tree.selection()
        print(f"into the treeview select. Selected Item is: {selected_item}", flush=True)
        if selected_item:
            # Extract the selected item's data
            item = tree.item(selected_item[0])
            
            # Make sure that the first column contains the residence_id
            res_history_id = item['values'][0]  # First column
            print(f"Into the Tree Select and the Res History ID is {res_history_id}", flush=True)
            residence_id = item['values'][1]  # Second column is residence_id
            print(f"Into the Tree Select and the Res ID is {residence_id}", flush=True)

            if residence_id:
                selected_residence[0] = residence_id  # Store the selected residence_id for future actions
                print(f"Selected residence_id set to: {selected_residence[0]}", flush=True)
                
                # Show the Edit, Delete, and Link Family Members buttons
                edit_residence_button.grid()
                delete_residence_button.grid()
                link_family_members_button.grid()
            else:
                # If the residence_id is not valid, hide the buttons and clear the selected ID
                selected_residence[0] = None
                edit_residence_button.grid_remove()
                delete_residence_button.grid_remove()
                link_family_members_button.grid_remove()
        else:
            # If no selection is made, hide the buttons and clear the selected ID
            selected_residence[0] = None
            edit_residence_button.grid_remove()
            delete_residence_button.grid_remove()
            link_family_members_button.grid_remove()

    frame = ttk.Frame(notebook)
    notebook.add(frame, text="Home/Property")

    is_programmatic_change = False
    is_editing = False
    current_edit_id = None

    sort_orders = {"Address": False, "Start Date": False, "End Date": False, "Notes": False}

    # Function to sort columns with non-date values (like Address, Notes)
    def sort_treeview_column(tree, col, reverse=False):
        data = [(tree.set(k, col), k) for k in tree.get_children('')]
        data.sort(reverse=reverse)

        for index, (val, k) in enumerate(data):
            tree.move(k, '', index)

        sort_orders[col] = not reverse

    def sort_treeview_by_date(tree, column_index, reverse=False):
        print(f"Starting sort_treeview_by_date function for column {column_index}")
        
        def convert_to_sortable_date(date_value):
            print(f"Converting date: {date_value}, type: {type(date_value)}")
            if not date_value:
                return None
            
            # Convert to string if it's an integer or any other type
            date_str = str(date_value)
            
            if date_str.lower().startswith("about "):
                date_str = date_str[6:]
            try:
                return datetime.strptime(date_str, "%m-%d-%Y").strftime("%Y-%m-%d")
            except ValueError:
                try:
                    return datetime.strptime(date_str, "%m-%Y").strftime("%Y-%m")
                except ValueError:
                    if re.match(r'^\d{4}$', date_str):
                        return date_str
                    return None

        data = []
        for item in tree.get_children(''):
            values = tree.item(item)['values']
            date_str = values[column_index]
            date_obj = convert_to_sortable_date(date_str)
            data.append((date_obj, values, item))
            print(f"Processed item: date_str={date_str}, date_obj={date_obj}")

        data.sort(reverse=reverse, key=lambda x: (x[0] is None, x[0]))
        for index, (_, values, item) in enumerate(data):
            tree.move(item, '', index)

        sort_orders["Start Date"] = not reverse
        print("Finished sort_treeview_by_date function")

    # Define the Treeview with the res_id column included
    tree = ttk.Treeview(frame, columns=("res_history_id", "residence_id", "Address", "Start Date", "End Date", "Notes", "Source", "Link"), show="headings")

    tree.column("res_history_id", width=0, stretch=tk.NO)  # Hide the res_history_id column
    tree.column("residence_id", width=0, stretch=tk.NO)  # Hide the residence_id column
    tree.column("Address", width=80)
    tree.column("Start Date", width=50)
    tree.column("End Date", width=50)
    tree.column("Notes", width=520)
    tree.column("Source", width=100)
    tree.column("Link", width=200)

    tree.heading("res_history_id", text="ResHistory ID")
    tree.heading("residence_id", text="Residence ID")
    tree.heading("Address", text="Address", command=lambda: sort_treeview_column(tree, "Address", sort_orders["Address"]))
    tree.heading("Start Date", text="Start Date", command=lambda: sort_treeview_by_date(tree, 3, sort_orders["Start Date"]))
    tree.heading("End Date", text="End Date", command=lambda: sort_treeview_by_date(tree, 4, sort_orders["End Date"]))
    tree.heading("Notes", text="Notes", command=lambda: sort_treeview_column(tree, "Notes", sort_orders["Notes"]))
    tree.heading("Source", text="Source", command=lambda: sort_treeview_column(tree, "Source", sort_orders["Source"]))
    tree.heading("Link", text="Link", command=lambda: sort_treeview_column(tree, "Link", sort_orders["Link"]))

    tree.pack(side='top', fill='both', expand=True)
    tree.bind('<<TreeviewSelect>>', on_treeview_select)
    tree.bind('<Double-1>', on_restree_double_click)

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side='right', fill='y')
    tree.configure(yscrollcommand=scrollbar.set)

    query = """
        SELECT 
            ResHistory.res_history_id, 
            Residence.residence_id, 
            COALESCE(Address.address, '') AS address, 
            COALESCE(Residence.start_date, '') AS start_date,
            COALESCE(Residence.start_date_precision, '') AS start_date_precision, 
            COALESCE(Residence.end_date, '') AS end_date,
            COALESCE(Residence.end_date_precision, '') AS end_date_precision,
            COALESCE(Residence.notes, '') AS notes, 
            COALESCE(Sources.title, '') AS source, 
            COALESCE(Residence.res_link, '') AS link
        FROM ResHistory
        JOIN Residence ON ResHistory.residence_id = Residence.residence_id
        LEFT JOIN Address ON Residence.address_id = Address.address_id
        LEFT JOIN Sources ON Residence.res_source = Sources.id
        WHERE ResHistory.person_id = ?
        ORDER BY Residence.start_date ASC
    """

    cursor.execute(query, (person_id,))
    data = cursor.fetchall()

    # Populate the tree
    for row in data:
        res_history_id = row[0] if len(row) > 0 else None  # Hidden
        residence_id = row[1] if len(row) > 1 else None  # Hidden
        address = row[2] if len(row) > 2 else ""
        start_date = row[3] if len(row) > 3 else ""
        start_date_precision = row[4] if len(row) > 4 else ""
        end_date = row[5] if len(row) > 5 else ""
        end_date_precision = row[6] if len(row) > 6 else ""
        notes = row[7] if len(row) > 7 else ""
        source = row[8] if len(row) > 8 else ""
        link = row[9] if len(row) > 9 else ""

        # Format dates for display
        start_date_formatted = format_date_for_display(start_date, start_date_precision)
        end_date_formatted = format_date_for_display(end_date, end_date_precision)

        # Handle source and link values
        source = source if source is not None else ""
        link = link if link not in (None, 'None') else ""

        tree.insert('', 'end', values=(res_history_id, residence_id, address, start_date_formatted, end_date_formatted, notes, source, link))

    # Frame for input fields (below the Treeview now)
    # Frame for input fields (below the Treeview now)
    frame_input = ttk.Frame(frame)
    frame_input.pack(side='top', fill='x', pady=10)

    # Search entry field for Address search
    search_address_var = tk.StringVar()  # Variable to hold the search text
    search_entry = ttk.Entry(frame_input, textvariable=search_address_var, width=40)
    search_entry.grid(row=0, column=1, padx=5, pady=5)

    # Search button for Address dropdown
    search_button = ttk.Button(frame_input, text="Search", command=lambda: search_address(address_dropdown))
    search_button.grid(row=0, column=0, padx=5, pady=5)

    # Address input field (Dropdown)
    ttk.Label(frame_input, text="Address:").grid(row=1, column=0, padx=5, pady=5)
    address_var = tk.StringVar()
    address_dropdown = ttk.Combobox(frame_input, textvariable=address_var, width=47, state="readonly")
    address_dropdown.grid(row=1, column=1, padx=5, pady=5)
    address_dropdown['values'] = get_all_addresses()  # Populate with existing addresses
    
    # Define the search function for the Address dropdown
    def search_address(dropdown):
        search_term = search_address_var.get().strip()
        if search_term:
            cursor.execute("SELECT address FROM Address WHERE address LIKE ?", (f'%{search_term}%',))
            results = [row[0] for row in cursor.fetchall()]
            if results:
                dropdown['values'] = results  # Update dropdown with filtered addresses
                dropdown.set('')  # Clear current selection if results are multiple
            else:
                messagebox.showerror("No results", "No addresses found matching the search term.")
        else:
            dropdown['values'] = get_all_addresses()  # Reset dropdown if search field is empty

    # Separator on the form
    separator = ttk.Separator(frame_input, orient='horizontal')
    separator.grid(row=2, columnspan=3, pady=10, sticky='ew')

    # Start date input field
    ttk.Label(frame_input, text="Start Date:").grid(row=3, column=0, padx=5, pady=5)
    start_date_entry = ttk.Entry(frame_input, width=20)
    start_date_entry.grid(row=3, column=1, padx=5, pady=5)
    add_date_format_menu(start_date_entry)

    # End date input field
    ttk.Label(frame_input, text="End Date:").grid(row=4, column=0, padx=5, pady=5)
    end_date_entry = ttk.Entry(frame_input, width=20)
    end_date_entry.grid(row=4, column=1, padx=5, pady=5)
    add_date_format_menu(end_date_entry)

    # Notes input field
    ttk.Label(frame_input, text="Notes:").grid(row=5, column=0, padx=5, pady=5)
    notes_entry = ttk.Entry(frame_input, width=50)
    notes_entry.grid(row=5, column=1, padx=5, pady=5)

    # Source field
    ttk.Label(frame_input, text="Source:").grid(row=6, column=0, padx=5, pady=5)
    source_var = tk.StringVar()
    source_dropdown = ttk.Combobox(frame_input, textvariable=source_var, width=47, state="readonly")
    source_dropdown.grid(row=6, column=1, padx=5, pady=5)
    source_dropdown['values'] = get_all_sources() + ["No Source"]

    # Link input field
    ttk.Label(frame_input, text="Link:").grid(row=7, column=0, padx=5, pady=5)
    link_entry = ttk.Entry(frame_input, width=50)
    link_entry.grid(row=7, column=1, padx=5, pady=5)

    # Function to manage button visibility on treeview select
    def on_treeview_select(event, tree, edit_residence_button, delete_residence_button, link_family_members_button):
        selected_item = tree.selection()
        if selected_item:
            edit_residence_button.grid()  # Show Edit button
            delete_residence_button.grid()  # Show Delete button
            link_family_members_button.grid()  # Show Link Family Members button
        else:
            edit_residence_button.grid_remove()
            delete_residence_button.grid_remove()
            link_family_members_button.grid_remove()

    # Refresh the treeview
    def refresh_residence_treeview():
        print("Starting refresh_residence_treeview function")
        tree.delete(*tree.get_children())  # Clear the Treeview

        query = """
        SELECT ResHistory.res_history_id, Residence.residence_id, Address.address, 
               Residence.start_date, Residence.start_date_precision, 
               Residence.end_date, Residence.end_date_precision, 
               Residence.notes, Sources.title, Residence.res_link
        FROM ResHistory
        JOIN Residence ON ResHistory.residence_id = Residence.residence_id
        JOIN Address ON Residence.address_id = Address.address_id
        LEFT JOIN Sources ON Residence.res_source = Sources.id
        WHERE ResHistory.person_id = ?
        ORDER BY Residence.start_date ASC
        """ 
        cursor.execute(query, (person_id,))
        data = cursor.fetchall()

        print(f"Fetched {len(data)} records from the database")

        # Initially hide the buttons before data is loaded
        edit_residence_button.grid_remove()
        delete_residence_button.grid_remove()
        link_family_members_button.grid_remove()

        if not data:
            print("No data found")
            # If no data, ensure buttons remain hidden
            edit_residence_button.grid_remove()
            delete_residence_button.grid_remove()
        else:
            for row in data:
                try:
                    res_history_id = row[0]
                    residence_id = row[1]
                    address = row[2]
                    start_date = row[3]
                    start_date_precision = row[4]
                    end_date = row[5]
                    end_date_precision = row[6]
                    notes = row[7] or ""
                    source = row[8] or ""
                    link = row[9] or ""

                    print(f"Processing row: {row}")
                    print(f"Start date: {start_date}, type: {type(start_date)}")
                    print(f"End date: {end_date}, type: {type(end_date)}")

                    start_date_display = format_date_for_display(start_date, start_date_precision)
                    end_date_display = format_date_for_display(end_date, end_date_precision)

                    print(f"Formatted start date: {start_date_display}")
                    print(f"Formatted end date: {end_date_display}")

                    # Insert the record into the Treeview
                    tree.insert('', 'end', values=(res_history_id, residence_id, address, start_date_display, end_date_display, notes, source, link))
                except Exception as e:
                    print(f"Error processing row {row}: {e}")
                    print(f"Error type: {type(e)}")
                    print(f"Error args: {e.args}")

            # Sort the treeview by date (Start Date) after loading data
            sort_treeview_by_date(tree, 3, False)  # 3 is the column index for "Start Date"

        print("Finished refresh_residence_treeview function") 
    

    # Function to delete a residence record
    def delete_residence_record():
        nonlocal current_edit_id
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a record to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected record?")
        if not confirm:
            return

        item = tree.item(selected_item[0])
        res_history_id = item['values'][0]
        residence_id = item['values'][1]

        # Delete the record from ResHistory and Residence
        cursor.execute("DELETE FROM ResHistory WHERE res_history_id = ? AND person_id = ?", (res_history_id, person_id))
        connection.commit()

        cursor.execute("SELECT COUNT(*) FROM ResHistory WHERE residence_id = ?", (residence_id,))
        remaining_links = cursor.fetchone()[0]

        if remaining_links == 0:
            cursor.execute("DELETE FROM Residence WHERE residence_id = ?", (residence_id,))
            connection.commit()

        refresh_residence_treeview()
        clear_input_fields()
        messagebox.showinfo("Success", "Record deleted successfully.")

    # Function to edit a residence record
    def edit_residence_record():
        nonlocal is_editing, current_edit_id
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a record to edit.")
            return

        item = tree.item(selected_item[0])
        res_history_id = item['values'][0]
        residence_id = item['values'][1]
        address = item['values'][2]
        start_date = item['values'][3]
        end_date = item['values'][4]
        notes = item['values'][5]
        source = item['values'][6]
        link = item['values'][7]

        current_edit_id = residence_id

        address_var.set(address)
        start_date_entry.delete(0, tk.END)
        start_date_entry.insert(0, start_date)
        end_date_entry.delete(0, tk.END)
        end_date_entry.insert(0, end_date)
        notes_entry.delete(0, tk.END)
        notes_entry.insert(0, notes)
        source_dropdown.set(source)
        link_entry.delete(0, tk.END)
        link_entry.insert(0, link)

        is_editing = True

        add_residence_button.config(text="Update Residence")
        cancel_edit_button.grid(row=9, column=1, pady=10)
        cancel_edit_button.config(state="normal")

        delete_residence_button.grid_remove()
        edit_residence_button.grid_remove()
        link_family_members_button.grid_remove()

    #
    def add_or_update_residence_record():
        nonlocal is_editing, current_edit_id
        
        print("Starting add_or_update_residence_record function")
        
        address = address_var.get().strip()
        start_date = start_date_entry.get().strip()
        end_date = end_date_entry.get().strip()
        notes = notes_entry.get().strip()
        res_link = link_entry.get().strip()
        source_name = source_var.get().strip()

        print(f"Input values: address={address}, start_date={start_date}, end_date={end_date}")
        print(f"Input types: start_date type={type(start_date)}, end_date type={type(end_date)}")

        if not address or not start_date:
            messagebox.showerror("Error", "Please enter both an address and a start date.")
            return

        cursor.execute("SELECT address_id FROM Address WHERE address = ?", (address,))
        address_data = cursor.fetchone()

        if not address_data:
            messagebox.showerror("Error", "Address not found. Please select a valid address.")
            return

        address_id = address_data[0]
        print(f"Address ID: {address_id}")

        if source_name == "No Source" or not source_name:
            res_source = None
        else:
            cursor.execute("SELECT id FROM Sources WHERE title = ?", (source_name,))
            source_data = cursor.fetchone()
            if not source_data:
                messagebox.showerror("Error", "Source not found. Please select a valid source.")
                return
            res_source = source_data[0]
        
        print(f"Source ID: {res_source}")

        try:
            print("Parsing start date")
            start_date, start_precision = parse_date_input(start_date)
            print(f"Parsed start date: {start_date}, precision: {start_precision}")

            print("Parsing end date")
            end_date, end_precision = parse_date_input(end_date) if end_date else ("", "")
            print(f"Parsed end date: {end_date}, precision: {end_precision}")

            if is_editing and current_edit_id:
                print(f"Updating existing record with ID: {current_edit_id}")
                cursor.execute("""
                    UPDATE Residence 
                    SET address_id = ?, start_date = ?, start_date_precision = ?, 
                        end_date = ?, end_date_precision = ?, notes = ?, res_source = ?, res_link = ?
                    WHERE residence_id = ?
                """, (address_id, start_date, start_precision, end_date, end_precision, 
                      notes, res_source, res_link, current_edit_id))
            else:
                print("Inserting new record")
                cursor.execute("""
                    INSERT INTO Residence (address_id, start_date, start_date_precision, 
                                           end_date, end_date_precision, notes, res_source, res_link) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (address_id, start_date, start_precision, end_date, end_precision, 
                      notes, res_source, res_link))
                residence_id = cursor.lastrowid
                print(f"New residence ID: {residence_id}")

                print("Inserting into ResHistory")
                cursor.execute("""
                    INSERT INTO ResHistory (person_id, residence_id)
                    VALUES (?, ?)
                """, (person_id, residence_id))

            connection.commit()
            print("Database commit successful")
            
            is_editing = False
            current_edit_id = None

            refresh_residence_treeview()
            clear_input_fields()
            add_residence_button.config(text="Add Residence")
            cancel_edit_button.grid_remove()
            delete_residence_button.grid()

        except Exception as e:
            connection.rollback()
            print(f"Error occurred: {e}")
            print(f"Error type: {type(e)}")
            print(f"Error args: {e.args}")
            messagebox.showerror("Error", f"Error during add/update operation: {e}")

        print("Finished add_or_update_residence_record function")    


    # Function to clear input fields and reset button states
    def clear_input_fields():
        nonlocal is_editing, current_edit_id

        address_var.set('')
        start_date_entry.delete(0, tk.END)
        end_date_entry.delete(0, tk.END)
        notes_entry.delete(0, tk.END)
        link_entry.delete(0, tk.END)
        source_dropdown.set('')

        is_editing = False
        current_edit_id = None

        add_residence_button.config(text="Add Residence")
        cancel_edit_button.grid_remove()
        delete_residence_button.grid_remove()
        edit_residence_button.grid_remove()
        link_family_members_button.grid_remove()

    # Add Residence button
    add_residence_button = ttk.Button(frame_input, text="Add Residence", command=add_or_update_residence_record)
    add_residence_button.grid(row=8, column=0, pady=10)

    # Cancel Edit button (hidden initially)
    cancel_edit_button = ttk.Button(frame_input, text="Cancel", command=clear_input_fields)
    cancel_edit_button.grid(row=9, column=1, pady=10)
    cancel_edit_button.grid_remove()

    # Delete Residence button (initially hidden)
    delete_residence_button = ttk.Button(frame_input, text="Delete Residence", command=delete_residence_record)
    delete_residence_button.grid(row=8, column=1, sticky='w', pady=10)
    delete_residence_button.grid_remove()

    # Edit Residence button (initially hidden)
    edit_residence_button = ttk.Button(frame_input, text="Edit Residence", command=edit_residence_record)
    edit_residence_button.grid(row=9, column=0, pady=10)
    edit_residence_button.grid_remove()

    # Link Family Members button (initially hidden)
    link_family_members_button = ttk.Button(frame_input, text="Show/Link Family Members", command=link_family_members)
    link_family_members_button.grid(row=10, column=0, pady=10)
    link_family_members_button.grid_remove()

# -------------------------------   
# START OF THE NARRATIVE TAB CODE
# -------------------------------

def create_narrative_tab(notebook, bio, person_id):
    frame_narrative = ttk.Frame(notebook)
    notebook.add(frame_narrative, text='Narrative')

    # Insert obituary editor directly under Bio
    create_embedded_bio_editor(frame_narrative, bio, person_id)
    create_embedded_obituary_editor(frame_narrative, person_id)
    create_embedded_life_events(frame_narrative, person_id)

def populate_spouse_dropdown(person_id):
    global spouse_list  
    person_id_int = int(person_id)
    
    # Query for marriages and include birth and death dates
    cursor.execute("""
        SELECT P.id, P.first_name, P.middle_name, P.last_name, P.birth_date, P.death_date 
        FROM People P 
        JOIN Marriages M ON P.id = M.person1_id OR P.id = M.person2_id 
        WHERE (M.person1_id = ? OR M.person2_id = ?) AND P.id != ?""",
        (person_id, person_id, person_id))
    marriages = cursor.fetchall()
    
    # Prepare a list for the dropdown
    spouse_list = []
    max_length = 0
    for spouse in marriages:
        spouse_id, first_name, middle_name, last_name, birth_date, death_date = spouse
        name = ' '.join(filter(None, [first_name, middle_name, last_name]))
        birth_str = f"(born: {birth_date}" if birth_date else ""
        death_str = f" died: {death_date})" if death_date else ""
        date_info = ' '.join(filter(None, [birth_str, death_str]))
        marriage_info = f"{spouse_id}: {name} - {date_info}" if date_info else f"{spouse_id}: {name}"
        spouse_list.append(marriage_info)
        max_length = max(max_length, len(marriage_info))

    current_selection = spouse_dropdown.get()  # Save the current selection
    
    # Unbind <<ComboboxSelected>> event temporarily
    spouse_dropdown.unbind("<<ComboboxSelected>>")
    
    spouse_dropdown['values'] = spouse_list  # Populate the dropdown
    spouse_dropdown.config(width=max_length)  # Adjust dropdown width

    # Restore the selection or set default
    if current_selection in spouse_list:
        spouse_dropdown.set(current_selection)
    elif spouse_list:
        spouse_dropdown.set(spouse_list[0])
    else:
        spouse_dropdown.set('')

    # Rebind <<ComboboxSelected>> event
    spouse_dropdown.bind("<<ComboboxSelected>>", update_children_tree_on_spouse_selection)

    create_spouse_dropdown_menu()  # Update the right-click menu
    
    return len(spouse_list) > 0

def create_spouse_dropdown_menu():
    
    global spouse_list

    # Create a menu
    spouse_dropdown_menu = tk.Menu(frame_overview, tearoff=0)
    
    # Add menu items
    if spouse_list:
        spouse_dropdown_menu.add_command(label="View Spouse Record", command=open_spouse_record)
        spouse_dropdown_menu.add_command(label="Edit Marriage", command=lambda: edit_marriage_record())
        spouse_dropdown_menu.add_command(label="Delete Marriage Record", command=delete_marriage_record)
    spouse_dropdown_menu.add_command(label="Add a Spouse", command=lambda: launch_tab("marriagerecord_add", str(record_id)))
    
    # Bind the right-click event
    label_spouse_dropdown.bind("<Button-1>", lambda e: spouse_dropdown_menu.post(e.x_root, e.y_root))

def edit_marriage_record():
    selected_spouse_info = spouse_dropdown.get()
    if selected_spouse_info:
        spouse_id = selected_spouse_info.split(':')[0].strip()
        if spouse_id.isdigit():
            launch_tab("marriagerecord_handle", str(record_id), spouse_id)
        else:
            messagebox.showerror("Error", "Invalid spouse ID.")
    else:
        messagebox.showerror("Error", "No spouse selected.")

def delete_marriage_record():
    selected_spouse_info = spouse_dropdown.get()

    if not selected_spouse_info:
        messagebox.showerror("Error", "No spouse selected.")
        return

    # Extracting the spouse ID from the dropdown selection
    spouse_id = selected_spouse_info.split(':')[0].strip()
    if spouse_id.isdigit():
        # Confirm deletion
        cursor.execute("SELECT first_name, middle_name, last_name FROM People WHERE id = ?", (spouse_id,))
        spouse_name = cursor.fetchone()
        if spouse_name:
            full_spouse_name = " ".join([name for name in spouse_name if name])
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the marriage record between {person_record[1]} {person_record[2]} {person_record[3]} and {full_spouse_name}?")
            if confirm:
                try:
                    # Delete the marriage record
                    cursor.execute("DELETE FROM Marriages WHERE (person1_id = ? AND person2_id = ?) OR (person1_id = ? AND person2_id = ?)", (record_id, spouse_id, spouse_id, record_id))
                    connection.commit()
                    messagebox.showinfo("Success", "Marriage record deleted successfully.")
                    
                    # Clear the marriage details labels
                    label2_marriage_date.config(text="")
                    label2_marriage_end_date.config(text="")
                    label2_marriage_location.config(text="")
                    label2_marriage_note.config(text="")
                    label2_marriage_link.config(text="")

                    populate_spouse_dropdown(record_id)  # Refresh the spouse list
                except sqlite3.Error as e:
                    messagebox.showerror("Error", f"An error occurred: {e}")
            else:
                messagebox.showinfo("Cancelled", "Marriage record deletion cancelled.")
        else:
            messagebox.showerror("Error", "Spouse not found.")
    else:
        messagebox.showerror("Error", "Invalid spouse ID.")

def spouse_dropdown_action():
    messagebox.showinfo("Action", "Action performed on spouse dropdown.")

def on_focus_in(event):
    # Refresh the spouse dropdown list in the frame_overview
    populate_spouse_dropdown(record_id)


def get_rec_status(ID):
    # Use the globally defined 'connection' instead of 'conn'
    cursor = connection.cursor()
    
    # Define a dictionary for status symbols
    status_symbols = {
        "To Be Reviewed": "-",
        "Out for Review": "o",
        "Reviewed": "✓"
    }

    # Execute the query with the correct ID
    cursor.execute("SELECT status FROM RecordTracking WHERE person_id = ?", (ID,))
    status_result = cursor.fetchone()
    status = status_result[0] if status_result else "X"
    status_symbol = status_symbols.get(status, "")  # Get symbol from dictionary
    
    return status_symbol  # Return the status symbol


def search_findagrave():
    first_name = entry_first_name.get().strip()
    middle_name = entry_middle_name.get().strip()  # If you have this field
    last_name = entry_last_name.get().strip()
    birth_year = entry_birth_date.get().strip()[:4]  # Just the year if available

    url = "https://www.findagrave.com/memorial/search?"

    params = []
    if first_name:
        params.append(f"firstname={first_name}")
    if middle_name:
        params.append(f"middlename={middle_name}")
    if last_name:
        params.append(f"lastname={last_name}")
    if birth_year:
        params.append(f"birthyear={birth_year}&birthyearfilter=3")  # '3' = ± 3 years range

    # Join all parameters
    full_url = url + "&".join(params)

    # Open the constructed URL
    webbrowser.open(full_url, new=2)


# Create the GUI window
window = tk.Tk()
window.title("Update Record")

# Set the window size and position
window_width = 1600
window_height = 900
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Allow dynamic resizing of the main interface
window.grid_rowconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
# Create a frame for the photo
frame_photo = ttk.Frame(window)
frame_photo.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="nsew")

# Create a frame for the form fields
frame_form = ttk.Frame(window)
frame_form.grid(row=0, column=1, rowspan=3, sticky="nsew")
frame_form.grid_rowconfigure(0, weight=1)
frame_form.grid_columnconfigure(0, weight=1)

# Create the notebook (tabbed interface)
notebook = ttk.Notebook(frame_form)
notebook.grid(row=0, column=0, sticky="nsew")

bold_font = font.Font(weight="bold")

tab_prefs = load_tab_prefs()

# Add the Vital tab
frame_overview = ttk.Frame(notebook, takefocus=True)
notebook.add(frame_overview, text='Overview')

# Bind the FocusIn event to refresh the spouse list
frame_overview.bind("<FocusIn>", lambda e: populate_spouse_dropdown(record_id))

# Create the Bio tab if the bio is not empty
# TODO - we will need to reset - it is now out of range
person_id = person_record[0]
bio = person_record[20]
create_narrative_tab(notebook, bio, person_id)

if tab_prefs.get("family") or has_family_data(person_record[0]):
    create_family_tab(notebook, person_record[0])

if tab_prefs.get("residence") or has_residence_data(person_record[0]):
    create_residence_tab(notebook, person_record[0])

if tab_prefs.get("education") or has_education_data(person_record[0]):
    create_education_tab(notebook, person_record[0])

if tab_prefs.get("business") or has_business_data(person_record[0]):
    create_business_tab(notebook, person_record[0])

if tab_prefs.get("records") or has_records_data(person_record[0]):
    create_records_tab(notebook, person_record[0])

if tab_prefs.get("orgs") or has_orgs_data(person_record[0]):
    create_orgs_tab(notebook, person_record[0])

# Conditionally add the Institutions tab
if has_institution_data(person_record[0]):
    create_institution_tab(notebook, person_record[0])

if tab_prefs.get("media") or has_media_data(person_record[0]):
    create_media_tab(notebook, person_record[0])

if tab_prefs.get("sources"):
    frame_sources = ttk.Frame(notebook)
    notebook.add(frame_sources, text='Sources')

# Record ID entry
label_id = ttk.Label(frame_overview, text="Record ID: ")
label_id.grid(row=0, column=0, padx=5, pady=5, sticky='e')

#label_id_value = ttk.Label(frame_overview, text="ID:")
#label_id_value.grid(row=0, column=1, padx=5, pady=5, sticky='w')
entry_id_var = tk.StringVar()
entry_id = ttk.Label(frame_overview, textvariable=entry_id_var)
entry_id.grid(row=0, column=1, padx=5, pady=5, sticky='w')


label_status = ttk.Label(frame_overview, text="Status: ")
label_status.grid(row=0, column=4, padx=5, pady=5, sticky='e')

# Call the function and store the result in a variable
status_symbol = get_rec_status(record_id)  
label_status2 = ttk.Label(frame_overview, text="")
label_status2.grid(row=0, column=5, padx=5, pady=5, sticky='w')
label_status2.config(text=f"{status_symbol if status_symbol else 'x'}")

# First Name entry
label_first_name = ttk.Label(frame_overview, text="First Name: ")
label_first_name.grid(row=1, column=0, padx=(5,0), pady=5, sticky='e')
entry_first_name = ttk.Entry(frame_overview)
entry_first_name.grid(row=1, column=1, padx=(0,5), pady=5, sticky='w')

# Middle Name entry
label_middle_name = ttk.Label(frame_overview, text="Middle Name: ")
label_middle_name.grid(row=1, column=2, padx=(0,0), pady=5, sticky='e')
entry_middle_name = ttk.Entry(frame_overview)
entry_middle_name.grid(row=1, column=3, padx=(0,0), pady=5, sticky='w')

# Last Name entry
label_last_name = ttk.Label(frame_overview, text="Last Name: ")
label_last_name.grid(row=1, column=4, padx=(5,0), pady=5, sticky='e')
entry_last_name = ttk.Entry(frame_overview)
entry_last_name.grid(row=1, column=5, padx=(0,5), pady=5, sticky='w')

# Title entry
label_title = ttk.Label(frame_overview, text="Title: ")
label_title.grid(row=2, column=0, padx=5, pady=5, sticky='e')
entry_title = ttk.Entry(frame_overview)
entry_title.grid(row=2, column=1, padx=5, pady=5, sticky='w')

# Nick Name entry
label_nick_name = ttk.Label(frame_overview, text="Nick Name: ")
label_nick_name.grid(row=2, column=2, padx=(0,0), pady=5, sticky='e')
entry_nick_name = ttk.Entry(frame_overview)
entry_nick_name.grid(row=2, column=3, padx=(0,0), pady=5, sticky='w')

# Married Name entry
label_married_name = ttk.Label(frame_overview, text="Married Name: ")
label_married_name.grid(row=2, column=4, padx=5, pady=5, sticky='e')
entry_married_name = ttk.Entry(frame_overview)
entry_married_name.grid(row=2, column=5, padx=5, pady=5, sticky='w')

# Separator on the form
separator = ttk.Separator(frame_overview, orient='horizontal')
separator.grid(row=3, columnspan=6, pady=10, sticky='ew')

# Birth Date entry
label_birth_date = ttk.Label(frame_overview, text="Birthdate: ")
label_birth_date.grid(row=4, column=0, padx=2, pady=5, sticky='e')
entry_birth_date = ttk.Entry(frame_overview)
entry_birth_date.grid(row=4, column=1, padx=2, pady=5, sticky='w')

# Birth Location entry
label_birth_location = ttk.Label(frame_overview, text="Birthplace: ")
label_birth_location.grid(row=4, column=2, padx=5, pady=5, sticky='e')
entry_birth_location = ttk.Entry(frame_overview)
entry_birth_location.grid(row=4, column=3, padx=5, pady=5, sticky='w')

# Death Date entry
label_death_date = ttk.Label(frame_overview, text="Death date: ")
label_death_date.grid(row=5, column=0, padx=2, pady=5, sticky='e')
entry_death_date = ttk.Entry(frame_overview)
entry_death_date.grid(row=5, column=1, padx=2, pady=5, sticky='w')

# Death Location entry
label_death_location = ttk.Label(frame_overview, text="Death place: ")
label_death_location.grid(row=5, column=2, padx=5, pady=5, sticky='e')
entry_death_location = ttk.Entry(frame_overview)
entry_death_location.grid(row=5, column=3, padx=5, pady=5, sticky='w')

# Death Cause entry
label_death_cause = ttk.Label(frame_overview, text="Death Cause: ")
label_death_cause.grid(row=5, column=4, padx=5, pady=5, sticky='e')
entry_death_cause = ttk.Entry(frame_overview)
entry_death_cause.grid(row=5, column=5, padx=5, pady=5, sticky='w')

# Buried Date entry
label_buried_date = ttk.Label(frame_overview, text="Buried date: ")
label_buried_date.grid(row=6, column=0, padx=2, pady=5, sticky='e')
entry_buried_date = ttk.Entry(frame_overview)
entry_buried_date.grid(row=6, column=1, padx=2, pady=5, sticky='w')

# Buried Location entry
label_buried_location = ttk.Label(frame_overview, text="Buried Location: ")
label_buried_location.grid(row=6, column=2, padx=5, pady=5, sticky='e')
entry_buried_location = ttk.Entry(frame_overview, width=50)
entry_buried_location.grid(row=6, column=3, padx=5, pady=5, sticky='ew')

# Buried Notes entry
label_buried_notes = ttk.Label(frame_overview, text="Buried Notes: ")
label_buried_notes.grid(row=7, column=0, padx=5, pady=5, sticky='e')
entry_buried_notes = ttk.Entry(frame_overview, width=35)
entry_buried_notes.grid(row=7, column=1, padx=2, pady=5, sticky='w')

# Buried Source entry
label_buried_source = ttk.Label(frame_overview, text="Buried Source: ")
label_buried_source.grid(row=7, column=2, padx=2, pady=5, sticky='e')
entry_buried_source = ttk.Entry(frame_overview)
entry_buried_source.grid(row=7,column=3, padx=2, pady=5, sticky='w')

# --- Buried Link Label and Entry ---
label_buried_link = ttk.Label(frame_overview, text="Buried Link: ")
label_buried_link.grid(row=8, column=0, padx=5, pady=5, sticky='e')

entry_buried_link = ttk.Entry(frame_overview, width=35)
entry_buried_link.grid(row=8, column=1, padx=5, pady=5, sticky='w')

# --- Button Frame (column 2) ---
buried_link_button_frame = ttk.Frame(frame_overview)
buried_link_button_frame.grid(row=8, column=2, padx=5, pady=5, sticky='w')

# --- Create both buttons immediately but don't pack yet ---
button_buried_link = ttk.Button(buried_link_button_frame, text="Open Link", command=lambda: open_link(entry_buried_link.get()))
button_findagrave = ttk.Button(buried_link_button_frame, text="Search FindAGrave", command=lambda: search_findagrave)

# --- Toggle the correct button ---
def toggle_findagrave_buttons():
    # Remove all widgets first
    for widget in buried_link_button_frame.winfo_children():
        widget.pack_forget()

    if entry_buried_link.get().strip():
        button_buried_link.pack()
    else:
        button_findagrave.pack()

# --- Bind changes ---
entry_buried_link.bind("<FocusOut>", lambda event: toggle_findagrave_buttons())
entry_buried_link.bind("<KeyRelease>", lambda event: toggle_findagrave_buttons())

# --- Initialize correct button at startup ---
toggle_findagrave_buttons()


# Buried Block Label
label_buried_block = ttk.Label(frame_overview, text="Buried Block:")
label_buried_block.grid(row=8, column=3, padx=5, pady=5, sticky='e')

# Buried Block Entry
entry_buried_block = ttk.Entry(frame_overview, width=10)
entry_buried_block.grid(row=8, column=4, padx=5, pady=5, sticky='w')

#Cemetery Tour Link
label_cem_tour_link = ttk.Label(frame_overview, text="Cem Tour Link: ")
label_cem_tour_link.grid(row=9, column=0, padx=5, pady=5, sticky='e')
entry_cem_tour_link = ttk.Entry(frame_overview, width=15)
entry_cem_tour_link.grid(row=9, column=1, padx=5, pady=5, sticky='w')
button_cem_tour_link = ttk.Button(frame_overview, text="Open Link", command=lambda: open_link(entry_cem_tour_link.get()))
button_cem_tour_link.grid(row=9, column=2, padx=5, pady=5, sticky='w')

# Separator on the form
separator = ttk.Separator(frame_overview, orient='horizontal')
separator.grid(row=10, columnspan=6, pady=10, sticky='ew')

# Father entry
father_var = tk.StringVar()
entry_father = ttk.Label(frame_overview, textvariable=father_var, width=7)
entry_father.grid(row=11, column=3, padx=1, pady=5, sticky='e')
label_father = ttk.Label(frame_overview, text="Father: ")
label_father.grid(row=11, column=0, padx=0, pady=5, sticky='e')

#Display the Father's Name
label_father_name = ttk.Label(frame_overview, text="Fathers Name Goes Here")
label_father_name.grid(row=11, column=1, padx=0, pady=1, sticky='w')
label_father_name.bind("<Double-1>", open_father_record)
ttk.Button(
    frame_overview,
    text="Link or Add Father",
    command=lambda: open_person_linkage_popup(record_id, role='father', refresh_callback=refresh_parent_vars)
).grid(row=11, column=4, padx=5, pady=5, sticky='w')

# Mother entry
mother_var = tk.StringVar()
entry_mother = ttk.Label(frame_overview, textvariable=mother_var, width=7)
entry_mother.grid(row=12, column=3, padx=2, pady=5, sticky='e')
label_mother = ttk.Label(frame_overview, text="Mother:")
label_mother.grid(row=12, column=0, padx=2, pady=5, sticky='e')

#Display the Mother's Name
label_mother_name = ttk.Label(frame_overview, text="Mother's Name Goes Here")
label_mother_name.grid(row=12, column=1, padx=0, pady=1, sticky='w')
label_mother_name.bind("<Double-1>", open_mother_record)
ttk.Button(
    frame_overview,
    text="Link or Add Mother",
    command=lambda: open_person_linkage_popup(record_id, role='mother', refresh_callback=refresh_parent_vars)
).grid(row=12, column=4, padx=5, pady=5, sticky='w')

# Separator on the form
separator = ttk.Separator(frame_overview, orient='horizontal')
separator.grid(row=13, columnspan=6, pady=10, sticky='ew')

# Marriage Date entry
label_marriage_date = ttk.Label(frame_overview, text="Marriage Date: ")
label_marriage_date.grid(row=15, column=0, padx=5, pady=5, sticky='e')
label2_marriage_date = ttk.Label(frame_overview, text="")
label2_marriage_date.grid(row=15, column=1, padx=5, pady=5, sticky='w')

#Marriage End Date
label_marriage_end_date = ttk.Label(frame_overview, text="Marriage End Date: ")
label_marriage_end_date.grid(row=15, column=2, padx=5, pady=5, sticky='e')
label2_marriage_end_date = ttk.Label(frame_overview, text="")
label2_marriage_end_date.grid(row=15, column=3, padx=5, pady=5, sticky='w')

# Marriage Location entry
label_marriage_location = ttk.Label(frame_overview, text="Marriage Location: ")
label_marriage_location.grid(row=16, column=0, padx=5, pady=5, sticky='e')
label2_marriage_location = ttk.Label(frame_overview, text="")
label2_marriage_location.grid(row=16, column=1, padx=5, pady=5, sticky='w')

label_marriage_note = ttk.Label(frame_overview, text="Marriage Notes: ")
label_marriage_note.grid(row=17, column=0, padx=5, pady=5, sticky='e')
label2_marriage_note = ttk.Label(frame_overview, text="")
label2_marriage_note.grid(row=17, column=1, padx=5, pady=5, sticky='w')

label_marriage_link = ttk.Label(frame_overview, text="Marriage Link:")
label_marriage_link.grid(row=18, column=0, padx=5, pady=5, sticky='e')
label2_marriage_link = ttk.Label(frame_overview, text="")
label2_marriage_link.grid(row=18, column=1, padx=5, pady=5, sticky='w')

# Open Married Link button
button_married_link = ttk.Button(frame_overview, text="Open Link", command=lambda: open_link(entry_buried_link.get()))

# Check the button's text and display or hide it accordingly
if label_marriage_link.cget('text') != "Marriage Link:":
    button_marriage_link = ttk.Button(frame_overview, text="Open Link", command=lambda: open_link(entry_buried_link.get()))
    button_marriage_link.grid(row=18, column=2, padx=5, pady=5, sticky='w')


def update_children_tree_on_spouse_selection(event=None):
    selected_spouse_info = spouse_dropdown.get()
    
    # Ensure spouse_id is only set when there is selected spouse info
    if selected_spouse_info:
        spouse_id = selected_spouse_info.split(':')[0].strip()
    else:
        print("No spouse selected.")
        # You can add any additional handling for when no spouse is selected

    if spouse_id:
        # Fetch marriage details
        cursor.execute("SELECT m_date, m_end_date, m_location, m_note, m_link FROM Marriages WHERE (person1_id = ? AND person2_id = ?) OR (person1_id = ? AND person2_id = ?)", (record_id, spouse_id, spouse_id, record_id))
        marriage_info = cursor.fetchone()

        if marriage_info:
            # Update marriage date and location labels
            marriage_date, marriage_end_date, marriage_location, marriage_note, marriage_link = marriage_info
            label2_marriage_date.config(text=f"{marriage_date if marriage_date else ''}")
            label2_marriage_end_date.config(text=f"{marriage_end_date if marriage_end_date else ''}")
            label2_marriage_location.config(text=f"{marriage_location if marriage_location else ''}")
            label2_marriage_note.config(text=f"{marriage_note if marriage_note else ''}")
            label2_marriage_link.config(text=f"{marriage_link if marriage_link else ''}")
       
            if marriage_end_date:
                label2_marriage_end_date.config(text=marriage_end_date)
                label_marriage_end_date.grid()  # Show the label if hidden
                label2_marriage_end_date.grid()  # Show the label if hidden
            else:
                label_marriage_end_date.grid_remove()  # Hide the label
                label2_marriage_end_date.grid_remove()  # Hide the label
    else:
            # Clear all marriage details labels if no marriage info found
            label2_marriage_date.config(text="")
            label2_marriage_location.config(text="")
            label2_marriage_note.config(text="")
            label2_marriage_link.config(text="")
            label_marriage_end_date.grid_remove()  # Hide the label
            label2_marriage_end_date.grid_remove()  # Hide the label        

    # Fetch and display children of the selected spouse
    query = """
        SELECT id, first_name, middle_name, last_name, title, nick_name, married_name, birth_date, birth_location, death_date, death_location 
        FROM People 
        WHERE father = ? AND mother = ? OR father = ? AND mother = ?
    """
    cursor.execute(query, (record_id, spouse_id, spouse_id, record_id))
    children = cursor.fetchall()

    # Convert birth dates and sort
    children_with_dates = [(child, convert_to_sortable_date(child[7])) for child in children]
    children_with_dates.sort(key=lambda x: x[1] or "")  # Sort by the converted date, placing None values last

    # Clear existing data in the treeview
    for i in children_tree.get_children():
        children_tree.delete(i)

    for child, _ in children_with_dates:
        formatted_child = [
            child[0],  # ID
            child[1] if child[1] is not None else "",  # First Name
            child[2] if child[2] is not None else "",  # Middle Name
            child[3] if child[3] is not None else "",  # Last Name
            child[4] if child[4] is not None else "",  # Title
            child[5] if child[5] is not None else "",  # Nick Name
            child[6] if child[6] is not None else "",  # Married Name
            format_date(child[7]),  # Birth Date
            child[8] if child[8] is not None else "",  # Birth Location
            format_date(child[9]),  # Death Date
            child[10] if child[10] is not None else ""  # Death Location
        ]
        children_tree.insert('', 'end', values=formatted_child)

    update_remove_button_state()
    # Adjust the height of the tree to match the number of children
    max_visible_rows = 6
    children_tree['height'] = min(len(children), max_visible_rows)

# Separator on the form
separator = ttk.Separator(frame_overview, orient='horizontal')
separator.grid(row=19, columnspan=6, pady=10, sticky='ew')

# Create a Treeview to display children
label_children = ttk.Label(frame_overview, text="Children:")
label_children.grid(row=20, column=0, padx=5, pady=5, sticky="w")

# Initialize the Treeview
children_tree = ttk.Treeview(frame_overview, columns=("ID", "First Name", "Middle Name", "Last Name", "Title", "Nick Name", "Married Name", "Birth Date", "Birth Location", "Death Date", "Death Location"), show='headings')

# Configure headings and columns
column_settings = {
    "ID": (35, "w"),
    "First Name": (100, "w"),
    "Middle Name": (75, "w"),
    "Last Name": (100, "w"),
    "Title": (35, "w"),
    "Nick Name": (45, "w"),
    "Married Name": (100, "w"),
    "Birth Date": (75, "w"),
    "Birth Location": (125, "w"),
    "Death Date": (75, "w"),
    "Death Location": (125, "w")
}

for col, (width, anchor) in column_settings.items():
    children_tree.heading(col, text=col)
    children_tree.column(col, width=width, anchor=anchor)

# Create a vertical scrollbar
v_scroll = ttk.Scrollbar(frame_overview, orient="vertical", command=children_tree.yview)
children_tree.configure(yscrollcommand=v_scroll.set)

# Grid the tree and scrollbar
children_tree.grid(row=21, column=0, columnspan=5, padx=5, pady=5, sticky='ewns')
v_scroll.grid(row=21, column=5, padx=0, pady=5, sticky='ns')  # Adjust column index as needed

# Bind double-click event
children_tree.bind('<Double-1>', open_child_record)
children_tree.bind("<<TreeviewSelect>>", update_remove_button_state)


# Create the Spouse Dropdown Combobox
label_spouse_dropdown = ttk.Label(frame_overview, text="Spouse(s): ↑")
label_spouse_dropdown.grid(row=14, column=0, padx=5, pady=5, sticky='e')
#create_spouse_dropdown_menu()

spouse_dropdown = ttk.Combobox(frame_overview, width=40)
#populate_spouse_dropdown(record_id)
#spouse_dropdown.bind("<<ComboboxSelected>>", update_children_tree_on_spouse_selection)

spouse_dropdown.grid(row=14, column=1, padx=5, pady=5, sticky='ew')

def display_children():
    query = "SELECT id, first_name, middle_name, last_name, title, nick_name, married_name, birth_date, birth_location, death_date, death_location FROM People WHERE father = ? OR mother = ?"
    cursor.execute(query, (record_id, record_id))
    children = cursor.fetchall()

    # Convert birth dates and sort
    children_with_dates = [(child, convert_to_sortable_date(child[7])) for child in children]
    children_with_dates.sort(key=lambda x: x[1] or "")  # Sort by the converted date, placing None values last

    # Clear existing data in the treeview
    for i in children_tree.get_children():
        children_tree.delete(i)

    # Inserting each child into the treeview
    for child, _ in children_with_dates:
        formatted_child = [
            child[0],  # ID
            child[1] if child[1] is not None else "",  # First Name
            child[2] if child[2] is not None else "",  # Middle Name
            child[3] if child[3] is not None else "",  # Last Name
            child[4] if child[4] is not None else "",  # Title
            child[5] if child[5] is not None else "",  # Nick Name
            child[6] if child[6] is not None else "",  # Married Name
            format_date(child[7]),  # Birth Date
            child[8] if child[8] is not None else "",  # Birth Location
            format_date(child[9]),  # Death Date
            child[10] if child[10] is not None else ""  # Death Location
        ]
        children_tree.insert('', 'end', values=formatted_child)

    # Adjust the height of the tree to match the number of children, up to a maximum
    max_visible_rows = 8  # Set a maximum for better UI experience
    children_tree['height'] = min(len(children), max_visible_rows)
    update_remove_button_state()

has_spouses = populate_spouse_dropdown(record_id)
refresh_func = (lambda: update_children_tree_on_spouse_selection(None)) if has_spouses else display_children

button_add_or_link_child = ttk.Button(
    frame_overview,
    text="Add or Link Child",
    command=lambda: open_person_linkage_popup(record_id, role='child', refresh_callback=refresh_func)
)
button_add_or_link_child.grid(row=22, column=0, padx=5, pady=(0, 10), sticky='w')

button_remove_child = ttk.Button(
    frame_overview,
    text="Remove Selected Child",
    command=remove_selected_child,
    state='disabled'
)
button_remove_child.grid(row=22, column=1, padx=5, pady=(0, 10), sticky='w')

if has_spouses:
    # Only call if there are spouses, this will set the children for the first spouse
    update_children_tree_on_spouse_selection(None)
else:
    # Call display_children if there are no spouses
    display_children()

# Separator on the form
separator = ttk.Separator(frame_overview, orient='horizontal')
separator.grid(row=23, columnspan=6, pady=10, sticky='ew')

# Business entry
label_business = ttk.Label(frame_overview, text="Business: ")
label_business.grid(row=24, column=0, padx=2, pady=5, sticky='e')
entry_business = ttk.Entry(frame_overview)
entry_business.grid(row=24, column=1, padx=2, pady=5, sticky= 'w')

# Occupation entry
label_occupation = ttk.Label(frame_overview, text="Occupation: ")
label_occupation.grid(row=24, column=2, padx=2, pady=5, sticky='e')
entry_occupation = ttk.Entry(frame_overview)
entry_occupation.grid(row=24, column=3, padx=1, pady=5, sticky= 'w')

# Notes entry
label_notes = ttk.Label(frame_overview, text="Notes: ")
label_notes.grid(row=26, column=0, padx=2, pady=5, sticky='e')
entry_notes = ttk.Entry(frame_overview, width =40)
entry_notes.grid(row=26, column=1, padx=1, pady=5, sticky= 'w')

# Separator on the form
separator = ttk.Separator(frame_overview, orient='horizontal')
separator.grid(row=27, columnspan=6, pady=10, sticky='ew')

# Set the form fields with the record data
entry_id_var.set(person_record[0] if person_record[0] is not None else '')
entry_first_name.insert(0, person_record[1] if person_record[1] is not None else '')
entry_middle_name.insert(0, person_record[2] if person_record[2] is not None else '')
entry_last_name.insert(0, person_record[3] if person_record[3] is not None else '')
entry_title.insert(0, person_record[4] if person_record[4] is not None else '')
entry_nick_name.insert(0, person_record[5] if person_record[5] is not None else '')
entry_married_name.insert(0, person_record[6] if person_record[6] is not None else '')
father_var.set(person_record[7] if person_record[7] is not None else '')
mother_var.set(person_record[8] if person_record[8] is not None else '')
entry_birth_date.insert(0, person_record[9] if person_record[9] is not None else '')
entry_birth_location.insert(0, person_record[10] if person_record[10] is not None else '')
entry_death_date.insert(0, person_record[11] if person_record[11] is not None else '')
entry_death_location.insert(0, person_record[12] if person_record[12] is not None else '')
entry_death_cause.insert(0, person_record[13] if person_record[13] is not None else '')
entry_buried_date.insert(0, person_record[14] if person_record[14] is not None else '')
entry_buried_location.insert(0, person_record[15] if person_record[15] is not None else '')
entry_buried_notes.insert(0, person_record[16] if person_record[16] is not None else '')
entry_buried_source.insert(0, person_record[17] if person_record[17] is not None else '')
entry_business.insert(0, person_record[18] if person_record[18] is not None else '')
entry_occupation.insert(0, person_record[19]if person_record[19] is not None else '')
entry_notes.insert(0, person_record[21]if person_record[21] is not None else '')
entry_buried_link.insert(0, person_record[22]if person_record[22] is not None else '')
toggle_findagrave_buttons()
entry_buried_block.insert(0, person_record[23] if person_record[23] is not None else '')
entry_cem_tour_link.insert(0, person_record[24] if person_record[24] is not None else '')


# After filling the form fields with the record data
# update_spouse_name()  # Update the spouse's name label
update_father_name()  # Update the father's name label
update_mother_name()  # Update the mother's name label

# Create a frame for the buttons
frame_buttons = ttk.Frame(frame_overview)
frame_buttons.grid(row=28, column=2, pady=10, sticky="nsew")
apply_context_menu_to_all_entries(frame_overview)

# Edit/Save Button
edit_button = ttk.Button(frame_buttons, text="Update", command=update_record)
edit_button.grid(row=0, column=0, padx=5)
edit_button.bind("<Return>", lambda event: on_enter(event, update_record))

# Close Button
button_close = ttk.Button(frame_buttons, text="Close", command=close_form)
button_close.grid(row=0, column=1, padx=5)
button_close.bind("<Return>", lambda event: on_enter(event, close_form))

# Add Photo Button
add_photo_button = ttk.Button(frame_buttons, text="Add Photo", command=add_a_photo)
add_photo_button.grid(row=0, column=2, padx=5)
add_photo_button.bind("<Return>", lambda event: on_enter(event, add_a_photo))
        
display_image(frame_photo, image_path, add_photo_button)

# Add-info button to create new links
add_info_btn = ttk.Button(frame_photo, text="+", width=3, command=open_add_menu)
add_info_btn.grid(row=1, column=0, pady=5)

# Button to open dynamic photo menu
photo_menu_btn = ttk.Button(frame_photo, text="Menu", width=5, command=open_photo_menu)
photo_menu_btn.grid(row=1, column=1, padx=5, pady=5)

# Right-click on photo area to open the menu
frame_photo.bind("<Button-3>", open_photo_menu)

my_custom_locations = get_custom_list('custom_locations')
my_custom_cemeteries = get_custom_list('custom_cemeteries')
create_context_menu(entry_birth_location, my_custom_locations)
create_context_menu(entry_death_location, my_custom_locations)
#create_context_menu(entry_marriage_location, my_custom_locations)
create_context_menu(entry_buried_location, my_custom_cemeteries)

# Run the GUI window
window.mainloop()

# Close the database connection
connection.close()