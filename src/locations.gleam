import gleam/dynamic/decode
import gleam/result
import gleam/string
import simplifile
import snag.{type Result}
import tom

pub type LocationConfig {
  LocationConfig(
    short_name: String,
    long_name: String,
    path: String,
    latitude: Float,
    longitude: Float,
  )
}

fn decoder() -> decode.Decoder(LocationConfig) {
  use short_name <- decode.field("short_name", decode.string)
  use long_name <- decode.field("long_name", decode.string)
  let path = string.lowercase(short_name) <> ".html"
  use latitude <- decode.field("latitude", decode.float)
  use longitude <- decode.field("longitude", decode.float)
  decode.success(LocationConfig(
    short_name:,
    long_name:,
    path:,
    latitude:,
    longitude:,
  ))
}

pub fn load(path) -> Result(List(LocationConfig)) {
  use contents <- result.try(
    simplifile.read(path)
    |> snag.map_error(string.inspect)
    |> snag.context("Failed to read " <> path),
  )
  use parsed <- result.try(
    tom.parse(contents)
    |> snag.map_error(string.inspect)
    |> snag.context("Failed to parse " <> path <> " as toml"),
  )
  tom.to_dynamic(parsed)
  |> decode.run(decode.at(["location"], decode.list(decoder())))
  |> snag.map_error(string.inspect)
  |> snag.context("Failed to load locations from " <> path)
}
