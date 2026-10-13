# Diseño: ejecución controlada de una cohorte

Fecha: 13 de octubre de 2026. El servicio descrito está implementado en
`event_creation_executor_v049.py`; su integración operativa por CLI permanece
pendiente. No se habilitaron escrituras productivas.

## Entrada y alcance

La ejecución consume el JSON generado por `plan-event-creation-cohorts`,
seleccionando una cohorte por su `event_code` esperado. Usará el seed del informe
revisado, sin regenerarlo silenciosamente desde una nueva selección de relaciones.
El archivo es una propuesta consultiva: sus datos no reemplazan la validación
actual del repository ni constituyen autorización humana de escritura.

Interfaz propuesta para el servicio:

```python
execute_planned_cohort(*, report, expected_event_code, dry_run=True)
```

`EventCreationExecutor(repository)` recibe un repository ya configurado. Nunca modifica
`event_creation_writes_enabled`; `dry_run=False` requiere que el caller haya
habilitado explícitamente ese repository. La integración de un comando de
escritura se decidirá después de validar este servicio localmente.

Se ejecuta una sola cohorte seleccionada. Si un informe tiene varias, la selección
por código debe ser inequívoca. No se ejecutan las restantes, ni attachments,
ni relaciones nuevas, ni modificaciones de lifecycle.

## Validaciones del adaptador

1. Exigir report de `mode=plan_only`, lista de cohortes y código esperado no vacío.
2. Encontrar exactamente una entrada con seed para el código esperado; rechazar
   códigos ausentes o duplicados y entradas estructuralmente inválidas.
3. Exigir que la validación registrada sea dry-run y `ready_to_create` o
   `already_exists`. Un plan blocked no se convierte en escritura por el adaptador.
4. Comprobar que señales y relaciones del seed coincidan con las de su cohorte
   seleccionada, sin duplicados ni IDs inválidos. El código no alcanza para
   representar la aprobación de cualquier seed.
5. Delegar al repository existente conservando el seed revisado y `dry_run`.

No copiar al adaptador validaciones de contexto, cobertura, equivalencia, locks,
membresías o lifecycle: corresponden a la transacción del repository. El estado
registrado en el informe puede quedar obsoleto; la respuesta actual prevalece.

## Resultado y atomicidad

En dry-run devuelve `ready_to_create`, `already_exists` o `blocked` del repository.
En ejecución devuelve `created`, `already_exists` o `blocked`. Conserva event ID,
código, reason y auditoría disponibles; no introduce un segundo formato de seed.
Un status inesperado es error del contrato, no éxito.

El repository mantiene una transacción por cohorte, sus locks y revalidación.
El adaptador no abre otra transacción de escritura ni hace commits adicionales.
No reintenta errores SQL. Si fallan lock timeout, SQL o inserción de membresías,
propaga el error después del rollback del repository.
Un plan `already_exists` se revalida también en ejecución; no se omite por el
estado del informe ni se reparan filas divergentes.

## TDD y aceptación

- Transporte/repository falso: selección inequívoca, rechazo de planes inválidos,
  preservación del seed, dry-run por defecto y ausencia de habilitación implícita.
- Diferentes estados actuales respecto del informe: prevalece el repository.
- PostgreSQL local: crear un evento con cinco membresías, replay sin cambios,
  plan obsoleto bloqueado y fallo parcial con rollback total.
- Cambiar una señal o membresía después del informe debe bloquear en la
  transacción existente; no usar una autorización derivada del dry-run anterior.
- Suite de regresión antes de selección para commit.

No conectar este servicio al orquestador ni al executor de attachments.
No hacer llamadas LLM ni probar escrituras en Supabase. Cualquier ejecución real
futura requiere selección revisada y autorización específica del usuario.

## Base inspeccionada

`EventCreationPlanner.plan_cohorts()` produce cohort, event_seed y validation.
`EventMatchingRepository.persist_event_creation_cohort()` ya implementa la
transacción necesaria, con dos opciones explícitas para escribir.
`EventAssignmentExecutor` conserva la creación diferida; no debe reutilizarse
su persistencia de attachments para crear eventos.
