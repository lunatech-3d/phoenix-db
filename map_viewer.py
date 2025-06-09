import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import json
import requests
from PIL import Image, ImageTk
from io import BytesIO
import math

# Constants for OpenStreetMap
OSM_TILE_SIZE = 256  # Standard OSM tile size in pixels
MAX_ZOOM_LEVEL = 19
MIN_ZOOM_LEVEL = 1


class OSMTileManager:
    def __init__(self):
        self.tile_cache = {}
        
    def get_tile(self, x, y, zoom):
        """Fetch and cache a single OSM tile"""
        tile_key = (x, y, zoom)
        
        # Return cached tile if available
        if tile_key in self.tile_cache:
            return self.tile_cache[tile_key]
            
        # Construct OSM URL
        url = f"https://a.tile.openstreetmap.org/{zoom}/{x}/{y}.png"
        
        try:
            # Fetch tile
            response = requests.get(url)
            image = Image.open(BytesIO(response.content))
            photo = ImageTk.PhotoImage(image)
            
            # Cache the tile
            self.tile_cache[tile_key] = photo
            return photo
            
        except Exception as e:
            print(f"Error fetching tile: {e}")
            return None



class MapViewer:
    def __init__(self, parent):
        print("Initializing MapViewer...")
        try:
            self.connection = sqlite3.connect('phoenix.db')
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {str(e)}")
            raise
                
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("GeoData Viewer")
        self.dialog.geometry("1200x800")

        # Map center and zoom settings
        self.center_lat = 42.371427
        self.center_lon = -83.468213
        self.current_zoom = 15
        self.scale_factor = 1.0
        self.pan_offset = (0, 0)
        self.zoom_levels = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0]
        self.current_zoom_index = 2  # Start at 1.0
        
        # Initialize OSM tile manager
        self.tile_manager = OSMTileManager()
        
        # Main container with fixed size
        self.main_frame = ttk.Frame(self.dialog, width=1200, height=800)
        self.main_frame.pack(fill='both', expand=True)
        self.main_frame.pack_propagate(False)  # Prevent frame from shrinking

        """
        # Left panel for controls
        self.control_panel = ttk.Frame(self.main_frame, width=250)
        self.control_panel.pack(side='left', fill='y', padx=5, pady=5)
        self.control_panel.pack_propagate(False)  # Prevent shrinking

        # Create layer controls
        self.create_layer_controls()
        """

        # Map frame with fixed size
        self.map_frame = ttk.Frame(self.main_frame, width=950, height=800)
        self.map_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        self.map_frame.grid_propagate(False)  # Prevent shrinking
        
        # Canvas for map display
        self.canvas = tk.Canvas(self.map_frame, width=950, height=800)
        self.canvas.pack(fill='both', expand=True)
        
        # Force complete window update
        self.dialog.update()  # Force full window update
        self.canvas.update_idletasks()
        
        # Verify canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        print(f"Canvas dimensions after update: {canvas_width}x{canvas_height}")
    
        if canvas_width <= 1 or canvas_height <= 1:
            raise ValueError("Canvas failed to initialize with proper dimensions")
            
            """
            # Bind mouse events
            self.bind_clearmouse_events()
        
        # Navigation controls
        self.create_nav_controls()

        print("Init complete - about to load geodata")
        self.load_geodata()
        print("Geodata loaded")
        """

        # Initialize map view
        self.update_map_view()

    
    def update_map_view(self):
        """Update the map display with OSM tiles and overlays"""
        print("\nStarting map view update...")
        self.canvas.delete('all')  # Clear canvas
        
        # Calculate tile coordinates for current view
        lat_rad = math.radians(self.center_lat)
        n = 2.0 ** self.current_zoom
        x_tile = int((self.center_lon + 180.0) / 360.0 * n)
        y_tile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        
        print(f"Center tile coordinates: x={x_tile}, y={y_tile}, zoom={self.current_zoom}")
        
        # Calculate number of tiles needed
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        tiles_x = (canvas_width // OSM_TILE_SIZE) + 2
        tiles_y = (canvas_height // OSM_TILE_SIZE) + 2
        
        print(f"Loading {tiles_x * tiles_y} tiles...")
        
        # Load and display tiles
        for dx in range(-tiles_x//2, tiles_x//2 + 1):
            for dy in range(-tiles_y//2, tiles_y//2 + 1):
                # Calculate tile position
                current_x = x_tile + dx
                current_y = y_tile + dy
                
                # Get tile image
                tile = self.tile_manager.get_tile(current_x, current_y, self.current_zoom)
                if tile:
                    # Calculate pixel position on canvas
                    pixel_x = (canvas_width // 2) + (dx * OSM_TILE_SIZE)
                    pixel_y = (canvas_height // 2) + (dy * OSM_TILE_SIZE)
                    
                    # Draw tile on canvas
                    self.canvas.create_image(
                        pixel_x, 
                        pixel_y,
                        anchor='nw',
                        image=tile,
                        tags='tile'
                    )
        
        print("Base map tiles loaded")
        
        # Draw overlays based on visible layers
        #visible_layers = self.get_visible_layers()
        
        #if 'show_sections' in visible_layers and hasattr(self, 'sections'):
        #    print("Drawing sections...")
        #    self.draw_sections()
        
        #if 'show_boundaries' in visible_layers and hasattr(self, 'boundaries'):
        #    print("Drawing boundaries...")
        #    self.draw_boundaries()
        
        #print("Map view update complete")




    def create_layer_controls(self):
        """Create layer control tree with checkboxes"""
        layers_frame = ttk.LabelFrame(self.control_panel, text="Layers")
        layers_frame.pack(fill='x', padx=5, pady=5)
        
        self.layer_tree = ttk.Treeview(layers_frame, height=15)
        self.layer_tree.pack(fill='both', expand=True)
        
        self.layer_vars = {}  # Store checkbutton variables

        # Create main categories with their IDs
        category_ids = {}
        for category in ['Properties', 'Sections', 'Boundaries']:
            category_ids[category] = self.layer_tree.insert('', 'end', text=category, open=True)
            var = tk.BooleanVar(value=True)
            self.layer_vars[category] = var
            
            # Add layer control under the category
            self.layer_tree.insert(category_ids[category], 'end', 
                                 text=f"Show {category}", 
                                 tags=(f"show_{category.lower()}",))
    
    def create_nav_controls(self):
        """Create navigation controls"""
        nav_frame = ttk.LabelFrame(self.control_panel, text="Navigation")
        nav_frame.pack(fill='x', padx=5, pady=5)

        # Zoom controls
        zoom_frame = ttk.Frame(nav_frame)
        zoom_frame.pack(fill='x', pady=2)
        
        ttk.Button(zoom_frame, text="🔍+", width=3,
                  command=lambda: self.zoom(1.2)).pack(side='left', padx=2)
        ttk.Button(zoom_frame, text="🔍-", width=3,
                  command=lambda: self.zoom(0.8)).pack(side='left', padx=2)
        ttk.Button(zoom_frame, text="Reset", width=6,
                  command=self.reset_view).pack(side='left', padx=2)

        # Pan controls
        pan_frame = ttk.Frame(nav_frame)
        pan_frame.pack(fill='x', pady=2)
        
        # Create pan buttons in a grid layout
        pan_buttons = [
            ('⬉', -1, -1), ('⬆', 0, -1), ('⬈', 1, -1),
            ('⬅', -1, 0),  ('⊙', 0, 0),   ('➡', 1, 0),
            ('⬋', -1, 1),  ('⬇', 0, 1),   ('⬊', 1, 1)
        ]
        
        for row in range(3):
            for col in range(3):
                idx = row * 3 + col
                symbol, dx, dy = pan_buttons[idx]
                btn = ttk.Button(pan_frame, text=symbol, width=2,
                               command=lambda x=dx, y=dy: self.pan(x*20, y*20))
                btn.grid(row=row, column=col, padx=1, pady=1)

        # Zoom slider
        zoom_scale = ttk.Scale(nav_frame, 
                              from_=0, 
                              to=len(self.zoom_levels)-1,
                              orient='horizontal',
                              command=self.on_zoom_scale)
        zoom_scale.set(self.current_zoom_index)
        zoom_scale.pack(fill='x', padx=5, pady=5)
    
    def on_zoom_scale(self, value):
        """Handle zoom scale changes"""
        try:
            new_index = int(float(value))
            if new_index != self.current_zoom_index:
                old_zoom = self.zoom_levels[self.current_zoom_index]
                new_zoom = self.zoom_levels[new_index]
                self.scale_factor *= (new_zoom / old_zoom)
                self.current_zoom_index = new_index
                self.update_display()
        except (ValueError, IndexError) as e:
            print(f"Zoom scale error: {e}")


    def toggle_category(self, category):
        """Toggle all layers in a category"""
        # Implementation here
        self.update_display()

    def zoom(self, factor):
        """Handle zoom operations"""
        # Implementation here
        self.update_display()

    def pan(self, dx, dy):
        """Handle pan operations"""
        # Implementation here
        self.update_display()

    def load_geodata(self):
        """Load GeoJSON data from database"""
        print("Starting load_geodata...")
        try:
            # Load sections
            self.cursor.execute("SELECT asset_name, coordinates_text FROM MapAssets WHERE asset_type='Section'")
            self.sections = self.cursor.fetchall()
            print(f"Loaded {len(self.sections)} sections")
            
            # Load boundaries
            self.cursor.execute("SELECT asset_name, coordinates_text FROM MapAssets WHERE asset_type='Boundary'")
            self.boundaries = self.cursor.fetchall()
            print(f"Loaded {len(self.boundaries)} boundaries")
            
            # Load properties
            self.cursor.execute("""
                SELECT gd.geojson_text, gd.feature_type
                FROM GeoJSONData gd
                JOIN GeoJSONLink gl ON gd.geojson_id = gl.geojson_id
                WHERE gl.record_type IN ('Deed', 'Tax')
            """)
            self.properties = self.cursor.fetchall()
            print(f"Loaded {len(self.properties)} properties")
            
            self.update_display()
        except sqlite3.Error as e:
            print(f"Database error in load_geodata: {e}")
            messagebox.showerror("Error", f"Failed to load geographic data: {str(e)}")
    
    def create_layer_controls(self):
        """Create layer control tree with checkboxes"""
        layers_frame = ttk.LabelFrame(self.control_panel, text="Layers")
        layers_frame.pack(fill='x', padx=5, pady=5)
        
        self.layer_tree = ttk.Treeview(layers_frame, height=15)
        self.layer_tree.pack(fill='both', expand=True)
        
        # Create layer variables dictionary
        self.layer_vars = {}  # Store checkbutton variables

        # Create main categories with their IDs
        category_ids = {}
        for category in ['Properties', 'Sections', 'Boundaries']:
            category_ids[category] = self.layer_tree.insert('', 'end', text=category, open=True)
            var = tk.BooleanVar(value=True)
            self.layer_vars[category] = var
            
            # Add layer control under the category
            self.layer_tree.insert(category_ids[category], 'end', 
                                 text=f"Show {category}", 
                                 tags=(f"show_{category.lower()}",))

        # Add tree bindings
        self.layer_tree.bind('<<TreeviewOpen>>', lambda e: self.update_display())
        self.layer_tree.bind('<<TreeviewClose>>', lambda e: self.update_display())
        self.layer_tree.bind('<Button-1>', self.handle_layer_click)


    def handle_layer_click(self, event):
        """Handle clicks on layer tree items"""
        item = self.layer_tree.identify('item', event.x, event.y)
        if item:
            # Toggle category if it's a main category
            if item in self.layer_vars:
                self.toggle_category(item)
            # Update display for individual layer toggles
            self.update_display()
    

    def load_layers(self):
        """Load all map layers"""
        try:
            # Load sections
            cursor = self.connection.cursor()
            cursor.execute("SELECT asset_name, coordinates_text FROM MapAssets WHERE asset_type='Section'")
            self.sections = cursor.fetchall()
            
            # Load boundaries
            cursor.execute("SELECT asset_name, coordinates_text FROM MapAssets WHERE asset_type='Boundary'")
            self.boundaries = cursor.fetchall()
            
            # Load properties
            cursor.execute("""
                SELECT gd.geojson_text, gd.feature_type
                FROM GeoJSONData gd
                JOIN GeoJSONLink gl ON gd.geojson_id = gl.geojson_id
                WHERE gl.record_type IN ('Deed', 'Tax')
            """)
            self.properties = cursor.fetchall()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load map layers: {str(e)}")

    
    def bind_mouse_events(self):
        """Bind mouse events for pan and zoom"""
        self.canvas.bind('<ButtonPress-1>', self.start_pan)
        self.canvas.bind('<B1-Motion>', self.do_pan)
        self.canvas.bind('<ButtonRelease-1>', self.end_pan)
        self.canvas.bind('<MouseWheel>', self.mouse_zoom)  # Windows
        self.canvas.bind('<Button-4>', self.mouse_zoom)    # Linux scroll up
        self.canvas.bind('<Button-5>', self.mouse_zoom)    # Linux scroll down

    def start_pan(self, event):
        """Start pan operation"""
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.configure(cursor='fleur')

    def do_pan(self, event):
        """Handle pan movement"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def end_pan(self, event):
        """End pan operation"""
        self.canvas.configure(cursor='arrow')

    def mouse_zoom(self, event):
        """Handle mouse wheel zoom"""
        # Get current mouse position
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Determine zoom direction
        if event.num == 4 or event.delta > 0:  # Zoom in
            factor = 1.1
        else:  # Zoom out
            factor = 0.9
        
        # Adjust current scale
        self.scale_factor *= factor
        
        # Update display with new scale
        self.update_display()


    def update_display(self):
        """Update map display based on visible layers"""
        print("\nStarting update_display...")
        self.canvas.delete('all')
        
        # Debug canvas state
        print(f"Canvas dimensions: {self.canvas.winfo_width()}x{self.canvas.winfo_height()}")
        print(f"Canvas state: {self.canvas.winfo_ismapped()}")
        print(f"Scale factor: {self.scale_factor}")
        print(f"Pan offset: {self.pan_offset}")
        
        visible_layers = self.get_visible_layers()
        print(f"Visible layers: {visible_layers}")
        
        try:
            # Draw sections if visible
            if 'show_sections' in visible_layers and hasattr(self, 'sections'):
                print("Drawing sections...")
                for name, coords in self.sections:
                    raw_points = self.parse_coordinates(coords)
                    print(f"Section {name}: {len(raw_points)} points")
                    scaled_points = self.scale_coordinates(raw_points)
                    if scaled_points:
                        self.canvas.create_polygon(scaled_points, 
                                                outline='gray', 
                                                fill='', 
                                                width=1,
                                                tags=('section', name))
                        print(f"Created polygon for section {name}")
            
            # Draw boundaries if visible
            if 'show_boundaries' in visible_layers and hasattr(self, 'boundaries'):
                print("Drawing boundaries...")
                for name, coords in self.boundaries:
                    raw_points = self.parse_coordinates(coords)
                    print(f"Boundary {name}: {len(raw_points)} points")
                    scaled_points = self.scale_coordinates(raw_points)
                    if scaled_points:
                        self.canvas.create_polygon(scaled_points,
                                                outline='black',
                                                fill='',
                                                width=2,
                                                tags=('boundary', name))
                        print(f"Created polygon for boundary {name}")
            
            # Draw properties if visible
            if 'show_properties' in visible_layers and hasattr(self, 'properties'):
                print("Drawing properties...")
                self.draw_properties()
                
            print("Display update complete")
            
        except Exception as e:
            print(f"Error in update_display: {e}")
            import traceback
            traceback.print_exc()

        # Force canvas update
        self.canvas.update_idletasks()

    def get_visible_layers(self):
        """Get list of visible layer tags"""
        print("\nChecking visible layers...")
        visible_layers = set()
        
        # Debug layer tree state
        print("Layer tree items:")
        for item in self.layer_tree.get_children():
            item_data = self.layer_tree.item(item)
            print(f"Category: {item_data['text']}")
            print(f"  Open: {self.layer_tree.item(item, 'open')}")
            print(f"  Tags: {item_data.get('tags', [])}")
            
            if self.layer_tree.item(item)['open']:
                for child in self.layer_tree.get_children(item):
                    child_data = self.layer_tree.item(child)
                    tag = child_data['tags'][0]
                    visible_layers.add(tag)
                    print(f"  Child layer: {child_data['text']}")
                    print(f"    Tag: {tag}")
                    print(f"    State: {'visible' if tag in visible_layers else 'hidden'}")
                    
        print(f"Final visible layers: {visible_layers}")
        return visible_layers


    def parse_coordinates(self, coords_text):
        """Parse coordinates from comma-separated lat/long pairs"""
        print(f"\nParsing coordinates: {coords_text[:100]}...")  # Show first 100 chars
        try:
            # Split into individual values
            values = coords_text.strip().split(',')
            coords = []
            
            # Process values in pairs
            for i in range(0, len(values), 2):
                if i + 1 < len(values):
                    lon = float(values[i])      # Longitude
                    lat = float(values[i + 1])  # Latitude
                    coords.append((lon, lat))
            
            # Debug output
            if coords:
                print(f"First coordinate pair: ({coords[0][0]}, {coords[0][1]})")
                print(f"Last coordinate pair: ({coords[-1][0]}, {coords[-1][1]})")
            print(f"Successfully parsed {len(coords)} coordinate pairs")
            
            return coords

        except Exception as e:
            print(f"Error parsing coordinates: {e}")
            print(f"Problem value: {coords_text[:100]}...")
            return []

    def toggle_category(self, category_id):
        """Toggle visibility of all layers in a category"""
        is_visible = self.layer_vars[category_id].get()
        for child in self.layer_tree.get_children(category_id):
            # Set checkbutton state
            if child in self.layer_vars:
                self.layer_vars[child].set(is_visible)
        self.update_display()


    def draw_sections(self):
        """Draw section boundaries over the base map"""
        print("\nDrawing sections:")
        
        if not hasattr(self, 'sections'):
            print("No section data available")
            return
            
        for name, coords in self.sections:
            try:
                # Parse the coordinate string into points
                points = self.parse_coordinates(coords)
                if not points:
                    continue
                    
                # Convert to screen coordinates
                screen_points = []
                for lon, lat in points:
                    x, y = self.latlon_to_pixels(lat, lon)
                    screen_points.append(x)
                    screen_points.append(y)
                
                # Draw the section polygon
                if len(screen_points) >= 4:  # Need at least 2 points (4 coordinates)
                    self.canvas.create_polygon(
                        screen_points,
                        outline='gray',
                        fill='',
                        width=1,
                        stipple='gray50',
                        tags=('section', name)
                    )
                    print(f"Drew section {name}")
                    
            except Exception as e:
                print(f"Error drawing section {name}: {e}")

    def draw_boundaries(self):
        """Draw township/community boundaries over the base map"""
        print("\nDrawing boundaries:")
        
        if not hasattr(self, 'boundaries'):
            print("No boundary data available")
            return
            
        for name, coords in self.boundaries:
            try:
                # Parse the coordinate string into points
                points = self.parse_coordinates(coords)
                if not points:
                    continue
                    
                # Convert to screen coordinates
                screen_points = []
                for lon, lat in points:
                    x, y = self.latlon_to_pixels(lat, lon)
                    screen_points.append(x)
                    screen_points.append(y)
                
                # Draw the boundary polygon
                if len(screen_points) >= 4:  # Need at least 2 points (4 coordinates)
                    self.canvas.create_polygon(
                        screen_points,
                        outline='black',
                        fill='',
                        width=2,
                        tags=('boundary', name)
                    )
                    print(f"Drew boundary {name}")
                    
            except Exception as e:
                print(f"Error drawing boundary {name}: {e}")

    def latlon_to_pixels(self, lat, lon):
        """Convert latitude/longitude to pixel coordinates on canvas"""
        # Convert lat/lon to tile coordinates at current zoom
        lat_rad = math.radians(lat)
        n = 2.0 ** self.current_zoom
        x_tile = (lon + 180.0) / 360.0 * n
        y_tile = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

        # Convert tile coordinates to pixels
        x_pixel = x_tile * OSM_TILE_SIZE
        y_pixel = y_tile * OSM_TILE_SIZE

        # Adjust for canvas center and pan offset
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        x = x_pixel - (self.pan_offset[0] * OSM_TILE_SIZE) + (canvas_width / 2)
        y = y_pixel - (self.pan_offset[1] * OSM_TILE_SIZE) + (canvas_height / 2)

        return x, y


    def draw_properties(self):
        """Draw property features"""
        colors = {
            'POLYGON': '#3388ff',
            'LINE': '#ff3333',
            'POINT': '#33ff33'
        }
        
        for geojson_text, feature_type in self.properties:
            try:
                geojson = json.loads(geojson_text)
                coords = self.extract_coordinates(geojson)
                points = self.scale_coordinates(coords)
                
                if feature_type == 'POLYGON':
                    self.canvas.create_polygon(points,
                                            fill=colors[feature_type],
                                            stipple='gray50',
                                            outline=colors[feature_type],
                                            width=1,
                                            tags=('property', 'polygon'))
                elif feature_type == 'LINE':
                    self.canvas.create_line(points,
                                          fill=colors[feature_type],
                                          width=2,
                                          tags=('property', 'line'))
                elif feature_type == 'POINT':
                    x, y = points[0]
                    self.canvas.create_oval(x-5, y-5, x+5, y+5,
                                          fill=colors[feature_type],
                                          tags=('property', 'point'))
                                          
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error drawing feature: {e}")

    def scale_coordinates(self, coords):
        """Scale coordinates to fit canvas"""
        if not coords:
            print("Warning: Empty coordinates in scale_coordinates")
            return []

        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        print(f"Canvas dimensions: {canvas_width}x{canvas_height}")

        if canvas_width <= 1 or canvas_height <= 1:
            print("Error: Invalid canvas dimensions")
            return []

        # Find bounds
        x_coords = [p[0] for p in coords]
        y_coords = [p[1] for p in coords]
        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        print(f"Coordinate bounds: X({min_x:.6f}, {max_x:.6f}), Y({min_y:.6f}, {max_y:.6f})")

        # Add padding
        padding = 20
        effective_width = canvas_width - (2 * padding)
        effective_height = canvas_height - (2 * padding)

        # Calculate scale factors (use absolute values)
        x_range = abs(max_x - min_x)
        y_range = abs(max_y - min_y)
        
        if x_range == 0 or y_range == 0:
            print("Warning: Zero range in coordinates")
            return []
            
        x_scale = effective_width / x_range
        y_scale = effective_height / y_range
        scale = min(abs(x_scale), abs(y_scale))  # Use absolute value for scale
        
        print(f"Scale factors - X: {x_scale:.6f}, Y: {y_scale:.6f}, Using: {scale:.6f}")

        # Scale and center points
        scaled_points = []
        for x, y in coords:
            # Normalize to 0-1 range then scale to canvas size
            norm_x = (x - min_x) / x_range
            norm_y = (y - min_y) / y_range
            
            scaled_x = padding + (norm_x * effective_width)
            scaled_y = canvas_height - (padding + (norm_y * effective_height))  # Flip Y axis
            
            scaled_points.append((scaled_x, scaled_y))

        print(f"Scaled {len(coords)} points")
        if scaled_points:
            print(f"First scaled point: ({scaled_points[0][0]:.1f}, {scaled_points[0][1]:.1f})")
            print(f"Last scaled point: ({scaled_points[-1][0]:.1f}, {scaled_points[-1][1]:.1f})")

        return scaled_points


    def extract_coordinates(self, geojson):
        """Extract coordinates from GeoJSON feature"""
        geom = geojson.get('geometry', {})
        coords = []

        if geom.get('type') == 'Point':
            coords = [geom['coordinates']]
        elif geom.get('type') == 'LineString':
            coords = geom['coordinates']
        elif geom.get('type') == 'Polygon':
            coords = geom['coordinates'][0]  # First ring
            
        return coords

    def on_canvas_configure(self, event):
        """Handle canvas resize"""
        self.update_display()

    def on_canvas_click(self, event):
        """Handle canvas click for feature selection"""
        clicked = self.canvas.find_closest(event.x, event.y)
        if clicked:
            tags = self.canvas.gettags(clicked[0])
            if 'property' in tags:
                self.highlight_feature(clicked[0])

    def highlight_feature(self, item_id):
        """Highlight selected feature"""
        self.canvas.dtag('all', 'selected')
        self.canvas.addtag('selected', 'withtag', item_id)
        
        # Store original colors
        if not hasattr(self, 'original_colors'):
            self.original_colors = {}
        
        # Highlight selected feature
        tags = self.canvas.gettags(item_id)
        if 'point' in tags:
            self.canvas.itemconfig(item_id, width=3)
        else:
            self.canvas.itemconfig(item_id, width=3, outline='yellow')

    def bind_events(self):
        """Bind canvas events"""
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        
        # Bind keyboard shortcuts
        self.dialog.bind('<Control-plus>', lambda e: self.zoom(1.2))
        self.dialog.bind('<Control-minus>', lambda e: self.zoom(0.8))

    
    def show(self):
        """Show the map viewer"""
        self.dialog.transient(self.dialog.master)
        self.dialog.grab_set()
        self.dialog.master.wait_window(self.dialog)

    def zoom(self, factor):
        """Zoom in/out by scaling factor"""
        self.scale_factor *= factor
        self.update_display()

    def pan(self, dx, dy):
        """Pan display by dx, dy pixels"""
        self.pan_offset = (
            self.pan_offset[0] + dx,
            self.pan_offset[1] + dy
        )
        self.update_display()

    def reset_view(self):
        """Reset zoom and pan to default"""
        self.scale_factor = 1.0
        self.pan_offset = (0, 0)
        self.update_display()

    def get_transformed_coords(self, coords):
        """Apply zoom and pan to coordinates"""
        scaled = self.scale_coordinates(coords)
        transformed = []
        
        for x, y in scaled:
            tx = x * self.scale_factor + self.pan_offset[0]
            ty = y * self.scale_factor + self.pan_offset[1]
            transformed.append((tx, ty))
            
        return transformed