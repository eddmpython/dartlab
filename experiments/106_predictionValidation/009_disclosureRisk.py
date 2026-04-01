"""009 — disclosureRisk 4시그널 → 매출 변화 예측력 검증.

scan 엔진의 disclosureRisk가 이미 changes.parquet에서
방향성 있는 구조적 시그널 4개를 추출한다:
  - contingentDebt: 우발부채 섹션 증가 (숨겨진 부채)
  - auditStruct: 감사/내부통제 구조 변경 3건+
  - affiliateChange: 계열/타법인 numeric 변화 (M&A)
  - bizPivot: 사업 내용 대규모 변경 (|delta|>5000)

이 시그널이 다음 해 매출 방향과 관련이 있는지 검증한다.
2개 연도 교차 검증 (008과 동일 구조).

사용법::

    uv run python -X utf8 experiments/106_predictionValidation/009_disclosureRisk.py
"""

from __future__ import annotations

import gc
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

_ROOT = Path(__file__).resolve().parent
_DATA = Path(__file__).resolve().parent.parent.parent / "data"
_RESULT_FILE = _ROOT / "disclosurerisk_results.json"


def _growth(val: float, prevVal: float) -> float:
    if prevVal == 0:
        return 0.0
    return max(-200, min(200, (val - prevVal) / abs(prevVal) * 100))


def _direction(g: float) -> str:
    if g > 1:
        return "up"
    elif g < -1:
        return "down"
    return "flat"


def _binomTest(k: int, n: int, p0: float) -> float:
    if n == 0:
        return 1.0
    pHat = k / n
    se = math.sqrt(p0 * (1 - p0) / n) if p0 * (1 - p0) > 0 else 1e-9
    z = (pHat - p0) / se
    return 0.5 * (1 + math.erf(-z / math.sqrt(2)))


def _computeSignals(changes: pl.DataFrame) -> pl.DataFrame:
    """disclosureRisk 로직을 재현 (특정 기간용)."""

    # 1. contingentDebt
    contingent = (
        changes.filter(
            pl.col("sectionTitle").str.contains("우발부채")
            & (pl.col("sizeDelta") > 0)
        )
        .group_by("stockCode")
        .agg(pl.col("sizeDelta").sum().alias("contingentDebt"))
    )

    # 2. auditStruct
    auditStruct = (
        changes.filter(
            (pl.col("sectionTitle").str.contains("감사") | pl.col("sectionTitle").str.contains("내부통제"))
            & (pl.col("changeType") == "structural")
        )
        .group_by("stockCode")
        .agg(pl.len().alias("auditStruct"))
    )

    # 3. affiliateChange
    affiliate = (
        changes.filter(
            (pl.col("sectionTitle").str.contains("계열") | pl.col("sectionTitle").str.contains("타법인출자"))
            & (pl.col("changeType") == "numeric")
        )
        .group_by("stockCode")
        .agg(pl.len().alias("affiliateChange"))
    )

    # 4. bizPivot
    bizPivot = (
        changes.filter(
            pl.col("sectionTitle").str.contains("사업의")
            & (pl.col("sizeDelta").abs() > 5000)
        )
        .group_by("stockCode")
        .agg(pl.col("sizeDelta").abs().max().alias("bizPivot"))
    )

    # 5. 추가: 수주/생산 변화 (매출 직접 선행 신호)
    orderChange = (
        changes.filter(
            (pl.col("sectionTitle").str.contains("수주") | pl.col("sectionTitle").str.contains("생산"))
            & (pl.col("changeType").is_in(["numeric", "structural"]))
        )
        .group_by("stockCode")
        .agg([
            pl.len().alias("orderChangeCount"),
            pl.col("sizeDelta").sum().alias("orderSizeDelta"),
        ])
    )

    # 6. 추가: 설비/투자 변화
    investChange = (
        changes.filter(
            (pl.col("sectionTitle").str.contains("설비") | pl.col("sectionTitle").str.contains("투자"))
            & (pl.col("changeType").is_in(["numeric", "structural"]))
        )
        .group_by("stockCode")
        .agg([
            pl.len().alias("investChangeCount"),
            pl.col("sizeDelta").sum().alias("investSizeDelta"),
        ])
    )

    # 병합
    allCodes = changes.select("stockCode").unique()
    result = allCodes
    for right in [contingent, auditStruct, affiliate, bizPivot, orderChange, investChange]:
        result = result.join(right, on="stockCode", how="left")
    result = result.fill_null(0)

    # activeSignals (원본 4개)
    result = result.with_columns(
        (
            (pl.col("contingentDebt") > 0).cast(pl.Int8)
            + (pl.col("auditStruct") >= 3).cast(pl.Int8)
            + (pl.col("affiliateChange") > 0).cast(pl.Int8)
            + (pl.col("bizPivot") > 0).cast(pl.Int8)
        ).alias("activeSignals")
    )

    return result


