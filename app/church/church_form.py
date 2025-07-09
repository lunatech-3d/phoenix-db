import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

from app.config import DB_PATH
from app.date_utils import format_date_for_display
from . import (
    church_event,
    church_group,
    church_groupmember,
    church_staff,
    baptisms,
    funerals,
)


def open_church_form(church_id=None):
    root = tk.Tk() if church_id is None else tk.Toplevel()
    ChurchForm(root, church_id)
    root.geometry("1000x700")
    root.mainloop()


class ChurchForm:
    def __init__(self, master, church_id=None):
        self.master = master
        self.church_id = church_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.setup_ui()
        if church_id:
            self.load_data()

    def setup_ui(self):
        self.master.title("Church")
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill="both", expand=True)

        self.overview_tab = ttk.Frame(self.notebook)
        self.events_tab = ttk.Frame(self.notebook)
        self.groups_tab = ttk.Frame(self.notebook)
        self.staff_tab = ttk.Frame(self.notebook)
        self.baptisms_tab = ttk.Frame(self.notebook)
        self.funerals_tab = ttk.Frame(self.notebook)

        for tab, label in [
            (self.overview_tab, "Church Overview"),
            (self.events_tab, "Events"),
            (self.groups_tab, "Groups + Members"),
            (self.staff_tab, "Staff"),
            (self.baptisms_tab, "Baptisms"),
            (self.funerals_tab, "Funerals"),
        ]:
            self.notebook.add(tab, text=label)

        self.setup_overview()
        self.setup_events()
        self.setup_groups()
        self.setup_staff()
        self.setup_baptisms()
        self.setup_funerals()

    def setup_overview(self):
        fields = [
            ("Name", 40),
            ("Denomination", 30),
            ("Start Date", 20),
            ("End Date", 20),
            ("Notes", 50),
        ]
        self.entries = {}
        for row, (label, width) in enumerate(fields):
            ttk.Label(self.overview_tab, text=label + ":").grid(row=row, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(self.overview_tab, width=width)
            entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
            self.entries[label] = entry

        ttk.Button(self.overview_tab, text="Save", command=self.save_overview).grid(row=len(fields), column=0, columnspan=2, pady=10)

    def setup_events(self):
        self.event_tree = ttk.Treeview(self.events_tab, columns=("id", "type", "date", "desc"), show="headings")
        self.event_tree.heading("type", text="Type")
        self.event_tree.heading("date", text="Date")
        self.event_tree.heading("desc", text="Description")
        self.event_tree.column("id", width=0, stretch=False)
        self.event_tree.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(self.events_tab)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Add", command=self.add_event).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Edit", command=self.edit_event).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_event).pack(side="left", padx=2)

    def setup_groups(self):
        self.group_tree = ttk.Treeview(self.groups_tab, columns=("id", "name", "type"), show="headings")
        for col in ("name", "type"):
            self.group_tree.heading(col, text=col.title())
        self.group_tree.column("id", width=0, stretch=False)
        self.group_tree.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(self.groups_tab, text="Manage Members", command=self.manage_members).pack(pady=5)

    def setup_staff(self):
        self.staff_tree = ttk.Treeview(self.staff_tab, columns=("id", "person", "title"), show="headings")
        for col in ("person", "title"):
            self.staff_tree.heading(col, text=col.title())
        self.staff_tree.column("id", width=0, stretch=False)
        self.staff_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_baptisms(self):
        self.baptism_tree = ttk.Treeview(self.baptisms_tab, columns=("id", "person", "date"), show="headings")
        for col in ("person", "date"):
            self.baptism_tree.heading(col, text=col.title())
        self.baptism_tree.column("id", width=0, stretch=False)
        self.baptism_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_funerals(self):
        self.funeral_tree = ttk.Treeview(self.funerals_tab, columns=("id", "person", "date"), show="headings")
        for col in ("person", "date"):
            self.funeral_tree.heading(col, text=col.title())
        self.funeral_tree.column("id", width=0, stretch=False)
        self.funeral_tree.pack(fill="both", expand=True, padx=5, pady=5)

    # --- Data Loading ---
    def load_data(self):
        self.cursor.execute("SELECT church_name, denomination, start_date, start_date_precision, end_date, end_date_precision, notes FROM Church WHERE church_id=?", (self.church_id,))
        row = self.cursor.fetchone()
        if row:
            name, denom, sdate, sprec, edate, eprec, notes = row
            self.entries["Name"].insert(0, name or "")
            self.entries["Denomination"].insert(0, denom or "")
            self.entries["Start Date"].insert(0, format_date_for_display(sdate, sprec) if sdate else "")
            self.entries["End Date"].insert(0, format_date_for_display(edate, eprec) if edate else "")
            self.entries["Notes"].insert(0, notes or "")
        self.load_events()
        self.load_groups()
        self.load_staff()
        self.load_baptisms()
        self.load_funerals()

    # --- Overview Save ---
    def save_overview(self):
        name = self.entries["Name"].get().strip()
        denom = self.entries["Denomination"].get().strip()
        if not name or not denom:
            messagebox.showerror("Missing", "Name and denomination required")
            return
        start = self.entries["Start Date"].get().strip()
        end = self.entries["End Date"].get().strip()
        notes = self.entries["Notes"].get().strip()
        if self.church_id:
            self.cursor.execute(
                "UPDATE Church SET church_name=?, denomination=?, start_date=?, end_date=?, notes=? WHERE church_id=?",
                (name, denom, start or None, end or None, notes, self.church_id),
            )
        else:
            self.cursor.execute(
                "INSERT INTO Church (church_name, denomination, start_date, end_date, notes) VALUES (?, ?, ?, ?, ?)",
                (name, denom, start or None, end or None, notes),
            )
            self.church_id = self.cursor.lastrowid
        self.conn.commit()
        messagebox.showinfo("Saved", "Church record saved")

    # --- Event Methods ---
    def load_events(self):
        if not self.church_id:
            return
        self.event_tree.delete(*self.event_tree.get_children())
        self.cursor.execute(
            "SELECT church_event_id, event_type, event_date, event_date_precision, description FROM Church_Event WHERE church_id=? ORDER BY event_date",
            (self.church_id,),
        )
        for row in self.cursor.fetchall():
            eid, etype, date, prec, desc = row
            display = format_date_for_display(date, prec) if date else ""
            self.event_tree.insert("", "end", values=(eid, etype or "", display, desc or ""))

    def add_event(self):
        if not self.church_id:
            messagebox.showerror("Save First", "Save church before adding events")
            return
        church_event.edit_event(self.master, self.church_id, refresh=self.load_events)

    def edit_event(self):
        sel = self.event_tree.selection()
        if not sel:
            return
        event_id = self.event_tree.item(sel[0])["values"][0]
        church_event.edit_event(self.master, self.church_id, event_id=event_id, refresh=self.load_events)

    def delete_event(self):
        sel = self.event_tree.selection()
        if not sel:
            return
        event_id = self.event_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Delete", "Delete selected event?"):
            self.cursor.execute("DELETE FROM Church_Event WHERE church_event_id=?", (event_id,))
            self.conn.commit()
            self.load_events()

    # --- Group Methods ---
    def load_groups(self):
        if not self.church_id:
            return
        self.group_tree.delete(*self.group_tree.get_children())
        self.cursor.execute(
            "SELECT church_group_id, group_name, group_type FROM Church_Group WHERE church_id=? ORDER BY group_name",
            (self.church_id,),
        )
        for row in self.cursor.fetchall():
            gid, name, gtype = row
            self.group_tree.insert("", "end", values=(gid, name or "", gtype or ""))

    def manage_members(self):
        sel = self.group_tree.selection()
        if not sel:
            return
        group_id = self.group_tree.item(sel[0])["values"][0]
        church_groupmember.manage_members(self.master, group_id)

    # --- Staff Methods ---
    def load_staff(self):
        if not self.church_id:
            return
        self.staff_tree.delete(*self.staff_tree.get_children())
        self.cursor.execute(
            """SELECT s.church_staff_id, p.first_name || ' ' || p.last_name, s.title
               FROM Church_Staff s
               JOIN People p ON s.person_id = p.id
               WHERE s.church_id=?""",
            (self.church_id,),
        )
        for row in self.cursor.fetchall():
            sid, pname, title = row
            self.staff_tree.insert("", "end", values=(sid, pname, title or ""))

    # --- Baptisms ---
    def load_baptisms(self):
        if not self.church_id:
            return
        self.baptism_tree.delete(*self.baptism_tree.get_children())
        self.cursor.execute(
            """SELECT b.baptism_id, p.first_name || ' ' || p.last_name, b.baptism_date, b.officiant_id
               FROM Baptism b JOIN People p ON b.person_id=p.id
               WHERE b.church_id=?""",
            (self.church_id,),
        )
        for row in self.cursor.fetchall():
            bid, pname, date, _ = row
            self.baptism_tree.insert("", "end", values=(bid, pname, date or ""))

    # --- Funerals ---
    def load_funerals(self):
        if not self.church_id:
            return
        self.funeral_tree.delete(*self.funeral_tree.get_children())
        self.cursor.execute(
            """SELECT f.funeral_id, p.first_name || ' ' || p.last_name, f.funeral_date, f.officiant_id
               FROM Funeral f JOIN People p ON f.person_id=p.id
               WHERE f.church_id=?""",
            (self.church_id,),
        )
        for row in self.cursor.fetchall():
            fid, pname, date, _ = row
            self.funeral_tree.insert("", "end", values=(fid, pname, date or ""))
