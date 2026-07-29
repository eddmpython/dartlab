"""panel native 전수 census . panel.parquet 단일 artifact 에서 native is/bs/cf/ratios 가 나오는지 검사.

panelCell 별 artifact 없이 ``c.panel("is")``/``c.panel("ratios")`` 는 panel.parquet 의 5표 contentRaw 를
read-time 분해(``cell._cellsFromPanel``)한다. 본 census 는 ``data/dart/panel/{code}/`` 종목별로:
    - panel.parquet period 수
    - 재무 5표(BS/IS1/IS2/IS3/CF/EF) 셀 커버 (in-memory 분해 결과)
    - 손익(IS1/2/3) 읽힘 여부 (연간→분기 폴백)
    - native 비율 행 수

회사당 ``_cellsFromPanel`` 1회만 파싱(lxml) 후 순수 함수로 재사용. 전수는 multiprocessing.

핵심 판정:
    - ``no_panel`` / ``no_cells``: panel.parquet 없음 / 5표 셀 분해 0 (stale disclosureKey = 재빌드 필요).
    - ``no_income_statement``: IS1/2/3 자체 부재 (구조화 재무 없는 신규/SPAC = 정상).
    - ``income_unreadable``: 손익 셀은 있는데 read 실패 = **진짜 버그 신호** (0 이어야 정상).

사용법::

    uv run python -X utf8 tests/audit/panelNativeCensus.py                 # 전종목 (multiprocessing)
    uv run python -X utf8 tests/audit/panelNativeCensus.py --codes 005930,000660
    uv run python -X utf8 tests/audit/panelNativeCensus.py --limit 200 --workers 4

종료 코드: 0 (보고용). --strict 면 income_unreadable 발견 시 1.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
from pathlib import Path

import dartlab.config as _cfg

_INCOME = {"IS1", "IS2", "IS3"}


def _censusOne(code: str) -> dict:
    """종목 1개 census . _cellsFromPanel 1회 파싱 후 순수 함수 재사용 (손익/비율)."""
    import polars as pl

    from dartlab.core.ratios import calcRatioSeries
    from dartlab.providers.dart.panel.cell import (
        STATEMENT_VARIANTS,
        _assembleRatioSeries,
        _cellsFromPanel,
        _ratiosToWide,
        _resolveStatement,
        cellStatements,
    )

    five = cellStatements()
    panelDir = Path(_cfg.dataDir) / "dart" / "panel" / code
    files = sorted(panelDir.glob("*.parquet")) if panelDir.exists() else []
    rec: dict = {"code": code, "periods": len(files), "statements": [], "ratioRows": 0, "isMinYear": None, "issues": []}
    if not files:
        rec["issues"].append("no_panel")
        return rec
    cells = _cellsFromPanel(code)  # 1회 lxml 파싱
    if cells is None:
        rec["issues"].append("no_cells")
        return rec
    rec["statements"] = sorted(s for s in cells["statement"].unique().to_list() if s in five)
    hasIncomeStmt = bool(set(rec["statements"]) & _INCOME)
    if not hasIncomeStmt:
        rec["issues"].append("no_income_statement")

    income = None
    for fr in ("year", "quarter", "ytd"):
        w = _resolveStatement(cells, variants=STATEMENT_VARIANTS["is"], freq=fr)
        if w is not None and not w.is_empty():
            income = w
            break
    rec["hasIncome"] = income is not None
    if not rec["hasIncome"] and hasIncomeStmt:
        rec["issues"].append("income_unreadable")  # 진짜 버그 신호
    if income is not None:
        cols = [c for c in income.columns if c[:4].isdigit()]
        rec["isMinYear"] = min(cols) if cols else None

    for fr in ("year", "quarter", "ytd"):
        src = {
            "BS": _resolveStatement(cells, variants=STATEMENT_VARIANTS["bs"], freq=fr),
            "IS": _resolveStatement(cells, variants=STATEMENT_VARIANTS["is"], freq=fr),
            "CF": _resolveStatement(cells, variants=STATEMENT_VARIANTS["cf"], freq=fr),
        }
        asm = _assembleRatioSeries(src)
        if asm is None:
            continue
        series, years = asm
        rs = calcRatioSeries(
            series,
            years,
            annual=fr != "quarter",
            yoyLag=(4 if fr in {"quarter", "ytd"} else 1),
        )
        wide = _ratiosToWide(rs, years)
        if wide is not None and not wide.is_empty():
            rec["ratioRows"] = wide.height
            break
    _ = pl  # noqa
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description="panel native 전수 census")
    ap.add_argument("--codes", type=str, default="", help="콤마구분 종목. 빈값=전종목")
    ap.add_argument("--limit", type=int, default=0, help="표본 N 종목 (0=전체)")
    ap.add_argument("--workers", type=int, default=4, help="multiprocessing workers")
    ap.add_argument("--out", type=str, default="dist/panelNative_census.json", help="JSON 출력 경로")
    ap.add_argument("--strict", action="store_true", help="income_unreadable 발견 시 exit 1")
    args = ap.parse_args()

    base = Path(_cfg.dataDir) / "dart" / "panel"
    if args.codes:
        codes = [c.strip() for c in args.codes.split(",") if c.strip()]
    elif base.exists():
        codes = sorted(d.name for d in base.iterdir() if d.is_dir() and d.name != "spine")
    else:
        codes = []
    if args.limit > 0:
        codes = codes[: args.limit]

    if args.workers > 1 and len(codes) > 1:
        with mp.Pool(processes=args.workers) as pool:
            records = pool.map(_censusOne, codes, chunksize=8)
    else:
        records = [_censusOne(c) for c in codes]

    withCells = [r for r in records if r["statements"]]
    withRatios = [r for r in records if r["ratioRows"] > 0]
    unreadable = [r for r in records if "income_unreadable" in r["issues"]]
    noIncome = [r for r in records if "no_income_statement" in r["issues"]]
    noPanel = [r for r in records if "no_panel" in r["issues"] or "no_cells" in r["issues"]]

    print(f"[panelNative-census] {len(codes)}종목")
    print(f"  셀보유 {len(withCells)} / 비율보유 {len(withRatios)}")
    print(f"  no_panel·no_cells(미빌드/stale) {len(noPanel)}")
    print(f"  no_income_statement(구조화재무 없음=정상) {len(noIncome)}")
    print(f"  ★ income_unreadable(셀있는데 read실패=버그) {len(unreadable)}")
    for r in unreadable[:30]:
        print(f"    BUG {r['code']}: statements={r['statements']}")

    outPath = Path(args.out)
    outPath.parent.mkdir(parents=True, exist_ok=True)
    outPath.write_text(
        json.dumps(
            {
                "total": len(codes),
                "withCells": len(withCells),
                "withRatios": len(withRatios),
                "noPanel": len(noPanel),
                "noIncome": len(noIncome),
                "incomeUnreadable": len(unreadable),
                "records": records,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"[panelNative-census] → {outPath}")
    return 1 if (args.strict and unreadable) else 0


if __name__ == "__main__":
    sys.exit(main())
