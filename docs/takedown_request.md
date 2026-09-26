# Zenodo takedown request — draft

Status of the public surface as of 2026-09-26:

| Channel | State |
|---|---|
| GitHub repository `fancy61333/GPDI-Analyzer` | **private** (was public) — 404 for anonymous access |
| GitHub releases `v1.0.0` / `v1.0.1` + assets | **deleted** |
| Git tags `v1.0.0` / `v1.0.1` | **deleted** |
| Zenodo record `10.5281/zenodo.22973905` (v1.0.1) | **still public — HTTP 200** |
| Zenodo concept DOI `10.5281/zenodo.22973904` | **still public** |

Zenodo records that have been published cannot be deleted from the web
interface. A removal has to be requested from Zenodo support. Send the draft
below to **info@zenodo.org** (CC `support@zenodo.org`). Fill in the two
placeholders marked `[...]` before sending.

---

## Email

**To:** info@zenodo.org
**Subject:** Takedown request — record 10.5281/zenodo.22973905 (and concept DOI 10.5281/zenodo.22973904)

Dear Zenodo support team,

I am the depositor of the record

    10.5281/zenodo.22973905   (GPDI Analyzer v1.0.1)
    10.5281/zenodo.22973904   (concept DOI for the same software)

and I am writing to request the removal of both records, and of the file
archive attached to the version record.

**Reason.** The archive is a source snapshot of a repository that was
published by mistake while it still contained material that is not mine to
redistribute:

1. A 3,500-character graded inventory of Old Chinese characters — an
   unpublished research asset compiled for a manuscript that is currently
   under review. **[state the provenance of the inventory here: who compiled
   it, and on what terms you hold it — e.g. "compiled by my research group
   from [...], not licensed for redistribution"]**
2. The complete scoring specification of the index (metric definitions and
   weights) together with the full per-item result table of the unpublished
   study, which the journal's policy does not permit to be distributed
   ahead of publication.

The GitHub repository and its releases have already been taken down, so the
Zenodo snapshot is now the only remaining public copy. Because the material
in point 1 is third-party / unpublished content that I am not entitled to
publish, I ask you to remove the records rather than to merely edit their
metadata.

If a full removal is not possible under Zenodo's policy for already-minted
DOIs, please at minimum:

- suppress both records from search and from the public landing pages, and
- remove the file archive `fancy61333/GPDI-Analyzer-v1.0.1.zip` from the
  version record.

I am happy to provide any further information you need. My Zenodo account is
linked to the GitHub account `fancy61333`, and the deposit was created on
2026-09-26.

Thank you for your help.

[Your name]
[Your affiliation]
[Date]

---

## After sending

- Zenodo may answer that published DOIs are permanent. If so, ask for the
  fallback (suppression + file removal) rather than arguing the point.
- Also switch off the GitHub integration so nothing can be archived again by
  accident: Zenodo → GitHub → *Settings* → remove the `GPDI-Analyzer` webhook.
- Do not delete the local working copy. Everything still exists under
  `D:\app\wampsever\GPDI-Analyzer`; only the public copies were removed.

## If the software is ever made public again

Do not re-open this repository — its history still contains `core/gpdi.py`,
`data/corpus_frozen.csv` and `data/poems_82_text.csv`. Create a **new**
repository containing only a README (the pattern used by
`corpustalk/AlphaLexChinese`), and never commit the inventory. If a binary
build has to be distributed again, remember that the inventory travels inside
it and can be recovered from `char_inventory.bin` with four lines of Python,
so a public build and a confidential inventory are mutually exclusive unless
the scoring runs server-side.
