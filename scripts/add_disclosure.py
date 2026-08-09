#!/usr/bin/env python3
"""Add or update an AI-generation disclosure in a white-label EPUB source tree."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from lxml import etree
from se.formatting import format_opf, format_xhtml

OPF_NAMESPACE = "http://www.idpf.org/2007/opf"
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"
EPUB_NAMESPACE = "http://www.idpf.org/2007/ops"
DISCLOSURE_ID = "ai-generation-disclosure"
DISCLOSURE_FILENAME = "ai-generation-disclosure.xhtml"


def locate_epub(project: Path) -> Path:
    candidates = [project / "epub", project]
    for candidate in candidates:
        if (candidate / "content.opf").exists():
            return candidate
    raise RuntimeError(f"Could not find epub/content.opf under {project}.")


def canonical_public_source_url(source_url: str) -> str:
    match = re.search(r"https?://(?:www\.)?gutenberg\.org/(?:cache/)?epub/(\d+)", source_url)
    if match:
        return f"https://www.gutenberg.org/ebooks/{match.group(1)}"
    return source_url


def disclosure_xhtml(title: str, source_url: str, source_description: str, process: str) -> str:
    escaped_title = html.escape(title)
    public_source_url = canonical_public_source_url(source_url)
    escaped_source_url = html.escape(public_source_url, quote=True)
    escaped_source = html.escape(source_description)
    escaped_process = html.escape(process)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="{XHTML_NAMESPACE}" xmlns:epub="{EPUB_NAMESPACE}" xml:lang="en-GB">
\t<head>
\t\t<title>About This Automated Edition</title>
\t\t<link href="../css/core.css" rel="stylesheet" type="text/css"/>
\t\t<link href="../css/local.css" rel="stylesheet" type="text/css"/>
\t</head>
\t<body epub:type="frontmatter">
\t\t<section id="{DISCLOSURE_ID}">
\t\t\t<h2 epub:type="title">About This Automated Edition</h2>
\t\t\t<p><strong>This is an unofficial, AI-generated edition.</strong> It was not produced, reviewed, or endorsed by <a href="https://standardebooks.org/">Standard Ebooks</a>.</p>
\t\t\t<p>Before reading <i>{escaped_title}</i>, check the <a href="https://standardebooks.org/ebooks">Standard Ebooks catalog</a>. If Standard Ebooks has published an edition, prefer it to this one.</p>
\t\t\t<p>Standard Ebooks volunteers invest substantial time in research, comparison against page scans, correction of transcription errors, semantic markup, typography, artwork research, proofreading, review, and compatibility testing. That work is reflected in the quality of their editions. An automated build cannot substitute for it.</p>
\t\t\t<p>This edition builds on the Standard Ebooks project’s <a href="https://github.com/standardebooks/tools">open-source tools</a>, <a href="https://standardebooks.org/manual">Manual of Style</a>, and published production guidance. It uses {escaped_source}, available at <a href="{escaped_source_url}">{escaped_source_url}</a>.</p>
\t\t\t<p>{escaped_process}</p>
\t\t\t<p>Automated transformations and AI-assisted editorial decisions may introduce errors or preserve defects in the source transcription. Treat this as a convenient interim reading copy, not a publication-quality Standard Ebook.</p>
\t\t</section>
\t</body>
</html>
'''


def write_disclosure(epub: Path, title: str, source_url: str, source_description: str, process: str) -> None:
    text_directory = epub / "text"
    text_directory.mkdir(parents=True, exist_ok=True)
    (text_directory / DISCLOSURE_FILENAME).write_text(
        format_xhtml(disclosure_xhtml(title, source_url, source_description, process)), encoding="utf-8"
    )


def update_opf(epub: Path) -> None:
    path = epub / "content.opf"
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(path), parser)
    root = tree.getroot()
    manifest = root.find(f"{{{OPF_NAMESPACE}}}manifest")
    spine = root.find(f"{{{OPF_NAMESPACE}}}spine")
    if manifest is None or spine is None:
        raise RuntimeError("content.opf has no manifest or spine.")

    manifest_id = DISCLOSURE_FILENAME
    matching_items = [
        item
        for item in manifest.findall(f"{{{OPF_NAMESPACE}}}item")
        if item.get("href") == f"text/{DISCLOSURE_FILENAME}" or item.get("id") == manifest_id
    ]
    if matching_items:
        item = matching_items[0]
        for duplicate in matching_items[1:]:
            manifest.remove(duplicate)
    else:
        item = etree.SubElement(manifest, f"{{{OPF_NAMESPACE}}}item")
    item.set("href", f"text/{DISCLOSURE_FILENAME}")
    item.set("id", manifest_id)
    item.set("media-type", "application/xhtml+xml")

    for itemref in list(spine.findall(f"{{{OPF_NAMESPACE}}}itemref")):
        if itemref.get("idref") == manifest_id:
            spine.remove(itemref)
    spine.insert(0, etree.Element(f"{{{OPF_NAMESPACE}}}itemref", idref=manifest_id))
    path.write_text(format_opf(etree.tostring(tree, encoding="unicode")), encoding="utf-8")


def update_toc(epub: Path) -> None:
    path = epub / "toc.xhtml"
    if not path.exists():
        raise RuntimeError("toc.xhtml does not exist; run `se build-toc` before adding the disclosure.")
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(path), parser)
    namespaces = {"x": XHTML_NAMESPACE, "epub": EPUB_NAMESPACE}
    navigation = tree.xpath('//x:nav[contains(concat(" ", normalize-space(@epub:type), " "), " toc ")]', namespaces=namespaces)
    if not navigation:
        raise RuntimeError("toc.xhtml has no table-of-contents navigation element.")
    ordered_list = navigation[0].find(f"{{{XHTML_NAMESPACE}}}ol")
    if ordered_list is None:
        raise RuntimeError("The table of contents has no ordered list.")

    target = f"text/{DISCLOSURE_FILENAME}#{DISCLOSURE_ID}"
    for list_item in list(ordered_list.findall(f"{{{XHTML_NAMESPACE}}}li")):
        links = list_item.findall(f".//{{{XHTML_NAMESPACE}}}a")
        if any(link.get("href", "").split("#", 1)[0] == f"text/{DISCLOSURE_FILENAME}" for link in links):
            ordered_list.remove(list_item)

    list_item = etree.Element(f"{{{XHTML_NAMESPACE}}}li")
    link = etree.SubElement(list_item, f"{{{XHTML_NAMESPACE}}}a", href=target)
    link.text = "About This Automated Edition"
    ordered_list.insert(0, list_item)
    path.write_text(format_xhtml(etree.tostring(tree, encoding="unicode")), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--source-description", required=True)
    parser.add_argument(
        "--process",
        default=(
            "The source was hash-pinned, converted to semantic XHTML with a book-specific parser, "
            "processed with the Standard Ebooks toolchain, and checked with EPUB validators."
        ),
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    epub = locate_epub(arguments.project)
    write_disclosure(epub, arguments.title, arguments.source_url, arguments.source_description, arguments.process)
    update_opf(epub)
    update_toc(epub)
    print(epub / "text" / DISCLOSURE_FILENAME)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
