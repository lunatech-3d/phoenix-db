import sqlite3
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

#Local Imports
from app.config import DB_PATH, PATHS
from app.showmayors import mayor_list_form 
from app.date_utils import parse_date_input, format_date_for_display, add_date_format_menu

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

current_sort_column = "First Name"
sort_order = {
    "First Name": True,
    "Middle Name": True,
    "Nickname": True,
    "Last Name": True,
    "Married Name": True,
    "Title": True,
    "Birth Date": True,
    "Death Date": True,
}

# Initialize sort_by and order globally
sort_by = "Last Name"
order = "ASC"

def add_mayor():
    item = tree.selection()
    if item:
        mayor_id = tree.item(item)["tags"][0]
        term_start = entry_term_start.get().strip()
        term_end = entry_term_end.get().strip()
        election_link = entry_election_link.get().strip()

        try:
            start_date, start_precision = parse_date_input(term_start)
            end_date, end_precision = parse_date_input(term_end) if term_end else ("", "")
        except ValueError as e:
            messagebox.showwarning("Error", str(e))
            return

        query = '''INSERT INTO Mayor (mayor_id, mayor_term_start, mayor_term_start_precision, 
                                      mayor_term_end, mayor_term_end_precision, mayor_election_link) 
                   VALUES (?, ?, ?, ?, ?, ?)'''
        
        try:
            cursor.execute(query, (mayor_id, start_date, start_precision, end_date, end_precision, election_link))
            connection.commit()
            messagebox.showinfo(title="Success", message="New mayor added successfully")
            window.destroy()
            mayor_list_form()  # Refresh the data
            
        except sqlite3.Error as e:
            messagebox.showerror(title="Error", message=f"Failed to add mayor: {e}")
    else:
        messagebox.showwarning("Tap, Tap, Tap", "Umm, Please select a person from the tree first")        

def load_people(sort_by="Last Name", order="ASC"):
    tree.delete(*tree.get_children())
    query = f'''SELECT 
        id, 
        first_name AS "First Name", 
        middle_name AS "Middle Name", 
        nick_name AS "Nickname",
        last_name AS "Last Name", 
        married_name AS "Married Name", 
        title AS "Title", 
        birth_date AS "Birth Date", 
        death_date AS "Death Date" 
    FROM People
    ORDER BY "{sort_by}" {order}
    '''

    cursor.execute(query)
    records = cursor.fetchall()
    
    for record in records:
        id, *fields = record
        tree.insert("", tk.END, values=fields, tags=(id,))

def on_column_header_double_click(column):
    global current_sort_column, sort_order, sort_by, order

    ascending = column == current_sort_column and sort_order[column]
    sort_order[column] = not ascending

    order = "ASC" if sort_order[column] else "DESC"

    load_people(sort_by=column, order=order)

    current_sort_column = column

def search_people(event=None):  
    global sort_by, order
    search_term = entry_search.get().strip()
    query = f"""SELECT 
        id, 
        first_name AS "First Name", 
        middle_name AS "Middle Name", 
        nick_name AS "Nickname",
        last_name AS "Last Name", 
        married_name AS "Married Name", 
        title AS "Title", 
        birth_date AS "Birth Date", 
        death_date AS "Death Date" 
    FROM People
    WHERE "First Name" LIKE '%{search_term}%' OR 
          "Middle Name" LIKE '%{search_term}%' OR
          "Nickname" LIKE '%{search_term}%' OR
          "Last Name" LIKE '%{search_term}%' OR
          "Married Name" LIKE '%{search_term}%' OR
          "Title" LIKE '%{search_term}%'
    ORDER BY "{sort_by}" {order}
    """

    cursor.execute(query)
    records = cursor.fetchall()
    tree.delete(*tree.get_children())
    for record in records:
        id, *fields = record
        tree.insert("", tk.END, values=fields, tags=(id,))

window = tk.Tk()
window.title("Add Mayor")

window_width = 1000
window_height = 800
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

frame = ttk.Frame(window)
frame.pack(padx=10, pady=10)

label_search = ttk.Label(frame, text="Search People:")
label_search.pack()
entry_search = ttk.Entry(frame)
entry_search.pack()
entry_search.bind('<Return>', search_people)  

search_button = ttk.Button(frame, text="Search", command=search_people)
search_button.pack()

tree = ttk.Treeview(frame, columns=("First Name", "Middle Name", "Nickname", "Last Name", "Married Name", "Title", "Birth Date", "Death Date"), show="headings")

tree.column("First Name", width=100)  
tree.column("Middle Name", width=100)  
tree.column("Nickname", width=75)  
tree.column("Last Name", width=100)  
tree.column("Married Name", width=120)  
tree.column("Title", width=50)  
tree.column("Birth Date", width=75) 
tree.column("Death Date", width=75)

tree.heading("First Name", text="First Name", command=lambda: on_column_header_double_click("First Name"))
tree.heading("Middle Name", text="Middle Name", command=lambda: on_column_header_double_click("Middle Name"))
tree.heading("Nickname", text="Nickname", command=lambda: on_column_header_double_click("Nickname"))
tree.heading("Last Name", text="Last Name", command=lambda: on_column_header_double_click("Last Name"))
tree.heading("Married Name", text="Married Name", command=lambda: on_column_header_double_click("Married Name"))
tree.heading("Title", text="Title", command=lambda: on_column_header_double_click("Title"))
tree.heading("Birth Date", text="Birth Date", command=lambda: on_column_header_double_click("Birth Date"))
tree.heading("Death Date", text="Death Date", command=lambda: on_column_header_double_click("Death Date"))
tree.pack()

label_term_start = ttk.Label(frame, text="Term Start:")
label_term_start.pack()
entry_term_start = ttk.Entry(frame)
entry_term_start.pack()
add_date_format_menu(entry_term_start)

label_term_end = ttk.Label(frame, text="Term End:")
label_term_end.pack()
entry_term_end = ttk.Entry(frame)
entry_term_end.pack()
add_date_format_menu(entry_term_end)

label_election_link = ttk.Label(frame, text="Election Link:")
label_election_link.pack()
entry_election_link = ttk.Entry(frame)
entry_election_link.pack()

button_add = ttk.Button(frame, text="Add Mayor", command=add_mayor)
button_add.pack()

load_people()

window.mainloop()

connection.close()