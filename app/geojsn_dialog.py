import tkinter as tk
from tkinter import ttk, messagebox
from property_boundary import PropertyBoundaryCalculator
import sqlite3

class AddGeoJSONDialog:
    def __init__(self, parent, record_type, record_id, township_id=None):
        """
        Initialize the dialog for adding GeoJSON data.
        
        Args:
            parent: Parent window
            record_type: "deed" or "tax"
            record_id: ID of the deed or tax record
            township_id: Optional township ID (can be fetched from record if not provided)
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Property Boundary")
        self.dialog.geometry("800x600")
        
        self.parent = parent
        self.record_type = record_type
        self.record_id = record_id
        self.connection = sqlite3.connect('phoenix.db')
        self.cursor = self.connection.cursor()
        
        # Fetch record details
        self.record_info = self.fetch_record_info()
        if not township_id and self.record_info:
            self.township_id = self.record_info.get('township_id')
        else:
            self.township_id = township_id
            
        self.calculator = PropertyBoundaryCalculator(self.connection)
        self.create_widgets()

    def fetch_record_info(self):
        """Fetch record details based on record type."""
        try:
            if self.record_type == "deed":
                query = """
                    SELECT d.township_id, ld.description_text, ld.section_number,
                           ld.quarter_section, ld.quarter_quarter, ld.half
                    FROM Deeds d
                    LEFT JOIN LegalDescriptions ld ON d.deed_id = ld.deed_id
                    WHERE d.deed_id = ?
                """
            else:  # tax record
                query = """
                    SELECT tr.township_id, tr.description as description_text,
                           tr.section as section_number
                    FROM Tax_Records tr
                    WHERE tr.record_id = ?
                """
            
            self.cursor.execute(query, (self.record_id,))
            result = self.cursor.fetchone()
            
            if result:
                # Convert to dictionary with standardized keys
                if self.record_type == "deed":
                    return {
                        'township_id': result[0],
                        'description_text': result[1],
                        'section_number': result[2],
                        'quarter_section': result[3],
                        'quarter_quarter': result[4],
                        'half': result[5]
                    }
                else:
                    return {
                        'township_id': result[0],
                        'description_text': result[1],
                        'section_number': result[2]
                    }
            return None
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error fetching record info: {e}")
            return None

    def create_widgets(self):
        """Create the dialog widgets."""
        # Method selection frame
        method_frame = ttk.LabelFrame(self.dialog, text="Boundary Creation Method")
        method_frame.pack(fill='x', padx=10, pady=5)
        
        self.method_var = tk.StringVar(value="calculate")
        ttk.Radiobutton(
            method_frame, 
            text="Calculate from Legal Description", 
            variable=self.method_var, 
            value="calculate",
            command=self.toggle_method
        ).pack(anchor='w', padx=5, pady=2)
        
        ttk.Radiobutton(
            method_frame, 
            text="Enter Coordinates Manually", 
            variable=self.method_var, 
            value="manual",
            command=self.toggle_method
        ).pack(anchor='w', padx=5, pady=2)

        # Description display
        desc_frame = ttk.LabelFrame(self.dialog, text="Legal Description")
        desc_frame.pack(fill='x', padx=10, pady=5)
        
        if self.record_info and self.record_info.get('description_text'):
            ttk.Label(
                desc_frame, 
                text=self.record_info['description_text'],
                wraplength=700
            ).pack(padx=5, pady=5)
        
        # Calculation frame
        self.calc_frame = ttk.LabelFrame(self.dialog, text="Calculate Boundary")
        self.calc_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(
            self.calc_frame,
            text="Calculate from Description",
            command=self.calculate_boundary
        ).pack(pady=10)

        # Manual entry frame
        self.manual_frame = ttk.LabelFrame(self.dialog, text="Manual Coordinate Entry")
        ttk.Label(
            self.manual_frame,
            text="Enter coordinates as longitude,latitude pairs (one pair per line):"
        ).pack(padx=5, pady=5)
        
        self.coords_text = tk.Text(self.manual_frame, height=10)
        self.coords_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Preview frame
        self.preview_frame = ttk.LabelFrame(self.dialog, text="Preview")
        self.preview_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Add preview map placeholder
        self.preview_text = tk.Text(self.preview_frame, height=10, width=60)
        self.preview_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self.save_geojson
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side='left', padx=5)

        # Initialize view
        self.toggle_method()

    def toggle_method(self):
        """Toggle between calculation and manual entry methods."""
        if self.method_var.get() == "calculate":
            self.calc_frame.pack(fill='x', padx=10, pady=5)
            self.manual_frame.pack_forget()
        else:
            self.calc_frame.pack_forget()
            self.manual_frame.pack(fill='x', padx=10, pady=5)

    def calculate_boundary(self):
        """Calculate boundary from legal description."""
        if not self.record_info or not self.record_info.get('description_text'):
            messagebox.showerror("Error", "No legal description available.")
            return
            
        try:
            geojson = self.calculator.try_calculate_boundary(
                self.record_info['description_text'],
                self.township_id
            )
            
            if geojson:
                self.preview_boundary(geojson)
                self.result_geojson = geojson
            else:
                messagebox.showerror("Error", "Could not calculate boundary from description.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Calculation failed: {str(e)}")

    def preview_boundary(self, geojson):
        """Display the boundary preview."""
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', str(geojson))
        
        # Here you could add code to display on a map if desired

    def save_geojson(self):
        """Save the GeoJSON to the database."""
        try:
            geojson_text = None
            
            if self.method_var.get() == "calculate" and hasattr(self, 'result_geojson'):
                geojson_text = str(self.result_geojson)
            else:  # manual entry
                coords_text = self.coords_text.get('1.0', 'end').strip()
                if coords_text:
                    geojson_text = coords_text

            if not geojson_text:
                messagebox.showerror("Error", "No boundary data to save.")
                return

            # Save to GeoJSONData and create link
            self.cursor.execute("""
                INSERT INTO GeoJSONData (geojson_text, description)
                VALUES (?, ?)
            """, (geojson_text, self.record_info.get('description_text')))
            
            geojson_id = self.cursor.lastrowid
            
            self.cursor.execute("""
                INSERT INTO GeoJSONLink (geojson_id, record_type, record_id)
                VALUES (?, ?, ?)
            """, (geojson_id, self.record_type, self.record_id))
            
            self.connection.commit()
            messagebox.showinfo("Success", "Boundary data saved successfully.")
            self.dialog.destroy()
            
        except Exception as e:
            self.connection.rollback()
            messagebox.showerror("Error", f"Failed to save boundary data: {str(e)}")

    def __del__(self):
        """Cleanup database connection."""
        try:
            self.connection.close()
        except:
            pass