# Evaluación exploratoria de corpus congelado

`onehealth_worker.evaluation.exploratory` compara resultados de una corrida
offline con gold provisional del agente. No llama proveedores, carga claves,
lee configuración productiva ni conecta a bases de datos.

```powershell
$env:PYTHONPATH = (Resolve-Path services/worker/src).Path
python -m onehealth_worker.evaluation.exploratory `
  --preregistration '<paquete>/evaluation-preregistration.v1.json' `
  --run-dir '<directorio de una corrida offline>' `
  --output '<archivo nuevo de evaluación.json>'
```

El archivo de salida debe ser nuevo. La función Python evaluate_exploratory
devuelve el reporte sin escribirlo. El CLI puede generar un reporte válido de
una corrida incompleta: consultar **complete**, summary y aggregate para decidir
completitud; que el comando termine no acredita resultados exitosos.

## Integridad y binding

Antes de puntuar verifica hash y ruta del manifiesto derivado, hashes de código
y fuentes mediante el mismo preflight del runner, hashes de todos los gold,
conteos de documentos/señales, case_code e IDs deterministas. Requiere estado
agent_provisional, human_review=false y clasificación exploratoria. No rebindea
silenciosamente un gold a cualquier UUID recibido aunque el gold sea portable.

El reporte de corrida debe identificar el mismo manifiesto y clasificación.
Rechaza documentos repetidos, ajenos o estados desconocidos. Para cada salida
generated verifica el archivo de entrada, su hash y binding, el hash del JSON
de señales, esquema y evidencia literal. Rutas y enlaces resueltos no pueden
escapar de los paquetes correspondientes. El runner ahora registra rutas/hashes
de claims y señales; resultados antiguos sin esos hashes no se puntúan como válidos.

Los hashes dan trazabilidad y detección de alteraciones frente a los registros
comparados; no constituyen una firma de autenticidad de un proveedor externo.

## Métricas, ausencias y fallos

Usa únicamente scorer v0.4.7 y el threshold preregistrado; versiones desconocidas
no caen por defecto en un scorer histórico. No cambia matching ni sus heurísticas.

- Detección macro: F1 medio por documento válido, con peso igual por documento.
- Detección micro: sumar TP, FP y FN antes de calcular precisión, recall y F1.
- Métricas de campos/evidencia: definidas solo con al menos un par emparejado.
  Si no hay pares, son null, no 1.0 como en la convención vacía del scorer legado.
  La media de campos usa documentos con pares y declara ese denominador, junto
  con la cantidad de señales emparejadas. Un campo perfecto en pocos pares no
  compensa falsos negativos de detección.
- Si están evaluados todos los documentos, aggregate contiene las métricas.
  Si hay failed, prepared, missing, invalid_prediction o evaluation_error,
  aggregate=null. conditional_metrics describe solo el subconjunto válido y
  muestra tanto su denominador como el total esperado. Sin documentos evaluados,
  no hay métricas de ningún tipo.
- Un fallo del scorer se registra como evaluation_error, separado de una salida
  de modelo inválida. No se guardan mensajes de excepción que puedan contener
  credenciales. El reporte de corrida original conserva usage y fallos de proveedor.

No se sustituye un fallo técnico por una predicción vacía. Los documentos con
predicciones válidas vacías sí conservan sus falsos negativos. No se omiten
documentos del total esperado ni se sobreescriben evaluaciones anteriores.

## Interpretación

El reporte siempre conserva exploratory_no_independent_review y no habilita
release ni event matching. No se trasladan gates positivos del scorer por
documento a la evaluación exploratoria. La puntuación del extractor no mide
agrupación de eventos y el gold actual H5 no incluye pares del matcher.

Las pruebas usan exclusivamente fixtures sintéticos y proveedores simulados.
El preflight real H5 sobre seis entradas solo preparadas debe informar complete=false,
prepared=6 y métricas null. No es una corrida del modelo ni un resultado de calidad.

Validación inicial 15/10/2026: 16 pruebas del adaptador y 14 del runner; suite
completa de 474 pruebas aprobada en 65,83 s con PostgreSQL local habilitado,
detenido al finalizar. No se ejecutaron llamadas LLM ni escrituras en Supabase.

El conjunto posterior del worker aprobó 588 pruebas locales en 68,08 s, incluidas
las regresiones de ensamblado animal y captura DOM. Esa cifra corresponde a
pruebas de software; no acredita desempeño epidemiológico ni CI remota de estos
cambios. Las seis extracciones H5 autorizadas se conservaron fuera del repositorio,
junto con su primera medición fallida y análisis de desarrollo posteriores.
No se convierten esos análisis incompletos en validación independiente o release.
