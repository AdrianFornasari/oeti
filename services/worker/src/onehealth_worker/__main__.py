from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .config import Settings
from .ingestion.pipeline import ingest_html_url


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="onehealth-worker", description="OETI ingestion worker")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest-url", help="Descarga y persiste una página HTML como raw_item")
    ingest.add_argument("--source-code", required=True)
    ingest.add_argument("--url", required=True)

    case = sub.add_parser("ingest-case", help="Procesa todos los targets HTML de un manifiesto de caso")
    case.add_argument("--manifest", required=True, type=Path)

    return parser


def main() -> None:
    args = _parser().parse_args()
    settings = Settings()

    if args.command == "ingest-url":
        result = ingest_html_url(settings.database_url, args.source_code, args.url)
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    results = []
    for target in manifest["targets"]:
        result = ingest_html_url(settings.database_url, target["source_code"], target["url"])
        results.append({"label": target.get("label"), **asdict(result)})
    print(json.dumps({"case_code": manifest["case_code"], "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
