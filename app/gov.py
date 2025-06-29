import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from app.config import DB_PATH
from app.context_menu import create_context_menu
from app.date_utils import format_date_for_display, date_sort_key
from app.editgov import open_edit_agency_form


class GovAgencyManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Government Agencies")
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

        self.sort_column = None
        self.sort_reverse = False

        self.setup_filters()
        self.setup_tree()
        self.setup_buttons()
        self.load_agencies()

    def setup_filters(self):
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Label(filter_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ttk.Entry(filter_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        create_context_menu(self.name_entry)

        ttk.Label(filter_frame, text="Jurisdiction:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.juris_entry = ttk.Entry(filter_frame, width=20)
        self.juris_entry.grid(row=0, column=3, padx=5, pady=5)
        create_context_menu(self.juris_entry)

        ttk.Label(filter_frame, text="Type:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.type_entry = ttk.Entry(filter_frame, width=20)
        self.type_entry.grid(row=0, column=5, padx=5, pady=5)
        create_context_menu(self.type_entry)

        ttk.Button(filter_frame, text="Search", command=self.load_agencies).grid(row=0, column=6, padx=10)
        ttk.Button(filter_frame, text="Clear", command=self.reset_filters).grid(row=0, column=7, padx=5)

    def reset_filters(self):
        self.name_entry.delete(0, tk.END)
        self.juris_entry.delete(0, tk.END)
        self.type_entry.delete(0, tk.END)
        self.load_agencies()

    def setup_tree(self):
        columns = ("id", "name", "jurisdiction", "type", "start", "end")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")

        headings = {
            "name": "Name",
            "jurisdiction": "Jurisdiction",
            "type": "Type",
            "start": "Start",
            "end": "End",
        }

        for col in columns:
            if col == "id":
                self.tree.column("id", width=0, stretch=False)
            else:
                self.tree.heading(col, text=headings.get(col, col.title()), command=lambda c=col: self.sort_by_column(c))

        self.tree.column("name", width=220, anchor="w")
        self.tree.column("jurisdiction", width=140, anchor="w")
        self.tree.column("type", width=120, anchor="w")
        self.tree.column("start", width=80, anchor="w")
        self.tree.column("end", width=80, anchor="w")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.edit_agency)

    def setup_buttons(self):
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="Add", command=self.add_agency).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Edit", command=self.edit_agency).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_agency).pack(side="left", padx=5)

    def sort_by_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        reverse = self.sort_column == col and not self.sort_reverse
        if col in ("start", "end"):
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)
        self.sort_reverse = reverse
        self.sort_column = col

    def load_agencies(self):
        self.tree.delete(*self.tree.get_children())

        query = """
            SELECT gov_agency_id, name, jurisdiction, type,
                   start_date, start_date_precision,
                   end_date, end_date_precision
            FROM GovAgency
            WHERE 1=1
        """
        params = []

        name_filter = self.name_entry.get().strip()
        if name_filter:
            query += " AND name LIKE ?"
            params.append(f"%{name_filter}%")

        juris_filter = self.juris_entry.get().strip()
        if juris_filter:
            query += " AND jurisdiction LIKE ?"
            params.append(f"%{juris_filter}%")

        type_filter = self.type_entry.get().strip()
        if type_filter:
            query += " AND type LIKE ?"
            params.append(f"%{type_filter}%")

        query += " ORDER BY name"
        self.cursor.execute(query, tuple(params))

        for row in self.cursor.fetchall():
            (
                ag_id,
                name,
                juris,
                typ,
                s_date,
                s_prec,
                e_date,
                e_prec,
            ) = row
            start_disp = format_date_for_display(s_date, s_prec) if s_date else ""
            end_disp = format_date_for_display(e_date, e_prec) if e_date else ""
            self.tree.insert(
                "",
                "end",
                values=(ag_id, name, juris, typ, start_disp, end_disp),
            )

    def add_agency(self):
        win = open_edit_agency_form(parent=self.root)
        if win:
            self.root.wait_window(win)
        self.load_agencies()

    def get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record.")
            return None
        return self.tree.item(selected[0])["values"][0]

    def edit_agency(self, event=None):
        agency_id = self.get_selected_id()
        if not agency_id:
            return
        win = open_edit_agency_form(agency_id, parent=self.root)
        if win:
            self.root.wait_window(win)
        self.load_agencies()

    def delete_agency(self):
        agency_id = self.get_selected_id()
        if not agency_id:
            return

        # Check for dependent records
        tables = ["GovPosition", "GovEvents"]
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE agency_id=?", (agency_id,))
            count = self.cursor.fetchone()[0]
            if count:
                messagebox.showwarning(
                    "Cannot Delete",
                    f"Related records found in {table} ({count}). Remove them first.",
                )
                return

        if messagebox.askyesno("Confirm Delete", "Delete selected agency?"):
            self.cursor.execute("DELETE FROM GovAgency WHERE gov_agency_id=?", (agency_id,))
            self.conn.commit()
            self.load_agencies()

def main():
    root = tk.Tk()
    root.geometry("900x600")
    app = GovAgencyManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()