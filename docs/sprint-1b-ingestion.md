# Sprint 1B - Catálogos e ingesta oficial Argentina-first

## Objetivo

Validar el primer tramo del pipeline con una fuente argentina real, preservando trazabilidad y sin introducir todavía decisiones de IA.

## Alcance implementado

1. Catálogos mínimos versionados como migración de datos.
2. Fuente específica `ARG_MSAL_NEWS` y `ARG_ANLIS_NEWS` para distinguir publisher y contexto.
3. Manifiesto retrospectivo del caso MV Hondius con seis publicaciones oficiales.
4. Fetch HTTP con redirects, timeout, User-Agent identificable y reintentos acotados.
5. Parser HTML con extracción de título, fecha, idioma y texto principal.
6. Hash SHA-256 del texto normalizado para deduplicación estable.
7. Persistencia transaccional de metadatos en `raw_items` y texto bruto parseado en `raw_item_payloads`.
8. CLI para una URL o para un manifiesto completo.
9. Test unitario del parser y del hash.

## Decisiones

- `raw_item` sigue siendo material fuente, no una señal epidemiológica.
- La ingesta no infiere enfermedad, causalidad, número de casos ni relaciones.
- El worker escribe por conexión PostgreSQL de servidor; el navegador continúa sin acceso al payload completo.
- No se hace scraping masivo: este sprint usa endpoints oficiales concretos, con cadencia manual.
- Los textos completos se almacenan para procesamiento interno. Antes de redistribuir contenido se deben validar las condiciones de cada fuente.

## Caso MV Hondius

Las publicaciones incluidas cubren: notificación inicial, actualizaciones BEN, evidencia de transmisión, investigación en roedores, incompatibilidad genómica en Tierra del Fuego y evidencia negativa en Mendoza. El objetivo del siguiente sprint será convertir estos `raw_items` en señales atómicas estructuradas.

## Criterio de aceptación

El sprint queda aceptado cuando:

- la migración de catálogos aparece en LOCAL y REMOTE;
- `ARG_MSAL_NEWS` y `ARG_ANLIS_NEWS` existen en `sources`;
- al menos una URL oficial produce un `raw_item` y un `raw_item_payload`;
- repetir la misma ingesta sin cambios no duplica el documento;
- el texto recuperado puede trazarse a la URL original.
