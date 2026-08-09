#!/usr/bin/env python3
"""Verify cover discovery and AI disclosure placement in an EPUB source tree or file."""

from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

OPF_NAMESPACE = "http://www.idpf.org/2007/opf"
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"
EPUB_NAMESPACE = "http://www.idpf.org/2007/ops"
CONTAINER_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:container"
DISCLOSURE_FILENAME = "ai-generation-disclosure.xhtml"
REQUIRED_DISCLOSURE_TEXT = (
    "unofficial, AI-generated edition",
    "not produced, reviewed, or endorsed by Standard Ebooks",
    "prefer it to this one",
    "Automated transformations and AI-assisted editorial decisions",
)


def locate_source_epub(path: Path) -> Path:
    for candidate in (path / "epub", path):
        if (candidate / "content.opf").exists():
            return candidate
    raise RuntimeError(f"Could not find content.opf under {path}.")


def extract_epub(path: Path, destination: Path) -> Path:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if not names or names[0] != "mimetype":
            raise RuntimeError("The EPUB mimetype entry is not first.")
        mimetype = archive.getinfo("mimetype")
        if mimetype.compress_type != zipfile.ZIP_STORED:
            raise RuntimeError("The EPUB mimetype entry is compressed.")
        if archive.read("mimetype") != b"application/epub+zip":
            raise RuntimeError("The EPUB has an invalid mimetype value.")
        archive.extractall(destination)

    container = etree.parse(str(destination / "META-INF" / "container.xml"))
    rootfiles = container.xpath("//c:rootfile/@full-path", namespaces={"c": CONTAINER_NAMESPACE})
    if len(rootfiles) != 1:
        raise RuntimeError("The EPUB container must identify one package document.")
    return destination / Path(rootfiles[0]).parent


def verify(epub: Path) -> list[str]:
    errors: list[str] = []
    opf_path = epub / "content.opf"
    tree = etree.parse(str(opf_path))
    root = tree.getroot()
    manifest = root.find(f"{{{OPF_NAMESPACE}}}manifest")
    spine = root.find(f"{{{OPF_NAMESPACE}}}spine")
    if manifest is None or spine is None:
        return ["content.opf has no manifest or spine."]

    items = manifest.findall(f"{{{OPF_NAMESPACE}}}item")
    cover_items = [item for item in items if "cover-image" in item.get("properties", "").split()]
    if len(cover_items) != 1:
        errors.append(f"Expected one manifest cover-image, found {len(cover_items)}.")
    elif not (epub / cover_items[0].get("href", "")).exists():
        errors.append("The manifest cover-image file does not exist.")

    disclosure_items = [item for item in items if item.get("href") == f"text/{DISCLOSURE_FILENAME}"]
    if len(disclosure_items) != 1:
        errors.append(f"Expected one disclosure manifest item, found {len(disclosure_items)}.")
        return errors

    disclosure_id = disclosure_items[0].get("id")
    itemrefs = spine.findall(f"{{{OPF_NAMESPACE}}}itemref")
    if not itemrefs or itemrefs[0].get("idref") != disclosure_id:
        errors.append("The AI disclosure is not first in the spine.")

    disclosure_path = epub / "text" / DISCLOSURE_FILENAME
    if not disclosure_path.exists():
        errors.append("The AI disclosure XHTML file does not exist.")
    else:
        disclosure = etree.parse(str(disclosure_path))
        disclosure_text = " ".join("".join(disclosure.getroot().itertext()).split())
        for required in REQUIRED_DISCLOSURE_TEXT:
            if required not in disclosure_text:
                errors.append(f"Disclosure is missing required text: {required!r}.")

    toc_path = epub / "toc.xhtml"
    if not toc_path.exists():
        errors.append("toc.xhtml does not exist.")
    else:
        toc = etree.parse(str(toc_path))
        links = toc.xpath(
            '//x:nav[contains(concat(" ", normalize-space(@epub:type), " "), " toc ")]//x:a/@href',
            namespaces={"x": XHTML_NAMESPACE, "epub": EPUB_NAMESPACE},
        )
        if not links or links[0].split("#", 1)[0] != f"text/{DISCLOSURE_FILENAME}":
            errors.append("The AI disclosure is not first in the table of contents.")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    if not arguments.path.exists():
        raise SystemExit(f"error: {arguments.path} does not exist")

    with tempfile.TemporaryDirectory(prefix="verify-ebook-") as temporary:
        if arguments.path.is_file():
            epub = extract_epub(arguments.path, Path(temporary))
        else:
            epub = locate_source_epub(arguments.path)
        errors = verify(epub)

    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print(f"Verified cover discovery and AI disclosure: {arguments.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
