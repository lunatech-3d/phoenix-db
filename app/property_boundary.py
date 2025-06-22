class PropertyBoundaryCalculator:
    def __init__(self, connection):
        self.connection = connection

    def get_section_coordinates(self, section_number, township_id):
        """Fetch section coordinates from MapAssets"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT coordinates_text
            FROM MapAssets
            WHERE asset_type = 'Section'
            AND asset_name = ?
        """, (f"Section {section_number}",))
        return cursor.fetchone()[0]

    def get_boundary_data(self, township_id):
        """Fetch township boundary data"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT coordinates_text
            FROM MapAssets
            WHERE asset_type = 'Boundary'
            AND asset_name = (
                SELECT township_name 
                FROM Townships 
                WHERE township_id = ?
            )
        """, (township_id,))
        return cursor.fetchone()[0]

    def calculate_boundary_points(self, legal_desc_id):
        """Calculate GeoJSON coordinates for a legal description"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT section_number, quarter_section, quarter_quarter, half
            FROM LegalDescriptions
            WHERE description_id = ?
        """, (legal_desc_id,))
        desc_data = cursor.fetchone()

        section_coords = self.get_section_coordinates(desc_data[0])
        boundary = self.subdivide_section(section_coords, desc_data[1], desc_data[2], desc_data[3])
        
        return self.create_geojson_polygon(boundary)

    def save_boundary_geojson(self, legal_desc_id, geojson):
        """Save calculated boundary to GeoJSONData and link to legal description"""
        cursor = self.connection.cursor()
        cursor.execute("BEGIN")
        try:
            cursor.execute("""
                INSERT INTO GeoJSONData (geojson_text, feature_type)
                VALUES (?, 'POLYGON')
            """, (geojson,))
            geojson_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO GeoJSONLink (geojson_id, record_type, legal_description_id)
                VALUES (?, 'Deed', ?)
            """, (geojson_id, legal_desc_id))

            cursor.execute("COMMIT")
        except:
            cursor.execute("ROLLBACK")
            raise

    def subdivide_section(self, section_coords, quarter=None, quarter_quarter=None, half=None):
        """Calculate subdivision coordinates based on section coordinates"""
        if not any([quarter, quarter_quarter, half]):
            return section_coords
            
        points = self.parse_coordinates(section_coords)
        
        if half:
            points = self.calculate_half(points, half)
        if quarter:
            points = self.calculate_quarter(points, quarter)
        if quarter_quarter:
            points = self.calculate_quarter(points, quarter_quarter)
            
        return self.format_coordinates(points)

    def calculate_half(self, points, direction):
        """Calculate half section coordinates"""
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2
        
        if direction.startswith('E'):
            return [p for p in points if p[0] >= mid_x]
        elif direction.startswith('W'):
            return [p for p in points if p[0] <= mid_x]
        elif direction.startswith('N'):
            return [p for p in points if p[1] >= mid_y]
        else:  # South
            return [p for p in points if p[1] <= mid_y]

    def calculate_quarter(self, points, direction):
        """Calculate quarter section coordinates"""
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2
        
        if direction.startswith('NE'):
            return [p for p in points if p[0] >= mid_x and p[1] >= mid_y]
        elif direction.startswith('NW'):
            return [p for p in points if p[0] <= mid_x and p[1] >= mid_y]
        elif direction.startswith('SE'):
            return [p for p in points if p[0] >= mid_x and p[1] <= mid_y]
        else:  # SW
            return [p for p in points if p[0] <= mid_x and p[1] <= mid_y]

    def parse_coordinates(self, coord_text):
       """Convert coordinate text to list of (x,y) tuples"""
       coords = []
       pairs = coord_text.strip().split()
       for pair in pairs:
           x, y = pair.split(',')
           coords.append((float(x), float(y)))
       return coords

    def format_coordinates(self, points):
       """Convert list of coordinate tuples to formatted string"""
       return ' '.join(f"{x},{y}" for x, y in points)

    def parse_legal_description(self, desc_text):
       """Parse standardized legal description into components"""
       parts = {
           'section': None,
           'subdivisions': []
       }
       
       # Match patterns like "E 1/2 of the SW 1/4 of Section 26"
       matches = re.findall(r'((?:N|S|E|W){1,2})\s+1/(\d)\s+', desc_text)
       section_match = re.search(r'Section\s+(\d+)', desc_text)
       
       if section_match:
           parts['section'] = int(section_match.group(1))
           
       for direction, division in matches:
           subdiv_type = 'half' if division == '2' else 'quarter'
           parts['subdivisions'].append({
               'direction': direction,
               'type': subdiv_type
           })
           
       return parts

    def create_geojson_polygon(self, coordinates):
       """Create GeoJSON polygon from coordinate string"""
       return {
           "type": "Feature",
           "geometry": {
               "type": "Polygon",
               "coordinates": [self.parse_coordinates(coordinates)]
           }
       }