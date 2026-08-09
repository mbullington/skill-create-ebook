# Editorial and Build Workflow

Read this before planning or implementing an unofficial edition.

## 1. Check for a published Standard Ebook

Run:

```sh
uv run python "$SKILL_DIR/scripts/check_standard_ebooks.py" \
  --title "BOOK TITLE" \
  --author "AUTHOR"
```

A published match is a hard stop. Give the user its Standard Ebooks URL instead of generating a competing automated edition. The checker also examines tables of contents for the author’s published collections; an essay, story, or chapter inside a larger volume counts as an existing edition.

Standard Ebooks search results may include entries marked `wanted`. These are requests for future productions, not published editions. The checker distinguishes them from available ebooks. If the catalog cannot be reached or parsed, stop until the check succeeds; absence of evidence is not evidence of absence.

Repeat the check immediately before release because the catalog changes.

## 2. Establish rights and provenance

Confirm that the work, translation, transcription, and artwork are public domain where the user will distribute the EPUB. Public-domain status is jurisdiction-specific. Do not infer a translation’s status from the original work’s status.

Prefer source transcriptions with page scans. Record:

- transcription URL and stable identifier;
- exact downloaded-file SHA-256;
- scan edition, publisher, date, and scan URL;
- translator and illustrator, including death dates when relevant;
- artwork title, artist, date, holding institution, source URL, rights declaration, and SHA-256;
- every editorial change that departs from the transcription.

Pin all remote inputs. A reproducible build must fail when upstream content changes rather than silently accepting it.

## 3. Create a white-label source tree

Use `se create-draft --offline --white-label`. Do not use Standard Ebooks logos, colophons, identifiers, release URLs, or publisher metadata. Do not describe the result as a Standard Ebook.

The bundled `scaffold_ebook.py` runs the catalog check before creating a draft. Book source HTML varies too much for a safe universal extractor. Inspect headings, paragraph boundaries, blockquotes, verse, letters, footnotes, illustrations, tables, and end matter, then write the smallest book-specific adapter.

Preserve structure before normalizing typography. Gutenberg blockquotes often contain several paragraphs; flattening descendant paragraphs destroys letters and multi-paragraph quotations.

## 4. Add the disclosure

Create the disclosure XHTML before typography cleanup so `se typogrify` can normalize its prose. After the final `se build-toc`, run `add_disclosure.py` again so it is first in the manifest spine and table of contents. The operation is idempotent.

The disclosure must remain first in the reading order, before the title page. Keep it candid and specific. It must not imply Standard Ebooks endorsed the edition.

## 5. Mechanical cleanup sequence

A reliable sequence is:

```sh
se typogrify epub/text
# Apply reviewed, book-specific surgical transformations.
se clean BOOK_DIR
se build-manifest BOOK_DIR
se build-spine BOOK_DIR
# Reorder the spine explicitly when reading order matters.
se build-toc BOOK_DIR
se clean BOOK_DIR
# Reapply only transformations that `se clean` intentionally canonicalizes away.
python "$SKILL_DIR/scripts/add_disclosure.py" ...
se lint BOOK_DIR
se build --check BOOK_DIR
```

`se clean` may move punctuation around italics or otherwise canonicalize markup. If an editorially reviewed change must survive, apply it after the final clean and validate the resulting XHTML. Do not use this as an excuse to fight intentional Standard Ebooks conventions blindly.

Treat lint categories correctly:

- Errors must be resolved before release.
- Manual-review findings are prompts for editorial judgment, not automatic defects.
- Do not hide unresolved findings in `se-lint-ignore.xml` merely to obtain a clean report.
- Nested dialogue, multi-paragraph quotations, epigraph punctuation, and ambiguous OCR require scan comparison.

## 6. Artwork and cover discovery

Choose thematically appropriate public-domain art from an institution that provides a rights statement and a high-resolution image. Prefer subtle thematic relationships over literal plot illustration. Record provenance in metadata and production notes.

A reading app discovers the cover through the OPF manifest item with `properties="cover-image"`. Verify that exactly one such item exists and that its image is packaged. Some services, including Google Play Books, process uploaded covers asynchronously.

## 7. Validation

Run the closest real checks available:

- `se lint` and preserve its report;
- `se build --check`, which invokes EPUB validation in the supported toolchain;
- epubcheck explicitly when it is not covered by the build;
- Nu HTML Validator for compatible output;
- `verify_ebook.py` against source trees and final EPUBs;
- a second clean build followed by SHA-256 comparison;
- visual inspection in at least one real reading application.

Builds and validators do not prove editorial quality. State what remains: scan comparison, cover-to-cover proofreading, manual semantic review, and device testing.

## 8. Completion report

Link the official catalog search, sources, artwork records, lint reports, production notes, compatible EPUB, and advanced EPUB. Separate automated errors from manual-review findings. Never call the edition publication-quality unless humans completed and documented the full editorial process.
