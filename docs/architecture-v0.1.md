# Architecture v0.1

```text
Official/Open sources
        |
        v
   Python worker
        |
        +--> raw_items (safe metadata)
        |        \--> raw_item_payloads (server only)
        |
        v
 AI extractor + JSON Schema validation
        |
        v
      signals
        |
  normalization
        |
        v
  event matcher
   /         \
existing     new
 event      event
    \       /
     evidence relations
           |
           v
      priority/review
           |
           v
      Next.js Radar
```

## Seguridad inicial

- `anon`: 0 privilegios sobre las tablas del dominio.
- `authenticated`: `SELECT` en datos derivados/curados.
- `authenticated`: sin `INSERT/UPDATE/DELETE`.
- `raw_items`: metadatos de procedencia legibles por usuarios autenticados.
- `raw_item_payloads`: texto completo/storage/error sólo en servidor.
- `service_role`: sólo en worker/servidor.
- Todas las tablas `public` tienen RLS habilitado.

## Decisiones pospuestas

- autenticación/roles de revisores expertos;
- workflow de aprobación editorial;
- colas persistentes;
- almacenamiento de PDFs en Supabase Storage;
- embeddings/vector search;
- alertas;
- modelado de organizaciones/equipos multi-tenant.
