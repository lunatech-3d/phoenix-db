import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox

# Database connection
conn = sqlite3.connect('phoenix.db')  # Replace with the actual path to your database
cursor = conn.cursor()

def add_document_type():
    document_type_name = doc_type_entry.get().strip()

    # Data checks
    if not document_type_name:
        messagebox.showerror("Error", "Please enter a document type name.")
        return

    # Check if the document type already exists
    cursor.execute("SELECT doc_type_name FROM DocType WHERE doc_type_name = ?", (document_type_name,))
    existing_document_type = cursor.fetchone()
    if existing_document_type:
        messagebox.showerror("Error", "The document type already exists.")
        return

    # Add the document type to the database
    cursor.execute("INSERT INTO DocType (doc_type_name) VALUES (?)", (document_type_name,))
    conn.commit()

    # Clear the form input
    doc_type_entry.delete(0, tk.END)

    # Update the document type list
    update_document_type_list()

    messagebox.showinfo("Success", "Document type added successfully.")

def edit_document_type():
    selected_item = doc_type_listbox.curselection()
    if not selected_item:
        messagebox.showerror("Error", "Please select a document type to edit.")
        return

    document_type_name = doc_type_entry.get().strip()

    # Data checks
    if not document_type_name:
        messagebox.showerror("Error", "Please enter a document type name.")
        return

    # Get the current document type name
    current_document_type = doc_type_listbox.get(selected_item)

    # Check if the document type already exists
    if document_type_name != current_document_type:
        cursor.execute("SELECT doc_type_name FROM DocType WHERE doc_type_name = ?", (document_type_name,))
        existing_document_type = cursor.fetchone()
        if existing_document_type:
            messagebox.showerror("Error", "The document type already exists.")
            return

    # Update the document type in the database
    cursor.execute("UPDATE DocType SET doc_type_name = ? WHERE doc_type_name = ?", (document_type_name, current_document_type))
    conn.commit()

    # Clear the form input
    doc_type_entry.delete(0, tk.END)

    # Update the document type list
    update_document_type_list()

    messagebox.showinfo("Success", "Document type updated successfully.")

def delete_document_type():
    selected_item = doc_type_listbox.curselection()
    if not selected_item:
        messagebox.showerror("Error", "Please select a document type to delete.")
        return

    document_type_name = doc_type_listbox.get(selected_item)

    # Check if the document type is in use by any documents
    cursor.execute("SELECT doc_type_id FROM Doc WHERE doc_type_id IN (SELECT doc_type_id FROM DocType WHERE doc_type_name = ?)", (document_type_name,))
    document_type_in_use = cursor.fetchone()
    if document_type_in_use:
        messagebox.showerror("Error", "Cannot delete the document type as it is in use by some documents.")
        return

    # Delete the document type from the database
    cursor.execute("DELETE FROM DocType WHERE doc_type_name = ?", (document_type_name,))
    conn.commit()

    # Update the document type list
    update_document_type_list()

    messagebox.showinfo("Success", "Document type deleted successfully.")

def update_document_type_list():
    doc_type_listbox.delete(0, tk.END)
    cursor.execute("SELECT doc_type_name FROM DocType ORDER BY doc_type_name")
    document_types = cursor.fetchall()
    for document_type in document_types:
        doc_type_listbox.insert(tk.END, document_type[0])

# Create the main application window
root = tk.Tk()
root.title("Document Type Management")

# Document Type Listbox
doc_type_listbox = tk.Listbox(root)
doc_type_listbox.grid(row=0, column=0, padx=10, pady=10)

# Document Type Entry
doc_type_entry = ttk.Entry(root)
doc_type_entry.grid(row=1, column=0, padx=10, pady=5)

# Add Button
add_button = ttk.Button(root, text="Add", command=add_document_type)
add_button.grid(row=2, column=0, padx=10, pady=5)

# Edit Button
edit_button = ttk.Button(root, text="Edit", command=edit_document_type)
edit_button.grid(row=3, column=0, padx=10, pady=5)

# Delete Button
delete_button = ttk.Button(root, text="Delete", command=delete_document_type)
delete_button.grid(row=4, column=0, padx=10, pady=5)

# Initialize the document type list
update_document_type_list()

root.mainloop()

# Close the database connection
conn.close()
