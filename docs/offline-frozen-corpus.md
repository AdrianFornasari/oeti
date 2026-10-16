# Runner de corpus congelado sin base de datos

El módulo `onehealth_worker.evaluation.offline` prepara entradas directamente
desde archivos congelados. No instancia Settings, no carga claves ni consulta
repositorios o Supabase. Se invoca como módulo separado del CLI principal,
porque aquel construye Settings con DATABASE_URL.

```powershell
$env:PYTHONPATH = (Resolve-Path services/worker/src).Path
python -m onehealth_worker.evaluation.offline `
  --manifest 'C:\Proyectos\OETI\holdout-h5-preparation-2026-10-14\source-freeze.json' `
  --output 'C:\Proyectos\OETI\local-postgres-tests\h5-plan-nuevo'
```

El modo de consola es únicamente `prepare_only`: no tiene opción para llamar
al LLM. Verifica todos los documentos y los hashes de código suministrados
antes de crear salidas. Requiere un directorio nuevo fuera del paquete de fuentes;
no sobrescribe resultados ni ofrece force/resume. No interpreta ni descarga URLs.

## Contrato de entrada

El manifiesto requiere case_code y una lista no vacía de documents. Cada entrada
incluye document_id único, title, requested_url, declared_page_date (fecha diaria
o null), evaluation_input_path relativo al manifiesto y evaluation_input_sha256.
Se rechazan rutas que salen del paquete, incluso tras resolver enlaces, y archivos
duplicados. Se compara el hash de los bytes antes de decodificar UTF-8; no se
normalizan silenciosamente saltos de línea. La metadata de publicación no se
convierte en fecha del hecho. Una fecha desconocida se pasa como unknown.

proposed_run.evaluation_scope fija el scope antes de generar entradas.
proposed_run.model es una declaración de intención; no acredita qué modelo
utilizaría un proveedor inyectado. code_freeze.files, cuando está presente,
verifica rutas y SHA-256 relativos al checkout actual. El manifiesto de origen
se conserva sin modificaciones.

## Salidas y reproducibilidad

El directorio nuevo contiene `001.input.txt`, etc. y `report.json`. El reporte
registra hash del manifiesto, runner, fuentes y entradas, IDs UUID5 deterministas,
versión de Python, archivos de código verificados y estado por documento.
Los IDs son locales a la evaluación: no son UUIDs de raw_items persistidos.
Cambiar fuente, metadata o scope cambia el binding. Esto no constituye un lockfile
de dependencias ni un registro automático del SHA Git de cada ejecución.

## Interfaz de extracción probada con proveedor simulado

La función Python `run_frozen_corpus` acepta execute=True únicamente junto con
un proveedor inyectado explícitamente. Se usa en pruebas con respuestas simuladas.
El valor por defecto no llama al proveedor aunque se le haya pasado uno.
No se conecta el proveedor OpenAI ni se lee su clave desde este módulo.

Al procesar una respuesta, usa la misma secuencia de producción:
atomic claims -> validación de esquema y binding/evidencia literal ->
assembly_v046 -> normalización -> signal_semantics_v049 -> validación del
esquema de señales, binding y evidencia literal. No cambia prompts, reglas,
umbrales ni semántica de esos componentes. El antiguo extractor de corpus
basado en DB se conserva separado y usa otra versión histórica de assembly.

Guarda claims originales antes de validar y señales solo si pasan los controles.
Si hay un fallo posterior a la respuesta, conserva response_id y usage conocido.
Un fallo de proveedor previo a respuesta deja usage=null; no inventa ceros ni
costos. Registra tipo y fase del error, sin mensajes de transporte que pudieran
contener credenciales. Continúa los otros documentos y conserva reporte parcial
después de cada uno; no omite fallos de la cuenta final. No agrega reintentos.
Registra además rutas y hashes de claims y señales para que el adaptador
exploratorio pueda verificar las salidas antes de puntuarlas.
Los reintentos internos de un futuro proveedor siguen siendo responsabilidad
de ese proveedor y deben quedar incluidos en la autorización/presupuesto.

## Límite opcional de salida del proveedor

El constructor `OpenAIResponsesProvider` acepta `max_output_tokens=None` o un
entero positivo. Con None omite el parámetro y conserva el comportamiento de
los llamadores existentes. Al inyectar un proveedor con, por ejemplo,
`max_output_tokens=8192`, envía ese valor a Responses API. No se agrega una
variable de entorno ni se modifica el CLI de preparación.

