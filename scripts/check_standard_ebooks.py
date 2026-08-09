#!/usr/bin/env python3
"""Check Standard Ebooks' public catalog for an existing edition."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, replace
from difflib import SequenceMatcher
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from xml.etree import ElementTree

CATALOG_URL = "https://standardebooks.org/ebooks"
USER_AGENT = "skill-create-ebook/1.0 (+https://standardebooks.org/)"
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"
NAMESPACE = {"x": XHTML_NAMESPACE}


@dataclass(frozen=True)
class CatalogEntry:
    title: str
    author: str
    url: str
    status: str
    title_similarity: float
    contained_title: str | None = None


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    ascii_value = "".join(character for character in decomposed if not unicodedata.combining(character))
    return " ".join(re.findall(r"[a-z0-9]+", ascii_value))


def primary_title(value: str) -> str:
    return value.split(":", 1)[0].strip()


def author_key(value: str) -> tuple[str, ...]:
    return tuple(sorted(normalize(value).split()))


def title_similarity(left: str, right: str) -> float:
    left_normalized = normalize(primary_title(left))
    right_normalized = normalize(primary_title(right))
    if left_normalized == right_normalized:
        return 1.0
    return SequenceMatcher(None, left_normalized, right_normalized).ratio()


def _text(element: ElementTree.Element | None) -> str:
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def parse_catalog_entries(document: bytes, requested_title: str) -> list[CatalogEntry]:
    try:
        root = ElementTree.fromstring(document)
    except ElementTree.ParseError as exception:
        raise RuntimeError("Standard Ebooks returned a catalog page that could not be parsed.") from exception

    entries: list[CatalogEntry] = []
    for item in root.findall('.//x:li[@typeof="schema:Book"]', NAMESPACE):
        title_element = item.find('.//x:span[@property="schema:name"]', NAMESPACE)
        author_element = item.find('.//x:p[@property="schema:author"]//x:span[@property="schema:name"]', NAMESPACE)
        entry_title = _text(title_element)
        entry_author = _text(author_element)
        relative_url = item.get("about", "")
        if not entry_title or not entry_author or not relative_url:
            continue
        classes = set(item.get("class", "").split())
        status = "wanted" if "wanted" in classes else "available"
        entries.append(
            CatalogEntry(
                title=entry_title,
                author=entry_author,
                url=urljoin(CATALOG_URL, relative_url),
                status=status,
                title_similarity=title_similarity(requested_title, entry_title),
            )
        )
    return entries


def fetch_catalog_entries(title: str, timeout: float = 30) -> list[CatalogEntry]:
    query_url = f"{CATALOG_URL}?{urlencode({'query': title, 'per-page': '48'})}"
    request = Request(
        query_url,
        headers={
            "Accept": "application/xhtml+xml,application/xml;q=0.9,text/html;q=0.8",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            document = response.read()
    except (HTTPError, URLError, TimeoutError) as exception:
        raise RuntimeError(f"Could not verify the Standard Ebooks catalog: {exception}") from exception
    return parse_catalog_entries(document, title)


def repository_name(entry: CatalogEntry) -> str:
    marker = "/ebooks/"
    if marker not in entry.url:
        raise RuntimeError(f"Unexpected Standard Ebooks URL: {entry.url}")
    return "_".join(part for part in entry.url.split(marker, 1)[1].split("/") if part)


def fetch_edition_toc(entry: CatalogEntry, timeout: float) -> bytes:
    repository = repository_name(entry)
    url = f"https://raw.githubusercontent.com/standardebooks/{repository}/master/src/epub/toc.xhtml"
    request = Request(url, headers={"Accept": "application/xhtml+xml", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as exception:
        if exception.code == 404:
            return b""
        raise RuntimeError(f"Could not inspect the contents of {entry.url}: {exception}") from exception
    except (URLError, TimeoutError) as exception:
        raise RuntimeError(f"Could not inspect the contents of {entry.url}: {exception}") from exception


def toc_contains_title(document: bytes, title: str) -> bool:
    if not document:
        return False
    try:
        root = ElementTree.fromstring(document)
        toc_text = " ".join(root.itertext())
    except ElementTree.ParseError as exception:
        raise RuntimeError("A Standard Ebooks table of contents could not be parsed.") from exception
    return normalize(primary_title(title)) in normalize(toc_text)


def check_catalog(title: str, author: str, timeout: float = 30) -> dict[str, object]:
    entries = fetch_catalog_entries(title, timeout)
    requested_author = author_key(author)
    candidates = [
        entry
        for entry in entries
        if author_key(entry.author) == requested_author and entry.title_similarity >= 0.72
    ]
    exact = [entry for entry in candidates if entry.title_similarity == 1.0]
    relevant = exact or candidates
    available = [entry for entry in relevant if entry.status == "available"]
    wanted = [entry for entry in relevant if entry.status == "wanted"]

    contained: list[CatalogEntry] = []
    if not available:
        author_entries = fetch_catalog_entries(author, timeout)
        related_editions = [
            entry
            for entry in author_entries
            if author_key(entry.author) == requested_author and entry.status == "available"
        ]
        seen_urls: set[str] = set()
        for entry in related_editions:
            if entry.url in seen_urls:
                continue
            seen_urls.add(entry.url)
            if toc_contains_title(fetch_edition_toc(entry, timeout), title):
                contained.append(
                    replace(entry, status="contains-work", title_similarity=1.0, contained_title=title)
                )

    matches = available + contained
    if matches:
        decision = "stop"
        message = "A published Standard Ebooks edition contains this work. Stop and use the official edition."
    elif wanted:
        decision = "continue"
        message = "The title is in Standard Ebooks’ wanted catalog, but no edition is published yet."
        matches = wanted
    elif relevant:
        decision = "review"
        message = "A similar catalog result needs human review before work begins."
        matches = relevant
    else:
        decision = "continue"
        message = "No matching published Standard Ebooks edition was found."
        matches = []

    return {
        "query": {"title": title, "author": author},
        "decision": decision,
        "message": message,
        "matches": [asdict(entry) for entry in matches],
        "search_url": f"{CATALOG_URL}?{urlencode({'query': title})}",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        result = check_catalog(arguments.title, arguments.author, arguments.timeout)
    except RuntimeError as exception:
        print(f"error: {exception}", file=sys.stderr)
        print("Do not begin an unofficial edition until the catalog check succeeds.", file=sys.stderr)
        return 2

    if arguments.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["message"])
        for match in result["matches"]:
            if match["status"] == "contains-work":
                print(
                    f"- [contains work] {match['contained_title']} in {match['title']} "
                    f"— {match['author']}: {match['url']}"
                )
            else:
                print(f"- [{match['status']}] {match['title']} — {match['author']}: {match['url']}")
        print(f"Catalog search: {result['search_url']}")
    return 3 if result["decision"] in {"stop", "review"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
