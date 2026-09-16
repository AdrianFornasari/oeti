-- OETI v0.3.5 hotfix
-- Keep PostgreSQL signal_type aligned with signal-extractor-v0.4 schema.
-- Additive migration: do not edit already-applied migrations.

alter type public.signal_type
  add value if not exists 'laboratory_investigation';
