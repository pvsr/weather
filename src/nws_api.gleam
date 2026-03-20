import gleam/dynamic/decode
import gleam/float
import gleam/http/request
import gleam/http/response.{type Response}
import gleam/httpc
import gleam/int
import gleam/json
import gleam/list
import gleam/result
import gleam/string
import snag.{type Result}

pub type WeatherPeriod {
  WeatherPeriod(
    name: String,
    fahrenheit: Int,
    celsius: Int,
    icon: String,
    short_forecast: String,
    detailed_forecast: String,
  )
}

pub type HourlyWeather {
  HourlyPeriod(
    start_time: String,
    fahrenheit: Int,
    celsius: Int,
    short_forecast: String,
  )
}

pub type WeatherAlert {
  Alert(event: String, severity: String, description: String, expires: String)
}

pub type ForecastData {
  ForecastData(
    periods: List(WeatherPeriod),
    hourly: List(HourlyWeather),
    alerts: List(WeatherAlert),
  )
}

pub fn get_forecast_data(lat: Float, lon: Float) -> Result(ForecastData) {
  let points_url =
    "https://api.weather.gov/points/"
    <> float.to_string(lat)
    <> ","
    <> float.to_string(lon)

  use resp <- result.try(get(points_url))

  use json <- result.try(
    json.parse(resp.body, decode.dynamic)
    |> snag.map_error(string.inspect)
    |> snag.context("Failed to parse json"),
  )

  use forecast_url <- result.try(
    decode_string(json, ["properties", "forecast"]),
  )
  use hourly_url <- result.try(
    decode_string(json, ["properties", "forecastHourly"]),
  )
  use alert_url <- result.try(
    decode_string(json, ["properties", "forecastZone"])
    |> result.map(string.replace(
      in: _,
      each: "/zones/forecast",
      with: "/alerts/active/zone",
    )),
  )

  use periods <- result.try(fetch_and_parse(
    forecast_url,
    ["properties", "periods"],
    period_decoder(),
  ))
  use hourly <- result.try(
    fetch_and_parse(hourly_url, ["properties", "periods"], hourly_decoder())
    |> result.map(list.take(_, 36)),
  )
  use alerts <- result.map(fetch_and_parse(
    alert_url,
    ["features"],
    decode.at(["properties"], alert_decoder()),
  ))

  ForecastData(periods:, hourly:, alerts:)
}

fn get(url) -> Result(Response(String)) {
  use req <- result.try(
    request.to(url)
    |> result.map(request.set_header(_, "user-agent", "weather.peterrice.xyz"))
    |> snag.map_error(string.inspect)
    |> snag.context("Request to " <> url <> " failed"),
  )

  use resp <- result.try(
    httpc.send(req)
    |> snag.map_error(string.inspect)
    |> snag.context("Failed to send request"),
  )

  case resp.status {
    200 -> Ok(resp)
    status ->
      snag.error(
        "Received " <> int.to_string(status) <> " response from " <> url,
      )
  }
}

fn decode_string(json, path) {
  decode.run(json, decode.at(path, decode.string))
  |> snag.map_error(string.inspect)
  |> snag.context("Failed to decode " <> string.inspect(path))
}

fn fetch_and_parse(
  url: String,
  path: List(String),
  decoder: decode.Decoder(a),
) -> Result(List(a)) {
  use resp <- result.try(get(url))
  resp.body
  |> json.parse(decode.at(path, decode.list(decoder)))
  |> snag.map_error(string.inspect)
  |> snag.context("Failed to parse path " <> string.inspect(path))
}

fn period_decoder() -> decode.Decoder(WeatherPeriod) {
  use name <- decode.field("name", decode.string)
  use temp <- decode.field("temperature", decode.int)
  use unit <- decode.field("temperatureUnit", decode.string)
  use icon <- decode.field("icon", decode.string |> decode.map(large_icon))
  use short_forecast <- decode.field("shortForecast", decode.string)
  use detailed_forecast <- decode.field("detailedForecast", decode.string)
  let #(fahrenheit, celsius) = get_temps(unit, temp)
  decode.success(WeatherPeriod(
    name:,
    fahrenheit:,
    celsius:,
    icon:,
    short_forecast:,
    detailed_forecast:,
  ))
}

fn hourly_decoder() {
  use start_time <- decode.field("startTime", decode.string)
  use temp <- decode.field("temperature", decode.int)
  use unit <- decode.field("temperatureUnit", decode.string)
  use short_forecast <- decode.field("shortForecast", decode.string)
  let #(fahrenheit, celsius) = get_temps(unit, temp)
  decode.success(HourlyPeriod(
    start_time:,
    fahrenheit:,
    celsius:,
    short_forecast:,
  ))
}

fn alert_decoder() {
  use event <- decode.field("event", decode.string)
  use severity <- decode.field("severity", decode.string)
  use description <- decode.field("description", decode.string)
  use expires <- decode.field("expires", decode.string)
  decode.success(Alert(event:, severity:, description:, expires:))
}

fn get_temps(unit: String, temp: Int) -> #(Int, Int) {
  case unit {
    "F" -> #(temp, celsius_from_f(temp))
    "C" -> #(fahrenheit_from_c(temp), temp)
    _ -> panic
  }
}

fn celsius_from_f(f: Int) -> Int {
  int.to_float(f - 32) *. 5.0 /. 9.0 |> float.round
}

fn fahrenheit_from_c(c: Int) -> Int {
  let scaled =
    int.to_float(c) *. 9.0 /. 5.0
    |> float.round
  scaled + 32
}

fn large_icon(url: String) -> String {
  string.replace(url, "?size=small", "?size=large")
  |> string.replace("?size=medium", "?size=large")
}
