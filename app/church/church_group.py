import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from app.config import DB_PATH
from app.context_menu import create_context_menu


def edit_group(master, church_id, group_id=None, refresh=None):
    win = tk.Toplevel(master)
    GroupEditor(win, church_id, group_id, refresh)
    win.grab_set()
    win.transient(master)
    return win


class GroupEditor:
    def __init__(self, master, church_id, group_id=None, refresh=None):
        self.master = master
        self.church_id = church_id
        self.group_id = group_id
        self.refresh = refresh
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.setup_form()
        if group_id:
            self.load_data()

    def setup_form(self):
        labels = ["Group Name", "Year Active", "Group Type", "Notes"]
        self.entries = {}
        for row, label in enumerate(labels):
            ttk.Label(self.master, text=label + ":").grid(row=row, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(self.master, width=40)
            entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
            create_context_menu(entry)
            self.entries[label] = entry
        btn_frame = ttk.Frame(self.master)
        btn_frame.grid(row=len(labels), columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)

    def load_data(self):
        self.cursor.execute(
            "SELECT group_name, year_active, group_type, notes FROM Church_Group WHERE church_group_id=?",
            (self.group_id,),
        )
        row = self.cursor.fetchone()
        if row:
            for label, value in zip(["Group Name", "Year Active", "Group Type", "Notes"], row):
                self.entries[label].insert(0, value or "")

    def save(self):
        data = [self.entries[l].get().strip() or None for l in ["Group Name", "Year Active", "Group Type", "Notes"]]
        if not data[0]:
            messagebox.showerror("Missing", "Group Name is required")
            return
        if self.group_id:
            self.cursor.execute(
                "UPDATE Church_Group SET group_name=?, year_active=?, group_type=?, notes=? WHERE church_group_id=?",
                (*data, self.group_id),
            )
        else:
            self.cursor.execute(
                "INSERT INTO Church_Group (church_id, group_name, year_active, group_type, notes) VALUES (?, ?, ?, ?, ?)",
                (self.church_id, *data),
            )
            self.group_id = self.cursor.lastrowid
        self.conn.commit()
        if self.refresh:
            self.refresh()
        self.master.destroy()