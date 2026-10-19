# Evaluation-only metric-period candidates

`evaluation.metric_period_provenance.build_metric_period_provenance` returns
canonical UTF-8 JSON bytes for a pair of claims/signals artifacts. It performs
no filesystem, network or database operations and is not connected to the
active extractor. The caller supplies both artifact byte strings, their trusted
expected SHA-256 hashes, expected document metadata and the canonical schemas.
No production schema or stored predictions are changed.

The builder validates hashes, strict JSON, both schemas and exact document
binding, including for empty artifacts. Duplicate JSON keys, non-finite numbers,
blank/duplicate claim or signal identifiers and external schema references are
rejected with a redacted `MetricProvenanceError`. Schemas must use local fragment
references. The caller must obtain hashes and schemas from a trusted source;
hashes supplied by an untrusted response do not establish authenticity.

For each signal metric, the result records its JSON pointer and every reported
claim metric that is exactly equal after removing the claim-only `reported`
field. Equality includes all cutoff fields and is deliberately strict about
numeric serialization, text and units; normalization can therefore produce an
unmatched metric. Candidate claim records retain their IDs, group IDs, pointers,
`reference_period`, `event_date` and evidence. Correspondence states are:

- `unique_metric_match`: one exact candidate across the document.
- `ambiguous_metric_match`: all exact candidates are retained; none is selected.
- `unmatched`: no exact candidate, including derived or normalized metrics.

An exact match does not prove that a claim belongs to the signal's assembly
group, that its period is correct or that its evidence is literal. Candidate
search intentionally spans all claims in the bound document; multiple groups
may contain the same metric. The output explicitly leaves group membership,
source literalness and semantic correctness unverified. It applies no decisions.
Qualitative claims without reported metrics are outside this numeric map and
remain available in the original claims artifact.

This preserves evaluation access to different per-claim periods when a signal
can store only one `reference_period`. It does not fix the canonical signal or
justify splitting metrics into independent events. The output version is
`metric-period-provenance-1`; it is a derived candidate map, not a model response
or independent gold. Manual adjudication artifacts remain manual after mapping.

File publication is intentionally left to the evaluation caller. Before writing,
that caller must enforce its allowed root and create a new output exclusively,
without overwriting either input. There is no new CLI or automatic export in
this change. The current evaluation runner and production prompt are unchanged.
