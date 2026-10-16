"""Export validated provisional agent decisions as a passive local HTML report."""
import argparse
import hashlib
import html
import json
from pathlib import Path

from .field_review import ReviewValidationError, validate_field_review


LABELS = {
    'accept_review_proposal': 'Propuesta aceptada por el agente',
    'reject_review_proposal': 'Propuesta rechazada por el agente',
    'retain_validation_failure': 'Fallo conservado',
    'confirm_current_value': 'Valor actual confirmado por el agente',
    'abstain': 'Abstención',
}


def export_field_review(*, decisions_path: Path, allowed_root: Path, output_path: Path) -> dict:
    """Validate first; create one new HTML file, never apply any decision.

    The output parent must exist. As for the validator, callers must use a tree
    that is not being changed concurrently. No referenced URL is fetched.
    """
    result = validate_field_review(decisions_path=decisions_path, allowed_root=allowed_root)
    decisions_path = decisions_path.resolve()
    decisions_bytes = decisions_path.read_bytes()
    if hashlib.sha256(decisions_bytes).hexdigest() != result['decisions_sha256']:
        raise ReviewValidationError('review changed during export')
    decisions = json.loads(decisions_bytes.decode('utf-8-sig'))
    review_path = Path(decisions['source_review_file'])
    if not review_path.is_absolute():
        review_path = decisions_path.parent / review_path
    review_bytes = review_path.read_bytes()
    if hashlib.sha256(review_bytes).hexdigest() != decisions['source_review_sha256']:
        raise ReviewValidationError('review changed during export')
    rows = {row['review_id']: row for row in json.loads(review_bytes.decode('utf-8-sig'))['rows']}
    esc = lambda value: html.escape(str(value), quote=True)
    pretty = lambda value: esc(json.dumps(value, ensure_ascii=False, indent=2))
    cards = []
    for entry in decisions['decisions']:
        row = rows[entry['review_id']]
        source = row['source']
        metadata = ''
        if 'frozen_metadata_reference' in row:
            ref = row['frozen_metadata_reference']
            metadata = (f'<h3>Metadatos congelados de respaldo</h3><p>Puntero: '
                        f'<code>{esc(ref["pointer"])}</code></p><pre>{pretty(ref["value"])}</pre>'
                        f'<p>SHA-256: <code>{esc(ref["sha256"])}</code></p>')
        cards.append(f'''<article>
<h2>{esc(row['review_id'])} · {esc(row['document_id'])}</h2>
<p><strong>{esc(LABELS[entry['disposition']])}</strong> · Sin aplicar</p>
<p>Campo: <code>{esc(row['field_pointer'])}</code></p>
<h3>Valor observado</h3><pre>{pretty(row['observed_value'])}</pre>
<h3>Valor propuesto</h3><pre>{pretty(row['proposed_value'])}</pre>
<p>Acción propuesta: <code>{esc(row['proposed_action'])}</code></p>
<p>{esc(entry['rationale'])}</p>
<h3>Cita de respaldo</h3><blockquote>{esc(source['excerpt'])}</blockquote>
<p>Fuente original (referencia textual): {esc(source.get('url', 'No indicada'))}</p>
<p>Intervalo Unicode [{source['unicode_start']}:{source['unicode_end']})<br>
Fuente SHA-256: <code>{esc(source['sha256'])}</code><br>
Artefacto SHA-256: <code>{esc(row['artifact_sha256'])}</code></p>{metadata}
</article>''')
    summary = ' · '.join(f'{esc(LABELS[key])}: {count}' for key, count in result['counts'].items())
    page = f'''<!doctype html><html lang="es"><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revisión provisional del agente</title>
<style>body{{font:16px/1.5 system-ui;max-width:960px;margin:2rem auto;padding:0 1rem;color:#172331}}article{{border-top:2px solid #ccd7df;margin-top:2rem}}pre,code{{white-space:pre-wrap;overflow-wrap:anywhere}}blockquote{{white-space:pre-wrap;border-left:4px solid #527582;margin-left:0;padding-left:1rem}}@media print{{article{{break-before:page}}body{{font-size:11pt}}}}</style>
<h1>Revisión provisional del agente</h1>
<p>{result['decisions']} decisiones sobre campos; no equivalen a señales. Sin revisión humana ni validación semántica independiente. Ninguna propuesta fue aplicada.</p>
<p>{summary}</p><p>Integridad referencial: {result['verified_files']} archivos verificados.</p>
<p>Decisiones SHA-256: <code>{result['decisions_sha256']}</code></p>
<p>Este informe no recupera documentos fallidos, modifica predicciones ni recalcula métricas.</p>
{''.join(cards)}</html>'''
    # Recheck all evidence before publishing the rendered snapshot.
    if validate_field_review(decisions_path=decisions_path, allowed_root=allowed_root) != result:
        raise ReviewValidationError('review changed during export')
    encoded = page.encode('utf-8')
    with output_path.open('xb') as stream:
        stream.write(encoded)
    return {**result, 'report_version': 'agent-field-review-html-1',
            'html_sha256': hashlib.sha256(encoded).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Export validated agent review to a new local HTML file.')
    parser.add_argument('--decisions', required=True, type=Path)
    parser.add_argument('--allowed-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = export_field_review(decisions_path=args.decisions, allowed_root=args.allowed_root,
                                     output_path=args.output)
    except (ReviewValidationError, OSError):
        print(json.dumps({'valid': False, 'error': 'Review export failed; check inputs and new output path.'}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
