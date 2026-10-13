# Diseño del comando de ejecución manual de cohortes

Fecha: 13 de octubre de 2026. Implementado y probado localmente; publicación
y cualquier ejecución productiva pendientes de autorización.

## Interfaz

```text
execute-event-creation-plan --plan-file PATH --event-code CODE [--output PATH] [--execute]
```

El comando consume el mismo informe revisado que `validate-event-creation-plan`.
Sin `--execute` reutiliza la revalidación existente: READ ONLY / REPEATABLE READ,
repository con creación deshabilitada y `dry_run=True`.

Con `--execute`, el caller crea una instancia de repository habilitada para
creación y llama al executor con `dry_run=False`. La habilitación queda limitada
a esa instancia; no se guarda en Settings, variables persistentes ni orquestador.
No se altera `validate-event-creation-plan`, que sigue siempre en solo lectura.

El código esperado selecciona una sola cohorte. El executor comprueba el informe,
IDs y propuesta; el repository reconstruye y revalida todos los datos dentro de
la transacción. El caller no regenera el seed ni crea una transacción externa.

## Resultados

Dry-run: ready_to_create, already_exists o blocked. Ejecución: created,
already_exists o blocked. La salida JSON es la respuesta del repository, con
su dry_run, event ID, reason y trazabilidad disponibles. El archivo de entrada
se conserva; se rechaza el mismo path como salida.

Una escritura puede terminar correctamente aunque falle después la salida a
disco o stdout. Ese fallo no significa rollback de la transacción ya finalizada:
revalidar el mismo informe, sin regenerarlo, permite comprobar already_exists.
No reintentar SQL automáticamente ni ejecutar otra cohorte como compensación.

El estado blocked no se convierte en creación. Los errores de contrato o SQL
se propagan. No agregar attachments, fusiones, cambios de lifecycle ni llamadas
LLM al comando. No conectar creación automática al orquestador.

## Pruebas antes de cualquier ejecución real

1. TDD de argumentos y forwarding: ausencia de flag siempre dry-run; ejecución
   explícita habilita solo la instancia seleccionada.
2. Preservación del informe y coherencia de salida con el resultado del executor.
3. PostgreSQL local: dry-run sin filas, creación exacta de un evento/cinco
   membresías, replay sin cambios, plan obsoleto blocked y rollback parcial.
4. Regresión y selección aislada, con el cluster descartable de memoria reducida.

Implementar y probar localmente el comando no autoriza a ejecutarlo con escritura
contra Supabase. Cualquier ejecución real futura requiere revisar la cohorte y
obtener autorización específica del usuario. La autorización previa de MV Hondius
fue para su primera creación; los replays posteriores se comprobaron solo lectura.

## Estado de partida

Los PR #9 y #10 están integrados: executor validado con 394 pruebas aisladas y
revalidación CLI con 401. El comando agrega acceso manual al write path
existente. No cambia su atomicidad, locks ni guards. La implementación se prueba
con escrituras en PostgreSQL local descartable; no se ejecutó contra Supabase
ni creó commits, tags o publicaciones.
