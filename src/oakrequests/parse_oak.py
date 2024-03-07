"""Get and parse city of Oakland 311 data."""

import datetime
import geopandas as gpd # type: ignore
import pandas as pd


class Oak311:
    """Oakland 311"""
    def __init__(self, filename):
        self.load_data(filename)

    def load_data(self, filename):
        """Load requests table."""
        df = pd.read_json(filename)
        df["latlon"] = df["reqaddress"].apply(
            lambda x: pd.NA if pd.isna(x) else (x["latitude"], x["longitude"])
        )
        df["daytime"] = pd.to_datetime(df["datetimeinit"]).apply(
            lambda x: x.strftime("%Y-%m-%d %I:%M:%S %p")
        )
        self.data = df

    def filter_data(self, description_query):
        """Filter table by `description_query`"""
        filtered_df = self.data.loc[ # pylint: disable=no-member
            (self.data["description"].str.contains(description_query, case=False))
            & ~(self.data["reqaddress"].isna()),
            [
                "datetimeinit",
                "source",
                "description",
                "reqcategory",
                "reqaddress",
                "status",
                "councildistrict",
                "beat",
                "probaddress",
                "latlon",
                "daytime",
            ],
        ].reset_index(drop=True)

        return filtered_df


def get_data_df(date_request: str = "2024-01-01") -> pd.DataFrame:
    """Return Oakland 311 request as DataFrame."""

    results_limit = 50000
    city_data_url = (
        "https://data.oaklandca.gov/resource/quth-gb8e.json?"
        f"$limit={results_limit}&$where=datetimeinit%20"
        ">"
        "%20%27"
        f"{date_request}T00:00:00"
        "%27"
    )

    return pd.read_json(city_data_url)


def save_oak311_data(oak311_df, description=None):
    """Save requested table as JSON."""
    save_date = datetime.datetime.today().strftime("%Y-%m-%d_%H:%M:%S")
    oak311_df.to_json(f"data/oakland311_{description}_{save_date}.json")


def load_districts(filename: str):
    """
    some district borders differ from what's shown here:
    https://oakgis.maps.arcgis.com/apps/instant/lookup/index.html?appid=da589a352c8641459af8a0f890398d44
    """
    districts_df = gpd.read_file(filename)
    districts_df["fullname"] = districts_df["fullname"].str.capitalize()

    return districts_df


def get_city_geom(file_shp: str, city: str):
    """Get geometry for `city`."""
    gdf = gpd.read_file(file_shp)
    return gdf.loc[
        gdf["NAMELSAD"].str.contains(f"{city} city"), "geometry"
    ].__geo_interface__


if __name__ == "__main__":
    oak311 = Oak311("data/oak311_20240101to20240306_2024-03-06_115017.json")
    potholes = oak311.filter_data("Poth")
    print(potholes)
