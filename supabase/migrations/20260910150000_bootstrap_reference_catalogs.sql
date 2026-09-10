-- OETI Sprint 1B
-- Reference catalogs required by the first Argentina-first ingestion pipeline.
-- This is a production-safe data migration: idempotent inserts, no destructive changes.

begin;

insert into public.sources (
  code, name, kind, ingestion, base_url, country_iso2, license_notes, metadata
) values
  (
    'ARG_MSAL_NEWS',
    'Ministerio de Salud de la Nación - Noticias',
    'primary_official',
    'html',
    'https://www.argentina.gob.ar/salud/noticias',
    'AR',
    'Conservar URL, metadatos, hash y evidencia breve. Revisar condiciones de reutilización antes de redistribuir texto completo.',
    '{"publisher":"Ministerio de Salud de la Nación","jurisdiction":"national","priority":1}'::jsonb
  ),
  (
    'ARG_MSAL_BEN',
    'Boletín Epidemiológico Nacional - Ministerio de Salud',
    'primary_official',
    'pdf',
    'https://www.argentina.gob.ar/salud/boletin-epidemiologico-nacional',
    'AR',
    'Fuente oficial nacional. Persistir metadatos, hash y evidencia necesaria; conservar referencia al documento original.',
    '{"publisher":"Ministerio de Salud de la Nación","jurisdiction":"national","priority":1}'::jsonb
  ),
  (
    'ARG_MSAL_COMMS',
    'Comunicaciones Epidemiológicas - Ministerio de Salud',
    'primary_official',
    'html',
    'https://www.argentina.gob.ar/salud/boletin-epidemiologico-nacional/comunicaciones-epidemiologicas',
    'AR',
    'Fuente oficial prioritaria para alertas nacionales.',
    '{"publisher":"Ministerio de Salud de la Nación","jurisdiction":"national","priority":1}'::jsonb
  ),
  (
    'ARG_ANLIS_NEWS',
    'ANLIS-Malbrán - Noticias',
    'primary_official',
    'html',
    'https://www.argentina.gob.ar/salud/anlis/novedades',
    'AR',
    'Laboratorio nacional de referencia, investigación de brotes y vigilancia genómica.',
    '{"publisher":"ANLIS-Malbrán","jurisdiction":"national","priority":1,"domains":["human","wildlife","genomic"]}'::jsonb
  ),
  (
    'ARG_SENASA',
    'SENASA - Sanidad Animal',
    'primary_official',
    'html',
    'https://www.argentina.gob.ar/senasa',
    'AR',
    'Sanidad animal, producción y fauna. Automatización por endpoint a validar caso por caso.',
    '{"publisher":"SENASA","jurisdiction":"national","priority":1,"domains":["animal","wildlife"]}'::jsonb
  ),
  (
    'ARG_SMN',
    'Servicio Meteorológico Nacional',
    'primary_official',
    'dataset',
    'https://www.smn.gob.ar/',
    'AR',
    'Variables meteorológicas y ambientales.',
    '{"publisher":"SMN","jurisdiction":"national","priority":2,"domains":["environment"]}'::jsonb
  ),
  (
    'PAHO',
    'Organización Panamericana de la Salud',
    'international_official',
    'html',
    'https://www.paho.org/',
    null,
    'Contexto regional y alertas de las Américas.',
    '{"priority":2}'::jsonb
  ),
  (
    'WHO_DON',
    'WHO Disease Outbreak News',
    'international_official',
    'html',
    'https://www.who.int/emergencies/disease-outbreak-news',
    null,
    'Confirmación y contexto internacional.',
    '{"priority":2}'::jsonb
  ),
  (
    'WOAH_WAHIS',
    'WOAH WAHIS',
    'international_official',
    'dataset',
    'https://wahis.woah.org/',
    null,
    'Sanidad animal internacional; verificar modalidad técnica y condiciones antes de automatizar.',
    '{"priority":2,"domains":["animal","wildlife"]}'::jsonb
  )
on conflict (code) do update set
  name = excluded.name,
  kind = excluded.kind,
  ingestion = excluded.ingestion,
  base_url = excluded.base_url,
  country_iso2 = excluded.country_iso2,
  license_notes = excluded.license_notes,
  metadata = public.sources.metadata || excluded.metadata,
  is_active = true,
  updated_at = now();

insert into public.diseases (canonical_name, synonyms, metadata) values
  ('Hantavirus pulmonary syndrome', array['síndrome pulmonar por hantavirus','SPH'], '{"mvp":true}'::jsonb),
  ('Avian influenza A(H5N1)', array['influenza aviar H5N1','IAAP H5N1'], '{"mvp":true}'::jsonb),
  ('Chikungunya', array['fiebre chikungunya'], '{"mvp":true}'::jsonb)
on conflict (canonical_name) do update set
  synonyms = excluded.synonyms,
  metadata = public.diseases.metadata || excluded.metadata;

insert into public.pathogens (canonical_name, pathogen_type, synonyms, metadata) values
  ('Andes virus', 'virus', array['virus Andes','ANDV'], '{"mvp":true}'::jsonb),
  ('Influenza A virus subtype H5N1', 'virus', array['H5N1'], '{"mvp":true}'::jsonb),
  ('Chikungunya virus', 'virus', array['CHIKV'], '{"mvp":true}'::jsonb)
on conflict (canonical_name) do update set
  pathogen_type = excluded.pathogen_type,
  synonyms = excluded.synonyms,
  metadata = public.pathogens.metadata || excluded.metadata;

insert into public.hosts (scientific_name, common_name, host_type, metadata) values
  ('Homo sapiens', 'Humano', 'human', '{"mvp":true}'::jsonb),
  (null, 'Roedores silvestres', 'wildlife', '{"mvp":true}'::jsonb),
  (null, 'Aves silvestres', 'wildlife', '{"mvp":true}'::jsonb),
  (null, 'Aves de corral', 'domestic_animal', '{"mvp":true}'::jsonb)
on conflict do nothing;

commit;
