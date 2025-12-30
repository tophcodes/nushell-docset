{
  description = "Nushell Docset Generator - Generate Dash docsets for Nushell documentation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        python = pkgs.python312;

        pythonEnv = python.withPackages (ps: with ps; [
          markdown
        ]);

        nushell-docset = pkgs.python312Packages.buildPythonApplication {
          pname = "nushell-docset";
          version = "1.0.0";
          format = "pyproject";

          src = ./.;

          nativeBuildInputs = with pkgs.python312Packages; [
            setuptools
            wheel
          ];

          propagatedBuildInputs = with pkgs.python312Packages; [
            markdown
          ];

          buildInputs = [ pkgs.git ];

          meta = with pkgs.lib; {
            description = "Generate Dash docsets for Nushell documentation";
            homepage = "https://github.com/nushell/nushell.github.io";
            license = licenses.mit;
            maintainers = [ ];
            mainProgram = "nushell-docset";
          };
        };

      in
      {
        packages = {
          default = nushell-docset;
          nushell-docset = nushell-docset;
        };

        apps = {
          default = {
            type = "app";
            program = "${nushell-docset}/bin/nushell-docset";
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.git
            pkgs.python312Packages.setuptools
            pkgs.python312Packages.wheel
            pkgs.python312Packages.pip
          ];

          shellHook = ''
            echo "Nushell Docset Generator development environment"
            echo "Python version: $(python --version)"
            echo ""
            echo "Available commands:"
            echo "  python generate_docset.py --help"
            echo "  python generate_docset.py --output ./output"
            echo ""
            echo "To install in development mode:"
            echo "  pip install -e ."
          '';
        };
      }
    );
}
