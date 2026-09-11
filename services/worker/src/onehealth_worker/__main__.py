from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .config import Settings
from .extraction.file_pipeline import persist_file, validate_file
from .extraction.pipeline import extract_raw_item
from .ingestion.pipeline import ingest_html_url


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="onehealth-worker", description="OETI ingestion and extraction worker")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest-url", help="Descarga y persiste una página HTML como raw_item")
    ingest.add_argument("--source-code", required=True)
    ingest.add_argument("--url", required=True)

    case = sub.add_parser("ingest-case", help="Procesa todos los targets HTML de un manifiesto de caso")
    case.add_argument("--manifest", required=True, type=Path)

    extract = sub.add_parser("extract-raw-item", help="Extrae señales estructuradas desde un raw_item")
    extract.add_argument("--raw-item-id", required=True)
    extract.add_argument("--provider", default=None, help="Default: LLM_PROVIDER")
    extract.add_argument("--model", default=None, help="Default: LLM_MODEL")
    extract.add_argument("--schema", type=Path, default=None)
    extract.add_argument("--no-persist", action="store_true", help="Valida y muestra JSON sin escribir signals")
    extract.add_argument("--output", type=Path, default=None, help="Guarda una copia del JSON estructurado")

    validate = sub.add_parser("validate-extraction", help="Valida un JSON de extracción contra el contrato")
    validate.add_argument("--file", required=True, type=Path)
    validate.add_argument("--schema", type=Path, default=None)

    persist = sub.add_parser("persist-extraction", help="Persiste un JSON de extracción previamente validado")
    persist.add_argument("--file", required=True, type=Path)
    persist.add_argument("--schema", type=Path, default=None)
    persist.add_argument("--provider", default="manual_json")
    persist.add_argument("--model", default="manual_or_fixture")

    return parser


def main() -> None:
    args = _parser().parse_args()
    settings = Settings()

    if args.command == "ingest-url":
        result = ingest_html_url(settings.database_url, args.source_code, args.url)
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return

    if args.command == "ingest-case":
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        results = []
        for target in manifest["targets"]:
            result = ingest_html_url(settings.database_url, target["source_code"], target["url"])
            results.append({"label": target.get("label"), **asdict(result)})
        print(json.dumps({"case_code": manifest["case_code"], "results": results}, ensure_ascii=False, indent=2))
        return

    if args.command == "validate-extraction":
        payload = validate_file(args.file, args.schema)
        print(json.dumps({"valid": True, "signals": len(payload.get("signals", []))}, ensure_ascii=False, indent=2))
        return

    if args.command == "persist-extraction":
        run_id, warnings = persist_file(
            database_url=settings.database_url,
            path=args.file,
            provider=args.provider,
            model_name=args.model,
            schema_path=args.schema,
        )
        print(json.dumps({"persisted": True, "extraction_run_id": run_id, "warnings": warnings}, ensure_ascii=False, indent=2))
        return

    provider = args.provider or settings.llm_provider
    model = args.model or settings.llm_model
    if not settings.llm_api_key:
        raise SystemExit("Falta LLM_API_KEY en .env para ejecutar extract-raw-item con provider=openai.")

    result = extract_raw_item(
        database_url=settings.database_url,
        raw_item_id=args.raw_item_id,
        provider_name=provider,
        model_name=model,
        api_key=settings.llm_api_key,
        schema_path=args.schema,
        persist=not args.no_persist,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result.payload, ensure_ascii=False, indent=2), encoding="utf-8")

    printable = asdict(result)
    if args.no_persist:
        printable["payload"] = result.payload
    else:
        printable.pop("payload", None)
    print(json.dumps(printable, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
