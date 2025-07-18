import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from app.config import DB_PATH
from app.context_menu import create_context_menu
from app.person_linkage import person_search_popup
import subprocess
import sys


def manage_members(master, group_id):
    win = tk.Toplevel(master)
    win.title("Manage Group Members")
    win.geometry("800x400")  # or any suitable size
    MemberManager(win, group_id)
    win.grab_set()
    win.transient(master)
    return win


class MemberManager:
    def __init__(self, master, group_id):
        self.master = master
        self.group_id = group_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.setup_ui()
        self.load_members()

    def setup_ui(self):
        self.tree = ttk.Treeview(self.master, columns=("id", "person", "role", "recognition", "notes"), show="headings")
        for col in ("person", "role", "recognition", "notes"):
            self.tree.heading(col, text=col.title())
        self.tree.column("id", width=0, stretch=False)
        self.tree.bind("<Double-1>", self.on_member_double)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Add", command=self.add_member).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Edit", command=self.edit_member).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_member).pack(side="left", padx=2)

    def load_members(self):
        self.tree.delete(*self.tree.get_children())
        self.cursor.execute(
            """SELECT m.church_group_member_id, m.person_id,
                       p.first_name || ' ' || p.last_name, m.role, m.recognition, m.notes
               FROM Church_GroupMember m JOIN People p ON m.person_id=p.id
               WHERE m.church_group_id=?""",
            (self.group_id,),
        )
        for row in self.cursor.fetchall():
            mid, pid, pname, role, recog, notes = row
            self.tree.insert("", "end", values=(mid, pname, role, recog or "", notes or ""), tags=(pid,))   

    def add_member(self):
        MemberEditor(self.master, self.group_id, refresh=self.load_members)

    def edit_member(self):
        sel = self.tree.selection()
        if not sel:
            return
        mid = self.tree.item(sel[0])["values"][0]
        MemberEditor(self.master, self.group_id, member_id=mid, refresh=self.load_members)

    def delete_member(self):
        sel = self.tree.selection()
        if not sel:
            return
        mid = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Delete", "Delete selected member?"):
            self.cursor.execute("DELETE FROM Church_GroupMember WHERE church_group_member_id=?", (mid,))
            self.conn.commit()
            self.load_members()

    def on_member_double(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        pid = self.tree.item(sel[0], "tags")[0]
        subprocess.Popen([sys.executable, "-m", "app.editme", str(pid)])


class MemberEditor:
    def __init__(self, master, group_id, member_id=None, refresh=None):
        self.master = tk.Toplevel(master)
        self.group_id = group_id
        self.member_id = member_id
        self.refresh = refresh
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.person_id = None
        self.setup_form()
        if member_id:
            self.load_data()
        self.master.grab_set()
        self.master.transient(master)

    def setup_form(self):
        labels = ["Role", "Recognition", "Start Date", "End Date", "Notes", "Tags"]
        self.entries = {}
        for row, label in enumerate(labels):
            ttk.Label(self.master, text=label + ":").grid(row=row+1, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(self.master, width=40)
            entry.grid(row=row+1, column=1, sticky="w", padx=5, pady=5)
            create_context_menu(entry)
            self.entries[label] = entry

        summary_row = len(labels) + 1
        ttk.Label(self.master, text="Curator Summary:").grid(row=summary_row, column=0, sticky="ne", padx=5, pady=5)
        summary_text = tk.Text(self.master, width=40, height=4, wrap="word")
        summary_text.grid(row=summary_row, column=1, sticky="we", padx=5, pady=5)
        create_context_menu(summary_text)
        self.entries["Curator Summary"] = summary_text

        ttk.Label(self.master, text="Person:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        pframe = ttk.Frame(self.master)
        pframe.grid(row=0, column=1, sticky="w")
        self.person_label = ttk.Label(pframe, text="(none)", width=30, relief="sunken")
        self.person_label.pack(side="left")
        ttk.Button(pframe, text="Lookup", command=lambda: person_search_popup(self.set_person)).pack(side="left", padx=5)

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
            "SELECT person_id, role, recognition, start_date, end_date, notes, event_context_tags, curator_summary FROM Church_GroupMember WHERE church_group_member_id=?",
            (self.member_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            return
        pid, role, recog, sdate, edate, notes, tags, summary = row
        self.set_person(pid)
        self.entries["Role"].insert(0, role or "")
        self.entries["Recognition"].insert(0, recog or "")
        self.entries["Start Date"].insert(0, sdate or "")
        self.entries["End Date"].insert(0, edate or "")
        self.entries["Notes"].insert(0, notes or "")
        self.entries["Tags"].insert(0, tags or "")
        self.entries["Curator Summary"].insert("1.0", summary or "")

    def save(self):
        if not self.person_id:
            messagebox.showerror("Missing", "Person required")
            return
        data = (
            self.group_id,
            self.person_id,
            self.entries["Role"].get().strip() or None,
            self.entries["Recognition"].get().strip() or None,
            self.entries["Start Date"].get().strip() or None,
            self.entries["End Date"].get().strip() or None,
            self.entries["Notes"].get().strip() or None,
            
        )
        if self.member_id:
            self.cursor.execute(
                "UPDATE Church_GroupMember SET church_group_id=?, person_id=?, role=?, recognition=?, start_date=?, end_date=?, notes=?, event_context_tags=?, curator_summary=? WHERE church_group_member_id=?",
                data + (self.member_id,),
            )
        else:
            self.cursor.execute(
                "INSERT INTO Church_GroupMember (church_group_id, person_id, role, recognition, start_date, end_date, notes, event_context_tags, curator_summary) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                data,
            )
            self.member_id = self.cursor.lastrowid
        self.conn.commit()
        if self.refresh:
            self.refresh()
        self.master.destroy()