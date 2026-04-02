"""확장 기술적 분석 — 신호, 베타, 괴리, 리스크, 플래그.

quant 독립 엔진의 확장 모듈. OHLCV + 재무 등급 교차검증.
review 6막 서사에서 시장분석 섹션이 이 함수들을 소비한다.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl

# ── OHLCV 캐싱 헬퍼 ──


def _fetchOHLCV(company: Any) -> pl.DataFrame | None:
    """gather("price")로 OHLCV 수집 — Company._cache에 저장.

    모든 함수가 이 캐시를 공유하므로 네트워크 호출은 1회만 발생.
    """
    cache = getattr(company, "_cache", None)
    _KEY = "_quant_ohlcv"
    if cache is not None and _KEY in cache:
        return cache[_KEY]

    stockCode = getattr(company, "stockCode", None)
    if not stockCode:
        return None

    result = None
    try:
        from dartlab.gather.http import run_async
        from dartlab.gather.price import fetch as fetchPrice

        snapshot = run_async(fetchPrice(stockCode, market=_detectMarket(company)))
        if snapshot is not None and hasattr(snapshot, "ohlcv"):
            result = snapshot.ohlcv
        elif isinstance(snapshot, pl.DataFrame) and "close" in snapshot.columns:
            result = snapshot
    except (ImportError, AttributeError, ValueError, TypeError, RuntimeError):
        pass

    # fallback: GatherEntry 경유
    if result is None:
        try:
            from dartlab.gather.entry import GatherEntry

            raw = GatherEntry()("price", stockCode)
            if isinstance(raw, pl.DataFrame) and "close" in raw.columns:
                result = raw
        except (ImportError, ValueError, TypeError, RuntimeError):
            pass

    if cache is not None:
        cache[_KEY] = result
    return result


def _fetchBenchmarkForCompany(company: Any) -> pl.DataFrame | None:
    """시장 벤치마크 OHLCV — currency 기반 분기."""
    cache = getattr(company, "_cache", None)
    _KEY = "_quant_benchmark"
    if cache is not None and _KEY in cache:
        return cache[_KEY]

    benchmark = "S&P500" if _isUSD(company) else "KOSPI"
    result = None
    try:
        from dartlab.quant.analyzer import _fetchBenchmark as _qfb

        result = _qfb(benchmark)
    except (ImportError, ValueError, TypeError, RuntimeError):
        pass

    if cache is not None:
        cache[_KEY] = result
    return result


def _detectMarket(company: Any) -> str:
    """company.currency로 시장 감지."""
    return "US" if _isUSD(company) else "KR"


def _isUSD(company: Any) -> bool:
    return getattr(company, "currency", "KRW") == "USD"


# ── 독립 함수 (Company 또는 raw OHLCV 모두 지원) ──


def calcTechnicalVerdict(company) -> dict | None:
    """기술적 종합 판단 — 강세/중립/약세 + 주요 지표.

    Args:
        company: Company 객체.

    Returns:
        dict — verdict, score, rsi, adx, aboveSma20, aboveSma60, bbPosition, signals.
    """
    ohlcv = _fetchOHLCV(company)
    if ohlcv is None or ohlcv.is_empty() or len(ohlcv) < 30:
        return None

    from dartlab.quant.analyzer import technicalVerdict

    verdict = technicalVerdict(ohlcv)
    if not verdict:
        return None

    return verdict


def calcTechnicalSignals(company) -> dict | None:
    """최근 20일 매매 신호 요약.

    Args:
        company: Company 객체 (gather("price")로 OHLCV 자동 수집).

    Returns:
        dict — signals, signalSummary, recentEvents.
    """
    ohlcv = _fetchOHLCV(company)
    if ohlcv is None or ohlcv.is_empty() or len(ohlcv) < 60:
        return None

    close = ohlcv["close"].to_numpy().astype(np.float64)
    high = ohlcv["high"].to_numpy().astype(np.float64)
    low = ohlcv["low"].to_numpy().astype(np.float64)

    from dartlab.quant import indicators as ind
    from dartlab.quant import signals as sig

    rsi = ind.vrsi(close, 14)
    recent = min(20, len(close))

    # 신호 생성
    golden = sig.vgoldenCross(close, fast=20, slow=60)
    rsi_sig = sig.vrsiSignal(rsi)
    macd_sig = sig.vmacdSignal(close)
    bb_sig = sig.vbollingerSignal(close)

    # 최근 20일 이벤트 수집
    dates = ohlcv["date"].to_list()
    recentEvents = []
    signalDefs = [
        ("goldenCross", golden),
        ("rsiSignal", rsi_sig),
        ("macdSignal", macd_sig),
        ("bollingerSignal", bb_sig),
    ]

    for name, arr in signalDefs:
        for i in range(max(0, len(arr) - recent), len(arr)):
            val = int(arr[i])
            if val != 0:
                recentEvents.append(
                    {
                        "date": str(dates[i]) if i < len(dates) else "",
                        "type": name,
                        "direction": "매수" if val > 0 else "매도",
                    }
                )

    bullish = sum(1 for e in recentEvents if e["direction"] == "매수")
    bearish = sum(1 for e in recentEvents if e["direction"] == "매도")

    return {
        "signals": {
            "goldenCross": int(golden[-recent:].sum()),
            "rsiSignal": int(rsi_sig[-recent:].sum()),
            "macdSignal": int(macd_sig[-recent:].sum()),
            "bollingerSignal": int(bb_sig[-recent:].sum()),
        },
        "signalSummary": {"bullish": bullish, "bearish": bearish},
        "recentEvents": recentEvents[-10:],  # 최근 10개까지
    }


def calcMarketBeta(company) -> dict | None:
    """시장 베타 + CAPM 기대수익률 + 해석.

    Args:
        company: Company 객체.

    Returns:
        dict — value, r2, capmExpected, relativeStrength, interpretation.
    """
    ohlcv = _fetchOHLCV(company)
    if ohlcv is None or ohlcv.is_empty() or len(ohlcv) < 60:
        return None

    benchmark = _fetchBenchmarkForCompany(company)
    if benchmark is None or benchmark.is_empty():
        return None

    from dartlab.quant.analyzer import _calcBeta, _relativeStrength

    beta_data = _calcBeta(ohlcv, benchmark)
    if beta_data is None:
        return None

    rs = _relativeStrength(ohlcv, benchmark)

    # 해석 텍스트
    bv = beta_data["value"]
    if bv > 1.5:
        interp = f"시장 대비 {(bv - 1) * 100:.0f}% 높은 변동성 — 고위험"
    elif bv > 1.1:
        interp = f"시장보다 약간 높은 변동성 (β={bv:.2f})"
    elif bv > 0.9:
        interp = f"시장과 유사한 변동성 (β={bv:.2f})"
    elif bv > 0.5:
        interp = f"시장보다 낮은 변동성 — 방어적 (β={bv:.2f})"
    else:
        interp = f"시장과 독립적 움직임 (β={bv:.2f})"

    return {
        **beta_data,
        "relativeStrength": rs,
        "interpretation": interp,
    }


def calcFundamentalDivergence(company, *, basePeriod: str | None = None) -> dict | None:
    """재무-시장 괴리 진단 — 교차검증의 핵심.

    재무 스코어카드 등급과 기술적 판단을 비교하여
    괴리(divergence) 여부와 진단 메시지를 반환한다.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간 (기본 최신).

    Returns:
        dict — financialGrade, technicalVerdict, divergence, diagnosis, matrix.
    """
    from dartlab.quant.analyzer import technicalVerdict

    # 재무 등급 가져오기
    financialGrade = None
    try:
        from dartlab.analysis.financial.scorecard import calcScorecard

        sc = calcScorecard(company, basePeriod=basePeriod)
        if sc:
            financialGrade = sc.get("overallGrade") or sc.get("grade")
    except (ImportError, KeyError, ValueError, TypeError, AttributeError):
        pass

    # 기술적 판단
    ohlcv = _fetchOHLCV(company)
    tv = None
    if ohlcv is not None and not ohlcv.is_empty() and len(ohlcv) >= 30:
        tv = technicalVerdict(ohlcv)

    if financialGrade is None and tv is None:
        return None

    techVerdict = tv.get("verdict") if tv else None
    techScore = tv.get("score", 0) if tv else 0

    # 재무 등급 → 3단계 분류
    _GOOD = {"A+", "A", "A-", "B+", "B"}
    _NEUTRAL = {"B-", "C+", "C"}
    finCategory = "unknown"
    if financialGrade:
        if financialGrade in _GOOD:
            finCategory = "good"
        elif financialGrade in _NEUTRAL:
            finCategory = "neutral"
        else:
            finCategory = "poor"

    # 기술적 → 3단계
    techCategory = "neutral"
    if techVerdict == "강세":
        techCategory = "bullish"
    elif techVerdict == "약세":
        techCategory = "bearish"

    # 2x3 매트릭스 진단
    _MATRIX = {
        ("good", "bullish"): ("순풍", "재무와 시장 모두 긍정적 — 기업 펀더멘털이 시장에서 인정받는 상태"),
        ("good", "neutral"): ("관심", "재무는 우량하나 시장이 아직 반영하지 않음 — 모멘텀 전환 주시"),
        ("good", "bearish"): ("괴리", "재무는 양호하나 시장은 약세 — 저평가 기회이거나 시장이 선행 반영한 리스크"),
        ("neutral", "bullish"): ("기대", "시장이 실적 개선을 선반영 — 실적 확인 필요"),
        ("neutral", "neutral"): ("균형", "재무와 시장 모두 중립적 — 방향성 모색 중"),
        ("neutral", "bearish"): ("경고", "시장이 먼저 하락 반응 — 실적 악화 가능성 주시"),
        ("poor", "bullish"): ("괴리", "기술적 반등이지만 재무 리스크 주의 — 지속 가능한 반등인지 확인 필요"),
        ("poor", "neutral"): ("관심", "실적 바닥을 탐색하는 구간 — 턴어라운드 신호 주시"),
        ("poor", "bearish"): ("위험", "재무와 시장 동반 악화 — 구조적 리스크에 노출"),
    }

    key = (finCategory, techCategory)
    divergence, diagnosis = _MATRIX.get(key, ("미정", "데이터 부족으로 교차검증 불가"))

    return {
        "financialGrade": financialGrade,
        "technicalVerdict": techVerdict,
        "technicalScore": techScore,
        "divergence": divergence,
        "diagnosis": diagnosis,
        "matrix": f"{finCategory}_{techCategory}",
    }


def calcMarketRisk(company) -> dict | None:
    """시장 리스크 — ATR 변동성 등급 + 베타 + 상대강도.

    Args:
        company: Company 객체.

    Returns:
        dict — beta, atr, atrPercent, relativeStrength, volatilityGrade, price.
    """
    ohlcv = _fetchOHLCV(company)
    if ohlcv is None or ohlcv.is_empty() or len(ohlcv) < 30:
        return None

    close = ohlcv["close"].to_numpy().astype(np.float64)
    high = ohlcv["high"].to_numpy().astype(np.float64)
    low = ohlcv["low"].to_numpy().astype(np.float64)

    from dartlab.quant import indicators as ind

    # ATR (변동성)
    atr = ind.vatr(high, low, close, 14)
    lastAtr = float(atr[-1]) if not np.isnan(atr[-1]) else None
    lastClose = float(close[-1])
    atrPct = round(lastAtr / lastClose * 100, 1) if lastAtr and lastClose > 0 else None

    # 변동성 등급
    if atrPct is not None:
        if atrPct >= 5.0:
            volGrade = "매우 높음"
        elif atrPct >= 3.0:
            volGrade = "높음"
        elif atrPct >= 1.5:
            volGrade = "보통"
        else:
            volGrade = "낮음"
    else:
        volGrade = None

    # 베타 + 상대강도
    betaData = calcMarketBeta(company)
    betaValue = betaData.get("value") if betaData else None
    rs = betaData.get("relativeStrength") if betaData else None

    return {
        "beta": betaValue,
        "atr": lastAtr,
        "atrPercent": atrPct,
        "relativeStrength": rs,
        "volatilityGrade": volGrade,
        "price": lastClose,
    }


def calcMarketAnalysisFlags(company) -> list[str]:
    """시장분석 플래그 — 기술적 신호 기반 경고/기회.

    Args:
        company: Company 객체.

    Returns:
        list[str] — 경고/기회 플래그 문자열 목록.
    """
    from dartlab.quant.analyzer import technicalVerdict

    flags: list[str] = []

    ohlcv = _fetchOHLCV(company)
    if ohlcv is None or ohlcv.is_empty() or len(ohlcv) < 30:
        return flags

    tv = technicalVerdict(ohlcv)
    if not tv:
        return flags

    rsi = tv.get("rsi", 50)
    adx = tv.get("adx")
    bbPos = tv.get("bbPosition")
    score = tv.get("score", 0)

    # RSI 과매수/과매도
    if rsi >= 70:
        flags.append(f"⚠ RSI {rsi:.0f} — 과매수 구간 (70 이상)")
    elif rsi <= 30:
        flags.append(f"▲ RSI {rsi:.0f} — 과매도 구간 (30 이하), 반등 가능성")

    # ADX 추세 강도
    if adx is not None and adx >= 40:
        flags.append(f"강한 추세 진행 중 (ADX {adx:.0f})")

    # BB 위치
    if bbPos is not None:
        if bbPos >= 95:
            flags.append("⚠ 볼린저밴드 상단 돌파 — 과열 주의")
        elif bbPos <= 5:
            flags.append("볼린저밴드 하단 근접 — 반등 주시")

    # SMA 정배열/역배열
    above20 = tv.get("aboveSma20")
    above60 = tv.get("aboveSma60")
    if above20 and above60:
        flags.append("이동평균 정배열 (20일/60일 위) — 상승 추세 안정적")
    elif above20 is False and above60 is False:
        flags.append("⚠ 이동평균 역배열 (20일/60일 아래) — 하락 추세")

    # 종합 점수
    if score >= 3:
        flags.append("기술적 종합 강세 (score +3 이상)")
    elif score <= -3:
        flags.append("⚠ 기술적 종합 약세 (score -3 이하)")

    # 신호
    signals = tv.get("signals", {})
    gc = signals.get("goldenCross", 0)
    if gc > 0:
        flags.append("최근 골든크로스 발생 — 중기 상승 신호")
    elif gc < 0:
        flags.append("⚠ 최근 데드크로스 발생 — 중기 하락 신호")

    # 시장 리스크
    mr = calcMarketRisk(company)
    if mr:
        beta = mr.get("beta")
        if beta is not None and beta > 1.5:
            flags.append(f"⚠ 높은 베타 ({beta:.2f}) — 시장 급락 시 더 큰 손실 가능")
        atrPct = mr.get("atrPercent")
        if atrPct is not None and atrPct >= 5.0:
            flags.append(f"⚠ 일일 변동성 {atrPct:.1f}% — 고변동 종목")

    return flags
