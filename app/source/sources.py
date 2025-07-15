import tkinter as tk
from tkinter import ttk
import sqlite3
import sys
from tkinter import messagebox

#Local Imports
from app.config import DB_PATH, PATHS

window = None
tree = None

def refresh_sources():
    """ Fetch sources from the database and update the tree view """
    for i in tree.get_children():
        tree.delete(i)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, title, author, publisher, pub_date, note FROM Sources")
    for row in cur.fetchall():
        tree.insert("", "end", values=row)
    conn.close()

    
def add_source(parent, refresh_fn=None):
    """Open a new window attached to ``parent`` to add a source.

    Parameters
    ----------
    parent : tk.Widget
        The parent window.
    refresh_fn : callable, optional
        Function to call after saving the source. This allows other modules to
        refresh their UI when a new source is added.

    Returns
    -------
    int | None
        The ``id`` of the newly created source or ``None`` if the dialog was
        closed without saving.
    """

    new_id = None



    def save_new_source():
        nonlocal new_id
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Sources (title, author, publisher, pub_date, note) VALUES (?, ?, ?, ?, ?)",
            (
                title_entry.get(),
                author_entry.get(),
                publisher_entry.get(),
                pub_date_entry.get(),
                note_entry.get(),
            ),
        )
        new_id = cur.lastrowid        
        conn.commit()
        conn.close()
        add_window.destroy()
         
    add_window = tk.Toplevel(parent)
    add_window.title("Add New Source")
    add_window.geometry("800x220")
    
    # Entry fields
    tk.Label(add_window, text="Title:").grid(row=0, column=0, sticky="w", pady=4)
    title_entry = tk.Entry(add_window, width=100, justify="left")
    title_entry.grid(row=0, column=1, sticky="w")

    tk.Label(add_window, text="Author:").grid(row=1, column=0, sticky="w", pady=4)
    author_entry = tk.Entry(add_window, width=50, justify="left")
    author_entry.grid(row=1, column=1, sticky="w")

    tk.Label(add_window, text="Publisher:").grid(row=2, column=0, sticky="w", pady=4)
    publisher_entry = tk.Entry(add_window, width=50, justify="left")
    publisher_entry.grid(row=2, column=1, sticky="w")

    tk.Label(add_window, text="Publication Date:").grid(row=3, column=0, sticky="w", pady=4)
    pub_date_entry = tk.Entry(add_window, width=30, justify="left")
    pub_date_entry.grid(row=3, column=1, sticky="w")

    tk.Label(add_window, text="Note:").grid(row=4, column=0, sticky="w", pady=4)
    note_entry = tk.Entry(add_window, width=100, justify="left")
    note_entry.grid(row=4, column=1, sticky="w")
    
    tk.Button(add_window, text="Save", command=save_new_source).grid(row=5, column=1, pady=4)
    
    add_window.grab_set()
    parent.wait_window(add_window)

    if refresh_fn:
        refresh_fn()

    return new_id

def edit_source():
    """ Open a form to edit the selected source """
    selected_item = tree.selection()
    if selected_item:  # Check if something is selected
        source_id = tree.item(selected_item, "values")[0]
        # Fetch source details from the database
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT title, author, publisher, pub_date, note FROM Sources WHERE id = ?", (source_id,))
        source_data = cur.fetchone()
        conn.close()

        # Open a new window to edit source
        edit_window = tk.Toplevel(window)
        edit_window.title("Edit Source")
        
        # Entry fields pre-populated with source data
        tk.Label(edit_window, text="Title:").grid(row=0, column=0)
        title_entry = tk.Entry(edit_window)
        title_entry.grid(row=0, column=1)
        title_entry.insert(0, source_data[0])
        
        tk.Label(edit_window, text="Author:").grid(row=1, column=0)
        author_entry = tk.Entry(edit_window)
        author_entry.grid(row=1, column=1)
        author_entry.insert(0, source_data[1])
        
        tk.Label(edit_window, text="Publisher:").grid(row=2, column=0)
        publisher_entry = tk.Entry(edit_window)
        publisher_entry.grid(row=2, column=1)
        publisher_entry.insert(0, source_data[2])
        
        tk.Label(edit_window, text="Publication Date:").grid(row=3, column=0)
        pub_date_entry = tk.Entry(edit_window)
        pub_date_entry.grid(row=3, column=1)
        pub_date_entry.insert(0, source_data[3])
        
        tk.Label(edit_window, text="Note:").grid(row=4, column=0)
        note_entry = tk.Entry(edit_window)
        note_entry.grid(row=4, column=1)
        note_entry.insert(0, source_data[4])

        # Save button
        def save_edited_source():
            # Update source in the database
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("UPDATE Sources SET title = ?, author = ?, publisher = ?, pub_date = ?, note = ? WHERE id = ?",
                            (title_entry.get(), author_entry.get(), publisher_entry.get(), pub_date_entry.get(), note_entry.get(), source_id))
                conn.commit()
                conn.close()
                edit_window.destroy()
                refresh_sources()
                messagebox.showinfo("Success", "Source updated successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update source: {e}")

        tk.Button(edit_window, text="Save Changes", command=save_edited_source).grid(row=5, column=1)
    else:
        messagebox.showerror("Error", "No source selected. Please select a source to edit.")

    
def delete_source():
    """ Delete the selected source after confirmation """
    selected_item = tree.selection()
    if selected_item:  # Check if something is selected
        source_id = tree.item(selected_item, "values")[0]
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this source?"):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("DELETE FROM Sources WHERE id = ?", (source_id,))
                conn.commit()
                conn.close()
                refresh_sources()
                messagebox.showinfo("Success", "Source deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete source: {e}")
    else:
        messagebox.showerror("Error", "No source selected. Please select a source to delete.")

def launch_gui():
    """Launch the standalone Source Management interface."""
    global window, tree
    window = tk.Tk()
    window.title("Source Management")

    tree = ttk.Treeview(window,
                        columns=("ID", "Title", "Author", "Publisher", "Publication Date", "Note"),
                        show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(fill=tk.BOTH, expand=True)

    ttk.Button(window, text="Refresh Sources", command=refresh_sources).pack(side=tk.LEFT)
    ttk.Button(window, text="Add Source", command=lambda: add_source(window, refresh_sources)).pack(side=tk.LEFT)    
    ttk.Button(window, text="Edit Source", command=edit_source).pack(side=tk.LEFT)
    ttk.Button(window, text="Delete Source", command=delete_source).pack(side=tk.LEFT)

    refresh_sources()  # Initial load of source data

    window.mainloop()

if __name__ == "__main__":
    launch_gui()
