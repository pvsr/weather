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
          self',
          inputs',
          ...
        }:
        {
          packages = {
            weather = inputs'.nix-gleam.packages.buildGleamApplication { src = ./.; };
            default = self'.packages.weather;
            upload = pkgs.writeShellScriptBin "upload" (builtins.readFile ./upload);
          };
          devShells.default = pkgs.mkShell { inherit (self'.packages.default) nativeBuildInputs; };
        };
    };
}
