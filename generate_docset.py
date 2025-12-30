#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import tempfile


class NushellDocsetGenerator:
    def __init__(self, output_dir: Path, work_dir: Path):
        self.output_dir = output_dir
        self.work_dir = work_dir
        self.repo_url = "https://github.com/nushell/nushell.github.io.git"
        self.repo_dir = work_dir / "nushell.github.io"
        self.html_dir = work_dir / "html"
        self.docset_name = "Nushell"

    def clone_repository(self):
        print(f"Cloning {self.repo_url}...")
        if self.repo_dir.exists():
            shutil.rmtree(self.repo_dir)

        subprocess.run(
            ["git", "clone", "--depth", "1", self.repo_url, str(self.repo_dir)],
            check=True,
            capture_output=True
        )
        print("Repository cloned successfully")

    def collect_markdown_files(self) -> Dict[str, List[Path]]:
        sections = {
            "Book": [],
            "Commands": [],
            "Cookbook": [],
            "Language Guide": []
        }

        book_dir = self.repo_dir / "book"
        commands_dir = self.repo_dir / "commands"
        cookbook_dir = self.repo_dir / "cookbook"
        lang_guide_dir = self.repo_dir / "lang-guide"

        if book_dir.exists():
            sections["Book"] = list(book_dir.rglob("*.md"))

        if commands_dir.exists():
            sections["Commands"] = list(commands_dir.rglob("*.md"))

        if cookbook_dir.exists():
            sections["Cookbook"] = list(cookbook_dir.rglob("*.md"))

        if lang_guide_dir.exists():
            sections["Language Guide"] = list(lang_guide_dir.rglob("*.md"))

        return sections

    def extract_title_from_markdown(self, md_file: Path) -> str:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

                if content.startswith('---'):
                    frontmatter_end = content.find('---', 3)
                    if frontmatter_end != -1:
                        frontmatter = content[3:frontmatter_end]
                        title_match = re.search(r'title:\s*["\']?([^"\'\n]+)', frontmatter)
                        if title_match:
                            return title_match.group(1).strip()

                h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if h1_match:
                    return h1_match.group(1).strip()

                return md_file.stem.replace('_', ' ').title()
        except Exception as e:
            print(f"Warning: Could not extract title from {md_file}: {e}")
            return md_file.stem.replace('_', ' ').title()

    def markdown_to_html(self, md_content: str, title: str) -> str:
        try:
            import markdown
            from markdown.extensions import fenced_code, tables, toc

            md = markdown.Markdown(extensions=[
                'fenced_code',
                'tables',
                'toc',
                'nl2br',
                'sane_lists'
            ])

            body = md.convert(md_content)
        except ImportError:
            body = f"<pre>{md_content}</pre>"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #24292e;
        }}
        code {{
            background-color: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 85%;
        }}
        pre {{
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }}
        h1 {{
            font-size: 2em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        h2 {{
            font-size: 1.5em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        table th, table td {{
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }}
        table th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        table tr:nth-child(2n) {{
            background-color: #f6f8fa;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        blockquote {{
            border-left: 4px solid #dfe2e5;
            padding: 0 15px;
            color: #6a737d;
            margin: 0;
        }}
    </style>
</head>
<body>
    {body}
</body>
</html>"""
        return html

    def generate_html_docs(self, sections: Dict[str, List[Path]]):
        print("Generating HTML documentation...")
        self.html_dir.mkdir(parents=True, exist_ok=True)

        index_links = []

        for section_name, md_files in sections.items():
            if not md_files:
                continue

            section_dir = self.html_dir / section_name.lower().replace(' ', '_')
            section_dir.mkdir(exist_ok=True)

            index_links.append(f"<h2>{section_name}</h2><ul>")

            for md_file in sorted(md_files):
                if md_file.name in ['README.md', '.vuepress']:
                    continue

                title = self.extract_title_from_markdown(md_file)

                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        md_content = f.read()

                    if md_content.startswith('---'):
                        frontmatter_end = md_content.find('---', 3)
                        if frontmatter_end != -1:
                            md_content = md_content[frontmatter_end + 3:].lstrip()

                    html_content = self.markdown_to_html(md_content, title)

                    relative_path = md_file.relative_to(self.repo_dir)
                    html_filename = str(relative_path).replace('/', '_').replace('.md', '.html')
                    html_file = section_dir / html_filename

                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(html_content)

                    relative_html = html_file.relative_to(self.html_dir)
                    index_links.append(f'<li><a href="{relative_html}">{title}</a></li>')

                except Exception as e:
                    print(f"Warning: Failed to process {md_file}: {e}")

            index_links.append("</ul>")

        index_html = self.markdown_to_html("", "Nushell Documentation")
        index_html = index_html.replace(
            "<body>",
            f"<body><h1>Nushell Documentation</h1>{''.join(index_links)}"
        )

        with open(self.html_dir / "index.html", 'w', encoding='utf-8') as f:
            f.write(index_html)

        print(f"Generated HTML documentation in {self.html_dir}")

    def create_search_index(self, docset_path: Path, sections: Dict[str, List[Path]]):
        db_path = docset_path / "Contents" / "Resources" / "docSet.dsidx"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);
        ''')
        cursor.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

        for section_name, md_files in sections.items():
            if not md_files:
                continue

            section_dir_name = section_name.lower().replace(' ', '_')
            entry_type = "Command" if section_name == "Commands" else "Guide"

            for md_file in md_files:
                if md_file.name in ['README.md', '.vuepress']:
                    continue

                title = self.extract_title_from_markdown(md_file)
                relative_path = md_file.relative_to(self.repo_dir)
                html_filename = str(relative_path).replace('/', '_').replace('.md', '.html')
                html_path = f"{section_dir_name}/{html_filename}"

                cursor.execute(
                    'INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)',
                    (title, entry_type, html_path)
                )

        conn.commit()
        conn.close()

    def generate_docset(self, sections: Dict[str, List[Path]]):
        print("Generating docset...")

        docset_path = self.output_dir / f"{self.docset_name}.docset"
        contents_path = docset_path / "Contents"
        resources_path = contents_path / "Resources"
        documents_path = resources_path / "Documents"

        docset_path.mkdir(parents=True, exist_ok=True)
        contents_path.mkdir(exist_ok=True)
        resources_path.mkdir(exist_ok=True)

        info_plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>nushell</string>
    <key>CFBundleName</key>
    <string>{self.docset_name}</string>
    <key>DocSetPlatformFamily</key>
    <string>nushell</string>
    <key>isDashDocset</key>
    <true/>
    <key>dashIndexFilePath</key>
    <string>index.html</string>
    <key>DashDocSetFallbackURL</key>
    <string>https://www.nushell.sh/</string>
</dict>
</plist>'''

        with open(contents_path / "Info.plist", 'w') as f:
            f.write(info_plist)

        shutil.copytree(self.html_dir, documents_path, dirs_exist_ok=True)

        icon_path = self.repo_dir / "icon.png"
        if icon_path.exists():
            shutil.copy(icon_path, docset_path / "icon.png")

        self.create_search_index(docset_path, sections)

        print(f"Docset generated successfully: {docset_path}")

    def cleanup(self):
        if self.work_dir.exists() and self.work_dir != self.output_dir:
            print("Cleaning up temporary files...")
            shutil.rmtree(self.work_dir, ignore_errors=True)

    def run(self, skip_clone: bool = False):
        try:
            if not skip_clone:
                self.clone_repository()

            sections = self.collect_markdown_files()
            total_files = sum(len(files) for files in sections.values())
            print(f"Found {total_files} markdown files")

            self.generate_html_docs(sections)
            self.generate_docset(sections)

            print("\n✓ Nushell docset generated successfully!")
            print(f"  Location: {self.output_dir / self.docset_name}.docset")

        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Dash docset for Nushell documentation"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path.cwd(),
        help="Output directory for the docset (default: current directory)"
    )
    parser.add_argument(
        "--work-dir",
        "-w",
        type=Path,
        default=None,
        help="Working directory for temporary files (default: system temp)"
    )
    parser.add_argument(
        "--skip-clone",
        action="store_true",
        help="Skip cloning the repository (use existing clone in work-dir)"
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary files after generation"
    )

    args = parser.parse_args()

    work_dir = args.work_dir or Path(tempfile.mkdtemp(prefix="nushell-docset-"))
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = NushellDocsetGenerator(output_dir, work_dir)

    try:
        generator.run(skip_clone=args.skip_clone)
    finally:
        if not args.keep_temp:
            generator.cleanup()


if __name__ == "__main__":
    main()
