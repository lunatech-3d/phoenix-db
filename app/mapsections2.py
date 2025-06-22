import folium
import sys
import webbrowser
import sqlite3
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from folium.plugins import TimestampedGeoJson


# Function to load and display boundaries
def display_prop(map_object, conn, owner_id, color='red', weight=2, fill_color='none'):
    with conn:
        cursor = conn.cursor()

        # Select properties for the given owner
        query = "SELECT coordinates_text FROM Property WHERE owner_id = ?"
        result = cursor.execute(query, (owner_id,)).fetchall()

        if result:
            property_data = {'geometry': []}

            for row in result:
                coordinates_text = row[0]
                coordinates = coordinates_text.split(',')
                coordinates = [float(coord) for coord in coordinates]

                # Create a polygon from the coordinates
                polygon = Polygon(zip(coordinates[::2], coordinates[1::2]))
                property_data['geometry'].append(polygon)

            gdf = gpd.GeoDataFrame(property_data, crs="EPSG:4326")

            # Create a GeoJson layer for the properties
            geojson_layer = folium.GeoJson(gdf, name="Properties", style_function=lambda feature: {
                'fillColor': fill_color,
                'color': color,
                'weight': weight
            })

            # Create a FeatureGroup for the properties
            property_group = folium.FeatureGroup(name="Properties")
            geojson_layer.add_to(property_group)

            # Add FeatureGroup to the map
            property_group.add_to(map_object)

            # Print owner's name on the left side pane
            map_object.get_root().html.add_child(folium.Element(f'<p><b>Owner:</b> {owner_name}</p>'))

            print("Properties for owner loaded successfully.")
        else:
            print("No properties found for the owner.")

# Function to load and display boundaries
def load_boundary(map_object, conn, asset_name, asset_type, color='blue', weight=2, fill_color='none'):
    with conn:
        cursor = conn.cursor()
        
        # Select rows with the specified asset_name and asset_type
        query = "SELECT coordinates_text FROM MapAssets WHERE asset_name = ? AND asset_type = ?"
        result = cursor.execute(query, (asset_name, asset_type)).fetchone()

        if result:
            coordinates_text = result[0]
            coordinates = coordinates_text.split(',')
            coordinates = [float(coord) for coord in coordinates]
            
            # Create a polygon from the coordinates
            polygon = Polygon(zip(coordinates[::2], coordinates[1::2]))

            # Create a GeoDataFrame for the boundary
            boundary_data = {'geometry': [polygon]}
            gdf = gpd.GeoDataFrame(boundary_data, crs="EPSG:4326")

            # Create a GeoJson layer for the boundary
            geojson_layer = folium.GeoJson(gdf, name=asset_name, style_function=lambda feature: {
                'fillColor': fill_color,
                'color': color,
                'weight': weight
            })

            # Create a FeatureGroup for the boundary
            boundary_group = folium.FeatureGroup(name=asset_name)
            geojson_layer.add_to(boundary_group)

            # Add FeatureGroup to the map
            boundary_group.add_to(map_object)

            print(f"{asset_name} loaded successfully.")
        else:
            print(f"{asset_name} not found in the database.")

# Function to load and display placemarks
def load_placemarks(map_object, conn):
    
    color_map = {
        # Add your placemark types and their corresponding valid colors
        'default': 'blue',  # default color if type doesn't match
        'church': 'red',
        'school': 'green',
        'business': 'orange',
        # Add more mappings as needed
    }

    with conn:
        cursor = conn.cursor()
        query = "SELECT * FROM MapPlacemarks"
        placemarks = cursor.fetchall()

        for placemark in placemarks:
            placemark_id, placemark_name, latitude, longitude, description, notes, placemark_type, specific_attributes = placemark

            # Get valid color from map or use default
            icon_color = color_map.get(placemark_type.lower(), 'blue')

            popup_html = f"<h4>{placemark_name}</h4><p>{description}</p>{specific_attributes}<p>{notes}</p>"

            folium.Marker(
                location=[latitude, longitude],
                tooltip=placemark_name,
                icon=folium.Icon(color=icon_color),  # Use mapped color
                popup=folium.Popup(popup_html)
            ).add_to(map_object)

            print(f"Placemark '{placemark_name}' loaded successfully.")

# Function to load and display sections as a layer
def load_sections(map_object, conn):
    # Create a GeoDataFrame to store section boundaries
    section_data = {'geometry': []}
    
    with conn:
        cursor = conn.cursor()
        # Select rows with asset_type 'Section' and non-empty coordinates_text
        query = "SELECT * FROM MapAssets WHERE asset_type = 'Section' AND coordinates_text IS NOT NULL"
        sections = cursor.execute(query).fetchall()

        for section in sections:
            coordinates_text = section[3]
            coordinates = coordinates_text.split(',')
            coordinates = [float(coord) for coord in coordinates]
            # Create a polygon from the coordinates
            polygon = Polygon(zip(coordinates[::2], coordinates[1::2]))
            section_data['geometry'].append(polygon)

    gdf = gpd.GeoDataFrame(section_data, crs="EPSG:4326")

    # Create a GeoJson layer for sections
    geojson_layer = folium.GeoJson(gdf, name="Sections", style_function=lambda feature: {
        'fillColor': 'none',  # Set fillColor to 'none' for no interior shading
        'color': 'green',       # Set the border color
        'weight': 1            # Set the border weight
    })

    # Add GeoJson layer to the map
    geojson_layer.add_to(map_object)


def generate_map(owner_id):
    plymouth_map = folium.Map(location=[42.371427, -83.468213], zoom_start=15)
    conn = sqlite3.connect('phoenix.db')

    load_sections(plymouth_map, conn)
    display_prop(plymouth_map, conn, owner_id)
    load_boundary(plymouth_map, conn, 'City of Plymouth', 'Boundary', color='blue')
    load_boundary(plymouth_map, conn, 'Plymouth Twp', 'Boundary', color='blue')
    load_boundary(plymouth_map, conn, 'City of Northville', 'Boundary', color='blue')
    load_boundary(plymouth_map, conn, 'Northville Twp', 'Boundary', color='blue')
    load_placemarks(plymouth_map, conn)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
    ).add_to(plymouth_map)

    folium.LayerControl().add_to(plymouth_map)
    conn.close()
    
    map_file = 'main_map.html'
    plymouth_map.save(map_file)
    return map_file




