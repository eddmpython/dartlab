"""007 — preview 텍스트 내 방향성 키워드 → 매출 예측.

006에서 sizeDelta만으로는 안 됐다. preview에 실제 텍스트가 있으므로
회사가 직접 쓴 방향성 키워드를 카운트한다.

사전 없이 가능한 이유: 한국 공시의 사업보고서는 회사가 직접
"매출이 증가하였습니다", "시장이 축소되었습니다" 같은 서술을 한다.
이건 감성 분석이 아니라 사실 진술 추출이다.

키워드 그룹:
  확장: 증가, 성장, 확대, 개선, 호조, 신규, 진출, 착공, 수주, 상승
  축소: 감소, 하락, 축소, 악화, 둔화, 위축, 부진, 철수, 중단, 손실

사용법::

    uv run python -X utf8 experiments/106_predictionValidation/007_textSignals.py
"""

from __future__ import annotations

import gc
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

_ROOT = Path(__file__).resolve().parent
_DATA = Path(__file__).resolve().parent.parent.parent / "data"
_RESULT_FILE = _ROOT / "textsignal_results.json"

# ---------------------------------------------------------------------------
# 방향성 키워드 (한국 공시 사업보고서 빈출 표현)
# ---------------------------------------------------------------------------
EXPAND_KW = ["증가", "성장", "확대", "개선", "호조", "신규", "진출", "착공",
             "수주", "상승", "호전", "신설", "확장", "증대", "늘어"]
SHRINK_KW = ["감소", "하락", "축소", "악화", "둔화", "위축", "부진", "철수",
             "중단", "손실", "적자", "폐쇄", "매각", "저하", "줄어"]


