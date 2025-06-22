import tkinter as tk
from tkinter import ttk, messagebox
import json

class GeoDataDialog:
    def __init__(self, parent, record_type, record_id, segment_id=None):
        """Initialize the dialog for managing geographic features"""
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Geographic Data Manager")
        self.dialog.geometry("900x700")
        
        # Initialize instance variables
        self.parent = parent
        self.record_type = record_type
        self.record_id = record_id
        self.segment_id = segment_id
        self.current_feature = None
        
        # Create database connection and manager
        self.connection = sqlite3.connect('phoenix.db')
        self.geo_manager = GeoDataManager(self.connection)
        
        # Create the interface
        self.create_widgets()
        
        # Load existing features
        self.load_existing_features()
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
    def create_widgets(self):
        """Create all dialog widgets"""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Existing Features Section
        features_frame = ttk.LabelFrame(main_frame, text="Geographic Features")
        features_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Features treeview
        columns = ("ID", "Type", "Description", "Status")
        self.features_tree = ttk.Treeview(
            features_frame, 
            columns=columns,
            show='headings',
            height=6
        )
        
        # Configure columns
        self.features_tree.column("ID", width=50, stretch=False)
        self.features_tree.column("Type", width=100)
        self.features_tree.column("Description", width=300)
        self.features_tree.column("Status", width=50, stretch=False)
        
        # Configure headings
        self.features_tree.heading("ID", text="ID")
        self.features_tree.heading("Type", text="Type")
        self.features_tree.heading("Description", text="Description")
        self.features_tree.heading("Status", text="Status")
        
        # Add scrollbar
        tree_scroll = ttk.Scrollbar(features_frame, orient="vertical", 
                                  command=self.features_tree.yview)
        self.features_tree.configure(yscrollcommand=tree_scroll.set)
        
        # Pack tree and scrollbar
        self.features_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Feature type selection
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="Feature Type:").pack(side=tk.LEFT, padx=5)
        self.feature_type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.feature_type_var,
            values=[info['name'] for info in GeoDataManager.FEATURE_TYPES.values()],
            state='readonly',
            width=30
        )
        self.type_combo.pack(side=tk.LEFT, padx=5)
        self.type_combo.bind('<<ComboboxSelected>>', self.on_type_selected)
        
        # Feature buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add New", 
                  command=self.add_feature).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Edit", 
                  command=self.edit_feature).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", 
                  command=self.delete_feature).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="View on Map", 
                  command=self.view_on_map).pack(side=tk.LEFT, padx=2)
        
        # Coordinate entry section
        coords_frame = ttk.LabelFrame(main_frame, text="Coordinates")
        coords_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.coords_text = tk.Text(coords_frame, height=6)
        self.coords_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(coords_frame, 
                 text="Enter coordinates as longitude,latitude pairs, one per line",
                 font=('Arial', 8, 'italic')).pack(pady=(0, 5))
        
        # Description entry
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(desc_frame, text="Description:").pack(side=tk.LEFT, padx=5)
        self.description_entry = ttk.Entry(desc_frame, width=50)
        self.description_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.preview_canvas = tk.Canvas(
            preview_frame,
            width=400,
            height=300,
            bg='white'
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Save", 
                  command=self.save_changes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def load_existing_features(self):
        """Load and display existing geographic features"""
        try:
            features = self.geo_manager.get_features_for_record(
                self.record_type,
                self.record_id,
                self.segment_id
            )
            
            # Clear existing items
            for item in self.features_tree.get_children():
                self.features_tree.delete(item)
            
            # Add features to tree
            for feature in features:
                geojson_id, geojson_text, feature_type, description, _ = feature
                type_info = GeoDataManager.FEATURE_TYPES.get(feature_type, {})
                
                self.features_tree.insert('', 'end', values=(
                    geojson_id,
                    type_info.get('name', feature_type),
                    description or "No description",
                    type_info.get('icon', '🗺️')
                ))
                
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load features: {str(e)}")


    def on_type_selected(self, event=None):
        """Handle feature type selection"""
        selected_type = self.feature_type_var.get()
        
        # Clear and update coordinate instructions
        self.coords_text.delete('1.0', tk.END)
        
        # Add appropriate instructions based on type
        if selected_type == "Point Location":
            self.coords_text.insert('1.0', "Enter as: longitude,latitude")
        elif selected_type == "Line Feature":
            self.coords_text.insert('1.0', "Enter coordinates for line, one pair per line:\nlongitude1,latitude1\nlongitude2,latitude2")
        elif selected_type == "Boundary":
            self.coords_text.insert('1.0', "Enter boundary coordinates, one pair per line:\nlongitude1,latitude1\nlongitude2,latitude2\n...")
        
        # Update preview if coordinates exist
        self.update_preview()

    def add_feature(self):
        """Add a new geographic feature"""
        # Clear current selections
        self.current_feature = None
        self.feature_type_var.set('')
        self.coords_text.delete('1.0', tk.END)
        self.description_entry.delete(0, tk.END)
        
        # Enable and focus type selection
        self.type_combo.configure(state='readonly')
        self.type_combo.focus()

    def edit_feature(self):
        """Edit selected feature"""
        selected = self.features_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", 
                                 "Please select a feature to edit.")
            return
            
        # Get feature details
        feature_id = self.features_tree.item(selected[0])['values'][0]
        
        try:
            # Fetch feature data
            self.cursor.execute("""
                SELECT gd.feature_type, gd.geojson_text, gd.description
                FROM GeoJSONData gd
                WHERE gd.geojson_id = ?
            """, (feature_id,))
            
            feature_data = self.cursor.fetchone()
            if feature_data:
                feature_type, geojson_text, description = feature_data
                
                # Set current feature
                self.current_feature = feature_id
                
                # Update type selection
                type_info = [info for info in GeoDataManager.FEATURE_TYPES.items() 
                           if info[0] == feature_type][0]
                self.feature_type_var.set(type_info[1]['name'])
                
                # Load coordinates
                try:
                    geojson = json.loads(geojson_text)
                    coords = self.extract_coordinates(geojson)
                    self.coords_text.delete('1.0', tk.END)
                    self.coords_text.insert('1.0', coords)
                except json.JSONDecodeError:
                    messagebox.showerror("Error", "Invalid GeoJSON data")
                    return
                
                # Set description
                self.description_entry.delete(0, tk.END)
                if description:
                    self.description_entry.insert(0, description)
                
                # Update preview
                self.update_preview()
                
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load feature data: {str(e)}")

    def delete_feature(self):
        """Delete selected feature"""
        selected = self.features_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", 
                                 "Please select a feature to delete.")
            return
            
        feature_id = self.features_tree.item(selected[0])['values'][0]
        
        if messagebox.askyesno("Confirm Delete", 
                              "Are you sure you want to delete this feature?"):
            try:
                self.geo_manager.delete_feature(feature_id)
                self.load_existing_features()
                
                # Clear form if we were editing this feature
                if self.current_feature == feature_id:
                    self.clear_form()
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete feature: {str(e)}")

    def clear_form(self):
        """Clear all form fields"""
        self.current_feature = None
        self.feature_type_var.set('')
        self.coords_text.delete('1.0', tk.END)
        self.description_entry.delete(0, tk.END)
        self.preview_canvas.delete('all')

    def extract_coordinates(self, geojson):
        """Extract coordinates from GeoJSON and format for display"""
        try:
            coords = []
            geom = geojson['geometry']
            
            if geom['type'] == 'Point':
                coords = [f"{geom['coordinates'][0]},{geom['coordinates'][1]}"]
            elif geom['type'] == 'LineString':
                coords = [f"{c[0]},{c[1]}" for c in geom['coordinates']]
            elif geom['type'] == 'Polygon':
                # Skip the last coordinate if it's the same as the first (closed polygon)
                ring = geom['coordinates'][0]
                if ring[0] == ring[-1]:
                    ring = ring[:-1]
                coords = [f"{c[0]},{c[1]}" for c in ring]
                
            return '\n'.join(coords)
            
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid GeoJSON structure: {str(e)}")

    def update_preview(self, event=None):
        """Update the preview canvas with current coordinates"""
        # Clear existing preview
        self.preview_canvas.delete('all')
        
        # Get coordinates
        coords_text = self.coords_text.get('1.0', tk.END).strip()
        if not coords_text:
            return
            
        try:
            # Parse coordinates
            coords = []
            for line in coords_text.split('\n'):
                if line.strip():
                    lon, lat = map(float, line.strip().split(','))
                    coords.append((lon, lat))
            
            if not coords:
                return
                
            # Calculate scaling for preview
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            # Scale coordinates to fit canvas
            scaled_coords = self.scale_coordinates(coords, canvas_width, canvas_height)
            
            # Draw based on feature type
            feature_type = self.feature_type_var.get()
            
            if feature_type == "Point Location":
                x, y = scaled_coords[0]
                self.preview_canvas.create_oval(x-5, y-5, x+5, y+5, fill='red')
                
            elif feature_type == "Line Feature":
                for i in range(len(scaled_coords)-1):
                    x1, y1 = scaled_coords[i]
                    x2, y2 = scaled_coords[i+1]
                    self.preview_canvas.create_line(x1, y1, x2, y2, fill='blue', width=2)
                    
            elif feature_type == "Boundary":
                # Create polygon
                flat_coords = [coord for point in scaled_coords for coord in point]
                self.preview_canvas.create_polygon(flat_coords, 
                                                fill='lightblue', 
                                                outline='blue', 
                                                stipple='gray50')
                
        except (ValueError, IndexError) as e:
            # Invalid coordinate format - clear preview
            self.preview_canvas.delete('all')

    def scale_coordinates(self, coords, width, height):
        """Scale coordinates to fit canvas"""
        # Find bounds
        min_lon = min(c[0] for c in coords)
        max_lon = max(c[0] for c in coords)
        min_lat = min(c[1] for c in coords)
        max_lat = max(c[1] for c in coords)
        
        # Add padding
        padding = 20
        effective_width = width - (2 * padding)
        effective_height = height - (2 * padding)
        
        # Calculate scaling factors
        lon_range = max_lon - min_lon
        lat_range = max_lat - min_lat
        
        if lon_range == 0:
            lon_scale = 1
        else:
            lon_scale = effective_width / lon_range
            
        if lat_range == 0:
            lat_scale = 1
        else:
            lat_scale = effective_height / lat_range
        
        # Use the smaller scale to maintain aspect ratio
        scale = min(lon_scale, lat_scale)
        
        # Scale and translate coordinates
        scaled_coords = []
        for lon, lat in coords:
            x = padding + ((lon - min_lon) * scale)
            y = height - (padding + ((lat - min_lat) * scale))  # Flip Y for canvas coordinates
            scaled_coords.append((x, y))
            
        return scaled_coords

    def view_on_map(self):
        """Open the selected feature in the mapping interface"""
        selected = self.features_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", 
                                 "Please select a feature to view.")
            return
            
        # TODO: Implement map viewer integration
        messagebox.showinfo("Not Implemented", 
                          "Map viewer integration coming soon!")

    def save_changes(self):
        """Save current feature data"""
        # Validate required fields
        if not self.feature_type_var.get():
            messagebox.showerror("Error", "Please select a feature type.")
            return
            
        coords_text = self.coords_text.get('1.0', tk.END).strip()
        if not coords_text:
            messagebox.showerror("Error", "Please enter coordinates.")
            return
            
        # Get feature type key from name
        type_name = self.feature_type_var.get()
        feature_type = next(
            (key for key, info in GeoDataManager.FEATURE_TYPES.items() 
             if info['name'] == type_name),
            None
        )
        
        if not feature_type:
            messagebox.showerror("Error", "Invalid feature type.")
            return
            
        try:
            description = self.description_entry.get().strip()
            
            if self.current_feature:
                # Update existing feature
                self.geo_manager.update_feature(
                    self.current_feature,
                    feature_type,
                    coords_text,
                    description
                )
            else:
                # Add new feature
                self.geo_manager.save_feature(
                    self.record_type,
                    self.record_id,
                    feature_type,
                    coords_text,
                    description,
                    self.segment_id
                )
            
            self.load_existing_features()
            self.clear_form()
            messagebox.showinfo("Success", "Feature saved successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save feature: {str(e)}")

    def __del__(self):
        """Clean up database connection"""
        try:
            self.connection.close()
        except:
            pass