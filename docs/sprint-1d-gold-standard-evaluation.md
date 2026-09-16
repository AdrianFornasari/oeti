# Sprint 1D - Gold standard y evaluación cuantitativa del extractor

## Objetivo

Sprint 1D introduce una capa de evaluación reproducible entre el extractor estructurado y el futuro event matcher. El objetivo no es demostrar que una única extracción "funciona", sino medir de forma explícita qué detecta, qué omite y qué clasifica incorrectamente contra una referencia humana adjudicada.

La regla de arquitectura es:

`raw item -> extracción automática -> gold standard humano -> evaluación -> gate -> recién después event matching`

## Primera referencia adjudicada

Caso: `ARG-HANTA-MV-HONDIUS-2026`.

Documento inicial: publicación oficial del 04/05/2026 sobre MV Hondius.

Gold standard:

`evaluation/gold/mv-hondius/2026-05-04-initial-notification.gold.json`

La referencia parte de la extracción revisada que fue persistida al cierre de Sprint 1C y agrega dos adjudicaciones explícitas:

1. `diagnostics.target` de la investigación de laboratorio se limita a `cepa`; el "origen del brote" es un objetivo epidemiológico, no un target diagnóstico.
2. El inicio de la temporada 2025-2026 conserva precisión diaria: `2025-07-29`.

Los IDs de las señales gold son estables (`GS-MVH-20260504-XX`) y no dependen de los IDs producidos por el modelo.

## Matching de señales

La evaluación no compara posiciones ni `local_signal_id`. Primero construye un matching semántico bipartito entre señales gold y señales predichas.

El score de emparejamiento pondera:

- `signal_type`: 0.22
- `signal_role`: 0.18
- enfermedad: 0.12
- métricas: 0.12
- patógeno: 0.10
- ubicaciones y roles: 0.10
- fecha de evento: 0.06
- período de referencia: 0.04
- diagnóstico: 0.04
- dominios: 0.02

Umbral inicial: `0.55`.

Para hasta 15 señales predichas se usa asignación óptima exacta; para documentos mayores se usa un fallback greedy determinístico.

## Métricas

La salida del evaluador informa:

- detección de señales: TP, FP, FN, precision, recall y F1;
- accuracy de `signal_role` y `signal_type`;
- disease/pathogen identity;
- estado de normalización;
- exactitud temporal;
- F1 de métricas, ubicaciones, hosts y evidencia;
- exactitud del bloque `diagnostics`;
- pares de señales matched y scores;
- señales gold omitidas y predicciones no asignadas.

`composite_score` es sólo un resumen descriptivo macro. No es un score de riesgo ni reemplaza el release gate.

## CLI - documento individual

```powershell
python -m onehealth_worker evaluate-extraction `
  --prediction ".\\tmp\\mv-hondius-semantic-v035-original.json" `
  --gold ".\\evaluation\\gold\\mv-hondius\\2026-05-04-initial-notification.gold.json" `
  --output ".\\tmp\\eval-mv-hondius-20260504.json"
```

La evaluación es offline: no necesita conexión a Supabase ni credenciales de LLM.

## CLI - corpus

```powershell
python -m onehealth_worker evaluate-corpus `
  --manifest ".\\config\\evaluation\\mv-hondius-gold-standard.json" `
  --output ".\\tmp\\eval-mv-hondius-corpus.json"
