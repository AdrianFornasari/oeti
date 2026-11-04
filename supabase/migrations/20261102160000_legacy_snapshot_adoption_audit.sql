-- Adoption of an unchanged legacy baseline is distinct from promotion.
begin;
alter table public.extraction_snapshot_promotions
  add column operation text not null default 'candidate_promotion'
    check (operation in ('candidate_promotion', 'legacy_adoption')),
  add column baseline_state_sha256 text,
  add constraint snapshot_adoption_state_required check (
    (operation = 'candidate_promotion' and baseline_state_sha256 is null)
    or (operation = 'legacy_adoption' and baseline_state_sha256 is not null
        and baseline_state_sha256 ~ '^[0-9a-f]{64}$')
  );
commit;
