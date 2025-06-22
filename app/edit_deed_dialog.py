import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys
import re
from datetime import datetime

#Local Imports
from app.config import PATHS, DB_PATH
from app.add_deed_dialog import AddDeedDialog  # Import the base class

class EditDeedDialog(AddDeedDialog):
    """Dialog for editing deed records. Inherits from AddDeedDialog."""
    def __init__(self, parent, current_person_id, deed_id):
        self.deed_id = deed_id
        self.skip_current_person = True    # Prevent automatic addition
        super().__init__(parent, current_person_id)
        self.dialog.title("Edit Deed Record")
        
        # Clear any existing data in trees (shouldn't be needed with skip_current_person, but safe)
        for tree in (self.grantors_tree, self.grantees_tree):
            for item in tree.get_children():
                tree.delete(item)
                
        # Load existing deed data
        self.load_deed_data()
            
    def load_deed_data(self):
        """Load existing deed data into the form"""
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        
        try:
            # Load the deed details including property_description
            cursor.execute("""
                SELECT deed_type, execution_date, acknowledge_date, recording_date,
                       consideration_amount, book_number, page_number, 
                       property_description, legal_text, notes, township_id
                FROM Deeds 
                WHERE deed_id = ?
            """, (self.deed_id,))
            
            deed_data = cursor.fetchone()
            if deed_data:
                
                cursor.execute("""
                    SELECT dp.party_role
                    FROM DeedParties dp
                    WHERE dp.deed_id = ? AND dp.person_id = ?
                """, (self.deed_id, self.current_person_id))

                party_role = cursor.fetchone()
                if party_role:
                    self.role_var.set(party_role[0])  # Set the correct role

                # Handle basic deed fields first
                if deed_data[1]:  # execution_date
                    self.execution_date_entry.insert(0, deed_data[1])
                    self.update_township_list()
                    if deed_data[10]:  # township_id
                        cursor.execute("""
                            SELECT township_name, county, state
                            FROM Townships 
                            WHERE township_id = ?
                        """, (deed_data[10],))
                        township_info = cursor.fetchone()
                        if township_info:
                            self.township_combo.set(f"{township_info[0]} ({township_info[1]}, {township_info[2]})")
                
                # Set other deed fields
                self.type_combo.set(deed_data[0])
                if deed_data[2]: self.acknowledge_date_entry.insert(0, deed_data[2])
                if deed_data[3]: self.recording_date_entry.insert(0, deed_data[3])
                if deed_data[4] is not None: self.amount_entry.insert(0, str(deed_data[4]))
                if deed_data[5]: self.book_entry.insert(0, deed_data[5])
                if deed_data[6]: self.page_entry.insert(0, deed_data[6])
                if deed_data[7]: self.desc_text.insert("1.0", deed_data[7])    # property_description
                if deed_data[8]: self.legal_text.insert("1.0", deed_data[8])   # legal_text
                if deed_data[9]: self.notes_text.insert("1.0", deed_data[9])   # notes
            
            # Load legal description segments
            cursor.execute("""
                SELECT section_number, quarter_section, quarter_quarter, half,
                       acres, description_text
                FROM LegalDescriptions
                WHERE deed_id = ?
                ORDER BY segment_order
            """, (self.deed_id,))
            
            segments = cursor.fetchall()
            
            if segments:
                # Clear any existing segments
                for item in self.segments_tree.get_children():
                    self.segments_tree.delete(item)
                
                if len(segments) == 1:  # Single parcel
                    segment = segments[0]
                    # Load into controls
                    if segment[0]: self.section_var.set(str(segment[0]))
                    if segment[1]: self.quarter_var.set(segment[1])
                    if segment[2]: self.quarter_quarter_var.set(segment[2])
                    if segment[3]: self.half_var.set(segment[3])
                    if segment[4]: self.acres_entry.insert(0, str(segment[4]))
                    self.update_legal_preview()
                else:  # Multiple parcels
                    for segment in segments:
                        self.segments_tree.insert('', 'end', values=(
                            segment[0],  # section_number
                            segment[1] if segment[1] else "",  # quarter_section
                            segment[2] if segment[2] else "",  # quarter_quarter
                            segment[3] if segment[3] else "",  # half
                            segment[4] if segment[4] else "",  # acres
                            segment[5] if segment[5] else ""   # description_text
                        ))
            
            # Load parties
            cursor.execute("""
                SELECT p.id, p.first_name, p.middle_name, p.last_name, 
                       p.married_name, p.birth_date, p.death_date, dp.party_role
                FROM DeedParties dp
                JOIN People p ON dp.person_id = p.id
                WHERE dp.deed_id = ?
                ORDER BY dp.party_order
            """, (self.deed_id,))
            
            for party in cursor.fetchall():
                tree = self.grantors_tree if party[7] == 'Grantor' else self.grantees_tree
                tree.insert('', 'end', values=(
                    party[0],           # ID
                    party[1],           # First name
                    party[2] or "",     # Middle name
                    party[3],           # Last name
                    party[4] or "",     # Married name
                    party[5] or "",     # Birth date
                    party[6] or ""      # Death date
                ))
                
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load deed data: {str(e)}")
            print(f"Database error: {e}")  # For debugging
            
        finally:
            cursor.close()
            connection.close()
    
    def save_deed(self):
        """Save changes to deed record"""
        # First check if this is a multi-segment deed
        has_multiple_segments = len(self.segments_tree.get_children()) > 1
        has_legal_text = bool(self.legal_text.get("1.0", tk.END).strip())
        has_control_values = bool(self.section_var.get().strip())
        
        if not has_multiple_segments:
            if not (has_legal_text or has_control_values):
                messagebox.showerror("Error", "Please provide either legal text or use the Legal Description controls")
                return

        # Validate required fields
        if not self.type_var.get():
            messagebox.showerror("Error", "Please select a deed type")
            return
                
        # Get and validate dates
        execution_date = self.execution_date_entry.get().strip()
        if not execution_date or not self.validate_date(execution_date):
            messagebox.showerror("Error", "Please enter a valid date for Dated field (YYYY, MM-YYYY, or MM-DD-YYYY)")
            return

        recording_date = self.recording_date_entry.get().strip()
        if recording_date and not self.validate_date(recording_date):
            messagebox.showerror("Error", "Please enter a valid date for Recorded field (YYYY, MM-YYYY, or MM-DD-YYYY)")
            return

        # Acknowledge date is optional but must be valid if provided
        acknowledge_date = self.acknowledge_date_entry.get().strip()
        if acknowledge_date and not self.validate_date(acknowledge_date):
            messagebox.showerror("Error", "Please enter a valid date for Acknowledged field (YYYY, MM-YYYY, or MM-DD-YYYY)")
            return
                
        # Handle amount - now optional
        amount_str = self.amount_entry.get().strip()
        amount_float = None
        if amount_str:
            try:
                amount_float = float(amount_str.replace('$', '').replace(',', ''))
            except ValueError:
                messagebox.showerror("Error", "Invalid amount format. Please enter a valid number or leave empty.")
                return

        # Get and validate township_id
        township_id = self.get_selected_township_id()
        if not township_id:
            messagebox.showerror("Error", "Please select a valid township")
            return

        # Validate section number if using controls
        section_number = None
        acres_float = None
        if has_control_values:
            section_number = self.section_var.get().strip()
            try:
                section_number = int(section_number)
                if not (1 <= section_number <= 36):
                    messagebox.showerror("Error", "Section number must be between 1 and 36")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid section number")
                return

            # Handle optional acres value
            acres = self.acres_entry.get().strip()
            if acres:
                try:
                    acres_float = float(acres)
                    if acres_float <= 0:
                        messagebox.showerror("Error", "Acres must be a positive number")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Invalid acres format")
                    return

        try:
            connection = sqlite3.connect('phoenix.db')
            cursor = connection.cursor()
            
            # Start transaction
            cursor.execute("BEGIN")
            
            # Update deed record
            cursor.execute("""
                UPDATE Deeds 
                SET deed_type = ?, 
                    execution_date = ?, 
                    acknowledge_date = ?,
                    recording_date = ?, 
                    consideration_amount = ?,
                    book_number = ?, 
                    page_number = ?, 
                    property_description = ?,
                    legal_text = ?, 
                    notes = ?, 
                    township_id = ?
                WHERE deed_id = ?
            """, (
                self.type_var.get(),
                execution_date,
                acknowledge_date if acknowledge_date else None,
                recording_date if recording_date else None,
                amount_float,
                self.book_entry.get().strip(),
                self.page_entry.get().strip(),
                self.preview_label.cget("text") if has_control_values else "See full legal description",
                self.legal_text.get("1.0", tk.END).strip(),  # Add this line
                self.notes_text.get("1.0", tk.END).strip(),
                township_id,
                self.deed_id
            ))

            # Check if LegalDescriptions record exists
            cursor.execute("SELECT COUNT(*) FROM LegalDescriptions WHERE deed_id = ?", 
                         (self.deed_id,))
            has_legal_record = cursor.fetchone()[0] > 0

            if has_legal_record:
                # Update existing LegalDescriptions record
                if has_control_values:
                    cursor.execute("""
                        UPDATE LegalDescriptions
                        SET township_id = ?,
                            section_number = ?,
                            quarter_section = ?,
                            quarter_quarter = ?,
                            half = ?,
                            acres = ?,
                            description_text = ?
                        WHERE deed_id = ?
                    """, (
                        township_id,
                        section_number,
                        self.quarter_var.get() or None,
                        self.quarter_quarter_var.get() or None,
                        self.half_var.get() or None,
                        acres_float,
                        self.preview_label.cget("text"),  # Save the formatted preview text
                        self.deed_id
                    ))
            else:
                # Create new LegalDescriptions record
                cursor.execute("""
                    INSERT INTO LegalDescriptions (
                        deed_id, township_id, section_number, quarter_section,
                        quarter_quarter, half, acres, description_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.deed_id,
                    township_id,
                    section_number,
                    self.quarter_var.get() or None,
                    self.quarter_quarter_var.get() or None,
                    self.half_var.get() or None,
                    acres_float,
                    self.preview_label.cget("text"),  # Save the formatted preview text
                    ))

            # Update deed parties
            # First delete existing parties
            cursor.execute("DELETE FROM DeedParties WHERE deed_id = ?", (self.deed_id,))
            
            # Insert all grantors
            for idx, item in enumerate(self.grantors_tree.get_children()):
                person_id = self.grantors_tree.item(item)['values'][0]
                cursor.execute("""
                    INSERT INTO DeedParties (deed_id, person_id, party_role, party_order)
                    VALUES (?, ?, ?, ?)
                """, (self.deed_id, person_id, "Grantor", idx + 1))
            
            # Insert all grantees
            for idx, item in enumerate(self.grantees_tree.get_children()):
                person_id = self.grantees_tree.item(item)['values'][0]
                cursor.execute("""
                    INSERT INTO DeedParties (deed_id, person_id, party_role, party_order)
                    VALUES (?, ?, ?, ?)
                """, (self.deed_id, person_id, "Grantee", idx + 1))
            
            connection.commit()
            messagebox.showinfo("Success", "Deed record updated successfully")
            self.dialog.destroy()
            
        except sqlite3.Error as e:
            connection.rollback()
            messagebox.showerror("Error", f"Failed to update deed record: {str(e)}")
            print(f"Database error: {e}")  # For debugging
        except Exception as e:
            connection.rollback()
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            print(f"Unexpected error: {e}")  # For debugging
        finally:
            cursor.close()
            connection.close()


def edit_deed_record(parent, person_id, deed_id):
    """Create and show the Edit Deed dialog"""
    dialog = EditDeedDialog(parent, person_id, deed_id)
    parent.wait_window(dialog.dialog)