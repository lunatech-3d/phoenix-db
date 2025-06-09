# geo_control_panel.py
import altair as alt
from ipyvega import VegaLite

class ControlPanel:
    def __init__(self, map_instance):
        self.map = map_instance
        self.vega_panel = VegaLite()
        self.vega_panel.display()

    def add_layer_control(self, layer_id, layer_name, color):
        data = alt.Data(values=[
            {"x": 0, "y": 0, "color": layer_name},
            {"x": 1, "y": 0, "color": layer_name}
        ])

        chart = alt.Chart(data).mark_rect().encode(
            x="x:Q",
            y="y:Q",
            color="color:N"
        )

        self.vega_panel.vega = chart.to_json()
        self.map.active_layers[layer_id].get_root().attr['data-layer-id'] = layer_id

    def show(self):
        self.vega_panel.display()