# OETI — Repository Instructions for Coding Agents

## Project identity

OETI stands for:

**One Health Emerging Threats Intelligence**

OETI is a One Health emerging-threat intelligence platform designed to integrate evidence from human health, animal health, environmental surveillance, genomics, scientific literature, and other relevant sources.

The system is intended to:

- ingest source documents;
- preserve provenance;
- extract atomic claims;
- assemble structured signals;
- associate signals with emerging events or threats;
- support transparent human review;
- evaluate system performance against adjudicated corpora.

Scientific traceability and preservation of uncertainty are core system requirements.

---

## Repository boundaries

This repository contains both frontend and backend components.

Before making changes:

1. Determine the current Git branch.
2. Inspect `git status`.
3. Identify which subsystem the requested change belongs to.
4. Modify only the subsystem required by the task unless the user explicitly authorizes cross-cutting changes.

Do not mix unrelated frontend and backend changes in the same implementation.

If the task concerns the sponsor demo, prefer changes under:

`apps/web/src/app/demo/**`

If the task concerns extraction, signal assembly, evaluation, event matching, ingestion, or worker behavior, identify the relevant backend location before editing.

---

## Git discipline

Treat the checked-out branch and current working tree as authoritative.

Before editing:

```bash
git branch --show-current
git status
```

Do not:

- switch branches without a task-related reason;
- overwrite unrelated uncommitted work;
- delete or reset user changes;
- force-push;
- rebase shared branches;
- merge branches automatically;
- push to `main` without explicit user approval.

When a task is complete:

1. show the files changed;
2. summarize the behavior changed;
3. report validation actually performed;
4. report any validation that could not be performed;
5. keep unrelated changes untouched.

Never claim a test or build passed unless it was actually run successfully.

---

## Scientific integrity rules

These rules are mandatory.

### Provenance

Every epidemiological or scientific assertion derived from a source must remain traceable to its source document or evidence object.

Do not discard provenance for convenience.

### Dates

Do not substitute publication date for event date.

Keep distinct when available:

- publication date;
- notification date;
- observation date;
- sampling date;
- event start/end dates.

Unknown event dates must remain unknown.

### Geography

Do not infer infection origin from:

- current patient location;
- current vessel location;
- laboratory location;
- publication location;
- travel history alone.

Do not invent coordinates.

Geographic precision must reflect the source evidence.

### Causality

Do not infer causality from association.

Examples:

- genomic relatedness does not establish geographic origin;
- travel history does not establish exposure location;
- detection of a pathogen in wildlife does not establish outbreak source;
- temporal association does not establish transmission.

Preserve explicit distinctions such as:

- confirmed;
- probable;
- possible;
- uncertain;
- refuted;
- negative evidence.

### Negative evidence

Negative, refuted, inconclusive, and contradictory evidence must not be silently discarded.

They are first-class evidence objects when epidemiologically relevant.

### One Health

Do not manufacture evidence to satisfy One Health coverage.

A case may legitimately lack evidence from one or more domains.

Do not create arbitrary One Health scores unless a formally defined and validated scoring model exists.

---

## Human review

Machine-generated findings and analyst decisions are distinct layers.

Human review may:

- confirm;
- correct;
- reject;
- annotate

a machine-generated result.

Human review must not erase:

- original source evidence;
- original extracted claim;
- original machine output;
- provenance.

A rejected signal may still remain auditable.

Confirmation of a signal does not automatically confirm causality.

---

## Evaluation discipline

Evaluation metrics describe system performance, not epidemiological severity.

Keep separate:

- corpus coverage;
- signal precision;
- signal recall;
- signal F1;
- evidence exact/support metrics;
- signal role accuracy;
- signal type accuracy;
- false positives;
- false negatives;
- release/readiness gates.

Do not reinterpret a coverage metric as model accuracy.

Do not change evaluation thresholds merely to make a benchmark pass.

Gold-standard or adjudicated-corpus changes must be deliberate and traceable.

Do not modify expected labels to accommodate current model output unless the underlying adjudication itself has changed.

---

## Benchmark and corpus integrity

The MV Hondius case is an adjudicated evaluation corpus.

Case code:

`ARG-HANTA-MV-HONDIUS-2026`

When working with this corpus:

- preserve adjudicated source facts;
- preserve negative and uncertain evidence;
- do not introduce unsupported epidemiological claims;
- do not silently change benchmark definitions;
- distinguish benchmark-version changes from application-code changes.

If metrics change, identify whether the cause is:

- extraction logic;
- signal assembly;
- evidence matching;
- scoring;
- corpus/gold-standard changes;
- evaluation implementation.

---

## Frontend versus backend truth

The frontend must not invent backend state.

When displaying benchmark or evaluation results:

- use actual stored evaluation results when available;
- clearly identify frozen/demo snapshots;
- do not present illustrative data as live operational data;
- clearly distinguish real adjudicated case data from illustrative interface data.

Frontend wording must not overstate system readiness.

---

## Sponsor demo

The sponsor demo is intended to communicate the OETI concept while remaining scientifically defensible.

The demo should communicate the pipeline:

`Sources → Documents → Atomic Claims → Deterministic Signal Assembly → Signals → Events/Threats → Human Review / Evaluation`

Sponsor-facing language should be understandable without unnecessary implementation jargon.

Technical terminology is appropriate where it conveys an important methodological distinction.

Do not simplify language in a way that changes scientific meaning.

---

## Validation

Run the narrowest relevant validation first.

For frontend work, identify the package scripts before assuming commands.

Known frontend validation includes:

```bash
npm run build:web
```

For presentation/testing after a successful build:

```bash
npm --workspace apps/web run start -- --hostname 0.0.0.0
```

Do not use successful localhost rendering as the only validation when a feature is intended for LAN/mobile presentation.

For backend changes, use the tests applicable to the changed subsystem.

Do not broaden the test scope unnecessarily unless the change is cross-cutting.

---

## Dependencies and configuration

Do not upgrade dependencies, framework versions, lockfiles, infrastructure, database schema, or deployment configuration merely because newer versions exist.

Such changes require an explicit task or a demonstrated technical need.

Keep dependency upgrades separate from feature work whenever practical.

Never expose credentials, API keys, service-role keys, tokens, or secrets.

---

## Scope control

For small changes, make the smallest coherent implementation.

For substantial features, architectural changes, migrations, or work expected to span multiple subsystems, provide a concise implementation plan before editing.

Do not create speculative abstractions for hypothetical future requirements.

Prefer existing project conventions over introducing new architectural patterns.

---

## Source of truth priority

When sources disagree, use this priority:

1. Current checked-out code and tests.
2. Current formal evaluation/corpus files.
3. Current repository documentation.
4. Explicit user instructions for the current task.
5. Historical notes or prior conversations.

Do not treat historical implementation notes as proof of current repository state.

---

## Completion report

At the end of an implementation task, report:

- branch worked on;
- files changed;
- important implementation decisions;
- tests/builds executed;
- results;
- remaining risks or known limitations.

Be explicit about anything not verified.