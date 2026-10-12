"""Evaluate product search against real query-log gold."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True, help="JSON/JSONL query-log gold path")
    parser.add_argument("--out", required=True, help="quality report JSON path")
    parser.add_argument("--miss-ledger", help="miss ledger JSONL path")
    parser.add_argument("--results-json", help="precomputed results by query JSON path")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--scope", default="auto")
    parser.add_argument("--min-rows", type=int, default=100)
    parser.add_argument("--required-targets", default="filing,news,noAnswer")
    parser.add_argument("--allow-proxy-query-log", action="store_true")
    parser.add_argument("--fail-on-ineligible", action="store_true")
    parser.add_argument(
        "--as-of",
        choices=("reviewed", "now"),
        default="reviewed",
        help="reviewed: search only documents filed by each row's reviewedAt. now: no date limit.",
    )
    args = parser.parse_args(argv)

    from dartlab.providers.dart.search.qualityGate import (
        buildMissLedgerRows,
        evaluateQueryGoldRows,
        loadQueryGold,
        writeMissLedger,
    )

    goldRows = loadQueryGold(args.gold)
    resultsByQuery = _loadResultsByQuery(args.results_json)
    if resultsByQuery is None:
        resultsByQuery = _runSearch(goldRows, limit=args.limit, scope=args.scope, asOfReviewed=args.as_of == "reviewed")

    requiredTargets = [part.strip() for part in args.required_targets.split(",") if part.strip()]
    report = evaluateQueryGoldRows(
        goldRows,
        resultsByQuery,
        minRows=args.min_rows,
        requiredTargets=requiredTargets,
        requireRealReviewed=not args.allow_proxy_query_log,
    )
    outPath = Path(args.out)
    outPath.parent.mkdir(parents=True, exist_ok=True)
    outPath.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    if args.miss_ledger:
        writeMissLedger(args.miss_ledger, buildMissLedgerRows(goldRows, resultsByQuery))

    print(
        json.dumps({"releaseEligible": report["releaseEligible"], "blockers": report["blockers"]}, ensure_ascii=False)
    )
    if args.fail_on_ineligible and not report["releaseEligible"]:
        return 1
    return 0


def _loadResultsByQuery(path: str | None) -> dict[str, list[dict[str, Any]]] | None:
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return {str(query): [dict(row) for row in rows] for query, rows in data.items()}
    if isinstance(data, list):
        out: dict[str, list[dict[str, Any]]] = {}
        for item in data:
            if isinstance(item, dict):
                rows = [dict(row) for row in item.get("results", [])]
                for key in _resultKeys(item):
                    out[key] = rows
        return out
    raise ValueError(f"unsupported results-json shape: {path}")


def _resultKeys(item: Mapping[str, Any]) -> list[str]:
    keys: list[str] = []
    for field in ("query", "queryId", "id"):
        key = str(item.get(field) or "").strip()
        if key and key not in keys:
            keys.append(key)
    return keys


def _runSearch(
    goldRows: list[dict[str, Any]], *, limit: int, scope: str, asOfReviewed: bool = True
) -> dict[str, list[dict[str, Any]]]:
    """정답셋 질의를 검색한다.

    정답은 검토한 날 존재하던 문서 가운데서 골랐으므로, 기본은 그날까지 접수된 문서만 검색한다.
    그 뒤에 들어온 같은 주제의 새 문서가 정답을 밀어내 생기는 놓침을 품질 저하로 세지 않기 위해서다.
    """
    from dartlab.providers.dart.search.api import search

    out: dict[str, list[dict[str, Any]]] = {}
    for row in goldRows:
        query = str(row.get("query") or "")
        if query in out:
            continue
        end = str(row.get("reviewedAt") or "")[:10].replace("-", "") if asOfReviewed else ""
        out[query] = search(query, limit=limit, scope=scope, end=end or None).to_dicts()
    return out


if __name__ == "__main__":
    sys.exit(main())
