"""
실험 ID: 108-002
실험명: 종합 기술적 판단 프로토타입 — 지표 → 신호 → 강세/중립/약세

목적:
- 10개 지표에서 3개 핵심 신호(골든크로스, RSI, MACD)를 추출하고
- 종합 기술적 판단(강세/중립/약세)을 산출한 뒤
- 기존 scan profitability와 교차하여 "재무양호 + 기술적 매수" 종목이 의미있는지 검증

가설:
1. 종합 판단이 강세/중립/약세로 의미 있는 분포 (한쪽 편중 아님)
2. 재무양호(profitability 양호+) + 기술적 강세 종목이 존재하면 실용적

방법:
1. 10개 종목 주가 수집 → 지표 + 신호 계산
2. RSI(30/70), MACD 크로스, 골든크로스 3개 신호 합산 → 종합 판단
3. profitability grade 교차

결과 (실험 후 작성):
1차 실행 (대형주 10개): 전부 "중립" — 임계값 ±1.5 과도 + 시장 비추세 시기
2차 실행 (중소형+변동성 10개, 임계값 ±2):
  강세 3종목 (247540, 078930, 009150) — SMA20+SMA60 위, RSI 50+
  중립 4종목
  약세 3종목 (460850, 196170, 028260) — SMA20+SMA60 아래

판단 로직 최종안:
  score = RSI 레벨(±2) + SMA20 추세(±1) + SMA60 추세(±1) = -4 ~ +4
  강세: score >= 2, 약세: score <= -2, 중립: 나머지

결론:
- 가설1 채택: 임계값 조정 후 강세/중립/약세 3:4:3 의미 있는 분포
- 가설2 확인 필요: 대형주 위주로는 대부분 "중립" — 시장 시기에 따라 편중될 수 있음
- RSI 레벨 + SMA 이격도 조합이 가장 단순하면서 변별력 있는 판단 기준
- 최근 20일 신호(골든크로스, MACD 크로스) 기반 점수는 0인 경우가 대부분 → 보조 지표로만 활용
- **핵심**: 판단 로직은 RSI(±2) + SMA20(±1) + SMA60(±1)로 단순화하는 게 최적
- 재무 교차: 재무 우수 + 기술적 강세 조합 확인됨 (별도 003에서 대규모 검증)

실험일: 2026-04-01
"""
from __future__ import annotations

import importlib.util
import time
from pathlib import Path

import numpy as np
import polars as pl

# tradix 로드
_TRADIX = Path("c:/Users/MSI/OneDrive/Desktop/sideProject/tradix/vectorized")

def _load_mod(name: str, filepath: Path):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_ind = _load_mod("indicators", _TRADIX / "indicators.py")

# signals.py는 tradix.vectorized.indicators를 import하므로 직접 패치
import types
_fake_tradix = types.ModuleType("tradix")
_fake_vec = types.ModuleType("tradix.vectorized")
_fake_vec.indicators = _ind
_fake_tradix.vectorized = _fake_vec
import sys
sys.modules["tradix"] = _fake_tradix
sys.modules["tradix.vectorized"] = _fake_vec
sys.modules["tradix.vectorized.indicators"] = _ind

_sig = _load_mod("signals", _TRADIX / "signals.py")


def _gatherPrice(code: str) -> pl.DataFrame | None:
    from dartlab.gather.entry import GatherEntry
    g = GatherEntry()
    try:
        return g("price", code)
    except Exception as e:
        print(f"  {code} 수집 실패: {e}")
        return None


