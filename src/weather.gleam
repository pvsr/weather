import gleam/dict
import gleam/int
import gleam/io
import gleam/list
import gleam/result
import gleam/string
import gleam/string_tree
import glemplate/assigns
import glemplate/html
import glemplate/parser
import locations.{type LocationConfig}
import nws_api.{type ForecastData}
import simplifile
import snag.{type Result}

pub fn main() {
  case build_site() {
    Ok(_) -> Nil
    Error(e) -> e |> snag.pretty_print |> io.println
  }
}

fn build_site() -> Result(Nil) {
  use locations <- result.try(locations.load("locations.toml"))

  io.println("Loaded " <> int.to_string(list.length(locations)) <> " locations")

  use template_str <- result.try(
    simplifile.read("templates/weather.html")
    |> snag.map_error(string.inspect)
    |> snag.context("Failed to read templates/weather.html"),
  )

  let p = parser.new()

  use tpl <- result.try(
    parser.parse_to_template(template_str, "weather.html", p)
    |> snag.map_error(string.inspect)
    |> snag.context("Failed to parse template"),
  )

  use _ <- result.try(
    simplifile.create_directory_all("output")
    |> snag.map_error(simplifile.describe_error)
    |> snag.context("Failed to create output dir"),
  )

  render_pages(tpl, locations)
  |> list.each(fn(r) {
    case r {
      Ok(dest) -> io.println("  Generated " <> dest)
      Error(e) -> e |> snag.pretty_print |> io.println_error
    }
  })

  let assert Ok(first) = list.first(locations)

  use _ <- result.try(link_index(first))

  link_static()
}

fn link_index(loc: LocationConfig) -> Result(Nil) {
  let to = loc.path
  let from = "output/index.html"
  let _ = simplifile.delete_file(from)
  use _ <- result.map(
    simplifile.create_symlink(to:, from: from)
    |> snag.map_error(simplifile.describe_error)
    |> snag.context("Failed to symlink " <> from <> " to " <> to),
  )
  io.println("  Linked " <> from <> " to " <> to)
}

fn link_static() -> Result(Nil) {
  let to = "../static"
  let from = "output/static"
  case simplifile.exists(from, follow_links: False) {
    Ok(True) -> Ok(Nil)
    Ok(False) -> {
      use _ <- result.map(
        simplifile.create_symlink(to:, from:)
        |> snag.map_error(simplifile.describe_error)
        |> snag.context("Failed to symlink " <> from <> " to " <> to),
      )
      io.println("  Linked " <> from <> " to " <> to)
    }
    Error(e) -> e |> string.inspect |> snag.error
  }
}

fn render_pages(tpl, locations: List(LocationConfig)) {
  let template_cache = dict.new()

  use loc <- list.map(locations)

  io.println("Fetching forecast for " <> loc.short_name <> "...")
  use assigns <- result.try(
    nws_api.get_forecast_data(loc.latitude, loc.longitude)
    |> result.map(build_assigns(locations, loc, _)),
  )

  let dest = "output/" <> loc.path
  use tree <- result.try(
    tpl
    |> html.render(assigns, template_cache)
    |> snag.map_error(string.inspect)
    |> snag.context("Failed to render " <> dest),
  )

  simplifile.write(dest, string_tree.to_string(tree))
  |> result.replace(dest)
  |> snag.map_error(simplifile.describe_error)
  |> snag.context("Failed to write " <> dest)
}

fn build_assigns(
  locations: List(LocationConfig),
  current: LocationConfig,
  data: ForecastData,
) {
  let nav_items =
    list.map(locations, fn(loc) {
      assigns.Dict(
        dict.from_list([
          #("name", assigns.String(loc.short_name)),
          #("path", assigns.String(loc.path)),
          #("is_current", assigns.Bool(loc.short_name == current.short_name)),
        ]),
      )
    })

  let alerts = list.map(data.alerts, alert_to_assign)

  let hourly_labels = build_hourly_labels(data.hourly)
  let hourly_temps = build_hourly_temps(data.hourly)

  let periods = list.map(data.periods, period_to_assign)

  assigns.from_list([
    #("long_name", assigns.String(current.long_name)),
    #("nav_items", assigns.List(nav_items)),
    #("alerts", assigns.List(alerts)),
    #("hourly_labels", assigns.String(hourly_labels)),
    #("hourly_temps", assigns.String(hourly_temps)),
    #("periods", assigns.List(periods)),
  ])
}

fn period_to_assign(p: nws_api.WeatherPeriod) -> assigns.AssignData {
  assigns.Dict(
    dict.from_list([
      #("name", assigns.String(p.name)),
      #("fahrenheit", assigns.Int(p.fahrenheit)),
      #("celsius", assigns.Int(p.celsius)),
      #("icon", assigns.String(p.icon)),
      #("detailed_forecast", assigns.String(p.detailed_forecast)),
    ]),
  )
}

fn alert_to_assign(a: nws_api.WeatherAlert) -> assigns.AssignData {
  assigns.Dict(
    dict.from_list([
      #("event", assigns.String(a.event)),
      #("severity", assigns.String(a.severity)),
      #("description", assigns.String(a.description)),
      #("expires", assigns.String(a.expires)),
    ]),
  )
}

fn build_hourly_labels(hourly: List(nws_api.HourlyWeather)) -> String {
  let labels = list.map(hourly, fn(h) { "\"" <> h.start_time <> "\"" })

  "[" <> string.join(labels, ", ") <> "]"
}

fn build_hourly_temps(hourly: List(nws_api.HourlyWeather)) -> String {
  let temps = list.map(hourly, fn(h) { int.to_string(h.fahrenheit) })
  string.join(temps, ",")
}
