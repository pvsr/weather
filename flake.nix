{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs =
    inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        ./module.nix
      ];

      systems = inputs.nixpkgs.lib.systems.flakeExposed;

      perSystem =
        {
          config,
          pkgs,
          self',
          ...
        }:
        {
          devShells.default = pkgs.mkShell {
            inputsFrom = [ self'.packages.default ];
            buildInputs = with pkgs; [
              (python3.withPackages (
                ps: with ps; [
                  mypy
                  black
                  pylsp-mypy
                  python-lsp-black
                ]
              ))
            ];
          };

          packages.default =
            with pkgs.python3Packages;
            buildPythonPackage {
              name = "weather";
              format = "pyproject";
              src = ./.;
              propagatedBuildInputs = [
                setuptools

                flask
                requests
                cachecontrol
              ];
            };

          formatter = pkgs.nixfmt-tree;
        };
    };
}
