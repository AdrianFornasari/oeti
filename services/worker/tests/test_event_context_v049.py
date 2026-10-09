from onehealth_worker.evaluation.event_context_v049 import (
    extract_event_context_anchors,
    resolve_signal_event_context_anchors,
)


def test_extracts_named_vessel_anchor():
    anchors = extract_event_context_anchors(
        "Se detect? un brote en el crucero MV Hondius."
    )

    assert anchors == (
        "vessel:mv hondius",
    )


def test_inherits_anchor_across_anaphoric_paragraph():
    raw_text = (
        "Se investiga un brote en el buque MV Hondius.\n\n"
        "Los casos contin?an en estudio y se realizan pruebas "
        "adicionales para identificar la cepa y origen del brote."
    )

    signal = {
        "signal_summary": (
            "Se realizan pruebas adicionales."
        ),
        "evidence": [
            {
                "text": (
                    "se realizan pruebas adicionales para identificar "
                    "la cepa y origen del brote"
                )
            }
        ],
    }

    anchors = (
        resolve_signal_event_context_anchors(
            signal,
            raw_text,
        )
    )

    assert anchors == (
        "vessel:mv hondius",
    )


def test_reporting_context_reset_blocks_inheritance():
    raw_text = (
        "Se investiga un brote en el crucero MV Hondius.\n\n"
        "A nivel nacional, en las ?ltimas dos semanas s?lo se "
        "notific? un caso nuevo de hantavirus en el pa?s."
    )

    signal = {
        "signal_summary": (
            "Se notific? un caso nuevo de hantavirus."
        ),
        "evidence": [
            {
                "text": (
                    "en las ?ltimas dos semanas s?lo se notific? "
                    "un caso nuevo de hantavirus en el pa?s"
                )
            }
        ],
    }

    anchors = (
        resolve_signal_event_context_anchors(
            signal,
            raw_text,
        )
    )

    assert anchors == ()


def test_no_anaphora_does_not_inherit_previous_anchor():
    raw_text = (
        "Se investiga un brote en el buque MV Hondius.\n\n"
        "Se notificaron dos casos de influenza en otra provincia."
    )

    signal = {
        "signal_summary": (
            "Dos casos de influenza."
        ),
        "evidence": [
            {
                "text": (
                    "Se notificaron dos casos de influenza "
                    "en otra provincia"
                )
            }
        ],
    }

    anchors = (
        resolve_signal_event_context_anchors(
            signal,
            raw_text,
        )
    )

    assert anchors == ()
