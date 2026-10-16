from datetime import datetime, timezone

from bs4 import BeautifulSoup
import pytest

from onehealth_worker.ingestion.html_parser import parse_html_document
from onehealth_worker.ingestion.models import FetchedDocument


@pytest.mark.parametrize('html,expected', [
    ('<p>Informe en <strong>Villa Norte</strong>, provincia X.</p>', 'Informe en Villa Norte, provincia X.'),
    ('<p>Presencia del <a href="/x">virus X</a>.</p>', 'Presencia del virus X.'),
    ('<p>Palabra<strong>compuesta</strong> sin espacio.</p>', 'Palabracompuesta sin espacio.'),
    ('<p>Dos <em>partes</em> separadas.</p>', 'Dos partes separadas.'),
    ('<p><strong>(Caso</strong> <em>positivo)</em>: confirmado.</p>', '(Caso positivo): confirmado.'),
    ('<p>Dato 1,<strong>5</strong> y fecha 04/<span>03</span>/2026.</p>', 'Dato 1,5 y fecha 04/03/2026.'),
    ('<p> Uno\n  <strong>dos</strong>\t tres&nbsp;cuatro. </p>', 'Uno dos tres cuatro.'),
    ('<h2>Situación</h2><p>Primer párrafo.</p><p>Segundo.</p>', 'Situación\n\nPrimer párrafo.\n\nSegundo.'),
    ('<p>Primera<br>Segunda<br/>Tercera</p>', 'Primera\nSegunda\nTercera'),
    ('<ul><li>Uno</li><li>Dos</li></ul>', 'Uno\n\nDos'),
    ('<ul><li>Principal<ul><li>Hijo</li></ul></li><li>Otro</li></ul>', 'Principal\n\nHijo\n\nOtro'),
    ('<p>Texto<!-- comentario --> literal.</p><script>falso()</script><style>.x{}</style>', 'Texto literal.'),
    ('<p>Real.</p><template>Oculto.</template><noscript>Alternativo.</noscript>', 'Real.'),
    ('<table><tr><td>Uno</td><td>Dos</td></tr><tr><td>Tres</td><td>Cuatro</td></tr></table>', 'Uno Dos\n\nTres Cuatro'),
])
def test_dom_text_preserves_inline_adjacency_and_structural_boundaries(html, expected):
    from onehealth_worker.ingestion.html_text import render_dom_text
    soup = BeautifulSoup(html, 'html.parser')
    before = str(soup)
    assert render_dom_text(soup) == expected
    assert str(soup) == before


def parse(body):
    return parse_html_document(FetchedDocument(url='https://example.invalid/news',
        status_code=200, mime_type='text/html', body=body.encode(),
        retrieved_at=datetime(2026, 10, 15, tzinfo=timezone.utc)))


def test_ingestion_preserves_punctuation_from_inline_elements():
    parsed = parse('<main><p>Se confirmó un caso en <strong>Villa Norte</strong>, provincia X.</p></main>')
    assert parsed.text == 'Se confirmó un caso en Villa Norte, provincia X.'
    assert parsed.metadata['parser'] == 'beautifulsoup-html-v0.2.2'


def test_nested_list_paragraph_is_not_captured_twice():
    parsed = parse('<main><ul><li><p>Primer elemento suficientemente largo.</p>'
        '<ul><li>Segundo elemento suficientemente largo.</li></ul></li></ul></main>')
    assert parsed.text.count('Primer elemento') == 1
    assert parsed.text.count('Segundo elemento') == 1
    assert '\n\n' in parsed.text


def test_fallback_preserves_short_inline_text_and_block_boundaries():
    assert parse('<main><div>Uno <b>dos</b>.</div><div>Tres.</div></main>').text == 'Uno dos.\n\nTres.'
