import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from app.config import DB_PATH
from app.context_menu import create_context_menu
from app.person_linkage import person_search_popup


def edit_staff(master, church_id, staff_id=None, refresh=None):
    win = tk.Toplevel(master)
    StaffEditor(win, church_id, staff_id, refresh)
    win.grab_set()
    win.transient(master)
    return win


class StaffEditor:
    def __init__(self, master, church_id, staff_id=None, refresh=None):
        self.master = master
        self.church_id = church_id
        self.staff_id = staff_id
        self.refresh = refresh
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.person_id = None
        self.setup_form()
        if staff_id:
            self.load_data()

    def setup_form(self):
        labels = ["Title", "Start Date", "End Date", "Notes"]
        self.entries = {}
        for row, label in enumerate(labels):
            ttk.Label(self.master, text=label + ":").grid(row=row+1, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(self.master, width=40)
            entry.grid(row=row+1, column=1, sticky="w", padx=5, pady=5)
            create_context_menu(entry)
            self.entries[label] = entry

        ttk.Label(self.master, text="Person:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        pframe = ttk.Frame(self.master)
        pframe.grid(row=0, column=1, sticky="w")
        self.person_label = ttk.Label(pframe, text="(none)", width=30, relief="sunken")
        self.person_label.pack(side="left")
        ttk.Button(pframe, text="Lookup", command=lambda: person_search_popup(self.set_person)).pack(side="left", padx=5)

        btn_frame = ttk.Frame(self.master)
        btn_frame.grid(row=len(labels)+1, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)

    def set_person(self, pid):
        if pid is None:
            self.person_label.config(text="(none)")
            self.person_id = None
            return
        self.cursor.execute("SELECT first_name, last_name FROM People WHERE id=?", (pid,))
        row = self.cursor.fetchone()
        if row:
            self.person_label.config(text=f"{row[0]} {row[1]}")
            self.person_id = pid

    def load_data(self):
        self.cursor.execute(
            "SELECT person_id, title, start_date, end_date, notes FROM Church_Staff WHERE church_staff_id=?",
            (self.staff_id,),
        )
        row = self.cursor.fetchone()
        if row:
            pid, title, sdate, edate, notes = row
            self.set_person(pid)
            self.entries["Title"].insert(0, title or "")
            self.entries["Start Date"].insert(0, sdate or "")
            self.entries["End Date"].insert(0, edate or "")
            self.entries["Notes"].insert(0, notes or "")

    def save(self):
        if not self.person_id:
            messagebox.showerror("Missing", "Person required")
            return
        data = (
            self.church_id,
            self.person_id,
            self.entries["Title"].get().strip() or None,
            self.entries["Start Date"].get().strip() or None,
            self.entries["End Date"].get().strip() or None,
            self.entries["Notes"].get().strip() or None,
        )
        if self.staff_id:
            self.cursor.execute(
                "UPDATE Church_Staff SET church_id=?, person_id=?, title=?, start_date=?, end_date=?, notes=? WHERE church_staff_id=?",
                data + (self.staff_id,),
            )
        else:
            self.cursor.execute(
                "INSERT INTO Church_Staff (church_id, person_id, title, start_date, end_date, notes) VALUES (?, ?, ?, ?, ?, ?)",
                data,
            )
            self.staff_id = self.cursor.lastrowid
        self.conn.commit()
        if self.refresh:
            self.refresh()
        self.master.destroy()