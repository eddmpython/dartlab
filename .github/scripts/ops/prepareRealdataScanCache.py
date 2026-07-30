"""Build shared scan prebuild files for realData CI shards."""

from __future__ import annotations

import sys
from pathlib import Path


def _missingReportApiTypes(scan_dir: Path, required: tuple[str, ...]) -> tuple[str, ...]:
    report_dir = scan_dir / "report"
    return tuple(Path(name).stem for name in required if not (report_dir / name).exists())


def main() -> int:
    from dartlab.scan.builders.kr.common import scanDir
    from dartlab.scan.builders.kr.core import (
        buildAffiliateDocs,
        buildChanges,
        buildFinance,
        buildFinanceLite,
        buildReport,
    )
    from dartlab.scan.builders.kr.shares import buildSharesOutstandingSafe
    from dartlab.scan.io import parquet as scan_parquet
    from dartlab.scan.network.affiliates import isCurrentAffiliateDocsArtifact

    scan_dir = Path(scanDir())
    scan_dir.mkdir(parents=True, exist_ok=True)

    print(f"[prepareRealdataScanCache] build into: {scan_dir}")

    if not (scan_dir / "changes.parquet").exists():
        buildChanges(sinceYear=2021, verbose=True)
    else:
        print("[prepareRealdataScanCache] preserve existing changes.parquet")

    finance_path = None
    if not (scan_dir / "finance.parquet").exists():
        finance_path = buildFinance(sinceYear=2021, verbose=True)
    else:
        print("[prepareRealdataScanCache] preserve existing finance.parquet")

    if finance_path is not None or (
        (scan_dir / "finance.parquet").exists() and not (scan_dir / "finance-lite.parquet").exists()
    ):
        buildFinanceLite(verbose=True)

    missing_report_api_types = _missingReportApiTypes(scan_dir, scan_parquet._REQUIRED_REPORT_FILES)
    if missing_report_api_types:
        buildReport(sinceYear=2016, verbose=True, apiTypes=missing_report_api_types)
    else:
        print("[prepareRealdataScanCache] preserve existing report prebuilds")

    if not (scan_dir / "sharesOutstanding.parquet").exists():
        buildSharesOutstandingSafe(verbose=True)
    else:
        print("[prepareRealdataScanCache] preserve existing sharesOutstanding.parquet")

    affiliate_docs = scan_dir / "network" / "affiliateDocs.parquet"
    if not isCurrentAffiliateDocsArtifact(affiliate_docs):
        buildAffiliateDocs(verbose=True)
    else:
        print("[prepareRealdataScanCache] preserve existing network/affiliateDocs.parquet")

    missing = scan_parquet._missingScanFiles(scan_dir, requireReports=True)
    if missing:
        print("[prepareRealdataScanCache] scan prebuild incomplete", file=sys.stderr)
        for rel in missing[:20]:
            print(f"  - {rel}", file=sys.stderr)
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more", file=sys.stderr)
        return 1

    files = sorted(p for p in scan_dir.rglob("*.parquet") if p.is_file())
    total_size = sum(p.stat().st_size for p in files)
    print(f"[prepareRealdataScanCache] ready: {scan_dir}")
    print(f"[prepareRealdataScanCache] files={len(files)} size_mb={total_size / 1024 / 1024:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
