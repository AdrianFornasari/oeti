# Contexto de evidencia para revisión manual offline

`evaluation.evidence_context_review.build_evidence_context_review(**review_inputs)`
acepta los mismos argumentos que `attribution_review.build_review`. Reutiliza sus
controles de hashes, documento, esquemas y literalidad. No usa red ni credenciales.
No está integrado al runner ni al pipeline de producción; el sidecar v2 existente
no cambia. Debe invocarse explícitamente con artefactos guardados.

Devuelve una fila por evidencia de cada claim, incluso sin métrica, con su puntero,
cita original y todas sus ocurrencias exactas en el documento, incluidas las
superpuestas. No elige una ocurrencia. Cada ocurrencia muestra hasta 160 caracteres
Unicode anteriores y posteriores como un único segmento contiguo de la fuente.
Los offsets son índices de puntos de código desde cero, con extremos exclusivos;
no son offsets de bytes ni unidades UTF-16.

Cada fila declara `occurrence_status`: `exact_matches` o `no_exact_match`.
La validación literal compartida admite normalización de espacios; por eso una
cita válida puede carecer de coincidencias exactas. En ese caso se conserva la
cita y una lista vacía, sin inventar offsets ni buscar un antecedente normalizado.

El contexto permite inspeccionar una cita como «se notificaron 3 probables en esa
misma temporada» junto al texto anterior, sin sustituir evidencia ni atribuirle
un antecedente. Una ventana puede truncar un antecedente o mostrar hechos ajenos:
no constituye evidencia ampliada aceptada. No se detecta anáfora ni se decide
completitud, corrección, pertenencia al grupo o aceptación semántica. El caso
SCOPE04 sigue requiriendo revisión humana y no se considera resuelto por este helper.

`test_evidence_context_review.py` usa controles construidos, no predicciones ni
gold independiente. Verifica contexto, ocurrencias repetidas/superpuestas, límites,
offsets Unicode, determinismo, integridad y no mutación. No cambia prompts, corpus,
artefactos históricos ni decisiones de producción.
