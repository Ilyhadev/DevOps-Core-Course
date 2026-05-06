{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";
  contents = [ app pkgs.bash ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "PORT=8080"
      "PYTHONUNBUFFERED=1"
      "PYTHONDONTWRITEBYTECODE=1"
    ];
    ExposedPorts = {
      "8080/tcp" = {};
    };
  };

  # Fixed creation time for reproducible image tarball.
  created = "1970-01-01T00:00:01Z";
}
