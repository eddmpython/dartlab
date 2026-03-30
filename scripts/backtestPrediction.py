"""예측신호 전종목 백테스트 — 방향 정확도 측정.

scan 데이터에서 전종목의 이익 모멘텀 방향을 예측하고,
실제 이익 변화와 비교하여 방향 정확도를 측정한다.

메모리 안전: Company를 생성하지 않고 scan ratio만 사용.
scan ratio는 Polars 메모리를 최소화하며 순차 처리.

사용법::

    uv run python scripts/backtestPrediction.py              # 전종목
    uv run python scripts/backtestPrediction.py --pilot 100  # 100개만
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

_ROOT = Path(__file__).resolve().parent.parent
_AUDIT_DIR = _ROOT / "data" / "dart" / "auditAi"


def _loadRatioSeries(ratioName: str) -> dict[str, list[float]]:
    """scan ratio를 {stockCode: [val_newest, val_older, ...]} 형태로 로드."""
    from dartlab.scan import Scan

    scan = Scan()
    result = {}
    try:
        scanResult = scan("ratio", ratioName)
        if scanResult is None or not hasattr(scanResult, "df"):
            return result
        df = scanResult.df
        codeCol = "stockCode" if "stockCode" in df.columns else df.columns[0]
        periodCols = [c for c in df.columns if c not in (codeCol, "companyName", "종목코드", "회사명")]
        if not periodCols:
            return result
        for row in df.iter_rows(named=True):
            code = str(row.get(codeCol, ""))
            vals = [row.get(c) for c in periodCols]
            cleanVals = [float(v) for v in vals if v is not None]
            if code and len(cleanVals) >= 3:
                result[code] = cleanVals
    except (ValueError, TypeError, AttributeError):
        pass
    return result


def _predictDirection(vals: list[float]) -> str | None:
    """최근 3개 값으로 방향 예측 (vals[0]=최신).

    최근 2년 연속 증가 → "up"
    최근 2년 연속 감소 → "down"
    그 외 → "flat"
    """
    if len(vals) < 3:
        return None
    d1 = vals[0] - vals[1]  # 최신 - 이전
    d2 = vals[1] - vals[2]  # 이전 - 그전
    if d1 > 0 and d2 > 0:
        return "up"
    elif d1 < 0 and d2 < 0:
        return "down"
    else:
        return "flat"


def _actualDirection(vals: list[float]) -> str | None:
    """실제 방향 (최신 vs 이전)."""
    if len(vals) < 2:
        return None
    d = vals[0] - vals[1]
    if d > 0:
        return "up"
    elif d < 0:
        return "down"
    else:
        return "flat"


def main():
    parser = argparse.ArgumentParser(description="예측신호 전종목 백테스트")
    parser.add_argument("--pilot", type=int, default=0, help="파일럿 종목 수 (0=전체)")
    args = parser.parse_args()

    print("[1/4] 영업이익 시계열 로드 중...")
    oiSeries = _loadRatioSeries("operatingIncome")
    print(f"       {len(oiSeries)}개 종목 로드")

    print("[2/4] 매출 시계열 로드 중...")
    revSeries = _loadRatioSeries("revenue")
    print(f"       {len(revSeries)}개 종목 로드")

    # 공통 종목
    commonCodes = sorted(set(oiSeries.keys()) & set(revSeries.keys()))
    if args.pilot > 0:
        commonCodes = commonCodes[:args.pilot]
    print(f"[3/4] {len(commonCodes)}개 종목 백테스트 시작...")

    # 백테스트: 각 종목에서 t-1 기준 예측 → t 실제와 비교
    results = []
    for code in commonCodes:
        oiVals = oiSeries[code]
        revVals = revSeries[code]

        if len(oiVals) < 4 or len(revVals) < 4:
            continue

        # 예측: vals[1:] 기준으로 예측 (t-1 시점)
        oiPredDir = _predictDirection(oiVals[1:])  # t-1 기준 예측
        revPredDir = _predictDirection(revVals[1:])

        # 실제: vals[0] vs vals[1]
        oiActualDir = _actualDirection(oiVals)
        revActualDir = _actualDirection(revVals)

        if oiPredDir and oiActualDir:
            results.append({
                "stockCode": code,
                "metric": "operatingIncome",
                "predicted": oiPredDir,
                "actual": oiActualDir,
                "correct": oiPredDir == oiActualDir,
            })

        if revPredDir and revActualDir:
            results.append({
                "stockCode": code,
                "metric": "revenue",
                "predicted": revPredDir,
                "actual": revActualDir,
                "correct": revPredDir == revActualDir,
            })

    # 정확도 계산
    if not results:
        print("[ERROR] 백테스트 결과 없음")
        sys.exit(1)

    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    accuracy = correct / total * 100

    oiResults = [r for r in results if r["metric"] == "operatingIncome"]
    revResults = [r for r in results if r["metric"] == "revenue"]
    oiAcc = sum(1 for r in oiResults if r["correct"]) / len(oiResults) * 100 if oiResults else 0
    revAcc = sum(1 for r in revResults if r["correct"]) / len(revResults) * 100 if revResults else 0

    # 방향별 breakdown
    upPred = [r for r in results if r["predicted"] == "up"]
    downPred = [r for r in results if r["predicted"] == "down"]
    upAcc = sum(1 for r in upPred if r["correct"]) / len(upPred) * 100 if upPred else 0
    downAcc = sum(1 for r in downPred if r["correct"]) / len(downPred) * 100 if downPred else 0

    print(f"\n[4/4] 결과")
    print(f"  종목 수: {len(commonCodes)}")
    print(f"  관측치: {total}")
    print(f"  전체 방향 정확도: {accuracy:.1f}% ({correct}/{total})")
    print(f"  영업이익 정확도: {oiAcc:.1f}% ({len(oiResults)} obs)")
    print(f"  매출 정확도: {revAcc:.1f}% ({len(revResults)} obs)")
    print(f"  상승 예측 정확도: {upAcc:.1f}% ({len(upPred)} obs)")
    print(f"  하락 예측 정확도: {downAcc:.1f}% ({len(downPred)} obs)")
    print(f"  (50% = 랜덤, 60%+ = 유의미)")

    # 결과 저장
    _AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    outPath = _AUDIT_DIR / f"backtest_prediction_{today}.jsonl"
    with open(outPath, "w", encoding="utf-8") as f:
        # 요약 행
        summary = {
            "type": "summary",
            "date": today,
            "nCompanies": len(commonCodes),
            "nObservations": total,
            "accuracy": round(accuracy, 2),
            "oiAccuracy": round(oiAcc, 2),
            "revAccuracy": round(revAcc, 2),
            "upAccuracy": round(upAcc, 2),
            "downAccuracy": round(downAcc, 2),
        }
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")
        # 개별 결과
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n  저장: {outPath}")

    gc.collect()


if __name__ == "__main__":
    main()
