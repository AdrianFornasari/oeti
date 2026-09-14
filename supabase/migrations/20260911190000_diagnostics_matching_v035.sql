-- OETI v0.3.5 - diagnostics separated from genomics and event-matching eligibility

alter type public.test_result add value if not exists 'pending';

alter table public.signals
  add column event_matching_eligible boolean not null default true;

update public.signals
set event_matching_eligible = false
where signal_type = 'official_alert'
   or signal_role in ('background_context', 'surveillance_baseline');

create index signals_event_matching_idx
  on public.signals(event_matching_eligible, is_current, created_at desc);

create table public.diagnostic_observations (
  id uuid primary key default gen_random_uuid(),
  signal_id uuid not null references public.signals(id) on delete cascade,
  pathogen_id uuid references public.pathogens(id) on delete set null,
  test_reported boolean not null default false,
  test_type text,
  test_method text,
  target text,
  specimen text,
  test_result public.test_result not null default 'unknown',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index diagnostic_observations_signal_idx
  on public.diagnostic_observations(signal_id, test_result);

alter table public.diagnostic_observations enable row level security;

revoke all on table public.diagnostic_observations from anon, authenticated;
grant select on table public.diagnostic_observations to authenticated;
grant all on table public.diagnostic_observations to service_role;

create policy diagnostic_observations_authenticated_read
  on public.diagnostic_observations for select to authenticated using (true);

comment on table public.diagnostic_observations is
  'Diagnostic/laboratory testing observations kept separate from genomic sequencing and lineage evidence.';

comment on column public.signals.event_matching_eligible is
  'Deterministic gate for future automatic event matching. Administrative alerts and contextual baselines are excluded.';
