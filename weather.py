from datetime import datetime, date, timedelta

from flask import Flask, render_template
import requests
from cachecontrol import CacheControl

app = Flask(__name__)
request_cache = CacheControl(requests.session())

BASE_URL = "https://api.weather.gov"

# afaict there doesn't seem to be an easy way to go from grid points to zone id
DEFAULT_PRESET = "Somerville"
PRESETS = {
    "DC": {
        "name": "Washington, DC",
        "zone_id": "DCZ001",
        "office": "LWX",
        "grid_xy": (95, 72),
    },
    "Somerville": {
        "name": "Somerville, MA",
        "zone_id": "MAZ014",
        "office": "BOX",
        "grid_xy": (69, 77),
    },
}


@app.route("/")
def default_weather():
    return weather(None)


@app.route("/<location>")
def weather(location: str):
    if not location or location not in PRESETS:
        location = DEFAULT_PRESET
    data = PRESETS[location]
    return render_template(
        "weather.html",
        current_preset=location,
        presets=PRESETS.keys(),
        location=data["name"],
        forecast=forecast(data["office"], data["grid_xy"]),
        alerts=alerts(data["zone_id"]),
    )


def alerts(zone_id: str):
    api = f"{BASE_URL}/alerts/active/zone/{zone_id}"
    req = request_cache.get(api)
    json = req.json()

    if not json["features"]:
        return None

    return map(alert_properties, json["features"])


def forecast(office: str, grid_xy):
    api = f"{BASE_URL}/gridpoints/{office}/{grid_xy[0]},{grid_xy[1]}/forecast"
    req = request_cache.get(api)
    json = req.json()

    forecast_data = json["properties"]["periods"]
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
