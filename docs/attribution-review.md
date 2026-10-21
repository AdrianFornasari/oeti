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
que dice probable. Tampoco basta una clase que aparezca únicamente en evidencia.
Esas inconsistencias quedan fuera de este helper; no interpretar ausencia de
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
