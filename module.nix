{ self, ... }:
{
  flake.nixosModules.default =

    {
      config,
      lib,
      pkgs,
      ...
    }:
    let
      cfg = config.services.weather;
      weather = self.outputs.packages."${pkgs.system}".default;
    in
    {
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
            Restart = "always";
            RestartSec = 5;
            ExecStart = ''
              ${pkgs.python3Packages.gunicorn}/bin/gunicorn -b ${cfg.bind} weather.app
            '';
          };
          environment = {
            PYTHONPATH = weather.pythonModule.pkgs.makePythonPath [ weather ];
          };
          wantedBy = [ "multi-user.target" ];
          after = [ "network.target" ];
        };
      };
    };
}
