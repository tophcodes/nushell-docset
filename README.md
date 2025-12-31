# Nushell Docset Generator

Generates [Dash](https://kapeli.com/dash) / [Zeal](https://zealdocs.org/) docsets for Nushell documentation. The docset is also conveniently [hosted on GitHub Pages](https://tophcodes.github.io/nushell-docset/) if you want to add it to your feeds.

!! Still work in progress at this moment.

### Using Nix Shell for Development

```bash
nix develop
python generate_docset.py --help

#
nix build
```
## Installing the Generated Docset

### Dash (macOS)

1. Double-click the generated `Nushell.docset` file, or
2. Copy it to `~/Library/Application Support/Dash/DocSets/`

### Zeal (Linux/Windows)

1. Open Zeal
2. Tools → Docsets → Add Feed → Browse
3. Select the generated `Nushell.docset` directory
