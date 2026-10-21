# Avisos opcionales de atribución en evaluación offline

`evaluation.attribution_review.build_review` genera un informe auxiliar de revisión,
sin reparación, rechazo, aprobación semántica ni asignación de clases. Es un helper
de desarrollo posterior a predicciones conocidas, no un evaluador independiente.

La API del runner permite habilitarlo explícitamente:

```python
run_frozen_corpus(
    manifest_path=manifest_path,
    output_dir=new_output_dir,
    execute=True,
    provider=saved_or_fake_provider,
    include_attribution_review=True,
)
```

`include_attribution_review=False` es el valor por defecto. La CLI sigue siendo
prepare-only: este cambio no crea una opción para llamar a proveedores reales.
Un provider de respuestas guardadas o fake permite probarlo sin llamadas reales.
La función no carga credenciales, red, Settings, repositorios ni base de datos.

## Integridad y salidas

El módulo verifica hashes esperados de claims/signals/texto fuente, documento
exacto, esquemas y evidencia literal. Regenera candidatos de procedencia métrica
con el módulo puro existente: igualdad estructural no prueba semántica ni grupo.

En ejecución válida produce `NNN.attribution-review.json`, con su hash y ruta en
`results[].attribution_review`. El informe general registra versión y hash del
código, `affects_validation=False` y `semantic_acceptance=not_assessed`.
Puede coexistir con `include_review_hints` e `include_metric_period_provenance`.

En preparación o tras fallo previo de validación, el estado es `not_generated`.
Si el helper o su escritura fallan, queda `generation_error` con sólo el tipo de
excepción. Eso no cambia el estado `generated` de una predicción válida. Si se
produce un fallo parcial de escritura, no consumir el sidecar como generado sin
su estado/hash correctos. El error no es permiso para reparar ni reejecutar.

No cambia instructions, input o esquema del provider, uso, response_id, bytes de
claims/signals, validaciones ni decisiones. Una revisión sin findings no aprueba
la predicción. No está integrado al pipeline de extracción/persistencia.

## Contexto original por métrica: formato v2

`attribution-review-sidecar-2` agrega `metric_source_contexts`, una fila por métrica
final con signal_id, metric_pointer, métrica original, binding_status y la lista
completa de source_claims candidatos exactos. Cada candidato conserva su puntero,
ID/grupo, claim_kind, polarity, subject, locations, reference_period, event_date,
metric, diagnostics, summary y evidence tal como figuran en el claim guardado.

El bloque se genera para nombres genéricos y explícitos, sin depender de palabras
clave de clase. Un candidato único es sólo una coincidencia estructural; no se
asigna clasificación ni se verifica pertenencia al grupo. Ambiguous conserva
todos los candidatos con sus diferencias; unmatched tiene source_claims vacío.
No hay selected_claim_id ni clase normalizada derivada. Un cero explícito reportado
conserva contexto; ausencia cualitativa o PCR sin métrica no genera filas métricas.

Esto permite revisar `case_count=3` junto a subject «casos probables» y
`case_count=2` junto a «casos confirmados» en sus fuentes candidatas, sin cambiar
las métricas de la señal. También expone nombres explícitos y campos fuente que
se contradigan para revisión manual; no los corrige. Son campos del modelo,
incluidos sus errores, no hechos adjudicados. Las declaraciones de no aceptación,
clasificación no asignada y grupo no verificado siguen vigentes.

Los sidecars v1 históricos permanecen intactos; el runner registra la nueva
versión y hash del generador cuando se habilita la opción. El mapa
metric-period-provenance-1 y los esquemas de producción no cambian.

## Interpretación de avisos

| Código | Observación que requiere revisión |
| --- | --- |
| REVIEW-LOCATION-DOCUMENT | Un valor textual de country/admin1/admin2/locality/region falta en las citas del claim y en el documento suministrado. Puede ser inferencia, alias o normalización. |
| REVIEW-LOCATION-QUOTE | El valor aparece en el documento pero no en las citas del claim. El alcance sigue sin verificarse. |
| REVIEW-METRIC-BINDING | No hay candidato métrico exacto único: ambiguous o unmatched. No se elige claim ni clase. |
| REVIEW-METRIC-CLASSIFICATION-SOURCE | Una métrica de nombre genérico tiene un candidato exacto único con vocabulario probable/confirmado/sospechoso en subject.verbatim, nombre métrico o summary. Se muestran campos y evidencia originales, sin clasificar la métrica. |

La búsqueda geográfica usa límites de palabra, casefold y espacios normalizados.
Cada cita se evalúa por separado: no se unen fragmentos para fabricar presencia
de un nombre geográfico completo.
No resuelve aliases, traducciones, acentos ni jerarquías. Por ejemplo, Estados
Unidos frente a EE.UU., Cordoba frente a Córdoba y país/provincia implícitos a
partir de una localidad pueden producir avisos revisables. No son prueba de error.
Los códigos ISO no se comparan con prosa. Un lugar mencionado en la cita puede
tener un rol erróneo sin producir aviso: presencia no es atribución correcta.

Los nombres métricos genéricos y palabras de clase son listas limitadas. Un nombre
explícito `confirmed_cases` no produce este aviso, incluso si contradice un subject
que dice probable. Tampoco basta una clase que aparezca únicamente en evidencia
para generar el aviso. El contexto v2 permite consultar esos campos originales,
pero no detecta ni decide esas inconsistencias. No interpretar ausencia de
findings como corrección. La ausencia cualitativa sin métrica no crea filas de
procedencia ni métricas sintéticas.

## Verificación y alcance

`test_attribution_review.py` cubre aliases/acentos/jerarquías, contexto fuera de
cita, límites de palabra, presencia frente a rol, nombres genéricos/expresivos,
procedencia ambigua o ausente, integridad, literalidad y no mutación. Sus controles
son construidos: no son predicciones ni gold independiente.

Las pruebas de integración comparan inputs exactos del provider fake, outputs,
uso, estados por defecto/opt-in, coexistencia con otros sidecars y fallos
redactados de generación/escritura. No hacen llamadas LLM ni base de datos.

Este cambio no activa candidatos de prompt ni altera corpus/gold/umbrales. Los
planes históricos con código congelado siguen siendo históricos: no actualizar
sus hashes para hacerlos pasar sobre código cambiado. Un ensayo nuevo requiere
su propio congelamiento y, para llamadas reales, autorización y presupuesto.
