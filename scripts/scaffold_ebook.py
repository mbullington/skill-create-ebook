#!/usr/bin/env python3
"""Create a white-label Standard Ebooks draft after checking the official catalog."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

from check_standard_ebooks import check_catalog

OPF_NAMESPACE = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}


def existing_project(workspace: Path, title: str, author: str) -> Path | None:
    for opf_path in workspace.glob("*/epub/content.opf"):
        try:
            root = ElementTree.parse(opf_path).getroot()
        except ElementTree.ParseError:
            continue
        found_title = root.findtext("opf:metadata/dc:title", namespaces=OPF_NAMESPACE)
        found_author = root.findtext("opf:metadata/dc:creator", namespaces=OPF_NAMESPACE)
        if found_title == title and found_author == author:
            return opf_path.parent.parent
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--translator")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--timeout", type=float, default=30)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        catalog = check_catalog(arguments.title, arguments.author, arguments.timeout)
    except RuntimeError as exception:
        print(f"error: {exception}", file=sys.stderr)
        print("Draft creation stopped because the official catalog could not be verified.", file=sys.stderr)
        return 2

    if catalog["decision"] != "continue":
        print(catalog["message"], file=sys.stderr)
        for match in catalog["matches"]:
            print(f"- {match['url']}", file=sys.stderr)
        return 3

    arguments.workspace.mkdir(parents=True, exist_ok=True)
    found = existing_project(arguments.workspace, arguments.title, arguments.author)
    if found:
        print(found)
        return 0

    before = {path.resolve() for path in arguments.workspace.iterdir()}
    command = [
        "se",
        "create-draft",
        "--offline",
        "--white-label",
        "--author",
        arguments.author,
        "--title",
        arguments.title,
    ]
    if arguments.translator:
        command.extend(["--translator", arguments.translator])
    subprocess.run(command, cwd=arguments.workspace, check=True)

    created = [
        path
        for path in arguments.workspace.iterdir()
        if path.resolve() not in before and (path / "epub" / "content.opf").exists()
    ]
    if len(created) != 1:
        raise RuntimeError(f"Expected one new draft, found {len(created)} in {arguments.workspace}.")

    project = created[0]
    notes = project / "production-notes.md"
    notes.write_text(
        "# Production Notes\n\n"
        f"Official catalog check: {catalog['search_url']}\n\n"
        "No matching published Standard Ebooks edition was found when this draft was created. "
        "Repeat the catalog check before every release.\n\n"
        "Record source-text URLs, scan editions, artwork records, public-domain evidence, "
        "SHA-256 hashes, and editorial decisions here.\n",
        encoding="utf-8",
    )
    print(project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
