# geo_map.py
import folium
import geopandas as gpd
from shapely.geometry import Polygon

class Map:
    def __init__(self, initial_location=(42.371427, -83.468213), zoom_start=15):
        self.map = folium.Map(location=initial_location, zoom_start=zoom_start)
        self.active_layers = {}

    def add_property_boundary(self, coordinates_text, owner_name, year):
        coordinates = [float(coord) for coord in coordinates_text.split(',')]
        polygon = Polygon(zip(coordinates[::2], coordinates[1::2]))
        property_data = {'geometry': [polygon]}
        gdf = gpd.GeoDataFrame(property_data, crs="EPSG:4326")

        layer_name = f"{owner_name}'s Property ({year})"
        layer_id = f"property_{owner_name.replace(' ', '_')}_{year}"
        property_layer = folium.GeoJson(
            gdf,
            name=layer_name,
            style_function=lambda feature: {
                'fillColor': 'none',
                'color': 'red',
                'weight': 2
            },
            tooltip=layer_name
        )
        property_layer.add_to(self.map)
        property_layer.get_root().attr['data-layer-id'] = layer_id
        self.active_layers[layer_id] = property_layer
        return layer_id

    def show(self):
        map_file = 'phoenix_map.html'
        self.map.save(map_file)
        webbrowser.open('file://' + os.path.abspath(map_file), new=2)