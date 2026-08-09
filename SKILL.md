---
name: skill-create-ebook
description: Create reproducible, unofficial, AI-assisted public-domain EPUBs with Standard Ebooks’ open-source toolchain and production guidance. Use whenever a user asks to make, convert, polish, rebuild, or package a public-domain book as an EPUB or “Standard-Ebooks-style” edition, especially from Project Gutenberg, Internet Archive scans, or OCR. Check for a real Standard Ebooks edition first, disclose AI generation, research cover art, preserve provenance, and validate the final ebook.
---

# Create an Unofficial Public-Domain Ebook

Produce a candid white-label reading edition without implying that Standard Ebooks made or endorsed it.

Set `SKILL_DIR` to the directory containing this file when running bundled scripts. Read [`references/editorial-workflow.md`](references/editorial-workflow.md) before beginning. Read [`references/disclosure-page.md`](references/disclosure-page.md) before writing front matter.

## Gate: check Standard Ebooks first

Run this before downloading a transcription, scaffolding files, or researching artwork:

```sh
uv run --project "$SKILL_DIR" python "$SKILL_DIR/scripts/check_standard_ebooks.py" \
  --title "TITLE" \
  --author "AUTHOR"
```

The checker searches both standalone titles and the tables of contents of published collections by the same author. This prevents rebuilding an essay, story, or chapter that Standard Ebooks already publishes inside a larger volume.

Interpret the result exactly:

- **Published standalone edition or work contained in a published collection:** stop. Link the Standard Ebooks page and recommend it. Do not build an unofficial substitute and do not offer an override.
- **Wanted listing:** explain that Standard Ebooks wants the title but has not published it; production may continue.
- **No match:** production may continue.
- **Network, parsing, or ambiguous-match failure:** stop until a human can verify the catalog.

Repeat the check before final release because the catalog changes.

## Establish scope and rights

Confirm the requested work, edition, language, translation, output variants, and intended jurisdiction. Check rights separately for the original work, translation, transcription, introduction, notes, illustrations, and cover art. If public-domain status is uncertain, stop and state what evidence is missing.

Create `production-notes.md` early. Record source URLs, editions, dates, rights evidence, SHA-256 hashes, artwork provenance, and editorial changes.

## Scaffold a white-label project

For a new project, run:

```sh
uv run --project "$SKILL_DIR" python "$SKILL_DIR/scripts/scaffold_ebook.py" \
  --workspace /path/to/workspace \
  --title "TITLE" \
  --author "AUTHOR"
```

Add `--translator` when applicable. The script performs the catalog gate and invokes `se create-draft --offline --white-label`.

Use a project-local `pyproject.toml`, `uv.lock`, build script, verification script, source cache, reports directory, source tree, and `dist/`. Pin dependencies and every remote input. Make rebuilds deterministic, including ZIP timestamps and metadata modification dates.

## Adapt the source deliberately

Inspect the transcription and scans before writing extraction logic. Gutenberg and OCR HTML do not have a universal structure. Write a small book-specific adapter rather than a parser that guesses silently.

Preserve semantic units: headings, paragraphs, multi-paragraph blockquotes, verse, letters, epigraphs, notes, tables, and illustrations. Remove distributor boilerplate without removing book content. Compare suspicious text and all non-mechanical edits against scans.

Automate only transformations whose correctness follows from structure or an explicit rule. Keep ambiguous quotation, punctuation, OCR, and semantic findings for human review.

## Add a candid disclosure

Every output begins with an AI-generation disclosure before the title page. It explains the edition’s unofficial status, Standard Ebooks’ human editorial work, the source and process, and the automated edition’s limitations.

Create the XHTML before typography cleanup. After the final `se build-toc`, run the bundled script again to enforce final spine and navigation placement:

```sh
uv run --project "$SKILL_DIR" python "$SKILL_DIR/scripts/add_disclosure.py" \
  /path/to/book-source \
  --title "TITLE" \
  --source-url "https://example.test/source" \
  --source-description "the public-domain transcription DESCRIPTION"
```

The script is idempotent. Do not replace its required disclosure with branding, a vague “made with AI” badge, or language suggesting affiliation.

## Research artwork

Prefer high-resolution public-domain art from a museum, library, or archive with a clear rights statement. Choose a defensible thematic connection rather than a literal plot summary. Verify the artist’s dates and the image’s rights, record the institution and object URL, pin the source hash, and credit the artist in metadata and production notes.

Keep covers white-label. Do not use Standard Ebooks logos, colophons, publisher identity, identifiers, or release URLs.

## Build and validate

Follow the command order and caveats in [`references/editorial-workflow.md`](references/editorial-workflow.md). Resolve all automated lint errors. Report manual-review findings instead of blindly changing or suppressing them.

Build compatible and advanced EPUBs when supported. Then run:

```sh
uv run --project "$SKILL_DIR" python "$SKILL_DIR/scripts/verify_ebook.py" /path/to/source-tree
uv run --project "$SKILL_DIR" python "$SKILL_DIR/scripts/verify_ebook.py" /path/to/book.epub
```

Also run `se build --check`, epubcheck, HTML validation, and a second build with SHA-256 comparison. Inspect the cover and disclosure in a real reader when available. Verify that the manifest has exactly one `cover-image`; services may extract uploaded covers asynchronously.

## Completion standard

Deliver links to the EPUBs, source trees, production notes, catalog check, artwork sources, and lint reports. State automated-error and manual-review counts separately. List scan comparison, proofreading, or device review that remains.

Call the result an **unofficial AI-generated interim edition**, never a Standard Ebook or publication-quality edition. A validator proves package correctness, not editorial quality.
