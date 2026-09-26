# Availability statements

Draft wording for the submitted manuscript. Everything here is copy-paste
ready; the `[…]` brackets are the only parts that need filling in.

---

## 1. Software availability

> To support reproducible application, the scoring framework was implemented
> in GPDI Analyzer (Version 1.0.0), a standalone tool that calculates GPDI and
> its component measures for individual texts or text batches. The software
> follows the same construct boundary as the present study and is publicly
> available at https://github.com/fancy61333/GPDI-Analyzer.
>
> The repository carries the complete scoring code — every constant and weight
> used in Section `[X]` is readable in `core/gpdi.py` — together with usage
> documentation, build scripts and sample input data. Release v1.0.0 provides a
> compiled Windows build; a macOS build is produced from the same source with
> `./build_macos.sh --public`.

If the journal wants a separate, labelled heading rather than a sentence inside
the method section, use:

> **Software availability.** GPDI Analyzer (Version 1.0.0), [Computer
> software]. https://github.com/fancy61333/GPDI-Analyzer. MIT licence.

---

## 2. What the software does not carry, and why

Put this in the same section, or in a footnote to it. Elsevier's availability
policy asks authors to share what they can and to *state the reason* when
something cannot be shared; an unexplained omission is what causes queries, not
the omission itself.

> Two assets are not distributed with the software.
>
> **The graded character inventory.** Character-level matching requires a
> graded inventory of `[3,500]` characters. The inventory used here derives
> from prior work of the research group and is subject to that group's
> intellectual-property position; it is therefore not the authors' to
> redistribute as an open data file. Accordingly no copy of it — plain-text,
> packed, or otherwise — is included in the repository or in any release asset.
> The software is written to accept any inventory supplied in a documented
> `char,level_value` format, so a researcher who obtains the inventory from the
> owning group can load it into the distributed build and reproduce the
> analyses in full; the application reports on launch that no inventory is
> loaded. Requests for the inventory should be addressed to `[owner / contact]`.
>
> **The reference corpus figures.** The per-poem figures for the `[82]`-poem
> reference corpus are results of the present study and are not published
> outside the manuscript, so the corpus files are not distributed. The
> corpus-relative banding is consequently unavailable in the distributed build
> (it is read from those files); all other measures reported here are produced
> by the distributed code without them.

---

## 3. Data availability

> All scores analysed in this study are reported in the manuscript
> (Table `[X]`, Table `[Y]`). The analysed texts are classical Chinese poems in
> the public domain.

If the journal insists on a repository link for data as well, the honest option
is the third of Elsevier's standard choices:

> Data will be made available on request.

Do **not** point a data-availability statement at the software repository: it
does not carry the data.

---

## 4. Three things to check before submitting

- **Look up the journal's own heading names.** Different journals label these
  sections differently — "Software availability" and "Data availability" as two
  labelled sections, or a single "Availability of data and materials". The
  wording above is split so it can be dropped into either shape.
  "Software availability" and "Data availability" as separate, labelled
  sections; the wording above is split so it can be dropped into either.
- **Decide whether the repository link is acceptable during review.** The
  repository is public at https://github.com/fancy61333/GPDI-Analyzer and is
  owned by the account `fancy61333`. A public repository is not anonymous. If
  the target journal runs a masked review, the software section should read
  "available from the authors on reasonable request" until the paper is
  accepted, and the link should be added at proof stage.
- **Check `CITATION.cff` before archiving anything.** Its author block still
  carries a placeholder name. Archiving a release while that placeholder is in
  place would print the wrong author on the public deposit, and once a deposit
  exists it also identifies the authors — the same anonymity question as the
  link above.
