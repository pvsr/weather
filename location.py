import configparser
import json

from typing import Mapping

import requests
from cachecontrol import CacheControl  # type: ignore

request_cache = CacheControl(requests.session())

BASE_URL = "https://api.weather.gov"
LOCAL = False

class Location:
    short_name: str
    long_name: str
    forecastUrl: str
    hourlyForecastUrl: str
    alertUrl: str

    def __init__(self, short_name: str, long_name: str, latitude: float, longitude: float):
        self.short_name = short_name
        self.long_name = long_name
        trunc = lambda f: format(f, '.4f')
        api = f"{BASE_URL}/points/{trunc(latitude)},{trunc(longitude)}"
        if LOCAL:
            with open('point', 'r') as f:
                data = json.load(f)['properties']
        else:
            data = request_cache.get(api).json()['properties']
        self.forecastUrl = data['forecast']
        self.hourlyForecastUrl = data['forecastHourly']
        # TODO really?
        self.alertUrl = data['forecastZone'].replace('/zones/forecast', '/alerts/active/zone')

    def hourly(self):
        if LOCAL:
            with open('hourly', 'r') as f:
                return json.load(f)
        req = request_cache.get(self.hourlyForecastUrl)
        return req.json()


    def forecast(self):
        if LOCAL:
            with open('forecast', 'r') as f:
                return json.load(f)
        req = request_cache.get(self.forecastUrl)
        return req.json()

    def alerts(self):
        if LOCAL:
            with open('alerts', 'r') as f:
                return json.load(f)
        req = request_cache.get(self.alertUrl)
        return req.json()


def read_locations() -> Mapping[str, Location]:
    c = configparser.ConfigParser()
    c.read('locations.ini')
    result = {}
    for s in c.sections():
        result[s] = Location(s, c[s]['long_name'], c[s].getfloat('latitude'), c[s].getfloat('longitude'))
    return result
