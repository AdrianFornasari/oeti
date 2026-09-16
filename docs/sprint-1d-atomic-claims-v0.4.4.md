# Sprint 1D - v0.4.4 Atomic Claims + Deterministic Signal Assembly

## Motivación

La corrida v0.4.3 del corpus adjudicado mostró una mejora de evidencia (`mean_evidence_support_f1=0.758333`) pero mantuvo `mean_signal_f1=0.674348` y produjo una regresión en el documento inicial del 04/05/2026. El patrón indicó que un único paso LLM estaba intentando simultáneamente extraer hechos, agruparlos, tipificarlos, normalizarlos y construir signals finales.

## Cambio arquitectónico

v0.4.4 divide el proceso:

```text
raw document
    -> LLM Structured Output: atomic claims v0.1
    -> local schema validation
    -> literal evidence validation
    -> deterministic signal assembler
    -> canonical signal-extractor v0.4 payload
    -> normalization
    -> canonical schema validation
    -> benchmark/persistence
```

El contrato persistido de `signals` permanece en `schema_version=0.4`; no se requiere migración de Supabase.

## Atomic claims v0.1

Cada claim contiene un solo hecho y como máximo una métrica. Los claims del mismo corte epidemiológico comparten `group_id`. El modelo ya no decide directamente `signal_role` ni `signal_type` finales.

Clases principales:

- `syndromic_cluster`
- `outbreak_update`
- `case_status`
- `death_count`
- `diagnostic_result`
- `laboratory_investigation`
- `genomic_finding`
- `transmission_statement`
- `surveillance_baseline`
- `wildlife_sampling`
- `wildlife_presence_absence`
- `mobility`
- `historical_context`
- `intervention`
- `official_action`

## Ensamblado determinístico

El assembler:

1. agrupa `outbreak_update`, `case_status` y `death_count` del mismo `group_id`;
2. consolida métricas del mismo corte en una única signal `outbreak`;
3. mantiene diagnóstico, genómica y transmisión como señales independientes;
4. convierte evidencia diagnóstica negativa en `negative_evidence + laboratory_result`;
5. convierte ausencia explícita de reservorio en `negative_evidence + wildlife_event`;
6. mantiene baselines como `surveillance_baseline + case_report`;
7. normaliza de forma determinística `hantavirus`, `cepa/virus Andes` y `Orthohantavirus andesense` sin inventar mayor especificidad;
8. sólo convierte sujetos biológicos en hosts;
9. deduplica métricas, ubicaciones, hosts y evidence dentro de cada signal ensamblada.

## Trazabilidad del benchmark

`extract-evaluation-corpus` genera dos archivos por documento:

- `...v044-atomic-automatic.claims.json`: salida atómica original del LLM;
- `...v044-atomic-automatic.json`: signals finales ensambladas determinísticamente.

Esto permite separar errores de extracción de claims de errores de ensamblado.

## Pruebas de no regresión

La suite incorpora una prueba adjudicada del documento del 04/05/2026. A partir de claims equivalentes al gold standard, el assembler debe recuperar:

- 7/7 signals;
- signal F1 = 1.0;
- signal role accuracy = 1.0;
- signal type accuracy = 1.0;
- evidence support F1 = 1.0.

También se prueban:

- consolidación de los cuatro conteos del BEN SE18 en una única signal outbreak;
- separación de serología, genómica, relación epidemiológica negativa y ausencia de reservorio en Tierra del Fuego.

## Release gate

No se modifican los umbrales del Sprint 1D:

- mean signal F1 >= 0.90
- mean evidence support F1 >= 0.90
- mean signal role accuracy >= 0.90
- mean signal type accuracy >= 0.85

El event matcher permanece bloqueado hasta superar el corpus de seis documentos.
