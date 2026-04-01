"""006 — 사전빌드 문서 변화 데이터 → 매출 예측 (전 종목).

changes.parquet: 190만 행, 2535 종목, Company 로드 불필요!
핵심 컬럼:
  - changeType: wording / numeric / structural
  - sizeDelta: 양수=텍스트 증가, 음수=감소 (변화 방향!)
  - sectionTitle: 어느 섹션이 바뀌었는가

가설:
  1. 위험/리스크 관련 섹션의 sizeDelta가 크게 양수 → 위험 내용 추가 → 매출 하락
  2. 사업/매출 관련 섹션의 sizeDelta가 양수 → 사업 확장 설명 → 매출 상승
  3. structural 변화가 많은 기업 → 사업 구조 변화 → 방향 전환
  4. 전체 wording 변화량 → 공시 성실도 또는 변동성 신호

사용법::

    uv run python -X utf8 experiments/106_predictionValidation/006_docDirection.py
"""

from __future__ import annotations

import gc
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import polars as pl

_ROOT = Path(__file__).resolve().parent
_DATA = Path(__file__).resolve().parent.parent.parent / "data"
_RESULT_FILE = _ROOT / "docdirection_results.json"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))


# ---------------------------------------------------------------------------
# 섹션 분류
# ---------------------------------------------------------------------------
RISK_KEYWORDS = ["리스크", "위험", "우발", "소송", "분쟁", "손실", "부채", "채무"]
BIZ_KEYWORDS = ["사업", "매출", "수주", "생산", "제품", "서비스", "시장", "고객", "점유"]
EXPANSION_KEYWORDS = ["설비", "투자", "연구", "개발", "특허", "지식재산", "신규", "해외"]


def _classifySection(title: str) -> str:
    """섹션 제목으로 카테고리 분류."""
    if not title:
        return "other"
    for kw in RISK_KEYWORDS:
        if kw in title:
            return "risk"
    for kw in BIZ_KEYWORDS:
        if kw in title:
            return "business"
    for kw in EXPANSION_KEYWORDS:
        if kw in title:
            return "expansion"
    return "other"


def _growth(val: float, prevVal: float) -> float:
    if prevVal == 0:
        return 0.0
    g = (val - prevVal) / abs(prevVal) * 100
    return max(-200, min(200, g))


def _direction(growth: float) -> str:
    if growth > 1:
        return "up"
    elif growth < -1:
        return "down"
    return "flat"


