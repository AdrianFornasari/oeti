-- One Health Emerging Threat Intelligence
-- Initial core schema v0.1 - Argentina-first MVP

begin;

create extension if not exists pgcrypto;
create schema if not exists gis;
create extension if not exists postgis with schema gis;

-- -----------------------------
-- ENUMS
-- -----------------------------
create type public.source_kind as enum (
  'primary_official', 'international_official', 'peer_reviewed',
  'expert_moderated', 'scientific_preprint', 'professional_media',
  'general_media', 'open_source', 'unknown'
);

create type public.ingestion_method as enum ('api', 'rss', 'html', 'pdf', 'dataset', 'manual', 'other');
create type public.processing_status as enum ('queued', 'processed', 'failed', 'ignored');
create type public.one_health_domain as enum (
  'human', 'animal', 'wildlife', 'vector', 'environment',
  'genomic', 'food', 'amr', 'mobility'
);
create type public.host_category as enum ('human', 'domestic_animal', 'wildlife', 'vector', 'other');
create type public.signal_type as enum (
  'case_report', 'cluster', 'outbreak', 'pathogen_detection',
  'animal_event', 'wildlife_event', 'vector_event', 'environmental_signal',
  'genomic_observation', 'mortality_event', 'transmission_observation',
  'laboratory_result', 'official_alert', 'intervention',
  'travel_or_mobility', 'other'
);
create type public.verification_status as enum ('confirmed', 'probable', 'suspected', 'reported', 'refuted', 'unknown');
create type public.review_status as enum ('pending', 'in_review', 'reviewed', 'rejected');
create type public.normalization_status as enum ('resolved', 'ambiguous', 'unresolved');
create type public.location_precision as enum ('country', 'admin1', 'admin2', 'locality', 'point', 'region', 'unknown');
create type public.event_lifecycle_status as enum ('active', 'monitoring', 'resolved', 'closed');
create type public.event_priority as enum ('P1', 'P2', 'P3', 'P4');
create type public.evidence_confidence as enum ('low', 'medium', 'high');
create type public.cross_sector_convergence as enum ('none', 'low', 'moderate', 'high');
create type public.relation_type as enum ('supports', 'duplicates', 'refines', 'contradicts', 'possibly_related', 'unrelated', 'unknown');
create type public.match_decision as enum ('auto_linked', 'review_required', 'rejected', 'manual_linked', 'manual_unlinked');
create type public.test_result as enum ('positive', 'negative', 'indeterminate', 'not_applicable', 'unknown');

