import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime
import sys
from .config import DB_PATH, PATHS  
import sqlite3


connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

current_sort_column = "Last Name"
sort_order = {
    "First Name": True,
    "Middle Name": True,
    "Last Name": True,
    "Married Name": True,
    "Birth Date": True,
    "Death Date": True,
}

# Initialize sort_by and order globally
sort_by = "Record ID"
order = "ASC"


def validate_and_transform_date(date_str):
    try:
        # Validate the date and transform it to the correct format
        dt = datetime.strptime(date_str, '%m-%d-%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        # The date is not in the correct format
        return None


def load_people(sort_by="Last Name", order="ASC", tree_view=None):
    if tree_view is None:
        return

    tree_view.delete(*tree_view.get_children())
    query = f'''SELECT 
        id AS "Rec ID", 
        first_name AS "First Name", 
        middle_name AS "Middle Name", 
        last_name as "Last Name",
        married_name as "Married Name",
        birth_date AS "Birth Date", 
        death_date AS "Death Date" 
    FROM People
    ORDER BY "{sort_by}" {order}
    '''

    cursor.execute(query)
    records = cursor.fetchall()
    
    for record in records:
        record_id, first_name, middle_name, last_name, married_name, birth_date, death_date = record
        # Replace "None" values with empty strings
        values = (record_id, first_name, middle_name, last_name if last_name is not None else "", married_name if married_name is not None else "", birth_date, death_date)
        tree_view.insert("", tk.END, values=values, tags=(record_id,))
        
    tree_view.update_idletasks()



def on_column_header_double_click(column):
    global current_sort_column
    global sort_order
    global sort_by
    global order

    ascending = column == current_sort_column and sort_order[column]
    sort_order[column] = not ascending

    order = "ASC" if sort_order[column] else "DESC"

    load_people(sort_by=column, order=order)

    current_sort_column = column

def clear_form():
    
    # Clear selected items in seller and buyer trees
    seller_tree.selection_remove(seller_tree.selection())
    buyer_tree.selection_remove(buyer_tree.selection())

    seller_entry.delete(0, tk.END)
    buyer_entry.delete(0, tk.END)
    entry_amount.delete(0, tk.END)
    entry_type.delete(0, tk.END)
    entry_recorded.delete(0, tk.END)
    entry_dated.delete(0, tk.END)
    entry_acknowledged.delete(0, tk.END)
    entry_transaction_date.delete(0, tk.END)
    entry_property_address.delete(0, tk.END)
    entry_property_city.delete(0, tk.END)
    entry_property_state.delete(0, tk.END)
    entry_property_zip.delete(0, tk.END)
    entry_property_county.delete(0, tk.END)
    text_property_desc.delete(1.0, tk.END)

    # Clear any selections in treeviews
    seller_tree.selection_remove(seller_tree.selection())
    buyer_tree.selection_remove(buyer_tree.selection())

def visualize_property():
    # To Be Continued
    seller_item = seller_tree.selection()

def add_trans():
    
    seller_item = seller_tree.selection()
    buyer_item = buyer_tree.selection()

    if not seller_item:
        messagebox.showwarning("Error", "Please select a seller")
        return
    if not buyer_item:
        messagebox.showwarning("Error", "Please select a buyer")
        return
        
    seller_id = seller_tree.item(seller_item)["tags"][0]
    buyer_id = buyer_tree.item(buyer_item)["tags"][0]
    deed_amount = entry_amount.get()
    deed_type = entry_type.get()
    deed_recorded = validate_and_transform_date(entry_recorded.get().strip())
    deed_dated = validate_and_transform_date(entry_dated.get().strip())
    deed_acknowledged = validate_and_transform_date(entry_acknowledged.get().strip())
    transaction_date = validate_and_transform_date(entry_transaction_date.get().strip())
    property_address = entry_property_address.get()
    property_city = entry_property_city.get()
    property_state = entry_property_state.get()
    property_zip = entry_property_zip.get()
    property_county = entry_property_county.get()
    property_description = text_property_desc.get("1.0", tk.END).strip()

    if deed_recorded is None or deed_dated is None or deed_acknowledged is None or transaction_date is None:
        messagebox.showwarning("Error", "Please make sure all dates are in MM-DD-YYYY format")
        return

    if not deed_amount:
        messagebox.showwarning("Error", "Please enter the amount for the transaction")
        return
    if not property_description:
        messagebox.showwarning("Error", "Please enter the description details of the transaction")
        return

    query = f'''INSERT INTO LandTransactions (seller_id, buyer_id, deed_amount, deed_type, deed_recorded, deed_dated, deed_acknowledged, transaction_date,
        property_description, property_address, property_city, property_state, property_zip, property_county) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

    print("query:", query)                
    try:
        cursor.execute(query, (seller_id, buyer_id, deed_amount, deed_type, deed_recorded, deed_dated, deed_acknowledged, transaction_date, property_description, property_address, property_city, property_state, property_zip, property_county))
        connection.commit()
        clear_form()
        messagebox.showinfo(title="Success", message="New Transaction Added Successfully")
    except sqlite3.Error as e:
        messagebox.showerror(title="Error", message=f"Failed to add transaction: {e}")
    finally:
        pass
        
def search_people(entry_field, tree_view):  
    global sort_by
    global order
    search_term = entry_field.get().strip()
    query = f"""SELECT 
        id, 
        first_name AS "First Name", 
        middle_name AS "Middle Name", 
        last_name AS "Last Name", 
        married_name AS "Married Name", 
        birth_date AS "Birth Date", 
        death_date AS "Death Date" 
    FROM People
    WHERE "First Name" LIKE '%{search_term}%' OR 
          "Middle Name" LIKE '%{search_term}%' OR
          "Last Name" LIKE '%{search_term}%' OR
          "Married Name" LIKE '%{search_term}%'
    ORDER BY "{sort_by}" {order}
    """

    cursor.execute(query)
    records = cursor.fetchall()
    tree_view.delete(*tree_view.get_children())
    for record in records:
        record_id, *fields = record
        # Replace "None" values with empty strings
        record_values = [record_id] + [field if field is not None else "" for field in fields]
        tree_view.insert("", tk.END, values=record_values, tags=(record_id,))


# Create a root window
window = tk.Tk()
window.title("Add Transaction")

window_width = 1200
window_height = 800
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Create frames for Seller and Buyer sections
seller_frame = ttk.Frame(window)
seller_frame.grid(row=0, column=0, padx=10, pady=10)

buyer_frame = ttk.Frame(window)
buyer_frame.grid(row=0, column=1, padx=10, pady=10)

# Create the entry fields for the Seller
seller_label = ttk.Label(seller_frame, text="Search Seller:")
seller_label.grid(row=0, column=0, padx=5, pady=5)
seller_entry = ttk.Entry(seller_frame)
seller_entry.grid(row=0, column=1, padx=5, pady=5)
seller_search_button = ttk.Button(seller_frame, text="Search", command=lambda: search_people(seller_entry, seller_tree))
seller_search_button.grid(row=0, column=2, padx=5, pady=5)

# Create the Treeview for the Seller
seller_tree = ttk.Treeview(seller_frame, columns=('id', 'First Name', 'Middle Name', 'Last Name', 'Married Name', 'Birth Date', 'Death Date'), show='headings')
seller_tree.heading('id', text='id')
seller_tree.heading('First Name', text='First Name', command=lambda: on_column_header_double_click("First Name"))
seller_tree.heading('Middle Name', text='Middle Name', command=lambda: on_column_header_double_click("Middle Name"))
seller_tree.heading('Last Name', text='Last Name', command=lambda: on_column_header_double_click("Last Name"))
seller_tree.heading('Married Name', text='Married Name', command=lambda: on_column_header_double_click("Married Name"))
seller_tree.heading('Birth Date', text='Birth Date', command=lambda: on_column_header_double_click("Birth Date"))
seller_tree.heading('Death Date', text='Death Date', command=lambda: on_column_header_double_click("Death Date"))

# Set the Seller column widths
seller_tree.column('id', width=50)
seller_tree.column('First Name', width=100)
seller_tree.column('Middle Name', width=60)
seller_tree.column('Last Name', width=100)
seller_tree.column('Married Name', width=100)
seller_tree.column('Birth Date', width=75)
seller_tree.column('Death Date', width=75)

vsb_seller = ttk.Scrollbar(seller_frame, orient="vertical", command=seller_tree.yview)
vsb_seller.grid(row=1, column=3, sticky='ns')
seller_tree.configure(yscrollcommand=vsb_seller.set)

seller_tree.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')


# Buyer Widgets
buyer_label = ttk.Label(buyer_frame, text="Search Buyer:")
buyer_label.grid(row=2, column=0, padx=5, pady=5)
buyer_entry = ttk.Entry(buyer_frame)
buyer_entry.grid(row=2, column=1, padx=5, pady=5)
buyer_search_button = ttk.Button(buyer_frame, text="Search", command=lambda: search_people(buyer_entry, buyer_tree))
buyer_search_button.grid(row=2, column=2, padx=5, pady=5)

# Create the Treeview for the Buyer
buyer_tree = ttk.Treeview(buyer_frame, columns=('id', 'First Name', 'Middle Name', 'Last Name', 'Married Name', 'Birth Date', 'Death Date'), show='headings')
buyer_tree.heading('id', text='id')
buyer_tree.heading('First Name', text='First Name',command=lambda: on_column_header_double_click("First Name"))
buyer_tree.heading('Middle Name', text='Middle Name', command=lambda: on_column_header_double_click("Middle Name"))
buyer_tree.heading('Last Name', text='Last Name', command=lambda: on_column_header_double_click("Last Name"))
buyer_tree.heading('Married Name', text='Married Name', command=lambda: on_column_header_double_click("Married Name"))
buyer_tree.heading('Birth Date', text='Birth Date', command=lambda: on_column_header_double_click("Birth Date"))
buyer_tree.heading('Death Date', text='Death Date', command=lambda: on_column_header_double_click("Death Date"))

# Set the Buyer tree column widths
buyer_tree.column('id', width=50)
buyer_tree.column('First Name', width=100)
buyer_tree.column('Middle Name', width=60)
buyer_tree.column('Last Name', width=100)
buyer_tree.column('Married Name', width=100)
buyer_tree.column('Birth Date', width=75)
buyer_tree.column('Death Date', width=75)

vsb_buyer = ttk.Scrollbar(buyer_frame, orient="vertical", command=buyer_tree.yview)
vsb_buyer.grid(row=3, column=3, sticky='ns')
buyer_tree.configure(yscrollcommand=vsb_buyer.set)

buyer_tree.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')


# Create a subframe for entry fields
entry_fields_frame = ttk.Frame(window)
entry_fields_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

# Entry fields for deed information
label_amount = ttk.Label(entry_fields_frame, text="Deed Amount:")
entry_amount = ttk.Entry(entry_fields_frame)
label_type = ttk.Label(entry_fields_frame, text="Deed Type:")
entry_type = ttk.Entry(entry_fields_frame)
label_recorded = ttk.Label(entry_fields_frame, text="Deed Recorded:")
entry_recorded = ttk.Entry(entry_fields_frame)
label_dated = ttk.Label(entry_fields_frame, text="Deed Dated:")
entry_dated = ttk.Entry(entry_fields_frame)
label_acknowledged = ttk.Label(entry_fields_frame, text="Deed Acknowledged:")
entry_acknowledged = ttk.Entry(entry_fields_frame)
label_transaction_date = ttk.Label(entry_fields_frame, text="Transaction Date:")
entry_transaction_date = ttk.Entry(entry_fields_frame)

# Place entry fields in a grid layout
label_amount.grid(row=0, column=0, padx=5, pady=5)
entry_amount.grid(row=0, column=1, padx=5, pady=5)
label_type.grid(row=0, column=2, padx=5, pady=5)
entry_type.grid(row=0, column=3, padx=5, pady=5)
label_recorded.grid(row=1, column=0, padx=5, pady=5)
entry_recorded.grid(row=1, column=1, padx=5, pady=5)
label_dated.grid(row=1, column=2, padx=5, pady=5)
entry_dated.grid(row=1, column=3, padx=5, pady=5)
label_acknowledged.grid(row=2, column=0, padx=5, pady=5)
entry_acknowledged.grid(row=2, column=1, padx=5, pady=5)
label_transaction_date.grid(row=2, column=2, padx=5, pady=5)
entry_transaction_date.grid(row=2, column=3, padx=5, pady=5)

# Entry fields for property information
label_property_address = ttk.Label(entry_fields_frame, text="Property Address:")
entry_property_address = ttk.Entry(entry_fields_frame)
label_property_city = ttk.Label(entry_fields_frame, text="Property City:")
entry_property_city = ttk.Entry(entry_fields_frame)
label_property_state = ttk.Label(entry_fields_frame, text="Property State:")
entry_property_state = ttk.Entry(entry_fields_frame)
label_property_zip = ttk.Label(entry_fields_frame, text="Property Zip:")
entry_property_zip = ttk.Entry(entry_fields_frame)
label_property_county = ttk.Label(entry_fields_frame, text="Property County:")
entry_property_county = ttk.Entry(entry_fields_frame)

# Place entry fields in a grid layout
label_property_address.grid(row=3, column=0, padx=5, pady=5)
entry_property_address.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky='ew')
label_property_city.grid(row=4, column=0, padx=5, pady=5)
entry_property_city.grid(row=4, column=1, padx=5, pady=5)
label_property_state.grid(row=4, column=2, padx=5, pady=5)
entry_property_state.grid(row=4, column=3, padx=5, pady=5)
label_property_zip.grid(row=5, column=0, padx=5, pady=5)
entry_property_zip.grid(row=5, column=1, padx=5, pady=5)
label_property_county.grid(row=5, column=2, padx=5, pady=5)
entry_property_county.grid(row=5, column=3, padx=5, pady=5)

# Create a subframe for property description
property_desc_frame = ttk.Frame(entry_fields_frame)
property_desc_frame.grid(row=6, column=0, columnspan=4, padx=5, pady=5, sticky='ew')
label_property_desc = ttk.Label(property_desc_frame, text="Property Description:")
label_property_desc.pack(side=tk.TOP, padx=5, pady=5)
text_property_desc = tk.Text(property_desc_frame, height=5, wrap=tk.WORD)
text_property_desc.pack(side=tk.TOP, padx=5, pady=5, fill=tk.BOTH, expand=True)

# Add Transaction button
button_frame = ttk.Frame(window)
button_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

visualize_button = ttk.Button(button_frame, text="Visualize Property", command=visualize_property)
visualize_button.pack()
button_add = ttk.Button(button_frame, text="Add Transaction", command=add_trans)
button_add.pack()

load_people(sort_by="id", order="ASC", tree_view=seller_tree)
load_people(sort_by="id", order="ASC", tree_view=buyer_tree)

def on_closing():
    connection.close()
    window.destroy()

# Attach the closing handler to the window's close button
window.protocol("WM_DELETE_WINDOW", on_closing)

# Start the GUI event loop
window.mainloop()