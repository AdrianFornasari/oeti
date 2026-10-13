-- OETI v0.4.9
-- Persist provider-reported token usage for extraction runs.
-- Historical/manual runs remain NULL when usage is unavailable.

begin;

alter table public.extraction_runs
  add column input_tokens bigint,
  add column cached_input_tokens bigint,
  add column output_tokens bigint,
  add column reasoning_tokens bigint,
  add column total_tokens bigint;

alter table public.extraction_runs
  add constraint extraction_runs_input_tokens_nonnegative
    check (input_tokens is null or input_tokens >= 0),
  add constraint extraction_runs_cached_input_tokens_nonnegative
    check (cached_input_tokens is null or cached_input_tokens >= 0),
  add constraint extraction_runs_output_tokens_nonnegative
    check (output_tokens is null or output_tokens >= 0),
  add constraint extraction_runs_reasoning_tokens_nonnegative
    check (reasoning_tokens is null or reasoning_tokens >= 0),
  add constraint extraction_runs_total_tokens_nonnegative
    check (total_tokens is null or total_tokens >= 0);

commit;
