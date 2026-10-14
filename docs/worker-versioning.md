# Versión del paquete y configuración de modelo

La versión del paquete worker es `0.4.9`, definida únicamente en
`services/worker/src/onehealth_worker/__init__.py`. Setuptools la lee mediante
`project.dynamic` y `tool.setuptools.dynamic.version` al construir o instalar
el paquete. Los directorios `*.egg-info/` son generados y quedan fuera de Git.
Tras actualizar un checkout, reinstalar el paquete para actualizar sus metadatos:

```powershell
python -m pip install -e './services/worker[test]'
```

Esta versión identifica el paquete completo. Las versiones de prompt, extractor,
schema, matcher, context resolver y policy identifican contratos diferentes y no
se derivan de ella. Se conservan los identificadores históricos en reportes y
registros persistidos. Para reproducir una ejecución se necesita además el SHA
del commit y la configuración utilizada; `0.4.9` por sí solo no identifica todos
los cambios realizados durante esta etapa.

El modelo por defecto es `gpt-5.4-mini`, coherente con `.env.example`. Es un
default de configuración, no una conclusión de evaluación comparativa de modelos.
`LLM_MODEL` y la opción CLI `--model` mantienen sus overrides. Una instalación
que no configuraba modelo pasa a este default; una con override lo conserva.
Este cambio no realiza llamadas al proveedor ni modifica extracciones previas.

Referencia: [metadatos dinámicos de setuptools](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html#dynamic-metadata).
