import sqlite3
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

# Connect to the database
connection = sqlite3.connect('phoenix.db')
cursor = connection.cursor()

# Define initial sort column and order
current_sort_column = ""
sort_order = {}

def search_by_last_name():
    last_name = entry_last_name.get().strip()
    married_name = entry_last_name.get().strip()
    query = f"SELECT Census.census_year, Census.census_housenumber, People.first_name, People.middle_name, People.last_name, People.married_name, Census.person_occupation, Census.person_age, Census.real_estate_value, Census.estate_value FROM People INNER JOIN Census ON People.id = Census.person_id WHERE People.last_name LIKE '{last_name}%' Or People.married_name LIKE '{married_name}%' ORDER BY Census.census_year, Census.census_housenumber"
    # Execute the query
    cursor.execute(query)
    records = cursor.fetchall()

    # Clear the treeview
    tree.delete(*tree.get_children())

    # Insert the records into the treeview
    for record in records:
        tree.insert("", tk.END, values=record)


# Define a dictionary to keep track of sort order for each column
sort_order = {
    # "ID": True,
    "Year": True,
    "Household": True,
    "First Name": True,
    "Middle Name": True,
    "Last Name": True,
    "Married Name": True,
    "Occupation": True,
    "Age": True,
    "Real Estate Value": True,
    "Estate Value": True
}

# Function to handle double-click event on column header
def on_column_header_double_click(column):
    global current_sort_column
    global sort_order

    # Check if the column is already sorted in ascending order
    if column == current_sort_column and sort_order[column] == "ASC":
        ascending = False
    else:
        ascending = True

    # Store the current sort column and order
    current_sort_column = column
    sort_order[column] = "ASC" if ascending else "DESC"

    # Clear the treeview
    tree.delete(*tree.get_children())

    # Map the column name to the corresponding field name
    field_mapping = {
        # "ID": "id",
        "Year": "census_year",
        "Household": "census_housenumber",
        "First Name": "first_name",
        "Middle Name": "middle_name",
        "Last Name": "last_name",
        "Married Name": "married_name",
        "Occupation": "person_occupation",
        "Age": "person_age",
        "Real Estate Value": "real_estate_value",
        "Estate Value": "estate_value"
    }

    # Retrieve the records from the database and apply sorting
    query = f"SELECT Census.census_year AS Year, Census.census_housenumber AS [Household], " \
    f"People.first_name AS [First Name], People.middle_name AS [Middle Name], " \
    f"People.last_name AS [Last Name], People.married_name AS [Married Name], " \
    f"Census.person_occupation AS Occupation, Census.person_age AS Age, " \
    f"Census.real_estate_value AS [Real Estate Value], Census.estate_value AS [Estate Value] " \
    f"FROM People INNER JOIN Census ON People.id = Census.person_id " \
    f"ORDER BY [{column}] {'ASC' if ascending else 'DESC'}"

    cursor.execute(query)
    records = cursor.fetchall()

    # Insert the sorted records into the treeview
    for record in records:
        tree.insert("", tk.END, values=record)


def delete_census_rec():
    selected_item = tree.selection()
    if len(selected_item) == 0:
        messagebox.showinfo("No Selection", "Please select a record to delete.")
    else:
        item = tree.item(selected_item[0])
        record = item['values']
        year, housenumber, first_name, middle_name, last_name, married_name, occupation, age, real_estate_value, estate_value = record
        # Get the record id from the database based on the other details of the record
        cursor.execute(
            f"SELECT Census.id FROM People INNER JOIN Census ON People.id = Census.person_id "
            f"WHERE Census.census_year = ? AND Census.census_housenumber = ? AND People.first_name = ? AND People.middle_name = ? "
            f"AND People.last_name = ? AND People.married_name = ? AND Census.person_occupation = ? AND Census.person_age = ? "
            f"AND Census.real_estate_value = ? AND Census.estate_value = ?",
            (year, housenumber, first_name, middle_name, last_name, married_name, occupation, age, real_estate_value, estate_value)
        )
        record_id = cursor.fetchone()[0]
        confirm = messagebox.askyesno("Confirmation", f"Do you want to delete the selected record (ID={record_id})?")
        if confirm:
            cursor.execute(f"DELETE FROM Census WHERE id = {record_id}")
            connection.commit()
            tree.delete(selected_item)
            messagebox.showinfo("Success", "Record deleted successfully.")



# Create the GUI window
window = tk.Tk()
window.title("Census Records")

# Set the window size and position
window_width = 1200
window_height = 800
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Create a frame for the search section
frame_search = ttk.Frame(window)
frame_search.pack(padx=10, pady=10)

# Last Name label
label_last_name = ttk.Label(frame_search, text="Last Name:")
label_last_name.grid(row=0, column=0, padx=5, pady=5)

# Last Name entry
entry_last_name = ttk.Entry(frame_search)
entry_last_name.grid(row=0, column=1, padx=5, pady=5)

# Search button
button_search = ttk.Button(frame_search, text="Search", command=search_by_last_name)
button_search.grid(row=0, column=2, padx=5, pady=5)

# Create a frame for the main content (Treeview)
frame_main = ttk.Frame(window)
frame_main.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)


