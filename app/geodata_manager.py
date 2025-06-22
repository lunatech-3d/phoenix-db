import sqlite3
import json

from app.config import DB_PATH, PATHS
from app.property_boundary import PropertyBoundaryCalculator

class GeoDataManager:
    """Manager class for handling all geographic data operations"""
    
    FEATURE_TYPES = {
        'POINT': {'icon': '📍', 'name': 'Point Location'},
        'LINE': {'icon': '〰️', 'name': 'Line Feature'},
        'POLYGON': {'icon': '⬡', 'name': 'Boundary'},
    }

    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.calculator = PropertyBoundaryCalculator(connection)
        self.preview_size = (400, 300)  # Default preview dimensions

    def get_features_for_record(self, record_type, record_id, segment_id=None):
        """Get all GeoJSON features for a record/segment"""
        query = """
            SELECT gd.geojson_id, gd.geojson_text, gd.feature_type, 
                   gd.description, gl.legal_description_id
            FROM GeoJSONData gd
            JOIN GeoJSONLink gl ON gd.geojson_id = gl.geojson_id
            WHERE gl.record_type = ? AND gl.record_id = ?
        """
        params = [record_type, record_id]
        
        if segment_id is not None:
            query += " AND gl.legal_description_id = ?"
            params.append(segment_id)
            
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def save_feature(self, record_type, record_id, feature_type, coords_text, 
                    description=None, segment_id=None):
        """Save a new geographic feature"""
        try:
            # Validate coordinates
            if not self.validate_coordinates(coords_text, feature_type):
                raise ValueError("Invalid coordinate format for feature type")

            # Create GeoJSON structure
            geojson = self.create_geojson(coords_text, feature_type)

            # Start transaction
            self.cursor.execute("BEGIN")

            # Insert into GeoJSONData
            self.cursor.execute("""
                INSERT INTO GeoJSONData (geojson_text, feature_type, description)
                VALUES (?, ?, ?)
            """, (json.dumps(geojson), feature_type, description))
            
            geojson_id = self.cursor.lastrowid

            # Create link record
            self.cursor.execute("""
                INSERT INTO GeoJSONLink (
                    geojson_id, record_type, record_id, legal_description_id
                ) VALUES (?, ?, ?, ?)
            """, (geojson_id, record_type, record_id, segment_id))

            self.connection.commit()
            return geojson_id

        except Exception as e:
            self.connection.rollback()
            raise

    def update_feature(self, geojson_id, feature_type, coords_text, description=None):
        """Update an existing geographic feature"""
        try:
            # Validate coordinates
            if not self.validate_coordinates(coords_text, feature_type):
                raise ValueError("Invalid coordinate format for feature type")

            # Create GeoJSON structure
            geojson = self.create_geojson(coords_text, feature_type)

            # Update the GeoJSON data
            self.cursor.execute("""
                UPDATE GeoJSONData 
                SET geojson_text = ?, feature_type = ?, description = ?
                WHERE geojson_id = ?
            """, (json.dumps(geojson), feature_type, description, geojson_id))

            self.connection.commit()
            return True

        except Exception as e:
            self.connection.rollback()
            raise

    def update_preview(self):
        """Update canvas preview based on current coordinates"""
        self.preview_canvas.delete('all')
        coords_text = self.coords_text.get('1.0', tk.END).strip()
        if not coords_text:
            return

        try:
            coords = self.parse_coordinates(coords_text)
            scaled_coords = self.scale_coordinates(coords)
            self.draw_feature(scaled_coords)
        except ValueError:
            pass

    def delete_feature(self, geojson_id):
        """Delete a geographic feature and its link"""
        try:
            self.cursor.execute("BEGIN")
            
            # Delete the link first
            self.cursor.execute("DELETE FROM GeoJSONLink WHERE geojson_id = ?", 
                              (geojson_id,))
            
            # Then delete the data
            self.cursor.execute("DELETE FROM GeoJSONData WHERE geojson_id = ?", 
                              (geojson_id,))

            self.connection.commit()
            return True

        except Exception as e:
            self.connection.rollback()
            raise

    def validate_coordinates(self, coords_text, feature_type):
        """Validate coordinate input based on feature type"""
        try:
            coords = [float(x.strip()) for x in coords_text.replace('\n', ' ').split(',')]
            
            if feature_type == 'POINT':
                return len(coords) == 2
            elif feature_type == 'LINE':
                return len(coords) >= 4 and len(coords) % 2 == 0
            elif feature_type == 'POLYGON':
                return len(coords) >= 6 and len(coords) % 2 == 0
            
            return False

        except ValueError:
            return False

    def create_geojson(self, coords_text, feature_type):
        """Create GeoJSON structure from coordinates"""
        coords = [float(x.strip()) for x in coords_text.replace('\n', ' ').split(',')]
        coord_pairs = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]

        if feature_type == 'POINT':
            return {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": coord_pairs[0]
                }
            }
        elif feature_type == 'LINE':
            return {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coord_pairs
                }
            }
        elif feature_type == 'POLYGON':
            # Ensure the polygon is closed
            if coord_pairs[0] != coord_pairs[-1]:
                coord_pairs.append(coord_pairs[0])
            return {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coord_pairs]
                }
            }
        else:
            raise ValueError(f"Unsupported feature type: {feature_type}")

    def generate_preview(self, geojson_data, size=None):
        """Generate SVG preview for a feature"""
        size = size or self.preview_size
        # SVG generation implementation will be added in next part
        pass