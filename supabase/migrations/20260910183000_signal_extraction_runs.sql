-- OETI Sprint 1C
-- Adds auditable extraction runs and links atomic signals to the run that produced them.

begin;

create table public.extraction_runs (
  id uuid primary key default gen_random_uuid(),
  raw_item_id uuid not null references public.raw_items(id) on delete cascade,
  schema_version text not null,
  extractor_version text not null,
  prompt_version text not null,
  provider text not null,
  model_name text not null,
  status text not null check (status in ('succeeded', 'failed')),
  response_id text,
  input_char_count integer not null default 0 check (input_char_count >= 0),
  output_json jsonb,
  warnings jsonb not null default '[]'::jsonb,
  error_text text,
  created_at timestamptz not null default now(),
  constraint extraction_runs_success_has_output check (
    status <> 'succeeded' or output_json is not null
  ),
  constraint extraction_runs_failure_has_error check (
    status <> 'failed' or error_text is not null
  )
);

create index extraction_runs_raw_item_created_idx
  on public.extraction_runs(raw_item_id, created_at desc);

create index extraction_runs_status_idx
  on public.extraction_runs(status, created_at desc);

alter table public.signals
  add column extraction_run_id uuid references public.extraction_runs(id) on delete restrict;

create index signals_extraction_run_idx on public.signals(extraction_run_id);

alter table public.extraction_runs enable row level security;

revoke all on table public.extraction_runs from anon, authenticated;
grant all on table public.extraction_runs to service_role;

-- Intentionally no client policy/grant: extraction output and model metadata remain server-side.

commit;
