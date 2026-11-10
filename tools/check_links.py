#!/usr/bin/env python3
"""Check that every relative link in the repository's Markdown files resolves.

Scans tracked *.md files (git ls-files), extracts Markdown links and
images ``[text](target)`` plus HTML ``src=``/``href=`` attributes, and
reports every relative target that does not exist on disk. External
links (http, https, mailto) and pure anchors are ignored; anchors on
relative links are stripped before the check.

Files under docs/archive/ are frozen history and are skipped by default.

Usage:
    python3 tools/check_links.py            # exit 1 if a link is broken
    python3 tools/check_links.py --all      # include docs/archive/
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
MD_LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HTML_LINK = re.compile(r"(?:src|href)=\"([^\"]+)\"")
FENCE = re.compile(r"^\s*(```|~~~)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "tel:")
ARCHIVE = "docs/archive/"


def tracked_markdown() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    return [line for line in out.splitlines() if line]


def links_in(text: str):
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # Inline code spans are not links.
        line = re.sub(r"`[^`]*`", "", line)
        for match in MD_LINK.finditer(line):
            yield lineno, match.group(1)
        for match in HTML_LINK.finditer(line):
            yield lineno, match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--all", action="store_true", help="also check docs/archive/")
    args = parser.parse_args()

    broken: list[str] = []
    files = tracked_markdown()
    for rel in files:
        if not args.all and rel.startswith(ARCHIVE):
            continue
        path = ROOT / rel
        if not path.exists():
            continue
        for lineno, target in links_in(path.read_text(encoding="utf-8")):
            if target.startswith(SKIP_PREFIXES):
                continue
            clean = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not clean:
                continue
            resolved = (ROOT / clean.lstrip("/")) if clean.startswith("/") else (path.parent / clean)
            if not resolved.exists():
                broken.append(f"{rel}:{lineno}: {target}")

    for line in broken:
        print(line)
    print(f"{len(files)} files, {len(broken)} broken links", file=sys.stderr)
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