-- -----------------------------
-- SUPPORT FUNCTION
-- -----------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- -----------------------------
-- CATALOGS AND SOURCE MATERIAL
-- -----------------------------
create table public.sources (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  name text not null,
  kind public.source_kind not null,
  ingestion public.ingestion_method not null,
  base_url text,
  country_iso2 char(2),
  is_active boolean not null default true,
  license_notes text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger sources_set_updated_at
before update on public.sources
for each row execute function public.set_updated_at();

create table public.raw_items (
  id uuid primary key default gen_random_uuid(),
  external_id text,
  url text not null,
  title text,
  published_at timestamptz,
  retrieved_at timestamptz not null default now(),
  language text,
  mime_type text,
  content_sha256 text not null,
  processing_status public.processing_status not null default 'queued',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (source_id, content_sha256)
);

create index raw_items_source_published_idx on public.raw_items(source_id, published_at desc);
create index raw_items_processing_idx on public.raw_items(processing_status, retrieved_at);

-- Full source payload is deliberately isolated from browser-readable metadata.
create table public.raw_item_payloads (
  raw_item_id uuid primary key references public.raw_items(id) on delete cascade,
  storage_path text,
  raw_text text,
  processing_error text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger raw_item_payloads_set_updated_at
before update on public.raw_item_payloads
for each row execute function public.set_updated_at();

create table public.diseases (
  id uuid primary key default gen_random_uuid(),
  canonical_name text not null unique,
  synonyms text[] not null default '{}',
  external_ids jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.pathogens (
  id uuid primary key default gen_random_uuid(),
  canonical_name text not null unique,
  pathogen_type text,
  taxonomy_id text,
  synonyms text[] not null default '{}',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.hosts (
  id uuid primary key default gen_random_uuid(),
  scientific_name text,
  common_name text not null,
  host_type public.host_category not null,
  taxonomy_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique nulls not distinct (scientific_name, common_name, host_type)
);

create table public.locations (
  id uuid primary key default gen_random_uuid(),
  display_name text not null,
  country_iso2 char(2),
  country_name text,
  admin1 text,
  admin2 text,
  locality text,
  region_name text,
  precision public.location_precision not null default 'unknown',
  point gis.geography(point, 4326),
  indec_code text,
  geonames_id text,
  normalization_status public.normalization_status not null default 'unresolved',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index locations_point_gix on public.locations using gist(point);
create index locations_argentina_admin_idx on public.locations(country_iso2, admin1, admin2, locality);

-- -----------------------------
-- ATOMIC SIGNALS
-- -----------------------------
create table public.signals (
  id uuid primary key default gen_random_uuid(),
  schema_version text not null default '0.1',
  raw_item_id uuid not null references public.raw_items(id) on delete restrict,
  local_signal_key text not null,
  version integer not null default 1 check (version > 0),
  supersedes_signal_id uuid references public.signals(id) on delete restrict,
  is_current boolean not null default true,
  domains public.one_health_domain[] not null default '{}',
  signal_type public.signal_type not null,
  signal_summary text not null,
  verification_status public.verification_status not null default 'unknown',
  extraction_confidence numeric(4,3) not null check (extraction_confidence between 0 and 1),
  disease_id uuid references public.diseases(id) on delete set null,
  disease_verbatim text,
  disease_confidence numeric(4,3) check (disease_confidence is null or disease_confidence between 0 and 1),
  disease_normalization_status public.normalization_status not null default 'unresolved',
  pathogen_id uuid references public.pathogens(id) on delete set null,
  pathogen_verbatim text,
  pathogen_confidence numeric(4,3) check (pathogen_confidence is null or pathogen_confidence between 0 and 1),
  pathogen_normalization_status public.normalization_status not null default 'unresolved',
  occurred_start date,
  occurred_end date,
  date_precision text,
  transmission jsonb not null default '{}'::jsonb,
  extractor_version text,
  model_name text,
  warnings jsonb not null default '[]'::jsonb,
  review_status public.review_status not null default 'pending',
  reviewed_by uuid references auth.users(id) on delete set null,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  constraint signals_date_order check (occurred_end is null or occurred_start is null or occurred_end >= occurred_start),
  unique (raw_item_id, local_signal_key, version)
);

create index signals_domains_gin on public.signals using gin(domains);
create index signals_current_idx on public.signals(is_current, created_at desc);
create unique index signals_one_current_version_idx on public.signals(raw_item_id, local_signal_key) where is_current;
create index signals_disease_pathogen_idx on public.signals(disease_id, pathogen_id);
create index signals_review_idx on public.signals(review_status, verification_status);

create table public.signal_locations (
  signal_id uuid not null references public.signals(id) on delete cascade,
  location_id uuid not null references public.locations(id) on delete restrict,
  location_role text not null default 'event_location',
  confidence numeric(4,3) check (confidence is null or confidence between 0 and 1),
  primary key (signal_id, location_id, location_role)
);

create table public.signal_hosts (
  signal_id uuid not null references public.signals(id) on delete cascade,
  host_id uuid not null references public.hosts(id) on delete restrict,
  host_role text not null default 'affected',
  count_numeric numeric,
  confidence numeric(4,3) check (confidence is null or confidence between 0 and 1),
  primary key (signal_id, host_id, host_role)
);

create table public.signal_metrics (
  id uuid primary key default gen_random_uuid(),
  signal_id uuid not null references public.signals(id) on delete cascade,
  metric_name text not null,
  value_numeric numeric,
  value_text text,
  unit text,
  population_scope text,
  as_of_date date,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint signal_metrics_has_value check (value_numeric is not null or value_text is not null)
);

create index signal_metrics_signal_name_idx on public.signal_metrics(signal_id, metric_name);

create table public.signal_evidence (
  id uuid primary key default gen_random_uuid(),
  signal_id uuid not null references public.signals(id) on delete cascade,
  evidence_type text not null default 'source_span',
  excerpt text not null,
  document_locator text,
  page_number integer check (page_number is null or page_number > 0),
  char_start integer,
  char_end integer,
  evidence_hash text,
  created_at timestamptz not null default now(),
  constraint signal_evidence_char_order check (char_end is null or char_start is null or char_end >= char_start)
);

create table public.genomic_observations (
  id uuid primary key default gen_random_uuid(),
  signal_id uuid not null references public.signals(id) on delete cascade,
  pathogen_id uuid references public.pathogens(id) on delete set null,
  accession text,
  lineage text,
  clade text,
  sequence_reported boolean not null default false,
  test_result public.test_result not null default 'unknown',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.environmental_observations (
  id uuid primary key default gen_random_uuid(),
  signal_id uuid references public.signals(id) on delete cascade,
  location_id uuid references public.locations(id) on delete restrict,
  variable_name text not null,
  value_numeric numeric,
  value_text text,
  unit text,
  observed_at timestamptz,
  anomaly_value numeric,
  baseline_period text,
  source_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint environmental_observations_has_value check (value_numeric is not null or value_text is not null)
);

-- -----------------------------
-- CONSOLIDATED EVENTS
-- -----------------------------
create table public.events (
  id uuid primary key default gen_random_uuid(),
  event_code text not null unique,
  title text not null,
  disease_id uuid references public.diseases(id) on delete set null,
  pathogen_id uuid references public.pathogens(id) on delete set null,
  domains_present public.one_health_domain[] not null default '{}',
  event_start_date date,
  first_signal_at timestamptz,
  last_update_at timestamptz not null default now(),
  lifecycle_status public.event_lifecycle_status not null default 'active',
  priority public.event_priority not null default 'P3',
  evidence_confidence public.evidence_confidence not null default 'low',
  cross_sector_convergence public.cross_sector_convergence not null default 'none',
  summary text,
  contradictions_present boolean not null default false,
  review_status public.review_status not null default 'pending',
  reviewed_by uuid references auth.users(id) on delete set null,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger events_set_updated_at
before update on public.events
for each row execute function public.set_updated_at();

create index events_priority_active_idx on public.events(lifecycle_status, priority, last_update_at desc);
create index events_domains_gin on public.events using gin(domains_present);

create table public.event_signals (
  event_id uuid not null references public.events(id) on delete cascade,
  signal_id uuid not null references public.signals(id) on delete restrict,
  relation_to_event public.relation_type not null default 'supports',
  match_score numeric(4,3) check (match_score is null or match_score between 0 and 1),
  match_decision public.match_decision not null default 'review_required',
  rationale jsonb not null default '{}'::jsonb,
  linked_by uuid references auth.users(id) on delete set null,
  linked_at timestamptz not null default now(),
  primary key (event_id, signal_id)
);

create index event_signals_signal_idx on public.event_signals(signal_id);

create table public.signal_relations (
  id uuid primary key default gen_random_uuid(),
  source_signal_id uuid not null references public.signals(id) on delete cascade,
  target_signal_id uuid not null references public.signals(id) on delete cascade,
  relation public.relation_type not null,
  score numeric(4,3) check (score is null or score between 0 and 1),
  hard_conflict boolean not null default false,
  rationale jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint signal_relations_not_self check (source_signal_id <> target_signal_id),
  unique (source_signal_id, target_signal_id, relation)
);

create table public.assessments (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references public.events(id) on delete cascade,
  assessment_type text not null,
  priority public.event_priority,
  confidence public.evidence_confidence,
  rationale jsonb not null default '{}'::jsonb,
  assessed_by uuid references auth.users(id) on delete set null,
  supersedes_assessment_id uuid references public.assessments(id) on delete restrict,
  created_at timestamptz not null default now()
);

create index assessments_event_created_idx on public.assessments(event_id, created_at desc);

-- -----------------------------
-- ROW LEVEL SECURITY AND GRANTS
-- Client is read-only. Worker/server uses service_role.
-- -----------------------------

alter table public.sources enable row level security;
alter table public.raw_items enable row level security;
alter table public.raw_item_payloads enable row level security;
alter table public.diseases enable row level security;
alter table public.pathogens enable row level security;
alter table public.hosts enable row level security;
alter table public.locations enable row level security;
alter table public.signals enable row level security;
alter table public.signal_locations enable row level security;
alter table public.signal_hosts enable row level security;
alter table public.signal_metrics enable row level security;
alter table public.signal_evidence enable row level security;
alter table public.genomic_observations enable row level security;
alter table public.environmental_observations enable row level security;
alter table public.events enable row level security;
alter table public.event_signals enable row level security;
alter table public.signal_relations enable row level security;
alter table public.assessments enable row level security;

-- PostGIS type lives in a dedicated schema; read clients need type/schema usage.
grant usage on schema gis to authenticated, service_role;

revoke all on table
  public.sources, public.raw_items, public.raw_item_payloads, public.diseases, public.pathogens, public.hosts,
  public.locations, public.signals, public.signal_locations, public.signal_hosts,
  public.signal_metrics, public.signal_evidence, public.genomic_observations,
  public.environmental_observations, public.events, public.event_signals,
  public.signal_relations, public.assessments
from anon, authenticated;

grant select on table
  public.sources, public.raw_items, public.diseases, public.pathogens, public.hosts, public.locations,
  public.signals, public.signal_locations, public.signal_hosts, public.signal_metrics,
  public.signal_evidence, public.genomic_observations, public.environmental_observations,
  public.events, public.event_signals, public.signal_relations, public.assessments
to authenticated;

grant all on table
  public.sources, public.raw_items, public.raw_item_payloads, public.diseases, public.pathogens, public.hosts,
  public.locations, public.signals, public.signal_locations, public.signal_hosts,
  public.signal_metrics, public.signal_evidence, public.genomic_observations,
  public.environmental_observations, public.events, public.event_signals,
  public.signal_relations, public.assessments
to service_role;

-- Authenticated users may read derived/curated epidemiological data.
create policy sources_authenticated_read on public.sources for select to authenticated using (true);
create policy raw_items_authenticated_read on public.raw_items for select to authenticated using (true);
create policy diseases_authenticated_read on public.diseases for select to authenticated using (true);
create policy pathogens_authenticated_read on public.pathogens for select to authenticated using (true);
create policy hosts_authenticated_read on public.hosts for select to authenticated using (true);
create policy locations_authenticated_read on public.locations for select to authenticated using (true);
create policy signals_authenticated_read on public.signals for select to authenticated using (true);
create policy signal_locations_authenticated_read on public.signal_locations for select to authenticated using (true);
create policy signal_hosts_authenticated_read on public.signal_hosts for select to authenticated using (true);
create policy signal_metrics_authenticated_read on public.signal_metrics for select to authenticated using (true);
create policy signal_evidence_authenticated_read on public.signal_evidence for select to authenticated using (true);
create policy genomic_observations_authenticated_read on public.genomic_observations for select to authenticated using (true);
create policy environmental_observations_authenticated_read on public.environmental_observations for select to authenticated using (true);
create policy events_authenticated_read on public.events for select to authenticated using (true);
create policy event_signals_authenticated_read on public.event_signals for select to authenticated using (true);
create policy signal_relations_authenticated_read on public.signal_relations for select to authenticated using (true);
create policy assessments_authenticated_read on public.assessments for select to authenticated using (true);

-- Intentionally NO client policy/grant for raw_item_payloads (full raw text/storage/error details).

commit;
