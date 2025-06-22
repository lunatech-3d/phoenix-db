import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk
import sqlite3
import sys
import webbrowser
import subprocess
from tkinter import filedialog
from datetime import datetime

#Local Imports
from app.config import PATHS, DB_PATH
from app.date_utils import parse_date_input, format_date_for_display, add_date_format_menu

def edit_mayor_form():
    
    global image_label
    global current_index
    entries = []
    
    # start creating the GUI
    window = tk.Tk()
    window.title("Edit Mayor")

    # Create StringVar instances for the Entry fields
    first_name_var = tk.StringVar()
    middle_name_var = tk.StringVar()
    last_name_var = tk.StringVar()
    married_name_var = tk.StringVar()
    term_start_var = tk.StringVar()
    term_start_precision_var = tk.StringVar()
    term_end_var = tk.StringVar()
    term_end_precision_var = tk.StringVar()
    election_link_var = tk.StringVar()

    vars_map = {
        'first_name': first_name_var,
        'middle_name': middle_name_var,
        'last_name': last_name_var,
        'married_name': married_name_var,
        'mayor_term_start': term_start_var,
        'mayor_term_start_precision': term_start_precision_var,
        'mayor_term_end': term_end_var,
        'mayor_term_end_precision': term_end_precision_var,
        'mayor_election_link': election_link_var
    }

    def display_image(image_label, image_path):
        if image_path:
            # Open the image file
            image = Image.open(image_path)

            # Calculate the ratio to keep aspect ratio
            ratio = 250.0 / image.height
            
            # Calculate the width using the same ratio
            width = int(image.width * ratio)

            # Resize the image
            image = image.resize((width, 250), Image.BILINEAR)

            photo = ImageTk.PhotoImage(image)
            image_label.config(image=photo)
            image_label.image = photo
        else:
            image_label.config(image='')

    #def display_image(image_label, image_path):
        #if image_path:
            #image = Image.open(image_path)
            #photo = ImageTk.PhotoImage(image)
            #image_label.config(image=photo)
            #image_label.image = photo
        #else:
            #image_label.config(image='')

    def update_data_frame(data_frame, data):
        entries.clear()
        for widget in data_frame.winfo_children():
            widget.destroy()

        labels = ['First Name', 'Middle Name', 'Last Name', 'Married Name', 'Term Start', 'Term End', 'Election Link']
        ttk.Label(data_frame, text="").grid(row=0, column=0, columnspan=2, padx=(10, 5), pady=(5, 5))
        for i, label in enumerate(labels):
            ttk.Label(data_frame, text=label).grid(row=i+1, column=0, padx=(10, 5), pady=(5, 5), sticky='w')
            key = label.lower().replace(' ', '_')
            if key in ['term_start', 'term_end', 'election_link']:
                key = 'mayor_' + key

            state = 'normal' if edit_mode and key in ['mayor_term_start', 'mayor_term_end', 'mayor_election_link'] else 'readonly'
            entry = ttk.Entry(data_frame, textvariable=vars_map[key], state=state)
            entry.grid(row=i+1, column=1, padx=(5, 10), pady=(5, 5), sticky='w')
            entries.append(entry)

            if key in ['mayor_term_start', 'mayor_term_end']:
                add_date_format_menu(entry)

    def display_mayor_data(data):
        entries_data_keys = ['first_name', 'middle_name', 'last_name', 'married_name', 'mayor_term_start', 'mayor_term_end', 'mayor_election_link']

        for key in entries_data_keys:
            if key in ['mayor_term_start', 'mayor_term_end']:
                formatted_date = format_date_for_display(data[key], data[key + '_precision'])
                vars_map[key].set(formatted_date)
            else:
                vars_map[key].set(data[key])

        for i, key in enumerate(entries_data_keys):
            if key in ['first_name', 'middle_name', 'last_name', 'married_name', 'mayor_election_link']:
                entries[i].config(state='readonly')
            else:
                entries[i].config(state='normal')

        display_image(image_label, data["image_path"])


    id = sys.argv[1]
    
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    edit_mode = False

    def fetch_mayor_data(mayor_id):
    
        global main_rec_id

        query = f"""
        SELECT People.id, People.first_name, People.middle_name, People.last_name, People.married_name,
        Mayor.mayor_id, Mayor.mayor_term_start, Mayor.mayor_term_start_precision, 
        Mayor.mayor_term_end, Mayor.mayor_term_end_precision, Mayor.mayor_election_link, Photos.image_path
        FROM Mayor
        INNER JOIN People ON Mayor.mayor_id = People.id
        LEFT JOIN Photos ON People.id = Photos.person_id
        WHERE Mayor.id = {mayor_id}
        ORDER BY Mayor.mayor_term_start ASC
        """
        cursor.execute(query)
        record = cursor.fetchone()

        if record is None:
                print(f"No data found for mayor_id {mayor_id}")
                print(f"query string is: {query}")
                return None

        #print(f"query string is: {query}")

        # create dictionary
        data_dict = {
            "main_rec_id": record[0],
            "first_name": record[1],
            "middle_name": record[2],
            "last_name": record[3],
            "married_name": record[4],
            "mayor_id": record[5],
            "mayor_term_start": record[6],
            "mayor_term_start_precision": record[7],
            "mayor_term_end": record[8],
            "mayor_term_end_precision": record[9],
            "mayor_election_link": record[10],
            "image_path": record[11]
        }
        #print(f"data dictionary is: {data_dict}")
        main_rec_id= record[0]
        return data_dict

    # Functions for the Prev and Next Mayor buttons

    def fetch_all_mayor_ids():
        query = """
        SELECT id
        FROM Mayor
        ORDER BY mayor_term_start
        """
        cursor.execute(query)
        records = cursor.fetchall()
        return [record[0] for record in records]


    def load_prev_mayor():
        global current_index
        if current_index > 0:  # there is a previous mayor
            current_index -= 1  # decrement the current index
            data = fetch_mayor_data(all_mayor_ids[current_index])  # fetch the data for the new current mayor
            display_mayor_data(data)  # display the new data

    def load_next_mayor():
        global current_index
        if current_index < len(all_mayor_ids) - 1:  # there is a next mayor
            current_index += 1  # increment the current index
            data = fetch_mayor_data(all_mayor_ids[current_index])  # fetch the data for the new current mayor
            display_mayor_data(data)  # display the new data


    # Fetch a list of all mayor IDs, sorted by term
    all_mayor_ids = fetch_all_mayor_ids()

    # Find the index of the current mayor in all_mayor_ids
    current_index = all_mayor_ids.index(int(id))

    # Fetch the data for the current mayor
    data = fetch_mayor_data(int(id))
    
    print(f"data found for mayor_id {data}")
    if data is None:    
        print("No data to display.")
        return


    def save_mayor_data():
        if not edit_mode:
            return

        term_start = term_start_var.get()
        term_end = term_end_var.get()
        election_link = election_link_var.get()

        try:
            db_term_start, db_term_start_precision = parse_date_input(term_start)
            db_term_end, db_term_end_precision = parse_date_input(term_end)
        except ValueError as e:
            tk.messagebox.showerror('Invalid Input', str(e))
            return

        query = f"""
        UPDATE Mayor
        SET mayor_term_start = ?, mayor_term_start_precision = ?,
            mayor_term_end = ?, mayor_term_end_precision = ?,
            mayor_election_link = ?
        WHERE id = ?
        """

        cursor.execute(query, (db_term_start, db_term_start_precision, db_term_end, db_term_end_precision, election_link, id))
        connection.commit()


    def switch_mode():
        nonlocal edit_mode
        edit_mode = not edit_mode

        if edit_mode:
            entry_term_start.config(state='normal')
            entry_term_end.config(state='normal')
            entry_election_link.config(state='normal')
            edit_button.config(text='Save')
        else:
            entry_term_start.config(state='readonly')
            entry_term_end.config(state='readonly')
            entry_election_link.config(state='readonly')
            save_mayor_data()
            edit_button.config(text='Edit')


    def add_photo():
        image_path = filedialog.askopenfilename(initialdir = "assets/images/thumb",title = "Select file",filetypes = (("jpeg files","*.jpg"),("all files","*.*")))
        query = """
        INSERT INTO Photos (person_id, image_path)
        VALUES (?, ?)
        """
        cursor.execute(query, (data["mayor_id"], image_path))
        connection.commit()
        data["image_path"] = image_path  # update the data dictionary
        display_image(image_label, data["image_path"])  # display the new image

    
    def open_pdf_link():
        url = election_link_var.get()
        browser = webbrowser.get()
        browser.open(url, new=2)

    def open_main_rec():
        print(f"Mayor ID is: {main_rec_id}")
        subprocess.Popen([sys.executable, "-m", "app.editme", str(main_rec_id)])
        window.destroy()
    
    window_width = 600
    window_height = 360
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # Top frame for photo and data
    top_frame = ttk.Frame(window)
    top_frame.pack(side='top', fill='x')

    # Photo frame inside the top frame
    photo_frame = ttk.Frame(top_frame)
    photo_frame.pack(side='left', fill='y')

    image_label = ttk.Label(photo_frame)
    image_label.pack(padx=10, pady=10)

    display_image(image_label, data["image_path"])

    # Data frame inside the top frame
    parent_frame = ttk.Frame(top_frame)
    parent_frame.pack(side='right', fill='both', expand=True)

    data_frame = ttk.Frame(parent_frame)
    data_frame.pack(side='top', fill='x')

    # Display mayor info
    labels = ['First Name', 'Middle Name', 'Last Name', 'Married Name', 'Term Start', 'Term End', 'Election Link']
    
    ttk.Label(data_frame, text="").grid(row=0, column=0, columnspan=2, padx=(10, 5), pady=(5, 5))
    for i, label in enumerate(labels):
        ttk.Label(data_frame, text=label).grid(row=i+1, column=0, padx=(10, 5), pady=(5, 5), sticky='w')
        key = label.lower().replace(' ', '_')
        if key in ['term_start', 'term_end', 'election_link']:
            key = 'mayor_' + key

        state = 'readonly'
        entry = ttk.Entry(data_frame, textvariable=vars_map[key], state=state)
        entry.grid(row=i+1, column=1, padx=(5, 10), pady=(5, 5), sticky='w')
        entries.append(entry)

    if key in ['mayor_term_start', 'mayor_term_end']:
            add_date_format_menu(entry)

    display_mayor_data (data)
        
    # Update this part to correctly assign entry widgets
    entry_term_start = entries[4]
    entry_term_end = entries[5]
    entry_election_link = entries[6]

    # Bottom frame for the buttons
    buttons_frame = ttk.Frame(parent_frame)
    buttons_frame.pack(side='bottom', fill='x')
    
    # Open link button
    open_link_button = ttk.Button(buttons_frame, text='Open Link', command=open_pdf_link)
    open_link_button.pack(side='left', padx=5, pady=10)

    # Edit button
    edit_button = ttk.Button(buttons_frame, text="Edit", command=switch_mode)
    edit_button.pack(side='left', padx=5, pady=10)
    
    # Add Photo button
    #photo_button = ttk.Button(buttons_frame, text="Add Photo", command=add_photo)
    #photo_button.pack(side='left', padx=10, pady=10) 

    #Open Rec button
    open_rec_button = ttk.Button(buttons_frame, text="Main Record", command=open_main_rec)
    open_rec_button.pack(side='left',padx=5, pady=5)
    
    # Cancel button - Just closes the window without saving changes
    cancel_button = ttk.Button(buttons_frame, text="Cancel", command=window.destroy)
    cancel_button.pack(side='right', padx=5, pady=10)
    
    prev_button_frame = ttk.Frame(window)
    prev_button_frame.pack(side='left', fill='x', expand=True)

    next_button_frame = ttk.Frame(window)
    next_button_frame.pack(side='right', fill='x', expand=True)

    prev_button = ttk.Button(prev_button_frame, text="Prev Mayor", command=load_prev_mayor)
    prev_button.pack(side='left', padx=5, pady=10)

    next_button = ttk.Button(next_button_frame, text="Next Mayor", command=load_next_mayor)
    next_button.pack(side='right', padx=5, pady=10)

    window.mainloop()

if __name__ == "__main__":
    edit_mayor_form()
