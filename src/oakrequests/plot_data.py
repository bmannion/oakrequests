"""Plot weather and city data."""

import folium  # type: ignore
from folium import plugins
import matplotlib.colors as mcolors

import parse_oak  # type: ignore # pylint: disable=import-error
import parse_weather  # type: ignore # pylint: disable=import-error


class OakMap:
    """Oakland map"""

    def __init__(self, location=None, zoom_start=12):
        self.map = folium.Map(location=location, zoom_start=zoom_start)

    def add_city(self, city_geom, descr=None, show=False):
        """Add city layer."""
        folium.GeoJson(
            city_geom,
            name=descr,
            show=show,
            style_function=lambda x: {"stroke": False, "fillOpacity": 0.2},
        ).add_to(self.map)

    def add_districts(self, districts_gpd, descr="Districts", show=False):
        """Add districts layer."""
        district_cmap = dict(
            list(
                zip(
                    sorted(districts_gpd["fullname"].values),
                    mcolors.TABLEAU_COLORS.values(),
                )
            )
        )
        folium.GeoJson(
            districts_gpd,
            name=descr,
            tooltip=folium.GeoJsonTooltip(["fullname"], aliases=["Name"]),
            style_function=lambda x: {
                "stroke": False,
                "fillColor": district_cmap[x["properties"]["fullname"]],
                "fillOpacity": 0.25,
            },
            show=show,
        ).add_to(self.map)

    def add_events(self, oak311_df, descr=None, show=True):
        """Add events layer."""
        events_feature = plugins.MarkerCluster(name=descr)
        marker_html = "table table-striped table-hover table-condensed table-responsive"
        for row in oak311_df.iterrows():
            folium.Marker(
                location=row[1]["latlon"],
                icon=folium.Icon(color="gray", prefix="fa", icon="exclamation"),
                popup=folium.Popup(
                    row[1][
                        [
                            "daytime",
                            "source",
                            "description",
                            "reqcategory",
                            "status",
                            "councildistrict",
                            "beat",
                            "probaddress",
                            "latlon",
                        ]
                    ]
                    .to_frame()
                    .to_html(header=False, classes=marker_html),
                    max_width=300,
                ),
                tooltip=row[1]["daytime"],
                show=show,
            ).add_to(events_feature)
        events_feature.add_to(self.map)

    def add_heatmap(self, oak311_df, descr="Heatmap", show=True):
        """Add heatmaps layer."""
        lat_long = list(
            oak311_df["reqaddress"].apply(lambda x: (x["latitude"], x["longitude"]))
        )
        plugins.HeatMap(
            data=lat_long,
            min_opacity=0.6,
            max_zoom=14,
            radius=25,
            blur=10,
            name=descr,
            show=show,
        ).add_to(self.map)

    def add_stations(self, station_df, show=True):
        """Add stations layer."""
        station_feature = folium.FeatureGroup(name="Weather stations", show=show)
        for row in station_df.iterrows():
            lat, lon = row[1]["latitude"], row[1]["longitude"]
            station_name = row[1]["name"]
            station_id = row[1]["id"]
            station_nameid = f"{station_name} ({station_id})"
            station_coverage = (
                f"Coverage for {row[1]['mindate']} "
                f"to {row[1]['maxdate']} : {row[1]['datacoverage']}"
            )
            icon = folium.Icon(
                prefix="fa",
                icon="satellite",
                icon_color="black",
                color="black",
                icon_size=(10, 10),
                shadow_size=(0, 0),
            )
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(html=station_coverage, max_width=300),
                tooltip=station_nameid,
                icon=icon,
            ).add_to(station_feature)
        station_feature.add_to(self.map)

    def render_map(self):
        """Display map."""
        folium.LayerControl().add_to(self.map)
        return self.map

    def save_map(self, title, filename):
        """Save map to `filename`."""
        folium.LayerControl().add_to(self.map)
        title_html = (
            f'<h4 style="position:absolute;z-index:100000;'
            f'left:40vw;color:black;opacity:0.7">{title}</h1>'
        )
        self.map.get_root().html.add_child(folium.Element(title_html))
        self.map.save(filename)


def generate_imap(filename):
    """Save example map to `filename`."""
    oak311 = parse_oak.Oak311("data/oak311_20240101to20240306_2024-03-06_115017.json")
    potholes = oak311.filter_data("Poth").query('datetimeinit < "2024-03-01"')
    stations = parse_weather.Station.list_stations()
    districts = parse_oak.load_districts("data/oak_districts.geojson")
    oakcity = parse_oak.get_city_geom(
        file_shp="data/tl_2023_06_place/tl_2023_06_place.shp", city="Oakland"
    )

    city_map = OakMap(location=[37.8123, -122.2635])
    city_map.add_stations(stations)
    city_map.add_events(potholes, "Potholes")
    city_map.add_heatmap(potholes, "heatmap")
    city_map.add_districts(districts, "Districts", False)
    city_map.add_city(oakcity, "Oakland")
    city_map.save_map("Potholes from OAK311 (Jan 2024 - Feb 2024)", filename)


if __name__ == "__main__":
    generate_imap("docs/citymap.html")
