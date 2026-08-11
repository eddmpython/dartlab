"""Evaluate product search source/no-answer canary packs."""

from __future__ import annotations

import argparse
import hashlib
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
    parser.add_argument(
        "--require-deterministic",
        action="store_true",
        help="Fail when manifest metadata cannot provide deterministic source/ref resolution.",
    )
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
    if args.require_deterministic:
        canaries = [{**row, "_requireDeterministic": True} for row in canaries]
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
                "injectionModes": sorted(
                    {str(row.get("injectionMode") or "") for row in report["rows"] if row.get("injectionMode")}
                ),
            },
            ensure_ascii=False,
        )
    )
    if args.fail_on_error and not report["valid"]:
        return 1
    return 0


def _injectRefResolution(canaries: list[dict[str, Any]], manifestPath: str | None) -> list[dict[str, Any]]:
    """Inject deterministic source/ref resolution from the exact manifest metadata.

    Regression for #107. The canary only needs bounded metadata and must not load the
    full postings arrays. The manifest hash check binds each metadata file to the
    candidate that supplied the canary pack.
    """
    if not manifestPath:
        return _markInjectionFallback(canaries, "manifestMissing")
    try:
        from dartlab.providers.dart.search.fieldIndexRebuild import _effectiveSegmentMeta, _readManifestMeta
        from dartlab.providers.dart.search.localUpdate import injectSourceRefResolution

        manifestFile = Path(manifestPath).resolve()
        manifest = json.loads(manifestFile.read_text(encoding="utf-8"))
        indexDir = manifestFile.parent
        hashes = manifest.get("fileHashes") if isinstance(manifest.get("fileHashes"), dict) else {}
        segmentMeta: dict[str, Any] = {}
        names = ["main"] + (["delta"] if bool(manifest.get("hasDelta")) else [])
        for name in names:
            metaPath = indexDir / f"{name}_meta.parquet"
            if not metaPath.exists():
                raise FileNotFoundError(metaPath.name)
            expectedHash = str(hashes.get(metaPath.name) or "")
            if expectedHash and _sha256File(metaPath) != expectedHash:
                raise ValueError(f"metadataHashMismatch:{metaPath.name}")
            segmentMeta[name] = _readManifestMeta(metaPath)
        effectiveMeta = _effectiveSegmentMeta(
            segmentMeta["main"],
            segmentMeta.get("delta"),
        )
        enriched = injectSourceRefResolution(canaries, {"docLengths": [1] * effectiveMeta.height}, effectiveMeta)
        return [{**row, "_injectionMode": "deterministic"} for row in enriched]
    except Exception as exc:  # noqa: BLE001 - report a bounded diagnostic before BM25 fallback.
        return _markInjectionFallback(canaries, exc.__class__.__name__)


def _markInjectionFallback(canaries: list[dict[str, Any]], error: str) -> list[dict[str, Any]]:
    return [{**row, "_injectionMode": "bm25Fallback", "_injectionError": error} for row in canaries]


def _sha256File(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
