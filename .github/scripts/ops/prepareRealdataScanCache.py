"""Build shared scan prebuild files for realData CI shards."""

from __future__ import annotations

import sys
from pathlib import Path


def _missingReportApiTypes(scan_dir: Path, required: tuple[str, ...]) -> tuple[str, ...]:
    report_dir = scan_dir / "report"
    return tuple(Path(name).stem for name in required if not (report_dir / name).exists())


def _ensureCorpProfile(scan_dir: Path) -> None:
    """affiliateDocs 가 요구하는 corpProfile identity parquet 을 HF 에서 내려받는다.

    책임 위치 SSOT(buildCorpProfile docstring): 외부 API 빌드는 sync(kindlist cron)
    소유이고 prebuild 는 HF 에 매일 업로드된 parquet 을 다운로드만 한다. 실측
    (2026-08-04): 이 준비 단계가 없어 CI 의 buildAffiliateDocs 가
    CorpProfileIdentityError 로 죽고 realdata-suite 가 통째로 skipped 됐다
    (11927a04e 가 corpProfile 의존을 추가하며 준비 단계를 넣지 않음). 다운로드
    실패는 삼키지 않는다: 어차피 affiliateDocs 빌드가 같은 부재로 죽는다.
    """
    import shutil

    from huggingface_hub import hf_hub_download

    corp_profile = scan_dir / "corpProfile.parquet"
    if corp_profile.exists():
        print("[prepareRealdataScanCache] preserve existing corpProfile.parquet")
        return
    downloaded = hf_hub_download(
        repo_id="eddmpython/dartlab-data",
        repo_type="dataset",
        filename="dart/scan/corpProfile.parquet",
    )
    shutil.copy(downloaded, corp_profile)
    print("[prepareRealdataScanCache] corpProfile.parquet <- HF dataset")


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
