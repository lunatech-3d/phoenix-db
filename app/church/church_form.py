import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import webbrowser
import urllib.parse

from app.config import DB_PATH
from app.date_utils import (
    format_date_for_display,
    parse_date_input,
    date_sort_key,
)

from . import (
    church_events,
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

        self.details_frame = ttk.LabelFrame(self.master, text="Church Details")
        self.details_frame.pack(fill="x", padx=10, pady=10)

        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill="both", expand=True)
        
        self.locations_tab = ttk.Frame(self.notebook)
        self.events_tab = ttk.Frame(self.notebook)
        self.groups_tab = ttk.Frame(self.notebook)
        self.staff_tab = ttk.Frame(self.notebook)
        self.baptisms_tab = ttk.Frame(self.notebook)
        self.funerals_tab = ttk.Frame(self.notebook)

        for tab, label in [
            (self.locations_tab, "Locations"),
            (self.events_tab, "Events"),
            (self.groups_tab, "Groups + Members"),
            (self.staff_tab, "Staff"),
            (self.baptisms_tab, "Baptisms"),
            (self.funerals_tab, "Funerals"),
        ]:
            self.notebook.add(tab, text=label)

        self.setup_details()
        self.setup_events()
        self.setup_locations()
        self.setup_groups()
        self.setup_staff()
        self.setup_baptisms()
        self.setup_funerals()

    def setup_details(self):
        rows = [
            ("Name", "Denomination"),
            ("Start Date", "End Date"),
            ("Notes", "URL"),
        ]
        self.entries = {}
        for r, pair in enumerate(rows):
            left, right = pair
            ttk.Label(self.details_frame, text=left + ":").grid(row=r, column=0, sticky="e", padx=5, pady=2)
            l_entry = ttk.Entry(self.details_frame, width=30)
            l_entry.grid(row=r, column=1, sticky="w", padx=5, pady=2)
            self.entries[left] = l_entry

            ttk.Label(self.details_frame, text=right + ":").grid(row=r, column=2, sticky="e", padx=5, pady=2)
            r_entry = ttk.Entry(self.details_frame, width=30)
            r_entry.grid(row=r, column=3, sticky="w", padx=5, pady=2)
            self.entries[right] = r_entry

        btn_frame = ttk.Frame(self.details_frame)
        btn_frame.grid(row=len(rows), column=0, columnspan=4, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save_overview).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Close", command=self.master.destroy).pack(side="left", padx=5)

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
        cols = ("id", "person", "title", "start", "end", "notes")
        self.staff_tree = ttk.Treeview(self.staff_tab, columns=cols, show="headings")
        headings = ["ID", "Person", "Title", "Start", "End", "Notes"]
        for col, h in zip(cols, headings):
            self.staff_tree.heading(col, text=h)
            width = 60 if col in ("start", "end") else 150
            self.staff_tree.column(col, width=width)
        self.staff_tree.column("id", width=0, stretch=False)
        self.staff_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_locations(self):
        cols = ("address", "start", "end", "notes", "url")
        self.location_tree = ttk.Treeview(self.locations_tab, columns=cols, show="headings", height=3)
        for col in cols:
            self.location_tree.heading(col, text=col.title(), command=lambda c=col: self.sort_location_tree_by_column(c))
            if col in ("start", "end"):
                self.location_tree.column(col, width=90)
            elif col == "address":
                self.location_tree.column(col, width=220)
            elif col == "url":
                self.location_tree.column(col, width=200)
            else:
                self.location_tree.column(col, width=180)
        self.location_tree.pack(side="top", fill="x", expand=False, padx=5)
        self.location_tree.bind("<Double-1>", self.on_location_double_click)

        loc_btns = ttk.Frame(self.locations_tab)
        loc_btns.pack(side="bottom", fill="x")
        ttk.Button(loc_btns, text="Add", command=self.add_location).pack(side="left", padx=5)
        ttk.Button(loc_btns, text="Edit", command=self.edit_location).pack(side="left", padx=5)
        ttk.Button(loc_btns, text="Delete", command=self.delete_location).pack(side="left", padx=5)

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
        self.load_locations()
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
            """SELECT s.church_staff_id,
                       p.first_name || ' ' || p.last_name,
                       s.title, s.start_date, s.start_date_precision,
                       s.end_date, s.end_date_precision, s.notes
               FROM Church_Staff s
               JOIN People p ON s.person_id = p.id
               WHERE s.church_id=?""",
            (self.church_id,),
        )
        for row in self.cursor.fetchall():
            (
                sid,
                pname,
                title,
                sdate,
                sprec,
                edate,
                eprec,
                notes,
            ) = row
            start_disp = format_date_for_display(sdate, sprec) if sdate else ""
            end_disp = format_date_for_display(edate, eprec) if edate else ""
            self.staff_tree.insert(
                "",
                "end",
                values=(sid, pname, title or "", start_disp, end_disp, notes or ""),
            )

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

    # --- Location Methods ---
    def load_locations(self):
        if not self.church_id:
            return
        self.location_tree.delete(*self.location_tree.get_children())
        self.cursor.execute(
            """SELECT a.address, l.start_date, l.start_date_precision,
                       l.end_date, l.end_date_precision, l.notes, l.url
                   FROM ChurchLocHistory l
                   JOIN Address a ON l.address_id = a.address_id
                   WHERE l.church_id=?""",
            (self.church_id,),
        )
        rows = self.cursor.fetchall()
        sorted_rows = sorted(rows, key=lambda r: date_sort_key(r[1]))
        for row in sorted_rows:
            address, sdate, sprec, edate, eprec, notes, url = row
            start_disp = format_date_for_display(sdate, sprec) if sdate else ""
            end_disp = format_date_for_display(edate, eprec) if edate else ""
            self.location_tree.insert(
                "",
                "end",
                values=(address, start_disp, end_disp, notes or "", url or ""),
            )

    def add_location(self):
        self.open_location_editor()

    def edit_location(self):
        sel = self.location_tree.selection()
        if not sel:
            return
        values = self.location_tree.item(sel[0])["values"]
        self.open_location_editor(existing=values)

    def open_location_editor(self, existing=None):
        self.location_win = tk.Toplevel(self.master)
        self.location_win.title("Edit Location" if existing else "Add Location")

        fields = ["Address", "Start Date", "End Date", "Notes", "URL"]
        self.location_entries = {}
        self.location_existing = existing

        for idx, label in enumerate(fields):
            ttk.Label(self.location_win, text=label + ":").grid(row=idx, column=0, padx=5, pady=3, sticky="e")

            if label == "Address":
                address_frame = ttk.Frame(self.location_win)
                address_frame.grid(row=idx, column=1, padx=5, pady=3, sticky="w")

                search_var = tk.StringVar(master=self.location_win)
                search_entry = ttk.Entry(address_frame, textvariable=search_var, width=30)
                search_entry.pack(side="left", padx=(0, 5))

                self.cursor.execute("SELECT address_id, address FROM Address ORDER BY address")
                address_rows = self.cursor.fetchall()
                address_list = [row[1] for row in address_rows]
                self.address_lookup = {row[1]: row[0] for row in address_rows}

                address_combo = ttk.Combobox(address_frame, width=40, state="readonly")
                address_combo['values'] = address_list
                address_combo.pack(side="left")
                self.location_entries["Address"] = address_combo

                def filter_addresses():
                    term = search_var.get().lower()
                    filtered = [a for a in address_list if term in a.lower()]
                    address_combo['values'] = filtered

                ttk.Button(address_frame, text="Search", command=filter_addresses).pack(side="left", padx=(5, 0))
            else:
                entry = ttk.Entry(self.location_win, width=50)
                entry.grid(row=idx, column=1, padx=5, pady=3)
                self.location_entries[label] = entry

        if existing:
            for key, value in zip(fields, existing):
                widget = self.location_entries.get(key)
                if not widget:
                    continue
                if isinstance(widget, ttk.Combobox):
                    widget.set(value)
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, value)

        def save_location():
            address_widget = self.location_entries.get("Address")
            if not address_widget:
                messagebox.showerror("Error", "Address field is missing.")
                return

            address = address_widget.get().strip()
            if address not in address_widget['values']:
                messagebox.showerror("Invalid Address", "The address you selected is not in the database.")
                return

            address_id = self.address_lookup.get(address)
            if not address_id:
                messagebox.showerror("Invalid Address", "The address is not recognized.")
                return

            try:
                start_input = self.location_entries["Start Date"].get().strip()
                start_date, start_prec = parse_date_input(start_input) if start_input else (None, None)

                end_input = self.location_entries["End Date"].get().strip()
                end_date, end_prec = parse_date_input(end_input) if end_input else (None, None)
            except ValueError as e:
                messagebox.showerror("Date Error", str(e))
                return

            notes = self.location_entries["Notes"].get().strip()
            url = self.location_entries["URL"].get().strip()

            try:
                if self.location_existing:
                    original_address = self.location_existing[0]
                    self.cursor.execute(
                        "SELECT address_id FROM Address WHERE address = ? LIMIT 1",
                        (original_address,),
                    )
                    result = self.cursor.fetchone()
                    if not result:
                        messagebox.showerror("Error", "Original address not found.")
                        return
                    original_address_id = result[0]
                    original_display_start = self.location_existing[1]
                    original_start_date, _ = parse_date_input(original_display_start)

                    self.cursor.execute(
                        """UPDATE ChurchLocHistory
                           SET address_id = ?,
                               start_date = ?, start_date_precision = ?,
                               end_date = ?, end_date_precision = ?,
                               notes = ?, url = ?
                         WHERE church_id = ? AND address_id = ?""",
                        (
                            address_id,
                            start_date,
                            start_prec,
                            end_date,
                            end_prec,
                            notes,
                            url,
                            self.church_id,
                            original_address_id,
                        ),
                    )
                else:
                    self.cursor.execute(
                        """INSERT INTO ChurchLocHistory (
                                church_id, address_id,
                                start_date, start_date_precision,
                                end_date, end_date_precision,
                                notes, url
                           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            self.church_id,
                            address_id,
                            start_date,
                            start_prec,
                            end_date,
                            end_prec,
                            notes,
                            url,
                        ),
                    )

                self.conn.commit()
                self.load_locations()
                self.location_win.destroy()

            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This location record already exists.")

        btn_frame = ttk.Frame(self.location_win)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=save_location).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.location_win.destroy).pack(side="left", padx=10)

    def delete_location(self):
        selected = self.location_tree.selection()
        if not selected:
            return

        confirm = messagebox.askyesno("Delete", "Delete selected location record?")
        if confirm:
            values = self.location_tree.item(selected[0])["values"]
            address = values[0]
            raw_start_date = values[1]

            try:
                parsed_start_date, _ = parse_date_input(raw_start_date)
            except ValueError:
                messagebox.showerror("Date Error", f"Could not parse start date: {raw_start_date}")
                return

            if parsed_start_date:
                query = """DELETE FROM ChurchLocHistory
                            WHERE church_id = ?
                              AND start_date = ?
                              AND address_id = (
                                  SELECT address_id FROM Address WHERE address = ? LIMIT 1
                              )"""
                params = (self.church_id, parsed_start_date, address)
            else:
                query = """DELETE FROM ChurchLocHistory
                            WHERE church_id = ?
                              AND start_date IS NULL
                              AND address_id = (
                                  SELECT address_id FROM Address WHERE address = ? LIMIT 1
                              )"""
                params = (self.church_id, address)

            self.cursor.execute(query, params)
            self.conn.commit()
            self.load_locations()

    def sort_location_tree_by_column(self, col):
        if not hasattr(self, "_location_sort_state"):
            self._location_sort_state = {}

        reverse = self._location_sort_state.get(col, False)
        items = [(self.location_tree.set(k, col), k) for k in self.location_tree.get_children("")]

        if col.lower() in ("start", "end", "start date", "end date"):
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)

        for index, (_, k) in enumerate(items):
            self.location_tree.move(k, "", index)

        self._location_sort_state[col] = not reverse

    def on_location_double_click(self, event):
        region = self.location_tree.identify("region", event.x, event.y)
        column = self.location_tree.identify_column(event.x)

        if region != "cell":
            return

        selected = self.location_tree.selection()
        if not selected:
            return

        values = self.location_tree.item(selected[0])["values"]
        address = values[0]
        url = values[4]

        if column == "#1":
            if address:
                query = urllib.parse.quote(address)
                map_url = f"https://www.google.com/maps/search/?api=1&query={query}"
                webbrowser.open(map_url, new=2)
            else:
                messagebox.showinfo("No Address", "No address provided.")
        elif column == "#5":
            if url and url.startswith("http"):
                webbrowser.open(url, new=2)
            else:
                messagebox.showinfo("No URL", "No valid link provided.")