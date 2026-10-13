# Timeout y reintentos del provider

`OpenAIResponsesProvider` conserva lectura de 600 segundos por defecto,
configurable con `read_timeout_seconds` al construirlo. El valor debe ser
numérico, finito y positivo; no acepta booleanos, NaN ni infinito.
Conexión, escritura y espera del pool tienen timeout explícito de 20 segundos.
Estos límites corresponden a fases de httpx; no constituyen un plazo máximo
global de ejecución. El parámetro no está expuesto todavía en Settings o CLI.

Solo `ConnectTimeout` y `ConnectError` se reintentan: máximo tres intentos,
esperas de uno y dos segundos, sin espera después del último fallo.

Los otros `RequestError`, incluidos Read/Write/PoolTimeout, Read/WriteError,
errores de protocolo y cierre, se traducen a `LLMProviderError`, conservando
la causa original, sin reintento. Un error después de enviar datos no demuestra
que el servidor haya descartado la solicitud; este cliente no confirma su
procesamiento ni garantiza ejecución exactamente una vez.

Los HTTP 429/500/503 conservan su comportamiento de error sin reintento.
No se agrega reintento de inferencia, SDK, idempotency key ni trabajo en background.
La extracción y el contrato de tokens mantienen sus interfaces actuales.

Las pruebas usan transporte falso y sustituyen sleep: verifican conteos de
solicitudes, esperas, agotamiento de conexión, recuperación, causas originales,
timeouts por fase y ausencia de reintentos tras errores ambiguos. No consumen
API ni tokens reales.
