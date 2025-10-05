# Repository Guidelines

## Project Structure & Module Organization
- Store the source chapter `Chapter*.md` at the project root; keep the original untouched for citation checks.
- Draft slide source files under `slides/` as numbered Markdown (`01_intro.md`, `02_encoding.md`) aligned with the lesson agenda.
- Capture bilingual speaking notes in `notes/` (`note-encoding-zh.md`) and map each to its slide filename for fast rehearsal.
- Keep supporting graphics and Mermaid specs in `assets/` and `diagrams/`; export presenter-ready images into `slides/img/`.

## Content Assembly Workflow
- Build every deck chunk as plain Markdown plus Mermaid so it can be pasted into Gamma without conversion steps.
- Gamma currently limits exports to 10 pages; group closely related subsections into separate files (`slides/03_lineups.md`) so each upload stays under the cap.
- Within each file, label Gamma page breaks using `---` and include a front-matter comment noting the target section (`<!-- Gamma: Perception Stage -->`).
- Preview Markdown locally with your editor or a lightweight viewer to confirm structure and cues before sharing drafts.
- For Mermaid diagrams, copy the `.mmd` source from `diagrams/` into the online editor at https://mermaid.live/edit to generate images for Gamma.

## Output Packaging Checklist
- Ensure `slides/` holds all session chunks (<=10 pages each) and that matching `notes/` files provide Traditional Chinese talking points with preserved English terms.
- Save diagram sources in `diagrams/` and export any required SVG or PNG copies into `assets/` or `slides/img/` prior to delivery.
- Refresh the interactive guide: rebuild `指引.html` (segment list with open links and copyable textareas) so it reflects the latest content.
- Bundle the Markdown, notes, diagrams, and guidance files together when handing off so classmates can study directly from the package.

## Content Coverage & Storycraft
- Ensure the deck itself delivers the learning: weave definitions, landmark experiments, procedural flow, and origin stories directly onto slides.
- Highlight pivotal terms in English with Traditional Chinese glosses; add one-sentence context cues so classmates can follow without rereading the chapter.
- Use synthesis slides (timelines, mind maps, flow charts) to connect perception, encoding, storage, and retrieval concepts at a glance.
- Close each section with a recap card listing key questions and references for self-study.

## Coding Style & Naming Conventions
- Write Markdown with 2-space indents, wrap prose near 100 characters, and keep heading levels sequential (`#`, `##`, `###`).
- Lead slide bullets with the English keyword and follow with the Traditional Chinese explanation in parentheses.
- Prefer active voice and short sentences on slides; move longer elaborations to the speaking notes.
- Name Mermaid files in kebab case that captures the concept (`memory-encoding-flow.mmd`).

## Testing & Review Guidelines
- Treat CLI warnings or missing assets as blockers; fix broken Mermaid renders or missing notes before reviews.
- Proofread speaking notes for terminology accuracy and append citation anchors in chapter style (e.g., `(Wells & Olson, 2003)`).
- Rehearse timing: each slide should support 2-3 minutes of narration; note cues in brackets (`[1:30]`).

## Commit & Pull Request Guidelines
- Use imperative commit titles such as `Draft encoding slides` and include scope tags (`slides`, `notes`).
- Log major visuals, tool versions, and rehearsal feedback in the commit body; reference tasks with `Refs #ticket` when relevant.
- PRs must attach the updated Markdown bundle, list sections needing peer focus, and flag pending translations or assets.

## Accessibility & Delivery Tips
- Ensure color contrast meets WCAG AA; favor dark text on light backgrounds for classroom projection.
- Embed alt text and add Taiwanese Mandarin pronunciation cues where useful to support classmates with limited English proficiency.
