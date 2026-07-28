"""시나리오 시뮬레이터 — 분기별 모니터링 + 행동 추천.

예측하지 않는다. 시나리오를 설정하고, 분기마다 실적과 비교하여
어떤 경로 위에 있는지 판정하고, 행동을 추천한다.

흐름::

    1. createSimulation(company, "반도체 회복", revenueGrowth=15)
       → 3개 시나리오(bull/base/bear) × ProForma IS/BS/CF
       → 과거 계절성으로 Q1~Q4 분기 목표 분해
       → 시나리오별 DCF 적정가치

    2. judgeQuarter(sim, "2025Q1", revenue, operatingIncome)
       → 매출 + 영업이익 이중 판정
       → 연간 착지 재예측
       → 행동 추천

검증: experiments/107_scenarioSim (001~008, 8개 기업 사후 검증 완료).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from dartlab.analysis.financial.proforma import (
    ProFormaResult,
    ProFormaYear,
    buildProforma,
    extractHistoricalRatios,
)
from dartlab.core.accounts import reverseKoreanLabels
from dartlab.core.utils.helpers import parseNumStr

# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass
class QuarterJudgment:
    """한 분기 실적 판정 결과."""

    quarter: str
    actualRevenue: float
    actualOI: float
    targetRevBase: float
    targetOIBase: float
    revDeviation: float  # (actual - base) / base × 100
    oiDeviation: float
    revPath: str  # on_track | outperform | outperform_mild | underperform | underperform_severe
    oiPath: str
    action: str  # 보유 | 비중확대 검토 | 비중축소 검토 | 시나리오 재설정
    reason: str
    reforecastRevenue: float  # 연간 착지 재예측
    reforecastOI: float


@dataclass
class ScenarioSimulation:
    """시나리오 시뮬레이션 세션."""

    stockCode: str
    companyName: str
    scenarioName: str
    baseYear: str
    targetYear: str
    createdAt: str = field(default_factory=lambda: datetime.now().isoformat())

    # 시나리오 가정
    revenueGrowthPath: list[float] = field(default_factory=list)
    marginBlendWeight: float = 0.5

    # ProForma 결과 (bull/base/bear)
    proformaResults: dict[str, ProFormaResult] = field(default_factory=dict)

    # 분기 목표
    quarterlyRevTargets: dict[str, list[float]] = field(default_factory=dict)
    quarterlyOITargets: dict[str, list[float]] = field(default_factory=dict)

    # DCF 적정가치
    dcfPerShare: dict[str, int] = field(default_factory=dict)

    # 판정 이력
    judgments: list[QuarterJudgment] = field(default_factory=list)

    # 계절성 비중
    revSeasonality: list[float] = field(default_factory=list)
    oiSeasonality: list[float] = field(default_factory=list)


# ══════════════════════════════════════
# 내부 유틸
# ══════════════════════════════════════


def _labelKeys(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()

    raw = str(value).strip()
    if not raw:
        return ()

    base = raw.split("(")[0].split("（")[0].strip()
    keys = [raw]
    if base and base != raw:
        keys.append(base)

    for key in list(keys):
        compact = "".join(key.split()).lower()
        if compact and compact not in keys:
            keys.append(compact)

    return tuple(keys)


def _rowMatchesSnakeId(row: dict[str, Any], snakeId: str) -> bool:
    if str(row.get("snakeId") or "").strip() == snakeId:
        return True

    reverseLabels = reverseKoreanLabels()
    for col in ("account", "label", "항목", "accountNm"):
        for key in _labelKeys(row.get(col)):
            if key == snakeId or reverseLabels.get(key) == snakeId:
                return True
    return False


def _numericValue(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, int | float):
        return float(value)

    parsed = parseNumStr(str(value))
    return float(parsed) if parsed is not None else 0.0


def quarterlyValues(isDf: Any, snakeId: str, year: str) -> dict[str, float]:
    """분기 IS 패널에서 특정 연도의 발표된 분기 값을 {"YYYYQn": 값} 으로 추출.

    Capabilities:
        - snakeId(계정 정본 키) 행 매칭 + 해당 연도 Q1~Q4 중 존재하는 열만 수집
        - 미발표 분기는 키 자체가 없음 (0 채움 없음: 미발표와 0 을 구분)

    Args:
        isDf: ``company.panel("is")`` 분기 wide DataFrame (열 = "2026Q1" 형).
        snakeId: 계정 정본 키 ("sales" · "operating_profit" 등).
        year: 대상 연도 문자열 ("2026").

    Returns:
        {"2026Q1": 1000.0, ...} 발표된 분기만. 행 미매칭·isDf None 이면 빈 dict.

    Guide:
        연 4개가 다 필요하면 값 개수를 호출자가 검사한다 (계절성 계산은 4개 강제).

    When:
        분기 실적 1개 단위가 필요할 때 (기대치 격자 분기 채점 등).

    How:
        _rowMatchesSnakeId 행 탐색 -> f"{year}Q{q}" 열 존재 검사 -> _numericValue 정규화.

    Requires:
        panel("is") 의 분기 wide 형태 (행 = 계정, 열 = 분기).

    Raises:
        없음 (미매칭은 빈 dict).

    Example:
        >>> quarterlyValues(None, "sales", "2026")
        {}

    See Also:
        - computeSeasonality : 이 값들로 Q1~Q4 비중 평균 계산

    AIContext:
        분기 실적 인용 시 "발표분만" 임을 함께 언급.
    """
    if isDf is None:
        return {}

    row = next((r for r in isDf.iter_rows(named=True) if _rowMatchesSnakeId(r, snakeId)), None)
    if row is None:
        return {}

    vals: dict[str, float] = {}
    for q in range(1, 5):
        col = f"{year}Q{q}"
        if col in row:
            vals[col] = _numericValue(row.get(col))
    return vals


def _quarterlyValues(isDf: Any, snakeId: str, year: str) -> list[float]:
    """IS DataFrame에서 특정 연도의 Q1~Q4 값 추출 (4개 완비 시에만, 계절성용)."""
    vals = quarterlyValues(isDf, snakeId, year)
    ordered = [vals[f"{year}Q{q}"] for q in range(1, 5) if f"{year}Q{q}" in vals]
    return ordered if len(ordered) == 4 else []


def seasonalSharesFromYearQuarters(byYear: dict[str, list[float]]) -> list[float]:
    """연도별 [Q1,Q2,Q3,Q4] 값 묶음에서 Q1~Q4 비중 평균(합=1)을 계산하는 계절성 코어.

    Capabilities:
        - 연도별 |값| 비중 -> 연도 평균 -> 재정규화 (음수 분기는 절대값 비중)
        - 4개 미완비 연도는 표본 제외 (부분 연도 왜곡 차단)

    Args:
        byYear: {"2024": [q1, q2, q3, q4], ...}. 값 4개 미만인 연도는 무시.

    Returns:
        [w1, w2, w3, w4] 합 1.0. 유효 표본 0이면 균등 [0.25]*4.

    Guide:
        데이터 소스 무관 공용 코어: panel("is") 경로는 computeSeasonality 가,
        _buildFinanceSeries(freq="Q") 경로는 기대치 격자가 각자 값을 모아 여기로 위임한다.

    When:
        분기 값 묶음을 이미 손에 들고 비중만 필요할 때.

    How:
        연도별 절대값 비중 -> 산술평균 -> 합 1 재정규화.

    Requires:
        없음 (순수 함수).

    Raises:
        없음.

    Example:
        >>> seasonalSharesFromYearQuarters({"2024": [1.0, 2.0, 3.0, 4.0]})
        [0.1, 0.2, 0.3, 0.4]

    See Also:
        - computeSeasonality : panel("is") 어댑터 (이 코어에 위임)

    AIContext:
        균등 비중 결과는 "계절성 표본 없음" 신호.
    """
    all_w: list[list[float]] = []
    for _, qv in sorted(byYear.items()):
        if len(qv) == 4:
            total = sum(abs(v) for v in qv)
            if total > 0:
                all_w.append([abs(v) / total for v in qv])
    if not all_w:
        return [0.25, 0.25, 0.25, 0.25]
    n = len(all_w)
    avg = [sum(w[q] for w in all_w) / n for q in range(4)]
    s = sum(avg)
    return [w / s for w in avg] if s > 0 else [0.25] * 4


def computeSeasonality(isDf: Any, snakeId: str, years: list[str]) -> list[float]:
    """과거 N년 분기 실적으로 Q1~Q4 비중 평균(합=1)을 계산.

    Capabilities:
        - 연도별 |값| 비중 -> 연도 평균 -> 재정규화 (음수 분기는 절대값 비중)
        - 4분기 완비 연도만 표본 채택 (부분 연도 왜곡 차단)

    Args:
        isDf: ``company.panel("is")`` 분기 wide DataFrame.
        snakeId: 계정 정본 키 ("sales" · "operating_profit").
        years: 표본 연도 리스트 (예 ["2023", "2024", "2025"]).

    Returns:
        [w1, w2, w3, w4] 합 1.0. 표본 0이면 균등 [0.25]*4 (호출자가 fallback 여부 판단).

    Guide:
        연간 값 x 비중 = 분기 목표 분해. 시나리오 경로를 깨지 않는 결정적 분해다.

    When:
        연간 추정을 분기 목표·분기 기대치로 나눌 때 (scenarioSim · 기대치 격자 공용).

    How:
        _quarterlyValues 로 4분기 완비 연도 수집 -> 절대값 비중 평균 -> 합 1 재정규화.

    Requires:
        panel("is") 분기 열. 상장 3년 미만이면 표본이 얇아진다.

    Raises:
        없음 (표본 부재는 균등 비중 반환).

    Example:
        >>> computeSeasonality(None, "sales", ["2024"])
        [0.25, 0.25, 0.25, 0.25]

    See Also:
        - quarterlyValues : 단일 연도 분기 값 추출
        - createSimulation : 동일 비중으로 분기 목표 분해

    AIContext:
        균등 비중 결과는 "계절성 표본 없음" 신호로 해석해 인용.
    """
    return seasonalSharesFromYearQuarters({y: _quarterlyValues(isDf, snakeId, y) for y in years})


def _blendWeight(baseOpMargin: float) -> float:
    """기준연도 영업이익률 → 과거 비율 가중치.

    저마진/적자 기업일수록 과거 비율(정상 수준)에 더 의존.
    """
    if baseOpMargin < 2.0:
        return 0.8
    elif baseOpMargin < 5.0:
        return 0.7
    else:
        return 0.5


def _judgePath(actual: float, bull: float, base: float, bear: float, tolerance: float = 0.05) -> str:
    """실적 vs 시나리오 목표 → 경로 판정."""
    if base == 0:
        return "unknown"
    dev = (actual - base) / abs(base)
    if abs(dev) <= tolerance:
        return "on_track"
    elif actual >= bull:
        return "outperform"
    elif actual <= bear:
        return "underperform_severe"
    elif dev > 0:
        return "outperform_mild"
    else:
        return "underperform"


def _decideAction(revPath: str, oiPath: str, history: list[QuarterJudgment]) -> tuple[str, str]:
    """매출 + 영업이익 이중 판정 → 행동 추천."""
    severity = {
        "outperform": 2,
        "outperform_mild": 1,
        "on_track": 0,
        "underperform": -1,
        "underperform_severe": -2,
        "unknown": 0,
    }
    combined = (severity.get(revPath, 0) + severity.get(oiPath, 0)) / 2

    prevScores = []
    for h in history[-2:]:
        ps = (severity.get(h.revPath, 0) + severity.get(h.oiPath, 0)) / 2
        prevScores.append(ps)
    consecutiveNeg = all(s < 0 for s in prevScores) if prevScores else False

    if combined >= 1.5:
        return "비중확대 검토", "매출+이익 모두 Bull 이상"
    elif combined >= 0.5:
        if prevScores and prevScores[-1] >= 0.5:
            return "비중확대 검토", "2분기 연속 상회"
        return "보유 (긍정)", "상회 관찰 중"
    elif combined >= -0.5:
        return "보유", "시나리오 경로 내"
    elif combined >= -1.5:
        if consecutiveNeg:
            return "비중축소 검토", "2분기 연속 하회"
        if oiPath == "underperform_severe" and "underperform" not in revPath:
            return "비중축소 검토", "매출은 괜찮으나 마진 붕괴"
        return "보유 (경계)", "1분기 하회, 추세 확인 필요"
    else:
        return "비중축소 검토", "Bear 시나리오 이탈"


def _scenarioDCF(
    projections: list[ProFormaYear],
    waccPct: float,
    netDebt: float = 0,
    shares: int = 1,
    terminalGrowth: float = 0.02,
) -> int:
    """3년 ProForma FCF → DCF 적정가 (per share)."""
    wacc = waccPct / 100
    if wacc <= terminalGrowth:
        wacc = terminalGrowth + 0.05

    pvFcf = sum(p.fcf / (1 + wacc) ** (i + 1) for i, p in enumerate(projections))

    lastP = projections[-1]
    normalizedFcf = lastP.ocf - lastP.depreciation
    if normalizedFcf <= 0:
        normalizedFcf = lastP.ocf * 0.3

    tv = normalizedFcf * (1 + terminalGrowth) / (wacc - terminalGrowth)
    pvTv = tv / (1 + wacc) ** len(projections)

    ev = pvFcf + pvTv
    equityValue = ev - netDebt
    return int(equityValue / shares) if shares > 0 else 0


# ══════════════════════════════════════
# 공개 API
# ══════════════════════════════════════


def createSimulation(
    company: Any,
    scenarioName: str,
    revenueGrowth: float | list[float],
    *,
    baseYear: str = "2024",
    targetYear: str = "2025",
    bullSpread: float = 1.5,
    bearSpread: float = 0.3,
    overrides: dict[str, float] | None = None,
    shares: int | None = None,
) -> ScenarioSimulation:
    """시나리오 시뮬레이션 생성.

    Capabilities:
        - Bull/Base/Bear 3 ProForma + 분기 매출/영업이익 목표 산출
        - 마진 블렌딩 + 계절성 분해 + 시나리오별 DCF 가치

    Args:
        company: Company 객체.
        scenarioName: 사용자 지정 이름 ("반도체 회복" 등).
        revenueGrowth: 연간 매출 성장률 (%). float이면 3년 수렴 자동 생성.
        baseYear: 기준 연도 (이 해까지의 데이터로 시나리오 설정).
        targetYear: 검증 대상 연도.
        bullSpread: Bull 성장률 = base × bullSpread.
        bearSpread: Bear 성장률 = base × bearSpread.
        overrides: ProForma 비율 오버라이드.
        shares: 발행주식수 (DCF per share 계산용).

    Returns:
        ScenarioSimulation — 3개 시나리오 ProForma + 분기 목표 + DCF.

    Guide:
        baseYear 시점 데이터 컷오프 → 3 시나리오 ProForma → 분기 목표 분배.

    When:
        분기별 실적 트래킹용 ProForma 목표가 필요할 때.

    How:
        buildProforma 3 회 (bull/base/bear) + 계절성 가중치로 분기 목표 분해.

    Requires:
        company 의 _buildFinanceSeries / panel("IS"). baseYear 데이터 있어야 함.

    Raises:
        ValueError : baseYear 데이터로 ProForma 생성 실패 시.

    Example:
        >>> sim = createSimulation(company, "반도체 회복", 10.0)
        >>> "base" in sim.proformaResults
        True

    See Also:
        - judgeQuarter : 분기 판정
        - buildProforma : ProForma 빌더

    AIContext:
        AI 답변 시 분기별 목표 vs 실적 트래킹 근거로 인용.
    """
    # 성장률 경로 생성
    if isinstance(revenueGrowth, (int, float)):
        g = float(revenueGrowth)
        growthPath = [g, g * 0.7, g * 0.5]  # 3년 수렴
    else:
        growthPath = list(revenueGrowth)

    # series 추출 + 시간 필터
    ts = company._buildFinanceSeries(freq="Q")
    fullSeries = ts[0] if isinstance(ts, tuple) else ts
    periods = ts[1] if isinstance(ts, tuple) else []

    cutoff = f"{baseYear}-Q4"
    cutIdx = periods.index(cutoff) + 1 if cutoff in periods else len(periods)
    series = {stmt: {k: v[:cutIdx] for k, v in fullSeries[stmt].items()} for stmt in ["IS", "BS", "CF"]}

    # 과거 비율 + 기준연도 비율
    ratios = extractHistoricalRatios(series)
    isDf = company.panel("is")  # show 은퇴 → panel native IS

    rev_base = sum(_quarterlyValues(isDf, "sales", baseYear))
    gp_base = sum(_quarterlyValues(isDf, "gross_profit", baseYear))
    oi_base = sum(_quarterlyValues(isDf, "operating_profit", baseYear))

    baseGM = gp_base / rev_base * 100 if rev_base else ratios.gross_margin
    baseOpMargin = oi_base / rev_base * 100 if rev_base else 0

    # GM이 0인 경우 (서비스업 등 매출총이익 미보고) → 과거 비율 전적 의존
    if baseGM < 1.0 and ratios.gross_margin > 5.0:
        baseGM = ratios.gross_margin

    # 마진 블렌딩 가중치
    hw = _blendWeight(baseOpMargin)
    blendedGM = baseGM * (1 - hw) + ratios.gross_margin * hw

    # 3개 시나리오 ProForma
    scenarioDefs = [
        ("bull", [g * bullSpread if g > 0 else g * (1 / bullSpread) for g in growthPath], blendedGM + 2),
        ("base", growthPath, blendedGM),
        ("bear", [g * bearSpread if g > 0 else g * (1 / bearSpread) for g in growthPath], blendedGM - 2),
    ]

    pfResults: dict[str, ProFormaResult] = {}
    for scName, path, gm in scenarioDefs:
        combinedOverrides = {"gross_margin": gm}
        if overrides:
            combinedOverrides.update(overrides)
        try:
            pf = buildProforma(
                series,
                revenueGrowthPath=path,
                scenarioName=scName,
                shares=shares,
                overrides=combinedOverrides,
            )
            if pf.projections:
                pfResults[scName] = pf
        except (KeyError, ValueError, ZeroDivisionError, TypeError):
            pass

    if "base" not in pfResults:
        msg = f"{baseYear} 데이터로 ProForma 생성 실패"
        raise ValueError(msg)

    # 계절성 분해
    seasonYears = [str(int(baseYear) - i) for i in range(3) if int(baseYear) - i >= 2019]
    revW = computeSeasonality(isDf, "sales", seasonYears)
    oiW = computeSeasonality(isDf, "operating_profit", seasonYears)

    # 분기 목표
    qRevTargets: dict[str, list[float]] = {}
    qOiTargets: dict[str, list[float]] = {}
    for sc, pf in pfResults.items():
        p = pf.projections[0]
        qRevTargets[sc] = [p.revenue * w for w in revW]
        qOiTargets[sc] = [p.operating_income * w for w in oiW]

    # DCF
    dcfValues: dict[str, int] = {}
    if shares and shares > 0:
        for sc, pf in pfResults.items():
            p1 = pf.projections[0]
            netDebt = (p1.short_term_debt + p1.long_term_debt) - p1.cash
            dcfValues[sc] = _scenarioDCF(pf.projections, pf.wacc, netDebt, shares)

    sim = ScenarioSimulation(
        stockCode=company.stockCode,
        companyName=getattr(company, "corpName", None) or company.stockCode,
        scenarioName=scenarioName,
        baseYear=baseYear,
        targetYear=targetYear,
        revenueGrowthPath=growthPath,
        marginBlendWeight=hw,
        proformaResults=pfResults,
        quarterlyRevTargets=qRevTargets,
        quarterlyOITargets=qOiTargets,
        dcfPerShare=dcfValues,
        revSeasonality=revW,
        oiSeasonality=oiW,
    )

    return sim


def judgeQuarter(
    simulation: ScenarioSimulation,
    quarter: str,
    actualRevenue: float,
    actualOI: float,
) -> QuarterJudgment:
    """분기 실적 판정.

    Capabilities:
        - 분기 실적이 어느 시나리오에 부합하는지 자동 판정
        - 시나리오 가중 재예측 + 행동 권고 동행

    Args:
        simulation: createSimulation()으로 생성한 시뮬레이션.
        quarter: 분기 식별자 ("2025Q1").
        actualRevenue: 실제 매출.
        actualOI: 실제 영업이익.

    Returns:
        QuarterJudgment — 판정 + 행동 + 재예측.

    Guide:
        실적 발표 직후 호출해 simulation 의 시나리오 가중을 갱신한다.

    When:
        분기 실적이 발표되어 시나리오 적중도를 평가할 때.

    How:
        quarter 의 Q-index 추출 → bull/base/bear 목표 비교 → 판정 dataclass 반환.

    Requires:
        createSimulation 으로 생성된 ScenarioSimulation.

    Raises:
        ValueError : quarter 형식 오류 시.
        IndexError : qIdx 범위 초과 시.

    Example:
        >>> j = judgeQuarter(sim, "2025Q1", 1e12, 1e11)
        >>> j is not None
        True

    See Also:
        - createSimulation : 사전 단계
        - buildProforma : ProForma 빌더

    AIContext:
        AI 답변 시 "X 분기 실적은 Y 시나리오 부합" 판정 인용.
    """
    qIdx = int(quarter[-1]) - 1  # Q1=0, Q2=1, ...

    # 목표값
    bullRev = simulation.quarterlyRevTargets.get("bull", [0] * 4)[qIdx]
    baseRev = simulation.quarterlyRevTargets["base"][qIdx]
    bearRev = simulation.quarterlyRevTargets.get("bear", [0] * 4)[qIdx]

    bullOI = simulation.quarterlyOITargets.get("bull", [0] * 4)[qIdx]
    baseOI = simulation.quarterlyOITargets["base"][qIdx]
    bearOI = simulation.quarterlyOITargets.get("bear", [0] * 4)[qIdx]

    # 판정
    revPath = _judgePath(actualRevenue, bullRev, baseRev, bearRev)
    oiPath = _judgePath(actualOI, bullOI, baseOI, bearOI)

    revDev = (actualRevenue - baseRev) / abs(baseRev) * 100 if baseRev else 0
    oiDev = (actualOI - baseOI) / abs(baseOI) * 100 if baseOI else 0

    # 행동
    action, reason = _decideAction(revPath, oiPath, simulation.judgments)

    # 재예측 (단순: YTD 실적 + 남은 분기 원래 목표)
    allActualsRev = [j.actualRevenue for j in simulation.judgments] + [actualRevenue]
    allActualsOI = [j.actualOI for j in simulation.judgments] + [actualOI]
    remainRevTargets = simulation.quarterlyRevTargets["base"][qIdx + 1 :]
    remainOITargets = simulation.quarterlyOITargets["base"][qIdx + 1 :]
    reforecastRev = sum(allActualsRev) + sum(remainRevTargets)
    reforecastOI = sum(allActualsOI) + sum(remainOITargets)

    judgment = QuarterJudgment(
        quarter=quarter,
        actualRevenue=actualRevenue,
        actualOI=actualOI,
        targetRevBase=baseRev,
        targetOIBase=baseOI,
        revDeviation=round(revDev, 1),
        oiDeviation=round(oiDev, 1),
        revPath=revPath,
        oiPath=oiPath,
        action=action,
        reason=reason,
        reforecastRevenue=reforecastRev,
        reforecastOI=reforecastOI,
    )

    simulation.judgments.append(judgment)
    return judgment
