# Sprint 1C semantic refinement v0.3.4

This patch refines the epidemiological extraction contract after manual review of the first MV Hondius extraction.

## Changes

- `signal_role`: distinguishes `primary_event`, `background_context`, `surveillance_baseline`, and `negative_evidence`.
- `location.role`: distinguishes event/current/exposure/travel/sampling/reporting locations.
- `reference_period`: represents historical and surveillance windows separately from the actual event date.
- Conservative pathogen normalization: broad labels such as `hantavirus` must not be promoted to a specific species/strain/lineage without explicit source evidence.
- Metrics cannot be attributed to a confirmed etiology merely because one confirmed case occurs inside a syndromic cluster.
- Syndromic clusters and etiologically confirmed cases must be emitted as separate signals unless the source explicitly attributes the whole cluster to the same agent.

## Database migration

`20260911160000_signal_semantics_v03.sql` adds `signals.signal_role` and `signals.reference_period`. `signal_locations.location_role` already existed and is now populated from the extractor output.

## Safety rule

Do not persist a re-extraction until its JSON is manually reviewed. First run with `--no-persist`, validate it, and compare it against the source.
