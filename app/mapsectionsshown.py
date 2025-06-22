import folium
import webbrowser
import sqlite3
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.wkt import loads

# Connect to SQLite database
conn = sqlite3.connect('phoenix.db')
cursor = conn.cursor()

# Select rows with asset_type 'Section' and non-empty coordinates_text
query = "SELECT * FROM MapAssets WHERE asset_type = 'Section' AND coordinates_text IS NOT NULL"
sections = cursor.execute(query).fetchall()

# Create a GeoDataFrame to store section boundaries
section_data = {'geometry': []}
for section in sections:
    coordinates_text = section[3]
    coordinates = coordinates_text.split(',')
    coordinates = [float(coord) for coord in coordinates]
    # Create a polygon from the coordinates
    polygon = Polygon(zip(coordinates[::2], coordinates[1::2]))
    section_data['geometry'].append(polygon)

gdf = gpd.GeoDataFrame(section_data, crs="EPSG:4326")

# Create a base map centered at Plymouth's approximate latitude and longitude
plymouth_map = folium.Map(location=[42.371427, -83.468213], zoom_start=15)

# Add GeoJSON overlay of section boundaries to the map
folium.GeoJson(gdf, style_function=lambda feature: {
    'fillColor': 'none',  # Set fillColor to 'none' for no interior shading
    'color': 'green',       # Set the border color
    'weight': 1            # Set the border weight
}).add_to(plymouth_map)

# Save the map to an HTML file
plymouth_map.save('section_map.html')

# Open the map in a web browser
webbrowser.open('section_map.html')

# Close the database connection
conn.close()
