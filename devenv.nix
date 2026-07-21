{pkgs, lib, ...}:
let
  pyproject = builtins.fromTOML (builtins.readFile ./api/pyproject.toml);
  requirements = pkgs.writeText "requirements.txt" (
    lib.concatStringsSep "\n" pyproject.project.dependencies + "\n"
  );
in {
  packages = [
    pkgs.pyright
    pkgs.python313Packages.debugpy
  ];

  languages.python = {
    enable = true;
    package = pkgs.python313;

    venv = {
      enable = true;
      requirements = requirements;
    };
  };
}
