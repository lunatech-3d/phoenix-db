import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from context_menu import create_context_menu
from person_search import search_people
import re

class AddDeedDialog:
    def __init__(self, parent, current_person_id):
        self.townships = []  # Will store township data including IDs
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Deed Record")
        self.dialog.geometry("1500x900")
        self.current_person_id = current_person_id
        self.skip_current_person = False
        
        # Get current person's name for display
        self.current_person_name = self.get_person_name(current_person_id)
        
        # Main frame with scrollbar
        main_canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        # Pack the scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        main_canvas.pack(side="left", fill="both", expand=True)
        
        # Main content frame
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current Person Section
        current_person_frame = ttk.LabelFrame(main_frame, text="Current Person", padding="5")
        current_person_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(current_person_frame, text=self.current_person_name).pack(side=tk.LEFT, padx=5)
        
        # Role selection
        ttk.Label(current_person_frame, text="Role:").pack(side=tk.LEFT, padx=5)
        self.role_var = tk.StringVar(value="Grantor")
        role_combo = ttk.Combobox(current_person_frame, textvariable=self.role_var, 
                                 values=["Grantor", "Grantee"], state="readonly")
        role_combo.pack(side=tk.LEFT, padx=5)
        role_combo.bind('<<ComboboxSelected>>', self.on_role_change)
        
        # Parties Section
        parties_frame = ttk.LabelFrame(main_frame, text="Parties", padding="5")
        parties_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Split into left and right sides
        parties_left = ttk.Frame(parties_frame)
        parties_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        parties_right = ttk.Frame(parties_frame)
        parties_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Grantors Section
        grantors_frame = ttk.LabelFrame(parties_left, text="Grantors")
        grantors_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Grantors tree
        self.grantors_tree = ttk.Treeview(grantors_frame, 
            columns=("ID", "First", "Middle", "Last", "Married", "Birth", "Death"),
            show='headings', 
            height=4)
        self.setup_party_tree(self.grantors_tree)
        self.grantors_tree.pack(fill=tk.BOTH, expand=True)
        
        grantor_btn_frame = ttk.Frame(grantors_frame)
        grantor_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(grantor_btn_frame, text="Add Grantor", 
                  command=lambda: self.show_search_dialog("Grantor")).pack(side=tk.LEFT, padx=2)
        ttk.Button(grantor_btn_frame, text="Remove Grantor", 
                  command=lambda: self.remove_party("Grantor")).pack(side=tk.LEFT, padx=2)
        
        # Grantees Section
        grantees_frame = ttk.LabelFrame(parties_right, text="Grantees")
        grantees_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Grantees tree
        self.grantees_tree = ttk.Treeview(grantees_frame, 
            columns=("ID", "First", "Middle", "Last", "Married", "Birth", "Death"),
            show='headings', 
            height=4)
        self.setup_party_tree(self.grantees_tree)
        self.grantees_tree.pack(fill=tk.BOTH, expand=True)
        
        grantee_btn_frame = ttk.Frame(grantees_frame)
        grantee_btn_frame.pack(fill=tk.X, pady=2)
        ttk.Button(grantee_btn_frame, text="Add Grantee", 
                  command=lambda: self.show_search_dialog("Grantee")).pack(side=tk.LEFT, padx=2)
        ttk.Button(grantee_btn_frame, text="Remove Grantee", 
                  command=lambda: self.remove_party("Grantee")).pack(side=tk.LEFT, padx=2)

        # Create a container frame for deed info and section
        deed_container = ttk.Frame(main_frame)
        deed_container.pack(fill=tk.X, pady=5)

        # Deed Information Section
        deed_info_frame = ttk.LabelFrame(deed_container, text="Deed Information", padding="5")
        deed_info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Type
        type_frame = ttk.Frame(deed_info_frame)
        type_frame.pack(fill=tk.X, pady=2)
        ttk.Label(type_frame, text="Type:*").pack(side=tk.LEFT, padx=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(type_frame, textvariable=self.type_var, 
                                      values=self.get_deed_types(), state="readonly",
                                      width=30)
        self.type_combo.pack(side=tk.LEFT, padx=5)

        # Amount
        amount_frame = ttk.Frame(deed_info_frame)
        amount_frame.pack(fill=tk.X, pady=2)
        ttk.Label(amount_frame, text="Amount:*").pack(side=tk.LEFT, padx=5)
        self.amount_entry = ttk.Entry(amount_frame)
        self.amount_entry.pack(side=tk.LEFT, padx=5)
        
        # Book-Liber/Page
        book_frame = ttk.Frame(deed_info_frame)
        book_frame.pack(fill=tk.X, pady=2)
        ttk.Label(book_frame, text="Book/Liber:").pack(side=tk.LEFT, padx=5)
        self.book_entry = ttk.Entry(book_frame, width=10)
        self.book_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(book_frame, text="Page:").pack(side=tk.LEFT, padx=5)
        self.page_entry = ttk.Entry(book_frame, width=10)
        self.page_entry.pack(side=tk.LEFT, padx=5)

        # Dates section
        dates_frame = ttk.LabelFrame(deed_info_frame, text="Dates")
        dates_frame.pack(fill=tk.X, pady=5)
        
        # Dated (execution_date)
        dated_frame = ttk.Frame(dates_frame)
        dated_frame.pack(fill=tk.X, pady=2)
        ttk.Label(dated_frame, text="Dated:*").grid(row=0, column=0, sticky='e', padx=5)
        self.execution_date_entry = ttk.Entry(dated_frame)
        self.execution_date_entry.grid(row=0, column=1, sticky='w', padx=5)
        self.execution_date_entry.bind('<FocusOut>', self.update_township_list)

        # Acknowledged
        ack_frame = ttk.Frame(dates_frame)
        ack_frame.pack(fill=tk.X, pady=2)
        ttk.Label(ack_frame, text="Acknowledged:").grid(row=0, column=0, sticky='e', padx=5)
        self.acknowledge_date_entry = ttk.Entry(ack_frame)
        self.acknowledge_date_entry.grid(row=0, column=1, sticky='w', padx=5)
        
        # Recorded
        recorded_frame = ttk.Frame(dates_frame)
        recorded_frame.pack(fill=tk.X, pady=2)
        ttk.Label(recorded_frame, text="Recorded:*").grid(row=0, column=0, sticky='e', padx=5)
        self.recording_date_entry = ttk.Entry(recorded_frame)
        self.recording_date_entry.grid(row=0, column=1, sticky='w', padx=5)
        
        # Date format note
        ttk.Label(dates_frame, text="(Format: YYYY, MM-YYYY, or MM-DD-YYYY)", 
                  font=('Arial', 8, 'italic')).pack(pady=(0,5))

        # Legal Description section
        legal_frame = ttk.LabelFrame(deed_container, text="Legal Description", padding="5")
        legal_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Township section
        township_frame = ttk.Frame(legal_frame)
        township_frame.pack(fill=tk.X, pady=2)
        ttk.Label(township_frame, text="Township:").pack(side=tk.LEFT, padx=5)
        self.township_var = tk.StringVar()
        self.township_combo = ttk.Combobox(township_frame, 
                                          textvariable=self.township_var, 
                                          state='disabled',
                                          width=50)
        self.township_combo.pack(side=tk.LEFT, padx=5)
        self.township_combo['values'] = ['Enter date first to see townships']
        self.township_combo.set('Enter date first to see townships')

        # Top row - Section and Acres
        top_frame = ttk.Frame(legal_frame)
        top_frame.pack(fill=tk.X, pady=2)

        # Section
        section_frame = ttk.Frame(top_frame)
        section_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(section_frame, text="Section Number *").pack(anchor=tk.W)
        self.section_var = tk.StringVar()
        self.section_combo = ttk.Combobox(section_frame, 
                                         textvariable=self.section_var,
                                         values=[str(i) for i in range(1, 37)],
                                         width=10)
        self.section_combo.pack()

        # Acres
        acres_frame = ttk.Frame(top_frame)
        acres_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(acres_frame, text="Acres").pack(anchor=tk.W)
        self.acres_entry = ttk.Entry(acres_frame, width=10)
        self.acres_entry.pack()

        # Quarter Sections frame
        quarters_frame = ttk.LabelFrame(legal_frame, text="Location Within Section")
        quarters_frame.pack(fill=tk.X, padx=5, pady=5)

        # Quarter Section
        quarter_frame = ttk.Frame(quarters_frame)
        quarter_frame.pack(fill=tk.X, pady=2)
        ttk.Label(quarter_frame, text="Quarter Section").pack(side=tk.LEFT, padx=5)
        self.quarter_var = tk.StringVar()
        self.quarter_combo = ttk.Combobox(quarter_frame, 
                                         textvariable=self.quarter_var,
                                         values=["", "Northeast Quarter", "Northwest Quarter", 
                                               "Southeast Quarter", "Southwest Quarter"],
                                         width=20)
        self.quarter_combo.pack(side=tk.LEFT, padx=5)

        # Quarter of Quarter
        quarter_quarter_frame = ttk.Frame(quarters_frame)
        quarter_quarter_frame.pack(fill=tk.X, pady=2)
        ttk.Label(quarter_quarter_frame, text="Quarter of Quarter").pack(side=tk.LEFT, padx=5)
        self.quarter_quarter_var = tk.StringVar()
        self.quarter_quarter_combo = ttk.Combobox(quarter_quarter_frame, 
                                                textvariable=self.quarter_quarter_var,
                                                values=["", "Northeast Quarter", "Northwest Quarter", 
                                                      "Southeast Quarter", "Southwest Quarter"],
                                                width=20)
        self.quarter_quarter_combo.pack(side=tk.LEFT, padx=5)

        # Half Designation
        half_frame = ttk.Frame(legal_frame)
        half_frame.pack(fill=tk.X, pady=2)
        ttk.Label(half_frame, text="Half Designation").pack(side=tk.LEFT, padx=5)
        self.half_var = tk.StringVar()
        self.half_combo = ttk.Combobox(half_frame, 
                                      textvariable=self.half_var,
                                      values=["", "North Half", "South Half", 
                                            "East Half", "West Half"],
                                      width=15)
        self.half_combo.pack(side=tk.LEFT, padx=5)

        # Preview frame
        preview_frame = ttk.LabelFrame(legal_frame, text="Description Preview")
        preview_frame.pack(fill=tk.X, padx=5, pady=5)
        self.preview_label = ttk.Label(preview_frame, text="")
        self.preview_label.pack(padx=5, pady=5)

        # Add bindings for legal description preview updates
        self.section_combo.bind('<<ComboboxSelected>>', self.update_legal_preview)
        self.quarter_combo.bind('<<ComboboxSelected>>', self.update_legal_preview)
        self.quarter_quarter_combo.bind('<<ComboboxSelected>>', self.update_legal_preview)
        self.half_combo.bind('<<ComboboxSelected>>', self.update_legal_preview)
        self.acres_entry.bind('<KeyRelease>', self.update_legal_preview)

        # Add frame for legal description segments
        self.segments_frame = ttk.LabelFrame(legal_frame, text="Land Segments")
        self.segments_frame.pack(fill=tk.X, padx=5, pady=5)

        # Create segments treeview
        self.segments_tree = ttk.Treeview(self.segments_frame,
            columns=("Section", "Quarter", "Quarter-Quarter", "Half", "Acres", "Description"),
            show='headings',
            height=4)
        
        # Configure columns
        self.segments_tree.heading("Section", text="Section")
        self.segments_tree.heading("Quarter", text="Quarter")
        self.segments_tree.heading("Quarter-Quarter", text="Quarter-Quarter")
        self.segments_tree.heading("Half", text="Half")
        self.segments_tree.heading("Acres", text="Acres")
        self.segments_tree.heading("Description", text="Description")

        # Set column widths
        self.segments_tree.column("Section", width=60)
        self.segments_tree.column("Quarter", width=110)
        self.segments_tree.column("Quarter-Quarter", width=100)
        self.segments_tree.column("Half", width=85)
        self.segments_tree.column("Acres", width=60)
        self.segments_tree.column("Description", width=275)

        self.segments_tree.pack(fill=tk.X, padx=5, pady=5)

        # Add segment buttons frame
        segment_buttons = ttk.Frame(self.segments_frame)
        segment_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(segment_buttons, text="Add Segment", 
                  command=self.add_segment).pack(side=tk.LEFT, padx=5)
        ttk.Button(segment_buttons, text="Remove Segment", 
                  command=self.remove_segment).pack(side=tk.LEFT, padx=5)

        # Description sections
        desc_frame = ttk.Frame(deed_info_frame)
        desc_frame.pack(fill=tk.X, pady=2)
        
        # Original Legal Text
        ttk.Label(desc_frame, text="Original Legal Text:").pack(anchor=tk.W, padx=5)
        self.legal_text = tk.Text(desc_frame, height=5, wrap='word')
        self.legal_text.pack(fill=tk.X, padx=5, pady=(0, 10))

        # Overview/Summary
        ttk.Label(desc_frame, text="Legal Description Overview:").pack(anchor=tk.W, padx=5)
        self.desc_text = tk.Text(desc_frame, height=3, wrap='word', 
                                background='#f0f0f0',
                                relief='flat')
        self.desc_text.configure(state='disabled', cursor='arrow')
        self.desc_text.pack(fill=tk.X, padx=5, pady=(0,5))

        # Notes
        notes_frame = ttk.Frame(deed_info_frame)
        notes_frame.pack(fill=tk.X, pady=2)
        ttk.Label(notes_frame, text="Notes:").pack(anchor=tk.W, padx=5)
        self.notes_text = tk.Text(notes_frame, height=5, wrap='word')
        self.notes_text.pack(fill=tk.X, padx=5)
        
        # If not skipping current person, add them
        if not hasattr(self, 'skip_current_person') or not self.skip_current_person:
            self.add_current_person()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Save", command=self.save_deed).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

        self.apply_context_menus()
  
    def update_overview_text(self, text):
        """Update the overview text safely"""
        self.desc_text.configure(state='normal')
        self.desc_text.delete('1.0', tk.END)
        self.desc_text.insert('1.0', text)
        self.desc_text.configure(state='disabled')

    def add_segment(self):
        """Add current legal description as a new segment"""
        segment_data = {
            "section": self.section_var.get().strip(),
            "quarter": self.quarter_var.get(),
            "quarter_quarter": self.quarter_quarter_var.get(),
            "half": self.half_var.get(),
            "acres": self.acres_entry.get().strip(),
            "description": self.preview_label.cget("text")
        }
        
        if not segment_data["section"]:
            messagebox.showerror("Error", "Section number is required")
            return
            
        self.segments_tree.insert('', 'end', values=(
            segment_data["section"],
            segment_data["quarter"],
            segment_data["quarter_quarter"],
            segment_data["half"],
            segment_data["acres"],
            segment_data["description"]
        ))
        
        combined_desc = []
        for item in self.segments_tree.get_children():
            values = self.segments_tree.item(item)['values']
            combined_desc.append(values[5])
        self.update_overview_text(" AND ".join(combined_desc) if combined_desc else "See full legal description")
        
        self.clear_legal_controls()
        
    def clear_legal_controls(self):
        """Clear all legal description controls"""
        self.section_var.set('')
        self.quarter_var.set('')
        self.quarter_quarter_var.set('')
        self.half_var.set('')
        self.acres_entry.delete(0, tk.END)
        self.update_legal_preview()
    
    def remove_segment(self):
        """Remove selected segment from tree"""
        selected = self.segments_tree.selection()
        if not selected:
            messagebox.showwarning("Select Segment", "Please select a segment to remove")
            return
        
        self.segments_tree.delete(selected)

    def clear_segment_controls(self):
        """Clear all legal description controls for next segment"""
        self.section_var.set('')
        self.quarter_var.set('')
        self.quarter_quarter_var.set('')
        self.half_var.set('')
        self.acres_entry.delete(0, tk.END)
        self.update_legal_preview()

    def apply_context_menus(self):
        """Apply context menus to all Entry and Text widgets"""
        self.apply_context_menu_to_all_entries(self.dialog)
        create_context_menu(self.legal_text)
        create_context_menu(self.desc_text)
        create_context_menu(self.notes_text)
        
    def apply_context_menu_to_all_entries(self, container):
        """Recursively apply context menus to all Entry widgets"""
        for widget in container.winfo_children():
            if isinstance(widget, ttk.Entry):
                create_context_menu(widget)
            elif isinstance(widget, (ttk.Frame, ttk.LabelFrame, tk.Frame)):
                self.apply_context_menu_to_all_entries(widget)

    def get_person_name(self, person_id):
        """Get person's full name from database"""
        connection = sqlite3.connect('phoenix.db')
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT first_name, middle_name, last_name 
                FROM People 
                WHERE id = ?
            """, (person_id,))
            result = cursor.fetchone()
            if result:
                return ' '.join(filter(None, result))
            return "Unknown Person"
        finally:
            cursor.close()
            connection.close()

    def get_deed_types(self):
        """Get list of deed types from database"""
        connection = sqlite3.connect('phoenix.db')
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT type_name FROM DeedTypes")
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
            connection.close()

    def setup_party_tree(self, tree):
        """Configure columns for party trees"""
        columns = [
            ("ID", 50, False),
            ("First", 100, True),
            ("Middle", 100, True),
            ("Last", 100, True),
            ("Married", 100, True),
            ("Birth", 80, False),
            ("Death", 80, False)
        ]
        
        for col, width, stretch in columns:
            tree.heading(col, text=col)
            tree.column(col, width=width, stretch=stretch)

    def add_current_person(self):
        """Add current person to appropriate tree based on role"""
        if hasattr(self, 'skip_current_person') and self.skip_current_person:
            return
            
        person_info = self.get_person_full_info(self.current_person_id)
        if person_info:
            tree = self.grantors_tree if self.role_var.get() == "Grantor" else self.grantees_tree
            tree.insert('', 'end', values=(
                person_info[0],
                person_info[1],
                person_info[2] or "",
                person_info[3],
                person_info[4] or "",
                person_info[5] or "",
                person_info[6] or ""
            ))

    def on_role_change(self, event=None):
        """Handle current person's role change"""
        for tree in (self.grantors_tree, self.grantees_tree):
            for item in tree.get_children():
                tree.delete(item)
        self.add_current_person()

    def get_person_full_info(self, person_id):
        """Get person's full information from database"""
        connection = sqlite3.connect('phoenix.db')
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT id, first_name, middle_name, last_name, married_name, 
                       birth_date, death_date
                FROM People 
                WHERE id = ?
            """, (person_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def show_search_dialog(self, party_type):
        """Show dialog to search and select additional parties"""
        search_dialog = PersonSearchDialog(self.dialog, self.current_person_id)
        if search_dialog.result:
            tree = self.grantors_tree if party_type == "Grantor" else self.grantees_tree
            if self.is_person_already_added(search_dialog.result[0]):
                messagebox.showwarning("Already Added", 
                    "This person has already been added to the deed.")
                return
            
            person_info = self.get_person_full_info(search_dialog.result[0])
            if person_info:
                tree.insert('', 'end', values=tuple(
                    "" if val is None else val for val in person_info
                ))

    def is_person_already_added(self, person_id):
        """Check if person is already in either tree"""
        for tree in (self.grantors_tree, self.grantees_tree):
            for item in tree.get_children():
                if tree.item(item)['values'][0] == person_id:
                    return True
        return False

    def remove_party(self, party_type):
        """Remove selected party from tree"""
        tree = self.grantors_tree if party_type == "Grantor" else self.grantees_tree
        selected = tree.selection()
        if not selected:
            return
                
        current_count = len(tree.get_children())
        remaining_count = current_count - len(selected)

        for item in selected:
            person_id = tree.item(item)['values'][0]
            
            if person_id == self.current_person_id:
                if remaining_count == 0:
                    messagebox.showerror("Error", 
                        f"Cannot remove the only {party_type}. " +
                        f"Add another {party_type} before removing this one.")
                    return
                    
                if messagebox.askyesno("Warning", 
                    "You are about to remove the current person from this deed record. " +
                    "This means this deed will no longer appear in their record list. " +
                    "Are you sure you want to do this?"):
                    tree.delete(item)
            else:
                if remaining_count == 0:
                    messagebox.showerror("Error", 
                        f"Cannot remove the only {party_type}. " +
                        f"Add another {party_type} before removing this one.")
                    return
                tree.delete(item)

    def save_deed(self):
        """Save deed record with multiple parties and segments"""
        has_legal_text = bool(self.legal_text.get("1.0", tk.END).strip())
        has_segments = len(self.segments_tree.get_children()) > 0
        
        if not (has_legal_text or has_segments):
            messagebox.showerror("Error", "Please provide either legal text or at least one land segment")
            return

        if not self.type_var.get():
            messagebox.showerror("Error", "Please select a deed type")
            return
                
        execution_date = self.execution_date_entry.get().strip()
        recording_date = self.recording_date_entry.get().strip()
        acknowledge_date = self.acknowledge_date_entry.get().strip()

        # Validate dates
        for date_val, field_name in [
            (execution_date, "Dated"),
            (recording_date, "Recorded"),
            (acknowledge_date, "Acknowledged")
        ]:
            if date_val and not self.validate_date(date_val):
                messagebox.showerror(
                    "Error", 
                    f"Invalid {field_name} date format. Use: YYYY, MM-YYYY, or MM-DD-YYYY"
                )
                return

        amount_str = self.amount_entry.get().strip()
        try:
            amount_float = float(amount_str.replace('$', '').replace(',', '')) if amount_str else None
        except ValueError:
            messagebox.showerror("Error", "Invalid amount format")
            return

        township_id = self.get_selected_township_id()
        if not township_id:
            messagebox.showerror("Error", "Please select a valid township")
            return

        if not (self.grantors_tree.get_children() and self.grantees_tree.get_children()):
            messagebox.showerror("Error", "Both grantor and grantee are required")
            return

        try:
            connection = sqlite3.connect('phoenix.db')
            cursor = connection.cursor()
            cursor.execute("BEGIN")
            
            # Generate deed number
            year = recording_date[:4] if recording_date else "UNREC"
            cursor.execute(
                "SELECT COUNT(*) FROM Deeds WHERE recording_date LIKE ?", 
                (f"{year}%",) if year != "UNREC" else ("",)
            )
            count = cursor.fetchone()[0] + 1
            deed_number = f"{year}-{count:04d}"
            
            # Build description
            if has_segments:
                combined_desc = []
                for item in self.segments_tree.get_children():
                    values = self.segments_tree.item(item)['values']
                    combined_desc.append(values[5])
                property_description = " AND ".join(combined_desc)
            else:
                property_description = "See full legal description"

            # Insert deed record
            cursor.execute("""
                INSERT INTO Deeds (
                    deed_number, book_number, page_number, recording_date,
                    execution_date, acknowledge_date, deed_type, consideration_amount,
                    property_description, legal_text, notes, township_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deed_number,
                self.book_entry.get().strip(),
                self.page_entry.get().strip(),
                recording_date or None,
                execution_date,
                acknowledge_date or None,
                self.type_var.get(),
                amount_float,
                property_description,
                self.legal_text.get("1.0", tk.END).strip(),
                self.notes_text.get("1.0", tk.END).strip(),
                township_id
            ))
            
            deed_id = cursor.lastrowid

            # Save legal descriptions
            if has_segments:
                for idx, item in enumerate(self.segments_tree.get_children(), 1):
                    values = self.segments_tree.item(item)['values']
                    cursor.execute("""
                        INSERT INTO LegalDescriptions (
                            deed_id, township_id, section_number,
                            quarter_section, quarter_quarter, half,
                            acres, description_text, segment_order
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        deed_id,
                        township_id,
                        values[0],  # section
                        values[1],  # quarter
                        values[2],  # quarter_quarter
                        values[3],  # half
                        values[4] if values[4] else None,  # acres
                        values[5],  # description
                        idx
                    ))

            # Save deed parties
            for tree, role in [(self.grantors_tree, "Grantor"), (self.grantees_tree, "Grantee")]:
                for idx, item in enumerate(tree.get_children(), 1):
                    person_id = tree.item(item)['values'][0]
                    cursor.execute("""
                        INSERT INTO DeedParties (deed_id, person_id, party_role, party_order)
                        VALUES (?, ?, ?, ?)
                    """, (deed_id, person_id, role, idx))
            
            connection.commit()
            messagebox.showinfo("Success", "Deed record saved successfully")
            self.dialog.destroy()
            
        except sqlite3.Error as e:
            connection.rollback()
            messagebox.showerror("Error", f"Failed to save deed record: {str(e)}")
            
        finally:
            cursor.close()
            connection.close()

    def update_township_list(self, *args):
        """Update township dropdown based on selected date"""
        date = self.execution_date_entry.get().strip()
        
        if not date:
            self.township_combo['values'] = ['Enter date first to see townships']
            self.township_combo.set('Enter date first to see townships')
            self.township_combo.configure(state='disabled')
            return

        try:
            parts = date.split('-')
            if len(parts) == 3:    # MM-DD-YYYY
                year = parts[2]
            elif len(parts) == 2:   # MM-YYYY
                year = parts[1]
            else:                   # YYYY
                year = parts[0]

            connection = sqlite3.connect('phoenix.db')
            cursor = connection.cursor()
            
            try:
                year_int = int(year)
                cursor.execute("""
                    SELECT township_id, township_name, county, state
                    FROM Townships 
                    WHERE (start_date IS NULL OR CAST(start_date AS INTEGER) <= ?) 
                    AND (end_date IS NULL OR CAST(end_date AS INTEGER) >= ?)
                """, (year_int, year_int))
                
                self.townships = cursor.fetchall()
                
                if self.townships:
                    township_values = [f"{t[1]} ({t[2]}, {t[3]})" for t in self.townships]
                    self.township_combo['values'] = township_values
                    self.township_combo.set(township_values[0])
                    self.township_combo.configure(state='readonly')
                else:
                    self.township_combo['values'] = ['No townships found for this date']
                    self.township_combo.set('No townships found for this date')
                    self.township_combo.configure(state='disabled')
                    
            except ValueError as e:
                self.township_combo['values'] = ['Invalid date format']
                self.township_combo.set('Invalid date format')
                self.township_combo.configure(state='disabled')
                
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load townships: {str(e)}")
            self.township_combo['values'] = ['Error loading townships']
            self.township_combo.set('Error loading townships')
            self.township_combo.configure(state='disabled')

        finally:
            cursor.close()
            connection.close()

    def get_selected_township_id(self):
        """Get the ID of the selected township"""
        selected = self.township_combo.get()
        if selected:
            for township in self.townships:
                if f"{township[1]} ({township[2]}, {township[3]})" == selected:
                    return township[0]
        return None

    def validate_date(self, date_str):
        """Validate date format"""
        patterns = [
            r'^\d{4}$',                    # YYYY
            r'^\d{2}-\d{4}$',              # MM-YYYY
            r'^\d{2}-\d{2}-\d{4}$'         # MM-DD-YYYY
        ]
        return any(re.match(pattern, date_str) for pattern in patterns)

    def update_legal_preview(self, event=None):
        """Update the preview of legal description based on selected values"""
        try:
            section = self.section_var.get().strip()
            quarter = self.quarter_var.get().strip()
            quarter_quarter = self.quarter_quarter_var.get().strip()
            half = self.half_var.get().strip()
            acres = self.acres_entry.get().strip()
            
            quarter_abbrev = {
                "Northeast Quarter": "NE 1/4",
                "Northwest Quarter": "NW 1/4",
                "Southeast Quarter": "SE 1/4",
                "Southwest Quarter": "SW 1/4"
            }
            
            half_abbrev = {
                "North Half": "N 1/2",
                "South Half": "S 1/2",
                "East Half": "E 1/2",
                "West Half": "W 1/2"
            }
            
            township_info = None
            selected_township = self.township_combo.get()
            if selected_township and self.townships:
                for t in self.townships:
                    if f"{t[1]} ({t[2]}, {t[3]})" == selected_township:
                        township_info = t
                        break
            
            description_parts = []
            
            if half and quarter:
                description_parts.append(half_abbrev.get(half, half))
                description_parts.append("of the")
                description_parts.append(quarter_abbrev.get(quarter, quarter))
            else:
                if quarter_quarter:
                    description_parts.append(quarter_abbrev.get(quarter_quarter, quarter_quarter))
                    if quarter:
                        description_parts.append("of the")
                        description_parts.append(quarter_abbrev.get(quarter, quarter))
                elif quarter:
                    description_parts.append(quarter_abbrev.get(quarter, quarter))
                elif half:
                    description_parts.append(half_abbrev.get(half, half))
            
            if description_parts:
                description_parts.append("of")
                
            if section:
                description_parts.append(f"Section {section}")
            
            if township_info:
                description_parts.append(f"in {township_info[1]},")
                description_parts.append(f"{township_info[2]},")
                description_parts.append(f"{township_info[3]}")
            
            description = " ".join(description_parts)
            
            if acres:
                try:
                    acres_float = float(acres)
                    is_partial = False
                    if half and quarter:  # Half of a quarter = 80 acres
                        is_partial = acres_float != 80
                    elif quarter_quarter:  # Quarter-quarter = 40 acres
                        is_partial = acres_float != 40
                    elif quarter:  # Full quarter = 160 acres
                        is_partial = acres_float != 160
                    elif half:  # Half section = 320 acres
                        is_partial = acres_float != 320
                        
                    if is_partial and description:
                        description = f"{acres_float:.2f} acres, part of the {description}"
                    else:
                        description = f"{acres_float:.2f} acres, being the {description}"
                except ValueError:
                    pass
            
            if description:
                self.preview_label.config(text=description)
            else:
                self.preview_label.config(text="")
                
        except Exception as e:
            print(f"Error updating preview: {e}")
            self.preview_label.config(text="Error generating preview")

class PersonSearchDialog:
    def __init__(self, parent, current_person_id):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Search Person")
        self.dialog.geometry("800x400")
        self.current_person_id = current_person_id
        self.result = None
        
        search_frame = ttk.Frame(self.dialog)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="First Name:").pack(side=tk.LEFT, padx=5)
        self.first_name_entry = ttk.Entry(search_frame)
        self.first_name_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(search_frame, text="Last Name:").pack(side=tk.LEFT, padx=5)
        self.last_name_entry = ttk.Entry(search_frame)
        self.last_name_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_frame, text="Search", 
                  command=self.search_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Clear", 
                  command=self.clear_search).pack(side=tk.LEFT, padx=5)
        
        self.tree = ttk.Treeview(self.dialog,
            columns=("ID", "First Name", "Middle Name", "Last Name", "Married Name", 
                    "Birth Date", "Death Date"),
            show='headings',
            height=15)
            
        for col, width in [("ID", 50), ("First Name", 100), ("Middle Name", 100),
                          ("Last Name", 100), ("Married Name", 100),
                          ("Birth Date", 80), ("Death Date", 80)]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tree.bind('<Double-1>', lambda e: self.select_person())
        ttk.Button(self.dialog, text="Select", 
                  command=self.select_person).pack(pady=5)
        
        self.dialog.transient(parent)
        self.dialog.grab_set()
        parent.wait_window(self.dialog)
    
    def search_person(self):
        first_name = self.first_name_entry.get().strip()
        last_name = self.last_name_entry.get().strip()
        
        connection = sqlite3.connect('phoenix.db')
        cursor = connection.cursor()
        
        try:
            results = search_people(
                cursor,
                columns="id, first_name, middle_name, last_name, married_name, birth_date, death_date",
                first_name=first_name,
                last_name=last_name,
            )
            results = [r for r in results if r[0] != self.current_person_id]
            
            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in results:
                self.tree.insert('', 'end', values=row)

        finally:
            cursor.close()
            connection.close()
    
    def clear_search(self):
        self.first_name_entry.delete(0, tk.END)
        self.last_name_entry.delete(0, tk.END)
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def select_person(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a person")
            return
            
        values = self.tree.item(selected[0])['values']
        self.result = (values[0], f"{values[1]} {values[2] or ''} {values[3]}".strip())
        self.dialog.destroy()


def add_deed_record(parent, person_id):
    """Create and show the Add Deed dialog"""
    dialog = AddDeedDialog(parent, person_id)
    parent.wait_window(dialog.dialog)