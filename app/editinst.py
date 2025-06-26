import subprocess
import sqlite3
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

from app.config import DB_PATH
from app.date_utils import parse_date_input, format_date_for_display, date_sort_key
from app.context_menu import create_context_menu, apply_context_menu_to_all_entries
from app.person_linkage import person_search_popup


class StaffForm:
    def __init__(self, master, inst_id, staff_id=None, person_id=None):
        self.master = master
        self.inst_id = inst_id
        self.staff_id = staff_id
        self.person_id = person_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.entries = {}
        self.setup_form()
        if staff_id:
            self.load_data()
        elif person_id:
            self.set_person_id(person_id)

    def setup_form(self):
        row = 0
        ttk.Label(self.master, text="Selected Person:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        pframe = ttk.Frame(self.master)
        pframe.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        self.person_display = ttk.Label(pframe, text="(none)", width=40, relief="sunken", anchor="w")
        self.person_display.pack(side="left", padx=(0, 5))
        ttk.Button(pframe, text="Search", command=lambda: person_search_popup(self.set_person_id)).pack(side="left")
        ttk.Button(pframe, text="Clear", command=lambda: self.set_person_id(None)).pack(side="left")
        row += 1
        for label in ["Title", "Start Date", "End Date", "Notes"]:
            ttk.Label(self.master, text=label + ":").grid(row=row, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(self.master, width=40)
            entry.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
            self.entries[label] = entry
            create_context_menu(entry)
            row += 1
        btn_frame = ttk.Frame(self.master)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)
        apply_context_menu_to_all_entries(self.master)

    def set_person_id(self, pid):
        if pid is None:
            self.person_display.config(text="(none)")
            self.person_id = None
            return
        self.cursor.execute(
            "SELECT first_name, middle_name, last_name, married_name FROM People WHERE id=?",
            (pid,),
        )
        row = self.cursor.fetchone()
        if row:
            name_parts = [row[0], row[1], row[2]]
            name = " ".join(part for part in name_parts if part)
            if row[3]:
                name += f" ({row[3]})"
            self.person_display.config(text=name)
            self.person_id = pid
        else:
            self.person_display.config(text="(not found)")
            self.person_id = None

    def load_data(self):
        self.cursor.execute(
            """SELECT person_id, title, start_date, start_date_precision, end_date, end_date_precision, notes
               FROM Inst_Staff WHERE inst_staff_id=?""",
            (self.staff_id,)
        )
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Staff record not found.")
            self.master.destroy()
            return
        pid, title, sdate, sprec, edate, eprec, notes = row
        self.set_person_id(pid)
        self.entries["Title"].insert(0, title or "")
        self.entries["Start Date"].insert(0, format_date_for_display(sdate, sprec) if sdate else "")
        self.entries["End Date"].insert(0, format_date_for_display(edate, eprec) if edate else "")
        self.entries["Notes"].insert(0, notes or "")

    def save(self):
        try:
            start_raw = self.entries["Start Date"].get().strip()
            end_raw = self.entries["End Date"].get().strip()
            start_date, start_prec = parse_date_input(start_raw) if start_raw else (None, None)
            end_date, end_prec = parse_date_input(end_raw) if end_raw else (None, None)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e))
            return
        pid = self.person_id
        title = self.entries["Title"].get().strip()
        notes = self.entries["Notes"].get().strip()
        if not pid:
            messagebox.showerror("Missing", "Please select a person")
            return
        if self.staff_id:
            self.cursor.execute(
                """UPDATE Inst_Staff SET person_id=?, title=?, start_date=?, start_date_precision=?,
                       end_date=?, end_date_precision=?, notes=? WHERE inst_staff_id=?""",
                (pid, title, start_date, start_prec, end_date, end_prec, notes, self.staff_id),
            )
        else:
            self.cursor.execute(
                """INSERT INTO Inst_Staff (inst_id, person_id, title, start_date, start_date_precision,
                       end_date, end_date_precision, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.inst_id, pid, title, start_date, start_prec, end_date, end_prec, notes),
            )
        self.conn.commit()
        self.master.destroy()


def open_staff_editor(inst_id, staff_id=None, parent=None, person_id=None):
    if parent is None:
        root = tk.Tk()
        StaffForm(root, inst_id, staff_id=staff_id, person_id=person_id)
        root.geometry("500x250")
        root.mainloop()
    else:
        win = tk.Toplevel(parent)
        StaffForm(win, inst_id, staff_id=staff_id, person_id=person_id)
        win.grab_set()
        return win


class MemberForm:
    def __init__(self, master, inst_id, member_id=None, person_id=None):
        self.master = master
        self.inst_id = inst_id
        self.member_id = member_id
        self.person_id = person_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.entries = {}
        self.setup_form()
        if member_id:
            self.load_data()

    def setup_form(self):
        row = 0
        ttk.Label(self.master, text="Group Name:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        g_entry = ttk.Entry(self.master, width=30)
        g_entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        self.entries["Group Name"] = g_entry
        create_context_menu(g_entry)
        row += 1

        ttk.Label(self.master, text="Person ID:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        pid_entry = ttk.Entry(self.master, width=30)
        pid_entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        self.entries["Person ID"] = pid_entry
        create_context_menu(pid_entry)
        ttk.Button(self.master, text="Lookup", command=lambda: person_search_popup(self.set_person_id)).grid(row=row, column=2, padx=5)
        row += 1

        for label in ["Role", "Start Date", "End Date", "Notes"]:
            ttk.Label(self.master, text=label + ":").grid(row=row, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(self.master, width=40)
            entry.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
            self.entries[label] = entry
            create_context_menu(entry)
            row += 1

        btn_frame = ttk.Frame(self.master)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)
        apply_context_menu_to_all_entries(self.master)

    def set_person_id(self, pid):
        self.entries["Person ID"].delete(0, tk.END)
        self.entries["Person ID"].insert(0, pid)
        self.person_id = pid

    def load_data(self):
        self.cursor.execute(
            """SELECT g.group_name, m.person_id, m.role, m.start_date, m.end_date, m.notes
               FROM Inst_GroupMember m JOIN Inst_Group g ON m.inst_group_id = g.inst_group_id
               WHERE m.inst_group_member_id=?""",
            (self.member_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Membership record not found.")
            self.master.destroy()
            return
        gname, pid, role, sdate, edate, notes = row
        self.entries["Group Name"].insert(0, gname or "")
        self.set_person_id(pid)
        self.entries["Role"].insert(0, role or "")
        self.entries["Start Date"].insert(0, sdate or "")
        self.entries["End Date"].insert(0, edate or "")
        self.entries["Notes"].insert(0, notes or "")

    def save(self):
        try:
            s_raw = self.entries["Start Date"].get().strip()
            e_raw = self.entries["End Date"].get().strip()
            sdate, _ = parse_date_input(s_raw) if s_raw else ("", None)
            edate, _ = parse_date_input(e_raw) if e_raw else ("", None)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e))
            return

        group_name = self.entries["Group Name"].get().strip()
        pid = self.entries["Person ID"].get().strip()
        role = self.entries["Role"].get().strip()
        notes = self.entries["Notes"].get().strip()

        if not group_name or not pid:
            messagebox.showerror("Missing", "Group name and person ID are required")
            return

        self.cursor.execute(
            "SELECT inst_group_id FROM Inst_Group WHERE inst_id=? AND group_name=?",
            (self.inst_id, group_name),
        )
        res = self.cursor.fetchone()
        if res:
            group_id = res[0]
        else:
            self.cursor.execute(
                "INSERT INTO Inst_Group (inst_id, group_name) VALUES (?, ?)",
                (self.inst_id, group_name),
            )
            group_id = self.cursor.lastrowid

        if self.member_id:
            self.cursor.execute(
                """UPDATE Inst_GroupMember SET inst_group_id=?, person_id=?, role=?, start_date=?, end_date=?, notes=?
                   WHERE inst_group_member_id=?""",
                (group_id, pid, role, sdate, edate, notes, self.member_id),
            )
        else:
            self.cursor.execute(
                """INSERT INTO Inst_GroupMember (inst_group_id, person_id, role, start_date, end_date, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (group_id, pid, role, sdate, edate, notes),
            )
        self.conn.commit()
        self.master.destroy()


def open_member_editor(inst_id, member_id=None, parent=None, person_id=None):
    if parent is None:
        root = tk.Tk()
        MemberForm(root, inst_id, member_id=member_id, person_id=person_id)
        root.geometry("600x300")
        root.mainloop()
    else:
        win = tk.Toplevel(parent)
        MemberForm(win, inst_id, member_id=member_id, person_id=person_id)
        win.grab_set()
        return win


class EventForm:
    def __init__(self, master, inst_id, event_id=None):
        self.master = master
        self.inst_id = inst_id
        self.event_id = event_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.entries = {}
        self.setup_form()
        if event_id:
            self.load_data()

    def setup_form(self):
        labels = ["Event Type", "Start Date", "End Date", "Description", "Link URL"]
        row = 0
        for label in labels:
            ttk.Label(self.master, text=label + ":").grid(row=row, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(self.master, width=50)
            entry.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
            self.entries[label] = entry
            create_context_menu(entry)
            row += 1

        ttk.Label(self.master, text="Person ID:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
        pid_entry = ttk.Entry(self.master, width=30)
        pid_entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        self.entries["Person ID"] = pid_entry
        create_context_menu(pid_entry)
        ttk.Button(self.master, text="Lookup", command=lambda: person_search_popup(self.set_person_id)).grid(row=row, column=2, padx=5)
        row += 1

        ttk.Label(self.master, text="Original Text:").grid(row=row, column=0, sticky="ne", padx=5, pady=5)
        otext = tk.Text(self.master, width=50, height=6)
        otext.grid(row=row, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        self.entries["Original Text"] = otext
        create_context_menu(otext)
        row += 1

        btn_frame = ttk.Frame(self.master)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.master.destroy).pack(side="left", padx=5)
        apply_context_menu_to_all_entries(self.master)

    def set_person_id(self, pid):
        self.entries["Person ID"].delete(0, tk.END)
        self.entries["Person ID"].insert(0, pid)

    def load_data(self):
        self.cursor.execute(
            """SELECT event_type, event_date, event_date_precision, end_date, end_date_precision,
               description, original_text, person_id, link_url
               FROM Inst_Event WHERE inst_event_id=?""",
            (self.event_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Event record not found.")
            self.master.destroy()
            return
        etype, sdate, sprec, edate, eprec, desc, original_text, pid, link = row
        self.entries["Event Type"].insert(0, etype or "")
        self.entries["Start Date"].insert(0, format_date_for_display(sdate, sprec) if sdate else "")
        self.entries["End Date"].insert(0, format_date_for_display(edate, eprec) if edate else "")
        self.entries["Description"].insert(0, desc or "")
        self.entries["Original Text"].insert("1.0", original_text or "")
        self.entries["Link URL"].insert(0, link or "")
        if pid:
            self.set_person_id(pid)

    def save(self):
        try:
            s_raw = self.entries["Start Date"].get().strip()
            e_raw = self.entries["End Date"].get().strip()
            sdate, sprec = parse_date_input(s_raw) if s_raw else (None, None)
            edate, eprec = parse_date_input(e_raw) if e_raw else (None, None)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e))
            return

        data = [
            self.entries["Event Type"].get().strip(),
            sdate, sprec,
            edate, eprec,
            self.entries["Description"].get().strip(),
            self.entries["Original Text"].get("1.0", tk.END).strip(),
            self.entries["Person ID"].get().strip() or None,
            self.entries["Link URL"].get().strip(),
        ]

        if self.event_id:
            self.cursor.execute(
                """UPDATE Inst_Event SET event_type=?, event_date=?, event_date_precision=?, end_date=?, end_date_precision=?, description=?, original_text=?, person_id=?, link_url=? WHERE inst_event_id=?""",
                data + [self.event_id],
            )
        else:
            self.cursor.execute(
                """INSERT INTO Inst_Event (inst_id, event_type, event_date, event_date_precision, end_date, end_date_precision, description, original_text, person_id, link_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [self.inst_id] + data,
            )
        self.conn.commit()
        self.master.destroy()


def open_event_editor(inst_id, event_id=None, parent=None):
    if parent is None:
        root = tk.Tk()
        EventForm(root, inst_id, event_id=event_id)
        root.geometry("700x400")
        root.mainloop()
    else:
        win = tk.Toplevel(parent)
        EventForm(win, inst_id, event_id=event_id)
        win.grab_set()
        return win


class EditInstitutionForm:
    def __init__(self, master, inst_id=None):
        self.master = master
        self.inst_id = inst_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.entries = {}
        self.setup_form()
        if inst_id:
            self.load_data()
            self.load_staff()
            self.load_members()
            self.load_events()
        else:
            self.disable_related()

    def setup_form(self):
        form = ttk.LabelFrame(self.master, text="Institution Details")
        form.pack(fill="x", padx=10, pady=10)

        rows = [
            ("Name", "Type"),
            ("Start Date", "End Date"),
            ("Notes", "URL"),
        ]
        for r, pair in enumerate(rows):
            left, right = pair
            ttk.Label(form, text=left + ":").grid(row=r, column=0, sticky="e", padx=5, pady=2)
            l_entry = ttk.Entry(form, width=30)
            l_entry.grid(row=r, column=1, sticky="w", padx=5, pady=2)
            self.entries[left] = l_entry
            create_context_menu(l_entry)

            ttk.Label(form, text=right + ":").grid(row=r, column=2, sticky="e", padx=5, pady=2)
            r_entry = ttk.Entry(form, width=30)
            r_entry.grid(row=r, column=3, sticky="w", padx=5, pady=2)
            self.entries[right] = r_entry
            create_context_menu(r_entry)

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=len(rows), column=0, columnspan=4, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Close", command=self.master.destroy).pack(side="left", padx=5)

        self.staff_frame = ttk.LabelFrame(self.master, text="Staff")
        self.staff_frame.pack(fill="both", expand=False, padx=10, pady=5)
        self.staff_tree = ttk.Treeview(
            self.staff_frame,
            columns=("id", "person", "title", "start", "end", "notes"),
            show="headings",
            height=5,
        )
        headings = ["ID", "Person", "Title", "Start", "End", "Notes"]
        for col, h in zip(self.staff_tree["columns"], headings):
            self.staff_tree.heading(col, text=h, command=lambda c=col: self.sort_staff(c))
            width = 50 if col in ("start", "end") else 150
            self.staff_tree.column(col, width=width)
        self.staff_tree.column("id", width=0, stretch=False)
        self.staff_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.staff_tree.bind("<Double-1>", self.on_staff_double)
        btns = ttk.Frame(self.staff_frame)
        btns.pack(fill="x")
        ttk.Button(btns, text="Add", command=self.add_staff).pack(side="left", padx=5)
        ttk.Button(btns, text="Edit", command=self.edit_staff).pack(side="left", padx=5)
        ttk.Button(btns, text="Delete", command=self.delete_staff).pack(side="left", padx=5)

        self.member_frame = ttk.LabelFrame(self.master, text="Members")
        self.member_frame.pack(fill="both", expand=False, padx=10, pady=5)
        self.member_tree = ttk.Treeview(
            self.member_frame,
            columns=("id", "group", "person", "role", "start", "end", "notes"),
            show="headings",
            height=5,
        )
        headings = ["ID", "Group", "Person", "Role", "Start", "End", "Notes"]
        for col, h in zip(self.member_tree["columns"], headings):
            self.member_tree.heading(col, text=h, command=lambda c=col: self.sort_members(c))
            width = 60 if col in ("start", "end") else 150
            self.member_tree.column(col, width=width)
        self.member_tree.column("id", width=0, stretch=False)
        self.member_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.member_tree.bind("<Double-1>", self.on_member_double)
        mb = ttk.Frame(self.member_frame)
        mb.pack(fill="x")
        ttk.Button(mb, text="Add", command=self.add_member).pack(side="left", padx=5)
        ttk.Button(mb, text="Edit", command=self.edit_member).pack(side="left", padx=5)
        ttk.Button(mb, text="Delete", command=self.delete_member).pack(side="left", padx=5)

        self.event_frame = ttk.LabelFrame(self.master, text="Events")
        self.event_frame.pack(fill="both", expand=False, padx=10, pady=5)
        self.event_tree = ttk.Treeview(
            self.event_frame,
            columns=("id", "type", "dates", "person", "description", "link"),
            show="headings",
            height=5,
        )
        headings = ["ID", "Type", "Date(s)", "Person", "Description", "Link"]
        for col, h in zip(self.event_tree["columns"], headings):
            self.event_tree.heading(col, text=h, command=lambda c=col: self.sort_events(c))
            if col == "description":
                width = 250
            elif col in ("dates", "person", "link"):
                width = 120
            else:
                width = 80
            self.event_tree.column(col, width=width)
        self.event_tree.column("id", width=0, stretch=False)
        self.event_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.event_tree.bind("<Double-1>", self.on_event_double)
        eb = ttk.Frame(self.event_frame)
        eb.pack(fill="x")
        ttk.Button(eb, text="Add", command=self.add_event).pack(side="left", padx=5)
        ttk.Button(eb, text="Edit", command=self.edit_event).pack(side="left", padx=5)
        ttk.Button(eb, text="Delete", command=self.delete_event).pack(side="left", padx=5)
        apply_context_menu_to_all_entries(self.master)

    def disable_related(self):
        widgets = (
            [self.staff_tree] + list(self.staff_frame.children.values()) +
            [self.member_tree] + list(self.member_frame.children.values()) +
            [self.event_tree] + list(self.event_frame.children.values())
        )
        for w in widgets:
            try:
                w.state(["disabled"])
            except tk.TclError:
                w.config(state="disabled")

    def enable_related(self):
        widgets = (
            [self.staff_tree] + list(self.staff_frame.children.values()) +
            [self.member_tree] + list(self.member_frame.children.values()) +
            [self.event_tree] + list(self.event_frame.children.values())
        )
        for w in widgets:
            try:
                w.state(["!disabled"])
            except tk.TclError:
                w.config(state="normal")

    def load_data(self):
        self.cursor.execute(
            "SELECT inst_name, inst_type, start_date, start_date_precision, end_date, end_date_precision, notes, url FROM Institution WHERE inst_id=?",
            (self.inst_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Institution not found.")
            self.master.destroy()
            return
        name, typ, sdate, sprec, edate, eprec, notes, url = row
        values = [name, typ, format_date_for_display(sdate, sprec) if sdate else "", format_date_for_display(edate, eprec) if edate else "", notes, url]
        for key, val in zip(["Name", "Type", "Start Date", "End Date", "Notes", "URL"], values):
            self.entries[key].insert(0, val or "")

    def save(self):
        try:
            sdate, sprec = parse_date_input(self.entries["Start Date"].get().strip())
            e_raw = self.entries["End Date"].get().strip()
            edate, eprec = parse_date_input(e_raw) if e_raw else (None, None)
        except ValueError as e:
            messagebox.showerror("Date Error", str(e))
            return
        data = [
            self.entries["Name"].get().strip(),
            self.entries["Type"].get().strip(),
            sdate,
            sprec,
            edate,
            eprec,
            self.entries["Notes"].get().strip(),
            self.entries["URL"].get().strip(),
        ]
        if not data[0]:
            messagebox.showerror("Missing", "Name is required")
            return
        if self.inst_id:
            self.cursor.execute(
                """UPDATE Institution SET inst_name=?, inst_type=?, start_date=?, start_date_precision=?, end_date=?, end_date_precision=?, notes=?, url=? WHERE inst_id=?""",
                data + [self.inst_id],
            )
        else:
            self.cursor.execute(
                """INSERT INTO Institution (inst_name, inst_type, start_date, start_date_precision, end_date, end_date_precision, notes, url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                data,
            )
            self.inst_id = self.cursor.lastrowid
            self.enable_related()
        self.conn.commit()
        messagebox.showinfo("Saved", "Institution saved", parent=self.master)

    def load_staff(self):
        self.staff_tree.delete(*self.staff_tree.get_children())
        self.cursor.execute(
            """SELECT s.inst_staff_id, s.person_id,
                       p.first_name || ' ' || IFNULL(p.middle_name||' ', '') || p.last_name ||
                       CASE WHEN p.married_name IS NOT NULL AND p.married_name!='' THEN ' ('||p.married_name||')' ELSE '' END,
                       s.title, s.start_date, s.start_date_precision,
                       s.end_date, s.end_date_precision, s.notes
               FROM Inst_Staff s JOIN People p ON s.person_id = p.id
               WHERE s.inst_id=?""",
            (self.inst_id,),
        )
        rows = self.cursor.fetchall()
        for row in rows:
            staff_id, pid, name, title, sd, sp, ed, ep, notes = row
            start = format_date_for_display(sd, sp) if sd else ""
            end = format_date_for_display(ed, ep) if ed else ""
            self.staff_tree.insert("", "end", values=(staff_id, name, title, start, end, notes), tags=(pid,))

    def get_selected_staff(self):
        sel = self.staff_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a staff record")
            return None
        item = self.staff_tree.item(sel[0])
        values = item["values"]
        pid = self.staff_tree.item(sel[0], "tags")[0]
        return sel[0], values, pid

    def add_staff(self):
        win = open_staff_editor(self.inst_id, parent=self.master)
        if win:
            self.master.wait_window(win)
            self.load_staff()

    def edit_staff(self):
        res = self.get_selected_staff()
        if not res:
            return
        item_id, values, pid = res
        staff_id = values[0]
        win = open_staff_editor(self.inst_id, staff_id=staff_id, parent=self.master)
        if win:
            self.master.wait_window(win)
            self.load_staff()

    def delete_staff(self):
        res = self.get_selected_staff()
        if not res:
            return
        _, values, _ = res
        staff_id = values[0]
        if messagebox.askyesno("Delete", "Delete selected staff?"):
            self.cursor.execute("DELETE FROM Inst_Staff WHERE inst_staff_id=?", (staff_id,))
            self.conn.commit()
            self.load_staff()

    def on_staff_double(self, event):
        sel = self.staff_tree.selection()
        if not sel:
            return
        pid = self.staff_tree.item(sel[0], "tags")[0]
        subprocess.Popen([sys.executable, "-m", "app.editme", str(pid)])

    def sort_staff(self, col):
        if not hasattr(self, "_staff_sort"):
            self._staff_sort = {}
        reverse = self._staff_sort.get(col, False)
        items = [(self.staff_tree.set(k, col), k) for k in self.staff_tree.get_children("")]
        if col in ("start", "end"):
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0],
                       reverse=reverse)
        for idx, (_, k) in enumerate(items):
            self.staff_tree.move(k, "", idx)
        self._staff_sort[col] = not reverse

    # --- Member Section ---
    def load_members(self):
        self.member_tree.delete(*self.member_tree.get_children())
        self.cursor.execute(
            """SELECT m.inst_group_member_id, g.group_name, m.person_id,
                       p.first_name || ' ' || IFNULL(p.middle_name||' ', '') || p.last_name ||
                       CASE WHEN p.married_name IS NOT NULL AND p.married_name!='' THEN ' ('||p.married_name||')' ELSE '' END,
                       m.role, m.start_date, m.end_date, m.notes
               FROM Inst_GroupMember m
               JOIN Inst_Group g ON m.inst_group_id = g.inst_group_id
               JOIN People p ON m.person_id = p.id
               WHERE g.inst_id=?""",
            (self.inst_id,),
        )
        for row in self.cursor.fetchall():
            mid, gname, pid, pname, role, sd, ed, notes = row
            self.member_tree.insert("", "end", values=(mid, gname, pname, role, sd or "", ed or "", notes or ""), tags=(pid,))

    def get_selected_member(self):
        sel = self.member_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a member record")
            return None
        item = self.member_tree.item(sel[0])
        pid = self.member_tree.item(sel[0], "tags")[0]
        return sel[0], item["values"], pid

    def add_member(self):
        win = open_member_editor(self.inst_id, parent=self.master)
        if win:
            self.master.wait_window(win)
            self.load_members()

    def edit_member(self):
        res = self.get_selected_member()
        if not res:
            return
        _, values, _ = res
        mem_id = values[0]
        win = open_member_editor(self.inst_id, member_id=mem_id, parent=self.master)
        if win:
            self.master.wait_window(win)
            self.load_members()

    def delete_member(self):
        res = self.get_selected_member()
        if not res:
            return
        _, values, _ = res
        mem_id = values[0]
        if messagebox.askyesno("Delete", "Delete selected member?"):
            self.cursor.execute("DELETE FROM Inst_GroupMember WHERE inst_group_member_id=?", (mem_id,))
            self.conn.commit()
            self.load_members()

    def on_member_double(self, event):
        sel = self.member_tree.selection()
        if not sel:
            return
        pid = self.member_tree.item(sel[0], "tags")[0]
        subprocess.Popen([sys.executable, "-m", "app.editme", str(pid)])

    def sort_members(self, col):
        if not hasattr(self, "_member_sort"):
            self._member_sort = {}
        reverse = self._member_sort.get(col, False)
        items = [(self.member_tree.set(k, col), k) for k in self.member_tree.get_children("")]
        if col in ("start", "end"):
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)
        for idx, (_, k) in enumerate(items):
            self.member_tree.move(k, "", idx)
        self._member_sort[col] = not reverse

    # --- Event Section ---
    def load_events(self):
        self.event_tree.delete(*self.event_tree.get_children())
        self.cursor.execute(
            """SELECT e.inst_event_id, e.event_type, e.event_date, e.event_date_precision,
                       e.end_date, e.end_date_precision, e.description, e.person_id,
                       e.link_url,
                       p.first_name || ' ' || IFNULL(p.middle_name||' ', '') || p.last_name ||
                       CASE WHEN p.married_name IS NOT NULL AND p.married_name!='' THEN ' ('||p.married_name||')' ELSE '' END
               FROM Inst_Event e
               LEFT JOIN People p ON e.person_id = p.id
               WHERE e.inst_id=?
               ORDER BY e.event_date""",
            (self.inst_id,),
        )
        for row in self.cursor.fetchall():
            (eid, etype, sd, sp, ed, ep, desc, pid, link, pname) = row
            start = format_date_for_display(sd, sp) if sd else ""
            end = format_date_for_display(ed, ep) if ed else ""
            dates = start if not end else f"{start} – {end}"
            self.event_tree.insert("", "end", values=(eid, etype, dates, pname or "", desc or "", link or ""), tags=(pid or "",))

    def get_selected_event(self):
        sel = self.event_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an event")
            return None
        item = self.event_tree.item(sel[0])
        pid = self.event_tree.item(sel[0], "tags")[0]
        return sel[0], item["values"], pid

    def add_event(self):
        win = open_event_editor(self.inst_id, parent=self.master)
        if win:
            self.master.wait_window(win)
            self.load_events()

    def edit_event(self):
        res = self.get_selected_event()
        if not res:
            return
        _, values, _ = res
        eid = values[0]
        win = open_event_editor(self.inst_id, event_id=eid, parent=self.master)
        if win:
            self.master.wait_window(win)
            self.load_events()

    def delete_event(self):
        res = self.get_selected_event()
        if not res:
            return
        _, values, _ = res
        eid = values[0]
        if messagebox.askyesno("Delete", "Delete selected event?"):
            self.cursor.execute("DELETE FROM Inst_Event WHERE inst_event_id=?", (eid,))
            self.conn.commit()
            self.load_events()

    def on_event_double(self, event):
        sel = self.event_tree.selection()
        if not sel:
            return
        column = self.event_tree.identify_column(event.x)
        values = self.event_tree.item(sel[0])["values"]
        pid = self.event_tree.item(sel[0], "tags")[0]
        if column == "#4" and pid:
            subprocess.Popen([sys.executable, "-m", "app.editme", str(pid)])
        elif column == "#6":
            url = values[5]
            if url and url.startswith("http"):
                webbrowser.open(url, new=2)

        def sort_events(self, col):
            if not hasattr(self, "_event_sort"):
                self._event_sort = {}
            reverse = self._event_sort.get(col, False)

            items = [(self.event_tree.set(k, col), k) for k in self.event_tree.get_children("")]   
            if col == "dates":
                items.sort(key=lambda item: date_sort_key(item[0].split("–")[0].strip()), reverse=reverse)
            else:
                items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)
            for idx, (_, k) in enumerate(items):
                self.event_tree.move(k, "", idx)
            self._event_sort[col] = not reverse


def open_edit_institution_form(inst_id=None):
    win = tk.Tk() if inst_id is None else tk.Toplevel()
    win.geometry("1200x800")
    EditInstitutionForm(win, inst_id)
    win.grab_set()


if __name__ == "__main__":
    arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    root = tk.Tk()
    EditInstitutionForm(root, arg)
    root.geometry("1200x800")
    root.mainloop()