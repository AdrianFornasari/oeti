# Event Persistence v0.4.9 — validación transaccional

## Alcance

`EventMatchingRepository.persist_event_creation_cohort()` conserva `dry_run=True`
por defecto. Para escribir se requieren ambas opciones explícitas:
`EventMatchingRepository(dsn, event_creation_writes_enabled=True)` y
`persist_event_creation_cohort(event_seed=seed, dry_run=False)`.
No se habilitó esta opción en ningún caller ni configuración de producción.

El dry-run devuelve `ready_to_create`, `already_exists` o `blocked`. La operación
de escritura devuelve `created`, `already_exists` o `blocked`; un fallo SQL se
propaga después de rollback. `ready_to_create` describe datos observados y no
reserva ni autoriza una creación posterior.

La escritura usa una sola conexión y transacción. Antes de validar, adquiere
locks `SHARE ROW EXCLUSIVE` sobre los catálogos, documentos, señales, evidencia,
relaciones, eventos y membresías involucrados. Estos locks bloquean también
escritores ajenos al repository. Luego reconstruye y valida el seed y consulta
membresías actuales antes de insertar un evento y todas sus membresías.
No ejecuta upserts ni reparaciones sobre eventos existentes.

Se utiliza `READ COMMITTED` para obtener una lectura nueva después de esperar
los locks: una creación concurrente puede terminar como `already_exists`.
El tiempo máximo de espera por un lock es cinco segundos. Un timeout o deadlock
causa rollback y se propaga; no hay reintentos automáticos.
La revalidación vuelve a aplicar el guard de baja cobertura v0.4.9 usando las
anclas respaldadas por ambos documentos. No basta con conservar una decisión
`auto_linked` y una versión compatible en rationale: cobertura ausente o una
excepción contextual inconsistente devuelve `blocked / invalid_matcher_policy`.

Esta estrategia es deliberadamente conservadora: los locks son de tabla y
serializan creaciones, además de bloquear temporalmente otras escrituras en
esas tablas. Su costo debe revisarse antes de autorizar uso en producción.

## PostgreSQL local descartable