def _loadRevSeries() -> dict[str, dict[str, float]]:
    from dartlab.scan import Scan
    scan = Scan()
    r = scan("account", "매출액")
    df = r.df if hasattr(r, "df") else r
    codeCol = "stockCode" if "stockCode" in df.columns else df.columns[0]
    skipCols = {codeCol, "companyName", "corpName", "종목코드", "회사명", "sector", "업종"}
    qCols = [c for c in df.columns if c not in skipCols and c[:1].isdigit()]
    yearSet = set()
    for c in qCols:
        yearSet.add(c[:4])
    years = sorted(yearSet)
    yearQCols = {y: sorted([c for c in qCols if c.startswith(y)]) for y in years}
    result = {}
    for row in df.iter_rows(named=True):
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
        if len(annuals) >= 3:
            result[code] = annuals
    del df, r
    gc.collect()
    return result


def _analyzeOnePeriod(signals: pl.DataFrame, revSeries: dict, fromY: str, toY: str, testY: str):
    """한 기간 분석."""
    records = []
    for row in signals.iter_rows(named=True):
        code = row["stockCode"]
        annuals = revSeries.get(code, {})
        if toY not in annuals or testY not in annuals:
            continue
        if abs(annuals[toY]) < 10_000_000_000:
            continue

        actualGrowth = _growth(annuals[testY], annuals[toY])
        actualDir = _direction(actualGrowth)

        prevDir = None
        if fromY in annuals:
            prevDir = _direction(_growth(annuals[toY], annuals[fromY]))

        records.append({**row, "actualGrowth": actualGrowth, "actualDir": actualDir, "prevDir": prevDir})

    return records


