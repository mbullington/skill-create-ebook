# AI-Generation Disclosure

Every generated EPUB begins with `text/ai-generation-disclosure.xhtml`. It is the first spine item and the first table-of-contents entry.

Use `scripts/add_disclosure.py` to create it. Preserve these facts when adapting the prose:

1. The edition is unofficial and AI-generated.
2. Standard Ebooks did not produce, review, or endorse it.
3. Readers should check the official catalog and prefer a published Standard Ebooks edition.
4. Standard Ebooks volunteers invest substantial time in research, scan comparison, transcription correction, semantic markup, typography, artwork research, proofreading, review, and compatibility testing.
5. Automated production cannot replace that work.
6. The edition builds on Standard Ebooks’ open-source tools, Manual of Style, and production guidance.
7. The exact text source and build process are identified.
8. Automated transformations and AI-assisted decisions may introduce or preserve defects.
9. The EPUB is an interim reading copy, not a publication-quality Standard Ebook.

## Accuracy

Describe only the Standard Ebooks resources actually used. “Builds on the project’s tools and guidance” is accurate when using the `se` toolchain and manual. Do not claim that an unofficial edition derives from a particular Standard Ebooks ebook unless files from that ebook were used and their license and attribution requirements were followed.

Do not add Standard Ebooks branding to the cover, title page, publisher metadata, or colophon. The disclosure provides attribution and context; it does not grant permission to imply affiliation.

## Placement checks

The final package must satisfy all of these conditions:

- `content.opf` contains one manifest item for the disclosure.
- The disclosure’s `itemref` is first in the spine.
- The table of contents links to it first.
- The XHTML contains the source URL and official catalog link.
- The page survives compatible and advanced builds.

Run `scripts/verify_ebook.py` on both the source tree and each final EPUB.
