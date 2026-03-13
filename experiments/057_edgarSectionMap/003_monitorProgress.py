"""
실험 ID: 057-003
실험명: 수집 진행 모니터링

목적:
- 002 배치 수집의 현재 상태를 요약한다.
- 언제든 실행해서 진행률, 성공/실패 비율, 예상 남은 시간을 확인한다.

사용법:
    python experiments/057_edgarSectionMap/003_monitorProgress.py

실험일: 2026-03-13
"""

from __future__ import annotations

import json
from pathlib import Path

from dartlab import config


def main() -> None:
    progressPath = Path(__file__).parent / "output" / "collectDocs.progress.jsonl"
    docsDir = Path(config.dataDir) / "edgar" / "docs"

    if not progressPath.exists():
        print("progress 파일 없음")
        return

    rows = []
    with progressPath.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    downloaded = [r for r in rows if r["status"] == "downloaded"]
    timeout = [r for r in rows if r["status"] == "timeout"]
    failed = [r for r in rows if r["status"] == "failed"]
    noData = [r for r in rows if r["status"] == "no_data"]

    totalRows = sum(r.get("rows", 0) for r in downloaded)
    totalFilings = sum(r.get("filings", 0) for r in downloaded)

    parquetFiles = list(docsDir.glob("*.parquet")) if docsDir.exists() else []

    print("=" * 60)
    print("057 EDGAR docs 수집 현황")
    print("=" * 60)
    print(f"progress records: {len(rows)}")
    print(f"  downloaded: {len(downloaded)}")
    print(f"  timeout:    {len(timeout)}")
    print(f"  failed:     {len(failed)}")
    print(f"  no_data:    {len(noData)}")
    print()
    print(f"parquet files on disk: {len(parquetFiles)}")
    print(f"total rows: {totalRows:,}")
    print(f"total filings: {totalFilings:,}")

    if timeout:
        print()
        print(f"timeout tickers ({len(timeout)}): {[r['ticker'] for r in timeout]}")

    if failed:
        print()
        print(f"failed tickers ({len(failed)}):")
        for r in failed[:10]:
            reason = str(r.get("reason", ""))[:100]
            print(f"  {r['ticker']}: {reason}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

    if downloaded:
        avgRows = totalRows / len(downloaded)
        print()
        print(f"avg rows/ticker: {avgRows:.0f}")
        print(f"avg filings/ticker: {totalFilings / len(downloaded):.0f}")

        forms = {}
        for r in downloaded:
            for form in r.get("forms", []):
                forms[form] = forms.get(form, 0) + 1
        print(f"form distribution: {dict(sorted(forms.items()))}")


if __name__ == "__main__":
    main()
