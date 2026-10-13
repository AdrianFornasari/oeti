# Revalidar una cohorte de un informe revisado

Desde la raíz del repositorio, con PYTHONPATH apuntando a services/worker/src:

```powershell
& 'C:\Proyectos\OETI\oeti\.venv\Scripts\python.exe' -m onehealth_worker validate-event-creation-plan --plan-file evaluation/reports/mv-hondius-v049-command-plan.json --event-code OETI-EVT-e3aa17f0-c789-5315-9dc8-ef7833697c06 --output evaluation/reports/mv-hondius-v049-revalidation.json
```

El comando lee un informe `plan_only`, exige exactamente una cohorte con el
código esperado, conserva su seed y reutiliza `EventCreationExecutor` para
obtener el estado actual: `ready_to_create`, `already_exists` o `blocked`.
El informe original no autoriza ni reserva una creación futura.

Todas las consultas y la validación comparten una conexión y transacción
`READ ONLY / REPEATABLE READ`. El repository conserva deshabilitada la creación,
y el executor se invoca siempre con `dry_run=True`. No hay flags de escritura.
El snapshot es consistente durante la invocación; puede quedar obsoleto después.

La salida se imprime como JSON y se puede guardar con `--output`. Se rechaza
el mismo path para entrada y salida, para preservar el informe revisado.
Un plan bloqueado, mal formado, con selección ambigua o código inexistente no
se ejecuta; los errores se propagan. El status actual blocked es un resultado
de validación, no un error de transporte. El comando no modifica señales,
eventos, membresías ni el informe de entrada.

No conecta creación automática ni agrega un comando productivo de escritura.
Pruebas locales verifican forwarding, protección del archivo de entrada,
ausencia de flags de ejecución y el bloqueo real de un plan obsoleto.
