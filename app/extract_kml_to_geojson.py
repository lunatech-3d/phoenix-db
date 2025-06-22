import os
import geopandas as gpd
import json
import sqlite3
from pykml import parser
from lxml import etree  # Helps handle namespaces properly

# Input & Output Paths (UPDATE THESE)
input_kml_directory = r"C:\Users\dwill\Downloads"  # Change to your KML folder
output_geojson_directory = r"C:\Users\dwill\Downloads\1860 Data"  # Where GeoJSON files will be saved

# Ensure output directory exists
os.makedirs(output_geojson_directory, exist_ok=True)

def extract_kml_to_geojson(kml_file, output_file):
    """Extracts polygons and corresponding person_id from a Section KML file."""
    try:
        print(f"📂 Processing: {kml_file}")

        with open(kml_file, 'r', encoding='utf-8') as file:
            root = parser.parse(file).getroot()

        ns = {"kml": "http://www.opengis.net/kml/2.2"}

        # Find all Placemark elements (regardless of nesting)
        placemarks = root.findall(".//kml:Placemark", ns)

        if not placemarks:
            print(f"⚠️ Warning: No Placemark elements found in {kml_file}")
            return  # Skip to next file

        features = []

        for placemark in placemarks:
            # Extract the name of the property owner
            name = placemark.find("kml:name", ns).text if placemark.find("kml:name", ns) is not None else "Unknown"

            # Extract description and split it into person_id and additional info
            description = placemark.find("kml:description", ns).text if placemark.find("kml:description", ns) is not None else ""

            # Extract person_id from description (format: ID:11614)
            person_id = None
            additional_info = ""
            if "ID:" in description:
                try:
                    parts = description.split("ID:")  # Split on "ID:"
                    person_id = int(parts[1].split()[0])  # Extract the number after "ID:"
                    additional_info = parts[1][len(str(person_id)):].strip()  # Extract remaining description
                except ValueError:
                    print(f"⚠️ Unable to extract person_id from {description}")
            else:
                additional_info = description.strip()  # If no ID, use full description as additional info

            # Extract coordinates
            coords_element = placemark.find(".//kml:coordinates", ns)
            if coords_element is None:
                print(f"⚠️ Warning: No coordinates found for {name}")
                continue  # Skip this Placemark

            coords_text = coords_element.text.strip()
            coord_pairs = [[float(c) for c in coord.split(",")[:2]] for coord in coords_text.split()]

            # Convert to GeoJSON format
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coord_pairs]
                },
                "properties": {
                    "name": name,
                    "person_id": person_id,
                    "additional_info": additional_info
                }
            }
            features.append(feature)

        # Create GeoJSON collection
        geojson_data = {"type": "FeatureCollection", "features": features}

        # Save to output GeoJSON file
        with open(output_file, "w", encoding="utf-8") as geojson_file:
            json.dump(geojson_data, geojson_file, indent=4)

        print(f"✅ Converted: {kml_file} → {output_file}")

    except Exception as e:
        print(f"❌ Error processing {kml_file}: {e}")

# Process all Section KML files
print(f"📂 Checking for KML files in: {input_kml_directory}")

for file in os.listdir(input_kml_directory):
    if file.endswith(".kml"):
        print(f"🔍 Found KML file: {file}")  # Debugging print
        input_file = os.path.join(input_kml_directory, file)
        output_file = os.path.join(output_geojson_directory, file.replace(".kml", ".geojson"))
        extract_kml_to_geojson(input_file, output_file)

print("✅ All Section KML files processed successfully!")
