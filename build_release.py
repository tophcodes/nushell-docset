#!/usr/bin/env python3

import argparse
import hashlib
import json
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import tempfile


class DocsetReleaseBuilder:
    def __init__(
        self,
        output_dir: Path,
        version: Optional[str] = None,
        base_url: Optional[str] = None,
        mirrors: Optional[List[str]] = None
    ):
        self.output_dir = output_dir
        self.version = version or datetime.now().strftime("%Y.%m.%d")
        self.base_url = base_url
        self.mirrors = mirrors or []
        self.docset_name = "Nushell"
        self.archive_name = f"{self.docset_name}.tgz"
        self.versioned_archive_name = f"{self.docset_name}-{self.version}.tgz"

    def generate_docset(self, work_dir: Path) -> Path:
        print(f"Generating {self.docset_name} docset...")

        docset_output = work_dir / "docset"
        docset_output.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent / "generate_docset.py"),
                "--output", str(docset_output),
                "--work-dir", str(work_dir / "temp")
            ],
            check=True,
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        docset_path = docset_output / f"{self.docset_name}.docset"
        if not docset_path.exists():
            raise FileNotFoundError(f"Docset not found at {docset_path}")

        return docset_path

    def create_archive(self, docset_path: Path) -> Path:
        print(f"Creating archive: {self.versioned_archive_name}")

        archive_path = self.output_dir / self.versioned_archive_name

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(docset_path, arcname=f"{self.docset_name}.docset")

        file_size = archive_path.stat().st_size
        print(f"Archive created: {archive_path} ({file_size:,} bytes)")

        return archive_path

    def calculate_checksums(self, archive_path: Path) -> dict:
        print("Calculating checksums...")

        checksums = {}
        with open(archive_path, "rb") as f:
            data = f.read()
            checksums["md5"] = hashlib.md5(data).hexdigest()
            checksums["sha1"] = hashlib.sha1(data).hexdigest()
            checksums["sha256"] = hashlib.sha256(data).hexdigest()

        return checksums

    def generate_xml_feed(self, archive_name: str, checksums: dict) -> str:
        urls = []

        if self.base_url:
            urls.append(f"{self.base_url.rstrip('/')}/{archive_name}")

        for mirror in self.mirrors:
            urls.append(f"{mirror.rstrip('/')}/{archive_name}")

        xml_lines = ['<entry>']
        xml_lines.append(f'    <version>{self.version}</version>')

        for url in urls:
            xml_lines.append(f'    <url>{url}</url>')

        xml_lines.append('</entry>')

        return '\n'.join(xml_lines)

    def generate_metadata(self, archive_path: Path, checksums: dict) -> dict:
        file_size = archive_path.stat().st_size

        metadata = {
            "name": self.docset_name,
            "version": self.version,
            "archive": {
                "filename": self.versioned_archive_name,
                "size": file_size,
                "size_human": self.format_size(file_size)
            },
            "checksums": checksums,
            "generated_at": datetime.now().isoformat(),
            "urls": []
        }

        if self.base_url:
            metadata["urls"].append(
                f"{self.base_url.rstrip('/')}/{self.versioned_archive_name}"
            )

        for mirror in self.mirrors:
            metadata["urls"].append(
                f"{mirror.rstrip('/')}/{self.versioned_archive_name}"
            )

        return metadata

    @staticmethod
    def format_size(size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def build_release(self):
        print(f"Building release for {self.docset_name} v{self.version}")
        print("=" * 60)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="nushell-release-") as temp_dir:
            work_dir = Path(temp_dir)

            docset_path = self.generate_docset(work_dir)
            archive_path = self.create_archive(docset_path)
            checksums = self.calculate_checksums(archive_path)

            xml_feed = self.generate_xml_feed(self.archive_name, checksums)
            xml_path = self.output_dir / f"{self.docset_name}.xml"
            with open(xml_path, 'w') as f:
                f.write(xml_feed)
            print(f"XML feed generated: {xml_path}")

            metadata = self.generate_metadata(archive_path, checksums)
            metadata_path = self.output_dir / f"{self.docset_name}-{self.version}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"Metadata generated: {metadata_path}")

            symlink_path = self.output_dir / self.archive_name
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()
            symlink_path.symlink_to(archive_path.name)
            print(f"Symlink created: {symlink_path} -> {archive_path.name}")

        print("\n" + "=" * 60)
        print("Release build completed successfully!")
        print(f"Version: {self.version}")
        print(f"Archive: {archive_path}")
        print(f"Size: {metadata['archive']['size_human']}")
        print(f"SHA256: {checksums['sha256']}")
        print("\nGenerated files:")
        print(f"  - {archive_path}")
        print(f"  - {xml_path}")
        print(f"  - {metadata_path}")
        print(f"  - {symlink_path}")

        return {
            "archive": archive_path,
            "xml": xml_path,
            "metadata": metadata_path,
            "checksums": checksums
        }


def main():
    parser = argparse.ArgumentParser(
        description="Build production release of Nushell docset with XML feed"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path.cwd() / "releases",
        help="Output directory for releases (default: ./releases)"
    )
    parser.add_argument(
        "--version",
        "-v",
        type=str,
        help="Version string (default: YYYY.MM.DD)"
    )
    parser.add_argument(
        "--base-url",
        "-u",
        type=str,
        help="Base URL where the docset will be hosted"
    )
    parser.add_argument(
        "--mirror",
        "-m",
        action="append",
        dest="mirrors",
        help="Additional mirror URLs (can be specified multiple times)"
    )
    parser.add_argument(
        "--github-release",
        action="store_true",
        help="Generate URLs for GitHub releases (requires --repo)"
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="GitHub repository (format: owner/repo)"
    )

    args = parser.parse_args()

    base_url = args.base_url
    mirrors = args.mirrors or []

    if args.github_release:
        if not args.repo:
            print("Error: --repo required when using --github-release", file=sys.stderr)
            sys.exit(1)

        version = args.version or datetime.now().strftime("%Y.%m.%d")
        base_url = f"https://github.com/{args.repo}/releases/download/v{version}"

    try:
        builder = DocsetReleaseBuilder(
            output_dir=args.output,
            version=args.version,
            base_url=base_url,
            mirrors=mirrors
        )
        builder.build_release()

    except subprocess.CalledProcessError as e:
        print(f"\nError during docset generation: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
