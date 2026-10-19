# Adaptador experimental de claims por referencias

`evaluation.claims_reference_adapter` convierte un protocolo experimental a
`claims-0.1`. Está separado del extractor, runner, prompt, proveedor, ensamblado
y scorer activos. No ejecuta inferencias, lee archivos o variables de entorno,
descarga recursos ni escribe resultados. Reutiliza las dependencias existentes.

## Contrato de respuesta separado

`shared/schemas/atomic-claims-refs-v0.1.experimental.schema.json` es una instantánea
derivada del esquema actual: cambia schema_version a `claims-refs-0.1` y sustituye
claim.evidence por evidence_refs. Los demás campos y restricciones se conservan.
`reference_response_schema(claims_schema)` deriva una copia independiente desde
el esquema confiable suministrado. Una prueba exige que coincida con la instantánea;
si cambia el esquema base, revisar y versionar explícitamente el experimental.
No se modifica el esquema usado por producción. Validación JSON Schema local
no acredita compatibilidad con una API de generación estructurada.

Cada claim exige al menos una referencia con documento, SHA-256 de fuente y catálogo,
ID de párrafo e índices Unicode relativos start/end. No admite evidence textual
alternativa, campos extra ni referencias duplicadas al mismo intervalo dentro
del mismo claim. Distintos claims pueden citar el mismo fragmento. Consultar
`docs/evidence-references-experimental.md` para límites de recortes y catálogos.

## API pura

```python
adapted = adapt_reference_claims(
    payload=experimental_response,
    expected_document=frozen_document_metadata,
    document_id=frozen_document_label,
    source_bytes=frozen_source_bytes,
    catalog_bytes=frozen_catalog_bytes,
    expected_catalog_sha256=frozen_catalog_hash,
    claims_schema=trusted_atomic_claims_schema,
)
```

El llamador carga los bytes/esquema y obtiene los bindings del manifiesto confiable.
expected_document es el objeto completo con raw_item_id, language y document_date;
debe coincidir exactamente. document_id es la identidad del catálogo, que puede
ser distinta del UUID raw_item_id. El llamador debe vincular ambos identificadores
con la misma fuente en su manifiesto. Los hashes y metadatos esperados no deben
obtenerse de la respuesta del modelo.

El adaptador rechaza valores no finitos o no serializables como JSON, valida el
protocolo, comprueba documento y catálogo determinístico incluso con claims vacíos,
y resuelve referencias. Devuelve una copia nueva con versión claims-0.1 y evidence
de tipo text, texto recuperado de fuente, location_in_document con intervalo Unicode
absoluto y page_number=null. No inventa página. Conserva todos los campos semánticos
y warnings. Valida esquema actual y literalidad al finalizar. No muta entradas ni
devuelve campos mutables compartidos. Si falla una referencia, no retorna una salida
parcial. Los errores de payload/binding se exponen como ClaimsReferenceError con
mensaje genérico sin citas. El esquema suministrado es configuración confiable;
errores de programación/configuración no forman parte de ese contrato de respuesta.

## Trazabilidad y límites

El llamador debe guardar separadamente respuesta experimental y resultado adaptado,
junto a versiones/hashes de schema, adaptador, catálogo y fuente. El resultado no
es una respuesta textual directa del modelo. La API no crea ese registro por sí
sola ni lo persiste en DB. No usarla para reparar o reemplazar respuestas históricas.

Un recorte literal puede no respaldar un hecho. No corrige localidades, fechas,
roles, scope o selección semántica ni verifica competencia del modelo para contar
offsets. Los ejemplos de oráculo solo prueban representación y compatibilidad.
Una evaluación real requiere prompt/esquema versionados, rúbrica previa, salidas
nuevas, presupuesto y autorización propios. Este módulo no activa ese experimento.
