# Integración continua del worker

El workflow `.github/workflows/worker-tests.yml` ejecuta la suite completa en
pull requests hacia `main`, pushes a `main` y ejecuciones manuales. No usa filtros
por ruta para que los checks puedan exigirse en todos los PR.

La matriz cubre Python 3.12 (mínimo declarado) y 3.13 (runtime local validado).
Cada job instala el paquete con el extra `test` y levanta PostgreSQL 18.6 en
`127.0.0.1:55449`, usuario `oeti_test`, con autenticación trust exclusivamente
para el servicio descartable del runner. No requiere secretos, Supabase ni LLM.
Las acciones están fijadas por SHA; las dependencias Python conservan los rangos
del paquete, por lo que esto no constituye un entorno con lockfile completo.

`OETI_LOCAL_PG_TESTS=1` activa las dos suites de integración existentes. Cada
fixture crea y elimina una base `oeti_test_*`. Si el servicio no está disponible,
las pruebas fallan; no se omiten. Un control del JUnit también exige al menos una
prueba ejecutada y cero omisiones, sin fijar un número que impida ampliar la suite.
Los fixtures aplican DDL relevante; no validan toda la instalación de Supabase,
sus políticas RLS ni PostGIS.

Reproducción desde la raíz con el PostgreSQL descartable ya iniciado:

```powershell
$env:OETI_LOCAL_PG_TESTS = '1'
$env:PYTHONPATH = (Resolve-Path .\services\worker\src).Path
python -m pytest services/worker/tests -q --tb=short --junitxml=worker-tests.xml
```

Al publicar el workflow, comprobar ambos jobs en GitHub. Después se podrán
configurar como checks obligatorios en la protección de `main`; agregar este
archivo no modifica esa protección. La primera ejecución remota queda pendiente
hasta publicar el cambio. No se incluyen despliegues ni escrituras de producción.

Referencia del servicio: [documentación de GitHub](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers).
