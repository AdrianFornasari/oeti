# OETI v0.4.4 - Atomic Claims + Deterministic Signal Assembly

Esta actualización cambia la frontera de extracción del Sprint 1D para reducir la inestabilidad observada en v0.4.3.

## Cambios principales

- Nuevo contrato `shared/schemas/atomic-claims-v0.1.schema.json`.
- El LLM extrae claims atómicos; ya no construye directamente las signals finales.
- Nuevo assembler determinístico `extraction/atomic_claims.py`.
- Consolidación por `group_id` de métricas del mismo corte epidemiológico.
- Diagnóstico, genómica, transmisión, movilidad, baseline e intervención se ensamblan mediante reglas de código.
- Normalización determinística de `hantavirus`, `Andes virus` y `Orthohantavirus andesense`.
- Hosts sólo para sujetos biológicos.
- `extract-evaluation-corpus` guarda sidecars `*.claims.json` para auditar la salida original del modelo.
- Nuevas predicciones `...v044-atomic-automatic.json`; no se sobrescriben v0.4.3.
- Prueba de no regresión del 04/05/2026 y pruebas específicas BEN SE18 / Tierra del Fuego.
- Sin migraciones de Supabase.
- Suite local: **43 tests passed**.

## Flujo recomendado

```powershell
cd C:\Proyectos\OETI\oeti
.\.venv\Scripts\Activate.ps1
pip install -e ".\services\worker[test]"
python -m pytest .\services\worker\tests

python -m onehealth_worker extract-evaluation-corpus `
  --manifest ".\config\evaluation\mv-hondius-gold-standard.json" `
  --force

python -m onehealth_worker evaluate-corpus `
  --manifest ".\config\evaluation\mv-hondius-gold-standard.json" `
  --output ".\tmp\eval-mv-hondius-corpus-v044.json"
```

## Gate

No avanzar a Sprint 1E salvo que:

- `evaluated_documents = 6`
- `skipped_documents = []`
- `mean_signal_f1 >= 0.90`
- `mean_evidence_support_f1 >= 0.90`
- `mean_signal_role_accuracy >= 0.90`
- `mean_signal_type_accuracy >= 0.85`
- `event_matcher_ready = true`