El cluster de pruebas está fuera del checkout, en
`C:\Proyectos\OETI\local-postgres-tests`, y escucha únicamente en
`127.0.0.1:55449`. Usa el usuario `oeti_test` y autenticación local `trust`;
no contiene datos reales ni credenciales de Supabase. Los binarios provienen
del [distribuidor EDB](https://www.enterprisedb.com/download-postgresql-binaries).

Desde PowerShell, iniciar el cluster:

```powershell
& 'C:\Proyectos\OETI\local-postgres-tests\pgsql\bin\pg_ctl.exe' -D 'C:\Proyectos\OETI\local-postgres-tests\data' -l 'C:\Proyectos\OETI\local-postgres-tests\server.log' -o '-h 127.0.0.1 -p 55449' -w start
```

Desde `C:\Proyectos\OETI\oeti-dev`, ejecutar la suite:

```powershell
$env:PYTHONPATH = (Resolve-Path .\services\worker\src).Path
$env:OETI_LOCAL_PG_TESTS = '1'
& 'C:\Proyectos\OETI\oeti\.venv\Scripts\python.exe' -m pytest services/worker/tests -q -p no:cacheprovider
Remove-Item Env:\OETI_LOCAL_PG_TESTS
```

Cada prueba de integración crea y elimina una base con nombre aleatorio
`oeti_test_*` en ese cluster. El endpoint está fijo en el archivo de pruebas;
no se lee `DATABASE_URL` ni ningún DSN productivo. La suite reproduce desde las
migraciones los enums y las tablas relevantes, sus constraints y los triggers
de `updated_at`. Agrega la columna de elegibilidad desde su migración.
No aplica el esquema Supabase completo, PostGIS, RLS ni permisos productivos.

Detener el cluster después de las pruebas:

```powershell
& 'C:\Proyectos\OETI\local-postgres-tests\pgsql\bin\pg_ctl.exe' -D 'C:\Proyectos\OETI\local-postgres-tests\data' -m fast -w stop
```

## Cobertura y próximo control

Las pruebas cubren un evento con cinco membresías, replay sin cambios,
ausencia de escrituras en dry-run, cambios de elegibilidad y vigencia,
relaciones invalidadas, versiones incompatibles, contexto sin respaldo,
membresías manuales y en otros eventos, lifecycle cerrado, rollback por fallo
de la tercera membresía, creaciones concurrentes y un escritor externo
bloqueado mientras se validan las señales.

El 9 de octubre de 2026 se inspeccionaron mediante lecturas el esquema y permisos
aplicados en Supabase y se ejecutó el dry-run real de MV Hondius. La transacción
fue `READ ONLY` y `REPEATABLE READ`; devolvió `ready_to_create` para el código
`OETI-EVT-e3aa17f0-c789-5315-9dc8-ef7833697c06`, cinco señales y tres relaciones.
El esquema observado conserva `events.event_code UNIQUE` y la PK compuesta
`event_signals(event_id, signal_id)`, sin unicidad global sobre `signal_id`.

La validación reveló que los arrays de enums PostgreSQL se devolvían como texto
y `_as_list` los interpretaba como listas vacías. Se corrigieron las proyecciones
de dominios de creación/equivalencia con `to_jsonb`, tras reproducir el fallo en
la prueba PostgreSQL. El seed real conserva ahora `genomic` y `human`.
Después de la corrección, la suite completa con integración obtuvo 289 passed.

El informe está en `evaluation/reports/mv-hondius-v049-read-only.json`, generado
por `services/worker/scripts/verify_mv_hondius_v049.py`. Contiene el seed y las
cinco membresías previstas, metadatos del esquema y auditoría, sin credenciales
ni textos completos. La escritura revalida todos los datos dentro de su propia
transacción: el resultado del dry-run no es una reserva.

## Primera persistencia autorizada — MV Hondius

El 9 de octubre de 2026 el usuario autorizó expresamente crear este evento y
sus cinco membresías en Supabase. La operación devolvió `created`:

- Event ID: `f3c0aefa-49e9-4553-aa67-ddf5a7cb84f6`.
- Event code: `OETI-EVT-e3aa17f0-c789-5315-9dc8-ef7833697c06`.
- Un evento y cinco membresías; dominios `genomic` y `human`.
- Trazabilidad conservada hacia las cinco señales y las tres relaciones.

Se usó el seed del informe revisado y se revalidó en la transacción de escritura.
Después del commit, una conexión `READ ONLY / REPEATABLE READ` comprobó un único
evento y el conjunto exacto de cinco membresías. El replay mediante dry-run
devolvió `already_exists` con el mismo Event ID, validando también la equivalencia
de campos y auditoría. No se ejecutó una segunda operación de escritura.

El informe posterior está en
`evaluation/reports/mv-hondius-v049-persistence.json`: conserva el resultado,
las filas persistidas, la autorización y la verificación. La habilitación de
escrituras se limitó a la instancia de esta ejecución; el valor por defecto del
repository y los callers productivos no cambiaron. No se hicieron commits.

## Integración de planificación por cohortes

`EventCreationPlanner.plan_cohorts(signal_relation_ids)` carga relaciones
persistidas, elimina IDs de entrada duplicados, excluye relaciones no elegibles
y reutiliza `build_event_creation_cohorts()` y `build_event_creation_cohort_seed()`.
Cada cohorte pasa por `persist_event_creation_cohort(dry_run=True)`. El informe
conserva las relaciones excluidas, el seed, la validación y un resumen de
`ready_to_create`, `already_exists` y `blocked`.

Una señal que deja de ser elegible bloquea su cohorte sin impedir la evaluación
de las otras. Una relación solicitada que ya no existe propaga el error del
repository; no se omite silenciosamente. La entrada por pares se conserva.
El método nuevo no habilita escrituras ni modifica el orquestador o el executor
de attachments. La creación automática permanece sin conectar.

La comprobación real, realizada dentro de una transacción de solo lectura,
produjo una cohorte MV Hondius y `already_exists` para el Event ID persistido.
Se conservó el informe anterior de creación. El resultado del planner está en
`evaluation/reports/mv-hondius-v049-cohort-planner.json`.
