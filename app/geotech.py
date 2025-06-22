import sqlite3
import json
import sys
from config import DB_PATH
from pathlib import Path
import webbrowser

# Define paths
script_dir = Path(__file__).resolve().parent
database_path = script_dir / DB_PATH
output_html_path = script_dir / 'interactive_map.html'

# Function to get unique asset types from database
def get_asset_types():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT asset_type FROM MapAssets WHERE coordinates_text IS NOT NULL")
    types = [row[0] for row in cursor.fetchall()]
    cursor.close()
    connection.close()
    return types

# Function to query MapAssets table
def query_map_assets():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    query = """
    SELECT asset_name, asset_type, coordinates_text
    FROM MapAssets
    WHERE coordinates_text IS NOT NULL
    """
    cursor.execute(query)
    assets = cursor.fetchall()
    cursor.close()
    connection.close()
    return assets

# Function to generate style based on asset type
def get_style_for_asset_type(asset_type):
    style_map = {
        'Section': {
            'color': '#ff7800',
            'weight': 2,
            'opacity': 0.8,
            'fillOpacity': 0.35
        },
        'Boundary': {
            'color': '#0000ff',
            'weight': 3,
            'opacity': 1,
            'fillOpacity': 0.2
        },
        'Park': {
            'color': '#00ff00',
            'weight': 2,
            'opacity': 0.7,
            'fillOpacity': 0.4
        }
    }
    return style_map.get(asset_type, {
        'color': '#777777',
        'weight': 2,
        'opacity': 0.8,
        'fillOpacity': 0.3
    })

# Function to generate GeoJSON features
def generate_geojson_feature(asset_name, asset_type, coordinates_text):
    try:
        coordinates = [float(coord) for coord in coordinates_text.split(',')]
        coordinate_pairs = [[coordinates[i], coordinates[i + 1]] for i in range(0, len(coordinates), 2)]
        if len(coordinate_pairs) >= 4 and coordinate_pairs[0] != coordinate_pairs[-1]:
            coordinate_pairs.append(coordinate_pairs[0])
        
        style = get_style_for_asset_type(asset_type)
        
        geojson_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinate_pairs]
            },
            "properties": {
                "name": asset_name,
                "type": asset_type,
                "style": style
            }
        }
        return geojson_feature
    except ValueError as e:
        print(f"Error processing asset '{asset_name}': {e}")
        return None

# Function to create the HTML content
def create_html(assets):
    # Get unique asset types
    asset_types = get_asset_types()
    
    # Initialize JavaScript code for layers
    layers_js = ""
    
    # Initialize the groupedOverlays object with asset types
    grouped_overlays_init = ""
    for asset_type in asset_types:
        grouped_overlays_init += f'groupedOverlays["{asset_type}"] = {{}};\n'    
    
    # Organize assets by type and name
    assets_by_type = {}
    for name, asset_type, coords in assets:
        if asset_type not in assets_by_type:
            assets_by_type[asset_type] = {}
        feature = generate_geojson_feature(name, asset_type, coords)
        if feature:
            if name not in assets_by_type[asset_type]:
                assets_by_type[asset_type][name] = []
            assets_by_type[asset_type][name].append(feature)

    # Generate layer definitions and add to groupedOverlays
    for asset_type, assets in assets_by_type.items():
        for name, features in assets.items():
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            layer_var = f"layer_{name.replace(' ', '_')}"
            
            # Add layer definition
            layers_js += f"""
            var {layer_var} = L.geoJson({json.dumps(geojson)}, {{
                style: function(feature) {{
                    return feature.properties.style;
                }},
                onEachFeature: function(feature, layer) {{
                    layer.bindPopup(feature.properties.name);
                }}
            }});
            """
            
            # Add to groupedOverlays
            layers_js += f'groupedOverlays["{asset_type}"]["{name}"] = {layer_var};\n'

    # Read template file
    with open(script_dir / 'map_template.html', 'r') as template_file:
        template = template_file.read()

    # Replace placeholders
    html_content = template.replace('{layers_js}', layers_js)
    html_content = html_content.replace('{grouped_layers_js}', grouped_overlays_init)
    
    return html_content

# Main function
def generate_and_open_map():
    assets = query_map_assets()
    html_content = create_html(assets)
    with open(output_html_path, 'w') as f:
        f.write(html_content)
    webbrowser.open(output_html_path.as_uri())
    print(f"Map saved to {output_html_path} and opened in the default browser.")

if __name__ == "__main__":
    generate_and_open_map()
