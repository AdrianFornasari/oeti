import json
from html.parser import HTMLParser

import pytest

from test_field_review import package, dump, sha, rewrite_review
from onehealth_worker.evaluation.field_review import ReviewValidationError
from onehealth_worker.evaluation.field_review_report import export_field_review, main


def test_export_preserves_originals_and_escapes_active_content(package, tmp_path):
    root, path = package
    data = json.loads(path.read_text())
    data['decisions'][0]['rationale'] = '<script src="https://example.org/x">&</script>'
    dump(path, data)
    original = {p: p.read_bytes() for p in root.iterdir()}
    output = tmp_path / 'report.html'
    result = export_field_review(decisions_path=path, allowed_root=root, output_path=output)
    assert original == {p: p.read_bytes() for p in root.iterdir()}
    text = output.read_text(encoding='utf-8')
    assert '&lt;script' in text
    class Tags(HTMLParser):
        tags = []
        def handle_starttag(self, tag, attrs):
            self.tags.append(tag)
            assert not any(key in {'src', 'href', 'action'} or key.startswith('on') for key, _ in attrs)
    parser = Tags()
    parser.feed(text)
    assert not {'script', 'iframe', 'form', 'img'} & set(parser.tags)
    assert parser.tags.count('article') == 1
    assert result['decisions_applied'] == 0 and not result['human_review_verified']
    assert 'Sin aplicar' in text and 'Cita literal.' in text


def test_stale_source_creates_no_report(package, tmp_path):
    root, path = package
    (root / 'source.txt').write_text('changed')
    output = tmp_path / 'report.html'
    with pytest.raises(ReviewValidationError):
        export_field_review(decisions_path=path, allowed_root=root, output_path=output)
    assert not output.exists()


def test_existing_output_is_never_overwritten(package):
    root, path = package
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        export_field_review(decisions_path=path, allowed_root=root, output_path=path)
    assert path.read_bytes() == before


def test_frozen_metadata_reference_is_visible(package, tmp_path):
    root, path = package
    metadata = root / 'metadata.json'
    dump(metadata, {'date': None})
    rewrite_review(root, path, lambda r: r['rows'][0].update(frozen_metadata_reference={
        'path': metadata.name, 'sha256': sha(metadata), 'pointer': '/date', 'value': None}))
    output = tmp_path / 'report.html'
    export_field_review(decisions_path=path, allowed_root=root, output_path=output)
    text = output.read_text(encoding='utf-8')
    assert 'Metadatos congelados de respaldo' in text and '/date' in text
    assert sha(metadata) in text and '<pre>null</pre>' in text


def test_cli_error_does_not_expose_input_path(package, tmp_path, capsys):
    root, path = package
    assert main(['--decisions', str(path), '--allowed-root', str(root), '--output', str(path)]) == 1
    assert str(path) not in capsys.readouterr().out
