import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime
from tkinter import messagebox
import subprocess
from date_utils import format_date_for_display, parse_date_input


def mayor_list_form():
    global selected_mayor_id
    global current_sort_column
    global sort_order
    connection = sqlite3.connect('phoenix.db')
    cursor = connection.cursor()

    selected_mayor_id = None
    current_sort_column = "ID"
    sort_order = {
        "ID": True,
        "First Name": True,
        "Middle Name": True,
        "Last Name": True,
        "Married Name": True,
        "Mayor Term Start": True,
        "Mayor Term End": True,
    }

    def load_data(sort_by="Mayor Term Start", order="ASC"):
        global selected_mayor_id
        tree.delete(*tree.get_children())
        query = f"""
                SELECT 
                    Mayor.id AS [ID],
                    People.first_name AS [First Name], 
                    People.middle_name AS [Middle Name], 
                    People.last_name AS [Last Name],
                    People.married_name AS [Married Name], 
                    Mayor.mayor_term_start AS [Mayor Term Start],
                    Mayor.mayor_term_start_precision AS [Start Precision],
                    Mayor.mayor_term_end AS [Mayor Term End],
                    Mayor.mayor_term_end_precision AS [End Precision]
                FROM People 
                INNER JOIN Mayor ON People.id = Mayor.mayor_id
                ORDER BY [{sort_by}] {order}
                """
                
        cursor.execute(query)
        records = cursor.fetchall()

        for record in records:
            id, first_name, middle_name, last_name, married_name, mayor_term_start, start_precision, mayor_term_end, end_precision = record

            # Format dates for display
            mayor_term_start = format_date_for_display(mayor_term_start, start_precision)
            mayor_term_end = format_date_for_display(mayor_term_end, end_precision)
            
            tree.insert("", tk.END, values=(first_name, middle_name, last_name, married_name, mayor_term_start, mayor_term_end), tags=(id,))



    def delete_mayor():
        global selected_mayor_id
        
        if selected_mayor_id:
            confirm = messagebox.askyesno("Confirm", "Do you really want to delete this mayor?")
            if confirm:
                try:
                    cursor.execute(f"DELETE FROM Mayor WHERE id={selected_mayor_id}")
                    connection.commit()
                    messagebox.showinfo("Success", "Mayor deleted successfully")
                    selected_mayor_id = None  # reset selected mayor id
                    load_data()  # Refresh the data
                except sqlite3.Error as e:
                    messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Warning", "Please select a mayor to delete")

    
    # Function to handle double-click event on column header
    def on_column_header_double_click(column):
        global current_sort_column
        global sort_order

        # Check if the column is already sorted in ascending order
        ascending = column == current_sort_column and sort_order[column]
        sort_order[column] = not ascending

        order = "ASC" if sort_order[column] else "DESC"

        load_data(sort_by=column, order=order)  # Load data with updated sorting

        # Store the current sort column and order
        current_sort_column = column

    def add_mayor(window):
        window.destroy()  # Destroy the 'Show Mayors' window
        subprocess.run(["python", "addmayor.py"])
        mayor_list_form()  # Refresh the data

    def on_tree_select(event):
        global selected_mayor_id
        selected_items = tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            selected_mayor_id = tree.item(selected_item, "tags")[0]
        

    def open_mayor_edit_form():
        global selected_mayor_id
        
        if selected_mayor_id:
            subprocess.run(["python", "editmayor.py", str(selected_mayor_id)])  # convert selected_mayor_id to string


    # Start the layout of the GUI Interface
    window = tk.Tk()
    window.title("Plymouth Mayors")

    window_width = 1000
    window_height = 800
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    frame_main = ttk.Frame(window)
    frame_main.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    frame = ttk.Frame(frame_main)
    frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

    tree = ttk.Treeview(frame, columns=("First Name", "Middle Name", "Last Name", "Married Name", "Mayor Term Start", "Mayor Term End"), show="headings")

    tree.column("First Name", width=100)  # Adjust width to 100
    tree.column("Middle Name", width=100)  # Adjust width to 100
    tree.column("Last Name", width=100)  # Adjust width to 100
    tree.column("Married Name", width=120)  # Adjust width to 120
    tree.column("Mayor Term Start", width=150)  # Adjust width to 150
    tree.column("Mayor Term End", width=150)  # Adjust width to 150

    tree.heading("First Name", text="First Name", command=lambda: on_column_header_double_click("First Name"))
    tree.heading("Middle Name", text="Middle Name", command=lambda: on_column_header_double_click("Middle Name"))
    tree.heading("Last Name", text="Last Name", command=lambda: on_column_header_double_click("Last Name"))
    tree.heading("Married Name", text="Married Name", command=lambda: on_column_header_double_click("Married Name"))
    tree.heading("Mayor Term Start", text="Mayor Term Start", command=lambda: on_column_header_double_click("Mayor Term Start"))
    tree.heading("Mayor Term End", text="Mayor Term End", command=lambda: on_column_header_double_click("Mayor Term End"))

    # Bind the '<<TreeviewSelect>>' event to the treeview
    tree.bind("<<TreeviewSelect>>", on_tree_select)
    # Bind double-click event to the treeview
    tree.bind("<Double-1>", lambda e: open_mayor_edit_form())


    tree.pack(fill=tk.BOTH, expand=True)
    tree.tag_configure("heading", background="lightblue")

    frame_buttons = ttk.Frame(frame_main)
    frame_buttons.pack(side=tk.LEFT, fill=tk.Y)

    btn_add = ttk.Button(frame_buttons, text="Add Mayor", command=lambda: add_mayor(window))
    btn_add.pack(padx=10, pady=10)

    btn_delete = ttk.Button(frame_buttons, text="Delete Mayor", command=delete_mayor)
    btn_delete.pack(padx=10, pady=10)

    # Call the load_data function to load the data when the script is first run
    load_data()

    window.mainloop()

if __name__ == "__main__":
    mayor_list_form()
