from datetime import date, datetime, timedelta
from typing import Optional

from flask import Flask, render_template

from location import read_locations

app = Flask(__name__)


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


@app.route("/")
def default_weather():
    return weather(None)


@app.route("/<key>")
def weather(key: Optional[str]):
    locations = read_locations()
    assert len(locations) > 0

    location = (key and locations.get(key)) or list(locations.values())[0]

    alerts = map(alert_properties, location.alerts()["features"] or [])

    return render_template(
        "weather.html",
        current_location=location,
        available_locations=locations.keys(),
        forecast=forecasts(location.forecast()),
        hourly=forecasts(location.hourly())[0:36],
        alerts=alerts,
    )


@app.template_filter('quote')
def quote(s: str):
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
    str_props = ["event", "severity", "description"]
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
