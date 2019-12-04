import configparser
import json

from typing import Mapping

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

    def __init__(self, short_name: str, long_name: str, latitude: float, longitude: float):
        self.short_name = short_name
        self.long_name = long_name

        trunc = lambda f: format(f, '.4f')
        url = f"{BASE_URL}/points/{trunc(latitude)},{trunc(longitude)}"
        data = fetch_json(url, 'point')['properties']

        self.forecast_url = data['forecast']
        self.hourly_forecast_url = data['forecastHourly']
        # TODO really?
        self.alert_url = data['forecastZone'].replace('/zones/forecast', '/alerts/active/zone')

    def hourly(self):
        return fetch_json(self.hourly_forecast_url, 'hourly')

    def forecast(self):
        return fetch_json(self.forecast_url, 'forecast')

    def alerts(self):
        return fetch_json(self.alert_url, 'alerts')


LOCAL = False
def fetch_json(url: str, default: str):
    if LOCAL:
        with open(default, 'r') as local_data:
            return json.load(local_data)
    else:
        return REQUEST_CACHE.get(url).json()


def read_locations() -> Mapping[str, Location]:
    conf = configparser.ConfigParser()
    conf.read('locations.ini')
    result = {}
    for long_name in conf.sections():
        section = conf[long_name]
        result[long_name] = Location(long_name,
                                     section.get('long_name', long_name),
                                     section.getfloat('latitude'),
                                     section.getfloat('longitude'))
    return result
