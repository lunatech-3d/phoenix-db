import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from app.config import DB_PATH
from app.context_menu import create_context_menu
from app.person_linkage import person_search_popup
from app.date_utils import parse_date_input


def edit_funeral(master, church_id, funeral_id=None, person_id=None, refresh=None):
    win = tk.Toplevel(master)
    FuneralEditor(win, church_id, funeral_id, person_id, refresh)
    win.grab_set()
    win.transient(master)
    return win


class FuneralEditor:
    def __init__(self, master, church_id, funeral_id=None, person_id=None, refresh=None):
        self.master = master
        self.church_id = church_id
        self.funeral_id = funeral_id
        self.refresh = refresh
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.person_id = person_id
        self.officiant_id = None
        self.setup_form()
        if funeral_id:
            self.load_data()
        elif person_id:
            self.set_person(person_id)

    def setup_form(self):
        labels = ["Funeral Date", "Notes", "Curator Summary", "Tags"]
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

        ttk.Label(self.master, text="Officiant:").grid(row=len(labels)+1, column=0, sticky="e", padx=5, pady=5)
        oframe = ttk.Frame(self.master)
        oframe.grid(row=len(labels)+1, column=1, sticky="w")
        self.off_label = ttk.Label(oframe, text="(none)", width=30, relief="sunken")
        self.off_label.pack(side="left")
        ttk.Button(oframe, text="Lookup", command=lambda: person_search_popup(self.set_officiant)).pack(side="left", padx=5)

        btn_frame = ttk.Frame(self.master)
        btn_frame.grid(row=len(labels)+2, columnspan=2, pady=10)
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

    def set_officiant(self, pid):
        if pid is None:
            self.off_label.config(text="(none)")
            self.officiant_id = None
            return
        self.cursor.execute("SELECT first_name, last_name FROM People WHERE id=?", (pid,))
        row = self.cursor.fetchone()
        if row:
            self.off_label.config(text=f"{row[0]} {row[1]}")
            self.officiant_id = pid

    def load_data(self):
        self.cursor.execute(
            "SELECT person_id, funeral_date, officiant_id, notes, curator_summary, event_context_tags FROM Funeral WHERE funeral_id=?",
            (self.funeral_id,),
        )
        row = self.cursor.fetchone()
        if row:
            pid, date, oid, notes, summ, tags = row
            self.set_person(pid)
            self.set_officiant(oid)
            self.entries["Funeral Date"].insert(0, date or "")
            self.entries["Notes"].insert(0, notes or "")
            self.entries["Curator Summary"].insert(0, summ or "")
            self.entries["Tags"].insert(0, tags or "")

    def save(self):
        if not self.person_id:
            messagebox.showerror("Missing", "Person required")
            return
        try:
            fdate, _ = parse_date_input(self.entries["Funeral Date"].get().strip()) if self.entries["Funeral Date"].get().strip() else (None, None)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e))
            return
        data = (
            self.person_id,
            self.church_id,
            fdate,
            self.officiant_id,
            self.entries["Notes"].get().strip() or None,
            self.entries["Curator Summary"].get().strip() or None,
            self.entries["Tags"].get().strip() or None,
        )
        if self.funeral_id:
            self.cursor.execute(
                "UPDATE Funeral SET person_id=?, church_id=?, funeral_date=?, officiant_id=?, notes=?, curator_summary=?, event_context_tags=? WHERE funeral_id=?",
                data + (self.funeral_id,),
            )
        else:
            self.cursor.execute(
                "INSERT INTO Funeral (person_id, church_id, funeral_date, officiant_id, notes, curator_summary, event_context_tags) VALUES (?, ?, ?, ?, ?, ?, ?)",
                data,
            )
            self.funeral_id = self.cursor.lastrowid
        self.conn.commit()
        if self.refresh:
            self.refresh()
        self.master.destroy()