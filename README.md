# Create Ebook Skill

A BB skill for creating reproducible, unofficial, AI-generated public-domain EPUBs with the Standard Ebooks toolchain and production guidance.

The skill checks Standard Ebooks’ official catalog first, including works contained in larger published collections. If a published edition exists, it stops and recommends that edition. Generated EPUBs are white-label and begin with a disclosure explaining their provenance and limitations.

## Install

```sh
cd ~/Projects/skill-create-ebook
uv sync --locked
uv run python scripts/install_skill.py
```

The installer copies the source package to `~/.bb/skills/skill-create-ebook`. Run it again after editing the source. New BB threads will discover the installed revision; existing threads do not reload skill metadata.

## Bundled tools

```sh
# Check for an existing published edition.
uv run python scripts/check_standard_ebooks.py \
  --title "Pride and Prejudice" \
  --author "Jane Austen"

# Create a white-label draft only when no published edition exists.
uv run python scripts/scaffold_ebook.py \
  --workspace /tmp/ebook-work \
  --title "Book Title" \
  --author "Author Name"

# Add or update the required disclosure.
uv run python scripts/add_disclosure.py /path/to/source-tree \
  --title "Book Title" \
  --source-url "https://example.test/source" \
  --source-description "the named public-domain transcription"

# Verify cover metadata and disclosure placement.
uv run python scripts/verify_ebook.py /path/to/source-tree
uv run python scripts/verify_ebook.py /path/to/book.epub
```

Read [`SKILL.md`](SKILL.md) for the agent workflow and [`references/editorial-workflow.md`](references/editorial-workflow.md) for production details.

## Test

```sh
uv run python -m unittest discover -s tests -v
```

The tests cover published-versus-wanted catalog entries, titles contained in collections, Project Gutenberg URL canonicalization, idempotent disclosure insertion, cover metadata, and disclosure placement.

## Scope

The bundled tools handle repeatable checks and package edits. Each book still needs a source-specific extraction adapter, rights research, scan comparison, editorial review, and proofreading. Passing EPUB validators does not make an automated edition equivalent to a human-produced Standard Ebook.
