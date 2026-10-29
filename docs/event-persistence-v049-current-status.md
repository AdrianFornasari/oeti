# Estado de Event Persistence v0.4.9

Estado histórico de los PR #5, #6 y #7: 13 de octubre de 2026.
Disponibilidad del comando manual contrastada con el código: 29 de octubre de 2026.

## Resultado integrado

El objetivo de persistir un evento y todas las membresías de una cohorte en
una única transacción está completado e integrado en `main`.

| Entrega | Commit de implementación | Merge en main |
| --- | --- | --- |
| [PR #5: persistencia transaccional](https://github.com/AdrianFornasari/oeti/pull/5) | `9ddc270` | `a426372` |
| [PR #6: comando de planificación de solo lectura](https://github.com/AdrianFornasari/oeti/pull/6) | `8a30239` | `8c620cb` |
| [PR #7: consumo de tokens y reintentos del provider](https://github.com/AdrianFornasari/oeti/pull/7) | `e725c88` | `c49cfa8` |

La persistencia reconstruye y revalida el seed desde datos actuales, exige una
única cohorte, comprueba contexto documental, versiones y política de cobertura,
protege membresías manuales y pertenencia a otros eventos, y respeta lifecycle.
La transacción garantiza rollback total y replay equivalente sin modificaciones.

`plan-event-creation-cohorts` reutiliza el planner en una única transacción
`READ ONLY / REPEATABLE READ`, genera JSON y no ofrece flags de escritura.
Su uso está en [la guía del comando](event-cohort-planning-command-v049.md).

## Evidencia

- Persistencia: 304 pruebas en selección aislada con PostgreSQL local.
- Comando: 311 pruebas en selección aislada; 23 pruebas relevantes.
- Tokens/provider: 364 pruebas en selección aislada con PostgreSQL local,
  completadas el 13 de octubre. Incluyen la regresión de las entregas anteriores.
- GitHub no registró statuses ni check runs en los controles previos a los tres
  merges; las cifras anteriores corresponden a validación local, no a CI.
- Ejecución real expresamente autorizada: MV Hondius, Event ID
  `f3c0aefa-49e9-4553-aa67-ddf5a7cb84f6`, un evento y cinco membresías.
- Verificaciones posteriores de solo lectura, incluida la ejecución real del
  comando, devuelven `already_exists` para ese mismo evento.

Los informes de ejecución y selección permanecen locales en `evaluation/reports`;
no forman parte de los commits. Este trabajo no aplicó migraciones en Supabase.
La inspección de solo lectura del 9 de octubre confirmó que la migración de
tokens `20261008093000` ya figuraba en el historial, con sus cinco columnas bigint
y constraints validados. Su archivo se incorporó en el PR #7 para reproducibilidad.

El consumo ausente se conserva como NULL; las métricas informadas deben ser
enteros no negativos. El pipeline conserva el consumo conocido cuando falla
validación después de recibir una respuesta. Ver [el contrato de tokens](extraction-token-usage-contract.md).
El provider reintenta únicamente errores de conexión, hasta tres intentos;
lectura, escritura y otros errores de transporte no repiten la solicitud.
Ver [la política de timeout y reintentos](provider-timeout-retry-policy.md).

## Límites y trabajo posterior

El cierre corresponde al núcleo de persistencia y su planificación operativa.
No se publicó un tag de versión ni se habilitó creación automática.
El orquestador persiste relaciones; el executor de assignment ejecuta attachments
y mantiene diferida la creación. El checkout actual sí incluye
`EventCreationExecutor` y el comando manual `execute-event-creation-plan`.
Sin `--execute`, el comando revalida en `READ ONLY / REPEATABLE READ` y con
`dry_run=True`. Con ese flag habilita escrituras sólo en la instancia del
repository creada para esa invocación. No habilita creación automática.
Ver [el diseño del comando manual](event-cohort-manual-execution-command-design.md).

Esta comprobación fue estática: no se ejecutó el comando ni se consultó la DB
el 29 de octubre. Su presencia en código no acredita permisos, estado operativo
de una base actual ni autorización para escribir. Incluso el modo de lectura
necesita conexión a DB; no confundirlo con una comprobación sobre archivos offline.

Los locks de creación son de tabla, con timeout de cinco segundos, y pueden
retrasar otras escrituras. Las pruebas locales no reproducen RLS, PostGIS ni
todos los permisos productivos. Revisar estos aspectos antes de uso sostenido.

Frontend y los seis benchmarks protegidos permanecen fuera de estas entregas.
Los cambios de tokens y timeout/reintentos ya se integraron mediante el PR #7.
El consumo no se recupera si el provider falla antes de devolver ProviderResponse;
los timeouts por fase no constituyen un plazo global de ejecución.
El checkout se mantiene en la rama de desarrollo original;
actualizar referencias remotas no cambió esa rama ni los archivos pendientes.

La ejecución explícita de una cohorte y su acceso manual por CLI ya están
implementados en este checkout; no corresponde desarrollarlos de nuevo a partir
de la nota histórica. Antes de cualquier uso futuro hay que revisar el informe,
la cohorte seleccionada y el entorno, y obtener autorización específica para
escritura. La implementación y validación local no autorizan nuevas escrituras
reales, commits ni publicación, ni su conexión automática al orquestador.

Los documentos de validación, selección de dependencias y revisión de cierre
conservan su cronología previa. Este archivo es la referencia del estado posterior
a los merges y sustituye sus menciones de commits o staging pendientes.
