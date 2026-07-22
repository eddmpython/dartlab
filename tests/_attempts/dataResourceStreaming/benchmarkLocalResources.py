"""로컬 DART와 EDGAR company-sharded resource streaming 실측.

결과
----
날짜: 2026-07-22.
표본: dart.panel, dart.finance, edgar.panel, edgar.finance 24,489 shard, 18.668 GiB.
핵심 수치: footerFast manifest 합계 6.149초, bounded scan 합계 4.938초, 200,000행.
결론: 최대 RSS 증가 75.254 MiB에서 projection과 predicate pushdown, 50,000행 cap을 지켰다.
다음 단계: structured finance 우선, raw text panel 후순위로 pageable owner executor를 승격한다.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import psutil
import pyarrow as pa

if __package__:
    from .resourceStreaming import (
        ResourcePredicate,
        ResourceReadRequest,
        buildResourceManifest,
        openResourceBatchReader,
    )
else:
    from resourceStreaming import (
        ResourcePredicate,
        ResourceReadRequest,
        buildResourceManifest,
        openResourceBatchReader,
    )

_RESOURCE_SPECS = {
    "dart.panel": {
        "root": "data/dart/panel",
        "columns": ("period", "corp", "rceptNo", "sectionLeaf"),
        "predicates": (ResourcePredicate("period", "ge", "2024"),),
    },
    "dart.finance": {
        "root": "data/dart/finance",
        "columns": ("stock_code", "bsns_year", "sj_div", "account_id", "thstrm_amount"),
        "predicates": (ResourcePredicate("bsns_year", "ge", "2024"),),
    },
    "edgar.panel": {
        "root": "data/edgar/panel",
        "columns": ("period", "corp", "rceptNo", "sectionLeaf"),
        "predicates": (ResourcePredicate("period", "ge", "2024"),),
    },
    "edgar.finance": {
        "root": "data/edgar/finance",
        "columns": ("cik", "tag", "val", "fy", "form", "filed"),
        "predicates": (
            ResourcePredicate("fy", "ge", 2024),
            ResourcePredicate("form", "isin", ("10-K", "10-Q")),
        ),
    },
}


def benchmarkResource(
    resourceId: str,
    integrityMode: str = "footerFast",
) -> dict[str, object]:
    """Resource 하나의 full manifest와 bounded scan을 실측한다.

    Capabilities:
        manifest 시간, scan 시간, RSS peak, Arrow bytes, rows와 batch 수를 반환한다.

    Args:
        resourceId: _RESOURCE_SPECS key.
        integrityMode: full 또는 benchmark 기본 footerFast.

    Returns:
        JSON-compatible benchmark mapping.

    Example:
        ``benchmarkResource("edgar.finance")``.

    Guide:
        resource마다 새 process로 실행해 allocator 잔존 영향을 분리한다.

    SeeAlso:
        resourceStreaming.buildResourceManifest.

    Requires:
        repo local data directory.

    AIContext:
        pageable resource 승격 우선순위를 정하는 실측 자료다.

    LLM Specifications:
        AntiPatterns:
            - 서로 다른 resource를 한 process에서 연속 측정
            - 전체 payload read_all로 OOM 유발
        Freshness:
            2026-07-22 local data snapshot.
        TargetMarkets:
            - KR (DART)
            - US (EDGAR)
    """
    spec = _RESOURCE_SPECS[resourceId]
    process = psutil.Process(os.getpid())
    startRss = process.memory_info().rss
    peakRss = startRss
    manifestStarted = time.perf_counter()
    manifest = buildResourceManifest(
        f"resource.{resourceId}",
        Path(spec["root"]),
        integrityMode=integrityMode,
    )
    manifestSeconds = time.perf_counter() - manifestStarted
    peakRss = max(peakRss, process.memory_info().rss)

    request = ResourceReadRequest(
        columns=spec["columns"],
        predicates=spec["predicates"],
        batchRows=2_048,
        maxRows=50_000,
        maxBytes=16 * 1024 * 1024,
    )
    scanStarted = time.perf_counter()
    peakArrowBytes = pa.total_allocated_bytes()
    with openResourceBatchReader(manifest, request) as reader:
        for _batch in reader:
            peakRss = max(peakRss, process.memory_info().rss)
            peakArrowBytes = max(peakArrowBytes, pa.total_allocated_bytes())
        receipt = reader.receipt()
    scanSeconds = time.perf_counter() - scanStarted
    peakRss = max(peakRss, process.memory_info().rss)
    return {
        "resourceId": resourceId,
        "backend": "duckdb",
        "integrityMode": manifest.integrityMode,
        "root": spec["root"],
        "manifestFiles": len(manifest.entries),
        "manifestGiB": round(manifest.totalBytes / 1024**3, 3),
        "manifestSeconds": round(manifestSeconds, 3),
        "sourcePin": manifest.sourcePin,
        "rows": receipt.rowCount,
        "batches": receipt.batchCount,
        "arrowResultMiB": round(receipt.byteCount / 1024**2, 3),
        "truncated": receipt.truncated,
        "scanSeconds": round(scanSeconds, 3),
        "rssStartMiB": round(startRss / 1024**2, 3),
        "rssPeakMiB": round(peakRss / 1024**2, 3),
        "rssDeltaMiB": round((peakRss - startRss) / 1024**2, 3),
        "arrowPeakMiB": round(peakArrowBytes / 1024**2, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resource", choices=tuple(_RESOURCE_SPECS), required=True)
    parser.add_argument("--integrity-mode", choices=("full", "footerFast"), default="footerFast")
    args = parser.parse_args()
    print(
        json.dumps(
            benchmarkResource(args.resource, integrityMode=args.integrity_mode),
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
