# Inserción de membresías mediante executemany

Fecha: 14 de octubre de 2026.

La creación de cohortes inserta el evento y entrega todas las membresías a
`cursor.executemany()` dentro de la misma transacción existente. Conserva SQL,
casts, orden de parámetros, score, decisión, relación y rationale completo por
señal. No cambia esquema, auditoría, guards, locks ni habilitación de escrituras.

Psycopg puede agrupar el envío mediante pipeline cuando el entorno lo soporta;
no es una única sentencia SQL ni implica reuso de conexiones entre invocaciones.
No se agregan reintentos automáticos. Un fallo en cualquier membresía se propaga
y revierte también el evento; la conexión administrada por el repository se
cierra al salir de la operación. Una invocación posterior abre otra conexión.

El experimento local previo, con 100 señales, observó inserciones de 133 a
104 ms y ventana protegida de 171 a 139 ms. Con cinco señales el beneficio fue
pequeño. Son resultados sintéticos locales, no un compromiso de rendimiento
productivo. La memoria de los parámetros y la auditoría repetida siguen creciendo
con el tamaño de cohorte; este cambio no reduce ese volumen ni la transferencia
repetida de documentos durante validación.

Pruebas verifican valores y auditoría Unicode, transacción única, error parcial,
rollback total, cierre de la conexión fallida y éxito posterior en conexión nueva.
Las pruebas PostgreSQL existentes cubren además replay, guards y concurrencia.
No silenciar avisos de pipeline ocultando la excepción original ni reintentar
una escritura cuyo resultado sea ambiguo.
