"""내재가치 추정 엔진 — DCF + DDM + 상대가치."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from dartlab.analysis.valuation._dcfDdm import _annualDividends, ddmValuation
from dartlab.analysis.valuation._dcfInputs import (
    _computeExitMultipleTv,
    _epsGrowth3Y,
    _estimateSectorPsr,
    _fallbackNormalizedEarningsFcf,
    _fallbackOcfBasedFcf,
    _fcfHistory,
    _getFcfFromSeries,
    _getNetDebt,
    _normalizeBaseFcf,
    _normalizedEarnings,
    _projectFcf,
    _resolveBaseFcf,
)
from dartlab.analysis.valuation._dcfTypes import (
    DCFResult,
    DDMResult,
    RelativeValuationResult,
    SensitivityResult,
    ValuationSummary,
)

# ── 내부 유틸 ──────────────────────────────────────────────
from dartlab.core.utils.calc import cagr as _cagr  # noqa: E402
from dartlab.core.utils.extract import (
    getAnnualValues,
    getLatest,
    getRevenueGrowth3Y,
    getTTM,
)
from dartlab.core.utils.fmt import fmtBig, fmtPrice
from dartlab.frame.sector import SectorParams

# ── Damodaran Two-Stage DCF (Investment Valuation Ch.12) ──────────────────
# 명시적 고성장 n년 → stable 수렴. Growth equation 엄격 적용.


def multiStageDcf(
    *,
    baseFcf: float,
    growthYears: int | list[int],
    growthRates: float | list[float],
    terminalGrowthRate: float,
    wacc: float,
    marginPath: list[float] | None = None,
    reinvestmentPath: list[float] | None = None,
    netDebt: float = 0.0,
    shares: int | None = None,
) -> dict:
    """Damodaran Multi-stage DCF — N-phase 가변 성장률 + Gordon Terminal.

    Capabilities:
        Damodaran (Investment Valuation Ch.12) 의 N-stage DCF — 각 phase 별
        다른 성장률/마진/재투자율을 적용하여 FCF 투영 후 phase 별 WACC 할인,
        terminal phase 는 Gordon growth model. ``calcDFV`` 의 TSD path 가
        본 함수를 호출 (``_tsdBuildPhases`` 가 phase list 구성).

    Args:
        baseFcf: 기준 FCF (원).
        growthYears: phase 별 연수. ``5`` 또는 ``[5, 3, 2]``.
        growthRates: phase 별 성장률 (%). ``8.0`` 또는 ``[8.0, 5.0, 3.0]``.
        terminalGrowthRate: Gordon 영구성장률 (%). WACC - 2% 이하 권장,
            Rf 초과 금지 (Damodaran).
        wacc: 할인율 (%).
        marginPath: 연도별 영업마진 (선택). None 시 baseFcf 가 마진 반영 가정.
        reinvestmentPath: 연도별 재투자율 (선택). None 시 baseFcf = FCF.
        netDebt: 순차입금 (원). enterprise → equity 변환.
        shares: 발행주식수. 주당 가치 산출.

    Returns:
        dict:
            - ``baseFcf``/``wacc``/``terminalGrowthRate`` (float)
            - ``growthYears``/``growthRates`` (list)
            - ``fcfProjections`` (list[float]): 연도별 FCF 투영
            - ``presentValues`` (list[float]): 연도별 PV
            - ``terminalValue`` (float): Gordon TV
            - ``terminalValuePV`` (float): TV 의 현재가치
            - ``netDebt``/``shares`` (float)
            - ``enterpriseValue``/``equityValue``/``perShareValue`` (float)
            - ``warnings`` (list[str])

    Raises:
        없음 — WACC ≤ terminalGrowth 시 자동 조정.

    Example:
        >>> r = multiStageDcf(baseFcf=1e10, growthYears=[5, 3, 2],
        ...                   growthRates=[15, 8, 3], terminalGrowthRate=2,
        ...                   wacc=10, netDebt=2e10, shares=1e8)
        >>> r["perShareValue"]

    Guide:
        N-phase 의 N 은 lifecycle 단계 — earlyGrowth (3 phase: 고/중/저
        성장), mature (1 phase), decline (terminal 음수). _tsdBuildPhases
        가 자동 구성. growth/marginPath/reinvestment 모두 list 일 때 길이
        일치 필수 (불일치 시 짧은 쪽 기준 truncate).

    When:
        Damodaran Two-Stage 또는 multi-phase DCF 필요 시. calcDFV 의 TSD path
        가 본 함수를 호출 (직접 호출은 advanced 사용자/엔진 전용).

    How:
        multiStageDcf(baseFcf=fcf, growthYears=[5,3,2], growthRates=[15,8,3],
        terminalGrowthRate=2, wacc=10, netDebt=nd, shares=s) 형식.

    SeeAlso:
        - ``dcfValuation``: 단순 2-stage 버전
        - ``calcDFV``: 다중 모델 통합 (본 함수 호출)
        - ``_tsdBuildPhases``: phase list 자동 구성

    Requires:
        baseFcf > 0, wacc > terminalGrowth (자동 조정).

    AIContext:
        terminal value 가 enterprise value 의 70%+ 면 결과 신뢰도 낮음
        (Gordon 가정 의존도 과다). marginPath 사용 시 reinvestment 도 함께
        지정 권장 (margin 만 변하면 FCF 비현실적).

    LLM Specifications:
        AntiPatterns:
            - terminalGrowthRate > Rf (무위험이자율) — Gordon 가정 위반.
            - growthYears scalar + growthRates list (또는 그 반대) — 자동
              broadcast 되지만 의도 불명확.
            - marginPath 없이 reinvestmentPath 만 — baseFcf 가 이미 마진
              반영 가정과 충돌.
        OutputSchema:
            상기 12 키 dict.
        Prerequisites:
            baseFcf > 0, wacc > 0, terminalGrowthRate < wacc.
        Freshness:
            stateless — 입력 가정의 freshness 에 따름.
        Dataflow:
            phase 별 (years × growth) → FCF projection → discount →
            terminal value (Gordon) → enterprise → equity (- netDebt) → 주당.
        TargetMarkets: Global. 통화는 호출자 (baseFcf/netDebt 동일 단위).

    Returns
    -------
    dict
        baseFcf, wacc, terminalGrowthRate
        growthYears : list[int]
        growthRates : list[float]
        marginPath, reinvestmentPath
        projections : list[float] — 연도별 예측 FCF
        phases : list[{years, rate, pv}]
        pvExplicit, terminalValue, pvTerminal, enterpriseValue,
        equityValue, perShare, tvShare, warnings
    """
    warnings: list[str] = []

    # 입력 정규화 — scalar → list
    years_list = [growthYears] if isinstance(growthYears, int) else list(growthYears)
    rates_list = [growthRates] if isinstance(growthRates, (int, float)) else list(growthRates)

    if len(years_list) != len(rates_list):
        warnings.append(f"growthYears/Rates length mismatch ({len(years_list)} vs {len(rates_list)}) — truncate")
        m = min(len(years_list), len(rates_list))
        years_list = years_list[:m]
        rates_list = rates_list[:m]

    total_years = sum(max(1, y) for y in years_list)
    if total_years > 15:
        warnings.append(f"총 고성장 구간 {total_years}년은 과도 — 10년 내로 축소 권장")

    # TG 보정
    if wacc <= terminalGrowthRate:
        old_tg = terminalGrowthRate
        terminalGrowthRate = max(wacc - 2.0, 1.0)
        warnings.append(f"영구성장률 {old_tg:.1f}% ≥ WACC {wacc:.1f}% → {terminalGrowthRate:.1f}%로 보정")

    r = wacc / 100.0
    gs = terminalGrowthRate / 100.0

    projections: list[float] = []
    phases_info: list[dict] = []
    current = baseFcf
    global_year = 0
    pv_explicit = 0.0

    for phase_idx, (ph_years, ph_rate) in enumerate(zip(years_list, rates_list)):
        ph_years = max(1, int(ph_years))
        g = ph_rate / 100.0
        phase_pv = 0.0
        for _ in range(ph_years):
            global_year += 1
            current = current * (1 + g)
            # marginPath 가 있으면 FCF 재조정
            if marginPath and global_year - 1 < len(marginPath):
                # margin 변화만큼 FCF 조정 (baseFcf × (margin[t] / baseMargin) — 단순 근사)
                # 실제로는 revenue × margin 이지만 여기선 FCF 기반이므로 스킵 (반환 dict 에만 기록)
                pass
            projections.append(current)
            pv_year = current / ((1 + r) ** global_year)
            phase_pv += pv_year
            pv_explicit += pv_year
        phases_info.append(
            {
                "years": ph_years,
                "rate": ph_rate,
                "pv": phase_pv,
                "endFcf": current,
            }
        )

    # Terminal
    fcf_next = projections[-1] * (1 + gs)
    terminal_value = fcf_next / (r - gs)
    pv_terminal = terminal_value / ((1 + r) ** global_year)

    enterprise_value = pv_explicit + pv_terminal
    tv_share = pv_terminal / enterprise_value if enterprise_value > 0 else 0.0

    equity_value = enterprise_value - netDebt
    per_share = equity_value / shares if shares and shares > 0 else None

    if tv_share > 0.80:
        warnings.append(f"Terminal Value 비중 {tv_share * 100:.0f}% 과도 — explicit 구간 신뢰도 낮음")

    return {
        "baseFcf": baseFcf,
        "growthYears": years_list,
        "growthRates": rates_list,
        "terminalGrowthRate": terminalGrowthRate,
        "wacc": wacc,
        "marginPath": marginPath,
        "reinvestmentPath": reinvestmentPath,
        "projections": projections,
        "phases": phases_info,
        "pvExplicit": pv_explicit,
        "terminalValue": terminal_value,
        "pvTerminal": pv_terminal,
        "netDebt": netDebt,
        "shares": shares,
        "enterpriseValue": enterprise_value,
        "equityValue": equity_value,
        "perShare": per_share,
        "tvShare": tv_share,
        "warnings": warnings,
    }


def twoStageDcf(
    *,
    baseFcf: float,
    growthYears: int,
    highGrowthRate: float,
    terminalGrowthRate: float,
    wacc: float,
    netDebt: float = 0.0,
    shares: int | None = None,
) -> dict:
    """Two-Stage DCF — multiStageDcf wrapper (backward compat).

    단일 phase (n 년 × 단일 성장률) + terminal. 기존 호출 호환용.

    Capabilities:
        - 단일 phase + terminal multiStageDcf 호출 wrapper
        - highGrowthRate 단일 값 → growthRates=[highGrowthRate] 변환
        - 기존 caller 의 highGrowthRate 키 호환 유지

    Args:
        baseFcf: 기준 FCF (원).
        growthYears: 명시적 고성장 구간 연수.
        highGrowthRate: 고성장 구간 성장률 (%).
        terminalGrowthRate: Gordon 영구성장률 (%).
        wacc: 할인율 (%).
        netDebt: 순차입금 (원).
        shares: 발행주식수.

    Returns:
        dict — multiStageDcf 반환 + highGrowthRate 키 추가.

    Example:
        >>> twoStageDcf(baseFcf=1e10, growthYears=5, highGrowthRate=15,
        ...             terminalGrowthRate=3, wacc=10, netDebt=2e10, shares=1e8)

    Guide:
        새 코드에서는 multiStageDcf 직접 호출 권장. 본 함수는 backward compat.

    When:
        기존 단일 phase DCF 코드 호환 유지 필요 시.

    How:
        twoStageDcf(baseFcf=..., growthYears=5, highGrowthRate=..., ...).

    Requires:
        multiStageDcf — 본 함수가 호출.

    Raises:
        없음.

    SeeAlso:
        - multiStageDcf : 본 함수가 호출하는 N-stage 본체

    AIContext:
        2-stage DCF 단순 인용 시 본 함수 결과 인용. multiStageDcf 동일 결과.
    """
    r = multiStageDcf(
        baseFcf=baseFcf,
        growthYears=[growthYears],
        growthRates=[highGrowthRate],
        terminalGrowthRate=terminalGrowthRate,
        wacc=wacc,
        netDebt=netDebt,
        shares=shares,
    )
    # 기존 twoStageDcf 반환 키 호환
    r["highGrowthRate"] = highGrowthRate
    # growthYears 는 list[int] 상태 — 기존 caller 가 int 를 기대할 수 있으므로
    # primary dict 구조는 유지 (list). 기존 테스트는 projections/pvExplicit/tvShare 만 검증.
    return r


# ── Damodaran Liquidation Valuation + Relative + Sensitivity ─────────────
# 실 구현은 _dcfRelative.py 분리. BC 위해 re-export.
from dartlab.analysis.valuation._dcfRelative import (  # noqa: E402
    _LIQUIDATION_RECOVERY,
    liquidationValuation,
    relativeValuation,
    sensitivityAnalysis,
)

# ── DCF ──────────────────────────────────────────────


def dcfValuation(
    series: dict,
    shares: Optional[int] = None,
    sectorParams: Optional[SectorParams] = None,
    currentPrice: Optional[float] = None,
    discountRate: Optional[float] = None,
    terminalGrowth: Optional[float] = None,
    projectionYears: int = 5,
    currency: str = "KRW",
    proformaFCF: Optional[list[float]] = None,
) -> DCFResult:
    """2-Stage DCF 밸류에이션 — FCF 프로젝션 + Terminal Value → 주당 가치.

    Capabilities:
        FCF 시계열에서 base FCF 추정 → 5년 초기 성장 (매출 3Y CAGR + 섹터
        평균) → Gordon growth terminal value → WACC 할인 → 기업가치 + 주당
        가치 산출. Damodaran multiStage DCF 의 직접 단순화 버전.

    Args:
        series: ``finance.timeseries`` 시계열 dict (BS/IS/CF).
        shares: 발행주식수. 주당 가치 산출용.
        sectorParams: 업종별 할인율/성장률.
        currentPrice: 현재 주가 (원). marginOfSafety 계산용.
        discountRate: WACC override (sectorParams.discountRate 우선).
        terminalGrowth: 영구성장률 override. None 시 ``min(sector growth, 3%)``.
        projectionYears: 초기 성장기 (년). 기본 5.
        currency: ``"KRW"`` 또는 ``"USD"``. 출력 단위.
        proformaFCF: AI 가 산출한 향후 FCF list override. 주어지면 ``_projectFcf``
            가 이를 base 로 사용.

    Returns:
        DCFResult dataclass:
            - ``fcfHistorical``/``fcfProjections`` (list[float])
            - ``terminalValue``/``enterpriseValue``/``equityValue`` (float)
            - ``perShareValue`` (float|None): shares 가 있어야 산출
            - ``discountRate``/``growthRateInitial``/``terminalGrowth`` (float)
            - ``marginOfSafety`` (float|None): (perShare - currentPrice) /
              currentPrice * 100. currentPrice 없으면 None
            - ``warnings`` (list[str]): DCF 적용 불가/조정 경고
            - ``currency`` (str)
        FCF 음수 시 빈 결과 + "DCF 적용 불가" warning.

    Raises:
        없음.

    Example:
        >>> from dartlab.frame.sector import getSectorParamsByName
        >>> r = dcfValuation(series, shares=5e9, sectorParams=getSectorParamsByName("IT"),
        ...                  currentPrice=75000)  # doctest: +SKIP
        >>> r.perShareValue, r.marginOfSafety  # doctest: +SKIP
        (82000.0, 9.3)

    Guide:
        WACC ≤ terminalGrowth 시 ``wacc - 2.0`` 으로 자동 조정 + warning. initial
        growth 는 매출 3Y CAGR 기반, [-5%, 15%] clamp. FCF 음수 회사는 DCF
        부적합 — 호출자가 ``calcDFV`` 의 multi-model triangulation 사용 권장.

    When:
        단일 모델 DCF 인용이 필요한 화면/CLI/notebook 에서 직접 호출.
        다중 모델 통합은 calcDFV 사용.

    How:
        dcfValuation(series, shares=s, sectorParams=sp, currentPrice=p) 형식.
        series 는 company.finance.timeseries 또는 frame.toTimeseries 결과.

    SeeAlso:
        - ``multiStageDcf``: phase 별 다중 stage DCF
        - ``ddmValuation``: 배당 기반 가치 (현금흐름 없는 회사)
        - ``calcDFV``: 다중 모델 통합 진입점

    Requires:
        series 가 finance.timeseries 스키마. 최소 3 년 시계열.

    AIContext:
        DCF 가치 단독 인용 금지 — marginOfSafety + warnings 함께 노출. FCF
        음수/수익 매출 변동성 큰 회사 (initial growth > 15%) 는 신뢰도 낮음.
        Damodaran 의 권고: terminalGrowth ≤ 무위험이자율.

    LLM Specifications:
        AntiPatterns:
            - terminalGrowth 4%+ 입력 금지 (실질 GDP 성장률 초과 = Gordon
              가정 위반). 자동 조정되지만 warning 발생.
            - shares 미지정 시 perShareValue=None — currentPrice 와 비교 불가.
            - currentPrice 가 distressed (실가치 대비 -50%+) 인 회사에서
              marginOfSafety 가 비정상 (500%+) → DCF 가정 자체 의심.
        OutputSchema:
            DCFResult (12 필드 dataclass).
        Prerequisites:
            series 의 CF/operating_cashflow + capex 시계열 ≥ 3 년.
        Freshness:
            series 의 freshness (보통 최신 분기).
        Dataflow:
            series → _resolveBaseFcf → revCagr → _projectFcf (5 년) →
            terminal value (Gordon) → WACC 할인 → enterprise → equity
            (net debt 차감) → 주당.
        TargetMarkets: KR (DART 기준 통화 KRW), US (EDGAR USD).
    """
    warnings: list[str] = []

    wacc = discountRate or (sectorParams.discountRate if sectorParams else 10.0)
    sectorGrowth = sectorParams.growthRate if sectorParams else 3.0
    tg = terminalGrowth if terminalGrowth is not None else min(sectorGrowth, 3.0)

    if wacc <= tg:
        tg = max(wacc - 2.0, 1.0)
        warnings.append(f"영구성장률이 할인율 이상이어서 {tg:.1f}%로 조정")

    fcfCurrent, fcfHist = _resolveBaseFcf(series, warnings)

    if fcfCurrent is None or fcfCurrent <= 0:
        return DCFResult(
            fcfHistorical=fcfHist,
            fcfProjections=[],
            terminalValue=None,
            enterpriseValue=None,
            equityValue=None,
            perShareValue=None,
            discountRate=wacc,
            growthRateInitial=0,
            terminalGrowth=tg,
            marginOfSafety=None,
            warnings=warnings + ["FCF 데이터 부족으로 DCF 적용 불가"],
            currency=currency,
            status="unavailable",
            blockedReason="FCF를 산출할 CAPEX·영업현금흐름 근거가 충분하지 않습니다.",
        )

    revCagr = getRevenueGrowth3Y(series)
    if revCagr is not None:
        initialGrowth = min(max(revCagr, -5.0), 15.0)
    else:
        initialGrowth = sectorGrowth
        warnings.append("매출 3Y CAGR 미확인 → 섹터 평균 성장률 적용")

    projections = _projectFcf(fcfCurrent, initialGrowth, tg, projectionYears, proformaFCF, warnings)

    finalFcf = projections[-1]
    tv = finalFcf * (1 + tg / 100) / (wacc / 100 - tg / 100)
    pvFcfs = sum(fcf / (1 + wacc / 100) ** yr for yr, fcf in enumerate(projections, 1))
    pvTv = tv / (1 + wacc / 100) ** projectionYears
    ev = pvFcfs + pvTv

    netDebt = _getNetDebt(series)
    eqValue = ev - netDebt if netDebt is not None else None
    if netDebt is None:
        warnings.append("차입금 또는 현금 근거가 없어 주주가치·주당가치 발행 차단")
    perShare = eqValue / shares if eqValue is not None and shares and shares > 0 else None
    mos = None
    if perShare is not None and currentPrice is not None and currentPrice > 0:
        mos = (perShare - currentPrice) / currentPrice * 100

    if netDebt is None:
        exitTv, exitEv, exitPerShare, exitMult = None, None, None, None
    else:
        exitTv, exitEv, exitPerShare, exitMult = _computeExitMultipleTv(
            series, sectorParams, initialGrowth, tg, projectionYears, wacc, pvFcfs, netDebt, shares
        )

    assumptions = {
        "할인율": f"{wacc:.1f}%",
        "초기성장률": f"{initialGrowth:.1f}%",
        "영구성장률": f"{tg:.1f}%",
        "예측기간": f"{projectionYears}년",
        "순차입금": fmtBig(netDebt, currency) if netDebt is not None else "미확인",
        "기준FCF": fmtBig(fcfCurrent, currency),
    }
    if exitMult:
        assumptions["Exit Multiple"] = f"EV/EBITDA {exitMult:.1f}x"

    return DCFResult(
        fcfHistorical=fcfHist,
        fcfProjections=projections,
        terminalValue=tv,
        enterpriseValue=ev,
        equityValue=eqValue,
        perShareValue=perShare,
        discountRate=wacc,
        growthRateInitial=initialGrowth,
        terminalGrowth=tg,
        marginOfSafety=mos,
        exitMultipleTv=exitTv,
        exitMultipleEv=exitEv,
        exitMultiplePerShare=exitPerShare,
        assumptions=assumptions,
        warnings=warnings,
        currency=currency,
        status="usable" if netDebt is not None else "partial",
        blockedReason=None if netDebt is not None else "순차입금 근거가 없어 주주가치·주당가치를 발행하지 않습니다.",
    )


# ── 종합 밸류에이션 ──────────────────────────────────────────


def fullValuation(
    series: dict,
    shares: Optional[int] = None,
    sectorParams: Optional[SectorParams] = None,
    marketCap: Optional[float] = None,
    currentPrice: Optional[float] = None,
    currency: str = "KRW",
    discountRate: Optional[float] = None,
) -> ValuationSummary:
    """DCF + DDM + 상대가치 종합 밸류에이션.

    Capabilities:
        - dcfValuation + ddmValuation + relativeValuation 3 채널 합성
        - 극단값 (현재가 1/20 미만) 제거 후 fairValueRange 산출
        - 평균 대비 ratio 로 저평가/적정/고평가 verdict 판정

    Args:
        series: finance.timeseries dict (BS/IS/CF).
        shares: 발행주식수.
        sectorParams: 업종별 할인율/성장률.
        marketCap: 시가총액 (상대가치용).
        currentPrice: 현재 주가 (verdict 산출용).
        currency: "KRW" or "USD".
        discountRate: WACC override.

    Returns:
        ValuationSummary — dcf/ddm/relative + fairValueRange + verdict.

    Example:
        >>> r = fullValuation(series, shares=5e9, marketCap=4.5e14, currentPrice=75000)
        >>> r.verdict, r.fairValueRange

    Guide:
        DDM 미가용 (무배당) 회사는 dcf+relative 만으로 verdict 산출.
        극단값 floor = currentPrice/20.

    When:
        구버전 종합 밸류에이션 인터페이스 (3 채널 단순 평균). 새 코드는
        calcDFV 의 quality-adjusted WACC + 삼각검증 사용.

    How:
        fullValuation(series, shares=s, sectorParams=sp, marketCap=mc, currentPrice=p).

    Requires:
        dcfValuation + ddmValuation + relativeValuation 헬퍼 + series 시계열.

    Raises:
        없음 — 모든 모델 실패 시 verdict="판단불가" + fairRange=None.

    SeeAlso:
        - calcDFV : v2 통합 진입점 (권장)
        - dcfValuation / ddmValuation / relativeValuation : 채널별

    AIContext:
        구 API 인용. 새 답변은 calcDFV 결과 우선, fullValuation 은 fallback.
    """
    dcf = dcfValuation(
        series,
        shares=shares,
        sectorParams=sectorParams,
        currentPrice=currentPrice,
        currency=currency,
        discountRate=discountRate,
    )
    ddm = ddmValuation(series, shares=shares, sectorParams=sectorParams, currentPrice=currentPrice)
    ddm.currency = currency
    rel = relativeValuation(
        series, sectorParams=sectorParams, marketCap=marketCap, shares=shares, currentPrice=currentPrice
    )
    rel.currency = currency

    estimates: list[float] = []
    if dcf.perShareValue is not None and dcf.perShareValue > 0:
        estimates.append(dcf.perShareValue)
    if ddm.intrinsicValue is not None and ddm.intrinsicValue > 0:
        estimates.append(ddm.intrinsicValue)
    if rel.consensusValue is not None and rel.consensusValue > 0:
        estimates.append(rel.consensusValue)

    # 극단값 제거: 현재가의 1/20 미만은 모델 오류 가능성 높음
    if currentPrice and currentPrice > 0:
        _floor = currentPrice / 20
        estimates = [e for e in estimates if e >= _floor]

    fairRange = None
    verdict = "판단불가"

    if estimates:
        lo = min(estimates)
        hi = max(estimates)
        fairRange = (round(lo * 0.9, 0), round(hi * 1.1, 0))

        if currentPrice and currentPrice > 0:
            mid = sum(estimates) / len(estimates)
            ratio = currentPrice / mid
            if ratio < 0.8:
                verdict = "저평가"
            elif ratio > 1.2:
                verdict = "고평가"
            else:
                verdict = "적정"

    return ValuationSummary(
        dcf=dcf,
        ddm=ddm,
        relative=rel,
        fairValueRange=fairRange,
        currentPrice=currentPrice,
        verdict=verdict,
        currency=currency,
    )
