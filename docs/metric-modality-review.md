# Modalidad métrica para revisión explícita de desarrollo

Helper de desarrollo, sin integración al runner ni a producción. No sustituye
schemas de claims/signals, assembler, sidecar de atribución ni persistencia.
build_assertion_view exige bytes/hashes de claims y anotaciones, texto/hash
fuente, schema local confiable y expected_document. Rechaza referencias externas.

Cada claim con metric.reported=true conserva cifra, clase, campos originales e
identidad ligada a versión/puntero. No deduplica ni suma. Claims sin métrica se
retienen aparte. Anotaciones explícitas asserted/possible conservan procedencia;
sin anotación la vista indica not_evaluated. No infiere modalidad desde polarity.

Los hashes/documento/literalidad verifican integridad, no aceptación semántica.
reviewer es texto de procedencia suministrado por el caller, no autenticación ni
permiso. Anotaciones conflictivas o sin destino se rechazan. El consumidor debe
conservar decisiones y su linaje por separado, sin presentar el campo reviewer
como adjudicación independiente. No se cambia ningún original.

API y formato draft. Uso explícito con anotaciones revisadas por caller; no cargar
automáticamente archivos de anotaciones ni actualizar decisiones de históricos.
Los controles son construidos y no demuestran que el modelo emita modalidades
correctas. La cita insuficiente de SCOPE04 sigue sin corregirse.

## Anotaciones explícitas

El caller suministra bytes JSON y su hash confiable. El sobre declara:

```json
{
  "version": "offline-modality-annotation-draft-1",
  "claims_sha256": "<hash del artefacto original>",
  "source_sha256": "<hash UTF-8 del texto fuente>",
  "entries": [
    {
      "claim_pointer": "/claims/0",
      "modality": "asserted",
      "reviewer": "<referencia de procedencia>",
      "review_kind": "assisted_user_review",
      "evidence_pointer": "/claims/0/evidence/0"
    }
  ]
}
```

`modality` admite `asserted` o `possible`; `entries=[]` deja todas las métricas
como `not_evaluated`. `review_kind` admite `assisted_user_review` y
`constructed_control`, sin autenticar la afirmación del caller sobre su origen.
La evidencia debe pertenecer al claim anotado y ser literal con normalización
de espacios. Eso no prueba que respalde la modalidad ni complete el contexto.

La salida conserva `assertions`, `nonmetric_claims`, hashes, documento y
`semantic_acceptance=not_assessed`. La identidad de una afirmación depende de
la versión de claims y su puntero métrico, no de la anotación; cambia al cambiar
el artefacto original. No es una identidad epidemiológica global.

`test_metric_modality_review.py` usa fixtures construidos dentro del repositorio;
no necesita carpetas locales del autor, predicciones ni acceso a proveedores.
