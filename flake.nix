{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    nix-gleam.url = "github:arnarg/nix-gleam";
    nix-gleam.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      systems = inputs.nixpkgs.lib.systems.flakeExposed;

      perSystem =
        {
          pkgs,
          lib,
          self',
          inputs',
          ...
        }:
        {
          packages = {
            weather = inputs'.nix-gleam.packages.buildGleamApplication {
              src = ./.;
              meta.mainProgram = "weather";
            };
            default = self'.packages.weather;
            upload = pkgs.writeShellApplication {
              name = "upload";
              runtimeInputs = with pkgs; [
                gnutar
                zstd
                curl
              ];
              text = builtins.readFile ./upload;
            };
          };
          devShells.default = pkgs.mkShell { inherit (self'.packages.default) nativeBuildInputs; };
          apps.serve = {
            type = "app";
            program = pkgs.writeShellScriptBin "serve-site" ''
              ${lib.getExe pkgs.live-server} output -o
            '';
          };
        };
    };
}
