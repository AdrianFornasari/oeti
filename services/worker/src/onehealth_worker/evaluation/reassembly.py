from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..extraction.assembly_v045 import assemble_claims_payload
from ..extraction.normalization import normalize_extraction_payload
from ..extraction.schema import (
    load_atomic_claims_schema,
    load_schema,
    validate_atomic_claims,
    validate_extraction,
)


def reassemble_evaluation_corpus(*, manifest_path: Path, force: bool = False) -> dict[str, Any]:
    """Rebuild benchmark predictions from existing atomic-claims sidecars only.

    This path intentionally performs no network, database, or LLM calls. It isolates
    assembler/evaluator changes from provider variability and API cost.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    base = manifest_path.parent
    claims_schema = load_atomic_claims_schema()
    signal_schema = load_schema()
    results: list[dict[str, Any]] = []

    for item in manifest.get("documents", []):
        if item.get("status") != "adjudicated":
            results.append({"label": item.get("label"), "status": "skipped_not_adjudicated"})
            continue

        claims_rel = item.get("claims")
        prediction_rel = item.get("prediction")
        if not claims_rel or not prediction_rel:
            results.append({"label": item.get("label"), "status": "skipped_missing_config"})
            continue

        claims_path = (base / claims_rel).resolve()
        prediction_path = (base / prediction_rel).resolve()
        if not claims_path.exists():
            results.append({
                "label": item.get("label"),
                "status": "skipped_claims_not_found",
                "claims_path": str(claims_path),
            })
            continue
        if prediction_path.exists() and not force:
            results.append({
                "label": item.get("label"),
                "status": "existing",
                "path": str(prediction_path),
                "claims_path": str(claims_path),
            })
            continue

        claims_payload = json.loads(claims_path.read_text(encoding="utf-8-sig"))
        validate_atomic_claims(claims_payload, claims_schema)
        payload = normalize_extraction_payload(assemble_claims_payload(claims_payload))
        validate_extraction(payload, signal_schema)

        prediction_path.parent.mkdir(parents=True, exist_ok=True)
        prediction_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append({
            "label": item.get("label"),
            "status": "reassembled",
            "claims_path": str(claims_path),
            "path": str(prediction_path),
            "claims": len(claims_payload.get("claims", [])),
            "signals": len(payload.get("signals", [])),
        })

    return {
        "case_code": manifest.get("case_code"),
        "architecture": "atomic_claims_v0.1+deterministic_signal_assembly_v0.4.5",
        "llm_invoked": False,
        "results": results,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m onehealth_worker.evaluation.reassembly",
        description="Reensambla predicciones de benchmark desde sidecars atomic claims existentes.",
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    args = _parser().parse_args()
    result = reassemble_evaluation_corpus(manifest_path=args.manifest, force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
