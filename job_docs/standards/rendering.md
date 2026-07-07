# Rendering — from markdown to a submittable file

**Markdown is the deliverable by default.** `cv.md` and `cover.md` are the reviewed, verified source of truth; a rendered file is a *view* of them, produced only when the user asks (or a portal demands an upload). Never edit content at the rendering stage — content changes go into the `.md` and re-verify.

## Options, in order of preference

| Option                                   | When                                                                                                                          | Notes                                                                                                                              |
| :--------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------- |
| **`pdf` skill** (if available)           | Default render path for single-column documents                                                                               | Clean Markdown → PDF; satisfies every `ats_rules.md` format constraint by construction                                             |
| **`pandoc`** (if on the system)          | Same, without the skill                                                                                                       | `pandoc cv.md -o CV_<Name>_<Company>.pdf` (add `--pdf-engine=xelatex` for non-Latin text); `-o .docx` for portals that demand Word |
| **`docx` skill**                         | Portal requires Word format                                                                                                   | Same single-column content                                                                                                         |
| **External CV builder** (e.g. rxresu.me) | User wants a designed, two-column, photo layout — commonly for DACH-market applications (see `standards/dach_conventions.md`) | Manual step: produce a **transfer block** (below), the user pastes it into the builder and exports                                 |

## The transfer block (external-builder path)

When the user chooses a builder, output the verified `cv.md` content restructured as a copy-paste block matching the builder's sections (basics / summary / experience / education / skills / languages), so the transfer is mechanical and nothing gets rewritten in transit. The trace file still governs the content — what goes into the builder is exactly what was verified.

## After any render

1. **Spot-check the artifact:** selectable text layer (not an image), no clipped sections, dates intact, umlauts/diacritics correct.
2. **Filename:** `CV_<Name>_<Company>.pdf` / `CoverLetter_<Name>_<Company>.pdf` — some portals index it.
3. **Designed layouts trade ATS safety for human appeal** — that's a deliberate user choice per `ats_rules.md`. For a designed CV going to a large company, suggest a quick run through a free ATS-parse checker before submission; for markdown-derived single-column renders this is unnecessary.
