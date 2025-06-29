import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from app.config import DB_PATH
from app.context_menu import create_context_menu, apply_context_menu_to_all_entries
from app.date_utils import (
    parse_date_input,
    format_date_for_display,
    add_date_format_menu,
)
from app.gov_linkage import open_gov_linkage_popup
from app.gov_position import open_position_manager

class EditGovAgencyForm:
    def __init__(self, master, agency_id=None):
        self.master = master
        self.agency_id = agency_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.parent_id = None
        self.entries = {}

        self.setup_form()

        if agency_id:
            self.load_data()
            self.load_children()
        else:
            self.disable_related()

    def setup_form(self):
        self.master.title("Edit Government Agency")
        row = 0

        ttk.Label(self.master, text="Name:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        name_entry = ttk.Entry(self.master, width=40)
        name_entry.grid(row=row, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        self.entries["name"] = name_entry
        create_context_menu(name_entry)
        row += 1

        ttk.Label(self.master, text="Jurisdiction:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        juris_entry = ttk.Entry(self.master, width=30)
        juris_entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        self.entries["jurisdiction"] = juris_entry
        create_context_menu(juris_entry)

        ttk.Label(self.master, text="Type:").grid(row=row, column=2, sticky="e", padx=5, pady=5)
        type_entry = ttk.Entry(self.master, width=20)
        type_entry.grid(row=row, column=3, sticky="w", padx=5, pady=5)
        self.entries["type"] = type_entry
        create_context_menu(type_entry)
        row += 1

        ttk.Label(self.master, text="Parent Agency:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        self.parent_label = ttk.Label(self.master, text="", width=30, relief="sunken", anchor="w")
        self.parent_label.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(self.master, text="Lookup", command=self.lookup_parent).grid(row=row, column=2, padx=2)
        ttk.Button(self.master, text="Clear", command=lambda: self.set_parent(None)).grid(row=row, column=3, padx=2)
        row += 1

        ttk.Label(self.master, text="Start Date:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        s_entry = ttk.Entry(self.master, width=15)
        s_entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        self.entries["start_date"] = s_entry
        create_context_menu(s_entry)
        add_date_format_menu(s_entry)
        row += 1

        ttk.Label(self.master, text="End Date:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        e_entry = ttk.Entry(self.master, width=15)
        e_entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        self.entries["end_date"] = e_entry
        create_context_menu(e_entry)
        add_date_format_menu(e_entry)
        row += 1

        ttk.Label(self.master, text="Notes:").grid(row=row, column=0, sticky="ne", padx=5, pady=5)
        notes_text = tk.Text(self.master, width=60, height=4)
        notes_text.grid(row=row, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        self.entries["notes"] = notes_text
        create_context_menu(notes_text)
        row += 1

        child_frame = ttk.LabelFrame(self.master, text="Child Agencies")
        child_frame.grid(row=row, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        self.child_tree = ttk.Treeview(child_frame, columns=("id", "name", "jurisdiction", "type"), show="headings", height=5)
        self.child_tree.column("id", width=0, stretch=False)
        self.child_tree.heading("name", text="Name")
        self.child_tree.heading("jurisdiction", text="Jurisdiction")
        self.child_tree.heading("type", text="Type")
        self.child_tree.column("name", width=220)
        self.child_tree.column("jurisdiction", width=140)
        self.child_tree.column("type", width=120)
        self.child_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.child_tree.bind("<Double-1>", self.open_child_agency)
        row += 1

        btn_frame = ttk.Frame(self.master)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        self.delete_btn = ttk.Button(btn_frame, text="Delete", command=self.delete_record)
        self.delete_btn.pack(side="left", padx=5)
        self.positions_btn = ttk.Button(btn_frame, text="Positions", command=self.open_positions)
        self.positions_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Close", command=self.master.destroy).pack(side="left", padx=5)

        apply_context_menu_to_all_entries(self.master)
        self.master.columnconfigure(1, weight=1)

    def disable_related(self):
        for widget in (self.child_tree, self.delete_btn, self.positions_btn):
            try:
                widget.state(["disabled"])
            except tk.TclError:
                widget.configure(state="disabled")

    def enable_related(self):
        for widget in (self.child_tree, self.delete_btn, self.positions_btn):
            try:
                widget.state(["!disabled"])
            except tk.TclError:
                widget.configure(state="normal")

    def lookup_parent(self):
        def set_parent_id(pid, _name=None):
            self.set_parent(pid)
        open_gov_linkage_popup(set_parent_id)

    def set_parent(self, pid):
        if pid:
            self.cursor.execute("SELECT name FROM GovAgency WHERE gov_agency_id=?", (pid,))
            row = self.cursor.fetchone()
            label = row[0] if row else ""
            self.parent_label.config(text=label)
            self.parent_id = pid
        else:
            self.parent_label.config(text="")
            self.parent_id = None

    def load_data(self):
        self.cursor.execute(
            """SELECT name, parent_agency_id, jurisdiction, type,
                      start_date, start_date_precision,
                      end_date, end_date_precision,
                      notes
               FROM GovAgency WHERE gov_agency_id=?""",
            (self.agency_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Agency record not found.", parent=self.master)
            self.master.destroy()
            return
        (
            name,
            parent_id,
            juris,
            typ,
            s_date,
            s_prec,
            e_date,
            e_prec,
            notes,
        ) = row
        self.entries["name"].insert(0, name or "")
        self.entries["jurisdiction"].insert(0, juris or "")
        self.entries["type"].insert(0, typ or "")
        self.entries["start_date"].insert(0, format_date_for_display(s_date, s_prec) if s_date else "")
        self.entries["end_date"].insert(0, format_date_for_display(e_date, e_prec) if e_date else "")
        if notes:
            self.entries["notes"].insert("1.0", notes)
        self.set_parent(parent_id)

    def load_children(self):
        if not self.agency_id:
            return
        self.child_tree.delete(*self.child_tree.get_children())
        self.cursor.execute(
            "SELECT gov_agency_id, name, jurisdiction, type FROM GovAgency WHERE parent_agency_id=? ORDER BY name",
            (self.agency_id,),
        )
        for row in self.cursor.fetchall():
            self.child_tree.insert("", "end", values=row)

    def open_positions(self):
        if not self.agency_id:
            return
        win = open_position_manager(self.agency_id, parent=self.master)
        if win:
            self.master.wait_window(win)
    
    def open_child_agency(self, event=None):
        sel = self.child_tree.selection()
        if not sel:
            return
        child_id = self.child_tree.item(sel[0])["values"][0]
        win = open_edit_agency_form(child_id, parent=self.master)
        if win:
            self.master.wait_window(win)
        self.load_children()

    def save(self):
        name = self.entries["name"].get().strip()
        if not name:
            messagebox.showerror("Missing", "Name is required.", parent=self.master)
            return
        jurisdiction = self.entries["jurisdiction"].get().strip()
        typ = self.entries["type"].get().strip()
        notes = self.entries["notes"].get("1.0", tk.END).strip()
        try:
            s_raw = self.entries["start_date"].get().strip()
            start_date, start_prec = parse_date_input(s_raw) if s_raw else (None, None)
            e_raw = self.entries["end_date"].get().strip()
            end_date, end_prec = parse_date_input(e_raw) if e_raw else (None, None)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e), parent=self.master)
            return

        if self.agency_id:
            self.cursor.execute(
                """UPDATE GovAgency SET name=?, parent_agency_id=?, jurisdiction=?, type=?,
                       start_date=?, start_date_precision=?, end_date=?, end_date_precision=?,
                       notes=? WHERE gov_agency_id=?""",
                (
                    name,
                    self.parent_id,
                    jurisdiction,
                    type,
                    start_date,
                    start_prec,
                    end_date,
                    end_prec,
                    notes,
                    self.agency_id,
                ),
            )
        else:
            self.cursor.execute(
                """INSERT INTO GovAgency (
                        name, parent_agency_id, jurisdiction, type,
                        start_date, start_date_precision,
                        end_date, end_date_precision,
                        notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    name,
                    self.parent_id,
                    jurisdiction,
                    type,
                    start_date,
                    start_prec,
                    end_date,
                    end_prec,
                    notes,
                ),
            )
            self.agency_id = self.cursor.lastrowid
            self.enable_related()
        self.conn.commit()
        messagebox.showinfo("Saved", "Agency record saved.", parent=self.master)
        self.master.destroy()

    def delete_record(self):
        if not self.agency_id:
            return
        # check related records
        self.cursor.execute("SELECT COUNT(*) FROM GovAgency WHERE parent_agency_id=?", (self.agency_id,))
        child_count = self.cursor.fetchone()[0]
        if child_count:
            messagebox.showwarning(
                "Cannot Delete",
                f"Child agencies exist ({child_count}). Remove them first.",
                parent=self.master,
            )
            return
        for table in ("GovPosition", "GovEvents"):
            self.cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE agency_id=?", (self.agency_id,))
            count = self.cursor.fetchone()[0]
            if count:
                messagebox.showwarning(
                    "Cannot Delete",
                    f"Related records found in {table} ({count}). Remove them first.",
                    parent=self.master,
                )
                return
        if messagebox.askyesno("Confirm Delete", "Delete this agency?", parent=self.master):
            self.cursor.execute("DELETE FROM GovAgency WHERE gov_agency_id=?", (self.agency_id,))
            self.conn.commit()
            self.master.destroy()


def open_edit_agency_form(agency_id=None, parent=None):
    if parent is None:
        root = tk.Tk()
        EditGovAgencyForm(root, agency_id)
        root.geometry("700x500")
        root.mainloop()
        return None
    else:
        win = tk.Toplevel(parent)
        EditGovAgencyForm(win, agency_id)
        win.grab_set()
        return win


if __name__ == "__main__":
    import sys
    arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    open_edit_agency_form(arg)