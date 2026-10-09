# Selección de dependencias — Event Persistence v0.4.9

Fecha: 9 de octubre de 2026.

## Resultado

El conjunto de Event Persistence y hardening semántico puede validarse sin los
cambios de token usage ni del provider. Se preparó un parche de revisión de
31 archivos y se aplicó, fuera del checkout, sobre un snapshot completo de HEAD.
`git apply --check` pasó y los contenidos aplicados se verificaron mediante SHA-256.
La suite del snapshot final, con PostgreSQL local habilitado, obtuvo **304 passed**.
La suite del checkout completo obtuvo **307 passed**; las tres pruebas
excluidas corresponden a token usage. No se cambió código del checkout durante
esta selección, ni el index de Git, ni datos de Supabase.

## Dependencias y límites

| Grupo | Selección | Motivo |
| --- | --- | --- |
| Módulos `evaluation/*v049.py` y tests `test_event*v049.py` | Archivos completos | Matching, contexto, política, assignment, cohortes, semillas, repository y pruebas |
| `extraction/matching.py` y `test_extraction_semantics_v04.py` | Diffs completos | Gate que exige identidad etiológica resuelta y excluye alertas/baselines |
| `extraction/signal_semantics_v049.py` y `test_signal_semantics_v049.py` | Archivos completos | Reclasificación conservadora de snapshots de vigilancia agregada |
| `extraction/pipeline.py` | Solo import y llamada a `harden_signal_semantics_v049` | Normalizar → hardening → validar; no incluye campos ni persistencia de tokens |
| `extraction/repository.py` | Cambios excluidos | Diff actual agrega exclusivamente columnas y persistencia de token usage |
| `extraction/openai_provider.py` | Cambios excluidos | Combina token usage con timeout configurable y cambios de reintentos |
| Tests de provider y token usage | Cambios excluidos | Tres pruebas de métricas ajenas a Event Persistence |
| Migración `20261008093000_extraction_run_token_usage.sql` | Excluida | DDL de extracción independiente; Event Persistence no necesita esta migración |
| `apps/web/` | Excluido | Frontend fuera del alcance autorizado |
| Seis JSON `mv-hondius/*v046-assembled.json` | Excluidos | Benchmarks locales protegidos, sin staging |

Los módulos de eventos consultan `signals.event_matching_eligible` ya persistido;
no importan el provider ni las métricas de extracción. Para futuras señales,
el pipeline necesita el gate y el hardening seleccionados. El gate se importa
desde el repository de extracción que ya existe en HEAD; su diff de tokens no
es necesario para aplicar el gate actualizado.

Se verificó que el snapshot usa exactamente el provider, el repository de
extracción y el test de provider de HEAD. No contiene la migración ni el archivo
de tests de token usage. El pipeline seleccionado no contiene `usage`.

## Artefactos de revisión

- `evaluation/reports/v049-event-persistence-semantic-review.patch`: parche de
  código y tests; no incluye informes ni documentación.
- `evaluation/reports/v049-dependency-selection.json`: commit base, SHA-256 del
  parche, selección por archivo, exclusiones, snapshot y resultado de pruebas.
- `docs/event-persistence-v049-validation.md` y
  `docs/event-persistence-v049-closure.md`: evidencia y límites operativos.
- Informes MV Hondius: evidencia local de dry-run, persistencia autorizada y replay.
  La decisión de incorporarlos a Git es separada del código y no se presume.

El parche es un artefacto para revisión. No se aplicó al checkout original ni se
preparó staging. En particular, no debe usarse `git add pipeline.py` completo para
este conjunto: incluiría también los cambios de tokens que siguen en ese archivo.
Al integrar más adelante debe seleccionarse el contenido semántico del parche.
El candidato final agrega los tres documentos de revisión: 34 archivos en total.
Los informes JSON, los parches generados y el script de verificación de Supabase
se conservan como evidencia/herramientas locales fuera de ese candidato.

## Trabajo independiente pendiente

Token usage necesita su propia revisión de contrato entre provider, pipeline,
repository y esquema aplicado en `extraction_runs`. Su migración no se ejecutó
en esta tarea. El provider también cambia la política operativa de timeout y
reintentos: actualmente no hay pruebas específicas de esos nuevos casos en la
suite, por lo que no se incluye como dependencia de Event Persistence.

La selección tampoco habilita creación automática. El próximo paso es revisar
el parche final y la documentación que acompañará al conjunto de Event
Persistence, antes de pedir autorización para un commit acotado. Los cambios
independientes siguen preservados en el checkout.
