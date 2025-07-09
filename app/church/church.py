import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from app.config import DB_PATH
from app.date_utils import format_date_for_display
from app.church.church_form import open_church_form


class ChurchManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Church Search")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.sort_column = None
        self.sort_reverse = False

        self.setup_filters()
        self.setup_tree()
        self.setup_buttons()
        self.load_churches()

    def setup_filters(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Label(frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ttk.Entry(frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Year:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.year_entry = ttk.Entry(frame, width=10)
        self.year_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Denomination:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.denom_entry = ttk.Entry(frame, width=20)
        self.denom_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(frame, text="Search", command=self.load_churches).grid(row=0, column=6, padx=10)
        ttk.Button(frame, text="Clear", command=self.reset_filters).grid(row=0, column=7, padx=5)

    def reset_filters(self):
        self.name_entry.delete(0, tk.END)
        self.year_entry.delete(0, tk.END)
        self.denom_entry.delete(0, tk.END)
        self.load_churches()

    def setup_tree(self):
        columns = ("id", "name", "denom", "start", "end")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")

        headings = {
            "name": "Name",
            "denom": "Denomination",
            "start": "Start",
            "end": "End",
        }

        for col in columns:
            if col == "id":
                self.tree.column("id", width=0, stretch=False)
            else:
                self.tree.heading(col, text=headings.get(col, col.title()), command=lambda c=col: self.sort_by_column(c))

        self.tree.column("name", width=200, anchor="w")
        self.tree.column("denom", width=150, anchor="w")
        self.tree.column("start", width=75, anchor="w")
        self.tree.column("end", width=75, anchor="w")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.edit_church)

    def setup_buttons(self):
        btn = ttk.Frame(self.root)
        btn.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn, text="Add", command=self.add_church).pack(side="left", padx=5)
        ttk.Button(btn, text="Edit", command=self.edit_church).pack(side="left", padx=5)
        ttk.Button(btn, text="Delete", command=self.delete_church).pack(side="left", padx=5)

    def sort_by_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        items.sort(reverse=self.sort_column == col and not self.sort_reverse)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)
        self.sort_reverse = self.sort_column == col and not self.sort_reverse
        self.sort_column = col

    def load_churches(self):
        self.tree.delete(*self.tree.get_children())

        query = """
            SELECT church_id, church_name, denomination,
                   start_date, start_date_precision,
                   end_date, end_date_precision
            FROM Church
            WHERE 1=1
        """
        params = []

        name_filter = self.name_entry.get().strip()
        if name_filter:
            query += " AND church_name LIKE ?"
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
                    ) OR (
                        TRIM(IFNULL(start_date, '')) != '' AND
                        TRIM(IFNULL(end_date, '')) = '' AND
                        CAST(SUBSTR(start_date, 1, 4) AS INTEGER) = ?
                    ) OR (
                        TRIM(IFNULL(start_date, '')) = '' AND
                        TRIM(IFNULL(end_date, '')) != '' AND
                        CAST(SUBSTR(end_date, 1, 4) AS INTEGER) = ?
                    )
                )
            """
            params.extend([year_filter, year_filter, year_filter, year_filter])

        denom_filter = self.denom_entry.get().strip()
        if denom_filter:
            query += " AND denomination LIKE ?"
            params.append(f"%{denom_filter}%")

        query += " ORDER BY church_name"
        self.cursor.execute(query, tuple(params))

        for row in self.cursor.fetchall():
            cid, name, denom, sdate, sprec, edate, eprec = row
            start_disp = format_date_for_display(sdate, sprec) if sdate else ""
            end_disp = format_date_for_display(edate, eprec) if edate else ""
            self.tree.insert("", "end", values=(cid, name, denom, start_disp, end_disp))

    def add_church(self):
        open_church_form()
        self.load_churches()

    def get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a record.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def edit_church(self, event=None):
        cid = self.get_selected_id()
        if not cid:
            return
        open_church_form(cid)
        self.load_churches()

    def delete_church(self):
        cid = self.get_selected_id()
        if not cid:
            return
        tables = [
            ("Church_Event", "church_id"),
            ("Church_Group", "church_id"),
            (
                "Church_GroupMember gm JOIN Church_Group g ON gm.church_group_id = g.church_group_id",
                "g.church_id",
            ),
            ("Church_Staff", "church_id"),
            ("Baptism", "church_id"),
            ("Funeral", "church_id"),
        ]
        for table, field in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {field}=?", (cid,))
            if self.cursor.fetchone()[0]:
                messagebox.showwarning(
                    "Cannot Delete",
                    "Supporting records were found for this Church. You must remove them first.",
                )
                return
        if messagebox.askyesno("Confirm Delete", "Delete selected church?"):
            self.cursor.execute("DELETE FROM Church WHERE church_id=?", (cid,))
            self.conn.commit()
            self.load_churches()


def main():
    root = tk.Tk()
    root.geometry("800x600")
    ChurchManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()