```

El manifiesto ya enumera las seis publicaciones previstas del caso. En esta versión sólo el documento del 04/05/2026 está adjudicado; los otros cinco quedan `pending_adjudication` y el evaluador los omite explícitamente.

## Release gate inicial

Un único documento puede superar `single_document_pass`, pero **nunca** habilita por sí solo el event matcher.

El gate de corpus exige, como mínimo:

- 6 documentos adjudicados y evaluados;
- mean signal F1 >= 0.90;
- mean evidence F1 >= 0.90;
- mean signal_role accuracy >= 0.90;
- mean signal_type accuracy >= 0.85.

Hasta completar ese corpus, `event_matcher_ready = false` por diseño.

## Resultado de calibración inicial

Comparando la extracción revisada v0.3.5 contra el nuevo gold standard del 04/05/2026:

- signal precision = 1.00
- signal recall = 1.00
- signal F1 = 1.00
- signal_role accuracy = 1.00
- signal_type accuracy = 1.00
- evidence F1 = 1.00
- reference_period accuracy = 0.857143
- diagnostics accuracy = 0.857143
- composite_score = 0.979592
- event_matcher_ready = false

Estas dos discrepancias son deliberadas: el gold standard captura las adjudicaciones de precisión temporal y target diagnóstico definidas al iniciar Sprint 1D.

## Siguiente subetapa

Adjudicar las cinco publicaciones restantes de MV Hondius, generar una extracción automática independiente para cada una y ejecutar `evaluate-corpus`. El futuro event matcher no se implementará hasta que el corpus complete el gate acordado o se documenten explícitamente los desvíos aceptados.


## Repetición autocontenida v0.4.1

La primera entrega v0.4.0 tenía una dependencia operacional incorrecta: el manifiesto de corpus apuntaba a `tmp/mv-hondius-semantic-v035-original.json`, un artefacto local no versionado. Esto hacía que el benchmark no fuese reproducible desde un checkout limpio.

La v0.4.1 corrige el diseño guardando la predicción automática no revisada en:

`evaluation/predictions/mv-hondius/2026-05-04-v035-automatic.json`

El manifiesto usa exclusivamente artefactos versionados. El benchmark inicial se ejecuta contra la salida automática previa a revisión humana, mientras que el gold standard conserva las correcciones adjudicadas.

### Resultado de calibración corregido

- signal detection precision/recall/F1: `1.0 / 1.0 / 1.0`
- locations F1: `0.642857`
- hosts F1: `0.857143`
- reference period accuracy: `0.857143`
- diagnostics accuracy: `0.857143`
- composite score: `0.943878`
- `event_matcher_ready`: `false`

El score previo 0.979592 no se considera resultado válido del benchmark automático porque la predicción usada había sido objeto de correcciones humanas. Se conserva como antecedente de calibración, pero no como métrica de performance del extractor.


## Corpus completo adjudicado - v0.4.2

Los cinco documentos restantes del caso MV Hondius quedaron adjudicados contra fuentes oficiales. El corpus ahora contiene seis gold standards.

### Scope de benchmark

Los BEN son publicaciones multitemáticas. Para evitar penalizar al extractor por detectar correctamente influenza, dengue, chikungunya u otros temas ajenos al caso, las predicciones de benchmark se generan con un `evaluation_scope` explícito limitado a hantavirus, MV Hondius y vigilancia nacional de hantavirus. Este scope se aplica sólo al benchmark y no modifica la extracción productiva general.

### Gold standards portables

Los cinco nuevos gold standards usan `adjudication.raw_item_binding = prediction`. El evaluador enlaza el UUID real de la predicción antes de validar. De esta forma, el gold no queda acoplado al UUID de una instalación particular de Supabase.

### Generación automática de las cinco predicciones faltantes

Primero asegurá que las seis URLs del caso estén ingeridas:

```powershell
python -m onehealth_worker ingest-case `
  --manifest ".\config\cases\mv-hondius.json"
```

Luego generá las predicciones de benchmark sin persistir señales:

```powershell
python -m onehealth_worker extract-evaluation-corpus `
  --manifest ".\config\evaluation\mv-hondius-gold-standard.json"
```

El comando conserva la predicción ya versionada del 04/05 y genera sólo los archivos faltantes, salvo que se use `--force`.

Finalmente:

```powershell
python -m onehealth_worker evaluate-corpus `
  --manifest ".\config\evaluation\mv-hondius-gold-standard.json" `
  --output ".\tmp\eval-mv-hondius-corpus-v042.json"
