# Captura HTML: parser 0.2.2

## Actualización local: parser 0.2.5 (30/10/2026)

La decodificación recibe el charset declarado en Content-Type HTTP, incluidos
parámetros entrecomillados y nombres en mayúsculas. Cuando no está declarado o
no se reconoce, BeautifulSoup conserva su fallback de metadatos/autodetección.
La metadata registra `http_charset` y `text_encoding` (codificación utilizada por
BeautifulSoup). Los bytes recibidos no se modifican. Esto corrige casos como
Łódź en ISO-8859-2, que la autodetección podía interpretar como £ód¼.

Un encabezado incorrecto sigue pudiendo inducir una decodificación equivocada;
el registro no acredita que la fuente declarase correctamente su codificación.
El cambio puede alterar texto/hash de futuras capturas, sin reprocesar históricos.
La versión 0.2.5 conserva la preservación de p/li breves de 0.2.4.

## Actualización local: parser 0.2.4 (30/10/2026)

El parser conserva todos los párrafos y elementos de lista no vacíos dentro del
contenedor seleccionado. El filtro anterior de 20 caracteres podía omitir hechos
breves como «No hubo casos.» o «3 casos.» cuando otro párrafo superaba el límite.
Se mantienen la exclusión de navegación y bloques ajenos, la serialización DOM,
el rechazo de texto vacío y la deduplicación estable de párrafos.

Este cambio puede modificar el texto y su hash en capturas futuras; la versión
0.2.4 permite distinguirlo. No reconstruye ni reemplaza capturas históricas, y
no demuestra extracción perfecta de cualquier sitio. La versión 0.2.3 ya conserva
fecha desconocida ante una fecha visible imposible. Las secciones siguientes
describen el comportamiento y validación históricos de 0.2.2; sus referencias al
filtro de 20 caracteres no aplican a 0.2.4.

`ingestion.html_text.render_dom_text` preserva adyacencia inline sin agregar
separadores entre negritas, enlaces o spans. `<strong>Lobos</strong>,` conserva
`Lobos,`. Mantiene espacios que existan en los nodos de texto, colapsando
whitespace repetido; no repara puntuación con una sustitución textual.

Los bloques usan líneas en blanco, br un salto y las celdas de tabla un espacio.
Se excluyen comentarios, declaraciones y script/style/template/noscript/svg/head.
El DOM no se modifica. Es serialización textual, sin CSS, JavaScript, estilos
computados ni selección automática del artículo.

## Integración y compatibilidad

`parse_html_document` usa el serializador para p/li y el fallback. Conserva la
selección genérica article/main/body, el filtro de 20 caracteres y deduplicación
estable. Los p/li anidados se capturan desde su contenedor para evitar duplicados.
Las reglas de título, idioma y publicación mantienen su implementación anterior.
La metadata identifica el cuerpo como `beautifulsoup-html-v0.2.2`.

Las fuentes congeladas conservan sus bytes/hashes. Cambiar el parser no cambia
retroactivamente una fuente ni vuelve válida su cita. Una respuesta que copió
espaciado artificial anterior puede dejar de coincidir con la representación
nueva. No se deben mezclar predicciones e inputs de distintas versiones para
presentar una primera medición. Registrar parser, HTML y texto de cada captura.

`normalized_text_sha256` solo colapsa whitespace: cambiar `Lobos ,` por `Lobos,`
altera el hash. Como la ingesta deduplica por fuente/hash, una futura captura puede
crear otro raw_item para la misma URL. No se modifica la deduplicación ni se migran
registros existentes; recapturas/escrituras requieren su alcance autorizado.
El validador literal conserva su contrato y no flexibiliza puntuación o palabras.

## Validación local, 15/10/2026

17 regresiones nuevas cubren inline, espacios, puntuación, decimales, fechas,
entidades, bloques, br, listas anidadas, contenido excluido, tablas e integración.
19 pruebas focalizadas aprobadas y suite completa de 588 pruebas aprobada en
68,08 s con PostgreSQL local habilitado y detenido al terminar.

Comparación offline de seis HTML H5: se reconstruyeron exactamente los hashes
previos antes de derivar texto con los mismos selectores/corte del corpus. También
se probó el parser completo, cuya selección genérica no es el scope de evaluación.
De nueve citas guardadas, siete coinciden con texto previo y ocho con texto nuevo:
se ganan dos por puntuación y se pierde una que copiaba espaciado artificial.
Es comparación de representación, no calidad clínica. No se ejecutó extractor ni
scorer ni se reasignaron IDs/gold. Las métricas anteriores permanecen intactas.
