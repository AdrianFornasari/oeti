# Registro explícito de una línea de base heredada

Estado: implementación local. La migración 20261102160000 y las adopciones
productivas no se han ejecutado. La migración previa de snapshots sí fue
aplicada por separado a oeti el 02/11/2026.

Esta operación registra el conjunto que ya está vigente; no reemplaza señales
ni acepta científicamente sus afirmaciones. No usa la promoción de candidatos
para adoptar silenciosamente runs históricos.

## Planificación y ejecución

`plan-legacy-snapshot-adoption --raw-item-id UUID --run-id UUID` abre una
transacción repeatable-read de sólo lectura. Exige un run exitoso, heredado
(snapshot_policy nulo), ligado al documento, no vacío, sin promoción anterior
ni head existente. Valida el esquema y la literalidad de la evidencia contra
el texto fuente; exige que todas y sólo sus señales sean el conjunto vigente,
con claves únicas y membresía completa. No infiere identidad entre runs.

Devuelve identificadores, conteos y expected_state_sha256, sin exportar texto
fuente o payloads. La huella abarca el documento, su payload fuente, el run,
las filas completas de señales, sus métricas/evidencias y las filas de
event_signals/signal_relations que tocan sus miembros. No incluye todos los
catálogos ni los detalles de eventos u otras tablas del dominio: es una huella
del estado operativo inspeccionado, no una aceptación integral del contenido.
Normaliza la zona horaria a UTC sólo dentro de la transacción.

`adopt-legacy-snapshot` requiere los mismos IDs, --expected-revision 0,
--expected-state-sha256, --actor, --reason y --execute. Sin --execute el parser
rechaza el comando antes de cargar configuración. Actor es procedencia
declarada, no una identidad autenticada ni una adjudicación científica.

La ejecución bloquea las ocho tablas inspeccionadas en SHARE y el documento
en FOR UPDATE, revalida la elegibilidad y compara la huella revisada. Es una
operación excepcional que puede bloquear escrituras de otros documentos;
lock_timeout es 3 segundos y debe ejecutarse con escritores pausados. Un
timeout o un cambio de estado requiere revisar de nuevo, sin reintentos
automáticos. El lock del documento serializa intentos y promociones.

Si la revisión sigue vigente, inserta head con revisión1 y auditoría en una
misma transacción. El registro lleva operation=legacy_adoption y la huella
revisada. No actualiza ningún run, signal, is_current, versión, supersedes,
revisión, evidencia, métrica o vínculo. Un error al registrar auditoría
revierte también el head. No hay backfill masivo ni elección del run por fecha.

## Auditoría y compatibilidad

La migración agrega operation y baseline_state_sha256 al registro existente.
Las promociones ordinarias mantienen operation=candidate_promotion y huella
nula mediante el default; no cambia su comportamiento. El constraint exige
una huella hexadecimal de64caracteres para legacy_adoption y la prohíbe para
candidate_promotion. Permisos y RLS se conservan.

Los runs heredados mantienen snapshot_policy nulo. El head puede referirlos
sin atribuirles retroactivamente el contrato document-v1. Se preservan también
las revisiones humanas y vínculos existentes: registrar lo que ya existe no
los copia, elimina ni reinterpreta. Una promoción futura sigue bloqueándose
si hay revisiones o vínculos, aunque ya exista el head. Una adopción no permite
reemplazar ni reprocesar el conjunto sin una reconciliación distinta.

## Validación local

Pruebas PostgreSQL sintéticas cubren planificación sin escrituras, conservación
de revisiones/vínculos e historia, cambios posteriores a planificación,
concurrencia, fallo de auditoría, ausencia de migración, rechazo de conjuntos
mixtos/incompletos/fallidos/candidatos/vacíos y permanencia de los bloqueos de
promoción. Pruebas CLI comprueban el --execute requerido y la huella revisada.
Los resultados exactos se registran en los artefactos locales del ensayo.

Publicar o fusionar este cambio no autoriza la nueva migración ni ninguna
adopción productiva. El lanzador fijado al commit anterior se detiene ante
estos cambios locales hasta que se cierre y valide la nueva versión.