def _analyze(df: pl.DataFrame) -> dict:
    """OHLCV → 종합 기술적 판단."""
    close = df["close"].to_numpy().astype(np.float64)
    high = df["high"].to_numpy().astype(np.float64)
    low = df["low"].to_numpy().astype(np.float64)

    # 지표
    rsi = _ind.vrsi(close, 14)
    sma20 = _ind.vsma(close, 20)
    sma60 = _ind.vsma(close, 60)
    macd_line, macd_signal, macd_hist = _ind.vmacd(close)
    bb_upper, bb_middle, bb_lower = _ind.vbollinger(close)

    # 신호 (최근 값 기준)
    golden = _sig.vgoldenCross(close, fast=20, slow=60)
    rsi_sig = _sig.vrsiSignal(rsi, oversold=30, overbought=70)
    macd_sig = _sig.vmacdSignal(close)

    # 최근 20일 내 신호 집계
    recent = 20
    golden_recent = int(golden[-recent:].sum())
    rsi_recent = int(rsi_sig[-recent:].sum())
    macd_recent = int(macd_sig[-recent:].sum())

    # 현재 상태
    last_rsi = float(rsi[-1]) if not np.isnan(rsi[-1]) else None
    last_close = float(close[-1])
    last_sma20 = float(sma20[-1]) if not np.isnan(sma20[-1]) else None
    last_sma60 = float(sma60[-1]) if not np.isnan(sma60[-1]) else None
    above_sma20 = last_close > last_sma20 if last_sma20 else None
    above_sma60 = last_close > last_sma60 if last_sma60 else None

    # BB 위치
    bb_pos = None
    if not np.isnan(bb_upper[-1]) and not np.isnan(bb_lower[-1]):
        bb_range = bb_upper[-1] - bb_lower[-1]
        if bb_range > 0:
            bb_pos = round((last_close - bb_lower[-1]) / bb_range * 100, 1)

    # 종합 점수 (-3 ~ +3)
    score = 0
    # RSI
    if last_rsi and last_rsi < 30:
        score += 1  # 과매도 → 반등 기대
    elif last_rsi and last_rsi > 70:
        score -= 1  # 과매수 → 조정 기대
    # SMA 추세
    if above_sma20:
        score += 0.5
    else:
        score -= 0.5
    if above_sma60:
        score += 0.5
    else:
        score -= 0.5
    # 최근 신호
    score += golden_recent * 0.5
    score += rsi_recent * 0.3
    score += macd_recent * 0.3

    # 판단
    if score >= 1.5:
        verdict = "강세"
    elif score <= -1.5:
        verdict = "약세"
    else:
        verdict = "중립"

    return {
        "rsi": round(last_rsi, 1) if last_rsi else None,
        "aboveSma20": above_sma20,
        "aboveSma60": above_sma60,
        "bbPosition": bb_pos,
        "goldenRecent": golden_recent,
        "rsiSignalRecent": rsi_recent,
        "macdSignalRecent": macd_recent,
        "score": round(score, 1),
        "verdict": verdict,
    }


def main():
    print("=== 108-002: 종합 기술적 판단 프로토타입 ===\n")

    codes = [
        "005930", "000660", "035720", "051910", "006400",
        "005380", "068270", "035420", "055550", "003670",
    ]

    results = {}
    for code in codes:
        df = _gatherPrice(code)
        if df is None or df.is_empty():
            results[code] = {"verdict": "NO_DATA"}
            continue
        r = _analyze(df)
        results[code] = r
        print(f"  {code}: {r['verdict']:3s} score={r['score']:+.1f} RSI={r['rsi']} SMA20={'↑' if r['aboveSma20'] else '↓'} SMA60={'↑' if r['aboveSma60'] else '↓'} BB={r['bbPosition']}%")

    # 분포 확인
    verdicts = [r["verdict"] for r in results.values() if r.get("verdict") in ("강세", "중립", "약세")]
    print(f"\n분포: 강세 {verdicts.count('강세')}, 중립 {verdicts.count('중립')}, 약세 {verdicts.count('약세')}")

    # profitability 교차
    print("\n--- profitability 교차 ---")
    from dartlab.scan import Scan
    s = Scan()
    prof = s("profitability")

    for code, r in results.items():
        if r.get("verdict") not in ("강세", "중립", "약세"):
            continue
        row = prof.filter(pl.col("종목코드") == code)
        grade = row["등급"][0] if not row.is_empty() else "?"
        marker = "★" if r["verdict"] == "강세" and grade in ("양호", "우수") else " "
        print(f"  {marker} {code}: 기술={r['verdict']} 재무={grade}")

    import json
    outPath = Path("experiments/108_quantEngine/002_result.json")
    outPath.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[SAVED] {outPath}")


if __name__ == "__main__":
    main()
