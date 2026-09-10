# OETI Worker - Sprint 1B

El worker v0.2 implementa la primera tubería real de ingesta HTML:

`URL oficial -> HTTP -> extracción de título/fecha/texto -> hash -> raw_items + raw_item_payloads`

Todavía **no** genera `signals`; eso corresponde al Sprint 1C (extractor IA + validación JSON).

## Instalación (PowerShell)

Desde la raíz del repo:

```powershell
cd C:\Proyectos\OETI\oeti
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".\services\worker[test]"
```

## Configuración

Copiar `.env.example` a `.env` y completar `DATABASE_URL`.
Para desarrollo desde una red IPv4, usar la cadena **Session pooler** del panel `Connect` de Supabase y exigir SSL.

No subir `.env` a Git.

## Aplicar catálogos del Sprint 1B

```powershell
npx supabase db push --dry-run
npx supabase db push
```

La migración nueva es `20260910150000_bootstrap_reference_catalogs.sql`.

## Probar una URL

```powershell
python -m onehealth_worker ingest-url `
  --source-code ARG_MSAL_NEWS `
  --url "https://www.argentina.gob.ar/noticias/salud-monitorea-junto-organismos-internacionales-los-casos-de-hantavirus-reportados-en-el"
```

## Ingerir el caso MV Hondius

```powershell
python -m onehealth_worker ingest-case `
  --manifest ".\config\cases\mv-hondius.json"
```

La operación es idempotente por `(source_id, content_sha256)`: si el contenido parseado no cambió, no crea otro `raw_item`.
Si una fuente publica una versión sustantivamente modificada, el hash cambia y se conserva una nueva versión como otro `raw_item`.

## Verificación SQL

```sql
select
  s.code as source_code,
  r.id,
  r.title,
  r.published_at,
  r.retrieved_at,
  r.processing_status,
  r.url
from public.raw_items r
join public.sources s on s.id = r.source_id
order by r.published_at nulls last, r.retrieved_at;
```

El texto completo está en `raw_item_payloads` y no tiene política de lectura para clientes autenticados.
