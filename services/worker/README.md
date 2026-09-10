# Worker

Responsabilidades previstas:

1. recuperar documentos desde fuentes permitidas;
2. calcular hash y persistir `raw_items`;
3. extraer texto/estructura;
4. invocar el extractor IA con `shared/schemas/signal-extractor-v0.1.schema.json`;
5. validar y normalizar la salida;
6. persistir `signals` y objetos relacionados;
7. en una etapa posterior, ejecutar event matching.

La `SUPABASE_SERVICE_ROLE_KEY` y `DATABASE_URL` son secretos de servidor y nunca deben llegar al frontend.
