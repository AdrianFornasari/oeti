from onehealth_worker.extraction.prompt import SYSTEM_INSTRUCTIONS, build_document_input


def test_prompt_preserves_unknown_and_evidence_rules():
    lowered = SYSTEM_INSTRUCTIONS.lower()
    assert "ausencia de información" in lowered
    assert "evidencia" in lowered
    assert "literal" in lowered


def test_document_input_binds_raw_item_id():
    text = build_document_input(
        raw_item_id="11111111-1111-4111-8111-111111111111",
        title="Título",
        url="https://example.test/a",
        published_at=None,
        language="es",
        raw_text="Texto fuente.",
    )
    assert "11111111-1111-4111-8111-111111111111" in text
    assert "DOCUMENT_TEXT_BEGIN" in text
    assert "Texto fuente." in text


def test_prompt_v043_requires_consolidation_negative_evidence_and_explicit_strain_normalization():
    assert "CONSOLIDACIÓN DE ACTUALIZACIONES" in SYSTEM_INSTRUCTIONS
    assert "NO SOBRE-FRAGMENTAR" in SYSTEM_INSTRUCTIONS
    assert "NORMALIZACIÓN EXPLÍCITA DE CEPA/ESPECIE" in SYSTEM_INSTRUCTIONS
    assert "EVIDENCIA NEGATIVA EN FAUNA" in SYSTEM_INSTRUCTIONS
    assert "SEROLOGÍA/DIAGNÓSTICO NEGATIVO" in SYSTEM_INSTRUCTIONS
    assert "EVIDENCIA MÍNIMA SUFICIENTE" in SYSTEM_INSTRUCTIONS
