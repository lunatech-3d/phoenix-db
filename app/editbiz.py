# editbiz.py
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sqlite3
import webbrowser
import urllib.parse
import sys

#Local Imports
from app.config import PATHS, DB_PATH
from app.date_utils import parse_date_input, format_date_for_display, date_sort_key
from app.context_menu import create_context_menu, apply_context_menu_to_all_entries
from app.person_linkage import person_search_popup
from app.biz_employees import open_employee_editor
from app.movie.edit_showing import open_edit_showing_form
from app.biz_linkage import open_biz_linkage_popup

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

PRECEDED_BY_TYPES = [
    "Predecessor", "Merged Into", "Rebranded From", "Split From", "Acquired"
]

SUCCEEDED_BY_TYPES = [
    "Successor", "Merged Into", "Rebranded As", "Split Into", "Acquired By"
]

RELATIONSHIP_INVERSION = {
    "Successor": "Predecessor",
    "Predecessor": "Successor",
    "Rebranded As": "Rebranded From",
    "Rebranded From": "Rebranded As",
    "Acquired": "Acquired By",
    "Acquired By": "Acquired",
    "Split Into": "Split From",
    "Split From": "Split Into",
    "Merged Into": "Merged From",
    "Merged From": "Merged Into",
    "Partnered With": "Partnered With"  # symmetric
}

