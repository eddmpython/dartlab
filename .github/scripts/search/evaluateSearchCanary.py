"""Evaluate product search source/no-answer canary packs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canary", help="JSON/JSONL canary pack path")
    parser.add_argument("--manifest", help="Search manifest JSON containing sourceCanaryPack")
    parser.add_argument("--out", required=True, help="canary report JSON path")
    parser.add_argument("--results-json", help="precomputed results by query JSON path")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--scope", default="auto")
    parser.add_argument("--min-pass-rate", type=float, default=1.0)
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args(argv)

    from dartlab.providers.dart.search.canaryPack import (
        evaluateCanaryPack,
        evaluateCanaryPackRows,
        loadCanaryPack,
        writeCanaryReport,
    )

    canaries = _loadCanaries(args.canary, args.manifest)
    canaries = _injectRefResolution(canaries, args.manifest)
    resultsByQuery = _loadResultsByQuery(args.results_json)
    if resultsByQuery is None:
        from dartlab.providers.dart.search.api import search

        report = evaluateCanaryPack(
            canaries,
            search,
            limit=args.limit,
            scope=args.scope,
            minPassRate=args.min_pass_rate,
        )
    else:
        report = evaluateCanaryPackRows(
            canaries,
            resultsByQuery,
            defaultTopK=args.limit,
            minPassRate=args.min_pass_rate,
        )
    writeCanaryReport(args.out, report)
    print(
        json.dumps(
            {
                "valid": report["valid"],
                "passRate": report["metrics"]["passRate"],
                "failureCount": len(report["failures"]),
            },
            ensure_ascii=False,
        )
    )
    if args.fail_on_error and not report["valid"]:
        return 1
    return 0


def _injectRefResolution(canaries: list[dict[str, Any]], manifestPath: str | None) -> list[dict[str, Any]]:
    """exact-ref 무결성을 결정론 ``_refResolved`` 로 주입 — publish selfcheck 와 동일 SSOT
    (localUpdate.injectSourceRefResolution). bigram 토크나이저서 보일러플레이트 공시는 BM25
    self-retrieval 이 불가능해 랭킹 멤버십 ref 검사는 flaky — 인덱스 아티팩트 직독으로 검증한다.
    인덱스를 못 열면 원본 그대로(BM25 폴백)."""
    if not manifestPath:
        return canaries
    try:
        from dartlab.providers.dart.search.fieldIndex import loadSegment
        from dartlab.providers.dart.search.fieldIndexRebuild import _effectiveSegmentMeta
        from dartlab.providers.dart.search.localUpdate import injectSourceRefResolution, resolveActiveIndexDir

        base = Path(manifestPath).resolve().parent
        indexDir = resolveActiveIndexDir(base) or base
        segments = {name: segment for name in ("main", "delta") if (segment := loadSegment(name, indexDir)) is not None}
        if "main" not in segments:
            return canaries
        effectiveMeta = _effectiveSegmentMeta(
            segments["main"][1],
            segments.get("delta", ({}, None))[1],
        )
        # round-trip 검사가 segment sidecar/docLengths 무결성을 먼저 보장한다. 여기서는 delta override와
        # tombstone을 반영한 유효 meta에서 ref/source 존재를 결정론적으로 확인한다.
        return injectSourceRefResolution(canaries, {"docLengths": [1] * effectiveMeta.height}, effectiveMeta)
    except Exception:  # noqa: BLE001 — 폴백: 결정론 주입 실패 시 기존 BM25 평가로 진행.
        return canaries


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
                out[str(item.get("query") or "")] = [dict(row) for row in item.get("results", [])]
        return out
    raise ValueError(f"unsupported results-json shape: {path}")


def _loadCanaries(canaryPath: str | None, manifestPath: str | None) -> list[dict[str, Any]]:
    if not canaryPath and not manifestPath:
        raise ValueError("one of --canary or --manifest is required")
    if canaryPath:
        from dartlab.providers.dart.search.canaryPack import loadCanaryPack

        return loadCanaryPack(canaryPath)
    manifest = json.loads(Path(str(manifestPath)).read_text(encoding="utf-8"))
    rows = manifest.get("sourceCanaryPack") if isinstance(manifest, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"manifest does not contain sourceCanaryPack: {manifestPath}")
    return [dict(row) for row in rows]


if __name__ == "__main__":
    sys.exit(main())
