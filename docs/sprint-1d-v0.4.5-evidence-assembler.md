# Sprint 1D - OETI v0.4.5 Evidence + Deterministic Assembly Hardening

## Objetivo

v0.4.5 corrige dos clases de error identificadas al evaluar v0.4.4 sobre el corpus adjudicado MV Hondius de seis documentos:

1. el evaluador trataba `evidence.type = "quote"` y `evidence.type = "text"` como clases distintas y asignaba score cero aun cuando el texto era equivalente;
2. el assembler v0.4.4 materializaba algunas claims correctamente extraídas en signals demasiado fragmentadas o con semántica canónica subóptima.

La versión mantiene sin cambios el contrato persistido de signals (`schema_version = 0.4`) y el contrato de atomic claims (`claims-0.1`). No requiere migración de Supabase.

## Corrección de evidence

`evaluation/scoring.py` normaliza `quote` y `text` como una única clase canónica de evidencia textual tanto para coincidencia exacta como para soporte. Se mantienen las defensas existentes contra:

- polaridad opuesta/negación;
- páginas explícitamente incompatibles;
- números epidemiológicos incompatibles;
- solapamiento léxico insuficiente.

Esto corrige el artefacto observado en Mendoza 08/07/2026, donde las cuatro signals coincidían con el gold standard pero `evidence_support_f1` era cero por la diferencia `quote` vs `text`.

## Hardening del assembler

La nueva capa `extraction/assembly_v045.py` recibe una copia profunda de las atomic claims y aplica reglas determinísticas antes de delegar en el assembler v0.4.4. Los sidecars `*.claims.json` originales no se modifican.

Reglas principales:

- cluster sindrómico + conteo de muertes del mismo `group_id` se ensamblan en una signal cluster con métrica `deaths`;
- resultado diagnóstico positivo en humano se representa como `case_report` con `confirmed_cases=1`, conservando diagnostics;
- `current_location` contextual no se propaga automáticamente a case reports ni transmission observations;
- narrativa histórica negativa sin una observación cuantificada permanece auditable en claims pero no materializa signal automática;
- conteos históricos cerrados pasan a `background_context`;
- itinerarios con múltiples claims del mismo grupo derivan una ventana `start/end` y `reference_period=observation_window`;
- wildlife sampling + ausencia explícita de reservorio del mismo operativo se consolidan en una sola `negative_evidence + wildlife_event`;
- claims genómicos del mismo grupo usan la taxonomía explícita más específica y preservan la descripción de variante/linaje;
- capacitaciones o transferencias de técnica sin medición epidemiológica quedan como contexto operativo y no como signal emergente.

## Reassembly offline

v0.4.5 agrega `onehealth_worker.evaluation.reassembly`. Este flujo permite reconstruir las predicciones a partir de los sidecars atomic claims v0.4.4 sin base de datos, sin red y sin volver a invocar al LLM. Así se mide exclusivamente el efecto del assembler y del evaluador.

Manifiesto dedicado:

`config/evaluation/mv-hondius-gold-standard-v045.json`

Comando:

```powershell
python -m onehealth_worker.evaluation.reassembly `
  --manifest ".\config\evaluation\mv-hondius-gold-standard-v045.json" `
  --force
```

Después ejecutar:

```powershell
python -m onehealth_worker evaluate-corpus `
  --manifest ".\config\evaluation\mv-hondius-gold-standard-v045.json" `
  --output ".\tmp\eval-mv-hondius-corpus-v045.json"
```

## Validación local requerida antes de merge

```powershell
cd C:\Proyectos\OETI\oeti
.\.venv\Scripts\Activate.ps1
pip install -e ".\services\worker[test]"
python -m pytest .\services\worker\tests
```

El repositorio no tiene CI configurado para esta rama, por lo que el PR debe permanecer sin merge hasta ejecutar localmente la suite y revisar el benchmark completo.

## Release gate

Los umbrales no se relajan:

- `mean_signal_f1 >= 0.90`
- `mean_evidence_support_f1 >= 0.90`
- `mean_signal_role_accuracy >= 0.90`
- `mean_signal_type_accuracy >= 0.85`
- corpus adjudicado completo de al menos seis documentos

No avanzar a Sprint 1E / Event Matching mientras `event_matcher_ready` permanezca en `false`.
