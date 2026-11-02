-- Explicit document-level extraction snapshots. No historical run is promoted.
begin;

alter table public.extraction_runs
  add column snapshot_policy text check (snapshot_policy is null or snapshot_policy = 'document-v1');
create unique index extraction_runs_document_id_idx on public.extraction_runs(raw_item_id, id);

create table public.extraction_snapshot_heads (
  raw_item_id uuid primary key references public.raw_items(id) on delete restrict,
  run_id uuid not null,
  revision bigint not null check (revision > 0),
  foreign key (raw_item_id, run_id) references public.extraction_runs(raw_item_id, id) on delete restrict
);

create table public.extraction_snapshot_promotions (
  raw_item_id uuid not null references public.raw_items(id) on delete restrict,
  revision bigint not null check (revision > 0),
  previous_run_id uuid,
  run_id uuid not null,
  actor text not null check (length(btrim(actor)) > 0),
  reason text not null check (length(btrim(reason)) > 0),
  promoted_at timestamptz not null default now(),
  primary key (raw_item_id, revision),
  unique (run_id),
  foreign key (raw_item_id, run_id) references public.extraction_runs(raw_item_id, id) on delete restrict,
  foreign key (raw_item_id, previous_run_id) references public.extraction_runs(raw_item_id, id) on delete restrict
);

alter table public.extraction_snapshot_heads enable row level security;
alter table public.extraction_snapshot_promotions enable row level security;
revoke all on public.extraction_snapshot_heads, public.extraction_snapshot_promotions from public, anon, authenticated, service_role;
grant select, insert, update on public.extraction_snapshot_heads to service_role;
grant select, insert on public.extraction_snapshot_promotions to service_role;
commit;
