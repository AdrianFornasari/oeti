# Data model v0.1

## Invariantes

1. `raw_item != signal != event`.
2. Un `signal` expresa una afirmación epidemiológica atómica y trazable.
3. El texto original y el nombre normalizado son campos diferentes.
4. `unknown` nunca equivale a `false` o `negative`.
5. La evidencia negativa se persiste.
6. Las contradicciones se modelan mediante `signal_relations` y `hard_conflict`.
7. Un conflicto duro impide event matching automático aunque el score de similitud sea alto.
8. `raw_items` expone sólo metadatos de procedencia; el payload completo vive en `raw_item_payloads` y no se expone al navegador.
9. El worker agrega versiones de señales; no debe sobrescribir silenciosamente una extracción previa.
10. Un evento es una vista consolidada y mutable; las señales son el registro probatorio.

## Event matching v0.1

Score candidato:

```text
M = 0.35 P + 0.25 G + 0.15 T + 0.10 H + 0.10 E + 0.05 C
```

- P: compatibilidad de patógeno/enfermedad.
- G: relación geográfica.
- T: compatibilidad temporal.
- H: relación de huéspedes.
- E: coincidencia epidemiológica.
- C: contexto compartido.

Umbrales iniciales:

- `>= 0.80`: candidato a vínculo automático, salvo conflicto duro.
- `0.60 - 0.79`: revisión humana.
- `< 0.60`: mantener separado.

Estos umbrales son hipótesis de ingeniería, no parámetros epidemiológicos validados. Deben calibrarse con los casos retrospectivos.
