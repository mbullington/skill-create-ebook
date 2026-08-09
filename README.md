# Create Ebook Skill

An agent skill for making reproducible, unofficial, AI-assisted EPUBs of public-domain books. It uses the Standard Ebooks toolchain and production guidance, but it does not produce or claim to produce Standard Ebooks.

Generated books are white-label editions with a disclosure page explaining their source, automated production, and limitations. Before beginning a book, the skill checks the official Standard Ebooks catalog. If Standard Ebooks has already published the work—either by itself or in a collection—the skill stops and directs the reader to that edition.

## What is Standard Ebooks?

[Standard Ebooks](https://standardebooks.org/) is a volunteer-driven project that creates free, open-source editions of public-domain books. Its contributors turn existing transcriptions and page scans into carefully edited ebooks with consistent typography, semantic markup, accessible navigation, complete metadata, public-domain cover art, and compatibility across reading software.

This goes well beyond converting text into an EPUB file. A Standard Ebook may take a team of specialists weeks or months to research, typeset, compare against scans, proofread, review, and test. The finished source is released openly, and the ebook is distributed free of cost and free of U.S. copyright restrictions.

For more background, read [What Makes Standard Ebooks Different](https://standardebooks.org/about/what-makes-standard-ebooks-different) and the [Standard Ebooks Manual of Style](https://standardebooks.org/manual/latest).

## What this project reuses

This skill builds on resources that Standard Ebooks makes available to ebook producers:

- the open-source [`standardebooks`](https://pypi.org/project/standardebooks/) Python toolset for scaffolding, cleaning, linting, and building EPUBs;
- the [Manual of Style](https://standardebooks.org/manual/latest) and public production guidance;
- the official catalog, used to avoid creating an automated substitute for an existing Standard Ebook; and
- the toolset’s white-label draft format, which omits Standard Ebooks branding.

It does **not** reuse the Standard Ebooks name as a publisher identity, imply review or endorsement, or add the project’s logos, colophons, identifiers, or release URLs to generated books. Unless a book’s production notes explicitly say otherwise, it also does not copy source files from a published Standard Ebook.

## Why an AI-generated edition is not a Standard Ebook

AI can help extract text, apply repeatable transformations, generate markup, and run validators. Those tasks can make a useful reading copy, but they do not replace editorial judgment.

An automated process can preserve OCR mistakes, damage poetry or multi-paragraph quotations, choose the wrong punctuation, misread a footnote, miss differences between editions, or produce plausible but incorrect rights and artwork claims. EPUB validation only shows that a package follows technical rules; it does not prove that the words are accurate, the structure is meaningful, or the book has been proofread.

Standard Ebooks relies on human research, scan comparison, transcription correction, semantic editing, artwork research, proofreading, review, and compatibility testing. This skill therefore calls its output an **unofficial AI-generated interim edition**, identifies the text source and process, and records work that still needs human review. If an official Standard Ebooks edition exists, readers should use that edition instead.

## Support Standard Ebooks

This project benefits from work that Standard Ebooks gives away: its ebooks, production tools, Manual of Style, and technical guidance. If those resources are useful to you, [donate directly to Standard Ebooks](https://standardebooks.org/donate).

The official donation page offers one-time and monthly donations processed by Fractured Atlas, Standard Ebooks’ fiscal sponsor. It also explains Patrons Circle membership, sponsoring a particular ebook, donor-advised funds, and corporate sponsorship. Donations are tax-deductible to the extent permitted by law.

You can also [get involved as a volunteer](https://standardebooks.org/contribute) by reporting errors, proofreading, producing ebooks, improving tools, or contributing through GitHub.

## Set up the skill

Requirements:

- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/)
- an agent that can load a directory-based skill, or another way to give your agent access to `SKILL.md` and the bundled files

Clone the repository and install its locked dependencies:

```sh
git clone https://github.com/mbullington/skill-create-ebook.git
cd skill-create-ebook
uv sync --locked
```

The repository itself is the skill; there is no installer. Point your agent’s skill configuration at this directory, or copy or symlink the directory into the location where your agent discovers skills. Keep `SKILL.md`, `references/`, `scripts/`, `pyproject.toml`, and `uv.lock` together. The exact skill directory and reload behavior depend on the agent, so consult its documentation.

Read [`SKILL.md`](SKILL.md) for the agent workflow and [`references/editorial-workflow.md`](references/editorial-workflow.md) for production details.

## Bundled tools

Check for an existing published edition:

```sh
uv run python scripts/check_standard_ebooks.py \
  --title "Pride and Prejudice" \
  --author "Jane Austen"
```

Create a white-label draft only when no published edition exists:

```sh
uv run python scripts/scaffold_ebook.py \
  --workspace /tmp/ebook-work \
  --title "Book Title" \
  --author "Author Name"
```

Add or update the required disclosure:

```sh
uv run python scripts/add_disclosure.py /path/to/source-tree \
  --title "Book Title" \
  --source-url "https://example.test/source" \
  --source-description "the named public-domain transcription"
```

Verify cover metadata and disclosure placement:

```sh
uv run python scripts/verify_ebook.py /path/to/source-tree
uv run python scripts/verify_ebook.py /path/to/book.epub
```

## Scope and limitations

The bundled scripts handle repeatable catalog checks and package edits. Each book still needs a source-specific extraction adapter, jurisdiction-specific rights research, comparison against page scans, editorial review, proofreading, and testing in real reading software.

The catalog check can fail when the network or Standard Ebooks website is unavailable. It deliberately stops rather than treating a failed lookup as proof that no edition exists. Public-domain status also varies by jurisdiction and must be researched separately for the text, translation, transcription, introduction, notes, illustrations, and cover art.

## Test

```sh
uv run python -m unittest discover -s tests -v
```

The tests cover published and wanted catalog entries, works contained in collections, Project Gutenberg URL canonicalization, idempotent disclosure insertion, cover metadata, and disclosure placement.

## Independence

This is an independent project. It is not affiliated with, produced by, reviewed by, or endorsed by Standard Ebooks.