# Create a frame for the treeview
frame_tree = ttk.Frame(frame_main)
frame_tree.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a horizontal scrollbar
x_scrollbar = ttk.Scrollbar(frame_tree, orient=tk.HORIZONTAL)

# Create a vertical scrollbar
y_scrollbar = ttk.Scrollbar(frame_tree)

# Create a treeview to display the records
tree = ttk.Treeview(frame_tree, xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
tree["columns"] = ("Year", "Household", "First Name", "Middle Name", "Last Name", "Married Name",
    "Occupation", "Age", "Real Estate Value", "Estate Value"
)

tree.heading("#0", text="", anchor="w")
tree.column("#0", width=1, anchor="w")
# tree.heading("ID", text="ID", anchor="w", command=lambda: on_column_header_double_click("ID"))
# tree.column("ID", width=25, anchor="w")
tree.heading("Year", text="Year", anchor="w", command=lambda: on_column_header_double_click("Year"))
tree.column("Year", width=25, anchor="w")
tree.heading("Household", text="House", anchor="w", command=lambda: on_column_header_double_click("Household"))
tree.column("Household", width=50, anchor="w")
tree.heading("First Name", text="First Name", anchor="w", command=lambda: on_column_header_double_click("First Name"))
tree.column("First Name", width=100, anchor="w")
tree.heading("Middle Name", text="Middle", anchor="w", command=lambda: on_column_header_double_click("Middle Name"))
tree.column("Middle Name", width=75, anchor="w")
tree.heading("Last Name", text="Last Name", anchor="w", command=lambda: on_column_header_double_click("Last Name"))
tree.column("Last Name", width=100, anchor="w")
tree.heading("Married Name", text="Married Name", anchor="w", command=lambda: on_column_header_double_click("Married Name"))
tree.column("Married Name", width=100, anchor="w")
tree.heading("Occupation", text="Occupation", anchor="w", command=lambda: on_column_header_double_click("Occupation"))
tree.column("Occupation", width=100, anchor="w")
tree.heading("Age", text="Age", anchor="w", command=lambda: on_column_header_double_click("Age"))
tree.column("Age", width=50, anchor="w")
tree.heading("Real Estate Value", text="Real Estate Value", anchor="w", command=lambda: on_column_header_double_click("Real Estate Value"))
tree.column("Real Estate Value", width=100, anchor="w")
tree.heading("Estate Value", text="Estate Value", anchor="w", command=lambda: on_column_header_double_click("Estate Value"))
tree.column("Estate Value", width=100, anchor="w")


# Retrieve all records from the People table
#cursor.execute("SELECT Census.id, Census.census_year, Census.census_housenumber, People.first_name, People.middle_name, People.last_name, People.married_name, Census.person_occupation, Census.person_age, Census.real_estate_value, Census.estate_value FROM People INNER JOIN Census ON People.id = Census.person_id ORDER BY Census.census_year, Census.census_housenumber")
cursor.execute("SELECT Census.census_year, Census.census_housenumber, People.first_name, People.middle_name, People.last_name, People.married_name, Census.person_occupation, Census.person_age, Census.real_estate_value, Census.estate_value FROM People INNER JOIN Census ON People.id = Census.person_id ORDER BY Census.census_year, Census.census_housenumber")
#cursor.execute("SELECT Census.census_year AS Year, Census.census_housenumber AS [Household], People.first_name AS [First Name], People.middle_name AS [Middle Name], People.last_name AS [Last Name], People.married_name AS [Married Name], Census.person_occupation AS Occupation, Census.person_age AS Age, Census.real_estate_value AS [Real Estate Value], Census.estate_value AS [Estate Value] FROM People INNER JOIN Census ON People.id = Census.person_id ORDER BY Census.census_year, Census.census_housenumber")
records = cursor.fetchall()


# Insert the records into the treeview
for record in records:
    tree.insert("", tk.END, values=record)

# Configure the scrollbars
x_scrollbar.configure(command=tree.xview)
y_scrollbar.configure(command=tree.yview)

# Grid the treeview and scrollbars
tree.grid(row=0, column=0, sticky="nsew")
x_scrollbar.grid(row=1, column=0, sticky="ew")
y_scrollbar.grid(row=0, column=1, sticky="ns")

# Configure grid weights
frame_tree.grid_rowconfigure(0, weight=1)
frame_tree.grid_columnconfigure(0, weight=1)

# Create a frame for the Edit and Delete buttons
frame_buttons = ttk.Frame(frame_main)
frame_buttons.pack(side=tk.RIGHT, pady=10, padx=(0, 10))

# Edit button...
button_edit = ttk.Button(frame_buttons, text="Edit")
button_edit.pack(pady=5)

# Delete button...
button_delete = ttk.Button(frame_buttons, text="Delete", command=delete_census_rec)
button_delete.pack(pady=5)

# Configure grid weights...
frame_main.columnconfigure(0, weight=9)  # 90% width for the Treeview
frame_main.columnconfigure(1, weight=1)  # 10% width for the buttons

# Run the GUI window
window.mainloop()

# Close the connection
connection.close()