class EditBusinessForm:
    def __init__(self, master, biz_id=None):
        self.master = master
        self.master.title("Edit Business")

        self.biz_id = biz_id
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.entries = {}
        self.preceded_by_id_map = {}
        self.succeeded_by_id_map = {}
        self.location_tab_added = False
        self.showing_tab_added = False
        
        self.setup_form()
        if biz_id:
            self.load_data()
            self.load_owners()
            self.load_locations()
            self.load_employees()
            self.load_bizevents()
            self.load_showings()
        else:
            self.disable_related_sections()
    

    def open_linked_business(self, field):
        label = self.entries[field].cget("text")
        if not label:
            return

        if field == "preceded_by":
            biz_id = self.preceded_by_id_map.get(label)
        elif field == "succeeded_by":
            biz_id = self.succeeded_by_id_map.get(label)
        else:
            return

        if biz_id:
            self.master.destroy()  # Close current Edit Business form
            new_root = tk.Tk()  # Create a new root window
            EditBusinessForm(new_root, biz_id)  # Launch a new form
            new_root.mainloop()  # Start the Tkinter event loop again

    def lookup_predecessor(self):
        def set_biz(biz_id):
            self.cursor.execute("SELECT biz_name, start_date, end_date FROM Biz WHERE biz_id = ?", (biz_id,))
            b = self.cursor.fetchone()
            if b:
                label = f"{b[0]} ({b[1]}–{b[2]})"
                self.entries['preceded_by'].config(text=label)
                self.preceded_by_id_map[label] = biz_id
        open_biz_linkage_popup(set_biz)

    def lookup_successor(self):
        def set_biz(biz_id):
            self.cursor.execute("SELECT biz_name, start_date, end_date FROM Biz WHERE biz_id = ?", (biz_id,))
            b = self.cursor.fetchone()
            if b:
                label = f"{b[0]} ({b[1]}–{b[2]})"
                self.entries['succeeded_by'].config(text=label)
                self.succeeded_by_id_map[label] = biz_id
        open_biz_linkage_popup(set_biz)
    
    def clear_lineage_field(self, field):
        if field in self.entries:
            self.entries[field].config(text="")
            if field == "preceded_by":
                self.preceded_by_id_map.clear()
            elif field == "succeeded_by":
                self.succeeded_by_id_map.clear()

    def setup_form(self):
        
        self.relationship_dropdowns = {}

        # Split fields into two columns starting from 'aliases'
        fields_column1 = [
            ("biz_name", "Business Name"),
            ("category", "Category"),
            ("start_date", "Start Date"),
            ("end_date", "End Date"),
            ("description", "Description")
        ]

        fields_column2 = [
            ("aliases", "Alternate Names"),
            ("image_path", "Image Path"),
            ("map_link", "Map Link"),
            ("external_url", "External URL")
        ]

        main = ttk.Frame(self.master)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)

        photo_frame = ttk.Frame(main)
        photo_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        ttk.Label(photo_frame, text="(photo)").pack()
        self.add_info_btn = ttk.Button(photo_frame, text="+", width=3, command=self.open_add_menu)
        self.add_info_btn.pack(pady=5)

        notebook_container = ttk.Frame(main)
        notebook_container.grid(row=0, column=1, sticky="nsew")
        notebook_container.columnconfigure(0, weight=1)
        notebook_container.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(notebook_container)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Tabs
        self.overview_tab = ttk.Frame(self.notebook)
        self.people_tab = ttk.Frame(self.notebook)
        self.locations_tab = ttk.Frame(self.notebook)
        self.showings_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.overview_tab, text="Overview")
        self.notebook.add(self.people_tab, text="People")

        form_frame = ttk.LabelFrame(self.overview_tab, text="Business Details")
        form_frame.pack(fill="x", padx=10, pady=10)

        # Column 1: Business identity
        labels_col1 = [("biz_name", "Business Name"), ("category", "Category"),
                       ("start_date", "Start Date"), ("end_date", "End Date")]
        for i, (field, label) in enumerate(labels_col1):
            ttk.Label(form_frame, text=label + ":").grid(row=i, column=0, sticky="e", padx=5, pady=2)
            entry = ttk.Entry(form_frame, width=30)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.entries[field] = entry

        # Column 2: Media and external references
        labels_col2 = [("aliases", "Alternate Names"), ("image_path", "Image Path"),
                       ("map_link", "Map Link"), ("external_url", "External URL")]
        for i, (field, label) in enumerate(labels_col2):
            ttk.Label(form_frame, text=label + ":").grid(row=i, column=2, sticky="e", padx=5, pady=2)
            entry = ttk.Entry(form_frame, width=30)
            entry.grid(row=i, column=3, sticky="w", padx=5, pady=2)
            self.entries[field] = entry

        # Preceded By
        self.relationship_dropdowns["preceded_by"] = ttk.Combobox(
            form_frame, values=PRECEDED_BY_TYPES, state="readonly", width=18)
        self.relationship_dropdowns["preceded_by"].grid(row=0, column=4, sticky="w", padx=5, pady=2)

        self.entries["preceded_by"] = ttk.Label(form_frame, text="", width=45, relief="sunken", anchor="w")
        self.entries["preceded_by"].grid(row=0, column=5, sticky="w", padx=5, pady=2)
        self.entries["preceded_by"].bind("<Double-1>", lambda e: self.open_linked_business("preceded_by"))

        ttk.Button(form_frame, text="Lookup", command=self.lookup_predecessor).grid(row=0, column=6, padx=2)
        ttk.Button(form_frame, text="Clear", command=lambda: self.clear_lineage_field("preceded_by")).grid(row=0, column=7, padx=2)

        # Succeeded By
        self.relationship_dropdowns["succeeded_by"] = ttk.Combobox(
            form_frame, values=SUCCEEDED_BY_TYPES, state="readonly", width=18)
        self.relationship_dropdowns["succeeded_by"].grid(row=1, column=4, sticky="w", padx=5, pady=2)

        self.entries["succeeded_by"] = ttk.Label(form_frame, text="", width=45, relief="sunken", anchor="w")
        self.entries["succeeded_by"].grid(row=1, column=5, sticky="w", padx=5, pady=2)
        self.entries["succeeded_by"].bind("<Double-1>", lambda e: self.open_linked_business("succeeded_by"))

        ttk.Button(form_frame, text="Lookup", command=self.lookup_successor).grid(row=1, column=6, padx=2)
        ttk.Button(form_frame, text="Clear", command=lambda: self.clear_lineage_field("succeeded_by")).grid(row=1, column=7, padx=2)        
            
        # Description spans all columns (row 5)
        ttk.Label(form_frame, text="Description:").grid(row=5, column=0, sticky="ne", padx=5, pady=2)
        desc_entry = tk.Text(form_frame, height=3, width=95)
        desc_entry.grid(row=5, column=1, columnspan=6, sticky="we", padx=5, pady=2)
        self.entries["description"] = desc_entry
              
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=6, column=0, columnspan=7, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Close", command=self.master.destroy).pack(side="left", padx=5)


        # Tree Section for Owners
        self.owner_frame = ttk.LabelFrame(self.people_tab, text="Business Owners")
        self.owner_frame.pack(fill="both", expand=False, padx=10, pady=5)

        #Start of the Tree Sections
        # 1 - Setup of the Owner Tree Section
        self.owner_tree = ttk.Treeview(self.owner_frame, columns=("biz_ownership_id", "person_id", "name", "type", "title", "start", "end", "notes"), show="headings", height=5)
        for col in self.owner_tree["columns"]:
            self.owner_tree.heading(col, text=col, command=lambda c=col: self.sort_owner_tree_by_column(c))
            
            if col in ("biz_ownership_id", "person_id"):
                self.owner_tree.column(col, width=0, stretch=False)  # Hide IDs
            elif col == "name":
                self.owner_tree.column(col, width=180)
            elif col == "type":
                self.owner_tree.column(col, width=60)
            elif col == "title":
                self.owner_tree.column(col, width=50)
            elif col in ("start", "end"):
                self.owner_tree.column(col, width=40)
            elif col == "notes":
                self.owner_tree.column(col, width=380)
            else:
                self.owner_tree.column(col, width=120)

        self.owner_tree.bind("<Double-1>", self.on_owner_double_click)
        self.owner_tree.pack(side="top", fill="x", expand=False, padx=5)

        owner_btns = ttk.Frame(self.owner_frame)
        owner_btns.pack(side="bottom", fill="x")
        
        self.owner_add_btn = ttk.Button(owner_btns, text="Add", command=self.add_owner)
        self.owner_add_btn.pack(side="left", padx=5)
        self.owner_edit_btn = ttk.Button(owner_btns, text="Edit", command=self.edit_owner)
        self.owner_edit_btn.pack(side="left", padx=5)
        self.owner_del_btn = ttk.Button(owner_btns, text="Delete", command=self.delete_owner)
        self.owner_del_btn.pack(side="left", padx=5)
        
        # 2- Setup of the Location Tree Section
        self.location_frame = ttk.LabelFrame(self.locations_tab, text="Locations")
        self.location_frame.pack(fill="both", expand=False, padx=10, pady=5)


        self.location_tree = ttk.Treeview(self.location_frame, columns=("address", "start", "end", "notes", "url"), show="headings", height=2)
        for col in self.location_tree["columns"]:
            self.location_tree.heading(col, text=col, command=lambda c=col: self.sort_location_tree_by_column(c))
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


        location_btns = ttk.Frame(self.location_frame)
        location_btns.pack(side="bottom", fill="x")
        
        self.location_add_btn = ttk.Button(location_btns, text="Add", command=self.add_location)
        self.location_add_btn.pack(side="left", padx=5)
        self.location_edit_btn = ttk.Button(location_btns, text="Edit", command=self.edit_location)
        self.location_edit_btn.pack(side="left", padx=5)
        self.location_del_btn = ttk.Button(location_btns, text="Delete", command=self.delete_location)
        self.location_del_btn.pack(side="left", padx=5)
        
        # 3 - Setup of the Employee Tree Section
        self.employee_frame = ttk.LabelFrame(self.people_tab, text="Employees")
        self.employee_frame.pack(fill="both", expand=False, padx=10, pady=5)

        self.employee_tree = ttk.Treeview(self.employee_frame, columns=("person_id", "name", "title", "start", "end", "notes"), show="headings", height=5)
        for col in self.employee_tree["columns"]:
            self.employee_tree.heading(col, text=col, command=lambda c=col: self.sort_employee_tree_by_column(c))
            if col == "person_id":
                self.employee_tree.column(col, width=0, stretch=False)  # Hide ID
            elif col == "name":
                self.employee_tree.column(col, width=180)
            elif col in ("start", "end"):
                self.employee_tree.column(col, width=90)
            elif col == "notes":
                self.employee_tree.column(col, width=240)
            else:
                self.employee_tree.column(col, width=120)

        
        self.employee_tree.pack(side="top", fill="x", expand=False, padx=5)
        self.employee_tree.bind("<Double-1>", self.on_employee_double_click)


        emp_btns = ttk.Frame(self.employee_frame)
        emp_btns.pack(side="bottom", fill="x")
        
        self.employee_add_btn = ttk.Button(emp_btns, text="Add", command=self.add_employee)
        self.employee_add_btn.pack(side="left", padx=5)
        self.employee_edit_btn = ttk.Button(emp_btns, text="Edit", command=self.edit_employee)
        self.employee_edit_btn.pack(side="left", padx=5)
        self.employee_del_btn = ttk.Button(emp_btns, text="Delete", command=self.delete_employee)
        self.employee_del_btn.pack(side="left", padx=5)

        # 4 - Setup of the Business Events Section
        self.bizevents_frame = ttk.LabelFrame(self.people_tab, text="Business Events")
        self.bizevents_frame.pack(fill="both", expand=False, padx=10, pady=5)

        self.bizevents_tree = ttk.Treeview(self.bizevents_frame, columns=("event_id", "event_type", "date_range", "person", "description", "link_url"), show="headings", height=5)
        
        self.bizevents_tree.column("event_id", width=0, stretch=False)  # Hidden ID
        self.bizevents_tree.heading("event_type", text="Event Type")
        self.bizevents_tree.column("event_type", width=120)
        self.bizevents_tree.heading("date_range", text="Date(s)")
        self.bizevents_tree.column("date_range", width=120)
        self.bizevents_tree.heading("person", text="Person")
        self.bizevents_tree.column("person", width=200)
        self.bizevents_tree.heading("description", text="Description")
        self.bizevents_tree.column("description", width=300)
        self.bizevents_tree.heading("link_url", text="Link")
        self.bizevents_tree.column("link_url", width=200)
        for col in self.bizevents_tree["columns"]:
            self.bizevents_tree.heading(col, text=col, command=lambda c=col: self.sort_bizevents_tree_by_column(c))
        
        self.bizevents_tree.pack(side="top", fill="x", expand=False, padx=5)
        self.bizevents_tree.bind("<Double-1>", self.on_bizevent_double_click)


        bizevents_btns = ttk.Frame(self.bizevents_frame)
        bizevents_btns.pack(side="bottom", fill="x")
        
        self.event_add_btn = ttk.Button(bizevents_btns, text="Add", command=self.add_bizevent)
        self.event_add_btn.pack(side="left", padx=5)
        self.event_edit_btn = ttk.Button(bizevents_btns, text="Edit", command=self.edit_bizevent)
        self.event_edit_btn.pack(side="left", padx=5)
        self.event_del_btn = ttk.Button(bizevents_btns, text="Delete", command=self.delete_bizevent)
        self.event_del_btn.pack(side="left", padx=5)
  
        # --- Movie Showings Section ---
        self.showings_frame = ttk.LabelFrame(self.showings_tab, text="Showings")
        self.showings_frame.pack(fill="both", expand=False, padx=10, pady=5)

        show_cols = ("showing_id", "title", "start", "end", "format", "event")
        self.showing_tree = ttk.Treeview(self.showings_frame, columns=show_cols, show="headings", height=5)
        for col in show_cols:
            self.showing_tree.heading(col, text=col.title(), command=lambda c=col: self.sort_showing_tree_by_column(c))
            width = 0 if col == "showing_id" else 100
            if col == "title":
                width = 200
            self.showing_tree.column(col, width=width, anchor="w", stretch=(col != "showing_id"))
        self.showing_tree.pack(side="top", fill="x", expand=False, padx=5)
        self.showing_tree.bind("<Double-1>", self.on_showing_double_click)

        show_btns = ttk.Frame(self.showings_frame)
        show_btns.pack(side="bottom", fill="x")
        self.showing_add_btn = ttk.Button(show_btns, text="Add", command=self.add_showing)
        self.showing_add_btn.pack(side="left", padx=5)
        self.showing_edit_btn = ttk.Button(show_btns, text="Edit", command=self.edit_showing)
        self.showing_edit_btn.pack(side="left", padx=5)
        self.showing_del_btn = ttk.Button(show_btns, text="Delete", command=self.delete_showing)
        self.showing_del_btn.pack(side="left", padx=5)

        apply_context_menu_to_all_entries(self.master)

    def disable_related_sections(self):
        widgets = [
            self.owner_tree, self.owner_add_btn, self.owner_edit_btn, self.owner_del_btn,
            self.location_tree, self.location_add_btn, self.location_edit_btn, self.location_del_btn,
            self.employee_tree, self.employee_add_btn, self.employee_edit_btn, self.employee_del_btn,
            self.bizevents_tree, self.event_add_btn, self.event_edit_btn, self.event_del_btn,
            self.showing_tree, self.showing_add_btn, self.showing_edit_btn, self.showing_del_btn,
        ]
        for w in widgets:
            try:
                w.state(["disabled"])
            except tk.TclError:
                w.config(state="disabled")

    def enable_related_sections(self):
        widgets = [
            self.owner_tree, self.owner_add_btn, self.owner_edit_btn, self.owner_del_btn,
            self.location_tree, self.location_add_btn, self.location_edit_btn, self.location_del_btn,
            self.employee_tree, self.employee_add_btn, self.employee_edit_btn, self.employee_del_btn,
            self.bizevents_tree, self.event_add_btn, self.event_edit_btn, self.event_del_btn,
            self.showing_tree, self.showing_add_btn, self.showing_edit_btn, self.showing_del_btn,
        ]
        for w in widgets:
            try:
                w.state(["!disabled"])
            except tk.TclError:
                w.config(state="normal")


    #
    #Support Functions for #1 - Owner Tree
    #
    
    def load_owners(self):
        self.owner_tree.delete(*self.owner_tree.get_children())

        self.cursor.execute("""
            SELECT o.biz_ownership_id, o.person_id,
                   CASE 
                       WHEN p.married_name IS NOT NULL AND p.married_name != ''
                       THEN p.first_name || ' ' || IFNULL(p.middle_name, '') || ' (' || p.last_name || ') ' || p.married_name
                       ELSE p.first_name || ' ' || IFNULL(p.middle_name || ' ', '') || p.last_name
                   END AS full_name,
                   o.ownership_type, o.title,
                   o.start_date, o.start_date_precision,
                   o.end_date, o.end_date_precision,
                   o.notes
            FROM BizOwnership o
            JOIN People p ON o.person_id = p.id
            WHERE o.biz_id = ?
        """, (self.biz_id,))

        rows = self.cursor.fetchall()

        # sort by start_date then ownership_type
        sorted_rows = sorted(rows, key=lambda row: (row[5] or "", row[3]))

        for row in sorted_rows:
            (biz_ownership_id, person_id, name, otype, title,
             start, start_prec, end, end_prec, notes) = row

            start_display = format_date_for_display(start, start_prec) if start else ""
            end_display = format_date_for_display(end, end_prec) if end else ""

            self.owner_tree.insert('', 'end', values=(
                biz_ownership_id, person_id, name, otype, title, start_display, end_display, notes))

    def add_owner(self):
        self.open_owner_editor()

    def edit_owner(self):
        selected = self.owner_tree.selection()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a record to edit.")
            return

        values = self.owner_tree.item(selected[0])['values']
        if values:
            self.open_owner_editor(existing=values)

    def open_owner_editor(self, existing=None, person_id=None):
        self.owner_win = tk.Toplevel(self.master)
        self.owner_win.title("Edit Owner" if existing else "Add Owner")

        self.owner_entries = {}
        self.owner_existing = existing

        def set_person_id(pid):
            self.owner_entries["Person ID"] = pid
            self.cursor.execute("SELECT first_name, middle_name, last_name, married_name FROM People WHERE id = ?", (pid,))
            result = self.cursor.fetchone()
            if result:
                name_parts = [result[0], result[1], result[2]]
                name = " ".join(p for p in name_parts if p)
                if result[3]:
                    name += f" ({result[3]})"
                person_display.config(text=name)
            else:
                person_display.config(text="(not found)")

        # --- Person selection ---
        ttk.Label(self.owner_win, text="Selected Person:").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        person_frame = ttk.Frame(self.owner_win)
        person_frame.grid(row=0, column=1, padx=5, pady=3, sticky="w")

        person_display = ttk.Label(person_frame, text="(none)", width=50, anchor="w", relief="sunken")
        person_display.pack(side="left", padx=(0, 5))
        self.owner_entries["Selected Person"] = person_display
        self.owner_entries["Person ID"] = None

        if person_id and not existing:
            self.owner_entries["Person ID"] = person_id
            set_person_id(person_id)

        ttk.Button(person_frame, text="Lookup", command=lambda: person_search_popup(set_person_id)).pack(side="left")
        ttk.Button(person_frame, text="Clear", command=lambda: [person_display.config(text="(none)"), self.owner_entries.update({"Person ID": None})]).pack(side="left")

        # --- Input fields ---
        labels = ["Ownership Type", "Title", "Start Date", "End Date", "Notes"]
        for i, label in enumerate(labels, start=1):
            ttk.Label(self.owner_win, text=label + ":").grid(row=i, column=0, padx=5, pady=3, sticky="e")
            entry = ttk.Entry(self.owner_win, width=40)
            entry.grid(row=i, column=1, padx=5, pady=3, sticky="w")
            self.owner_entries[label] = entry

        biz_ownership_id = None
        if existing:
            biz_ownership_id = existing[0]
            self.owner_entries["Person ID"] = existing[1]
            set_person_id(existing[1])

            # Extract values: name, otype, title, start_display, end_display, notes
            self.owner_entries["Ownership Type"].insert(0, existing[3])
            self.owner_entries["Title"].insert(0, existing[4])
            self.owner_entries["Start Date"].insert(0, existing[5])
            self.owner_entries["End Date"].insert(0, existing[6])
            self.owner_entries["Notes"].insert(0, existing[7])

        def save_owner():
            person_id = self.owner_entries["Person ID"]
            if not person_id:
                messagebox.showerror("Missing Person", "Please use Lookup to select a person.")
                return

            ownership_type = self.owner_entries["Ownership Type"].get().strip()
            title = self.owner_entries["Title"].get().strip()
            notes = self.owner_entries["Notes"].get().strip()

            try:
                start_input = self.owner_entries["Start Date"].get().strip()
                start_date, start_prec = parse_date_input(start_input) if start_input else (None, None)

                end_input = self.owner_entries["End Date"].get().strip()
                end_date, end_prec = parse_date_input(end_input) if end_input else (None, None)
            except ValueError as e:
                messagebox.showerror("Date Error", str(e))
                return

            try:
                if biz_ownership_id:  # Update
                    self.cursor.execute("""
                        UPDATE BizOwnership 
                        SET ownership_type = ?, title = ?, 
                            start_date = ?, start_date_precision = ?, 
                            end_date = ?, end_date_precision = ?, 
                            notes = ?
                        WHERE biz_ownership_id = ?
                    """, (
                        ownership_type, title,
                        start_date, start_prec,
                        end_date, end_prec,
                        notes, biz_ownership_id
                    ))
                else:  # Insert
                    self.cursor.execute("""
                        INSERT INTO BizOwnership (
                            biz_id, person_id, ownership_type, title,
                            start_date, start_date_precision,
                            end_date, end_date_precision,
                            notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.biz_id, person_id, ownership_type, title,
                        start_date, start_prec,
                        end_date, end_prec,
                        notes
                    ))

                self.conn.commit()
                self.load_owners()
                self.owner_win.destroy()

            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "An ownership record for this person with the same start date already exists.")

        # Buttons (fixed indentation)
        ttk.Button(self.owner_win, text="Save", command=save_owner).grid(row=len(labels)+2, column=0, pady=10)
        ttk.Button(self.owner_win, text="Cancel", command=self.owner_win.destroy).grid(row=len(labels)+2, column=1, pady=10)
     
    def open_owner_editor_with_person(self, person_id):
        self.open_owner_editor(person_id=person_id)

    def delete_owner(self):
        selected = self.owner_tree.selection()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a record to delete.")
            return

        values = self.owner_tree.item(selected[0])['values']
        if not values:
            return

        biz_ownership_id = values[0]
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this ownership record?")
        if not confirm:
            return

        try:
            self.cursor.execute("DELETE FROM BizOwnership WHERE biz_ownership_id = ?", (biz_ownership_id,))
            self.conn.commit()
            self.load_owners()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete ownership record: {e}")
   
    def on_owner_double_click(self, event):
        selected = self.owner_tree.selection()
        if selected:
            values = self.owner_tree.item(selected[0])['values']
            person_id = values[0]
            if person_id:
                self.master.destroy()  # Optional: close current biz form if needed
                subprocess.Popen([sys.executable, "-m", "app.editme", str(person_id)])
    
    def sort_owner_tree_by_column(self, col):
        if not hasattr(self, '_owner_sort_state'):
            self._owner_sort_state = {}

        reverse = self._owner_sort_state.get(col, False)

        items = [(self.owner_tree.set(k, col), k) for k in self.owner_tree.get_children('')]

        if col.lower() in ("start", "end", "start date", "end date"):
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)

        for index, (_, k) in enumerate(items):
            self.owner_tree.move(k, '', index)

        self._owner_sort_state[col] = not reverse

    # Support Functions for #2 - Location Tree
    # Biz location records are stored in the BizLocHistory table.
    # No standalone BizLocation table is used.

    def load_locations(self):
        self.location_tree.delete(*self.location_tree.get_children())

        self.cursor.execute("""
            SELECT a.address,
                   l.start_date, l.start_date_precision,
                   l.end_date, l.end_date_precision,
                   l.notes, l.url
            FROM BizLocHistory l
            JOIN Address a ON l.address_id = a.address_id
            WHERE l.biz_id = ?
        """, (self.biz_id,))

        rows = self.cursor.fetchall()

        if rows and not self.location_tab_added:
            tab_count = len(self.notebook.tabs())
            if 2 >= tab_count:
                self.notebook.add(self.locations_tab, text="Locations")
            else:
                self.notebook.insert(2, self.locations_tab, text="Locations")
            self.location_tab_added = True
        elif not rows and self.location_tab_added:
            self.notebook.forget(self.locations_tab)
            self.location_tab_added = False

        # Sort by raw start_date (index 1)
        sorted_rows = sorted(rows, key=lambda r: date_sort_key(r[1]))

        for row in sorted_rows:
            address, start, start_prec, end, end_prec, notes, url = row

            start_display = format_date_for_display(start, start_prec) if start else ""
            end_display = format_date_for_display(end, end_prec) if end else ""

            self.location_tree.insert('', 'end', values=(
                address, start_display, end_display, notes, url
            ))
        
        self.update_add_menu_state()

    def add_location(self):
        self.open_location_editor()

    
    def edit_location(self):
        selected = self.location_tree.selection()
        if not selected:
            return
        values = self.location_tree.item(selected[0])['values']
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
                        (original_address,)
                    )
                    result = self.cursor.fetchone()
                    if not result:
                        messagebox.showerror("Error", "Original address not found.")
                        return
                    original_address_id = result[0]
                    original_display_start = self.location_existing[1]
                    original_start_date, _ = parse_date_input(original_display_start)

                    update_query = """
                        UPDATE BizLocHistory
                        SET address_id = ?,
                            start_date = ?, start_date_precision = ?,
                            end_date = ?, end_date_precision = ?,
                            notes = ?, url = ?
                        WHERE biz_id = ? AND address_id = ?
                    """
                    params = [
                        address_id,
                        start_date, start_prec,
                        end_date, end_prec,
                        notes, url,
                        self.biz_id,
                        original_address_id,
                    ]
                    if original_start_date is not None:
                        update_query += " AND start_date = ?"
                        params.append(original_start_date)
                    else:
                        update_query += " AND start_date IS NULL"

                    self.cursor.execute(update_query, params)
                else:
                    self.cursor.execute("""
                        INSERT INTO BizLocHistory (
                            biz_id, address_id,
                            start_date, start_date_precision,
                            end_date, end_date_precision,
                            notes, url
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.biz_id, address_id,
                        start_date, start_prec,
                        end_date, end_prec,
                        notes, url
                    ))

                self.conn.commit()
                self.load_locations()
                self.location_win.destroy()

            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This location record already exists.")

        # Save and Cancel buttons
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
            values = self.location_tree.item(selected[0])['values']
            address = values[0]
            raw_start_date = values[1]

            try:
                parsed_start_date, _ = parse_date_input(raw_start_date)
            except ValueError:
                messagebox.showerror("Date Error", f"Could not parse start date: {raw_start_date}")
                return

            if parsed_start_date:
                query = """
                    DELETE FROM BizLocHistory
                    WHERE biz_id = ?
                      AND start_date = ?
                      AND address_id = (
                          SELECT address_id FROM Address WHERE address = ? LIMIT 1
                      )
                """
                params = (self.biz_id, parsed_start_date, address)
            else:
                query = """
                    DELETE FROM BizLocHistory
                    WHERE biz_id = ?
                      AND start_date IS NULL
                      AND address_id = (
                          SELECT address_id FROM Address WHERE address = ? LIMIT 1
                      )
                """
                params = (self.biz_id, address)

            self.cursor.execute(query, params)
            self.conn.commit()
            self.load_locations()

    def sort_location_tree_by_column(self, col):
        if not hasattr(self, '_location_sort_state'):
            self._location_sort_state = {}

        reverse = self._location_sort_state.get(col, False)

        items = [(self.location_tree.set(k, col), k) for k in self.location_tree.get_children('')]

        if col.lower() in ("start", "end", "start date", "end date"):
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)

        for index, (_, k) in enumerate(items):
            self.location_tree.move(k, '', index)

        self._location_sort_state[col] = not reverse
 
    #
    #Support Functions for #3 - Employee Tree
    #

    def load_employees(self):
        self.employee_tree.delete(*self.employee_tree.get_children())

        self.cursor.execute("""
            SELECT e.person_id,
                   CASE 
                       WHEN p.married_name IS NOT NULL AND p.married_name != ''
                       THEN p.first_name || ' ' || IFNULL(p.middle_name || ' ', '') || '(' || p.last_name || ') ' || p.married_name
                       ELSE p.first_name || ' ' || IFNULL(p.middle_name || ' ', '') || p.last_name
                   END AS full_name,
                   e.job_title,
                   e.start_date, e.start_date_precision,
                   e.end_date, e.end_date_precision,
                   e.notes
            FROM BizEmployment e
            JOIN People p ON e.person_id = p.id
            WHERE e.biz_id = ?
        """, (self.biz_id,))

        rows = self.cursor.fetchall()
        sorted_rows = sorted(rows, key=lambda r: date_sort_key(r[3]))  # r[3] = start_date

        for row in sorted_rows:
            person_id, name, job_title, start, start_prec, end, end_prec, notes = row
            start_display = format_date_for_display(start, start_prec) if start else ""
            end_display = format_date_for_display(end, end_prec) if end else ""

            self.employee_tree.insert('', 'end', values=(
                person_id, name, job_title, start_display, end_display, notes
            ))

    def add_employee(self):
        def on_person_selected(person_id):
            win = open_employee_editor(person_id=person_id, parent=self.master, biz_id=self.biz_id)
            if win is not None:
                self.master.wait_window(win)
                self.load_employees()        
        person_search_popup(on_person_selected)

    def edit_employee(self):
        selected = self.employee_tree.selection()
        if not selected:
            return
        values = self.employee_tree.item(selected[0])['values']
        self.open_employee_editor(existing=values)

    def open_employee_editor(self, existing=None):
        win = tk.Toplevel(self.master)
        win.title("Edit Employee" if existing else "Add Employee")
        win.geometry("600x300")
        self.employee_entries = {}
        self.employee_existing = existing
        entries = self.employee_entries

        def set_person_id(pid):
            entries["Person ID"].delete(0, tk.END)
            entries["Person ID"].insert(0, pid)

        ttk.Label(win, text="Person ID:").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        person_frame = ttk.Frame(win)
        person_frame.grid(row=0, column=1, padx=5, pady=3)
        person_id_entry = ttk.Entry(person_frame, width=30)
        person_id_entry.pack(side="left")
        ttk.Button(person_frame, text="Lookup", command=lambda: person_search_popup(set_person_id)).pack(side="left", padx=5)
        entries["Person ID"] = person_id_entry

        labels = ["Job Title", "Start Date", "End Date", "Notes"]
        for i, label in enumerate(labels, start=1):
            ttk.Label(win, text=label + ":").grid(row=i, column=0, padx=5, pady=3, sticky="e")
            entry = ttk.Entry(win, width=40)
            entry.grid(row=i, column=1, padx=5, pady=3)
            entries[label] = entry

        if existing:
            entries["Person ID"].insert(0, existing[0])
            for key, value in zip(labels, existing[2:]):
                entries[key].insert(0, value)

        def save_employee():
            person_id = entries["Person ID"].get().strip()
            title = entries["Job Title"].get().strip()
            notes = entries["Notes"].get().strip()

            try:
                start_raw = entries["Start Date"].get().strip()
                end_raw = entries["End Date"].get().strip()

                start_date, start_prec = parse_date_input(start_raw) if start_raw else (None, None)
                end_date, end_prec = parse_date_input(end_raw) if end_raw else (None, None)
            except ValueError as e:
                messagebox.showerror("Date Error", str(e))
                return

            try:
                if self.employee_existing:
                    # Use original DB-formatted start_date for WHERE clause
                    original_display_start = self.employee_existing[3]
                    original_start_date, _ = parse_date_input(original_display_start)

                    self.cursor.execute("""
                        UPDATE BizEmployment SET 
                            job_title = ?, 
                            start_date = ?, start_date_precision = ?, 
                            end_date = ?, end_date_precision = ?, 
                            notes = ?
                        WHERE biz_id = ? AND person_id = ? AND start_date = ?
                    """, (
                        title,
                        start_date, start_prec,
                        end_date, end_prec,
                        notes,
                        self.biz_id, person_id, original_start_date
                    ))
                else:
                    self.cursor.execute("""
                        INSERT INTO BizEmployment (
                            biz_id, person_id, job_title,
                            start_date, start_date_precision,
                            end_date, end_date_precision,
                            notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.biz_id, person_id, title,
                        start_date, start_prec,
                        end_date, end_prec,
                        notes
                    ))

                self.conn.commit()
                self.load_employees()
                win.destroy()

            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This employment record already exists with the same start date.")

        ttk.Button(win, text="Save", command=save_employee).grid(row=len(labels)+1, column=0, columnspan=2, pady=10)
        

    def delete_employee(self):
        selected = self.employee_tree.selection()
        if not selected:
            return
        person_id = self.employee_tree.item(selected[0])['values'][0]
        confirm = messagebox.askyesno("Delete", "Delete selected employment record?")
        if confirm:
            self.cursor.execute("DELETE FROM BizEmployment WHERE biz_id = ? AND person_id = ?", (self.biz_id, person_id))
            self.conn.commit()
            self.load_employees()

    
    def on_employee_double_click(self, event):
        selected = self.employee_tree.selection()
        if selected:
            values = self.employee_tree.item(selected[0])['values']
            person_id = values[0]
            if person_id:
                subprocess.Popen([sys.executable, "-m", "app.editme", str(person_id)])

            
    def sort_employee_tree_by_column(self, col):
        if not hasattr(self, '_employee_sort_state'):
            self._employee_sort_state = {}

        reverse = self._employee_sort_state.get(col, False)

        items = [(self.employee_tree.set(k, col), k) for k in self.employee_tree.get_children('')]

        if col.lower() in ("start", "end", "start date", "end date"):
            items.sort(key=lambda item: date_sort_key(item[0]), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)

        for index, (_, k) in enumerate(items):
            self.employee_tree.move(k, '', index)

        self._employee_sort_state[col] = not reverse
    

    def on_location_double_click(self, event):
        region = self.location_tree.identify("region", event.x, event.y)
        column = self.location_tree.identify_column(event.x)

        if region != "cell":
            return

        selected = self.location_tree.selection()
        if not selected:
            return

        values = self.location_tree.item(selected[0])['values']
        address = values[0]
        url = values[4]  # Assuming column 5 is URL

        if column == "#1":  # Address column
            if address:
                query = urllib.parse.quote(address)
                map_url = f"https://www.google.com/maps/search/?api=1&query={query}"
                webbrowser.open(map_url, new=2)
            else:
                messagebox.showinfo("No Address", "No address provided.")
        elif column == "#5":  # URL column
            if url and url.startswith("http"):
                webbrowser.open(url, new=2)
            else:
                messagebox.showinfo("No URL", "No valid link provided.")

    #
    #Support Functions for #4 - Business Events Tree   
    #
    
    def load_bizevents(self):
        self.bizevents_tree.delete(*self.bizevents_tree.get_children())

        query = """
            SELECT 
                e.event_id,
                e.event_type,
                e.event_start_date,
                e.event_start_date_precision,
                e.event_end_date,
                e.event_end_date_precision,
                e.summary,
                e.original_text,
                p.first_name, p.middle_name, p.last_name, p.married_name,
                e.description,
                e.link_url
            FROM BizEvents e
            LEFT JOIN People p ON e.person_id = p.id
            WHERE e.biz_id = ?
            ORDER BY e.event_start_date
        """
        self.cursor.execute(query, (self.biz_id,))
        
        for row in self.cursor.fetchall():
            (
                event_id, event_type,
                start_date, start_prec,
                end_date, end_prec,
                summary, original_text,
                first, middle, last, married,
                description, link_url
            ) = row

            start_fmt = format_date_for_display(start_date, start_prec) if start_date else ""
            end_fmt = format_date_for_display(end_date, end_prec) if end_date else ""

            date_range = start_fmt if not end_fmt else f"{start_fmt} – {end_fmt}"

            if married and last:
                person_name = f"{first or ''} {middle or ''} ({last}) {married}".strip()
            else:
                person_name = f"{first or ''} {middle or ''} {last or ''}".strip()

            self.bizevents_tree.insert('', 'end', values=(
                event_id, event_type, date_range, person_name,
                description or '', link_url or ''
            ))

    def add_bizevent(self):
        self.open_bizevent_editor()

    def edit_bizevent(self):
        selected = self.bizevents_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an event to edit.")
            return
        item = self.bizevents_tree.item(selected[0])
        self.open_bizevent_editor(existing=item['values'])   
    

    def open_bizevent_editor(self, existing=None):
        is_edit = existing is not None
        win = tk.Toplevel(self.master)
        win.title("Edit Business Event" if is_edit else "Add Business Event")
        win.geometry("700x600")

        labels = ["Event Type", "Start Date", "End Date", "Description", "Link URL"]
        entries = {}

        for i, label in enumerate(labels):
            ttk.Label(win, text=label + ":").grid(row=i, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(win, width=50)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[label] = entry

        row_index = len(labels)

        # --- Person Display and Linkage ---
        ttk.Label(win, text="Person:").grid(row=row_index, column=0, sticky="e", padx=5, pady=5)
        person_label = ttk.Label(win, text="", width=50, anchor="w")
        person_label.grid(row=row_index, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        person_label.person_id = None
        row_index += 1

        def set_person_id(pid):
            self.cursor.execute("SELECT first_name, middle_name, last_name, married_name FROM People WHERE id = ?", (pid,))
            name_parts = self.cursor.fetchone()
            if name_parts:
                first, middle, last, married = name_parts
                if married and last:
                    display = f"{first or ''} {middle or ''} ({last}) {married}".strip()
                else:
                    display = f"{first or ''} {middle or ''} {last or ''}".strip()
                person_label.config(text=display)
            person_label.person_id = pid
            clear_button.grid()

        def clear_person():
            person_label.config(text="")
            person_label.person_id = None
            clear_button.grid_remove()

        ttk.Button(win, text="Lookup Person", command=lambda: person_search_popup(set_person_id)).grid(row=row_index, column=0, padx=5, pady=5)
        clear_button = ttk.Button(win, text="Clear Person", command=clear_person)
        clear_button.grid(row=row_index, column=1, padx=5, pady=5)
        clear_button.grid_remove()
        row_index += 1

        # --- Summary Field ---
        ttk.Label(win, text="Summary:").grid(row=row_index, column=0, sticky="ne", padx=5, pady=5)
        summary_text = tk.Text(win, width=50, height=3)
        summary_text.grid(row=row_index, column=1, padx=5, pady=5)
        create_context_menu(summary_text)
        row_index += 1

        # --- Original Text Field ---
        ttk.Label(win, text="Original Text:").grid(row=row_index, column=0, sticky="ne", padx=5, pady=5)
        original_text_box = tk.Text(win, width=50, height=6)
        original_text_box.grid(row=row_index, column=1, padx=5, pady=5)
        create_context_menu(original_text_box)
        row_index += 1

        ttk.Separator(win, orient="horizontal").grid(row=row_index, column=0, columnspan=3, sticky="ew", padx=5, pady=10)
        row_index += 1

        # --- Pre-fill if editing ---
        event_id = None
        if is_edit:
            event_id = existing[0]
            self.cursor.execute("""
                SELECT event_type, event_start_date, event_start_date_precision,
                       event_end_date, event_end_date_precision, summary, original_text,
                       person_id, description, link_url
                FROM BizEvents WHERE event_id = ?
            """, (event_id,))
            res = self.cursor.fetchone()
            if res:
                etype, sdate, sprec, edate, eprec, summary, original_text, pid, desc, link = res
                entries["Event Type"].insert(0, etype or "")
                entries["Start Date"].insert(0, format_date_for_display(sdate, sprec))
                entries["End Date"].insert(0, format_date_for_display(edate, eprec))
                entries["Description"].insert(0, desc or "")
                entries["Link URL"].insert(0, link or "")
                summary_text.insert("1.0", summary or "")
                original_text_box.insert("1.0", original_text or "")
                if pid:
                    set_person_id(pid)

        # --- Save Handler ---
        def save_event():
            data = {k: v.get().strip() for k, v in entries.items()}
            summary = summary_text.get("1.0", tk.END).strip()
            original_text = original_text_box.get("1.0", tk.END).strip()
            try:
                start_date, start_prec = parse_date_input(data["Start Date"])
                end_date, end_prec = parse_date_input(data["End Date"]) if data["End Date"] else (None, None)
            except ValueError as e:
                messagebox.showerror("Date Error", str(e))
                return

            try:
                if is_edit:
                    self.cursor.execute("""
                        UPDATE BizEvents
                        SET event_type = ?, 
                            event_start_date = ?, event_start_date_precision = ?,
                            event_end_date = ?, event_end_date_precision = ?,
                            summary = ?, original_text = ?,
                            person_id = ?, description = ?, link_url = ?
                        WHERE event_id = ?
                    """, (
                        data["Event Type"],
                        start_date, start_prec,
                        end_date, end_prec,
                        summary, original_text,
                        person_label.person_id,
                        data["Description"],
                        data["Link URL"],
                        event_id
                    ))
                else:
                    self.cursor.execute("""
                        INSERT INTO BizEvents (
                            biz_id, event_type,
                            event_start_date, event_start_date_precision,
                            event_end_date, event_end_date_precision,
                            summary, original_text, 
                            person_id, description, link_url
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.biz_id, data["Event Type"],
                        start_date, start_prec,
                        end_date, end_prec,
                        summary, original_text,     
                        person_label.person_id,
                        data["Description"],
                        data["Link URL"]
                    ))
                self.conn.commit()
                self.load_bizevents()
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save event: {e}")

        # --- Buttons ---
        btn_frame = ttk.Frame(win)
        btn_frame.grid(row=row_index, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="Save", command=save_event).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side="left", padx=10)



    def delete_bizevent(self):
        selected = self.bizevents_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an event to delete.")
            return

        item = self.bizevents_tree.item(selected[0])
        event_id = item['values'][0]

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected business event?")
        if confirm:
            try:
                self.cursor.execute("DELETE FROM BizEvents WHERE event_id = ?", (event_id,))
                self.conn.commit()
                self.load_bizevents()
                messagebox.showinfo("Deleted", "Business event deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete event: {e}")


    
    def on_bizevent_double_click(self, event):
        region = self.bizevents_tree.identify("region", event.x, event.y)
        column = self.bizevents_tree.identify_column(event.x)

        if region != "cell":
            return

        selected = self.bizevents_tree.selection()
        if not selected:
            return

        values = self.bizevents_tree.item(selected[0])['values']

        # Column #4 = person name, Column #6 = link_url
        if column == "#4":
            # We need to fetch the person ID from elsewhere — store it in the hidden first column if not already
            person_name = values[3]  # e.g., "John Doe"
            event_id = self.bizevents_tree.item(selected[0])['values'][0]

            # Assuming your event links to a person_id, you can adjust this part:
            self.cursor.execute("""
                SELECT person_id FROM BizEvents WHERE event_id = ?
            """, (event_id,))
            result = self.cursor.fetchone()
            if result:
                person_id = result[0]
                subprocess.Popen([sys.executable, "-m", "app.editme", str(person_id)])
            else:
                messagebox.showinfo("Info", f"No linked person found for '{person_name}'.")

        elif column == "#6":
            url = values[5]  # link_url column
            if url and url.startswith("http"):
                webbrowser.open(url, new=2)
            else:
                messagebox.showinfo("No URL", "No valid link provided for this event.")

    def sort_showing_tree_by_column(self, col):
        if not hasattr(self, '_showing_sort_state'):
            self._showing_sort_state = {}
        reverse = self._showing_sort_state.get(col, False)
        items = [(self.showing_tree.set(k, col), k) for k in self.showing_tree.get_children('')]
        items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)
        for index, (_, k) in enumerate(items):
            self.showing_tree.move(k, '', index)
        self._showing_sort_state[col] = not reverse

    def load_showings(self):
        self.showing_tree.delete(*self.showing_tree.get_children())
        self.cursor.execute(
            """SELECT s.showing_id, m.title, s.start_date, s.end_date, s.format, s.special_event
               FROM MovieShowings s JOIN Movies m ON s.movie_id=m.movie_id
               WHERE s.biz_id=? ORDER BY s.start_date""",
            (self.biz_id,)
        )
        rows = self.cursor.fetchall()
  
        if rows and not self.showing_tab_added:
            index = 3 if self.location_tab_added else 2
            tab_count = len(self.notebook.tabs())
            if index >= tab_count:
                self.notebook.add(self.showings_tab, text="Showings")
            else:
                self.notebook.insert(index, self.showings_tab, text="Showings")
            self.showing_tab_added = True
        elif not rows and self.showing_tab_added:
            self.notebook.forget(self.showings_tab)
            self.showing_tab_added = False

        for row in rows:
            self.showing_tree.insert('', 'end', values=row)

        self.update_add_menu_state()

    
    def add_showing(self):
        win = open_edit_showing_form(parent=self.master, biz_id=self.biz_id)
        if win:
            self.master.wait_window(win)
        self.load_showings()

    def edit_showing(self, event=None):
        sel = self.showing_tree.selection()
        if not sel:
            return
        showing_id = self.showing_tree.item(sel[0])['values'][0]
        win = open_edit_showing_form(showing_id, parent=self.master)
        if win:
            self.master.wait_window(win)
        self.load_showings()

    def delete_showing(self):
        sel = self.showing_tree.selection()
        if not sel:
            return
        showing_id = self.showing_tree.item(sel[0])['values'][0]
        if not messagebox.askyesno("Confirm Delete", "Delete selected showing?"):
            return
        try:
            self.cursor.execute("DELETE FROM MovieShowings WHERE showing_id=?", (showing_id,))
            self.conn.commit()
            self.load_showings()
        except Exception as e:
            messagebox.showerror("Delete Failed", str(e))

    
    def on_showing_double_click(self, event):
        self.edit_showing()

    
    def sort_bizevents_tree_by_column(self, col):
        if not hasattr(self, '_bizevent_sort_state'):
            self._bizevent_sort_state = {}

        reverse = self._bizevent_sort_state.get(col, False)

        items = [(self.bizevents_tree.set(k, col), k) for k in self.bizevents_tree.get_children('')]

        if col.lower() in ("date", "date_range", "start"):
            items.sort(key=lambda item: date_sort_key(item[0].split("–")[0].strip()), reverse=reverse)
        else:
            items.sort(key=lambda item: item[0].lower() if isinstance(item[0], str) else item[0], reverse=reverse)

        for index, (_, k) in enumerate(items):
            self.bizevents_tree.move(k, '', index)

        self._bizevent_sort_state[col] = not reverse

    def load_business_dropdowns(self):
        # Clear old values
        self.relationship_dropdowns['preceded_by']['values'] = []
        self.relationship_dropdowns['succeeded_by']['values'] = []
        self.preceded_by_id_map.clear()
        self.succeeded_by_id_map.clear()

    def open_add_menu(self, event=None):
        menu = tk.Menu(self.master, tearoff=0)
        if not self.location_tab_added:
            menu.add_command(label="Add Location", command=self.add_location)
        if not self.showing_tab_added:
            menu.add_command(label="Add Showing", command=self.add_showing)
        if menu.index("end") is None:
            return
        if event:
            menu.tk_popup(event.x_root, event.y_root)
        else:
            x = self.add_info_btn.winfo_rootx()
            y = self.add_info_btn.winfo_rooty() + self.add_info_btn.winfo_height()
            menu.tk_popup(x, y)

    def update_add_menu_state(self):
        """Refresh any dynamic UI elements when tabs are added or removed."""
        pass
         

    def load_data(self):
        # Load Biz main fields
        self.cursor.execute("""
            SELECT biz_name, category, start_date, start_date_precision,
                   end_date, end_date_precision, description, aliases, 
                   image_path, map_link, external_url 
            FROM Biz 
            WHERE biz_id = ?
        """, (self.biz_id,))
        row = self.cursor.fetchone()

        if row:
            keys = [
                "biz_name", "category", "start_date", "start_date_precision",
                "end_date", "end_date_precision", "description", "aliases", 
                "image_path", "map_link", "external_url"
            ]
            data = dict(zip(keys, row))

            # Format and load date fields
            start_display = format_date_for_display(data["start_date"], data["start_date_precision"])
            end_display = format_date_for_display(data["end_date"], data["end_date_precision"])

            self.entries["start_date"].delete(0, tk.END)
            self.entries["start_date"].insert(0, start_display or "")

            self.entries["end_date"].delete(0, tk.END)
            self.entries["end_date"].insert(0, end_display or "")

            # Load the rest
            for k in ["biz_name", "category", "description", "aliases", "image_path", "map_link", "external_url"]:
                if k == "description":
                    self.entries[k].delete("1.0", "end")
                    self.entries[k].insert("1.0", data[k] or "")
                else:
                    self.entries[k].delete(0, tk.END)
                    self.entries[k].insert(0, data[k] or "")

        # Load Predecessor
        self.cursor.execute("""
            SELECT parent_biz_id, relationship_type FROM BizLineage
            WHERE child_biz_id = ?
        """, (self.biz_id,))
        row = self.cursor.fetchone()
        if row:
            parent_id, rel_type = row
            self.cursor.execute("SELECT biz_name, start_date, end_date FROM Biz WHERE biz_id = ?", (parent_id,))
            b = self.cursor.fetchone()
            if b:
                label = f"{b[0]} ({b[1]}–{b[2]})"
                self.entries["preceded_by"].config(text=label)
                self.preceded_by_id_map[label] = parent_id
                display_type = RELATIONSHIP_INVERSION.get(rel_type, rel_type)
                self.relationship_dropdowns["preceded_by"].set(display_type)

        # Load Successor
        self.cursor.execute("""
            SELECT child_biz_id, relationship_type FROM BizLineage
            WHERE parent_biz_id = ?
        """, (self.biz_id,))
        row = self.cursor.fetchone()
        if row:
            child_id, rel_type = row
            self.cursor.execute("SELECT biz_name, start_date, end_date FROM Biz WHERE biz_id = ?", (child_id,))
            b = self.cursor.fetchone()
            if b:
                label = f"{b[0]} ({b[1]}–{b[2]})"
                self.entries["succeeded_by"].config(text=label)
                self.succeeded_by_id_map[label] = child_id
                self.relationship_dropdowns["succeeded_by"].set(rel_type)



    def save_lineage_links(self, preceded_by_id, succeeded_by_id, preceded_by_type, succeeded_by_type):
        self.cursor.execute("""
            DELETE FROM BizLineage
            WHERE (child_biz_id = ? OR parent_biz_id = ?)
        """, (self.biz_id, self.biz_id))

        if preceded_by_id:
            self.cursor.execute("""
                INSERT INTO BizLineage (parent_biz_id, child_biz_id, relationship_type)
                VALUES (?, ?, ?)
            """, (preceded_by_id, self.biz_id, preceded_by_type))

        if succeeded_by_id:
            self.cursor.execute("""
                INSERT INTO BizLineage (parent_biz_id, child_biz_id, relationship_type)
                VALUES (?, ?, ?)
            """, (self.biz_id, succeeded_by_id, succeeded_by_type))

    def save(self):
        try:
            data = {}
            for k, widget in self.entries.items():
                if isinstance(widget, tk.Text):
                    data[k] = widget.get("1.0", tk.END).strip()
                elif isinstance(widget, ttk.Label):  # For preceded_by and succeeded_by
                    label_text = widget.cget("text").strip()
                    if k == "preceded_by":
                        data["preceded_by"] = self.preceded_by_id_map.get(label_text)
                    elif k == "succeeded_by":
                        data["succeeded_by"] = self.succeeded_by_id_map.get(label_text)
                elif isinstance(widget, ttk.Entry):
                    data[k] = widget.get().strip()

            # Parse and extract date + precision
            start_date, start_prec = parse_date_input(data["start_date"])
            end_date, end_prec = parse_date_input(data["end_date"]) if data.get("end_date") else ("", "")

            new_record = self.biz_id is None
            if self.biz_id:  # Update
                self.cursor.execute("""
                    UPDATE Biz SET
                        biz_name = ?, category = ?, start_date = ?, start_date_precision = ?,
                        end_date = ?, end_date_precision = ?, description = ?, aliases = ?,
                        image_path = ?, map_link = ?, external_url = ?
                    WHERE biz_id = ?
                """, (
                    data["biz_name"], data["category"], start_date, start_prec,
                    end_date, end_prec, data["description"], data["aliases"],
                    data["image_path"], data["map_link"], data["external_url"],
                    self.biz_id
                ))
            else:  # Insert
                self.cursor.execute("""
                    INSERT INTO Biz (
                        biz_name, category, start_date, start_date_precision,
                        end_date, end_date_precision, description, aliases,
                        image_path, map_link, external_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["biz_name"], data["category"], start_date, start_prec,
                    end_date, end_prec, data["description"], data["aliases"],
                    data["image_path"], data["map_link"], data["external_url"]
                ))
                self.biz_id = self.cursor.lastrowid

            pred_type = self.relationship_dropdowns["preceded_by"].get()
            succ_type = self.relationship_dropdowns["succeeded_by"].get()

            self.save_lineage_links(
                preceded_by_id=data.get("preceded_by"),
                succeeded_by_id=data.get("succeeded_by"),
                preceded_by_type=pred_type or "Predecessor",
                succeeded_by_type=succ_type or "Successor"
            )

            self.conn.commit()
            if new_record:
                self.enable_related_sections()

            messagebox.showinfo("Saved", "Business record updated.", parent=self.master)
            self.master.lift()
            self.master.focus_force()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")


def open_edit_business_form(biz_id=None):
    win = tk.Tk() if biz_id is None else tk.Toplevel()
    win.geometry("1300x900")
    EditBusinessForm(win, biz_id)
    win.grab_set()

if __name__ == "__main__":
    import sys
    root = tk.Tk()
    biz_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    app = EditBusinessForm(root, biz_id)
    root.mainloop()