def _countKeywords(text: str | None) -> tuple[int, int]:
    """텍스트에서 확장/축소 키워드 수를 카운트."""
    if not text:
        return 0, 0
    expandCount = sum(text.count(kw) for kw in EXPAND_KW)
    shrinkCount = sum(text.count(kw) for kw in SHRINK_KW)
    return expandCount, shrinkCount


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
    print("106 예측 검증 — 007 텍스트 방향성 키워드")
    print("=" * 60)

    # 1. 데이터 로드
    print("\n[1/4] changes.parquet 로드...")
    changes = pl.read_parquet(str(_DATA / "dart" / "scan" / "changes.parquet"))

    # 2022→2023 wording 변화의 사업 관련 섹션
    docChanges = changes.filter(
        (pl.col("fromPeriod") == "2022") &
        (pl.col("toPeriod") == "2023") &
        (pl.col("changeType") == "wording")
    )
    print(f"  2022→2023 wording: {docChanges.shape[0]:,} 행")

    # 2. 매출 시계열
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
        if "2023" in annuals and "2024" in annuals:
            if abs(annuals["2023"]) >= 10_000_000_000:
                revSeries[code] = annuals
    print(f"  대상: {len(revSeries)} 종목")

    del revDf, scanResult
    gc.collect()

    # 3. 종목별 키워드 집계
    print("\n[3/4] 키워드 집계...")
    codeKw: dict[str, dict] = defaultdict(lambda: {
        "expand": 0, "shrink": 0, "expandBiz": 0, "shrinkBiz": 0,
        "expandRisk": 0, "shrinkRisk": 0, "nChanges": 0,
    })

    BIZ_KW = ["사업", "매출", "수주", "생산", "제품", "서비스", "시장"]
    RISK_KW = ["위험", "리스크", "우발", "소송", "손실", "부채"]

    for row in docChanges.iter_rows(named=True):
        code = row["stockCode"]
        if code not in revSeries:
            continue

        preview = row.get("preview") or ""
        title = row.get("sectionTitle") or ""
        expand, shrink = _countKeywords(preview)

        codeKw[code]["expand"] += expand
        codeKw[code]["shrink"] += shrink
        codeKw[code]["nChanges"] += 1

        isBiz = any(kw in title for kw in BIZ_KW)
        isRisk = any(kw in title for kw in RISK_KW)

        if isBiz:
            codeKw[code]["expandBiz"] += expand
            codeKw[code]["shrinkBiz"] += shrink
        if isRisk:
            codeKw[code]["expandRisk"] += expand
            codeKw[code]["shrinkRisk"] += shrink

    # 결과 조합
    records = []
    for code in codeKw:
        if code not in revSeries:
            continue
        kw = codeKw[code]
        annuals = revSeries[code]

        actualGrowth = _growth(annuals["2024"], annuals["2023"])
        actualDir = _direction(actualGrowth)

        total = kw["expand"] + kw["shrink"]
        expandRatio = kw["expand"] / total if total > 0 else 0.5

        bizTotal = kw["expandBiz"] + kw["shrinkBiz"]
        bizExpandRatio = kw["expandBiz"] / bizTotal if bizTotal > 0 else 0.5

        riskTotal = kw["expandRisk"] + kw["shrinkRisk"]
        riskShrinkRatio = kw["shrinkRisk"] / riskTotal if riskTotal > 0 else 0.5

        # 키워드 기반 예측 방향
        if expandRatio > 0.6:
            kwDir = "up"
        elif expandRatio < 0.4:
            kwDir = "down"
        else:
            kwDir = "flat"

        prevDir = None
        if "2022" in annuals:
            prevDir = _direction(_growth(annuals["2023"], annuals["2022"]))

        records.append({
            "stockCode": code,
            "expand": kw["expand"],
            "shrink": kw["shrink"],
            "expandRatio": round(expandRatio, 3),
            "bizExpandRatio": round(bizExpandRatio, 3),
            "riskShrinkRatio": round(riskShrinkRatio, 3),
            "nChanges": kw["nChanges"],
            "kwDir": kwDir,
            "actualGrowth": round(actualGrowth, 1),
            "actualDir": actualDir,
            "prevDir": prevDir,
        })

    n = len(records)
    print(f"  분석: {n} 종목")

    # 4. 분석
    print(f"\n[4/4] 분석 ({n} 종목)")

    # --- A. 키워드 방향 예측 정확도 ---
    print(f"\n=== A. 키워드 방향 예측 정확도 ===")
    kwCorrect = sum(1 for r in records if r["kwDir"] == r["actualDir"])
    print(f"  정확도: {kwCorrect/n*100:.1f}% ({kwCorrect}/{n})")
    print(f"  (비교: 001 OLS=47%, 모멘텀=13%, 항상up=53%)")

    for d in ["up", "down", "flat"]:
        predicted = [r for r in records if r["kwDir"] == d]
        if predicted:
            correct = sum(1 for r in predicted if r["actualDir"] == d)
            print(f"  {d} 예측: {correct/len(predicted)*100:.1f}% 정확 (n={len(predicted)})")

    # --- B. expandRatio 구간별 ---
    print(f"\n=== B. 확장키워드 비율 구간별 매출 ===")
    rBins = [(0, 0.4, "축소우세(<40%)"), (0.4, 0.5, "균형(40-50%)"),
             (0.5, 0.6, "확장소폭(50-60%)"), (0.6, 1.01, "확장우세(60%+)")]
    for lo, hi, label in rBins:
        subset = [r for r in records if lo <= r["expandRatio"] < hi]
        if not subset:
            continue
        sn = len(subset)
        upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn * 100
        downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn * 100
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:18s}: n={sn:4d}  up={upRate:4.0f}%  down={downRate:4.0f}%  평균={avgGrowth:+.1f}%")

    # --- C. 사업섹션 확장비율 vs 매출 ---
    print(f"\n=== C. 사업섹션 확장키워드 비율 vs 매출 ===")
    for lo, hi, label in rBins:
        subset = [r for r in records if lo <= r["bizExpandRatio"] < hi]
        if not subset:
            continue
        sn = len(subset)
        upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn * 100
        downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn * 100
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:18s}: n={sn:4d}  up={upRate:4.0f}%  down={downRate:4.0f}%  평균={avgGrowth:+.1f}%")

    # --- D. 리스크 축소키워드 비율 vs 매출 ---
    print(f"\n=== D. 리스크섹션 축소키워드 비율 vs 매출 ===")
    for lo, hi, label in [(0, 0.3, "축소적음(<30%)"), (0.3, 0.5, "중간(30-50%)"),
                          (0.5, 0.7, "많음(50-70%)"), (0.7, 1.01, "매우많음(70%+)")]:
        subset = [r for r in records if lo <= r["riskShrinkRatio"] < hi]
        if not subset:
            continue
        sn = len(subset)
        upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn * 100
        downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn * 100
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:18s}: n={sn:4d}  up={upRate:4.0f}%  down={downRate:4.0f}%  평균={avgGrowth:+.1f}%")

    # --- E. 방향 전환 감지 ---
    print(f"\n=== E. 키워드 신호 vs 방향 전환 ===")
    turnRecords = [r for r in records if r["prevDir"] is not None]
    if turnRecords:
        tn = len(turnRecords)
        # 키워드가 이전 방향과 다른 방향을 가리킬 때
        antiRecords = [r for r in turnRecords if r["kwDir"] != r["prevDir"] and r["kwDir"] != "flat"]
        proRecords = [r for r in turnRecords if r["kwDir"] == r["prevDir"]]

        if antiRecords:
            an = len(antiRecords)
            actuallyTurned = sum(1 for r in antiRecords if r["actualDir"] != r["prevDir"])
            print(f"  키워드가 반대 방향 지시: n={an}, 실제 전환율={actuallyTurned/an*100:.1f}%")
        if proRecords:
            pn = len(proRecords)
            actuallyKept = sum(1 for r in proRecords if r["actualDir"] == r["prevDir"])
            print(f"  키워드가 같은 방향 지시: n={pn}, 실제 유지율={actuallyKept/pn*100:.1f}%")

    # --- F. 상위/하위 비교 ---
    print(f"\n=== F. 확장비율 상위25% vs 하위25% ===")
    sortedByExpand = sorted(records, key=lambda r: r["expandRatio"], reverse=True)
    q = max(1, n // 4)
    top25 = sortedByExpand[:q]
    bottom25 = sortedByExpand[-q:]
    for label, subset in [("상위25%(확장우세)", top25), ("하위25%(축소우세)", bottom25)]:
        sn = len(subset)
        upRate = sum(1 for r in subset if r["actualDir"] == "up") / sn * 100
        downRate = sum(1 for r in subset if r["actualDir"] == "down") / sn * 100
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:22s}: n={sn:4d}  up={upRate:4.0f}%  down={downRate:4.0f}%  평균={avgGrowth:+.1f}%")

    # 저장
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total": n,
        "kwAccuracy": round(kwCorrect / n * 100, 1),
        "test": "2022→2023 문서 키워드 → 2024 매출",
    }
    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")

    gc.collect()


if __name__ == "__main__":
    main()