def main():
    print("=" * 60)
    print("106 예측 검증 — 006 문서 변화 방향 (전 종목, Scan)")
    print("=" * 60)

    # 1. changes.parquet 로드
    print("\n[1/4] changes.parquet 로드...")
    changes = pl.read_parquet(str(_DATA / "dart" / "scan" / "changes.parquet"))
    print(f"  {changes.shape[0]:,} 행, {changes['stockCode'].n_unique()} 종목")

    # 2. 매출 시계열 로드 (Scan)
    print("\n[2/4] 매출 시계열 로드...")
    from dartlab.scan import Scan
    scan = Scan()
    scanResult = scan("account", "매출액")
    revDf = scanResult.df if hasattr(scanResult, "df") else scanResult

    codeCol = "stockCode" if "stockCode" in revDf.columns else revDf.columns[0]
    skipCols = {codeCol, "companyName", "corpName", "종목코드", "회사명", "sector", "업종"}
    qCols = [c for c in revDf.columns if c not in skipCols and c[:1].isdigit()]

    yearSet = set()
    for c in qCols:
        yearSet.add(c[:4])
    years = sorted(yearSet)

    yearQCols = {}
    for y in years:
        yearQCols[y] = sorted([c for c in qCols if c.startswith(y)])

    revSeries: dict[str, dict[str, float]] = {}
    for row in revDf.iter_rows(named=True):
        code = str(row.get(codeCol, ""))
        if not code:
            continue
        annuals = {}
        for y in years:
            qs = yearQCols[y]
            if len(qs) < 4:
                continue
            qvals = [row.get(q) for q in qs]
            if any(v is None for v in qvals):
                continue
            annuals[y] = sum(float(v) for v in qvals)
        if len(annuals) >= 2:
            revSeries[code] = annuals
    print(f"  매출: {len(revSeries)} 종목")

    del revDf, scanResult
    gc.collect()

    # 3. 문서 변화 집계: 2022→2023 변화 → 2024 매출과 비교
    # (문서 변화 = 선행 신호, 매출 = 후행 결과)
    print("\n[3/4] 문서 신호 집계...")

    # 2022→2023 변화를 사용 (2023 공시에서 드러난 변화)
    docChanges = changes.filter(
        (pl.col("fromPeriod") == "2022") & (pl.col("toPeriod") == "2023")
    )
    print(f"  2022→2023 변화: {docChanges.shape[0]:,} 행, {docChanges['stockCode'].n_unique()} 종목")

    # 섹션 분류 추가
    docChanges = docChanges.with_columns(
        pl.col("sectionTitle").map_elements(
            _classifySection, return_dtype=pl.Utf8
        ).alias("sectionCategory")
    )

    # 종목별 집계
    codeSignals: dict[str, dict] = {}
    for code, group in docChanges.group_by("stockCode"):
        code = code[0]
        if code not in revSeries:
            continue
        annuals = revSeries[code]
        if "2023" not in annuals or "2024" not in annuals:
            continue
        if abs(annuals["2023"]) < 10_000_000_000:  # 매출 100억+ 필터
            continue

        gdf = group

        # 카테고리별 sizeDelta 합산
        riskDelta = gdf.filter(pl.col("sectionCategory") == "risk")["sizeDelta"].sum()
        bizDelta = gdf.filter(pl.col("sectionCategory") == "business")["sizeDelta"].sum()
        expDelta = gdf.filter(pl.col("sectionCategory") == "expansion")["sizeDelta"].sum()

        # changeType별 건수
        wordingCount = gdf.filter(pl.col("changeType") == "wording").height
        structuralCount = gdf.filter(pl.col("changeType") == "structural").height
        numericCount = gdf.filter(pl.col("changeType") == "numeric").height

        totalDelta = gdf["sizeDelta"].sum()
        totalChanges = gdf.height

        actualGrowth = _growth(annuals["2024"], annuals["2023"])
        actualDir = _direction(actualGrowth)

        # 2022→2023 매출 방향 (이전 방향)
        prevDir = None
        if "2022" in annuals:
            prevGrowth = _growth(annuals["2023"], annuals["2022"])
            prevDir = _direction(prevGrowth)

        codeSignals[code] = {
            "stockCode": code,
            "riskDelta": int(riskDelta or 0),
            "bizDelta": int(bizDelta or 0),
            "expDelta": int(expDelta or 0),
            "totalDelta": int(totalDelta or 0),
            "totalChanges": totalChanges,
            "wordingCount": wordingCount,
            "structuralCount": structuralCount,
            "numericCount": numericCount,
            "actualGrowth": round(actualGrowth, 1),
            "actualDir": actualDir,
            "prevDir": prevDir,
        }

    records = list(codeSignals.values())
    n = len(records)
    print(f"  분석 대상: {n} 종목")

    if n == 0:
        print("[ERROR] 결과 없음")
        sys.exit(1)

    # 4. 분석
    print(f"\n[4/4] 분석 ({n} 종목)")

    # --- A. 리스크 섹션 sizeDelta vs 매출 ---
    print(f"\n=== A. 리스크 섹션 크기 변화 vs 다음 해 매출 ===")
    print(f"  (riskDelta > 0 = 위험 내용 추가, < 0 = 삭제)")
    rBins = [(-9999999, -100, "대폭축소(<-100)"), (-100, 0, "소폭축소(-100~0)"),
             (0, 100, "소폭증가(0~100)"), (100, 1000, "증가(100~1K)"), (1000, 9999999, "대폭증가(1K+)")]
    for lo, hi, label in rBins:
        subset = [r for r in records if lo <= r["riskDelta"] < hi]
        if not subset:
            continue
        sn = len(subset)
        upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn * 100
        downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn * 100
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:18s}: n={sn:4d}  up={upRate:4.0f}%  down={downRate:4.0f}%  평균={avgGrowth:+.1f}%")

    # --- B. 사업 섹션 sizeDelta vs 매출 ---
    print(f"\n=== B. 사업/매출 섹션 크기 변화 vs 다음 해 매출 ===")
    for lo, hi, label in rBins:
        subset = [r for r in records if lo <= r["bizDelta"] < hi]
        if not subset:
            continue
        sn = len(subset)
        upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn * 100
        downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn * 100
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:18s}: n={sn:4d}  up={upRate:4.0f}%  down={downRate:4.0f}%  평균={avgGrowth:+.1f}%")

    # --- C. 확장 섹션 (설비/R&D/특허) ---
    print(f"\n=== C. 확장 섹션(설비/R&D/특허) 변화 vs 다음 해 매출 ===")
    for lo, hi, label in rBins:
        subset = [r for r in records if lo <= r["expDelta"] < hi]
        if not subset:
            continue
        sn = len(subset)
        upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn * 100
        downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn * 100
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:18s}: n={sn:4d}  up={upRate:4.0f}%  down={downRate:4.0f}%  평균={avgGrowth:+.1f}%")

    # --- D. structural 변화 건수 vs 매출 ---
    print(f"\n=== D. 구조적 변화 건수 vs 다음 해 매출 ===")
    sBins = [(0, 1, "없음(0)"), (1, 5, "소수(1-4)"), (5, 20, "중간(5-19)"), (20, 9999, "많음(20+)")]
    for lo, hi, label in sBins:
        subset = [r for r in records if lo <= r["structuralCount"] < hi]
        if not subset:
            continue
        sn = len(subset)
        upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn * 100
        downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn * 100
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        # 방향 전환율
        turnCount = sum(1 for r in subset if r["prevDir"] and r["prevDir"] != r["actualDir"])
        turnN = sum(1 for r in subset if r["prevDir"])
        turnRate = turnCount / turnN * 100 if turnN > 0 else 0
        print(f"  {label:12s}: n={sn:4d}  up={upRate:4.0f}%  down={downRate:4.0f}%  평균={avgGrowth:+.1f}%  전환={turnRate:.0f}%")

    # --- E. 핵심: 리스크 대폭 증가 + 사업 축소 = 하락 신호? ---
    print(f"\n=== E. 복합 신호: 리스크↑ + 사업↓ = 하락? ===")
    bearSignal = [r for r in records if r["riskDelta"] > 500 and r["bizDelta"] < -100]
    bullSignal = [r for r in records if r["riskDelta"] < -100 and r["bizDelta"] > 500]
    neutral = [r for r in records if r not in bearSignal and r not in bullSignal]

    for label, subset in [("약세신호(risk↑biz↓)", bearSignal),
                          ("강세신호(risk↓biz↑)", bullSignal),
                          ("중립", neutral)]:
        if not subset:
            print(f"  {label:22s}: n=0")
            continue
        sn = len(subset)
        upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn * 100
        downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn * 100
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:22s}: n={sn:4d}  up={upRate:4.0f}%  down={downRate:4.0f}%  평균={avgGrowth:+.1f}%")

    # --- F. 상위/하위 비교 ---
    print(f"\n=== F. 리스크 변화 상위25% vs 하위25% ===")
    sortedByRisk = sorted(records, key=lambda r: r["riskDelta"], reverse=True)
    q = max(1, n // 4)
    top25 = sortedByRisk[:q]
    bottom25 = sortedByRisk[-q:]

    for label, subset in [("상위25%(리스크↑)", top25), ("하위25%(리스크↓)", bottom25)]:
        sn = len(subset)
        upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn * 100
        downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn * 100
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:22s}: n={sn:4d}  up={upRate:4.0f}%  down={downRate:4.0f}%  평균={avgGrowth:+.1f}%")

    # 저장
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total": n,
        "test": "2022→2023 문서변화 → 2024 매출",
        "dataSource": "changes.parquet (사전빌드, Company 미로드)",
    }
    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")

    gc.collect()


if __name__ == "__main__":
    main()
