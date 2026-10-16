# Validación local de registros de revisión

`onehealth_worker.evaluation.field_review` valida exclusivamente registros
provisionales del agente sin aplicar cambios. No importa Settings, proveedor LLM,
repositorios DB ni clientes de red. No escribe archivos ni interpreta URLs.

```powershell
$env:PYTHONPATH = (Resolve-Path services/worker/src).Path
python -m onehealth_worker.evaluation.field_review `
  --decisions C:/Proyectos/OETI/local-postgres-tests/h5-field-adjudication-20261016/decisions.json `
  --allowed-root C:/Proyectos/OETI
```

Código de salida 0: referencias y contrato válidos. Código 1: registro inválido,
obsoleto o archivo no disponible; error genérico sin contenido de documentos.
La API `validate_field_review(decisions_path=..., allowed_root=...)` devuelve
un resumen o lanza ReviewValidationError. No tiene opción force/apply ni DB.

## Contrato inicial

El registro decisions enlaza source_review_file y su SHA-256. rows del archivo
referido contiene IDs únicos, documento, puntero JSON al campo observado,
archivo/hash del artefacto, valor observado, propuesta y fuente/hash/cita con
intervalo Unicode [start:end). La fuente se decodifica UTF-8 sin normalizar CRLF;
los offsets deben corresponder a ese texto exacto. Se verifica también cualquier
frozen_metadata_reference suministrada con archivo/hash/puntero/valor esperado.

Cada decisión debe cubrir exactamente una fila, sin duplicados ni IDs ajenos,
con documento/campo, valor propuesto, autoría agent/human_review=false, fecha ISO,
motivo no vacío, applied=false y hashes de evidencia coincidentes. Se exigen
conteos coherentes y decisiones_applied=0. Disposiciones: accept_review_proposal,
reject_review_proposal, retain_validation_failure, confirm_current_value, abstain.
Confirmar un valor exige igualdad con el observado; conservar un fallo requiere
la acción retain_validation_failure en la propuesta. No convierte el rechazo
de una propuesta en una reparación alternativa ni elige campos por abstención.

Los punteros admiten escapes ~0/~1 y raíz vacía; índices de array solo enteros
canónicos no negativos dentro de límites. La comparación distingue bool/int/null,
no solo la igualdad flexible de Python. Todos los archivos se resuelven dentro
de la raíz explícita, incluidos enlaces: rutas absolutas históricas son válidas
si quedan dentro. Rutas relativas se resuelven junto al JSON que las referencia.
Elegir una raíz acotada: es el límite permitido de lecturas locales, no se amplía
automáticamente. No usar el validador sobre árboles que otro actor cambia a la vez.

## Alcance y límites

Un resultado válido acredita integridad referencial, no corrección semántica,
autenticidad criptográfica del autor ni revisión humana. Los hashes no son firmas;
quien pueda editar todos los archivos puede generar hashes nuevos. El contrato
no admite atribuir revisión humana; se necesitaría un flujo distinto con identidad
verificada. Tampoco decide si el motivo o corrección propuesta son adecuados.
No sustituye schema/literalidad/binding de una predicción ni el scorer.

El SHA del propio archivo decisions queda en el resumen para vincular el resultado.
No se modifican predicciones, fuentes, decisiones, gold ni métricas. Guardar un
nuevo resumen es responsabilidad explícita del llamador. Versiones/hashes de
código deben congelarse al reproducir; un cambio de registro requiere revalidar.
Los paquetes de revisión H5 siguen fuera de Git y no se incluyen en los ejemplos
de prueba. Los tests utilizan archivos sintéticos y no necesitan credenciales.

## Informe HTML local

Para leer decisiones, valores y citas sin abrir cada JSON:

```powershell
python -m onehealth_worker.evaluation.field_review_report `
  --decisions C:/ruta/paquete/decisions.json `
  --allowed-root C:/ruta/paquete `
  --output C:/ruta/salidas/revision.html
```

El directorio de salida debe existir y el archivo debe ser nuevo. La API
`export_field_review(decisions_path=..., allowed_root=..., output_path=...)`
valida antes de generar el informe y vuelve a comprobar las referencias antes
de escribir. Usa creación exclusiva, incluso si la salida coincide con un input.
No modifica registros ni aplica propuestas. Se debe trabajar con archivos que
nadie esté modificando simultáneamente, igual que con el validador.

El HTML muestra una sección por decisión, valor observado/propuesto, disposición,
motivo, cita literal, intervalo Unicode, hashes y referencia opcional de metadatos
congelados. Incluye conteos y SHA-256 de decisions. Sus URL son texto; no descarga
fuentes. Escapa el contenido y no incluye scripts, formularios ni recursos externos.
El resumen de API/CLI añade report_version y html_sha256; no se guarda otro archivo
automáticamente. CLI devuelve 0 al exportar y 1 ante un error de validación o E/S,
sin imprimir rutas o contenido de los documentos en el error.

Aceptar una propuesta en el registro no significa aplicarla ni acreditar su
corrección. El informe conserva explícitamente autoría provisional del agente,
ausencia de revisión humana y decisiones_applied=0. No transforma documentos
fallidos en predicciones válidas ni recalcula métricas. Se genera para lectura
local; revisar su contenido antes de compartirlo, pues contiene citas originales.
