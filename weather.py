from datetime import datetime, date, timedelta

from flask import Flask, render_template
import requests
from cachecontrol import CacheControl

app = Flask(__name__)
request_cache = CacheControl(requests.session())

base_url = "https://api.weather.gov"

# afaict there doesn't seem to be an easy way to go from grid points to zone id
DEFAULT_ZONE_ID = "DCZ001"
DEFAULT_OFFICE = "LWX"
DEFAULT_GRID_X = 95
DEFAULT_GRID_Y = 72


@app.route("/")
def weather():
    return render_template(
        "weather.html",
        forecast=forecast(DEFAULT_OFFICE, DEFAULT_GRID_X, DEFAULT_GRID_Y),
        alerts=alerts(DEFAULT_ZONE_ID),
    )


def alerts(zone_id: str):
    api = "{}/alerts/active/zone/{}".format(base_url, zone_id)
    req = request_cache.get(api)
    json = req.json()

    if len(json["features"]) == 0:
        return None

    return map(alert_properties, json["features"])


def forecast(office: str, grid_x: int, grid_y: int):
    api = "{}/gridpoints/{}/{},{}/forecast".format(base_url, office, grid_x, grid_y)
    req = request_cache.get(api)
    json = req.json()

    forecast = json["properties"]["periods"]
    for period in forecast:
        if period["temperatureUnit"] == "F":
            period["fahrenheit"] = period["temperature"]
            period["celsius"] = round((period["temperature"] - 32) * (5 / 9))
        elif period["temperatureUnit"] == "C":
            period["celsius"] = period["temperature"]
            period["fahrenheit"] = round(period["temperature"] * (9 / 5) + 32)

        del period["temperatureUnit"]
        del period["temperature"]
        period["kelvin"] = period["celsius"] + 273.15
    return forecast


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


def pretty_date(d_str: datetime) -> str:
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
        day = "%b {}".format(ordinal(d.day))

    return d.strftime("%R {}".format(day))


def ordinal(n: int) -> str:
    if n % 10 == 1 and n != 11:
        suff = "st"
    elif n % 10 == 2 and n != 12:
        suff = "nd"
    elif n % 10 == 3 and n != 13:
        suff = "rd"
    else:
        suff = "th"
    return "{}{}".format(n, suff)
