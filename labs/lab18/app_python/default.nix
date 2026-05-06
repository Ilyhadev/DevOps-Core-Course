{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python312;
  pyPkgs = pkgs.python312Packages;
  pythonEnv = python.withPackages (ps: with ps; [
    flask
    prometheus-client
    python-json-logger
  ]);
in
pyPkgs.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;
  format = "other";

  installPhase = ''
    runHook preInstall

    mkdir -p $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    mkdir -p $out/bin
    cat > $out/bin/devops-info-service <<EOF
#!${pythonEnv}/bin/python
import os
import runpy
import sys

os.environ.setdefault("DATA_DIR", "/tmp/devops-info-service-data")
sys.path.insert(0, "$out/share/devops-info-service")
runpy.run_path("$out/share/devops-info-service/app.py", run_name="__main__")
EOF
    chmod +x $out/bin/devops-info-service

    runHook postInstall
  '';
}
