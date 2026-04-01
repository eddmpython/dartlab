"""
실험 ID: 108-003
실험명: scan 횡단 통합 — 상위 100종목 기술적 분석 일괄 + 재무 교차

목적:
- 상위 100종목에 대해 기술적 판단을 일괄 계산하고
- profitability/quality와 교차하여 "재무양호 + 기술적 강세" 종목을 탐색
- screen "technical" 프리셋의 실현 가능성 검증

가설:
1. 100종목 일괄 처리 3분 이내 (종목당 1초 + 지표 6ms)
2. 재무양호(profitability 양호+) + 기술적 강세 조합이 10종목 이상 존재
3. 반대 조합(재무위험 + 기술적 강세)도 존재 → 가치 함정 탐지 가능

방법:
1. dartlab.listing()에서 시가총액 상위 100종목 추출
2. 종목별 gather("price") → RSI + SMA 판단
3. profitability + quality 등급 교차
4. 조합별 종목수 집계

결과 (실험 후 작성):
100종목 → 97종목 성공(3실패), 273초(종목당 2.8초, 야후 rate limit 포함)
분포: 강세 30(31%), 중립 47(48%), 약세 20(21%) — 의미 있는 분포

교차 분석:
| 조합 | 종목수 | 의미 |
|------|--------|------|
| 재무양호+강세 | 11 | 진짜 기회 — 펀더멘털+모멘텀 정렬 |
| 재무양호+약세 | 5 | 실적 좋지만 주가 눌림 — 매수 기회? |
| 재무위험+강세 | 12 | 가치 함정 — 주가만 올라가는 위험 |
| 재무위험+약세 | 13 | 펀더멘털+모멘텀 모두 나쁨 — 회피 |

결론:
- 가설1 부분 채택: 97종목 273초 (종목당 2.8초). 네이버+야후 fallback + rate limit이 병목. 순수 계산은 무시할 수준
- 가설2 채택: 재무양호+강세 11종목 존재 → screen "technical" 프리셋 실현 가능
- 가설3 채택: 재무위험+강세 12종목 = 가치 함정 탐지 가능
- **핵심 병목**: 주가 수집 속도. 100종목에 4.5분은 사용성 한계. 캐시 필요.
- **흡수 결론**: quant 엔진 L1 독립 배치 유효. scan 횡단은 "사전 캐시된 주가" 또는 "소규모 종목 집합" 대상으로 제한하면 실용적.

실험일: 2026-04-01
"""
from __future__ import annotations

import gc
import importlib.util
import json
import sys
import time
import types
from pathlib import Path

import numpy as np
import polars as pl

# tradix 로드
_TRADIX = Path("c:/Users/MSI/OneDrive/Desktop/sideProject/tradix/vectorized")


def _load(name, fp):
    spec = importlib.util.spec_from_file_location(name, fp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_ind = _load("indicators", _TRADIX / "indicators.py")


def _quickVerdict(close: np.ndarray) -> dict:
    """OHLCV close → 빠른 기술적 판단."""
    rsi = _ind.vrsi(close, 14)
    sma20 = _ind.vsma(close, 20)
    sma60 = _ind.vsma(close, 60)

    last_rsi = float(rsi[-1]) if not np.isnan(rsi[-1]) else 50
    above20 = bool(close[-1] > sma20[-1]) if not np.isnan(sma20[-1]) else None
    above60 = bool(close[-1] > sma60[-1]) if not np.isnan(sma60[-1]) else None

    score = 0
    if last_rsi < 30:
        score += 2
    elif last_rsi < 40:
        score += 1
    elif last_rsi > 70:
        score -= 2
    elif last_rsi > 60:
        score -= 1
    if above20:
        score += 1
    elif above20 is not None:
        score -= 1
    if above60:
        score += 1
    elif above60 is not None:
        score -= 1

    if score >= 2:
        verdict = "강세"
    elif score <= -2:
        verdict = "약세"
    else:
        verdict = "중립"

    return {"rsi": round(last_rsi, 1), "above20": above20, "above60": above60, "score": score, "verdict": verdict}


def main():
    print("=== 108-003: scan 횡단 통합 — 100종목 ===\n")

    # 1. profitability에서 상위 100종목 (데이터 확보 확실한 종목)
    from dartlab.scan import Scan

    s = Scan()
    prof = s("profitability")
    codes = prof["종목코드"].head(100).to_list()
    print(f"profitability 상위 {len(codes)}종목\n")

    # 2. 일괄 주가 수집 + 판단
    from dartlab.gather.entry import GatherEntry

    g = GatherEntry()
    results: dict[str, dict] = {}
    t0 = time.time()
    fail_count = 0

    for i, code in enumerate(codes):
        try:
            df = g("price", code)
            if df is None or df.is_empty() or df.height < 60:
                fail_count += 1
                continue
            close = df["close"].to_numpy().astype(np.float64)
            r = _quickVerdict(close)
            results[code] = r
        except Exception:
            fail_count += 1
            continue

        if (i + 1) % 20 == 0:
            elapsed = time.time() - t0
            print(f"  {i + 1}/{len(codes)} 처리... {elapsed:.0f}s")

    total_time = time.time() - t0
    print(f"\n수집 완료: {len(results)}종목 성공, {fail_count}종목 실패, {total_time:.0f}초")

    # 분포
    verdicts = [r["verdict"] for r in results.values()]
    print(f"분포: 강세 {verdicts.count('강세')}, 중립 {verdicts.count('중립')}, 약세 {verdicts.count('약세')}")

    del g
    gc.collect()

    # 3. profitability 교차 (이미 위에서 로드됨)
    print("\n--- profitability 교차 ---")

    cross = {"재무양호+강세": [], "재무양호+약세": [], "재무위험+강세": [], "재무위험+약세": []}

    for code, r in results.items():
        row = prof.filter(pl.col("종목코드") == code)
        grade = row["등급"][0] if not row.is_empty() else None
        if grade is None:
            continue

        is_good = grade in ("양호", "우수")
        is_bad = grade in ("적자", "저수익")
        is_bull = r["verdict"] == "강세"
        is_bear = r["verdict"] == "약세"

        if is_good and is_bull:
            cross["재무양호+강세"].append(code)
        elif is_good and is_bear:
            cross["재무양호+약세"].append(code)
        elif is_bad and is_bull:
            cross["재무위험+강세"].append(code)
        elif is_bad and is_bear:
            cross["재무위험+약세"].append(code)

    for label, codes_list in cross.items():
        print(f"  {label}: {len(codes_list)}종목 {codes_list[:5]}")

    # 저장
    out = {
        "totalStocks": len(results),
        "failCount": fail_count,
        "totalTimeSec": round(total_time, 1),
        "distribution": {
            "강세": verdicts.count("강세"),
            "중립": verdicts.count("중립"),
            "약세": verdicts.count("약세"),
        },
        "crossAnalysis": {k: {"count": len(v), "samples": v[:10]} for k, v in cross.items()},
    }
    outPath = Path("experiments/108_quantEngine/003_result.json")
    outPath.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[SAVED] {outPath}")


if __name__ == "__main__":
    main()
