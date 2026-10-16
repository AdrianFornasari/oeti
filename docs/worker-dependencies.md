# Dependencias reproducibles del worker

El paquete mantiene sus rangos compatibles en pyproject.toml. Para CI y entornos
reproducibles se añaden requirements-test.lock (runtime + extra test) y
requirements-build.lock (backend de construcción declarado en requirements-build.in).
Ambos archivos fijan versiones y hashes SHA-256 de distribuciones permitidas.
No incluyen el propio worker ni rutas, credenciales o paquetes del venv compartido.

## Instalación en entorno nuevo

Desde la raíz, con Python 3.12 o 3.13 en un venv nuevo y pip disponible:

```powershell
python -m pip install --require-hashes --only-binary=:all: -r services/worker/requirements-test.lock -r services/worker/requirements-build.lock
python -m pip install --no-deps --no-build-isolation -e ./services/worker
python -m pip check
```

La instalación del worker usa el backend ya fijado y evita resolver otras
dependencias. --only-binary=:all: evita construir dependencias descargadas desde
sdist; si no hay wheel compatible para una plataforma, falla en vez de compilar
con herramientas distintas. Los hashes no sustituyen revisión de dependencias.
No es una auditoría de vulnerabilidades ni prueba de seguridad de cada paquete.

## Generación y actualización explícitas

Se generaron con uv 0.13.1, instalado en herramientas descartables fuera del repo.
Para regenerar con esa versión, sin modificar el entorno compartido, ejecutar:

```powershell
uv --no-config --no-python-downloads pip compile services/worker/pyproject.toml --extra test --universal --python-version 3.12 --generate-hashes --no-header --no-annotate --default-index https://pypi.org/simple --output-file services/worker/requirements-test.lock
uv --no-config --no-python-downloads pip compile services/worker/requirements-build.in --universal --python-version 3.12 --generate-hashes --no-header --no-annotate --default-index https://pypi.org/simple --output-file services/worker/requirements-build.lock
```

uv reutiliza pins existentes al regenerar. Una actualización deliberada puede
usar --upgrade-package NOMBRE; revisar el diff y volver a probar en entorno nuevo.
La primera resolución se sembró con versiones del runtime ya probado, excluyendo
pip y las entradas obsoletas de metadata del worker. Esas restricciones temporales
no forman parte del contrato de regeneración: los locks conservan los pins.
El backend quedó fijado a setuptools 84.0.0. No se cambió pyproject.toml.
Si cambia el backend o sus requisitos declarados, actualizar también el input
requirements-build.in y su lock. Actualizar locks cuando cambien dependencias.

## Alcance validado

Resolución universal con Python >=3.12 como límite inferior; eso no equivale a
haber probado cada plataforma o versión futura de Python. El resolver local usó
Python 3.13.8 para metadata/build porque no hay intérprete 3.12 local.
Windows/Python 3.13.8: entorno nuevo instalado desde locks con hashes, worker
editable 0.4.9 sin resolver dependencias y comprobación de compatibilidad aprobada.
Linux/Python 3.12 y 3.13: verificar instalación y suite en los jobs del PR.

CI conserva Ubuntu 24.04, PostgreSQL 18.6 y las acciones existentes. El lock no
congela el runner, intérprete, pip ni bibliotecas del sistema. No añade uv a CI.
Las capturas y freezes de evaluaciones anteriores quedan intactos; estos locks
no acreditan retroactivamente que aquellas corridas usaran el entorno nuevo.

Referencia del resolver: https://docs.astral.sh/uv/pip/compile/
