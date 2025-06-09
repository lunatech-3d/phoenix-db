import sys
import os
from pathlib import Path
import folium
import sqlite3
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QCheckBox, QPushButton, QFrame, QDesktopWidget)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import Qt


class MapViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plymouth GIS Viewer")
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger('MapViewer')
        
        # Initialize variables
        self.map_file = Path("map.html").absolute()
        self.db_path = 'phoenix.db'
        self.map_center = [42.371427, -83.468213]
        self.zoom_level = 15
        
        # Create UI
        self.setup_ui()
        
        # Create initial map
        self.create_map()
        
        # Show window
        self.show()
  

    def setup_ui(self):
        """Create the application UI"""
        # Maximize the window to fill the screen
        self.setWindowState(self.windowState() | Qt.WindowMaximized)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Control panel
        control_panel = QFrame()
        control_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
        control_panel.setMaximumWidth(250)
        control_layout = QVBoxLayout(control_panel)
        
        # Layer checkboxes
        self.layers = {}
        for layer_name in ["Sections", "Townships", "Properties"]:
            checkbox = QCheckBox(layer_name)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.refresh_map)
            self.layers[layer_name] = checkbox
            control_layout.addWidget(checkbox)
        
        # Dictionary to manage FeatureGroup instances
        self.layer_objects = {
            "Sections": None,
            "Townships": None,
            "Properties": None
        }


        # Refresh button
        refresh_btn = QPushButton("Refresh Map")
        refresh_btn.clicked.connect(self.refresh_map)
        control_layout.addWidget(refresh_btn)
        
        # Add stretch to push controls to top
        control_layout.addStretch()
        
        # Map view
        self.web_view = QWebEngineView()
        
        # Add widgets to main layout
        layout.addWidget(control_panel)
        layout.addWidget(self.web_view)

              
    def create_map(self):
        """Create the Folium map with enabled layers"""
        self.map_instance = folium.Map(
            location=self.map_center,
            zoom_start=self.zoom_level,
            control_scale=True
        )

        # Add custom JavaScript to ensure map is initialized
        custom_js = """
            <script>
            // Store map reference when initialized
            var map;
            document.addEventListener('DOMContentLoaded', function() {
                // Wait for map element to be available
                var mapEl = document.querySelector('#map');
                if (mapEl && mapEl._leaflet) {
                    map = mapEl._leaflet;
                    window.mapObject = map;
                }
            });
            </script>
        """
        
        self.map_instance.get_root().html.add_child(folium.Element(custom_js))
        self.map_instance.add_child(folium.LayerControl(position='topright'))

        # Save the map
        map_html = self.map_instance.get_root().render()
        
        with open(self.map_file, "w", encoding="utf-8") as f:
            f.write(map_html)

        # Load the map into the web view
        self.web_view.setUrl(QUrl.fromLocalFile(str(self.map_file)))

    

    def refresh_map(self):
        """Refresh map with layer management."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create new map instance
                self.create_map()

                # Add layers only after ensuring map is initialized
                if self.layers["Sections"].isChecked():
                    sections_group = self.add_sections(self.map_instance, conn)
                    if sections_group:
                        self.map_instance.add_child(sections_group)

                if self.layers["Townships"].isChecked():
                    townships_group = self.add_townships(self.map_instance, conn)
                    if townships_group:
                        self.map_instance.add_child(townships_group)

                if self.layers["Properties"].isChecked():
                    properties_group = self.add_properties(self.map_instance, conn)
                    if properties_group:
                        self.map_instance.add_child(properties_group)

                # Save and reload
                self.map_instance.save(str(self.map_file))
                self.web_view.reload()  # Use reload instead of setUrl to maintain state
                self.logger.debug(f"Map refreshed and loaded: {self.map_file}")

        except Exception as e:
            self.logger.error(f"Error refreshing map: {e}")
            raise

    def create_geometry_df(self, df):
        """Convert coordinates to GeoDataFrame"""
        geometries = []
        for coords in df['coordinates_text']:
            try:
                points = [float(x) for x in coords.split(',')]
                geometries.append(Polygon(zip(points[::2], points[1::2])))
            except Exception as e:
                self.logger.error(f"Error creating geometry: {coords}, Error: {e}")
                geometries.append(None)  # Add None for invalid geometries
        
        gdf = gpd.GeoDataFrame(
            df.drop('coordinates_text', axis=1),
            geometry=geometries,
            crs="EPSG:4326"
        )
        self.logger.debug(f"Created GeoDataFrame: {gdf}")
        return gdf

    def add_sections(self, m, conn):
        """Add section boundaries to map"""
        query = "SELECT asset_name, coordinates_text FROM MapAssets WHERE asset_type = 'Section'"
        sections = pd.read_sql_query(query, conn)
        
        if not sections.empty:
            gdf = self.create_geometry_df(sections)
            
            feature_group = folium.FeatureGroup(name="Sections", overlay=True, show=True)
            feature_group.layer_name = "Sections"
            
            geojson = folium.GeoJson(
                gdf,
                name="Sections",
                style_function=lambda x: {
                    'fillColor': 'none',
                    'color': 'green',
                    'weight': 2
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['asset_name'],
                    aliases=['Section:']
                )
            )
            
            geojson.add_to(feature_group)
            return feature_group
        return None

    def add_townships(self, m, conn):
        """Add township boundaries to map"""
        query = "SELECT asset_name, coordinates_text FROM MapAssets WHERE asset_type = 'Boundary'"
        boundaries = pd.read_sql_query(query, conn)
        
        if not boundaries.empty:
            gdf = self.create_geometry_df(boundaries)
            
            feature_group = folium.FeatureGroup(name="Townships", overlay=True, show=True)
            feature_group.layer_name = "Townships"
            
            geojson = folium.GeoJson(
                gdf,
                name="Townships",
                style_function=lambda x: {
                    'fillColor': 'none',
                    'color': 'blue',
                    'weight': 2
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['asset_name'],
                    aliases=['Township:']
                )
            )
            
            geojson.add_to(feature_group)
            return feature_group
        return None

    def add_properties(self, m, conn):
        """Add property boundaries to map"""
        query = """
            SELECT 
                p.coordinates_text, 
                TRIM(
                    COALESCE(o.first_name, '') || 
                    CASE 
                        WHEN o.middle_name IS NOT NULL AND LENGTH(o.middle_name) > 0 THEN ' ' || o.middle_name 
                        ELSE ''
                    END || ' ' || 
                    COALESCE(
                        CASE 
                            WHEN o.married_name IS NOT NULL AND LENGTH(o.married_name) > 0 THEN o.married_name
                            ELSE o.last_name
                        END, ''
                    )
                ) as owner_name
            FROM Property p
            JOIN People o ON p.owner_id = o.id
            WHERE p.coordinates_text IS NOT NULL
        """
        properties = pd.read_sql_query(query, conn)
        
        if not properties.empty:
            gdf = self.create_geometry_df(properties)
            
            feature_group = folium.FeatureGroup(name="Properties", overlay=True, show=True)
            feature_group.layer_name = "Properties"
            
            geojson = folium.GeoJson(
                gdf,
                name="Properties",
                style_function=lambda x: {
                    'fillColor': 'red',
                    'color': 'red',
                    'weight': 1,
                    'fillOpacity': 0.2
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['owner_name'],
                    aliases=['Owner:'],
                    style=(
                        "background-color: white; "
                        "color: black; "
                        "font-size: 24px; "  
                        "font-family: Arial; "
                        "padding: 5px;"
                    )
                )
            )
            
            geojson.add_to(feature_group)
            return feature_group
        return None  

def main():
    app = QApplication(sys.argv)
    
    try:
        viewer = MapViewer()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    main()