# Planificación operativa de cohortes v0.4.9

Desde la raíz del repositorio, con `PYTHONPATH` apuntando a `services/worker/src`:

```powershell
& 'C:\Proyectos\OETI\oeti\.venv\Scripts\python.exe' -m onehealth_worker plan-event-creation-cohorts --relation-id 583a2172-9226-4e29-9ec2-8e3dbe982d24 --relation-id 6d1d9f0a-a2f0-48be-9387-48be304515f8 --relation-id cb994680-0281-496e-a0e4-bb3afec3abd3 --output evaluation/reports/cohort-plan.json
```

El comando usa `DATABASE_URL` de Settings y exige al menos un UUID de relación
persistida. `--relation-id` puede repetirse; el planner elimina duplicados.
El informe se imprime como JSON y, opcionalmente, se guarda en el archivo indicado.

Todas las lecturas y dry-runs comparten una conexión y una transacción
`READ ONLY / REPEATABLE READ`. PostgreSQL rechaza escrituras accidentales;
la habilitación de creación del repository permanece en su valor por defecto.
No hay flags de persistencia ni ejecución del matcher o del executor.

El resultado contiene cohortes, seeds, validaciones, relaciones excluidas y
contadores de `ready_to_create`, `already_exists` y `blocked`. Una relación
inexistente propaga un error; no se omite silenciosamente. La disponibilidad
observada no reserva el evento: una ejecución futura debe revalidar en su propia
transacción y contar con autorización. Este comando no habilita creación automática.

Las pruebas cubren argumentos inválidos, ausencia de flags de escritura,
salida JSON, snapshot compartido y la protección efectiva de solo lectura
en PostgreSQL local descartable.

Validación local del 9 de octubre de 2026: 23 pruebas relevantes y 314 pruebas
de regresión aprobadas con PostgreSQL habilitado en el checkout. La regresión
incluye los cambios previos de token usage aún fuera de Git. No se ejecutó el
comando contra Supabase en este paso. El cluster local se detuvo al finalizar.
