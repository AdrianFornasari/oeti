# Qualitative surveillance baselines

The v0.4.5 preparation layer suppresses an unquantified negative
`surveillance_baseline` only when its structured `reference_period.period_type`
is `historical_period`. The v0.4.6 assembler delegates to that layer and inherits
the same guard.

Negative baselines with `season`, `surveillance_period`, `observation_window`, or
`unknown` periods remain canonical signals with their baseline role and no
invented numeric metric. Retaining an unknown or seasonal period does not mean
that the observation is current. The guard uses the supplied period type; it
does not infer chronology from wording or correct an incorrectly typed claim.

Explicit numeric zero remains a reported metric and is not suppressed by this
qualitative guard. Negative `case_status` claims retain their existing
`negative_evidence` behavior. No change is made to diagnostic classification,
grouping, or operational-context filtering.

This distinction matters when an absence and a positive count share a group.
The absence must not disappear solely because it was represented as a
nonhistorical baseline. Its absence of a numeric metric must not become a
synthetic zero. Original atomic claims remain unchanged and auditable.

Schema and literal-evidence validation alone cannot detect a dropped qualitative
fact. Regression tests in `test_qualitative_baseline_guard.py` check retention
through assembly, normalization, and semantic hardening, historical suppression,
explicit zero, shared groups, and input immutability for both assembly versions.

This guard does not validate whether a source supports a period label or a
baseline role. It does not address evidence that omits an anaphoric antecedent,
nor does it establish extraction quality or authorize prompt activation.
