"""scan 산출물 커버리지 census: 실제 구워진 scan parquet 을 유니버스 대비 실측.

``extractionCoverageCensus`` 는 panel 원신호(추출 *가능성*)를 재고, 본 도구는 그 하류인 scan
프리빌드 산출물(``report/`` · ``note/`` · root parquet)이 전 유니버스로 실제 구워졌는지를 잰다.
note 가 조용히 DARK 로 회귀한 사건(HF 404, 배선은 완비인데 산출물 부재)처럼 "panel census 는 ok
인데 scan 축은 empty" 맹점을 닫는 기계 게이트다. Company facade 를 안 잡고 폴라스 직독(finance 는
lazy unique)만 해 OOM 안전(CLAUDE.md Polars Rust 힙 가드).

**판정**: 기대 산출물(SCAN_API_TYPES 24 + SCAN_NOTE_CONCEPTS 30 + root)마다 (행수·종목수·최신기간)을
재고 DARK(부재/빈) · THIN(< floor) · LIVE 로 분류. CORE(finance + report 전부)가 DARK 면 exit 1
(프리빌드 실패 신호). note/narrative 등 산업편중·희소 축은 THIN 을 정직 gap 으로 보고만 한다.

실행::

    uv run python -X utf8 tests/audit/scanOutputCensus.py          # 원장 출력
    uv run python -X utf8 tests/audit/scanOutputCensus.py --json   # JSON
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import polars as pl

# 유니버스 기대치(상장사 ~2900). CORE 축은 이 floor 를 넘어야 정상.
_UNIVERSE_FLOOR = 1500
_CORE_FLOOR = 2000


def _scanDir() -> Path:
    """scan 산출물 디렉토리 경로 (dataConfig SSOT, 실패 시 관례 경로)."""
    try:
        from dartlab.core.dataConfig import DATA_RELEASES, dataRoot

        return Path(dataRoot()) / DATA_RELEASES["scan"]["dir"]
    except (ImportError, KeyError, AttributeError, ValueError):
        return Path("data/dart/scan")


def _coverage(path: Path, codeCol: str = "stockCode") -> tuple[int, int, str | None]:
    """단일 parquet 의 (행수, 고유 종목수, 최신 period). 부재/오류는 (0,0,None). 큰 파일은 lazy."""
    if not path.exists():
        return 0, 0, None
    try:
        lf = pl.scan_parquet(str(path))
        cols = lf.collect_schema().names()
        if codeCol not in cols:
            codeCol = "종목코드" if "종목코드" in cols else next((c for c in cols if c.lower() == "stockcode"), "")
        rows = lf.select(pl.len()).collect().item()
        codes = lf.select(pl.col(codeCol).n_unique()).collect().item() if codeCol else 0
        latest: str | None = None
        if "period" in cols:
            latest = lf.select(pl.col("period").max()).collect().item()
        elif "bsns_year" in cols:
            latest = str(lf.select(pl.col("bsns_year").max()).collect().item())
        return int(rows), int(codes), latest
    except (pl.exceptions.PolarsError, OSError, ValueError):
        return 0, 0, None


def _status(codes: int, floor: int) -> str:
    """종목수 기준 DARK/THIN/LIVE 분류."""
    if codes <= 0:
        return "DARK"
    if codes < floor:
        return "THIN"
    return "LIVE"


def censusRows() -> list[dict]:
    """기대 scan 산출물 전수(root + report 24 + note 30)의 커버리지 원장을 반환한다.

    Returns:
        [{artifact, category, rows, codes, latest, status}] 리스트. 부재 산출물은 status=DARK.
    """
    from dartlab.scan.builders.kr.notes import SCAN_NOTE_CONCEPTS
    from dartlab.scan.builders.kr.report.build import SCAN_API_TYPES

    sd = _scanDir()
    rows: list[dict] = []

    rootFiles = [
        ("finance.parquet", "core"),
        ("changes.parquet", "core"),
        ("valuation.parquet", "valuation"),
        ("salesByProduct.parquet", "segment"),
        ("narrativeMetrics.parquet", "narrative"),
        ("sharesOutstanding.parquet", "shares"),
    ]
    for name, cat in rootFiles:
        r, c, latest = _coverage(sd / name)
        floor = _CORE_FLOOR if cat == "core" else _UNIVERSE_FLOOR
        rows.append(
            {"artifact": name, "category": cat, "rows": r, "codes": c, "latest": latest, "status": _status(c, floor)}
        )

    for apiType in SCAN_API_TYPES:
        r, c, latest = _coverage(sd / "report" / f"{apiType}.parquet")
        rows.append(
            {
                "artifact": f"report/{apiType}",
                "category": "report",
                "rows": r,
                "codes": c,
                "latest": latest,
                "status": _status(c, _CORE_FLOOR),
            }
        )

    for bare, _ntKey, _label in SCAN_NOTE_CONCEPTS:
        r, c, latest = _coverage(sd / "note" / f"{bare}.parquet")
        rows.append(
            {
                "artifact": f"note/{bare}",
                "category": "note",
                "rows": r,
                "codes": c,
                "latest": latest,
                "status": _status(c, _UNIVERSE_FLOOR),
            }
        )

    return rows


def summarize(rows: list[dict]) -> dict:
    """census 원장을 status/category 집계 + CORE DARK 목록으로 요약한다.

    Returns:
        {counts, coreDark, totalArtifacts} dict. coreDark 는 core/report 중 DARK 인 artifact.
    """
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    coreDark = [r["artifact"] for r in rows if r["category"] in ("core", "report") and r["status"] == "DARK"]
    return {"counts": counts, "coreDark": coreDark, "totalArtifacts": len(rows)}


def main() -> None:
    """census 원장을 출력하고 CORE 축이 DARK 면 exit 1 (프리빌드 실패 신호)."""
    ap = argparse.ArgumentParser(description="scan 산출물 커버리지 census")
    ap.add_argument("--json", action="store_true", help="JSON 출력")
    args = ap.parse_args()

    rows = censusRows()
    summary = summarize(rows)

    if args.json:
        print(json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False, indent=2))
    else:
        print("=== scan 산출물 커버리지 census (실제 구워진 parquet) ===")
        print(f"{'artifact':28s} {'cat':10s} {'status':6s} {'종목':>6s} {'행':>10s}  최신")
        for row in sorted(rows, key=lambda x: (x["category"], -x["codes"])):
            print(
                f"  {row['artifact']:26s} {row['category']:10s} {row['status']:6s} "
                f"{row['codes']:6d} {row['rows']:10d}  {row['latest'] or '-'}"
            )
        print("\n=== 집계 ===")
        for k, v in sorted(summary["counts"].items(), key=lambda x: -x[1]):
            print(f"  {k:6s} {v}")
        if summary["coreDark"]:
            print(f"\n  ❌ CORE DARK: {summary['coreDark']}")

    if summary["coreDark"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
