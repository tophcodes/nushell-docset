# Nushell Docset Generator

Generate [Dash](https://kapeli.com/dash) / [Zeal](https://zealdocs.org/) docsets for Nushell documentation.

This tool automatically clones the [Nushell documentation repository](https://github.com/nushell/nushell.github.io), processes the markdown files from the book, commands, cookbook, and language guide sections, and generates a searchable docset for offline viewing in Dash-compatible documentation browsers.

## Features

- Automatically clones the latest Nushell documentation
- Processes markdown files from multiple documentation sections:
  - Book (Getting Started, Fundamentals, Programming Guide)
  - Commands (Command Reference)
  - Cookbook (Practical Examples)
  - Language Guide (Detailed Language Documentation)
- Converts markdown to well-formatted HTML with syntax highlighting
- Builds Dash-compatible docsets with SQLite search index
- Clean, styled documentation matching modern documentation standards

## Installation

### Using Nix Flakes (Recommended)

```bash
nix build
nix run
```

Or install directly:

```bash
nix profile install .
```

### Using Nix Shell for Development

```bash
nix develop
python generate_docset.py --help
```

### Using pip

```bash
pip install -e .
```

Or install dependencies manually:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Generate a docset in the current directory:

```bash
python generate_docset.py
```

Or with Nix:

```bash
nix run
```

### Specify Output Directory

```bash
python generate_docset.py --output ~/Documents/Docsets
```

### Advanced Options

```bash
python generate_docset.py --help
```

Available options:

- `--output, -o`: Output directory for the docset (default: current directory)
- `--work-dir, -w`: Working directory for temporary files (default: system temp)
- `--skip-clone`: Skip cloning the repository (use existing clone in work-dir)
- `--keep-temp`: Keep temporary files after generation

### Example Workflows

Generate docset with custom working directory:

```bash
python generate_docset.py --output ./docsets --work-dir ./temp
```

Re-generate without re-cloning:

```bash
python generate_docset.py --work-dir ./temp --skip-clone --keep-temp
```

## Installing the Generated Docset

### Dash (macOS)

1. Double-click the generated `Nushell.docset` file, or
2. Copy it to `~/Library/Application Support/Dash/DocSets/`

### Zeal (Linux/Windows)

1. Open Zeal
2. Tools → Docsets → Add Feed → Browse
3. Select the generated `Nushell.docset` directory

## Production Builds

### Building Releases

The project includes a production build tool that creates distribution-ready packages with XML feeds for Dash/Zeal.

#### Quick Start

```bash
# Using Make (recommended)
make release-github REPO=yourusername/nushell-docset

# Or directly with Python
nix develop
python build_release.py --output releases --github-release --repo yourusername/nushell-docset
```

#### Build Options

```bash
python build_release.py --help
```

Available options:

- `--output, -o`: Output directory for releases (default: ./releases)
- `--version, -v`: Version string (default: YYYY.MM.DD format)
- `--base-url, -u`: Base URL where the docset will be hosted
- `--mirror, -m`: Additional mirror URLs (can be specified multiple times)
- `--github-release`: Generate URLs for GitHub releases (requires --repo)
- `--repo`: GitHub repository in format owner/repo

#### What Gets Generated

A production build creates:

1. **Versioned Archive**: `Nushell-YYYY.MM.DD.tgz` - The compressed docset
2. **Latest Symlink**: `Nushell.tgz` - Always points to the latest version
3. **XML Feed**: `Nushell.xml` - Zeal-compatible feed for auto-updates
4. **Metadata**: `Nushell-YYYY.MM.DD.json` - Version info and checksums

Example XML feed:
```xml
<entry>
    <version>2025.12.31</version>
    <url>https://github.com/user/repo/releases/download/v2025.12.31/Nushell.tgz</url>
</entry>
```

#### Using with Multiple Mirrors

For CDN distribution across multiple mirrors:

```bash
python build_release.py \
  --version 2025.12.31 \
  --base-url https://primary-cdn.example.com/docsets \
  --mirror https://eu.cdn.example.com/docsets \
  --mirror https://us.cdn.example.com/docsets \
  --mirror https://asia.cdn.example.com/docsets
```

### Automated Releases with GitHub Actions

The repository includes a GitHub Actions workflow that automatically builds and publishes releases.

#### Setup

1. Fork this repository
2. (Optional) Set up Cachix for faster builds:
   - Create a Cachix cache
   - Add `CACHIX_AUTH_TOKEN` to repository secrets

#### Creating a Release

**Option 1: Tag-based release**
```bash
git tag v2025.12.31
git push origin v2025.12.31
```

**Option 2: Manual workflow**
1. Go to Actions → "Build and Release Docset"
2. Click "Run workflow"
3. Optionally specify a version
4. Click "Run workflow"

#### What Happens

The workflow will:
1. Build the docset using Nix
2. Create a versioned `.tgz` archive
3. Generate XML feed and metadata
4. Create a GitHub release with all files
5. Attach checksums for verification

Users can then subscribe to the feed in Zeal:
```
https://github.com/yourusername/nushell-docset/releases/download/v2025.12.31/Nushell.xml
```

### Distribution Methods

#### Method 1: GitHub Releases (Recommended)

1. Build and publish releases using GitHub Actions
2. Users subscribe to: `https://github.com/USER/REPO/releases/latest/download/Nushell.xml`

#### Method 2: Self-Hosted

1. Build the release locally:
   ```bash
   python build_release.py --base-url https://your-cdn.com/docsets
   ```
2. Upload files to your web server:
   - `Nushell.tgz` (actual archive)
   - `Nushell.xml` (feed file)
3. Users subscribe to: `https://your-cdn.com/docsets/Nushell.xml`

#### Method 3: Dash User Contributed Docsets

1. Fork [Dash-User-Contributions](https://github.com/Kapeli/Dash-User-Contributions)
2. Add your docset following their guidelines
3. Submit a pull request

## Development

### Project Structure

```
.
├── .github/
│   └── workflows/
│       └── release.yml         # GitHub Actions release workflow
├── flake.nix                   # Nix flake for development and packaging
├── generate_docset.py          # Main docset generation script
├── build_release.py            # Production build and release tool
├── pyproject.toml              # Python package configuration
├── requirements.txt            # Python dependencies
├── Makefile                    # Convenience build targets
└── README.md                   # This file
```

### Development Environment

Enter the Nix development shell:

```bash
nix develop
```

Or use a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Making Changes

1. Edit `generate_docset.py`
2. Test your changes:
   ```bash
   python generate_docset.py --output ./test-output
   ```
3. Build with Nix to ensure packaging works:
   ```bash
   nix build
   ```

## Requirements

- Python 3.9+
- Git
- markdown (Python library)

All dependencies are automatically managed when using Nix.

## How It Works

1. **Clone Repository**: Clones the latest Nushell documentation from GitHub
2. **Collect Markdown**: Scans documentation directories for markdown files
3. **Extract Metadata**: Parses frontmatter and headings to extract titles
4. **Convert to HTML**: Transforms markdown to styled HTML with:
   - Syntax highlighting for code blocks
   - Proper table formatting
   - Typography matching modern documentation
5. **Generate Index**: Creates a master index linking all documentation
6. **Build Docset**: Creates the docset bundle structure with:
   - Info.plist configuration
   - SQLite search index for fast lookups
   - Proper categorization (Commands, Guides, etc.)

## License

MIT

## Contributing

Contributions are welcome! Please ensure:

- Code follows existing style conventions
- All features are tested
- Documentation is updated

## Troubleshooting

### "git: command not found"

Install Git:

```bash
# On Nix
nix-shell -p git

# On Debian/Ubuntu
sudo apt install git

# On macOS
brew install git
```

### Clone Fails

If the repository clone fails due to network issues, you can:

1. Clone manually: `git clone https://github.com/nushell/nushell.github.io.git`
2. Use `--work-dir` pointing to the parent directory
3. Use `--skip-clone` to use the existing clone

## Acknowledgments

- [Nushell](https://www.nushell.sh/) - The modern shell
- [Dash](https://kapeli.com/dash) - API documentation browser
