from datetime import date, datetime, timedelta
from typing import NamedTuple, Optional, Tuple
import json

import requests
from cachecontrol import CacheControl  # type: ignore
from flask import Flask, render_template

app = Flask(__name__)
request_cache = CacheControl(requests.session())

BASE_URL = "https://api.weather.gov"
LOCAL = False


class Location(NamedTuple):
    name: str
    zone_id: str
    office: str
    grid_xy: Tuple[int, int]

    def hourly(self):
        if LOCAL:
            with open('hourly', 'r') as f:
                return json.load(f)
        api = f"{BASE_URL}/gridpoints/{self.office}/{self.grid_xy[0]},{self.grid_xy[1]}/forecast/hourly"
        req = request_cache.get(api)
        return req.json()


    def forecast(self):
        if LOCAL:
            with open('forecast', 'r') as f:
                return json.load(f)
        api = f"{BASE_URL}/gridpoints/{self.office}/{self.grid_xy[0]},{self.grid_xy[1]}/forecast"
        req = request_cache.get(api)
        return req.json()

    def alerts(self):
        if LOCAL:
            with open('alerts', 'r') as f:
                return json.load(f)
        api = f"{BASE_URL}/alerts/active/zone/{self.zone_id}"
        req = request_cache.get(api)
        return req.json()

def forecasts(data):
    forecast_data = data["properties"]["periods"]
    for period in forecast_data:
        if period["temperatureUnit"] == "F":
            period["fahrenheit"] = period["temperature"]
            period["celsius"] = round((period["temperature"] - 32) * (5 / 9))
        elif period["temperatureUnit"] == "C":
            period["celsius"] = period["temperature"]
            period["fahrenheit"] = round(period["temperature"] * (9 / 5) + 32)

        del period["temperatureUnit"]
        del period["temperature"]
        period["kelvin"] = period["celsius"] + 273.15

    return forecast_data

# afaict there doesn't seem to be an easy way to go from grid points to zone id
DEFAULT_PRESET = "Somerville"
PRESETS = {
    "DC": Location("Washington, DC", "DCZ001", "LWX", (95, 72)),
    "Somerville": Location("Somerville, MA", "MAZ014", "BOX", (69, 77)),
}


@app.route("/")
def default_weather():
    return weather(None)


@app.route("/<key>")
def weather(key: Optional[str]):
    if not key or key not in PRESETS:
        key = DEFAULT_PRESET
    data = PRESETS[key]

    alerts = map(alert_properties, data.alerts()["features"] or [])

    return render_template(
        "weather.html",
        current_preset=key,
        presets=PRESETS.keys(),
        location=data.name,
        forecast=forecasts(data.forecast()),
        hourly=forecasts(data.hourly())[0:24],
        alerts=alerts,
    )


@app.template_filter('quote')
def quote(s):
    return f'"{s}"'


def alert_properties(feature):
    # definitely useful
    # onset: datetime
    # expires: datetime
    # event: Flash Flood Watch | ...
    # severity: Severe | ???
    # maybe useful
    # affectedZones: [zoneId]
    # areaDesc: readable affectedZones
    # sent: datetime
    # effective: datetime
    # status: Actual | ???
    # messageType: Update | ???
    # category: Met (ie meterological?) | ???
    # certainty: Possible | ???
    # urgency: Future | ???
    # response: Monitor | ???
    # headline: Watch issued at time until time by office
    # description
    # instruction
    properties = feature["properties"]
    # TODO more detail. event can be "Special Weather Statement", which isn't
    # very useful on its own
    str_props = ["event", "severity"]
    date_props = ["onset", "expires"]
    return {
        **{k: properties[k] for k in str_props},
        **{k: pretty_date(properties[k]) for k in date_props},
    }


def pretty_date(d_str: str) -> str:
    try:
        d = datetime.fromisoformat(d_str)
    except ValueError as e:
        return d_str

    if d.date() == date.today():
        day = "today"
    elif d.date() == date.today() + timedelta(days=1):
        day = "tomorrow"
    elif d.date() > date.today() and d.date() - date.today() < timedelta(days=7):
        day = "%A"
    else:
        day = f"%b {ordinal(d.day)}"

    return d.strftime(f"%R {day}")


def ordinal(n: int) -> str:
    if n % 10 == 1 and n != 11:
        suff = "st"
    elif n % 10 == 2 and n != 12:
        suff = "nd"
    elif n % 10 == 3 and n != 13:
        suff = "rd"
    else:
        suff = "th"
    return f"{n}{suff}"