```

El objetivo operativo es `evaluated_documents = 6` y `skipped_documents = []`. La decisión `event_matcher_ready` se toma exclusivamente con el release gate ya definido.

## Diagnóstico del corpus completo - resultado v0.4.2

La primera evaluación de los seis documentos adjudicados completó el corpus (`evaluated_documents = 6`, `skipped_documents = []`) pero no superó el release gate:

- mean signal F1: `0.648135`
- mean evidence F1 (comparación textual exacta v0.1): `0.208333`
- mean signal_role accuracy: `0.902778`
- mean signal_type accuracy: `0.819445`
- `metrics_pass = false`
- `event_matcher_ready = false`

El análisis por documento mostró dos problemas distintos. En los BEN, el extractor sobre-fragmentaba actualizaciones del mismo brote y producía señales adicionales para cifras que debían convivir como métricas dentro de una sola señal. En los documentos de fauna, los principales errores correspondían a evidencia negativa, relación/no relación genómica, hosts y clasificación del tipo de señal.

También se detectó un problema del propio benchmark: `evidence_f1` exigía identidad textual exacta del fragmento. Dos citas literales diferentes podían sostener la misma proposición y recibir score cero. Por eso la v0.4.3 separa exactitud de cita y suficiencia de soporte.

## Hardening v0.4.3

### Evaluador de evidencia v0.2

El reporte incorpora dos métricas:

- `evidence_exact_f1`: conserva el criterio estricto de identidad de tipo + texto + página.
- `evidence_support_f1`: acepta dos fragmentos literales como soporte equivalente cuando uno es un subspan suficiente del otro o existe un solapamiento fuerte de tokens de contenido.

La comparación de soporte tiene guardas para evitar falsos equivalentes:

- una cita afirmativa y otra negada no pueden emparejarse;
- si ambas contienen cifras explícitas incompatibles, no pueden emparejarse;
- debe existir suficiente contenido compartido;
- la validación previa de `evidence.text` como fragmento literal del `raw_text` sigue siendo obligatoria.

Desde `evaluation_schema_version = 0.2`, el release gate usa `evidence_support_f1 >= 0.90`. `evidence_exact_f1` se conserva como métrica diagnóstica. El campo histórico `evidence_f1` queda como alias de `evidence_support_f1` para compatibilidad.

### Reporte de errores accionable

`unmatched_gold` y `unmatched_prediction` dejan de ser simples listas de IDs. El reporte ahora incluye un snapshot de cada señal no emparejada con:

- `signal_role` y `signal_type`;
- summary;
- enfermedad y patógeno;
- métricas;
- ubicaciones y roles;
- hosts;
- diagnóstico;
- evidencia.

Esto permite diagnosticar la siguiente iteración directamente desde el JSON de evaluación.

### Reglas nuevas del extractor

La versión `oeti-signal-extractor-v0.4.3` agrega reglas explícitas para:

1. consolidar varios conteos del mismo corte epidemiológico en una sola señal;
2. no fragmentar una actualización de brote en múltiples señales equivalentes;
3. evitar duplicados por repetición entre título/resumen/cuerpo;
4. separar actualización del brote de baseline nacional;
5. resolver `cepa Andes` como `Andes virus` sólo cuando la fuente lo expresa explícitamente;
6. distinguir observación genómica descriptiva de evidencia negativa de relación epidemiológica;
7. representar ausencia explícita de especie reservorio como `negative_evidence + wildlife_event`;
8. representar serología/diagnóstico negativo como `negative_evidence + laboratory_result`;
9. excluir buques, edificios, laboratorios e instituciones de `hosts`;
10. seleccionar evidencia literal mínima suficiente, preservando negaciones y cifras relevantes.

### Normalización determinística adicional

Después de la respuesta del proveedor y antes de validar/persistir:

- `cepa Andes`, `virus Andes` o `variante Andes` explícitos se normalizan a `Andes virus / resolved`;
- `Orthohantavirus andesense` explícito se conserva a ese nivel;
- entidades no biológicas obvias se eliminan de `hosts`;
- señales exactamente duplicadas se eliminan de forma determinística.

Estas reglas no intentan inferir epidemiología. Sólo corrigen inconsistencias estructurales que pueden verificarse a partir del texto explícito del propio output.

### Benchmark v0.4

Las predicciones v0.3.5 se conservan como artefactos históricos. El manifiesto v0.4 usa rutas nuevas `v043-automatic.json`, de modo que la evaluación de v0.4.3 no sobrescribe resultados anteriores.

Los seis documentos tienen `source_url`, incluido el artículo inicial del 04/05, por lo que el corpus completo puede regenerarse con el extractor nuevo:

```powershell
python -m onehealth_worker extract-evaluation-corpus `
  --manifest ".\config\evaluation\mv-hondius-gold-standard.json" `
  --force

python -m onehealth_worker evaluate-corpus `
  --manifest ".\config\evaluation\mv-hondius-gold-standard.json" `
  --output ".\tmp\eval-mv-hondius-corpus-v043.json"
```

El gate continúa sin relajarse:

- mean signal F1 >= `0.90`
- mean evidence support F1 >= `0.90`
- mean signal_role accuracy >= `0.90`
- mean signal_type accuracy >= `0.85`
- seis documentos evaluados, sin skips.

No se habilita Sprint 1E/event matching mientras `event_matcher_ready` permanezca en `false`.
