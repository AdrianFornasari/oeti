# One Health Emerging Threat Intelligence

MVP **Argentina-first** para integrar señales de salud humana, sanidad animal, fauna silvestre, ambiente, genómica y otras fuentes relevantes en eventos epidemiológicos trazables.

## Arquitectura inicial

```text
apps/web           Next.js - radar y revisión de eventos
services/worker    Python - ingesta, extracción y normalización
supabase           PostgreSQL/PostGIS, migraciones, seed y pruebas RLS
shared/schemas     contratos estructurados compartidos
docs               decisiones de arquitectura y modelo de datos
```

El navegador tiene acceso de **solo lectura** a las tablas epidemiológicas aprobadas. Las escrituras de ingesta y extracción se realizan exclusivamente desde procesos de servidor/worker. `raw_items` contiene sólo metadatos trazables (URL, título, fechas, hash) y es legible por usuarios autenticados; el contenido fuente completo se aísla en `raw_item_payloads`, accesible sólo desde servidor.

## Arranque local

Requisitos: Node.js compatible con Next.js 16, Docker Desktop o runtime compatible, Python 3.14 recomendado y Git.

```bash
npm install
# solo la primera vez, si todavía no existe supabase/config.toml:
npx supabase init
npx supabase start
npx supabase db reset
npx supabase test db
```

Copiar `.env.example` a `.env.local`/`.env` y completar las claves que muestra `supabase start`.

Web:

```bash
npm run dev:web
```

Worker:

```bash
cd services/worker
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -e .
python -m onehealth_worker
```

## Estado de esta entrega

- Esquema de base de datos v0.1.
- PostGIS habilitado en esquema `gis`.
- RLS activado en todas las tablas `public`.
- `anon`: sin acceso.
- `authenticated`: lectura sobre tablas derivadas; sin escritura.
- `raw_items`: metadatos trazables en sólo lectura para usuarios autenticados.
- `raw_item_payloads`: contenido fuente completo sólo en servidor.
- Catálogo inicial de fuentes Argentina/One Health.
- Contrato JSON v0.1 del extractor.
- Frontend y worker mínimos para comprobar estructura; todavía no implementan ingesta real.

## Siguiente objetivo

Construir el primer pipeline real sobre una publicación oficial argentina relacionada con hantavirus/MV Hondius: **fetch -> raw_item -> extractor -> signal -> validación -> persistencia**.

## Sprint 1B - ingesta Argentina-first

La versión 0.2 agrega el primer pipeline real de ingesta de páginas oficiales argentinas y un manifiesto retrospectivo del caso hantavirus / MV Hondius.

Flujo implementado:

`URL oficial -> raw_item -> raw_item_payload`

La generación de `signals` queda deliberadamente fuera de este sprint y se implementará en Sprint 1C.

Ver `docs/sprint-1b-ingestion.md` y `services/worker/README.md`.
