# Authors-block Extension For Quarto

<!-- badges: start -->
[![R build status](https://github.com/kapsner/authors-block/workflows/tests/badge.svg?branch=main)](https://github.com/kapsner/authors-block/actions)
<!-- badges: end -->

This extension brings the capability to add an author-related header block when rendering docx-documents with Quarto.

This fork's local `0.3.0-dev` adds vector ORCID and correspondence icons,
equal-contribution marks, merged email links and Chinese author notes for DOCX.
See [DOCX author-block support](README-orcid.md) for
installation, examples and integration checks. These changes are not yet published.

The extension adds some modifications to the code originally provided with the lua-filters [scholarly-metadata](https://github.com/pandoc/lua-filters/tree/master/scholarly-metadata) (by Albert Krewinkel and Robert Winkler) and [author-info-block](https://github.com/pandoc/lua-filters/tree/master/author-info-blocks) (by Albert Krewinkel) in order to make it compatible with Quarto and its [normalized author-block](https://quarto.org/docs/journals/authors.html).  

## Installing

```bash
quarto add ../authors-block
```

Run this from the consuming project and adjust the path to this local checkout.
After publishing a release, install the fork with a chosen tag as described in
[DOCX ORCID support](README-orcid.md). Installing the upstream repository does
not include this fork's unpublished ORCID changes.

Using `authors-block` requires Quarto version >= 1.3.0

This will install the extension under the `_extensions` sub-directory.
If you're using version control, you will want to check in this directory.

## Using

<br>
<img src="example.png" align="center" width=100% />
<br>

## Example

Here is the source code for a minimal example: [example.qmd](example.qmd).

```yml
---
title: "Authors-block Example"

authors:
  - name: John Doe
    affiliations:
      - ref: jdct
    corresponding: true
    email: john.doe@jdct.edu
    # Official example record; replace before using this author metadata.
    orcid: 0000-0002-1825-0097
    equal-contributor: true
  - name: John Roe
    affiliations:
      - ref: jdct
  - name: Jane Roe
    affiliations:
      - ref: jdct
      - ref: iot
    equal-contributor: true

affiliations:
  - id: jdct
    name: John Doe Center for Technology, John Doe University, Doetown, Germany.
  - id: iot
    name: Institute of Technology, John Doe University, Doetown, Germany.

filters:
  - authors-block

format:
  docx: default
  pdf:
    keep-tex: true
---
```
