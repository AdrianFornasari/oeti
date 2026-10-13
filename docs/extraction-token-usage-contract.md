# Contrato de consumo de tokens de extracción

El consumo informado se representa como `dict[str, int] | None`. Las cinco
métricas son `input_tokens`, `cached_input_tokens`, `output_tokens`,
`reasoning_tokens` y `total_tokens`.

- Ausencia de usage, campos ausentes o valores null: no informados, SQL NULL.
- Cero explícito: informado, SQL 0.
- Valores aceptados: enteros no negativos; booleanos, fracciones, cadenas y
  negativos se rechazan sin conversión ni truncamiento.
- Los detalles anidados del provider se mapean a cached/reasoning tokens sin
  completar métricas faltantes ni derivar totales.

`normalize_token_usage()` aplica el mismo contrato al provider y al repository.
El pipeline devuelve el consumo disponible y lo entrega a persistencia. Si
recibió un `ProviderResponse` y falla validación/assembly, registra el consumo
conocido junto con el fallo. Si no recibió esa respuesta, registra NULL. El modo
sin persistencia no registra una ejecución fallida.

Si el provider falla antes de devolver `ProviderResponse` (por ejemplo al parsear
el JSON de extracción), este incremento no recupera métricas del response bruto.
Los registros no representan una estimación ni el costo monetario facturado.

La persistencia requiere las cinco columnas de `extraction_runs`; la migración
local `20261008093000_extraction_run_token_usage.sql` conserva históricos en NULL
y agrega constraints de no negatividad. La inspección de solo lectura del 9 de
octubre de 2026 confirmó las cinco columnas bigint, los cinco constraints
validados y la entrada `20261008093000` en el historial de migraciones de Supabase.
No corresponde reaplicar esa migración allí. No se aplicó DDL en Supabase en
este trabajo; conservar el archivo permite reproducir el esquema en otras bases.

La validación PostgreSQL local usa el DDL relevante de las migraciones en bases
descartables de localhost. Prueba ejecuciones exitosas y fallidas, métricas
completas/parciales/ausentes, históricos y constraints. No cubre RLS ni permisos
productivos. La política de timeout y reintentos está documentada en
[su guía](provider-timeout-retry-policy.md) y se valida con transporte falso.
