# Sprint 1C - refinamiento semántico v0.3.5

## Objetivo
Cerrar la brecha entre una extracción estructuralmente válida y una señal epidemiológica auditable antes de la primera persistencia real.

## Cambios
- `diagnostics` separado de `genomics`.
- `laboratory_investigation` para pruebas en curso.
- `laboratory_location` y `testing_location`; `sampling_location` queda reservado a la toma de muestra.
- Validación determinística: cada `evidence.text` debe ser un fragmento literal y contiguo del `raw_text`, normalizando sólo espacios en blanco.
- Regla de captura completa de itinerarios explícitos.
- `event_matching_eligible` persistido de forma determinística; `official_alert`, `background_context` y `surveillance_baseline` quedan fuera del matching automático.

## Criterio de aprobación
La reextracción MV Hondius debe separar diagnóstico/genómica, usar rol de laboratorio correcto, rechazar evidencias con elipsis y capturar el itinerario explícito sin reinterpretarlo como exposición.
