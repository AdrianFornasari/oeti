# Política adoptada: conjuntos completos de extracción por documento

Decisión del usuario: 02/11/2026. Este contrato reemplaza la interpretación de
las extracciones automáticas como actualizaciones parciales por clave local.
Estado: implementación local preparada y probada en PostgreSQL desechable.
Migración productiva, publicación y despliegue todavía no aplicados.

## Unidad de vigencia

Cada run exitoso conserva su resultado completo e inmutable como candidato.
Un run exitoso no equivale a una promoción ni a aceptación científica.
Un documento tendrá como máximo un conjunto automático promovido vigente.
Las señales elegibles del conjunto pertenecen al mismo documento y run; no se
mezclan señales vigentes de extracciones diferentes por conservar claves ausentes.

Los runs, señales, evidencia, métricas y decisiones previas se conservan como
historia. Retirar vigencia técnica no borra hechos fuente ni los refuta.
La política no activa modelos ni autoriza reprocesar documentos históricos.

## Promoción explícita

La promoción recibe documento, run candidato y el identificador de la promoción
vigente esperada. Validará que el candidato esté completo y exitoso y que sus
señales pertenezcan al documento. Guardar un resultado no lo promueve por sí solo.

Una transacción serializa promociones del mismo documento y comprueba la versión
esperada: si otro actor ya cambió la vigencia, se rechaza el intento obsoleto.
No se elige ganador por hora del proveedor, ordinal o finalización de descarga.

La promoción retira la vigencia del conjunto automático anterior, activa todo el
nuevo conjunto y registra la transición y su procedencia en la misma transacción.
Un fallo en cualquier paso conserva la vigencia anterior completa. El registro
de promoción debe ser distinto de warnings y de decisiones científicas.

## Revisión humana y vínculos

No se copian, eliminan o reinterpretan revisiones, membresías de eventos o
relaciones para hacer coincidir el nuevo resultado. Un conjunto anterior con
revisión humana o vínculos persistidos exige reconciliación explícita antes de
su reemplazo; la promoción normal se bloquea, sin dejar un conjunto mezclado.

La primera implementación será conservadora y bloqueará también los vínculos
persistidos cuyo carácter automático/manual no pueda establecer inequívocamente.
La reconciliación se diseñará por separado; no se supone que aprobar esta política
autorice a migrar revisiones, eventos o relaciones existentes.

## Resultado vacío

Un candidato vacío se conserva como resultado de extracción y no promueve ni
retira señales anteriores automáticamente. Requiere una confirmación explícita
separada para promover un conjunto vacío. Esa confirmación no significa «cero
casos» ni evidencia negativa: sólo define el conjunto técnico promovido.
No se habilitará promoción vacía en el primer cambio sin ese mecanismo definido.

## Identidad y sucesión

local_signal_id/asm-NN es una referencia local de la salida, no identidad estable
de un hecho. Reordenar señales no autoriza una cadena semántica de supersedes.
Las filas históricas no se reutilizan para otro hecho por tener el mismo ordinal.

La nueva representación identificará cada señal dentro de su run. Una eventual
correspondencia entre hechos de runs distintos será un vínculo explícito, con
criterio y procedencia propios. No se infiere por cifra, ordinal o posición.
El caso de misma clave y payload equivalente tampoco debe elevarse a una garantía
general de identidad semántica para cualquier reextracción.

## Transición del almacenamiento y consumidores

La migración 20261102120000 agrega snapshot_policy a los runs, un head con revisión
por documento y un registro de promociones. No promueve runs históricos ni cambia
sus señales. persist_extraction guarda candidatos con is_current=false. version
es sólo una secuencia de almacenamiento y supersedes_signal_id queda null en
filas nuevas; no se infiere sucesión semántica por clave local.

La promoción cambia is_current del conjunto completo, head y registro en una sola
transacción, bajo lock del documento. Las consultas existentes que exigen
is_current no reciben los candidatos almacenados. No se usa warnings para guardar
estado de promoción. En las tablas nuevas RLS queda habilitado; anon/authenticated
no reciben acceso y service_role no recibe UPDATE/DELETE del registro de
promociones. Esto no impide modificaciones por un administrador propietario.

