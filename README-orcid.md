# DOCX author block and ORCID support

The local `0.3.0-dev` version adds a DOCX author renderer with the order **name → ORCID → affiliation/equal-contribution superscripts → correspondence envelope**. Institutions use numbers, equal contributors use `†`, and corresponding authors use a black envelope at normal line height. The original green ORCID artwork is preserved. Both icons are embedded as SVG with bundled PNG fallbacks for older viewers; document rendering needs no network or converter.

This is our serif author-block design, not a publisher's official specification. At the default 12 pt author size, the ORCID drawing is 9 pt (.75 em). Marks are 8 pt (2/3 em), raised 4.5 pt (.375 em). The envelope outline is .85 em wide and .65 em high, with .05 em transparent padding above/below in a .75 em-high canvas to align its visual center with the ORCID. Image runs themselves are never superscript or raised. Target gaps are .15 em before ORCID, .10 em between ORCID and marks, .05 em before marks without ORCID, and .15 em before the envelope. Word geometry rounds to its supported precision; the ORCID has a .0125 em optical correction before the image.

Each affiliation is a separate paragraph. The equal-contribution note reads “同等贡献” for Chinese and “Equal contribution” otherwise. Corresponding email addresses share one paragraph in author order, separated by semicolons, with a single leading envelope and individual mailto links. Names and a “Correspondence:” label are not repeated. The author-line envelope also links to that author's email when supplied; a missing email does not create an empty contact paragraph or empty link. Dates and abstracts follow these details.

Each author-line affiliation number links to its institution paragraph, and each `†` links to the shared equal-contribution note. For example, `1,2,†` contains three separate internal links; its commas remain unlinked separators. The marks retain their black, non-underlined superscript appearance, including after following a link. Bookmark names are allocated automatically without colliding with existing document identifiers. No extra YAML or manually inserted Word bookmarks are needed.

ORCID accepts a bare iD or an `https://orcid.org/...` URL, validates its format and ISO 7064 check digit, and fails clearly on invalid input. An absent ORCID leaves no placeholder. This is formatting and validation, not identity authentication.

Use the filter under `format.docx.filters`. For PDF see README-pdf.md; HTML should keep its native metadata handling. Institutional superscripts, equal contributors, corresponding authors, optional affiliations, structured names and Chinese labels are supported.

Use the reference document's `Author`, `Affiliation`, `Author Note` and `Author Contact` paragraph styles to control fonts and alignment. `Affiliation Last`, `Author Note Last` and `Author Contact Continued` provide spacing variants without blank paragraphs. `Author Email` is a character style for black, non-underlined links. The accompanying quarto-template references use 12 pt authors and 10.5 pt notes, centered, with 1.15 line spacing; author/affiliation/group/contact gaps are 6/2/4/2/6 pt as described in that repository's design specification.

If those reference font sizes change, set the matching inline-size bases (these options do not override paragraph fonts):

```yaml
authors-block:
  docx:
    author-size: 12
    note-size: 10.5
```

```yaml
author:
  - name: Josiah Carberry
    orcid: 0000-0002-1825-0097
    affiliations:
      - ref: example
    corresponding: true
    email: example@example.org
affiliations:
  - id: example
    name: Example institution
format:
  docx:
    filters: [authors-block]
```

Use `quarto add <path-to-this-repository>` for local testing. After a release is published, pin its tag in `quarto add wiederholung/authors-block@<tag>`. No `0.3.0` remote release is implied by this working tree. Commit the installed `_extensions` files in consuming projects.

The repository's integration check is `python tests/check_docx.py`; it uses the installed Quarto CLI and Python's standard library. Nine cases cover structured names, multiple affiliations, both author symbols, merged emails, optional metadata, inline size overrides, internal link destinations, bookmark collisions and invalid ORCID identifiers. Native Word rendering and internal hyperlink navigation are checked separately in quarto-template. The examples are static and require no R environment.
