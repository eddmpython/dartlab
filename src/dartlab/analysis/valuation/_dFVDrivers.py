"""dFV 드라이버 — 재투자연동 성장 · ROIC fade · 드라이버 시나리오 · reverse-DCF (P1a).

사상: 성장은 재투자에서만 나온다. g = reinvestRate × ROIC (Damodaran 성장방정식).
ROIC 는 명시구간 동안 WACC 로 경쟁 수렴(fade) — 초과수익 영구 가정 폐기. naive 매출
CAGR 외삽을 펀더멘털 anchor 로 대체. 시나리오는 ±12% 산술밴드 대신 드라이버(g·WACC)
교란. SSOT 재사용 — calcRoicTimeline(ROIC·NOPAT·투하자본 시계열) · priceImplied(reverse
-DCF 솔버) · multiStageDcf(DCF 본체). 본 모듈은 L2(analysis) 내부, synth/calc 만 호출.
"""

from __future__ import annotations

from typing import Any


def _estimateReinvestRate(history: list[dict]) -> float | None:
    """재투자율 = ΔInvestedCapital / NOPAT 의 중앙값 (Damodaran).

    history 는 최신→과거 순(calcRoicTimeline). reinvestment_t = IC_t - IC_{t-1}
    (당해 순신규 투하자본), rate = reinvestment / NOPAT. clamp [0, 0.9].
    음수(disinvestment)·NOPAT≤0 기간은 제외. 유효 연도 없으면 None.
    """
    rates: list[float] = []
    for i in range(len(history) - 1):
        icNew = history[i].get("investedCapital")
        icOld = history[i + 1].get("investedCapital")
        nopat = history[i].get("nopat")
        if icNew and icOld and nopat and nopat > 0:
            r = (icNew - icOld) / nopat
            rates.append(max(0.0, r))  # 순투자 회수(음수) 연도는 재투자 0 으로 floor(제외 아님)
    if not rates:
        return None
    rates.sort()
    med = rates[len(rates) // 2]
    return max(0.0, min(med, 0.9))


def _growthPathFromRoics(
    validRoic: list[float], reinvestRate: float, waccPct: float, years: int, fadeExponent: float = 1.0
) -> dict | None:
    """through-cycle ROIC anchor → WACC fade → 연도별 펀더멘털 성장 (순수, 테스트용).

    roicAnchor = through-cycle 중앙값(median) — 사이클 peak/trough 평탄화. 최신 peak 대신
    정규화 ROIC 로 성장을 앵커링해 사이클 고점 과대평가 차단(FCF 정규화와 정합).
    예: 하이닉스 latest 31% → median 7.35%(2023 메모리 불황 -10.4% 포함) → 과공격 성장 차단.
    roicAnchor ≤ 0(구조적 적자) 면 None.
    """
    if not validRoic:
        return None
    # 데이터 아티팩트 가드 — ROIC > 100% 는 투하자본 분모 이상(예: 삼양식품 699%) → 제외.
    # 지속 가능 ROIC 상한도 40%로 cap(Damodaran: 영구 초과수익 비현실) — 성장 과대 차단.
    clean = [r for r in validRoic if -50.0 <= r <= 100.0]
    if not clean:
        return None
    s = sorted(clean)
    roicAnchor = min(s[len(s) // 2], 40.0)
    if roicAnchor <= 0:
        return None
    n = max(1, int(years))
    roicPath = [roicAnchor + (waccPct - roicAnchor) * (t / n) ** fadeExponent for t in range(1, n + 1)]
    # 성장 클램프 상한 18% — Damodaran: 8년 지속 >18% 성장은 상위 <5%(fad 외삽 차단).
    # 25%→18 보수화: 고-ROIC 종목 과대평가 억제(삼양식품류), 일반 성장주 무영향.
    growthRates = [max(-5.0, min(reinvestRate * r, 18.0)) for r in roicPath]
    return {"growthRates": growthRates, "roicPath": roicPath, "roicAnchor": round(roicAnchor, 2)}


def buildReinvestmentPath(
    company: Any,
    *,
    waccPct: float | None = None,
    years: int = 8,
    fadeExponent: float = 1.0,
    basePeriod: str | None = None,
) -> dict | None:
    """재투자연동 성장 경로 — g_t = reinvestRate × ROIC_t, ROIC_0 → WACC fade.

    Capabilities:
        calcRoicTimeline 의 ROIC·NOPAT·투하자본 시계열에서 재투자율(ΔIC/NOPAT)을
        추정하고, ROIC 를 명시구간 동안 WACC 로 수렴시킨 뒤 연도별 펀더멘털
        성장률 g_t = reinvestRate × ROIC_t 를 산출. naive 매출 CAGR 대체.

    Args:
        company: Company 객체.
        waccPct: 회사 WACC(%). None 이면 calcRoicTimeline 의 waccEstimate → 9.0.
        years: 명시 성장구간 연수(기본 8).
        fadeExponent: ROIC 수렴 곡률. >1 느린수렴(해자), <1 빠른수렴, 1 선형.
        basePeriod: 재무 기준 기간(예 "2024Q4"). None=최신. 공시 가용일·시장데이터
            vintage를 고정하는 point-in-time 백테스트 계약은 아님.

    Returns:
        dict | None:
            - ``growthRates`` (list[float]): 연도별 성장률(%) — multiStageDcf growthRates.
            - ``roicPath`` (list[float]): 연도별 ROIC(%, WACC 로 fade).
            - ``reinvestRate`` (float): 추정 재투자율 [0,0.9].
            - ``roic0``/``roicAnchor``/``wacc``/``fundamentalGrowth`` (float): 진단용
              (roic0=최신 ROIC, roicAnchor=through-cycle median 정규화 — fundamentalGrowth 의 anchor).
        ROIC/재투자율 추정 실패 시 None (호출부가 기존 phase 폴백).

    Example:
        >>> buildReinvestmentPath(Company("005930"), waccPct=8.7)
        {"growthRates": [...], "reinvestRate": 0.42, "fundamentalGrowth": 6.3, ...}

    Guide:
        성장률 clamp [-5, 18]. ROIC_0 ≤ 0 또는 재투자율 추정 불가 시 None.
        끄지 말고 호출부가 매출 CAGR 폴백(가정 명시). terminal 무료성장은
        성장이 ROIC 에 묶여 자동 차단(초과수익 fade).

    When:
        _calcTwoStageDcf 가 growthRates 를 펀더멘털 anchor 로 채울 때.

    How:
        buildReinvestmentPath(company, waccPct=wacc) → growthYears=[1]*N + growthRates.

    SeeAlso:
        - ``calcRoicTimeline``: ROIC·NOPAT·투하자본 시계열 (입력)
        - ``buildDriverScenarios``: 본 경로 교란 시나리오
        - ``reverseDcfExhibit``: fundamentalGrowth 를 시장내재 성장과 비교

    Requires:
        calcRoicTimeline 가 history(≥2년, investedCapital·nopat·roic) 반환.

    Raises:
        없음 — 내부 catch, 실패 시 None.

    AIContext:
        성장률을 입력으로 받지 말고 본 함수로 도출. fundamentalGrowth 가 매출
        CAGR 보다 낮으면 "재투자가 성장을 지지하지 못함" 신호.
    """
    try:
        from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline
    except ImportError:
        return None
    try:
        rt = calcRoicTimeline(company, basePeriod=basePeriod)
    except (AttributeError, ValueError, TypeError):
        return None
    if not rt or not rt.get("history"):
        return None
    hist = rt["history"]
    # 유효 ROIC 시계열 — 당해 미완 연도(IS 미집계)는 roic None 이라 skip.
    validRoic = [h.get("roic") for h in hist if h.get("roic") is not None]
    if not validRoic:
        return None
    reinvest = _estimateReinvestRate(hist)
    if reinvest is None:
        return None
    wacc = waccPct if waccPct is not None else (hist[0].get("waccEstimate") or 9.0)
    # through-cycle median anchor (사이클 peak 정규화) — _growthPathFromRoics.
    path = _growthPathFromRoics(validRoic, reinvest, wacc, years, fadeExponent)
    if path is None:
        return None
    return {
        "growthRates": path["growthRates"],
        "roicPath": path["roicPath"],
        "reinvestRate": round(reinvest, 4),
        "roic0": round(validRoic[0], 2),  # 최신(진단용)
        "roicAnchor": path["roicAnchor"],  # through-cycle 정규화 앵커
        "wacc": round(wacc, 2),
        "fundamentalGrowth": round(reinvest * path["roicAnchor"], 2),
    }


def buildDriverScenarios(
    *,
    baseFcf: float,
    growthRates: list[float],
    terminalGrowth: float,
    wacc: float,
    netDebt: float,
    shares: float | None,
    waccDelta: float = 1.0,
    growthDelta: float = 0.2,
) -> dict | None:
    """bear/base/bull = 드라이버(WACC·성장) 교란 DCF 재계산 (±12% 산술밴드 폐기).

    bull = WACC −Δ + 성장 ×(1+δ),  bear = WACC +Δ + 성장 ×(1−δ).
    multiStageDcf 를 perturbed 입력으로 재호출 → 진짜 드라이버 시나리오.

    Args:
        baseFcf: 기준 FCF(원). growthRates: 연도별 성장률(%). terminalGrowth: 영구성장률(%).
        wacc: 할인율(%). netDebt: 순차입금(원). shares: 발행주식수.
        waccDelta: WACC 교란폭(%p). growthDelta: 성장 배수 교란폭.

    Returns:
        dict | None: ``{bear, base, bull, drivers}``. drivers = 각 시나리오의
        wacc·growthMult. perShare 산출 불가(shares None) 시 None.

    Example:
        >>> buildDriverScenarios(baseFcf=3e13, growthRates=[8, 7, 6], terminalGrowth=2.5,
        ...                      wacc=8.7, netDebt=-3e13, shares=6e9)
        {"bear": 110000, "base": 125000, "bull": 142000, "drivers": {...}}

    Raises:
        없음 — multiStageDcf import 실패·shares None 시 None.
    """
    try:
        from dartlab.analysis.valuation.dcf import multiStageDcf
    except ImportError:
        return None
    if shares is None or shares <= 0:
        return None
    yearsVec = [1] * len(growthRates)

    def _run(waccP: float, mult: float) -> float | None:
        rates = [g * mult for g in growthRates]
        r = multiStageDcf(
            baseFcf=baseFcf,
            growthYears=yearsVec,
            growthRates=rates,
            terminalGrowthRate=terminalGrowth,
            wacc=waccP,
            netDebt=netDebt,
            shares=shares,
        )
        return r.get("perShare")

    base = _run(wacc, 1.0)
    bull = _run(max(wacc - waccDelta, terminalGrowth + 0.5), 1.0 + growthDelta)
    bear = _run(wacc + waccDelta, 1.0 - growthDelta)
    if base is None:
        return None
    return {
        "bear": round(bear) if bear else None,
        "base": round(base),
        "bull": round(bull) if bull else None,
        "drivers": {
            "bull": {"wacc": round(wacc - waccDelta, 1), "growthMult": round(1 + growthDelta, 2)},
            "base": {"wacc": round(wacc, 1), "growthMult": 1.0},
            "bear": {"wacc": round(wacc + waccDelta, 1), "growthMult": round(1 - growthDelta, 2)},
        },
    }


def reverseDcfExhibit(
    company: Any,
    *,
    waccPct: float,
    fundamentalGrowth: float | None,
    marketCap: float | None,
    netDebt: float | None = None,
) -> dict | None:
    """헤드라인 reverse-DCF — 시장이 내재한 성장률 vs 펀더멘털 지지 성장률.

    priceImplied.reverseImpliedGrowth 를 *회사 WACC* 로 호출(하드코딩 10 폐기)
    하고 fundamentalGrowth(=reinvest×ROIC)와 비교. "시장은 g*% 가격에 반영,
    펀더멘털 지지 g_fund% → 격차 N%p" — 미래 예측 아닌 시장 가정 해독.

    Args:
        company: Company 객체(_series/_finance.series 보유). waccPct: 회사 WACC(%).
        fundamentalGrowth: 펀더멘털 지지 성장률(%, buildReinvestmentPath). marketCap: 시총(원).
        netDebt: 순차입금(원, EV 보정).

    Returns:
        dict | None: ``{impliedGrowth, fundamentalGrowth, gap, signal, assumptions}``.
        marketCap·series 부재 시 None.

    Example:
        >>> reverseDcfExhibit(company, waccPct=8.7, fundamentalGrowth=8.9, marketCap=4.5e14)
        {"impliedGrowth": 6.2, "fundamentalGrowth": 8.9, "gap": 2.7, "signal": "underpriced", ...}

    Raises:
        없음 — series/marketCap 부재·역산 실패 시 None.
    """
    try:
        from dartlab.analysis.valuation.priceImplied import computeGap, reverseImpliedGrowth
    except ImportError:
        return None
    if marketCap is None or marketCap <= 0:
        return None
    # 예전에는 company._series 를 먼저 봤는데 그 이름은 Company 에 없어 늘 건너뛰었다.
    # 실제 공급원은 재무 accessor 하나다.
    series = getattr(getattr(company, "_finance", None), "series", None)
    if not series:
        return None
    try:
        implied = reverseImpliedGrowth(series, marketCap, wacc=waccPct, netDebt=netDebt)
    except (AttributeError, ValueError, TypeError, RuntimeError):
        return None
    if implied is None:
        return None
    out: dict[str, Any] = {
        "impliedGrowth": round(implied.impliedGrowthRate, 2),
        "fundamentalGrowth": round(fundamentalGrowth, 2) if fundamentalGrowth is not None else None,
        "assumptions": {
            "wacc": round(waccPct, 2),
            "assumedMargin": round(implied.assumedMargin, 2),
            "terminalGrowth": implied.assumedTerminalGrowth,
        },
    }
    if fundamentalGrowth is not None:
        computeGap(implied, fundamentalGrowth)
        out["gap"] = implied.gapVsForecast
        # signal 방향: 시장내재 > 펀더멘털 → 시장이 낙관(고평가 위험)
        out["signal"] = (
            "overpriced"
            if implied.impliedGrowthRate > fundamentalGrowth + 2
            else ("underpriced" if implied.impliedGrowthRate < fundamentalGrowth - 2 else "fair")
        )
    return out


__all__ = ["buildDriverScenarios", "buildReinvestmentPath", "reverseDcfExhibit"]
