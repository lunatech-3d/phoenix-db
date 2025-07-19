import tkinter as tk
import sys
from tkinter import ttk, messagebox
import sqlite3
import webbrowser

#Local Imports
from app.config import DB_PATH, PATHS
from app.date_utils import format_date_for_display
from app.editbiz import open_edit_business_form
from app.context_menu import apply_context_menu_to_all_entries

class BusinessManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Business Search")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

        self.sort_column = None
        self.sort_reverse = False

        self.setup_filters()
        self.setup_tree()
        self.setup_buttons()  # <-- Add/Edit/Delete
        self.load_businesses()
        # Ensure context menus on search fields and tree view
        apply_context_menu_to_all_entries(self.root)

    def setup_tree(self):
        # Define internal column keys
        columns = ("biz_id", "biz_name", "category", "start_date", "end_date", "external_url")

        # Create the Treeview
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")

        # Define user-friendly column labels
        column_headings = {
            "biz_id": "ID",
            "biz_name": "Name",
            "category": "Category",
            "start_date": "Start",
            "end_date": "End",
            "external_url": "URL"
        }

        # Apply headings and sorting
        for key in columns:
            self.tree.heading(key, text=column_headings[key], command=lambda c=key: self.sort_by_column(c))

        # Configure column widths and anchors
        self.tree.column("biz_id", width=0, stretch=False)  # Hidden but accessible
        self.tree.column("biz_name", width=200, anchor="w")
        self.tree.column("category", width=100, anchor="w")
        self.tree.column("start_date", width=75, anchor="w")
        self.tree.column("end_date", width=75, anchor="w")
        self.tree.column("external_url", width=200, anchor="w")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Bind double-click to edit
        self.tree.bind("<Double-1>", self.edit_business)


    def setup_filters(self):
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Label(filter_frame, text="Business Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ttk.Entry(filter_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(filter_frame, text="Year:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.year_entry = ttk.Entry(filter_frame, width=10)
        self.year_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(filter_frame, text="Type:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.type_entry = ttk.Entry(filter_frame, width=20)
        self.type_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(filter_frame, text="Search", command=self.load_businesses).grid(row=0, column=6, padx=10)
        ttk.Button(filter_frame, text="Clear", command=self.reset_filters).grid(row=0, column=7, padx=5)


    def reset_filters(self):
        self.name_entry.delete(0, tk.END)
        self.year_entry.delete(0, tk.END)
        self.type_entry.delete(0, tk.END)
        self.load_businesses()

    def setup_buttons(self):
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="Add", command=self.add_business).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Edit", command=self.edit_business).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_business).pack(side="left", padx=5)

    def sort_by_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        items.sort(reverse=self.sort_column == col and not self.sort_reverse)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, '', idx)
        self.sort_column = col
        self.sort_reverse = not (self.sort_column == col and self.sort_reverse)


    def load_businesses(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        query = """
            SELECT biz_id, biz_name, category,
                   start_date, start_date_precision,
                   end_date, end_date_precision,
                   external_url
            FROM Biz
            WHERE 1=1
        """
        params = []

        name_filter = self.name_entry.get().strip()
        if name_filter:
            query += " AND biz_name LIKE ?"
            params.append(f"%{name_filter}%")

        year_filter = self.year_entry.get().strip()
        if year_filter.isdigit():
            query += """
                AND (
                    (
                        TRIM(IFNULL(start_date, '')) != '' AND
                        TRIM(IFNULL(end_date, '')) != '' AND
                        CAST(SUBSTR(start_date, 1, 4) AS INTEGER) <= ? AND
                        CAST(SUBSTR(end_date, 1, 4) AS INTEGER) >= ?
                    )
                    OR (
                        TRIM(IFNULL(start_date, '')) != '' AND
                        TRIM(IFNULL(end_date, '')) = '' AND
                        CAST(SUBSTR(start_date, 1, 4) AS INTEGER) = ?
                    )
                    OR (
                        TRIM(IFNULL(start_date, '')) = '' AND
                        TRIM(IFNULL(end_date, '')) != '' AND
                        CAST(SUBSTR(end_date, 1, 4) AS INTEGER) = ?
                    )
                )
            """
            params.extend([year_filter, year_filter, year_filter, year_filter])

        type_filter = self.type_entry.get().strip()
        if type_filter:
            query += " AND category LIKE ?"
            params.append(f"%{type_filter}%")

        query += " ORDER BY biz_name"
        self.cursor.execute(query, tuple(params))

        for row in self.cursor.fetchall():
            (
                biz_id,
                name,
                category,
                start_date,
                start_prec,
                end_date,
                end_prec,
                url,
            ) = row
            start_fmt = format_date_for_display(start_date, start_prec) if start_date else ""
            end_fmt = format_date_for_display(end_date, end_prec) if end_date else ""
            self.tree.insert(
                '',
                'end',
                values=(
                    biz_id,
                    name or "",
                    category or "",
                    start_fmt,
                    end_fmt,
                    url or "",
                ),
            )

    def add_business(self):
        open_edit_business_form()

    
    def edit_business(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        biz_id = self.tree.item(selected[0])['values'][0]
        open_edit_business_form(biz_id)

    
    def delete_business(self):
        selected = self.tree.selection()
        if not selected:
            return

        biz_id = self.tree.item(selected[0])['values'][0]

        # Check support tables
        tables_to_check = [
            ("BizOwnership", "biz_ownership_id"),
            ("BizEmployment", "id"),
            ("BizLocHistory", "start_date"),
            ("BizEvents", "event_id")
        ]

        for table, id_field in tables_to_check:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE biz_id = ?", (biz_id,))
            count = self.cursor.fetchone()[0]
            if count > 0:
                messagebox.showwarning(
                    "Cannot Delete",
                    f"This business has related records in '{table}' ({count} found). Please remove them first."
                )
                return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this business?")
        if confirm:
            self.cursor.execute("DELETE FROM Biz WHERE biz_id = ?", (biz_id,))
            self.conn.commit()
            self.load_businesses()


def main():
    root = tk.Tk()
    app = BusinessManager(root)
    root.geometry("1000x600")
    root.mainloop()

if __name__ == "__main__":
    main()
