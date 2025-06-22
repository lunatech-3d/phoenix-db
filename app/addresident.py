import tkinter as tk
from tkinter import ttk
import sqlite3
import sys
from .config import DB_PATH, PATHS

# Connect to the database
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check if an id is passed as a command-line argument
#if len(sys.argv) > 1:
#    try:
#        person_id = int(sys.argv[1])
#    except ValueError:
#        print("Invalid person id provided.")
#        sys.exit(1)
#else:
#    person_id = None


def search_people():
    last_name = people_search_entry.get()
    if last_name:
        c.execute("SELECT id, first_name, middle_name, last_name, married_name, birth_date FROM People WHERE last_name LIKE ? OR married_name LIKE ?", (f"%{last_name}%", f"%{last_name}%"))

        search_results = c.fetchall()
        person_tree.delete(*person_tree.get_children())
        for record in search_results:
            person_tree.insert("", tk.END, values=record)


def search_address():
    # Clear previous search results
    address_tree.delete(*address_tree.get_children())

    # Retrieve search query from the search field
    query = address_search_entry.get().lower()

    # Filter address records based on the search query
    for record in address_records:
        address_id, address = record
        if address and query.lower() in address.lower():
            address_tree.insert("", tk.END, values=(address_id, address))

def reset_person_id():
    global person_id
    person_id = None


# Create the GUI window
window = tk.Tk()
window.title("ResHistory Records")

# Set the window size and position
window_width = 1200
window_height = 800
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Create a frame for the trees and fields
frame = ttk.Frame(window)
frame.pack(padx=10, pady=10)

# Create a 70/30 split layout
frame.columnconfigure(0, weight=7)
frame.columnconfigure(1, weight=3)

# Create a 2-column frame for the search boxes
search_frame = ttk.Frame(frame)
search_frame.grid(row=0, column=0, columnspan=2, pady=5)

# Create the search box for People
people_search_label = ttk.Label(search_frame, text="Search by Last Name:")
people_search_label.grid(row=0, column=0, padx=5, pady=5)
people_search_entry = ttk.Entry(search_frame)
people_search_entry.grid(row=0, column=1, padx=5, pady=5)

# Add the search button for People
people_search_button = ttk.Button(search_frame, text="Search")
people_search_button.grid(row=0, column=2, padx=5, pady=5)
people_search_button.config(command=search_people)


# Create a 2-column frame for the address search boxes
address_search_frame = ttk.Frame(frame)
address_search_frame.grid(row=0, column=1, pady=5)

# Create the search box for Address
address_search_label = ttk.Label(address_search_frame, text="Search by Address:")
address_search_label.grid(row=0, column=0, padx=5, pady=5)
address_search_entry = ttk.Entry(address_search_frame)
address_search_entry.grid(row=0, column=1, padx=5, pady=5)

# Add the search button for Address
address_search_button = ttk.Button(address_search_frame, text="Search")
address_search_button.grid(row=0, column=2, padx=5, pady=5)
address_search_button.config(command=search_address)

# Create a treeview for selecting a person
person_tree = ttk.Treeview(frame)
person_tree["columns"] = ("ID", "First Name", "Middle Name", "Last Name", "Married Name", "Birth Date")
person_tree.heading("#0", text="ID")
person_tree.column("#0", width=50)
person_tree.heading("ID", text="ID")
person_tree.column("ID", width=50)
person_tree.heading("First Name", text="First Name")
person_tree.column("First Name", width=100)
person_tree.heading("Middle Name", text="Middle Name")
person_tree.column("Middle Name", width=100)
person_tree.heading("Last Name", text="Last Name")
person_tree.column("Last Name", width=100)
person_tree.heading("Married Name", text="Married Name")
person_tree.column("Married Name", width=100)
person_tree.heading("Birth Date", text="Birth Date")
person_tree.column("Birth Date", width=100)

# Retrieve records from the People table
c.execute("SELECT id, first_name, middle_name, last_name, married_name, birth_date FROM People")
people_records = c.fetchall()

# Insert records into the person treeview
for record in people_records:
    person_tree.insert("", tk.END, values=record)

person_tree.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

# Create a treeview for selecting an address
address_tree = ttk.Treeview(frame, show="headings")
address_tree["columns"] = ("ID", "Address")
address_tree.heading("ID", text="ID")
address_tree.column("ID", width=25)
address_tree.heading("Address", text="Address")
address_tree.column("Address", width=200)

# Retrieve records from the Address table
c.execute("SELECT address_id, address FROM Address")
address_records = c.fetchall()

# Insert records into the address treeview
for record in address_records:
    address_tree.insert("", tk.END, values=record)

address_tree.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
#person_tree.bind("<<TreeviewSelect>>", lambda event: reset_person_id())

# Create a frame for the buttons
button_frame = ttk.Frame(window)
button_frame.pack(pady=10)

def add_resident():
    selected_person = person_tree.selection()
    selected_address = address_tree.selection()
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()
    
    if selected_person and selected_address and start_date and end_date:
        person_id = person_tree.item(selected_person)["values"][0]
        address_id = address_tree.item(selected_address)["values"][0]
        print(f"Person ID: {person_id}")
        print(f"Address ID: {address_id}")
        print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")
        
        # Add code to insert the record into the ResHistory table here
        c.execute("INSERT INTO ResHistory (owner_id, address_id, start_date, end_date) VALUES (?, ?, ?, ?)",
                  (person_id, address_id, start_date, end_date))
        conn.commit()
        print("Record inserted successfully!")
        
    else:
        print("Please select a person, address, start date, and end date.")

start_date_label = ttk.Label(button_frame, text="Start Date:")
start_date_label.grid(row=0, column=0, padx=5, pady=5)

start_date_entry = ttk.Entry(button_frame)
start_date_entry.grid(row=0, column=1, padx=5, pady=5)

end_date_label = ttk.Label(button_frame, text="End Date:")
end_date_label.grid(row=1, column=0, padx=5, pady=5)

end_date_entry = ttk.Entry(button_frame)
end_date_entry.grid(row=1, column=1, padx=5, pady=5)

add_resident_button = ttk.Button(button_frame, text="Add Resident", command=add_resident)
add_resident_button.grid(row=2, column=0, columnspan=2, pady=5)

# Start the main event loop
window.mainloop()

# Close the database connection
conn.close()
