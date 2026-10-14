# Normalización del veto textual de no relación

Fecha: 14 de octubre de 2026.

La evaluación externa identificó marcadores de no relación con mojibake en el
matcher v0.4.8. El veto no reconocía «sin relación» o «descartó» en texto acentuado,
aunque sus formas sin tilde sí estaban contempladas. Esto afectaba un guard
funcional, no solo la presentación de mensajes.

La corrección normaliza marcadores canónicos y una copia del texto comparado
mediante casefold, NFKD y eliminación de caracteres combinantes. Se aplica solo
en `_contains_explicit_non_relation`; no modifica `_signal_text`, los objetos
de entrada, la evidencia literal, las puntuaciones ni los thresholds del matcher.
La extracción y persistencia de textos fuente conservan sus tildes originales.

Se mantienen los prerrequisitos de señal negativa/refutada y la prioridad de
razones del veto. El cambio no incorpora un analizador semántico de negación ni
interpreta cualquier mención de descarte como un conflicto sin esos guards.

Las pruebas cubren variantes acentuadas, mayúsculas, sin tilde, Unicode
descompuesto, texto inglés, resumen/evidencia, simetría y entradas inmutables.
El recorrido completo del matcher rechaza la fusión de los casos de regresión.
El benchmark original de 14 pares mantiene el reporte y gate previos sin cambios.
Ese benchmark no contenía la redacción defectuosa: por eso el gate aprobado no
detectaba el hueco. Las nuevas regresiones amplían esa cobertura; no prueban
generalización a un segundo evento independiente.
