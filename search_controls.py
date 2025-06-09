import tkinter as tk
from tkinter import ttk, messagebox

class SearchControls:
    def __init__(self, parent_frame, tree_to_populate, cursor, population_function):
        """
        Initialize search controls
        parent_frame: Frame where controls will be placed
        tree_to_populate: The TreeView that will show results
        cursor: Database cursor
        population_function: Function to populate tree with results
        """
        self.frame_search = ttk.Frame(parent_frame)
        self.tree = tree_to_populate
        self.cursor = cursor
        self.populate_tree = population_function
        
        # Last Name entry
        label_first_name = ttk.Label(self.frame_search, text="First Name:")
        label_first_name.grid(row=0, column=0, padx=5, pady=5)
        self.entry_first_name = ttk.Entry(self.frame_search)
        self.entry_first_name.grid(row=0, column=1, padx=5, pady=5)

        # Last Name entry
        label_last_name = ttk.Label(self.frame_search, text="Last Name:")
        label_last_name.grid(row=1, column=0, padx=5, pady=5)
        self.entry_last_name = ttk.Entry(self.frame_search)
        self.entry_last_name.grid(row=1, column=1, padx=5, pady=5)

        # Search by Name button
        button_search_name = ttk.Button(self.frame_search, text="Search by Name", 
                                      command=self.search_by_name)
        button_search_name.grid(row=0, column=2, padx=5, pady=5)

        # Clear Fields button
        button_clear_fields = ttk.Button(self.frame_search, text="Reset", 
                                       command=self.clear_search_fields)
        button_clear_fields.grid(row=1, column=2, padx=5, pady=5)

        # Record Number entry (optional, can be hidden for family_linkage)
        self.label_record_number = ttk.Label(self.frame_search, text="Record Number:")
        self.entry_record_number = ttk.Entry(self.frame_search)
        self.button_search_record_number = ttk.Button(
            self.frame_search, 
            text="Search by Record Number",
            command=self.search_by_record_number
        )

    def show_record_number_search(self, show=True):
        """Show or hide record number search controls"""
        if show:
            self.label_record_number.grid(row=3, column=0, padx=5, pady=5)
            self.entry_record_number.grid(row=3, column=1, padx=5, pady=5)
            self.button_search_record_number.grid(row=3, column=2, padx=5, pady=5)
        else:
            self.label_record_number.grid_remove()
            self.entry_record_number.grid_remove()
            self.button_search_record_number.grid_remove()

    def search_by_name(self):
        """Search functionality"""
        last_name = self.entry_last_name.get().strip()
        first_name = self.entry_first_name.get().strip()

        query = """
            SELECT id, first_name, middle_name, last_name, married_name, birth_date, death_date 
            FROM People 
            WHERE 1=1
        """
        parameters = []

        if last_name:
            query += " AND (last_name LIKE ? OR married_name LIKE ?)"
            parameters.extend([f"{last_name}%", f"{last_name}%"])

        if first_name:
            query += " AND first_name LIKE ?"
            parameters.append(f"{first_name}%")

        if not parameters:
            messagebox.showinfo("No Input", "Please enter a first name, a last name, or both.")
            return

        self.display_records(query, parameters)

    def search_by_record_number(self):
        """Record number search functionality"""
        record_number = self.entry_record_number.get().strip()
        try:
            record_number = int(record_number)
            query = "SELECT * FROM People WHERE id = ?"
            self.display_records(query, [record_number])
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid record number.")

    def clear_search_fields(self):
        """Clear all search fields"""
        self.entry_last_name.delete(0, tk.END)
        self.entry_first_name.delete(0, tk.END)
        self.entry_record_number.delete(0, tk.END)

    def display_records(self, query, parameters=[]):
        """Display search results"""
        self.cursor.execute(query, parameters)
        records = self.cursor.fetchall()
        self.populate_tree(records)

    def pack(self, **kwargs):
        """Pack the search frame"""
        self.frame_search.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the search frame"""
        self.frame_search.grid(**kwargs)