# Negative case-status isolation

A `case_status` claim with explicit `polarity="negative"` uses a separate
assembly bucket from positive case, outbreak and death-count claims, even when
the provider assigns the same `group_id`. A single negative case-status claim
produces a `case_report` with role `negative_evidence`.

For example, three probable cases and no confirmed cases can both be true.
Assembly preserves these as separate signals rather than placing the absence
of confirmed cases inside the positive signal. Metrics and supporting evidence
stay with their respective claims. The raw provider response is not modified.

Routing depends on declared polarity, not a numeric zero, metric presence or
text matching. It does not verify that the provider classified the source
correctly. It also does not convert a derived zero into a source-reported zero,
repair dates or restore omitted facts. Positive and uncertain case-status
claims retain their previous behavior. Negative death counts retain their
existing grouping because the absence of deaths can contextualize an outbreak.

Repeated negative case-status claims in the same group still consolidate under
the existing rules; their resulting signal type may be `outbreak` for multiple
claims. Negative outbreak updates retain their separate existing bucket. This
change isolates polarities without redesigning general signal types or roles.

Regression coverage exercises both claim orders across assembly versions and
the current normalization/semantic-hardening sequence, including input
immutability, metric/evidence preservation and metric-free negative claims.
