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

## Sprint 1C - structured signal extraction

OETI now includes an auditable epidemiological extraction boundary: `raw_item_payload -> Structured Output JSON -> schema validation -> catalog resolution -> signals/evidence`. See `docs/sprint-1c-signal-extraction.md`.

Before first use, apply migration `20260910183000_signal_extraction_runs.sql` and configure `LLM_API_KEY` only in the root `.env`.

## Sprint 1C v0.3.5

El extractor separa diagnóstico de genómica, valida evidencia literal contra el raw_text, distingue ubicaciones de laboratorio y excluye alertas administrativas/baselines del futuro event matching.

## Sprint 1D v0.4.0 - evaluación contra gold standard

Se agrega un benchmark reproducible para comparar extracciones contra referencias humanas adjudicadas antes de habilitar deduplicación/event matching. Incluye el primer gold standard del caso MV Hondius (04/05/2026), matching semántico de señales, métricas de precision/recall/F1 por documento y un gate de corpus. Ver `docs/sprint-1d-gold-standard-evaluation.md`.


## Sprint 1D v0.4.1 - benchmark autocontenido

La predicción automática de referencia del 04/05/2026 se versiona en `evaluation/predictions/` y el manifiesto ya no depende de archivos temporales locales. El benchmark inicial compara deliberadamente la salida automática no revisada contra el gold standard humano.


### Resultado reproducible v0.4.1

Sobre la salida automática no revisada del 04/05/2026, el benchmark devuelve composite score 0.943878. El event matcher continúa bloqueado hasta completar y adjudicar el corpus de seis documentos.


## Sprint 1D v0.4.2

Corpus MV Hondius de seis documentos adjudicado; usar `extract-evaluation-corpus` para generar automáticamente las cinco predicciones faltantes y luego `evaluate-corpus` para ejecutar el release gate.

## Sprint 1D v0.4.3 - hardening del extractor y evaluator v0.2

La primera corrida del corpus completo v0.4.2 no superó el gate (`mean_signal_f1=0.648135`; evidencia exacta macro=0.208333). La v0.4.3 corrigió dos capas por separado:

- extractor: consolidación de actualizaciones, menos sobre-fragmentación, normalización explícita de Andes virus y reglas para evidencia negativa/genómica;
- evaluador: `evidence_exact_f1` + `evidence_support_f1`, snapshots de señales no emparejadas y release thresholds versionados en el manifiesto.

Las predicciones v0.4.3 usan archivos nuevos `evaluation/predictions/...v043-automatic.json`. Regenerar con `extract-evaluation-corpus --force` y volver a ejecutar `evaluate-corpus`; no se habilita event matching hasta superar el gate completo.

## Sprint 1D v0.4.4 - Atomic Claims + Deterministic Signal Assembly

La extracción se divide en dos etapas: el LLM produce claims epidemiológicos atómicos y un assembler determinístico construye las signals canónicas v0.4. Esto reduce la sobre-fragmentación y permite distinguir si un error proviene del modelo o de las reglas de ensamblado. Cada predicción de benchmark conserva además un sidecar `*.claims.json` para auditoría. Ver `docs/sprint-1d-atomic-claims-v0.4.4.md`.

## Sprint 1D v0.4.5 - Evidence + Deterministic Assembly Hardening

La v0.4.5 corrige el artefacto `quote` vs `text` del evaluador y agrega reglas determinísticas para consolidar cluster+mortalidad, casos humanos confirmados, itinerarios, contexto histórico, evidencia wildlife negativa y claims genómicos relacionados. Los sidecars v0.4.4 quedan intactos.

La validación inicial de v0.4.5 debe hacerse **offline**, reensamblando los atomic claims existentes sin volver a invocar al LLM:

```powershell
python -m onehealth_worker.evaluation.reassembly `
  --manifest ".\config\evaluation\mv-hondius-gold-standard-v045.json" `
  --force

python -m onehealth_worker evaluate-corpus `
  --manifest ".\config\evaluation\mv-hondius-gold-standard-v045.json" `
  --output ".\tmp\eval-mv-hondius-corpus-v045.json"
```

Ver `docs/sprint-1d-v0.4.5-evidence-assembler.md`. Los thresholds del release gate no cambian y Sprint 1E continúa bloqueado hasta obtener `event_matcher_ready=true`.
