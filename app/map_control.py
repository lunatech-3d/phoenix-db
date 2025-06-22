import folium
import logging
import os
import sys
import webbrowser
import sqlite3
import geopandas as gpd
from datetime import datetime
from shapely.geometry import Polygon

#Local Imports
from app.config import DB_PATH, PATHS

class MapController:
    _instance = None
    
    class BoundaryLoadingError(Exception):
        pass

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MapController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.map = None
        self.setup_logging()
        
        try:
            self.connection = sqlite3.connect(DB_PATH)
            self.cursor = self.connection.cursor()
            self.active_layers = {}
            self.logger.info("MapController initialized successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            raise

    def setup_logging(self):
        self.logger = logging.getLogger('MapController')
        self.logger.setLevel(logging.DEBUG)
        
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        fh = logging.FileHandler(f'logs/map_controller_{datetime.now().strftime("%Y%m%d")}.log')
        fh.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def generate_map(self, owner_id=None):
        self.initialize_map()
        if owner_id:
            self.display_prop(owner_id)
        map_file = 'phoenix_map.html'
        self.map.save(map_file)
        return map_file

    def initialize_map(self):
        self.map = folium.Map(location=[42.371427, -83.468213], zoom_start=15)
        
        self.load_sections()
        self.load_all_boundaries()
        # self.load_placemarks()
        self.add_layer_control()
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Satellite',
        ).add_to(self.map)

    def add_layer_control(self):
        folium.LayerControl().add_to(self.map)

    def load_sections(self):
        section_data = {'geometry': []}
        query = "SELECT * FROM MapAssets WHERE asset_type = 'Section' AND coordinates_text IS NOT NULL"
        sections = self.cursor.execute(query).fetchall()
        for i, section in enumerate(sections):
            coordinates_text = section[3]
            coordinates = [float(coord) for coord in coordinates_text.split(',')]
            polygon = Polygon(zip(coordinates[::2], coordinates[1::2]))
            
            gdf = gpd.GeoDataFrame({'geometry': [polygon]}, crs="EPSG:4326")
            
            geojson_layer = folium.GeoJson(
                gdf,
                name=f"Section_{i}",  # Unique name
                style_function=lambda feature: {
                    'fillColor': 'none',
                    'color': 'green',
                    'weight': 3
                }
            )
            
            # Add layer to the map and log success
            geojson_layer.add_to(self.map)
            self.logger.info(f"Section_{i} layer added to map")



    def load_all_boundaries(self):
        """Load all standard boundaries and add them to the map and control panel"""
        boundary_types = ['Boundary']
        
        for boundary_type in boundary_types:
            self.logger.info(f"Loading boundaries of type: {boundary_type}")
            query = "SELECT asset_name, coordinates_text, description FROM MapAssets WHERE asset_type = ?"
            results = self.cursor.execute(query, (boundary_type,)).fetchall()
            
            for result in results:
                asset_name, coordinates_text, description = result
                formatted_asset_name = asset_name.replace(" ", "_")
                layer_id = f"boundary_{formatted_asset_name}"
                
                self.logger.info(f"Loading boundary: {asset_name}")
                try:
                    layer = self.load_boundary(asset_name, boundary_type, coordinates_text, description)
                    if layer:
                        self.logger.info(f"Boundary '{asset_name}' loaded successfully")
                        self.active_layers[layer_id] = layer
                        layer.add_to(self.map)
                        self.logger.info(f"Adding layer '{asset_name}' to active layers")
                except self.BoundaryLoadingError as e:
                    self.logger.error(e)
                    # Provide a fallback or skip the problematic boundary

    def load_boundary(self, asset_name, asset_type, coordinates_text, description, style_options=None):
        # Define style with defaults or custom values
        style = style_options or {
            'fillColor': '#ffffff',
            'color': '#000000',
            'weight': 2,
            'fillOpacity': 0.0
        }
        
        # Create polygon from coordinates
        coordinates = [float(coord) for coord in coordinates_text.split(',')]
        polygon = Polygon(zip(coordinates[::2], coordinates[1::2]))
        boundary_data = {'geometry': [polygon]}
        gdf = gpd.GeoDataFrame(boundary_data, crs="EPSG:4326")

        # Define unique layer name using asset_name
        geojson_layer = folium.GeoJson(
            gdf,
            name=f"{asset_name}_layer",  # Ensure unique layer name
            style_function=lambda feature: {
                'fillColor': style['fillColor'],
                'color': style['color'],
                'weight': style['weight'],
                'fillOpacity': style.get('fillOpacity', 0.5)
            },
            tooltip=asset_name,
            popup=folium.Popup(description, max_width=300)
        )

        geojson_layer.add_to(self.map)
        self.active_layers[f"{asset_name}_layer"] = geojson_layer  # Track active layers
        return geojson_layer


    def add_property(self, property_id, geojson_text, owner_name, year, description):
        if not self.map:
            self.initialize_map()

        try:
            # Parse coordinates
            coordinates = [[float(coord), float(coord)] for coord in geojson_text.split(',')]
            
            # Ensure polygon closure
            if coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])

            # Construct GeoJSON
            geo_json = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [coordinates]
                        },
                        "properties": {
                            "name": f"{owner_name}'s Property ({year}"
                        }
                    }
                ]
            }

            # Create and add GeoJson layer to map
            property_layer = folium.GeoJson(
                geo_json,
                name=f"{owner_name}'s Property ({year})",
                style_function=lambda feature: {
                    'fillColor': 'none',
                    'color': 'red',
                    'weight': 2
                },
                tooltip=f"{owner_name}'s Property ({year})",
                popup=folium.Popup(f"<b>{owner_name}'s Property ({year})</b><br>{description}", max_width=300)
            )
            property_layer.add_to(self.map)
            self.active_layers[f"prop_{property_id}"] = property_layer

            self.logger.info(f"Property '{property_layer.get_name()}' added to map")
        except Exception as e:
            self.logger.error(f"Error adding property layer: {e}")

    def display_prop(self, owner_id, color='red', weight=2, fill_color='none'):
        query = "SELECT coordinates_text FROM Property WHERE owner_id = ?"
        result = self.cursor.execute(query, (owner_id,)).fetchall()

        if result:
            property_data = {'geometry': []}
            for row in result:
                coordinates_text = row[0]
                coordinates = [float(coord) for coord in coordinates_text.split(',')]
                polygon = Polygon(zip(coordinates[::2], coordinates[1::2]))
                property_data['geometry'].append(polygon)
            gdf = gpd.GeoDataFrame(property_data, crs="EPSG:4326")
            geojson_layer = folium.GeoJson(gdf, name="Properties", style_function=lambda feature: {
                'fillColor': fill_color,
                'color': color,
                'weight': weight
            })
            geojson_layer.add_to(self.map)
            self.active_layers[f"prop_{owner_id}"] = geojson_layer
            self.logger.info(f"Property for owner {owner_id} added to map")

    def display_tax_property(self, record_id, color='red'):
        """Display a specific tax record property"""
        self.logger.info(f"Starting display_tax_property for record_id {record_id}")
        try:
            # Ensure the map is initialized
            if not self.map:
                self.initialize_map()
                self.logger.info("Map initialized inside display_tax_property")
            
            # Get property details
            query = """
                SELECT 
                    p.first_name, p.last_name,
                    t.year,
                    gd.geojson_text, gd.description
                FROM Tax_Records t
                JOIN People p ON t.people_id = p.id
                JOIN GeoJSONLink gl ON t.record_id = gl.record_id
                JOIN GeoJSONData gd ON gl.geojson_id = gd.geojson_id
                WHERE t.record_id = ?
            """
            result = self.cursor.execute(query, (record_id,)).fetchone()
            
            if result:
                self.logger.info(f"Data retrieved for record_id {record_id}: {result}")
                owner_name = f"{result[0]} {result[1]}"
                year = result[2]
                geojson_text = result[3]
                description = result[4]

                # Ensure geojson_text is not empty and parse coordinates
                if not geojson_text:
                    self.logger.error(f"No geojson_text found for record_id {record_id}")
                    return False
                
                coordinates = geojson_text.split(',')
                try:
                    coordinates = [float(coord) for coord in coordinates]
                except ValueError:
                    self.logger.error(f"Invalid coordinate format in geojson_text for record_id {record_id}")
                    return False
                
                if len(coordinates) < 4:
                    self.logger.error(f"Insufficient coordinates for record_id {record_id}")
                    return False

                # Create the polygon and log bounds
                polygon = Polygon(zip(coordinates[::2], coordinates[1::2]))
                property_data = {'geometry': [polygon]}
                gdf = gpd.GeoDataFrame(property_data, crs="EPSG:4326")
                self.logger.info(f"Polygon bounds: {polygon.bounds}")

                # Define layer details and add GeoJson to the map
                layer_name = f"{owner_name}'s Property ({year})"
                property_layer = folium.GeoJson(
                    gdf,
                    name=layer_name,
                    style_function=lambda x: {'fillColor': 'none', 'color': color, 'weight': 2},
                    tooltip=layer_name,
                    popup=folium.Popup(f"<b>{layer_name}</b><br>{description}", max_width=300)
                )
                property_layer.add_to(self.map)
                self.active_layers[f"tax_{record_id}"] = property_layer

                # Center and zoom map to fit this property
                self.map.fit_bounds(property_layer.get_bounds())

                self.logger.info(f"Property '{layer_name}' added to map")
                
                return True
                
            else:
                self.logger.error(f"No data found for record_id {record_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error displaying tax property for record_id {record_id}: {e}")
            return False

    def show_map(self):
        if not self.map:
            self.initialize_map()
        map_file = 'phoenix_map.html'
        self.map.save(map_file)
        webbrowser.open('file://' + os.path.abspath(map_file), new=2)

    def activate_map(self):
        """Ensure map is initialized and displayed in the browser"""
        if not self.map:
            self.initialize_map()
        
        map_file = 'phoenix_map.html'
        self.map.save(map_file)
        webbrowser.open('file://' + os.path.abspath(map_file), new=2)
        self.logger.info("Map activated and opened in browser")

    def __del__(self):
        if hasattr(self, 'connection'):
            self.cursor.close()
            self.connection.close()