Los documentos con vigencia antigua mezclada se identificarán para conciliación,
sin seleccionar silenciosamente un run histórico como ganador. La ruta antigua
no debe seguir promoviendo implícitamente una mezcla tras habilitar la política.
Cambio de contrato: persist-extraction y extract-raw-item con persistencia guardan
un candidato, no lo promueven. persisted=true sólo significa almacenamiento;
promoted=false lo explicita. Debe aplicarse la migración antes de desplegar el
código. Un despliegue sin esa migración falla, no vuelve al comportamiento antiguo.

## Operación explícita

El método ExtractionRepository.promote_extraction_snapshot y el comando
promote-extraction-snapshot reciben raw_item_id, run_id, expected_revision, actor y
reason. Revisión esperada0 significa que aún no hay promoción; no habilita adoptar
señales legacy. La revisión se obtiene consultando extraction_snapshot_heads.
actor es procedencia declarada por el operador, no autenticación de una revisión.

Ejemplo con valores a sustituir, no ejecutado contra producción:

```powershell
python -m onehealth_worker promote-extraction-snapshot `
  --raw-item-id "<uuid-del-documento>" --run-id "<uuid-del-candidato>" `
  --expected-revision "<revision-vigente>" --actor "<operador>" `
  --reason "<fundamento-de-promocion>" --execute
```

Sin --execute el parser rechaza el comando antes de cargar configuración. No hay
promoción automática al guardar. Un run ya promovido no se promueve de nuevo;
un intento con revisión obsoleta se rechaza. No se habilita promoción de vacíos
ni reconciliación legacy en este cambio. No se migran eventos/relaciones/revisiones.

## Orden de habilitación futura

Antes de habilitar promociones deben detenerse/drenarse los escritores con la
implementación anterior. Esos procesos no respetan el nuevo lock ni el contrato
de candidatos y no deben coexistir como escritores de vigencia con el nuevo flujo.
Aplicar la migración y desplegar todos los escritores compatibles, manteniendo
la promoción como operación manual. Después revisar qué documentos necesitan
conciliación legacy; no habilitar un backfill automático.

Un rollback de código no debe reactivar sin revisión los escritores antiguos,
porque volverían a promover por ordinal. Este documento no ejecuta ese rollout
ni una reversión productiva. Las operaciones y conciliaciones necesitan su
autorización específica.

## Criterios de aceptación de la implementación

| Caso sintético | Resultado exigido |
| --- | --- |
| Guardar candidato | Historia conservada; no cambia el conjunto promovido |
| Reducir de dos señales a una y promover | Sólo el nuevo conjunto automático queda vigente |
| Reordenar dos hechos | No se crea correspondencia semántica por ordinal |
| Candidato vacío sin confirmación | No cambia vigencia anterior |
| Fallo en candidato o promoción | Rollback de la transición completa |
| Fuente o run ajenos | Rechazo antes de cambiar vigencia |
| Revisión humana o vínculo existente | Bloqueo y conservación exacta de decisiones/vínculos |
| Dos promociones con la misma base esperada | Una gana; la otra se rechaza como obsoleta |
| Consulta de candidatos para matching | No mezcla señales de runs distintos como un snapshot |
| Historia legacy mezclada | Se informa pendiente de conciliación, sin promoción automática |

Se ejecutaron pruebas PostgreSQL dedicadas de candidatos, reducción,
reordenamiento, vacíos, revisión, vínculos, rollback, concurrencia y aislamiento de
documentos, además de CLI y persistencia/tokens. La suite completa del worker pasó
1227 pruebas en el primer cierre; la selección final valida además permisos y dos
casos añadidos de runs históricos/fallidos. Los resultados exactos se conservan
en XML locales, sin atribuir esos conteos a CI o producción.

No cambian corpus, gold, prompt o umbrales. Publicación, migraciones productivas y
despliegue requieren sus alcances autorizados. PR #38 sigue fuera de esta entrega.
