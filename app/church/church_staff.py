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
        labels = ["Title", "Start Date", "End Date", "Notes", "Tags"]
        self.entries = {}
        for row, label in enumerate(labels):
            ttk.Label(self.master, text=label + ":").grid(row=row+1, column=0, sticky="e", padx=5, pady=5)
            if label == "Notes":
                widget = tk.Text(self.master, width=40, height=4, wrap="word")
                widget.grid(row=row+1, column=1, sticky="we", padx=5, pady=5)
            else:
                widget = ttk.Entry(self.master, width=40)
                widget.grid(row=row+1, column=1, sticky="w", padx=5, pady=5)
            create_context_menu(widget)
            self.entries[label] = widget

        ttk.Label(self.master, text="Person:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        pframe = ttk.Frame(self.master)
        pframe.grid(row=0, column=1, sticky="w")
        self.person_label = ttk.Label(pframe, text="(none)", width=30, relief="sunken")
        self.person_label.pack(side="left")
        ttk.Button(pframe, text="Lookup", command=lambda: person_search_popup(self.set_person)).pack(side="left", padx=5)

        summary_row = len(labels) + 1
        ttk.Label(self.master, text="Curator Summary:").grid(row=summary_row, column=0, sticky="ne", padx=5, pady=5)
        summary_text = tk.Text(self.master, width=40, height=4, wrap="word")
        summary_text.grid(row=summary_row, column=1, sticky="we", padx=5, pady=5)
        create_context_menu(summary_text)
        self.entries["Curator Summary"] = summary_text
        
        btn_frame = ttk.Frame(self.master)
        btn_frame.grid(row=summary_row + 1, columnspan=2, pady=10)
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
            "SELECT person_id, title, start_date, end_date, notes, event_context_tags, curator_summary FROM Church_Staff WHERE church_staff_id=?",
            (self.staff_id,),
        )
        row = self.cursor.fetchone()
        if row:
            pid, title, sdate, edate, notes, tags, summary = row
            self.set_person(pid)
            self.entries["Title"].insert(0, title or "")
            self.entries["Start Date"].insert(0, sdate or "")
            self.entries["End Date"].insert(0, edate or "")
            self.entries["Notes"].insert("1.0" if isinstance(self.entries["Notes"], tk.Text) else 0, notes or "")
            self.entries["Tags"].insert(0, tags or "")
            self.entries["Curator Summary"].insert("1.0", summary or "")

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
            self.entries["Notes"].get("1.0", tk.END).strip() or None,
            self.entries["Tags"].get().strip() or None,
            self.entries["Curator Summary"].get("1.0", tk.END).strip() or None,
        )
        if self.staff_id:
            self.cursor.execute(
                "UPDATE Church_Staff SET church_id=?, person_id=?, title=?, start_date=?, end_date=?, notes=? WHERE church_staff_id=?",
                data + (self.staff_id,),
            )
        else:
            self.cursor.execute("INSERT INTO Church_Staff (church_id, person_id, title, start_date, end_date, notes, event_context_tags, curator_summary) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                data,
            )
            self.staff_id = self.cursor.lastrowid
        self.conn.commit()
        if self.refresh:
            self.refresh()
        self.master.destroy()