{
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.pre-commit-hooks.url = "github:cachix/pre-commit-hooks.nix";

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    pre-commit-hooks,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
      in rec {
        packages.default = with pkgs.python3Packages;
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

        devShells.default = pkgs.mkShell {
          inherit (self.checks.${system}.pre-commit-check) shellHook;
          buildInputs = with pkgs;
            [
              (python3.withPackages (ps:
                with ps; [
                  mypy
                  black
                  pylsp-mypy
                  python-lsp-black
                ]))
            ]
            ++ self.packages.${system}.default.propagatedBuildInputs;
        };

        checks = {
          pre-commit-check = pre-commit-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              alejandra.enable = true;
              black.enable = true;
              ruff.enable = true;
            };
          };
        };
      }
    )
    // {
      nixosModules.default = {
        config,
        lib,
        pkgs,
        ...
      }: let
        cfg = config.services.weather;
        weather = self.outputs.packages."${pkgs.system}".default;
      in {
        options = {
          services.weather = with lib; {
            enable = mkEnableOption "weather";
            bind = mkOption {
              type = types.str;
              default = "localhost:5997";
            };
          };
        };
        config = lib.mkIf (cfg.enable) {
          systemd.services.weather = {
            inherit (cfg) enable;
            serviceConfig = {
              DynamicUser = true;
              ExecStart = ''
                ${pkgs.python3Packages.gunicorn}/bin/gunicorn -b ${cfg.bind} weather.app
              '';
            };
            environment = {
              PYTHONPATH = weather.pythonModule.pkgs.makePythonPath [weather];
            };
            wantedBy = ["multi-user.target"];
            after = ["network.target"];
          };
        };
      };
    };
}
