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
      inherit (self.outputs.packages."${pkgs.stdenv.hostPlatform.system}") weather upload;
    in
    {
      options.services.weather = with lib; {
        enable = mkEnableOption "weather";
        startAt = mkOption {
          type = types.str;
          default = "*:09/30";
        };
      };

      config = lib.mkIf cfg.enable {
        systemd.services.build-weather = {
          inherit (cfg) startAt;
          serviceConfig = {
            Type = "oneshot";
            DynamicUser = true;
            RuntimeDirectory = "weather";
            ConfigurationDirectory = "weather";
            EnvironmentFile = "/etc/weather/env";
          };
          script = ''
            cd $RUNTIME_DIRECTORY && \
              ${lib.getExe weather} && \
              ${lib.getExe upload}
          '';
        };
      };
    };
}
