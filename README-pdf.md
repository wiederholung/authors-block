# PDF author block

The LaTeX backend supports XeLaTeX with `ctexart` and `scrartcl`.
Install with `quarto add ../authors-block`, or a published pinned release.

```yaml
format:
  pdf:
    documentclass: scrartcl
    pdf-engine: xelatex
    filters:
      - quarto
      - authors-block
```

Run after Quarto so the filter can consume normalized `by-author` and
`by-affiliation`. The filter leaves author metadata, date and abstract intact.
It sets `\author` in a begin-document hook; the document class still owns
`\maketitle`, author fonts, date and surrounding spacing. It does not replace
the title template or post-process the PDF. Other document classes need an
explicit adapter and currently produce a clear error.

Authors appear as name, linked vector ORCID, linked institution/equal-contribution
superscripts, and linked vector envelope. Institution numbers and daggers point
to their notes. Emails share a line, in author order. Missing optional fields
leave no placeholder. All link colors follow the document's hyperref settings.
Assets are bundled and resolved relative to the installed extension, offline.

`latex-author-block.tex` contains the presentation defaults; Lua handles data
and links. Defaults can be overridden in `include-in-header` using
`\newcommand` (the extension supplies them with `\providecommand`):

```tex
\newcommand{\AuthorsBlockNoteFont}{\small}
\newcommand{\AuthorsBlockIconScale}{1}
\newcommand{\AuthorsBlockIconGap}{.15em}
\newcommand{\AuthorsBlockMarkGap}{.08em}
\newcommand{\AuthorsBlockGroupGap}{.45\baselineskip}
\newcommand{\AuthorsBlockNoteGap}{.15\baselineskip}
```

Icons use the current font's capital H height, without superscripting.
Notes default to the class's `\small`. The bounded author area can wrap;
spaces in long names remain breakable. Date and abstract follow the complete
author area. The block is not intended for multi-page consortium author lists.

Validation: `python tests/check_pdf.py` requires Quarto, XeLaTeX and pypdf.
The existing DOCX regression suite remains `python tests/check_docx.py`.
