import configparser
import json
from collections.abc import Mapping
from importlib.resources import files

import requests
from cachecontrol import CacheControl  # type: ignore

REQUEST_CACHE = CacheControl(requests.session())

BASE_URL = "https://api.weather.gov"


class Location:
    short_name: str
    long_name: str
    forecast_url: str
    hourly_forecast_url: str
    alert_url: str

    def __init__(
        self, short_name: str, long_name: str, latitude: float, longitude: float
    ) -> None:
        self.short_name = short_name
        self.long_name = long_name

        def trunc(f):
            return format(f, ".4f")

        url = f"{BASE_URL}/points/{trunc(latitude)},{trunc(longitude)}"
        data = fetch_json(url, "point")["properties"]

        self.forecast_url = data["forecast"]
        self.hourly_forecast_url = data["forecastHourly"]
        # TODO really?
        self.alert_url = data["forecastZone"].replace(
            "/zones/forecast", "/alerts/active/zone"
        )

    def hourly(self):
        return fetch_json(self.hourly_forecast_url, "hourly")

    def forecast(self):
        return fetch_json(self.forecast_url, "forecast")

    def alerts(self):
        return fetch_json(self.alert_url, "alerts")


LOCAL = False


def fetch_json(url: str, default: str):
    if LOCAL:
        with open(default) as local_data:
            return json.load(local_data)
    else:
        # print(f"requesting {url}")
        resp = REQUEST_CACHE.get(url)
        # print(resp)
        return resp.json()


def read_locations() -> Mapping[str, Location]:
    conf = configparser.ConfigParser()
    conf.read_string(files("weather").joinpath("locations.ini").read_text())
    result = {}
    for long_name in conf.sections():
        section = conf[long_name]
        result[long_name] = Location(
            long_name,
            section.get("long_name", long_name),
            section.getfloat("latitude"),
            section.getfloat("longitude"),
        )
    return result
