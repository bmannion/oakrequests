"""Parse weather data from NOAA API."""

import os
from pathlib import Path

import pandas as pd
import requests

NOAA_TOKEN = os.getenv("NOAA_TOKEN")


def check_station_data():
    """Check if station JSON is within data directory."""

    station_file = "data/station_coords.json"
    if Path(station_file).exists():
        print(f"{station_file} exists!")
    else:
        coords = [37.7584, -122.3086, 37.8647, -122.1551]
        station_response = get_stations(
            coords, start_date="2024-01-01", end_date="2024-02-29", token=NOAA_TOKEN
        )
        station_df = pd.DataFrame(station_response.json()["results"])
        station_df.to_json(station_file)


def get_stations(coords: list[float], start_date: str, end_date: str, token: str):
    """Request and return NOAA stations around `coords`.

    Example coords: 37.7584,-122.3086,37.8647,-122.1551
    Example dates: 2024-01-01 ; 2024-02-29

    Parameters
    ----------
    coords : [SE lat, SE long, NW lat, NW long]
    start_date : YYYY-mm-dd
    end_date : YYYY-mm-dd
    """

    se_lat, se_lon, nw_lat, nw_lon = coords[0], coords[1], coords[2], coords[3]

    # GPS coord pairs in `extent` are from SE lat,long to NW lat,long
    station_url = (
        "https://www.ncei.noaa.gov/cdo-web/api/v2/stations?extent="
        f"{se_lat},{se_lon},{nw_lat},{nw_lon}&"
        f"startdate={start_date}&enddate={end_date}&"
        "sortfield=datacoverage&"
        "sortorder=desc"
    )

    return requests.get(station_url, headers={"token": token}, timeout=10)


class Station:
    """Weather station"""

    def __init__(self, name, station_id):
        self.name = name
        self.station_id = station_id
        self.get_station_coords()

    def get_station_coords(self):
        """Parse table station-specific coords."""
        df = Station.list_stations()
        self.latitude = df.loc[df["name"] == self.name, "latitude"].values[  # pylint: disable=no-member
            0
        ]
        self.longitude = df.loc[df["name"] == self.name, "longitude"].values[ # pylint: disable=no-member
            0
        ]

    @staticmethod
    def list_stations():
        """Display local station table."""
        station_file = "data/station_coords.json"
        return pd.read_json(station_file)

    def get_weather(self, start_date, end_date, token):
        """Request weather from specific station."""
        datid = "GHCND"
        dattypeid = "PRCP"
        units = "standard"
        results_limit = 1000

        data_url = (
            f"https://www.ncei.noaa.gov/cdo-web/api/v2/data?datasetid={datid}&"
            f"datatypeid={dattypeid}&"
            f"stationid={self.station_id}&startdate={start_date}&enddate={end_date}&"
            f"units={units}&"
            f"limit={results_limit}"
        )
        response = requests.get(data_url, headers={"token": token}, timeout=10)
        df = pd.DataFrame(response.json()["results"])
        df["name"] = self.name

        df["date"] = pd.to_datetime(df["date"])
        _full_dates_df = pd.DataFrame(
            index=pd.date_range(start=start_date, end=end_date, freq="D")
        )
        merged_df = _full_dates_df.join(df.set_index("date"))

        merged_df = (
            merged_df.fillna(
                {
                    "station": self.station_id,
                    "name": self.name,
                    "datatype": dattypeid,
                }  # , axis=0
            )
            .reset_index(drop=False)
            .rename(columns={"index": "date"})
        )
        return merged_df


if __name__ == "__main__":
    check_station_data()
    print(Station.list_stations())
