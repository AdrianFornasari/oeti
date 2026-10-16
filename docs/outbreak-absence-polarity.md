# Polaridad de ausencia de brotes

El ensamblador conserva `signal_type=outbreak` para una declaración explícita
`outbreak_update` con `polarity=negative`, pero asigna `negative_evidence`.
No infiere un diagnóstico negativo, métricas cero, fechas ni localidades.

Una ausencia se agrupa por separado de las actualizaciones/recuentos positivos,
aunque el proveedor les asigne el mismo group_id. Ausencias repetidas del mismo
grupo aún pueden consolidarse. Los grupos positivos y de polaridad incierta
conservan su tratamiento previo. No es un filtro textual ni un clasificador de
negaciones: requiere la polaridad explícita del claim.

La corrección está en atomic_claims, compartido por los ensambladores 0.4.4,
0.4.5 y 0.4.6. Las salidas históricas no se migran ni se sobrescriben. Un freeze
que incluya ese archivo debe revisarse antes de ejecutar código nuevo.

Dieciocho regresiones sintéticas comprueban los tres ensambladores, polaridades
positiva/negativa/incierta, orden de claims mixtos, aislamiento de evidencia y
recuentos, consolidación de ausencias y no mutación del payload de entrada.

El replay H5 DOM separado utiliza respuestas ya guardadas: conserva cuatro
documentos válidos y dos fallidos por literalidad. La única diferencia de las
señales válidas es el rol de la ausencia de Entre Ríos. No se recalculan métricas
ni se cambia gold/scorer/threshold. Siguen pendientes localidad, alcance y fechas.
