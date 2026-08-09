from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from add_disclosure import canonical_public_source_url, update_opf, update_toc, write_disclosure
from check_standard_ebooks import parse_catalog_entries, toc_contains_title
from verify_ebook import verify


class CatalogTests(unittest.TestCase):
    def test_published_and_wanted_entries_are_distinct(self) -> None:
        document = b'''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body><ol class="ebooks-list">
<li about="/ebooks/jane-austen/pride-and-prejudice" typeof="schema:Book">
<span property="schema:name">Pride and Prejudice</span>
<p property="schema:author"><span property="schema:name">Jane Austen</span></p>
</li>
<li about="/ebooks/stendhal/the-red-and-the-black" class="ribbon wanted" typeof="schema:Book">
<span property="schema:name">The Red and the Black</span>
<p property="schema:author"><span property="schema:name">Stendhal</span></p>
</li>
</ol></body></html>'''
        entries = parse_catalog_entries(document, "Pride and Prejudice")
        self.assertEqual([entry.status for entry in entries], ["available", "wanted"])
        self.assertEqual(entries[0].title_similarity, 1.0)

    def test_component_title_is_found_in_collection_toc(self) -> None:
        document = b'''<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml"><body><nav><ol>
<li><a href="text/on-the-shortness-of-life.xhtml">On the Shortness of Life</a></li>
</ol></nav></body></html>'''
        self.assertTrue(toc_contains_title(document, "On the Shortness of Life"))
        self.assertFalse(toc_contains_title(document, "On Benefits"))


class DisclosureTests(unittest.TestCase):
    def test_project_gutenberg_download_url_becomes_canonical(self) -> None:
        source = "https://www.gutenberg.org/cache/epub/8578/pg8578-images.html"
        self.assertEqual(canonical_public_source_url(source), "https://www.gutenberg.org/ebooks/8578")

    def test_disclosure_update_is_idempotent_and_verifiable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            epub = Path(temporary) / "epub"
            (epub / "text").mkdir(parents=True)
            (epub / "images").mkdir()
            (epub / "images" / "cover.jpg").write_bytes(b"test")
            (epub / "content.opf").write_text(
                '''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
\t<metadata/>
\t<manifest>
\t\t<item href="images/cover.jpg" id="cover.jpg" media-type="image/jpeg" properties="cover-image"/>
\t\t<item href="text/titlepage.xhtml" id="titlepage.xhtml" media-type="application/xhtml+xml"/>
\t\t<item href="toc.xhtml" id="toc.xhtml" media-type="application/xhtml+xml" properties="nav"/>
\t</manifest>
\t<spine><itemref idref="titlepage.xhtml"/></spine>
</package>
''',
                encoding="utf-8",
            )
            (epub / "toc.xhtml").write_text(
                '''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
\t<head><title>Table of Contents</title></head>
\t<body><nav epub:type="toc"><ol><li><a href="text/titlepage.xhtml">Titlepage</a></li></ol></nav></body>
</html>
''',
                encoding="utf-8",
            )

            for _ in range(2):
                write_disclosure(
                    epub,
                    "Test Book",
                    "https://example.test/source",
                    "a public-domain test transcription",
                    "The source was hash-pinned and validated.",
                )
                update_opf(epub)
                update_toc(epub)

            self.assertEqual(verify(epub), [])


if __name__ == "__main__":
    unittest.main()
