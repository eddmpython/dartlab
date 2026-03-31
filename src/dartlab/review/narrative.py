"""재무제표 순환 서사(Narrative) — 섹션 간 인과관계 자동 감지.

재무제표는 유기체다. BS/IS/CF가 하나의 순환계를 이루고,
한 영역의 문제가 다른 영역에 전파된다.
이 모듈은 company.select()로 원본 시계열을 읽어
7가지 인과 패턴을 감지하고 NarrativeThread로 반환한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

_MAX_YEARS = 5


@dataclass
class NarrativeThread:
    """섹션 간 인과 연결 하나."""

    threadId: str
    title: str
    story: str
    involvedSections: list[str] = field(default_factory=list)
    severity: str = "warning"  # critical | warning | neutral | positive
    evidence: list[str] = field(default_factory=list)


# ── 유틸 ──


def _toDict(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    from dartlab.analysis.financial._helpers import toDict

    return toDict(selectResult)


def _annualCols(periods: list[str], maxYears: int = _MAX_YEARS) -> list[str]:
    cols = sorted([c for c in periods if "Q" not in c], reverse=True)
    if cols:
        return cols[:maxYears]
    return sorted([c for c in periods if c.endswith("Q4")], reverse=True)[:maxYears]


def _get(row: dict, col: str) -> float:
    v = row.get(col) if row else None
    return v if v is not None else 0


def _yoy(cur: float, prev: float) -> float | None:
    """YoY 변화율(%). prev가 0이면 None."""
    if prev == 0:
        return None
    return (cur - prev) / abs(prev) * 100


def _collectFlags(blockMap, *keys: str) -> list[str]:
    """BlockMap에서 FlagBlock의 flags를 수집."""
    from dartlab.review.blocks import FlagBlock

    result = []
    for key in keys:
        blocks = blockMap.get(key)
        if not blocks:
            continue
        for b in blocks:
            if isinstance(b, FlagBlock):
                result.extend(b.flags)
    return result


# ── 패턴 1: 매출 하락 → 마진 압박 → 현금 악화 ──


def _detectRevenueDeclineChain(company, blockMap) -> NarrativeThread | None:
    isResult = company.select("IS", ["매출액", "영업이익", "당기순이익"])
    cfResult = company.select("CF", ["영업활동현금흐름"])

    isParsed = _toDict(isResult)
    cfParsed = _toDict(cfResult)
    if isParsed is None or cfParsed is None:
        return None

    isData, isPeriods = isParsed
    cfData, _ = cfParsed

    revRow = isData.get("매출액", {})
    opRow = isData.get("영업이익", {})
    ocfRow = cfData.get("영업활동현금흐름", {})

    yCols = _annualCols(isPeriods)
    if len(yCols) < 2:
        return None

    col0, col1 = yCols[0], yCols[1]
    rev0, rev1 = _get(revRow, col0), _get(revRow, col1)
    op0, op1 = _get(opRow, col0), _get(opRow, col1)
    ocf0, ocf1 = _get(ocfRow, col0), _get(ocfRow, col1)

    revGrowth = _yoy(rev0, rev1)
    if revGrowth is None or revGrowth >= 0:
        return None

    # 영업이익률 하락
    opm0 = op0 / rev0 * 100 if rev0 > 0 else None
    opm1 = op1 / rev1 * 100 if rev1 > 0 else None
    if opm0 is None or opm1 is None or opm0 >= opm1:
        return None

    # 영업CF도 감소
    if ocf0 >= ocf1:
        return None

    evidence = [
        f"매출 YoY {revGrowth:+.1f}% ({col1}→{col0})",
        f"영업이익률 {opm1:.1f}%→{opm0:.1f}%",
        f"영업CF {ocf1:,.0f}→{ocf0:,.0f}",
    ]

    return NarrativeThread(
        threadId="revenue_decline_chain",
        title="매출 하락 -> 마진 압박 -> 현금 악화",
        story=(
            f"매출이 {revGrowth:+.1f}% 감소하며 영업이익률이 "
            f"{opm1:.1f}%에서 {opm0:.1f}%로 하락했다. "
            f"영업현금흐름도 동반 감소하여 수익-현금 순환이 약화되고 있다."
        ),
        involvedSections=["수익구조", "수익성", "현금흐름"],
        severity="critical",
        evidence=evidence,
    )


# ── 패턴 2: 차입 증가 → 이자부담 → 수익성 악화 ──


def _detectDebtBurdenChain(company, blockMap) -> NarrativeThread | None:
    bsResult = company.select("BS", ["부채총계", "자본총계"])
    isResult = company.select("IS", ["영업이익", "이자비용"])

    bsParsed = _toDict(bsResult)
    isParsed = _toDict(isResult)
    if bsParsed is None or isParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    isData, _ = isParsed

    tlRow = bsData.get("부채총계", {})
    eqRow = bsData.get("자본총계", {})
    opRow = isData.get("영업이익", {})
    intRow = isData.get("이자비용", {})

    yCols = _annualCols(bsPeriods)
    if len(yCols) < 2:
        return None

    col0, col1 = yCols[0], yCols[1]
    tl0, tl1 = _get(tlRow, col0), _get(tlRow, col1)
    eq0 = _get(eqRow, col0)
    eq1 = _get(eqRow, col1)
    op0, op1 = _get(opRow, col0), _get(opRow, col1)
    int0, int1 = _get(intRow, col0), _get(intRow, col1)

    # 부채 증가
    debtGrowth = _yoy(tl0, tl1)
    if debtGrowth is None or debtGrowth <= 5:
        return None

    # 이자보상배율 하락
    icr0 = op0 / abs(int0) if int0 != 0 else None
    icr1 = op1 / abs(int1) if int1 != 0 else None
    if icr0 is None or icr1 is None or icr0 >= icr1:
        return None

    # ROE 하락
    roe0 = op0 / eq0 * 100 if eq0 > 0 else None
    roe1 = op1 / eq1 * 100 if eq1 > 0 else None
    if roe0 is None or roe1 is None or roe0 >= roe1:
        return None

    evidence = [
        f"부채 YoY {debtGrowth:+.1f}%",
        f"이자보상배율 {icr1:.1f}x→{icr0:.1f}x",
        f"ROE {roe1:.1f}%→{roe0:.1f}%",
    ]

    return NarrativeThread(
        threadId="debt_burden_chain",
        title="차입 증가 -> 이자부담 -> 수익성 악화",
        story=(
            f"부채가 {debtGrowth:+.1f}% 증가하며 이자보상배율이 "
            f"{icr1:.1f}x에서 {icr0:.1f}x로 하락했다. "
            f"ROE도 {roe1:.1f}%에서 {roe0:.1f}%로 떨어져 "
            f"차입 확대가 수익성을 잠식하고 있다."
        ),
        involvedSections=["자금조달", "안정성", "수익성"],
        severity="critical",
        evidence=evidence,
    )


# ── 패턴 3: 운전자본 팽창 → 현금 고갈 → 유동성 위기 ──


def _detectWorkingCapitalStrain(company, blockMap) -> NarrativeThread | None:
    bsResult = company.select("BS", ["매출채권및기타채권", "재고자산", "매입채무", "유동자산", "유동부채"])
    isResult = company.select("IS", ["매출액", "당기순이익"])
    cfResult = company.select("CF", ["영업활동현금흐름"])

    bsParsed = _toDict(bsResult)
    isParsed = _toDict(isResult)
    cfParsed = _toDict(cfResult)
    if bsParsed is None or isParsed is None or cfParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    isData, _ = isParsed
    cfData, _ = cfParsed

    recRow = bsData.get("매출채권및기타채권", {})
    invRow = bsData.get("재고자산", {})
    payRow = bsData.get("매입채무", {})
    caRow = bsData.get("유동자산", {})
    clRow = bsData.get("유동부채", {})
    revRow = isData.get("매출액", {})
    niRow = isData.get("당기순이익", {})
    ocfRow = cfData.get("영업활동현금흐름", {})

    yCols = _annualCols(bsPeriods)
    if len(yCols) < 2:
        return None

    col0, col1 = yCols[0], yCols[1]
    rev0 = _get(revRow, col0)
    ni0 = _get(niRow, col0)
    ocf0 = _get(ocfRow, col0)

    # 매출채권 + 재고 - 매입채무 = 순운전자본
    nwc0 = _get(recRow, col0) + _get(invRow, col0) - _get(payRow, col0)
    nwc1 = _get(recRow, col1) + _get(invRow, col1) - _get(payRow, col1)

    nwcGrowth = _yoy(nwc0, nwc1)
    if nwcGrowth is None or nwcGrowth <= 10:
        return None

    # 영업CF/순이익 괴리 (현금 전환 부족)
    if ni0 <= 0 or ocf0 / ni0 > 0.7:
        return None

    # 유동비율 하락
    cr0 = _get(caRow, col0) / _get(clRow, col0) if _get(clRow, col0) > 0 else None
    cr1 = _get(caRow, col1) / _get(clRow, col1) if _get(clRow, col1) > 0 else None
    if cr0 is None or cr1 is None or cr0 >= cr1:
        return None

    # 순현금 상태이면 "유동성 위기" 서사 억제
    try:
        ratios = company.finance.ratios
        nd = getattr(ratios, "netDebt", None)
        if nd is not None and nd < 0:
            return None  # 순현금이면 유동성 위기 아님
    except (AttributeError, ValueError):
        pass

    ocfNiRatio = ocf0 / ni0 * 100

    evidence = [
        f"순운전자본 YoY {nwcGrowth:+.1f}%",
        f"영업CF/순이익 {ocfNiRatio:.0f}%",
        f"유동비율 {cr1:.2f}→{cr0:.2f}",
    ]

    return NarrativeThread(
        threadId="working_capital_strain",
        title="운전자본 팽창 -> 현금 고갈 -> 유동성 위기",
        story=(
            f"순운전자본이 {nwcGrowth:+.1f}% 팽창하며 현금이 묶이고 있다. "
            f"영업CF/순이익 비율이 {ocfNiRatio:.0f}%로 이익 대비 현금 회수가 부족하고, "
            f"유동비율도 {cr1:.2f}에서 {cr0:.2f}로 하락했다."
        ),
        involvedSections=["자산구조", "현금흐름", "자금조달"],
        severity="warning",
        evidence=evidence,
    )


# ── 패턴 4: 과잉투자 → ROIC 하락 → EVA 음수 ──


def _detectOverinvestment(company, blockMap) -> NarrativeThread | None:
    cfResult = company.select("CF", ["유형자산의취득"])
    isResult = company.select("IS", ["영업이익", "감가상각비", "법인세비용", "법인세차감전순이익", "세전이익"])
    bsResult = company.select("BS", ["자산총계", "자본총계", "부채총계"])

    cfParsed = _toDict(cfResult)
    isParsed = _toDict(isResult)
    bsParsed = _toDict(bsResult)
    if cfParsed is None or isParsed is None or bsParsed is None:
        return None

    cfData, cfPeriods = cfParsed
    isData, _ = isParsed
    bsData, _ = bsParsed

    capexRow = cfData.get("유형자산의취득", {})
    depRow = isData.get("감가상각비", {})
    opRow = isData.get("영업이익", {})
    taxRow = isData.get("법인세비용", {})
    ptRow = isData.get("법인세차감전순이익", isData.get("세전이익", {}))
    taRow = bsData.get("자산총계", {})
    eqRow = bsData.get("자본총계", {})

    yCols = _annualCols(cfPeriods)
    if len(yCols) < 2:
        return None

    col0 = yCols[0]
    capex = abs(_get(capexRow, col0))
    dep = _get(depRow, col0)
    op = _get(opRow, col0)
    tax = _get(taxRow, col0)
    pt = _get(ptRow, col0)
    ta = _get(taRow, col0)
    eq = _get(eqRow, col0)

    # CAPEX/감가상각 > 2
    if dep <= 0 or capex / dep <= 2:
        return None

    capexDepRatio = capex / dep

    # ROIC 추정: NOPAT / 투하자본
    effTaxRate = tax / pt if pt > 0 else 0.25
    nopat = op * (1 - min(max(effTaxRate, 0), 0.5))
    investedCapital = eq + (_get(bsData.get("부채총계", {}), col0) - _get(bsData.get("자본총계", {}), col0) * 0)
    # 간이 투하자본 = 자산총계 (현금 차감 없는 단순화)
    roic = nopat / ta * 100 if ta > 0 else None

    if roic is None or roic > 8:
        return None

    # EVA 추정 (WACC 8% 가정)
    wacc = 8.0
    eva = nopat - ta * (wacc / 100)

    if eva >= 0:
        return None

    evidence = [
        f"CAPEX/감가상각 {capexDepRatio:.1f}x",
        f"ROIC 추정 {roic:.1f}%",
        f"EVA 추정 {eva:,.0f} (WACC {wacc}% 가정)",
    ]

    return NarrativeThread(
        threadId="overinvestment_chain",
        title="과잉투자 -> ROIC 하락 -> EVA 음수",
        story=(
            f"CAPEX가 감가상각의 {capexDepRatio:.1f}배로 공격적 투자가 진행 중이나, "
            f"ROIC가 {roic:.1f}%로 자본비용(WACC {wacc}%)을 하회하여 "
            f"경제적 부가가치가 마이너스다."
        ),
        involvedSections=["자산구조", "투자효율", "수익성"],
        severity="warning",
        evidence=evidence,
    )


# ── 패턴 5: 이익 조작 징후 복합 ──


def _detectEarningsManipulation(company, blockMap) -> NarrativeThread | None:
    isResult = company.select("IS", ["당기순이익", "매출액"])
    cfResult = company.select("CF", ["영업활동현금흐름"])
    bsResult = company.select("BS", ["자산총계", "매출채권및기타채권"])

    isParsed = _toDict(isResult)
    cfParsed = _toDict(cfResult)
    bsParsed = _toDict(bsResult)
    if isParsed is None or cfParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    cfData, _ = cfParsed
    bsData, _ = bsParsed

    niRow = isData.get("당기순이익", {})
    revRow = isData.get("매출액", {})
    ocfRow = cfData.get("영업활동현금흐름", {})
    taRow = bsData.get("자산총계", {})

    yCols = _annualCols(isPeriods)
    if not yCols:
        return None

    col0 = yCols[0]
    ni = _get(niRow, col0)
    ocf = _get(ocfRow, col0)
    ta = _get(taRow, col0)
    rev = _get(revRow, col0)

    if ta <= 0 or ni == 0:
        return None

    # Sloan 발생액비율
    accrualRatio = (ni - ocf) / ta
    if accrualRatio <= 0.10:
        return None

    # IS-CF 괴리
    divergence = (ni - ocf) / abs(ni) * 100
    if divergence <= 50:
        return None

    evidence = [
        f"Sloan 발생액비율 {accrualRatio:.1%}",
        f"IS-CF 괴리 {divergence:.0f}%",
    ]

    # M-Score가 있으면 보조 근거로 추가
    from dartlab.analysis.financial.earningsQuality import calcBeneishTimeline

    beneish = None
    try:
        beneish = calcBeneishTimeline(company)
    except (KeyError, ValueError, TypeError, AttributeError):
        pass

    mScoreExceeded = False
    if beneish and beneish.get("history"):
        ms = beneish["history"][0].get("mScore")
        if ms is not None and ms > -1.78:
            evidence.append(f"Beneish M-Score {ms:.2f} (임계값 -1.78 초과)")
            mScoreExceeded = True

    severity = "critical" if mScoreExceeded else "warning"

    return NarrativeThread(
        threadId="earnings_manipulation_signal",
        title="이익 조작 징후 복합",
        story=(
            f"발생액비율이 {accrualRatio:.1%}로 이익 중 현금이 아닌 비중이 크고, "
            f"순이익 대비 영업CF 괴리가 {divergence:.0f}%에 달한다. "
            + (
                "Beneish M-Score도 임계값을 초과하여 복합적 주의가 필요하다."
                if mScoreExceeded
                else "재무제표 신뢰성에 주의가 필요하다."
            )
        ),
        involvedSections=["이익품질", "현금흐름", "재무정합성"],
        severity=severity,
        evidence=evidence,
    )


# ── 패턴 6: 성장 + 수익성 동반 개선 (긍정) ──


def _detectGrowthProfitability(company, blockMap) -> NarrativeThread | None:
    isResult = company.select("IS", ["매출액", "영업이익", "당기순이익"])
    cfResult = company.select("CF", ["영업활동현금흐름", "유형자산의취득"])

    isParsed = _toDict(isResult)
    cfParsed = _toDict(cfResult)
    if isParsed is None or cfParsed is None:
        return None

    isData, isPeriods = isParsed
    cfData, _ = cfParsed

    revRow = isData.get("매출액", {})
    opRow = isData.get("영업이익", {})
    ocfRow = cfData.get("영업활동현금흐름", {})
    capexRow = cfData.get("유형자산의취득", {})

    yCols = _annualCols(isPeriods)
    if len(yCols) < 2:
        return None

    col0, col1 = yCols[0], yCols[1]
    rev0, rev1 = _get(revRow, col0), _get(revRow, col1)
    op0, op1 = _get(opRow, col0), _get(opRow, col1)
    ocf0 = _get(ocfRow, col0)
    capex0 = abs(_get(capexRow, col0))

    revGrowth = _yoy(rev0, rev1)
    if revGrowth is None or revGrowth <= 3:
        return None

    # 영업이익률 확대 — 적자(음수)에서 적자 축소는 "확대"가 아님
    opm0 = op0 / rev0 * 100 if rev0 > 0 else None
    opm1 = op1 / rev1 * 100 if rev1 > 0 else None
    if opm0 is None or opm1 is None or opm0 <= opm1 or opm0 < 0:
        return None

    # FCF 양수
    fcf = ocf0 - capex0
    if fcf <= 0:
        return None

    evidence = [
        f"매출 YoY {revGrowth:+.1f}%",
        f"영업이익률 {opm1:.1f}%→{opm0:.1f}%",
        f"FCF {fcf:,.0f}",
    ]

    return NarrativeThread(
        threadId="growth_profitability_positive",
        title="매출 성장 + 마진 확대 + FCF 양수",
        story=(
            f"매출이 {revGrowth:+.1f}% 성장하면서 영업이익률이 "
            f"{opm1:.1f}%에서 {opm0:.1f}%로 확대되었다. "
            f"FCF도 양수를 유지하여 질적 성장이 확인된다."
        ),
        involvedSections=["수익구조", "수익성", "현금흐름", "성장성"],
        severity="positive",
        evidence=evidence,
    )


# ── 패턴 7: 구조적 효율화 (긍정) ──


def _detectStructuralEfficiency(company, blockMap) -> NarrativeThread | None:
    isResult = company.select("IS", ["매출액", "매출원가", "판매비와관리비", "영업이익"])
    bsResult = company.select("BS", ["자산총계", "자본총계"])

    isParsed = _toDict(isResult)
    bsParsed = _toDict(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    revRow = isData.get("매출액", {})
    cogsRow = isData.get("매출원가", {})
    sgaRow = isData.get("판매비와관리비", {})
    opRow = isData.get("영업이익", {})
    taRow = bsData.get("자산총계", {})
    eqRow = bsData.get("자본총계", {})

    yCols = _annualCols(isPeriods)
    if len(yCols) < 2:
        return None

    col0, col1 = yCols[0], yCols[1]
    rev0, rev1 = _get(revRow, col0), _get(revRow, col1)
    cogs0, cogs1 = _get(cogsRow, col0), _get(cogsRow, col1)
    sga0, sga1 = _get(sgaRow, col0), _get(sgaRow, col1)
    op0 = _get(opRow, col0)
    ta0, ta1 = _get(taRow, col0), _get(taRow, col1)
    eq0, eq1 = _get(eqRow, col0), _get(eqRow, col1)

    if rev0 <= 0 or rev1 <= 0 or ta0 <= 0 or ta1 <= 0 or eq0 <= 0 or eq1 <= 0:
        return None

    # 비용률 하락
    costRatio0 = (cogs0 + sga0) / rev0 * 100
    costRatio1 = (cogs1 + sga1) / rev1 * 100
    if costRatio0 >= costRatio1:
        return None

    # 자산회전율 개선
    turnover0 = rev0 / ta0
    turnover1 = rev1 / ta1
    if turnover0 <= turnover1:
        return None

    # ROE 상승
    roe0 = op0 / eq0 * 100
    roe1 = _get(opRow, col1) / eq1 * 100
    if roe0 <= roe1:
        return None

    evidence = [
        f"영업비용률 {costRatio1:.1f}%→{costRatio0:.1f}%",
        f"자산회전율 {turnover1:.2f}→{turnover0:.2f}",
        f"ROE {roe1:.1f}%→{roe0:.1f}%",
    ]

    return NarrativeThread(
        threadId="structural_efficiency_positive",
        title="비용 절감 + 자산 효율화 + ROE 상승",
        story=(
            f"영업비용률이 {costRatio1:.1f}%에서 {costRatio0:.1f}%로 하락하고, "
            f"자산회전율이 {turnover1:.2f}에서 {turnover0:.2f}로 개선되었다. "
            f"ROE도 {roe1:.1f}%에서 {roe0:.1f}%로 상승하여 구조적 효율화가 진행 중이다."
        ),
        involvedSections=["비용구조", "효율성", "수익성"],
        severity="positive",
        evidence=evidence,
    )


# ── 메인 ──


_DETECTORS: list[tuple] = [
    (_detectRevenueDeclineChain, {"수익구조", "수익성", "현금흐름"}),
    (_detectDebtBurdenChain, {"자금조달", "안정성", "수익성"}),
    (_detectWorkingCapitalStrain, {"자산구조", "효율성", "현금흐름"}),
    (_detectOverinvestment, {"자산구조", "투자효율", "현금흐름"}),
    (_detectEarningsManipulation, {"이익품질", "재무정합성"}),
    (_detectGrowthProfitability, {"성장성", "수익성", "수익구조"}),
    (_detectStructuralEfficiency, {"효율성", "비용구조", "수익성"}),
]


def detectThreads(company, blockMap, sections: set[str] | None = None) -> list[NarrativeThread]:
    """7가지 인과 패턴을 감지하여 NarrativeThread 리스트 반환.

    sections가 지정되면 관련 섹션이 겹치는 detector만 실행.
    """
    threads = []
    for detect, involved in _DETECTORS:
        if sections is not None and not (sections & involved):
            continue
        try:
            thread = detect(company, blockMap)
            if thread is not None:
                threads.append(thread)
        except (KeyError, ValueError, TypeError, AttributeError, ArithmeticError, IndexError):
            continue
    return threads


def buildActTransitions(company, blockMap: dict) -> dict[str, str]:
    """6막 전환 시점의 인과 문장 생성.

    각 막의 핵심 숫자를 뽑아서 다음 막으로 연결하는 한 문장.
    반환: {"1→2": "...", "2→3": "...", "3→4": "...", "4→5": "...", "5→6": "..."}
    """
    transitions = {}

    try:
        ratios = company.finance.ratios
    except (AttributeError, ValueError):
        return transitions

    # 1막→2막: 매출 구조 → 수익성
    rev = getattr(ratios, "revenueTTM", None)
    opMargin = getattr(ratios, "operatingMargin", None) or getattr(ratios, "operatingMarginTTM", None)
    if rev and opMargin is not None:
        revStr = f"{rev / 1e12:.1f}조" if rev > 1e12 else f"{rev / 1e8:.0f}억"
        transitions["1→2"] = f"매출 {revStr}에서 영업이익률 {opMargin:.1f}% — 이 마진의 원천은?"

    # 2막→3막: 수익성 → 현금 전환
    ni = getattr(ratios, "netIncomeTTM", None)
    ocf = getattr(ratios, "operatingCashflowTTM", None)
    if ni and ocf:
        niStr = f"{ni / 1e12:.1f}조" if abs(ni) > 1e12 else f"{ni / 1e8:.0f}억"
        ocfStr = f"{ocf / 1e12:.1f}조" if abs(ocf) > 1e12 else f"{ocf / 1e8:.0f}억"
        ratio = ocf / ni * 100 if ni != 0 else 0
        # 한국어 조사: 받침 있으면 "이", 없으면 "가"
        lastChar = niStr[-1]
        hasBatchim = ord(lastChar) >= 0xAC00 and (ord(lastChar) - 0xAC00) % 28 != 0
        josa = "이" if hasBatchim else "가"
        transitions["2→3"] = (
            f"순이익 {niStr}{josa} 영업CF {ocfStr}로 전환 ({ratio:.0f}%) — 이익이 현금으로 뒷받침되는가?"
        )

    # 3막→4막: 현금 → 안정성
    fcf = getattr(ratios, "fcf", None) or getattr(ratios, "fcfTTM", None)
    ic = getattr(ratios, "interestCoverage", None)
    if fcf is not None and ic is not None:
        fcfStr = f"{fcf / 1e12:.1f}조" if abs(fcf) > 1e12 else f"{fcf / 1e8:.0f}억"
        transitions["3→4"] = f"FCF {fcfStr}, 이자보상 {ic:.1f}배 — 이 현금으로 부채를 감당할 수 있는가?"

    # 4막→5막: 안정성 → 자본배분
    nd = getattr(ratios, "netDebt", None)
    dr = getattr(ratios, "debtRatio", None)
    if nd is not None and dr is not None:
        status = "순현금" if nd < 0 else f"순차입금 {nd / 1e12:.1f}조"
        transitions["4→5"] = f"{status}, 부채비율 {dr:.0f}% — 안전한 자본 안에서 어떻게 배분하는가?"

    # 5막→6막: 자본배분 → 전망/가치
    roic = getattr(ratios, "roic", None)
    if roic is not None:
        transitions["5→6"] = f"ROIC {roic:.1f}% — 이 수익률이 지속되면 이 회사의 가치는?"

    return transitions


def buildCirculationSummary(threads: list[NarrativeThread]) -> str:
    """감지된 threads를 종합 서사로 합성."""
    if not threads:
        return ""

    criticals = [t for t in threads if t.severity == "critical"]
    warnings = [t for t in threads if t.severity == "warning"]
    positives = [t for t in threads if t.severity == "positive"]

    parts = []

    if criticals:
        parts.append("핵심 위험: " + " / ".join(t.title for t in criticals) + ".")

    if warnings:
        parts.append("주의 신호: " + " / ".join(t.title for t in warnings) + ".")

    if positives:
        parts.append("긍정 신호: " + " / ".join(t.title for t in positives) + ".")

    if not parts:
        return ""

    # 각 thread의 story 중 가장 심각한 것 1개 + 가장 긍정적인 것 1개 요약
    details = []
    if criticals:
        details.append(criticals[0].story)
    elif warnings:
        details.append(warnings[0].story)
    if positives:
        details.append(positives[0].story)

    summary = " ".join(parts)
    if details:
        summary += "\n" + "\n".join(details)

    return summary
