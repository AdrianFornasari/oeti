-- Initial catalogs for Argentina-first development

insert into public.sources (code, name, kind, ingestion, base_url, country_iso2, license_notes) values
  ('ARG_MSAL_BEN', 'Boletín Epidemiológico Nacional - Ministerio de Salud', 'primary_official', 'pdf', 'https://www.argentina.gob.ar/salud/boletin-epidemiologico-nacional', 'AR', 'Persistir metadatos y evidencia permitida; verificar condiciones de reutilización de cada documento.'),
  ('ARG_MSAL_COMMS', 'Comunicaciones Epidemiológicas - Ministerio de Salud', 'primary_official', 'html', 'https://www.argentina.gob.ar/salud/boletin-epidemiologico-nacional/comunicaciones-epidemiologicas', 'AR', 'Fuente oficial prioritaria para alertas nacionales.'),
  ('ARG_ANLIS', 'ANLIS-Malbrán', 'primary_official', 'html', 'https://www.argentina.gob.ar/salud/anlis', 'AR', 'Laboratorio de referencia y vigilancia genómica.'),
  ('ARG_SENASA', 'SENASA - Sanidad Animal', 'primary_official', 'html', 'https://www.argentina.gob.ar/senasa', 'AR', 'Sanidad animal, fauna y eventos de notificación veterinaria.'),
  ('ARG_SMN', 'Servicio Meteorológico Nacional', 'primary_official', 'dataset', 'https://www.smn.gob.ar/', 'AR', 'Variables ambientales y meteorológicas.'),
  ('PAHO', 'Organización Panamericana de la Salud', 'international_official', 'html', 'https://www.paho.org/', null, 'Contexto regional y alertas de las Américas.'),
  ('WHO_DON', 'WHO Disease Outbreak News', 'international_official', 'html', 'https://www.who.int/emergencies/disease-outbreak-news', null, 'Confirmación y contexto internacional.'),
  ('WOAH_WAHIS', 'WOAH WAHIS', 'international_official', 'dataset', 'https://wahis.woah.org/', null, 'Sanidad animal internacional; verificar modalidad técnica/licencia antes de automatizar.' )
on conflict (code) do nothing;

insert into public.diseases (canonical_name, synonyms) values
  ('Hantavirus pulmonary syndrome', array['síndrome pulmonar por hantavirus', 'SPH']),
  ('Avian influenza A(H5N1)', array['influenza aviar H5N1', 'IAAP H5N1']),
  ('Chikungunya', array['fiebre chikungunya'])
on conflict (canonical_name) do nothing;

insert into public.pathogens (canonical_name, pathogen_type, synonyms) values
  ('Andes virus', 'virus', array['virus Andes', 'ANDV']),
  ('Influenza A virus subtype H5N1', 'virus', array['H5N1']),
  ('Chikungunya virus', 'virus', array['CHIKV'])
on conflict (canonical_name) do nothing;

insert into public.hosts (scientific_name, common_name, host_type) values
  ('Homo sapiens', 'Humano', 'human'),
  (null, 'Roedores silvestres', 'wildlife'),
  (null, 'Aves silvestres', 'wildlife'),
  (null, 'Aves de corral', 'domestic_animal')
on conflict do nothing;
