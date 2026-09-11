-- OETI Sprint 1C semantic refinement v0.3
-- Separates current event facts from context, adds explicit reference periods,
-- and persists semantic location roles already supported by signal_locations.

create type public.signal_role as enum (
  'primary_event',
  'background_context',
  'surveillance_baseline',
  'negative_evidence'
);

alter table public.signals
  add column signal_role public.signal_role not null default 'primary_event',
  add column reference_period jsonb not null default '{}'::jsonb;

create index signals_role_current_idx
  on public.signals(signal_role, is_current, created_at desc);

comment on column public.signals.signal_role is
  'Semantic role of the atomic signal relative to the investigated event: primary event, contextual background, surveillance baseline or negative evidence.';

comment on column public.signals.reference_period is
  'Structured temporal context (season/historical/surveillance window) kept separate from occurred_start/occurred_end to avoid fabricated date precision.';
