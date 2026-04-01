"""005 — 문서 텍스트 신호 → 매출 변화 예측 검증.

가설: 공시 문서의 텍스트 변화가 다음 해 매출 변화의 선행 지표다.
  - 숫자(재무제표)는 결과를 기록하고, 문서는 원인을 기록한다.
  - 문서가 크게 바뀐 기업 → 다음 해 매출 방향이 바뀔 가능성 높다.
  - 리스크 섹션이 크게 바뀐 기업 → 다음 해 실적 악화 가능성 높다.

검증 신호 (dartlab 기존 인프라):
  1. overallChangeRate — 전체 공시 변화율
  2. riskChangeRate — 리스크 관련 섹션 변화율
  3. businessChangeRate — 사업 내용 변화율
  4. revenueRelatedChange — 매출 관련 섹션 변화율
  5. signalDirection — 종합 신호 방향 (positive/negative/neutral)
  6. keywordTrend — 리스크/기회 키워드 빈도 변화

메모리 안전:
  - Company 1개씩 순차 로드 → 신호 추출 → del + gc.collect()
  - 동시에 2개 이상 Company 존재하지 않음

사용법::

    uv run python -X utf8 experiments/106_predictionValidation/005_docSignals.py
    uv run python -X utf8 experiments/106_predictionValidation/005_docSignals.py --n 30
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

_ROOT = Path(__file__).resolve().parent
_RESULT_FILE = _ROOT / "docsignal_results.json"


def _loadRevenueSeries() -> dict[str, dict[str, float]]:
    """Scan에서 전종목 연간 매출 로드 → {code: {year: value}}."""
    from dartlab.scan import Scan

    scan = Scan()
    scanResult = scan("account", "매출액")
    if scanResult is None:
        return {}
    df = scanResult.df if hasattr(scanResult, "df") else scanResult
    if df is None or df.height == 0:
        return {}

    codeCol = "stockCode" if "stockCode" in df.columns else df.columns[0]
    skipCols = {codeCol, "companyName", "corpName", "종목코드", "회사명", "sector", "업종"}
    qCols = [c for c in df.columns if c not in skipCols and c[:1].isdigit()]

    # 연도별 분기 매핑
    yearSet: set[str] = set()
    for c in qCols:
        yearSet.add(c[:4])
    years = sorted(yearSet)

    yearQCols: dict[str, list[str]] = {}
    for y in years:
        yearQCols[y] = sorted([c for c in qCols if c.startswith(y)])

    result: dict[str, dict[str, float]] = {}
    for row in df.iter_rows(named=True):
        code = str(row.get(codeCol, ""))
        if not code:
            continue
        annuals: dict[str, float] = {}
        for y in years:
            qs = yearQCols[y]
            if len(qs) < 4:
                continue
            qvals = [row.get(q) for q in qs]
            if any(v is None for v in qvals):
                continue
            annuals[y] = sum(float(v) for v in qvals)
        if len(annuals) >= 2:
            result[code] = annuals
    return result


def _extractDocSignals(code: str) -> dict | None:
    """Company 1개 로드 → c.diff() DataFrame에서 직접 신호 추출 → 즉시 해제."""
    try:
        from dartlab import Company

        c = Company(code)

        # 1. diff() DataFrame에서 직접 신호 추출
        diffDf = c.diff()
        if diffDf is None or not hasattr(diffDf, "height") or diffDf.height == 0:
            del c
            gc.collect()
            return None

        # topic별 평균 changeRate 집계
        riskTopics = {"riskFactors", "riskDerivative", "contingentLiability"}
        businessTopics = {"businessOverview", "businessContent", "companyOverview"}
        revenueTopics = {"revenue", "salesOrder", "productService", "segments"}

        overallRates = []
        riskRates = []
        businessRates = []
        revenueRates = []
        topicRates: dict[str, list[float]] = {}

        for row in diffDf.iter_rows(named=True):
            topic = row.get("topic", "")
            cr = row.get("changeRate")
            if cr is None:
                continue
            cr = float(cr) * 100  # 0-1 → 0-100%

            overallRates.append(cr)

            if topic not in topicRates:
                topicRates[topic] = []
            topicRates[topic].append(cr)

            if topic in riskTopics:
                riskRates.append(cr)
            elif topic in businessTopics:
                businessRates.append(cr)
            elif topic in revenueTopics:
                revenueRates.append(cr)

        overallChangeRate = sum(overallRates) / len(overallRates) if overallRates else 0
        riskChangeRate = max(riskRates) if riskRates else 0
        businessChangeRate = max(businessRates) if businessRates else 0
        revenueChangeRate = max(revenueRates) if revenueRates else 0

        # 변화 큰 topic top 5
        topicAvg = {t: sum(vs) / len(vs) for t, vs in topicRates.items() if vs}
        topChanged = sorted(topicAvg.items(), key=lambda x: x[1], reverse=True)[:5]

        # 신호 방향
        if riskChangeRate > 60:
            signalDirection = "negative"
        elif riskChangeRate > 30:
            signalDirection = "cautious"
        elif businessChangeRate > 40 and riskChangeRate < 20:
            signalDirection = "positive"
        elif overallChangeRate < 10:
            signalDirection = "stable"
        else:
            signalDirection = "neutral"

        delta = {
            "overallChangeRate": round(overallChangeRate, 1),
            "riskChangeRate": round(riskChangeRate, 1),
            "businessChangeRate": round(businessChangeRate, 1),
            "revenueRelatedChange": round(revenueChangeRate, 1),
            "signalDirection": signalDirection,
            "topChangedTopics": [{"topic": t, "changeRate": round(r, 1)} for t, r in topChanged],
        }

        result = {
            "stockCode": code,
            "delta": delta,
        }

        del c
        gc.collect()
        return result

    except Exception as e:
        print(f"    [ERR] {code}: {e}")
        gc.collect()
        return None


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100, help="검증할 종목 수")
    args = parser.parse_args()

    print("=" * 60)
    print("106 예측 검증 — 005 문서 텍스트 신호 → 매출 변화")
    print("=" * 60)

    # 1. 매출 데이터 로드 (Scan, 메모리 안전)
    print("\n[1/4] 매출 시계열 로드 (Scan)...")
    revSeries = _loadRevenueSeries()
    print(f"  {len(revSeries)}개 종목")

    # 2024를 예측 대상으로: 2023 문서 신호 → 2024 매출 변화
    # 매출 100억 이상 + 2023, 2024 데이터 모두 존재
    candidates = []
    for code, annuals in revSeries.items():
        if "2023" in annuals and "2024" in annuals:
            if abs(annuals["2023"]) >= 10_000_000_000:
                candidates.append(code)
    candidates.sort()

    nTarget = min(args.n, len(candidates))
    # 균등 샘플링 (앞쪽에 편향되지 않도록)
    step = max(1, len(candidates) // nTarget)
    selected = candidates[::step][:nTarget]

    print(f"  후보 {len(candidates)}개 중 {len(selected)}개 선택")

    # 2. 순차 신호 추출
    print(f"\n[2/4] 문서 신호 추출 (Company 순차 로드)...")
    records = []
    for i, code in enumerate(selected):
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  [{i+1}/{len(selected)}] {code}...")

        signals = _extractDocSignals(code)
        if signals is None:
            if (i + 1) <= 5:
                print(f"    {code}: signals=None (추출 실패)")
            continue
        if signals["delta"] is None:
            if (i + 1) <= 5:
                print(f"    {code}: delta=None (diff 없음)")
            continue

        annuals = revSeries[code]
        rev2023 = annuals["2023"]
        rev2024 = annuals["2024"]
        actualGrowth = _growth(rev2024, rev2023)
        actualDir = _direction(actualGrowth)

        delta = signals["delta"]
        records.append({
            "stockCode": code,
            "actualGrowth": round(actualGrowth, 1),
            "actualDir": actualDir,
            "overallChangeRate": delta.get("overallChangeRate", 0),
            "riskChangeRate": delta.get("riskChangeRate", 0),
            "businessChangeRate": delta.get("businessChangeRate", 0),
            "revenueRelatedChange": delta.get("revenueRelatedChange", 0),
            "signalDirection": delta.get("signalDirection", "neutral"),
            "nTopicChanges": len(delta.get("topChangedTopics", [])),
        })

    print(f"  신호 추출 완료: {len(records)}개")

    if not records:
        print("[ERROR] 결과 없음")
        sys.exit(1)

    # 3. 분석
    print(f"\n[3/4] 분석...")
    n = len(records)

    # --- A. signalDirection vs actualDir ---
    print(f"\n=== A. 신호 방향 vs 실제 매출 방향 ===")
    for sigDir in ["positive", "negative", "neutral"]:
        subset = [r for r in records if r["signalDirection"] == sigDir]
        if not subset:
            continue
        upCount = sum(1 for r in subset if r["actualDir"] == "up")
        downCount = sum(1 for r in subset if r["actualDir"] == "down")
        flatCount = sum(1 for r in subset if r["actualDir"] == "flat")
        sn = len(subset)
        print(f"  신호={sigDir:8s}: n={sn:3d}  실제 up={upCount/sn*100:.0f}%  down={downCount/sn*100:.0f}%  flat={flatCount/sn*100:.0f}%")

    # --- B. 변화율 구간별 매출 방향 ---
    print(f"\n=== B. 전체 변화율 구간별 매출 방향 ===")
    bins = [(0, 10, "낮음(0-10%)"), (10, 30, "중간(10-30%)"), (30, 60, "높음(30-60%)"), (60, 999, "매우높음(60%+)")]
    for lo, hi, label in bins:
        subset = [r for r in records if lo <= r["overallChangeRate"] < hi]
        if not subset:
            continue
        upCount = sum(1 for r in subset if r["actualDir"] == "up")
        downCount = sum(1 for r in subset if r["actualDir"] == "down")
        sn = len(subset)
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:16s}: n={sn:3d}  up={upCount/sn*100:.0f}%  down={downCount/sn*100:.0f}%  평균성장={avgGrowth:+.1f}%")

    # --- C. 리스크 변화율 vs 매출 ---
    print(f"\n=== C. 리스크 변화율 구간별 매출 방향 ===")
    for lo, hi, label in bins:
        subset = [r for r in records if lo <= r["riskChangeRate"] < hi]
        if not subset:
            continue
        upCount = sum(1 for r in subset if r["actualDir"] == "up")
        downCount = sum(1 for r in subset if r["actualDir"] == "down")
        sn = len(subset)
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:16s}: n={sn:3d}  up={upCount/sn*100:.0f}%  down={downCount/sn*100:.0f}%  평균성장={avgGrowth:+.1f}%")

    # --- D. 사업 변화율 vs 매출 ---
    print(f"\n=== D. 사업내용 변화율 구간별 매출 방향 ===")
    for lo, hi, label in bins:
        subset = [r for r in records if lo <= r["businessChangeRate"] < hi]
        if not subset:
            continue
        upCount = sum(1 for r in subset if r["actualDir"] == "up")
        downCount = sum(1 for r in subset if r["actualDir"] == "down")
        sn = len(subset)
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:16s}: n={sn:3d}  up={upCount/sn*100:.0f}%  down={downCount/sn*100:.0f}%  평균성장={avgGrowth:+.1f}%")

    # --- E. 매출관련 섹션 변화 vs 매출 ---
    print(f"\n=== F. 매출관련 섹션 변화율 구간별 ===")
    for lo, hi, label in bins:
        subset = [r for r in records if lo <= r["revenueRelatedChange"] < hi]
        if not subset:
            continue
        upCount = sum(1 for r in subset if r["actualDir"] == "up")
        downCount = sum(1 for r in subset if r["actualDir"] == "down")
        sn = len(subset)
        avgGrowth = sum(r["actualGrowth"] for r in subset) / sn
        print(f"  {label:16s}: n={sn:3d}  up={upCount/sn*100:.0f}%  down={downCount/sn*100:.0f}%  평균성장={avgGrowth:+.1f}%")

    # --- G. 방향 전환 감지력 ---
    # 핵심: "문서가 많이 바뀐 기업"이 실제로 "매출 방향이 전환"된 비율
    print(f"\n=== G. 핵심 질문: 문서 변화 = 매출 방향 전환? ===")
    # 2022→2023 매출 방향과 2023→2024 매출 방향이 다른 기업 = "전환"
    turnRecords = []
    for r in records:
        code = r["stockCode"]
        annuals = revSeries.get(code, {})
        if "2022" not in annuals or "2023" not in annuals:
            continue
        prevGrowth = _growth(annuals["2023"], annuals["2022"])
        prevDir = _direction(prevGrowth)
        turned = prevDir != r["actualDir"]
        turnRecords.append({**r, "prevDir": prevDir, "turned": turned})

    if turnRecords:
        tn = len(turnRecords)
        turnRate = sum(1 for r in turnRecords if r["turned"]) / tn * 100
        print(f"  전체 방향 전환율: {turnRate:.1f}% ({tn}개)")

        # 변화율 상위 vs 하위의 전환율 비교
        sorted_by_change = sorted(turnRecords, key=lambda r: r["overallChangeRate"], reverse=True)
        top25 = sorted_by_change[:max(1, tn // 4)]
        bottom25 = sorted_by_change[-max(1, tn // 4):]

        topTurnRate = sum(1 for r in top25 if r["turned"]) / len(top25) * 100
        bottomTurnRate = sum(1 for r in bottom25 if r["turned"]) / len(bottom25) * 100
        print(f"  변화율 상위25%: 전환율 {topTurnRate:.1f}% (n={len(top25)})")
        print(f"  변화율 하위25%: 전환율 {bottomTurnRate:.1f}% (n={len(bottom25)})")
        print(f"  차이: {topTurnRate - bottomTurnRate:+.1f}%p")

        # 리스크 변화 상위의 하락 전환율
        sorted_by_risk = sorted(turnRecords, key=lambda r: r["riskChangeRate"], reverse=True)
        topRisk = sorted_by_risk[:max(1, tn // 4)]
        topRiskDownTurn = sum(1 for r in topRisk if r["turned"] and r["actualDir"] == "down") / len(topRisk) * 100
        print(f"  리스크변화 상위25%: 하락전환율 {topRiskDownTurn:.1f}% (n={len(topRisk)})")

    # 4. 저장
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total": n,
        "testPeriod": "2023문서→2024매출",
        "records": records,
    }
    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {_RESULT_FILE}")

    gc.collect()


if __name__ == "__main__":
    main()