def main():
    print("=" * 60)
    print("106 예측 검증 — 009 disclosureRisk 시그널 검증")
    print("=" * 60)

    print("\n[1/3] 데이터 로드...")
    allChanges = pl.read_parquet(str(_DATA / "dart" / "scan" / "changes.parquet"))
    revSeries = _loadRevSeries()
    print(f"  changes: {allChanges.shape[0]:,} 행, 매출: {len(revSeries)} 종목")

    periods = [
        ("2021", "2022", "2023"),
        ("2022", "2023", "2024"),
    ]

    for fromY, toY, testY in periods:
        print(f"\n{'='*60}")
        print(f"[2/3] {fromY}→{toY} 시그널 → {testY} 매출")
        print(f"{'='*60}")

        periodChanges = allChanges.filter(
            (pl.col("fromPeriod") == fromY) & (pl.col("toPeriod") == toY)
        )
        signals = _computeSignals(periodChanges)
        records = _analyzeOnePeriod(signals, revSeries, fromY, toY, testY)
        n = len(records)
        if n == 0:
            print("  결과 없음")
            continue

        baseUp = sum(1 for r in records if r["actualDir"] == "up") / n
        baseDown = sum(1 for r in records if r["actualDir"] == "down") / n
        print(f"  종목: {n}, base up={baseUp:.1%}, down={baseDown:.1%}")

        # --- 개별 시그널 vs 매출 ---
        signalCols = ["contingentDebt", "auditStruct", "affiliateChange", "bizPivot",
                      "orderChangeCount", "investChangeCount"]
        signalNames = {
            "contingentDebt": "우발부채↑",
            "auditStruct": "감사구조변경",
            "affiliateChange": "계열변화",
            "bizPivot": "사업대전환",
            "orderChangeCount": "수주/생산변화",
            "investChangeCount": "설비/투자변화",
        }

        print(f"\n  --- 개별 시그널 활성 vs 비활성 ---")
        print(f"  {'시그널':<16s} {'활성n':>6s} {'up%':>6s} {'down%':>6s} {'평균':>8s} | {'비활성n':>6s} {'up%':>6s} {'down%':>6s} {'평균':>8s} | {'p값':>7s}")

        for col in signalCols:
            threshold = 3 if col == "auditStruct" else 1 if col in ("orderChangeCount", "investChangeCount") else 0
            active = [r for r in records if r[col] > threshold]
            inactive = [r for r in records if r[col] <= threshold]

            if not active or not inactive:
                continue

            an, inn = len(active), len(inactive)
            aUp = sum(1 for r in active if r["actualDir"] == "up") / an
            aDown = sum(1 for r in active if r["actualDir"] == "down") / an
            aAvg = sum(r["actualGrowth"] for r in active) / an
            iUp = sum(1 for r in inactive if r["actualDir"] == "up") / inn
            iDown = sum(1 for r in inactive if r["actualDir"] == "down") / inn
            iAvg = sum(r["actualGrowth"] for r in inactive) / inn

            # 활성 그룹의 하락율이 base rate보다 높은지
            aDownCount = sum(1 for r in active if r["actualDir"] == "down")
            p = _binomTest(aDownCount, an, baseDown)

            sig = "✅" if p < 0.05 else ""
            print(f"  {signalNames[col]:<14s} {an:>6d} {aUp:>5.0%} {aDown:>5.0%} {aAvg:>+7.1f}% | {inn:>6d} {iUp:>5.0%} {iDown:>5.0%} {iAvg:>+7.1f}% | {p:>6.3f} {sig}")

        # --- activeSignals 등급별 ---
        print(f"\n  --- 종합 등급별 (activeSignals) ---")
        for grade, lo, hi in [("안정(0)", 0, 0), ("주의(1-2)", 1, 2), ("고위험(3+)", 3, 4)]:
            subset = [r for r in records if lo <= r["activeSignals"] <= hi]
            if not subset:
                continue
            sn = len(subset)
            upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn
            downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn
            avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
            print(f"  {grade:12s}: n={sn:5d}  up={upRate:5.1%}  down={downRate:5.1%}  평균={avgGrowth:+.1f}%")

        # --- 방향 전환 감지력 ---
        print(f"\n  --- 시그널 활성 + 이전 상승 → 하락 전환? ---")
        prevUp = [r for r in records if r["prevDir"] == "up"]
        if prevUp:
            for col in signalCols:
                threshold = 3 if col == "auditStruct" else 1 if col in ("orderChangeCount", "investChangeCount") else 0
                active = [r for r in prevUp if r[col] > threshold]
                inactive = [r for r in prevUp if r[col] <= threshold]
                if not active or len(active) < 10:
                    continue
                an = len(active)
                aDownRate = sum(1 for r in active if r["actualDir"] == "down") / an
                iDownRate = sum(1 for r in inactive if r["actualDir"] == "down") / len(inactive) if inactive else 0
                diff = aDownRate - iDownRate
                if abs(diff) > 0.03:  # 3%p 이상 차이만 표시
                    print(f"    {signalNames[col]:<14s}: 활성→하락 {aDownRate:.1%} (n={an}) vs 비활성→하락 {iDownRate:.1%}  차이={diff:+.1%}")

    # 저장
    summary = {"date": datetime.now().strftime("%Y-%m-%d"), "test": "disclosureRisk 4+2 시그널"}
    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")
    gc.collect()


if __name__ == "__main__":
    main()
