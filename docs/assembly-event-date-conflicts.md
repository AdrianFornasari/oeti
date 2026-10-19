# Event-date ambiguity during assembly

Assembly selects event dates within each signal bucket, after claim grouping.
When multiple candidates at the highest known precision have different
`start`, `end` or `precision` values, it now emits an unknown event date:

```json
{"start": null, "end": null, "precision": "unknown"}
```

It also appends `ASM-EVENT-DATE-01` to the payload's `warnings`. This identifies
an ambiguous single-date representation; it does not assert that the source
claims contradict one another. Inspect the saved source claims to recover their
individual dates. Raw claims, metrics and evidence remain available. Assembly
does not infer a continuous interval or create separate events from this tie.

For example, two claims in one outbreak bucket dated September 3 and September
10 previously selected whichever appeared first. Both input orders now produce
an unknown signal date with the warning. Separate groups retain separate dates.

Comparison is deliberately conservative: overlapping intervals and open versus
closed intervals also warn when their date tuples differ. Identical dates do
not warn. Unknown dates do not compete with known dates. The existing preference
for greater precision remains, including when a less precise date might be
incompatible; that case is outside this change. All-unknown candidates retain
the existing behavior. `reference_period` selection is unchanged.

The warning does not reject the document or repair its claims. This policy does
not establish that a selected date applies to every metric in a mixed bucket,
and it does not guarantee order independence for other signal fields. Regression
tests cover both orders of conflicting dates through assembly, normalization
and semantic hardening, plus metric/evidence preservation and input immutability.