El límite incluye los tokens visibles y los de razonamiento/formato no visibles,
según la [documentación oficial de OpenAI](https://developers.openai.com/api/docs/guides/reasoning#controlling-costs).
Es un límite por respuesta, no un tope monetario para el corpus. Si la API
devuelve status=incomplete, el proveedor conserva su rechazo de esa respuesta:
no acepta JSON parcial ni aumenta el límite ni reintenta la inferencia. Puede
haber consumo facturado aun sin salida utilizable; en el reporte del runner
usage permanece desconocido cuando el proveedor no llega a retornar respuesta.

Si el proveedor está incluido en un freeze previo, su modificación invalida ese
freeze para ejecutar con el código actual. Se prepara una revisión vinculada
antes de predicciones, conservando el manifiesto y registro previos originales,
las fuentes, scope, bindings y gold. El límite efectivo debe constar en la
configuración del proveedor realmente inyectado: el runner no lo impone por
leer una declaración del manifiesto.

## Compatibilidad de tipos de hospedador

El contrato de claims admite `subject_type=animal`, mientras que el esquema de
señales admite human, domestic_animal, wildlife, vector y other. El ensamblador
común convierte el animal genérico a `host_type=other`, conservando verbatim,
canonical_name y confidence. No deduce condición doméstica o silvestre del tipo
genérico ni agrega normalización taxonómica. Human, wildlife y vector conservan
su comportamiento; los sujetos no hospedadores siguen excluidos de hosts.
La entrada de claims no se modifica.

La incompatibilidad se detectó en la primera corrida H5. Se preservó el código
congelado de esa corrida antes de corregirlo. La aplicación del arreglo a sus
respuestas guardadas se registra como análisis de desarrollo posterior, sin
nuevas llamadas al modelo y sin sustituir la medición inicial. Los errores de
evidencia literal siguen rechazándose con las mismas reglas. H5 deja de servir
como evaluación independiente del desarrollo posterior que utiliza este caso.

## Clasificación de la evaluación

Los reportes se etiquetan `exploratory_no_independent_review`. El usuario
autorizó continuar con adjudicación del agente el 15 de octubre de 2026.
No se declara revisión humana ni validación independiente. Antes de una primera
corrida real faltan gold provisional, métricas/configuración preregistradas y
autorización específica de LLM. Si luego se ajusta con el corpus, pasa a ser
corpus de desarrollo, conservando la primera medición.

## Guardas conservadoras para claims animales

La preparación del ensamblador v0.4.6 aplica dos guardas sobre una copia de claims
y agrega warnings auditables; los archivos originales del proveedor no cambian.

- Un diagnostic_result animal positivo y confirmado pasa a outbreak_update solo
  cuando su evidencia textual confirma explícitamente un brote o una detección
  focal de población animal en un establecimiento, tiene una única
  localidad del evento resuelta y no presenta negación/incertidumbre ni período
  histórico explícito. Se conservan los datos diagnósticos. Un positivo aislado,
  un resultado humano o una localidad de laboratorio no bastan. No se separan
  automáticamente claims con múltiples localidades ni se inventan recuentos.
- Una wildlife_presence_absence negativa referida exclusivamente a un inventario
  cero de granjas, con sujeto other y sin prueba diagnóstica/secuenciación, se
  excluye de las señales cuando la evidencia dice que no existen esas granjas.
  La regla tiene vocabulario acotado; no pretende cubrir todas las instalaciones.
  No elimina declaraciones de ausencia de brotes/infección, resultados negativos
  ni sujetos biológicos. Ausencia de establecimientos no equivale a ausencia
  de patógenos o fauna.

Estas guardas usan campos estructurados y evidencia, no resúmenes generados ni
nombres de localidades/enfermedades de H5. Se probaron con ejemplos sintéticos
positivos y contraejemplos. La validación literal ocurre antes de la preparación
en el pipeline; no se usa la guarda para aceptar evidencia inválida.
La evaluación posterior de respuestas H5 guardadas sigue siendo análisis de
desarrollo y conserva gold, umbral, primera medición y replays anteriores.

### Política operativa de detección focal en establecimientos

La representación `outbreak` se usa también para una detección confirmada que la
fuente ubica en una población animal de un establecimiento. Esto es una decisión
del contrato de representación de OETI; no afirma que se hayan demostrado umbrales
epidemiológicos de brote ni implica una clasificación sanitaria oficial.

Además de los controles anteriores de positividad/confirmación, dominio animal,
localidad única y ausencia de incertidumbre o período histórico explícito, esta
vía exige subject_type=animal y un sujeto de población, con vocabulario acotado
de grupos animales. Su verbatim debe aparecer en la misma oración de evidencia
que la confirmación/detección de un caso positivo, un establecimiento singular
explícito y la localidad del evento. Se admite una colección de animales aunque
la fuente reporte un caso: no se transforma ese caso en cantidad de aves/animales.

La localidad completa debe estar vinculada a la cláusula del establecimiento,
mediante una construcción locativa admitida (por ejemplo, «un predio de A» o
«un establecimiento situado en A»). No basta que aparezca en otra cláusula de
la misma oración. Se rechazan nombres que solo coincidan por prefijo y apartes
entre rayas que introduzcan otra ubicación. Los apartes de listas animales sin
información locativa pueden omitirse solo para comprobar ese vínculo; su texto
original sigue conservado en la evidencia. La gramática es intencionalmente
acotada y las construcciones no reconocidas permanecen como diagnósticos.

Un individuo aislado, una muestra remitida desde una granja, la sola mención de
un predio en otra oración, un resultado de laboratorio sin ubicación del evento
o múltiples localidades no cumplen esta regla. No se inventan datos para
desagregar un claim que combina varios predios. La cobertura lingüística es
deliberadamente limitada; las reglas no consultan el gold ni scores.

Una confirmación de laboratorio se incorpora como evidencia del foco solo si
comparte grupo explícito con un único foco animal positivo/confirmado y una
localidad resuelta, tiene el mismo pathogen_verbatim no vacío, sujeto other,
localizaciones exclusivamente de laboratorio y texto explícito de confirmación
del resultado. Requiere prueba positiva reportada, sin métrica independiente,
secuenciación ni fecha contradictoria. Se conservan su evidencia y localización
de laboratorio con ese rol, sin contarlas como otra localidad epidemiológica.
Si falta alguno de esos controles, el resultado diagnóstico queda separado.
Agrupar claims no crea una relación entre eventos persistidos ni prueba identidad
entre establecimientos de distintos documentos.

Ambas operaciones se aplican a copias; los claims originales y sus hashes siguen
siendo la auditoría del proveedor. Se generan warnings para distinguir una
representación focal de la adhesión de confirmación diagnóstica. No cambia el
esquema, prompt, gold, umbral de scoring ni reglas de evidencia literal.

### Desagregación multisitio conservadora

`animal_multisite.prepare_animal_multisite_claims` prepara una copia de un claim
diagnóstico animal positivo/confirmado únicamente cuando expresa dos detecciones
con atribución explícita «de dos predios, uno en A y otro en B». La primera versión
reconoce esa construcción en español, dentro de un mismo ítem y oración de
evidencia, con la población animal común explícita. No usa summaries ni consulta
gold. Exige exactamente dos localidades del evento distintas, con jerarquía
geográfica compartida y resuelta según los campos disponibles, y un único claim
en el grupo. Otros patrones quedan para revisión, sin distribuir hechos.

Se rechaza la separación si existen métricas reportadas o valores agregados aun
con reported=false; fechas o períodos conocidos; método, espécimen, target o
prueba diagnóstica reportada; datos genómicos/de transmisión; taxón canónico o
sujeto con especies mezcladas; localizaciones de laboratorio o jerarquías
distintas. La cobertura de sujetos se limita a categorías genéricas explícitas.
El resultado positivo común se conserva; no se infiere una prueba por predio ni
se transforma un total de casos/predios en cantidad de animales.

Los hijos reciben group_id y claim_id derivados sin colisionar con IDs existentes,
una única ubicación del evento, resumen focal y tipo outbreak_update. Se conserva
la cita literal completa que respalda las dos atribuciones; no se fabrican citas
recortadas ni se asignan métricas, fechas o especies a un sitio. El proveedor
original y su archivo de claims permanecen intactos. La entrada se valida antes
de esta preparación y las señales se vuelven a validar después del ensamblado.

Una separación aceptada agrega ASM-MULTISITE-01; un claim animal diagnóstico con
múltiples localidades que no cumple las condiciones se conserva sin dividir y
agrega ASM-MULTISITE-REVIEW. El aviso no cambia por sí mismo la validez de esquema
ni convierte el resultado en adjudicación humana o rechazo automático del evento.
El estado de revisión se expresa actualmente como warning auditable del payload;
no hay una cola ni persistencia nueva para ese aviso.

H5-005 no satisface la atribución explícita y contiene datos agregados/temporales;
se mantiene sin dividir. Su gold y las mediciones anteriores permanecen intactos.
Esta política no promete corregir todos los errores del corpus de desarrollo.
La segunda localidad debe cerrar la oración: no se aceptan coincidencias de
prefijo («Villa Sur» frente a «Villa Sur del Monte») ni una tercera localidad
oculta en la continuación. La formulación admitida es intencionalmente estricta;
una provincia u otra cláusula posterior también puede requerir revisión.

Para futuras capturas HTML, el parser 0.2.2 preserva adyacencia inline y separa
bloques mediante un serializador DOM. Sus pruebas y efectos sobre los hashes
se describen en [html-text-capture.md](html-text-capture.md). No sustituye los
bytes del corpus congelado ni autoriza mezclar predicciones con otra entrada.

La preparación de H5 no incluye predicciones, ingesta ni escrituras en Supabase.
Los paquetes y reportes locales quedan fuera de esta selección de código.

## Validación inicial del runner (15/10/2026)

14 pruebas nuevas del runner aprobadas y suite completa de 458 pruebas aprobada
en 69,34 s, con PostgreSQL local descartable habilitado. La instancia iniciada
para las pruebas se detuvo al finalizar. Preparación real de los seis documentos
H5: prepared=6, generated=0, failed=0, con hashes de fuentes/código verificados.
No hubo llamadas LLM ni escrituras en Supabase. Los ensamblados históricos de
MV Hondius generados por la suite quedan fuera de la selección de estos cambios.

Al cerrar el conjunto posterior de evaluación, guardas animales y serialización
DOM, la suite completa aprobó 588 pruebas en 68,08 s, con PostgreSQL local
habilitado y detenido al terminar. Es validación de software, no generalización.
La evaluación H5 y sus replays son artefactos locales separados: la primera
corrida real tuvo seis fallos de validación; el análisis posterior es de desarrollo,
incompleto, sin sustituir la medición inicial. Ningún gate de release queda habilitado.

## Binding de metadatos del documento

Además del raw_item_id, el runner exige que language y document_date coincidan
con los metadatos congelados. La fecha desconocida debe permanecer null; no se
admite completarla desde un prefijo del cuerpo. La comprobación se realiza
sobre los claims y sobre las señales ensambladas antes de guardar salidas válidas.
Un desajuste queda como fallo de validación, preserva claims originales y consumo
conocido y permite continuar el resto del corpus. No se corrige silenciosamente.

Esta guarda no prueba que event_date o cada campo semántico tenga fundamento:
la fecha del documento y la del hecho son contratos distintos. No cambia el
prompt ni reinterpreta las fuentes. Las mediciones históricas quedan intactas;
los freezes que incluyan offline.py requieren una revisión para ejecutar el
código nuevo.

## Avisos opcionales de revisión de claims

La API Python acepta include_review_hints=True (por defecto False). Se ejecuta
solo después de validar esquema, binding y evidencia literal de los claims.
No conecta ningún proveedor por sí sola y no cambia el CLI de preparación.

Cuando se habilita, report.claim_review registra versión/hash del módulo de
revisión y affects_validation=false. Cada documento distingue:
- not_reviewed, findings=null: preparación sin respuestas o fallo previo a revisión.
- reviewed, findings=[]: revisión ejecutada sin avisos; no acredita corrección semántica.
- reviewed con findings: avisos por claim/campo/código para revisión posterior.
- review_error, findings=null y error_type: error del revisor, redaccionado, sin
  cambiar la aceptación de una respuesta válida.

La revisión se refiere a claims, antes del ensamblado. Si luego falla el ensamblado,
puede existir revisión ejecutada en un documento failed. No equiparar ambos estados.
REVIEW-LOCALITY-QUOTE marca localidad completa ausente de las citas de ese claim;
puede estar sustentada por contexto de otra frase del documento. No prueba error.
REVIEW-TEST-RESULT marca test_reported=false con resultado/estado diagnóstico.
REVIEW-INVESTIGATION-STATE marca investigación sin estado pending, que puede ser
metadata incompleta. No corrige campos ni clasifica automáticamente toda negación.

Los avisos no modifican claims, señales, validaciones, métricas o scorer; tampoco
son una cola persistida ni autorización de publicación. Su presencia en el reporte
sí cambia su hash. No reescribir reportes históricos: usar una ejecución/replay
separada con freeze actualizado. El módulo nuevo debe incluirse en ese freeze.
La ausencia de avisos no garantiza localidad correcta, scope cumplido o fechas
sustentadas; la herramienta tiene cobertura limitada y puede producir falsos avisos.
