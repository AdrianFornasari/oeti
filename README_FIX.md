# OETI Sprint 1C — temporal precision fix v0.3.3

Corrige el caso real en que el extractor devuelve un año (por ejemplo `2004`) en `metrics[].as_of_date`.

## Decisión epidemiológica

OETI no convierte `2004` en `2004-01-01`, porque eso inventaría precisión temporal. El contrato v0.2 de extracción conserva:

- `as_of_date`: sólo fecha exacta `YYYY-MM-DD` o `null`;
- `as_of_year`: año cuando está disponible;
- `as_of_month`: mes cuando está disponible;
- `as_of_precision`: `day | month | year | unknown`;
- `as_of_verbatim`: expresión temporal original.

La base no requiere migración: `signal_metrics.as_of_date` conserva fechas exactas y los componentes parciales se guardan en `signal_metrics.metadata`.

Además, el pipeline normaliza defensivamente salidas del proveedor antes de la validación canónica, por lo que un año aislado queda preservado con precisión anual y genera un warning auditable.
