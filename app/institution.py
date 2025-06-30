import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# Local imports
from app.config import DB_PATH
from app.date_utils import format_date_for_display
from app.editinst import open_edit_institution_form


class InstitutionManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Institution Search")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

        self.sort_column = None
        self.sort_reverse = False

        self.setup_filters()
        self.setup_tree()
        self.setup_buttons()
        self.load_institutions()

    def setup_filters(self):
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Label(filter_frame, text="Institution Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ttk.Entry(filter_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(filter_frame, text="Year:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.year_entry = ttk.Entry(filter_frame, width=10)
        self.year_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(filter_frame, text="Type:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.type_entry = ttk.Entry(filter_frame, width=20)
        self.type_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(filter_frame, text="Search", command=self.load_institutions).grid(row=0, column=6, padx=10)
        ttk.Button(filter_frame, text="Clear", command=self.reset_filters).grid(row=0, column=7, padx=5)

    def reset_filters(self):
        self.name_entry.delete(0, tk.END)
        self.year_entry.delete(0, tk.END)
        self.type_entry.delete(0, tk.END)
        self.load_institutions()

    def setup_tree(self):
        columns = ("id", "name", "type", "start", "end")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")

        headings = {
            "name": "Name",
            "type": "Type",
            "start": "Start",
            "end": "End",
        }

        for key in columns:
            if key == "id":
                self.tree.column("id", width=0, stretch=False)
            else:
                self.tree.heading(key, text=headings.get(key, key.title()), command=lambda c=key: self.sort_by_column(c))

        self.tree.column("name", width=200, anchor="w")
        self.tree.column("type", width=100, anchor="w")
        self.tree.column("start", width=75, anchor="w")
        self.tree.column("end", width=75, anchor="w")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.edit_institution)

    def setup_buttons(self):
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="Add", command=self.add_institution).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Edit", command=self.edit_institution).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_institution).pack(side="left", padx=5)

    def sort_by_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        items.sort(reverse=self.sort_column == col and not self.sort_reverse)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)
        self.sort_column = col
        self.sort_reverse = not (self.sort_column == col and self.sort_reverse)


    def load_institutions(self):
        self.tree.delete(*self.tree.get_children())

        query = """
            SELECT inst_id, inst_name, inst_type,
                   start_date, start_date_precision,
                   end_date, end_date_precision
            FROM Institution
            WHERE 1=1
        """
        params = []

        name_filter = self.name_entry.get().strip()
        if name_filter:
            query += " AND inst_name LIKE ?"
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
            query += " AND inst_type LIKE ?"
            params.append(f"%{type_filter}%")

        query += " ORDER BY inst_name"
        self.cursor.execute(query, tuple(params))

        for row in self.cursor.fetchall():
            inst_id, name, typ, start_date, start_prec, end_date, end_prec = row
            start_fmt = format_date_for_display(start_date, start_prec) if start_date else ""
            end_fmt = format_date_for_display(end_date, end_prec) if end_date else ""
            self.tree.insert("", "end", values=(inst_id, name, typ, start_fmt, end_fmt))

    def add_institution(self):
        open_edit_institution_form()
        self.load_institutions()

    def get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record.")
            return None
        return self.tree.item(selected[0])["values"][0]

    def edit_institution(self, event=None):
        inst_id = self.get_selected_id()
        if not inst_id:
            return
        open_edit_institution_form(inst_id)
        self.load_institutions()

    def delete_institution(self):
        inst_id = self.get_selected_id()
        if not inst_id:
            return

        queries = [
            ("Inst_Event", "SELECT COUNT(*) FROM Inst_Event WHERE inst_id = ?"),
            ("Inst_Group", "SELECT COUNT(*) FROM Inst_Group WHERE inst_id = ?"),
            (
                "Inst_GroupMember",
                """
                SELECT COUNT(*)
                FROM Inst_GroupMember gm
                JOIN Inst_Group g ON gm.inst_group_id = g.inst_group_id
                WHERE g.inst_id = ?
                """,
            ),
            ("Inst_Staff", "SELECT COUNT(*) FROM Inst_Staff WHERE inst_id = ?"),
            ("InstLocHistory", "SELECT COUNT(*) FROM InstLocHistory WHERE inst_id = ?"),
        ]

        for table, query in queries:
            self.cursor.execute(query, (inst_id,))

        for table, query in queries:
            self.cursor.execute(query, (inst_id,))
            count = self.cursor.fetchone()[0]
            if count:
                messagebox.showwarning(
                    "Cannot Delete",
                    f"Supporting records were found for this Institution. You must remove them first.",
                )
                return

        if messagebox.askyesno("Confirm Delete", "Delete selected institution?"):
            self.cursor.execute("DELETE FROM Institution WHERE inst_id = ?", (inst_id,))
            self.conn.commit()
            self.load_institutions()


def main():
    root = tk.Tk()
    root.geometry("800x600")
    app = InstitutionManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()