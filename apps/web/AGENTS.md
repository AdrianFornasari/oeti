# OETI Web / Sponsor Demo Instructions

These instructions apply to work under `apps/web`.

Also follow the repository-level `AGENTS.md`.

## Scope

The OETI web application contains the sponsor-facing demonstration interface.

The current sponsor demo is primarily located under:

`apps/web/src/app/demo/**`

When a task concerns the sponsor demo, keep changes inside that directory unless another file is genuinely required.

Do not modify backend extraction, worker, benchmark, event-matching, or adjudicated-corpus code from a frontend task unless explicitly authorized.

---

## Sponsor demo goals

The interface must communicate OETI clearly to:

- scientific collaborators;
- One Health stakeholders;
- institutional sponsors;
- non-software audiences.

The application should look operational while clearly distinguishing:

- real adjudicated data;
- frozen benchmark results;
- illustrative interface elements;
- browser-local demo state;
- production/backend state.

Never imply that browser-local demo actions modify production data.

---

## Scientific wording

Frontend simplification must preserve scientific meaning.

Avoid language implying unsupported:

- causality;
- geographic origin;
- transmission route;
- exposure;
- certainty.

Use explicit wording for:

- probable;
- uncertain;
- inconclusive;
- negative;
- refuted;
- confirmed.

Do not convert evidence relationships into causal statements.

---

## MV Hondius demo

The principal demonstration case is:

`ARG-HANTA-MV-HONDIUS-2026`

The sponsor demo currently includes:

- Dashboard;
- Threat Explorer;
- One Health convergence;
- Signal Detail;
- Evidence Traceability;
- Analyst Review;
- System Evaluation;
- Guided Presentation Mode.

Preserve navigability between these views.

---

## Human review UI

Analyst review must remain visibly separate from machine output.

When showing analyst decisions:

- preserve the original machine proposal;
- preserve source evidence;
- preserve claims;
- show review state separately;
- make clear that confirmation does not establish causality.

Demo-only review state may be stored locally in the browser but must be identified as demo/browser state.

---

## Preferences

The sponsor demo supports:

- Spanish and English;
- light and dark themes;
- font-size controls.

Spanish is the default unless a saved browser preference exists.

Preferences should persist locally where currently implemented.

Changes to one preference must not break the others.

When modifying the top bar or shell, verify:

- desktop;
- tablet;
- mobile;
- localhost access;
- LAN access where practical.

---

## Responsive behavior

The sponsor demo is expected to work on:

- desktop browsers;
- tablets;
- smartphones.

Do not optimize desktop at the expense of mobile navigation.

Avoid fixed widths that cause horizontal overflow.

Interactive controls must remain usable on touch devices.

---

## Styling

Reuse the existing demo style system before creating new styling mechanisms.

Relevant files currently include:

- `demo.module.css`
- `demo-mobile.module.css`
- `demo-responsive.css`

Avoid unnecessary global CSS changes.

Do not redesign unrelated screens as part of a focused change.

---

## Language support

Any new sponsor-visible text should have both:

- Spanish;
- English

unless the task explicitly says otherwise.

Do not add English-only controls to an otherwise bilingual screen.

---

## Evaluation screen

Metrics displayed in the UI must come from a defined benchmark/evaluation snapshot.

Never invent improved values.

When evaluation data is frozen at an older backend version, identify it as a frozen snapshot rather than silently presenting it as the current backend result.

A benchmark update should be treated separately from a purely visual frontend change.

---

## Validation

After meaningful frontend changes, run:

```bash
npm run build:web
```

A successful development render alone is insufficient evidence of a valid production build.

For LAN/mobile presentation testing, prefer after build:

```bash
npm --workspace apps/web run start -- --hostname 0.0.0.0
```

because the sponsor demo must work outside `localhost`.

When modifying interactive controls, verify that client-side hydration and interaction work, not merely that the HTML renders.

---

## Change reporting

At completion report:

- changed files;
- visible behavior changed;
- build result;
- device/responsive implications;
- whether LAN/mobile interaction was actually verified.

Do not claim device validation unless it was actually performed.