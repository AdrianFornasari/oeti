# Referencias experimentales a evidencia

`onehealth_worker.evaluation.evidence_references` es una API experimental pura
en memoria. No está conectada al extractor, runner, proveedor, prompt, schema de
claims, ensamblado ni scorer. No lee archivos, variables de entorno o URLs ni
escribe resultados. Usa únicamente stdlib.

## Catálogo determinístico

`build_catalog(document_id=..., source_bytes=...)` devuelve bytes JSON UTF-8
canónicos con versión `evidence-paragraphs-1`, identidad del documento, SHA-256
de los bytes fuente, longitud Unicode y párrafos numerados P001, P002, etc.
El documento debe tener ID textual no vacío, sin espacios en sus extremos, y
fuente UTF-8 con contenido. No normaliza saltos de línea, acentos o Unicode.

Separa párrafos con dos saltos LF/CRLF, permitiendo espacios/tabulaciones en la
línea vacía. Descarta solo whitespace de los extremos de cada fragmento y guarda
offsets absolutos Unicode `[start:end)` que siguen correspondiendo a la fuente
original. Los saltos simples internos se conservan. No es segmentación lingüística.
No elimina información del texto fuente ni transforma una copia existente.

## Resolución explícita

`resolve_references(document_id=..., source_bytes=..., catalog_bytes=...,
expected_catalog_sha256=..., references=...)` recibe un hash confiable del catálogo
desde el manifiesto congelado del llamador. No tomar ese valor de una respuesta
del modelo. La lista de referencias debe ser no vacía y cada entrada debe contener
exactamente:

```json
{
  "document_id": "D1",
  "source_sha256": "SHA256_DE_FUENTE",
  "catalog_sha256": "SHA256_DE_CATALOGO",
  "paragraph_id": "P001",
  "start": 0,
  "end": 10
}
```

Los hashes reales son SHA-256; el esperado debe ser hexadecimal minúsculo de 64
caracteres. start/end son índices Unicode relativos al texto del párrafo, no bytes
UTF-8 ni unidades UTF-16; bool/float no cuentan como enteros. Los recortes deben
estar dentro del párrafo, ser no vacíos, incluir algún carácter no whitespace
y no repetir exactamente un intervalo previo. Distintos intervalos solapados
están permitidos; esta API no decide si expresan hechos repetidos.

La API comprueba el hash confiable y exige que los bytes de catálogo sean idénticos
a regenerarlo desde ese documento/fuente. Rechaza cambios de formato JSON, versión,
texto, offsets, IDs o binding, incluso si se recalculó el hash de un catálogo
alterado. El llamador debe conservar los bytes devueltos por build_catalog; no
reserializarlos. Devuelve una lista nueva con texto literal, offsets absolutos
Unicode, ID del párrafo, documento y hashes. No muta entradas ni admite un texto
de cita alternativo. Un contrato inválido lanza EvidenceReferenceError con mensaje
genérico; no repara offsets ni busca coincidencias aproximadas.

## Límites y evaluación

El hash esperado debe provenir de una fuente confiable. Quien pueda sustituir
fuente, catálogo y manifiesto puede producir un conjunto coherente nuevo; los
hashes no son firmas. El catálogo incluye toda la fuente y puede contener datos
sensibles; la API no controla su almacenamiento o distribución.

Origen literal no significa soporte semántico. Un párrafo puede mezclar foco y
laboratorio, contextos o negaciones. El modelo aún podría elegir un fragmento
equivocado, inventar un hecho o producir offsets inválidos. Esta API no identifica
esos errores ni acredita selección correcta, generalización o precisión.

El round trip H5 con referencias calculadas desde el gold es solo una prueba de
representación, no una inferencia. No usarlo como puntuación de extracción ni
reescribir respuestas históricas para aparentar mayor aceptación. Comparar un
protocolo de modelo nuevo requiere esquema/prompt versionados, salidas separadas,
rúbrica previa, presupuesto y autorización propios. El extractor activo sigue
usando evidencia textual y no cambia con este módulo.
