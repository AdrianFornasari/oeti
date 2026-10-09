# Revisión de cierre — Event Persistence v0.4.9

Fecha: 9 de octubre de 2026.

## Resultado y alcance

El núcleo de persistencia de cohortes está validado localmente y cuenta con una
primera ejecución real autorizada: MV Hondius, Event ID
`f3c0aefa-49e9-4553-aa67-ddf5a7cb84f6`, un evento y cinco membresías.
Esto no equivale a publicar una versión ni habilitar creación automática.
No se hicieron commits, merges, push ni cambios de rama.

La revisión de cierre detectó un hueco en el acceso directo al repository:
la cobertura de señales no garantizaba que los pares pertenecieran a una única
cohorte. Se reprodujo con PostgreSQL y se corrigió reutilizando el agrupador
existente después de comprobar el respaldo documental de las anclas. Dos grupos
desconectados sin ancla compartida, o con anclas distintas, ahora devuelven
`blocked / multiple_event_creation_cohorts`, tanto en dry-run como en escritura.
La cohorte MV Hondius mantiene `already_exists` bajo esta validación adicional.
Resultado final de regresión: **303 passed**, con integración PostgreSQL habilitada.
En la revisión final del candidato se agregó la reaplicación del guard de cobertura
y se alcanzaron **307 passed** en el checkout y **304 passed** en la selección
aislada. El repository bloquea cobertura ausente y excepciones inconsistentes
antes de crear o reconocer un evento; MV Hondius mantiene `already_exists`.

## Criterios de aceptación

| Requisito | Evidencia |
| --- | --- |
| Un evento y cinco membresías en una transacción | Prueba PostgreSQL y primera persistencia MV Hondius |
| Rollback total ante fallo parcial | Trigger de prueba que falla en la tercera membresía |
| Idempotencia sin cambios en replay | Comparación de filas y timestamps antes/después |
| Concurrencia sin eventos duplicados | Dos creaciones simultáneas: `created` y `already_exists` |
| Revalidación de señales, relaciones, contexto y versiones | Cambios después del planning bloqueados en transacción |
| Protección de decisiones manuales y otros eventos | Pruebas de membresía manual, `manual_unlinked` y pertenencia externa |
| No reabrir eventos cerrados o resueltos | Lifecycle guards y pruebas de bloqueo |
| Una sola cohorte por evento | Pruebas PostgreSQL de grupos desconectados y anclas distintas |
| Auditoría separada de versiones y fuentes | Rationale por membresía con cinco señales y tres relaciones |
| Dry-run sin escrituras | Snapshots PostgreSQL y conexiones reales `READ ONLY` |
| Planificación reproducible por cohortes | Planner reutiliza agrupador, builder y dry-run del repository |

La suite usa DDL relevante del repositorio en una base local descartable. La
inspección real revisó columnas, constraints, índices, enums, trigger y permisos
de las tablas relevantes. No se ejecutaron migraciones nuevas en Supabase.

## Archivos para revisión

El inventario `evaluation/reports/v049-closure-inventory.json` registra los paths
y hashes del código y las pruebas de eventos v0.4.9, los informes locales y el
estado Git observado. Es una selección para revisión, no una lista autorizada
para staging o commit. No sustituye la revisión de dependencias semánticas.

Los seis JSON de benchmark MV Hondius deben permanecer fuera de staging.
Los cambios previos de extracción, consumo de tokens y frontend se preservaron.
Los archivos de frontend no se modificaron durante este trabajo. La migración
de token usage no pertenece al diseño de persistencia de eventos y no se aplicó
como parte de esta tarea.

## Pendientes para cierre de versión

1. Revisar y delimitar los cambios previos de extracción y semántica de señales
   de los que dependen matcher/policy; separar el trabajo de token usage.
2. Revisar el conjunto final de archivos antes de preparar un commit específico.
   No incluir los seis benchmarks ni frontend por accidente.
3. Decidir por separado la integración de ejecución por cohortes. El orquestador
   actual persiste relaciones y el executor actual ejecuta attachments; ninguno
   habilita automáticamente creación de eventos. El planner nuevo es solo lectura.
4. Revisar capacidad y contención antes de uso sostenido: los locks actuales son
   de tabla, tienen un timeout de cinco segundos y pueden retrasar otras escrituras.
5. Autorizar expresamente commits, merge/push y cualquier nueva escritura real.
   La autorización anterior fue para el evento MV Hondius y sus cinco membresías.

Las dependencias de extracción/semántica quedaron delimitadas en
`docs/event-persistence-v049-dependencies.md`. El parche aislado de 31 archivos
obtuvo 304 passed en su revisión final con PostgreSQL local y conserva únicamente las dos líneas de
hardening de `pipeline.py`, excluyendo tokens/provider/frontend. La revisión de
selección está completada; cualquier staging o commit sigue pendiente de
autorización. Los cambios de token usage y timeout/reintentos del provider
requieren una revisión independiente.
