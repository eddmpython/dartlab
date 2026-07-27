"""Damodaran 3-Test — 모든 스토리는 세 시험을 통과해야 한다.

Aswath Damodaran (NYU Stern) "Narrative & Numbers" 프레임워크:
1. History Test  — 과거에 이 스토리를 산 기업이 있는가? 어떻게 됐나?
2. Experience Test — 같은 업종에서 이 문제를 겪은 전례가 있는가?
3. Common Sense Test — 경제학적으로 말이 되는가? (불변량 위반 체크)

story 보고서 끝에 3-test 결과를 부착하여 스토리의 신뢰도를 높인다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TestResult:
    """단일 테스트 결과."""

    name: str
    passed: bool
    detail: str


@dataclass
class DamodaranResult:
    """3-test 전체 결과."""

    historyTest: TestResult | None = None
    experienceTest: TestResult | None = None
    commonSenseTest: TestResult | None = None
    passCount: int = 0
    totalCount: int = 3

    @property
    def summary(self) -> str:
        """summary — TODO 한국어 동작 설명."""
        return f"Damodaran 3-test: {self.passCount}/{self.totalCount} 통과"


def damodaranTest(company, metrics: dict | None = None) -> DamodaranResult:
    """Company + 핵심 지표로 Damodaran 3-test 실행.

    Parameters
    ----------
    company : DartCompany | EdgarCompany
    metrics : dict, optional
        baseCase dict (scenarioSensitivity 결과 등). 없으면 내부 추출.

    Returns
    -------
    DamodaranResult
    """
    result = DamodaranResult()
    pass_count = 0

    # ── Test 1: History Test ──
    result.historyTest = _historyTest(company)
    if result.historyTest and result.historyTest.passed:
        pass_count += 1

    # ── Test 2: Experience Test ──
    result.experienceTest = _experienceTest(company)
    if result.experienceTest and result.experienceTest.passed:
        pass_count += 1

    # ── Test 3: Common Sense Test ──
    result.commonSenseTest = _commonSenseTest(company, metrics)
    if result.commonSenseTest and result.commonSenseTest.passed:
        pass_count += 1

    result.passCount = pass_count
    return result


def _historyTest(company) -> TestResult:
    """과거 유사 기업 사례 매칭 — historicalContext 활용 + scan peer.

    현재: scan 기반 peer 기업 중 유사 재무구조를 가진 top 3가 존재하는지.
    """
    try:
        from dartlab.scan.builders.kr.extended import calcPeerPosition

        peer = calcPeerPosition(company)
        if peer and peer.get("crossViews"):
            views = [cv["view"] for cv in peer["crossViews"]]
            return TestResult(
                name="History",
                passed=True,
                detail=f"유사 포지션 기업 확인됨: {', '.join(views[:2])} 유형에서 동종 사례 존재",
            )
        return TestResult(
            name="History",
            passed=False,
            detail="peer 비교 데이터 부족. scan 프리빌드 또는 collect 데이터 준비 후 재시도",
        )
    except (ImportError, AttributeError, ValueError):
        return TestResult(
            name="History",
            passed=False,
            detail="scan 데이터 접근 불가. scan 프리빌드 또는 collect 데이터 필요",
        )


def _experienceTest(company) -> TestResult:
    """같은 업종 기업 3개 이상이 비교 가능한지. 동업 전례 확인."""
    try:
        import importlib

        calcPeerPosition = importlib.import_module("dartlab.scan.builders.kr.extended").calcPeerPosition

        peer = calcPeerPosition(company)
        total = peer.get("total_stocks", 0) if peer else 0
        if total >= 50:
            return TestResult(
                name="Experience",
                passed=True,
                detail=f"동종업계 {total}개사 비교 가능 — 업종 내 전례 충분",
            )
        return TestResult(
            name="Experience",
            passed=False,
            detail=f"동종업계 {total}개사 — 비교 표본 부족 (50개 미만). scan 데이터 준비 후 재시도",
        )
    except (ImportError, AttributeError, ValueError):
        return TestResult(
            name="Experience",
            passed=False,
            detail="scan 데이터 접근 불가. scan 프리빌드 또는 collect 데이터 필요",
        )


# ── Common Sense Checks ──
# 회계 항등식과 위험 휴리스틱 20개. 항등식 위반은 데이터 오류를 뜻하고, 휴리스틱 위반은
# 사람이 들여다볼 자리를 가리킨다. 둘을 싸잡아 "불변량" 이라 부르면 후자의 무게를 과장한다.
#
# 각 검사는 자기가 읽는 지표를 함께 등록한다. 그 지표가 없으면 검사는 통과가 아니라
# 미적용이다. 예전에는 지표가 하나도 없어도 "20개 전부 통과" 가 찍혔다.

_INVARIANTS: list[tuple[str, tuple[str, ...], callable]] = []


def _register(desc: str, *keys: str):
    """검사를 설명과 필요한 지표 이름과 함께 등록한다."""

    def deco(fn):
        """검사 함수를 목록에 담고 그대로 돌려준다."""
        _INVARIANTS.append((desc, keys, fn))
        return fn

    return deco


@_register("영업이익 < 순이익 (비영업손익 확인 필요)", "operatingIncome", "netIncome")
def _invOpGtNi(m: dict) -> bool:
    opi = m.get("operatingIncome")
    ni = m.get("netIncome")
    # 예전에는 ROE 와 OPM 을 비교했다. 분모가 자기자본과 매출로 서로 달라서 OPM 3%,
    # ROE 15% 인 평범한 소매업이 위반으로 찍혔다. 설명대로 두 이익을 직접 비교한다.
    if opi is not None and ni is not None and opi > 0 and ni > opi:
        return False
    return True


@_register("ROE 음수 (자기자본 대비 손실)", "roe")
def _invNegativeRoe(m: dict) -> bool:
    roe = m.get("roe")
    if roe is not None and roe < 0:
        return False
    return True


@_register("부채비율 300% 초과 + 이자보상 2 미만 = 재무위기", "debtRatio", "interestCoverage")
def _invDistressCombo(m: dict) -> bool:
    dr = m.get("debtRatio")
    ic = m.get("interestCoverage")
    # `dr and ic` 로 쓰면 이자보상배율 0.0 에서 검사가 꺼진다. 영업이익으로 이자를 한 푼도
    # 못 갚는 상태가 바로 이 검사가 잡아야 할 최악인데, 하필 그때만 침묵했다.
    if dr is not None and ic is not None and dr > 300 and ic < 2:
        return False
    return True


@_register("OPM 50% 초과는 독과점 아니면 의심", "opm")
def _invExtremeMargin(m: dict) -> bool:
    opm = m.get("opm")
    if opm is not None and opm > 50:
        return False
    return True


@_register("FCF 음수", "fcf")
def _invNegativeFcf(m: dict) -> bool:
    fcf = m.get("fcf")
    if fcf is not None and fcf < 0:
        return False
    return True


# ── Phase 10 F2: 불변량 15개 추가 (총 20개) ──


@_register("FCF = OCF - Capex (계산 일관성)", "fcf", "ocf", "capex")
def _invFcfIdentity(m: dict) -> bool:
    fcf, ocf, capex = m.get("fcf"), m.get("ocf"), m.get("capex")
    if fcf is not None and ocf is not None and capex is not None:
        expected = ocf - capex
        if expected != 0 and abs(fcf - expected) / abs(expected) > 0.10:
            return False
    return True


@_register("영업이익 = 매출 - COGS - SGA (decomposition)", "revenue", "cogs", "sga", "operatingIncome")
def _invOperatingIncomeDecomp(m: dict) -> bool:
    rev, cogs, sga, opi = m.get("revenue"), m.get("cogs"), m.get("sga"), m.get("operatingIncome")
    if all(x is not None for x in (rev, cogs, sga, opi)):
        expected = rev - cogs - sga
        if expected != 0 and abs(opi - expected) / abs(expected) > 0.15:
            return False
    return True


@_register("ROIC = NOPAT / InvestedCapital", "roic", "nopat", "investedCapital")
def _invRoicIdentity(m: dict) -> bool:
    roic, nopat, ic = m.get("roic"), m.get("nopat"), m.get("investedCapital")
    if all(x is not None for x in (roic, nopat, ic)) and ic != 0:
        expected_pct = (nopat / ic) * 100
        if abs(roic - expected_pct) > 5:
            return False
    return True


@_register("ROE = NI / Equity", "roe", "netIncome", "equity")
def _invRoeIdentity(m: dict) -> bool:
    roe, ni, eq = m.get("roe"), m.get("netIncome"), m.get("equity")
    if all(x is not None for x in (roe, ni, eq)) and eq != 0:
        expected_pct = (ni / eq) * 100
        if abs(roe - expected_pct) > 5:
            return False
    return True


@_register("Interest Coverage = EBIT / Interest", "interestCoverage", "ebit", "interestExpense")
def _invInterestCoverage(m: dict) -> bool:
    ic, ebit, interest = m.get("interestCoverage"), m.get("ebit"), m.get("interestExpense")
    if all(x is not None for x in (ic, ebit, interest)) and interest != 0:
        expected = ebit / interest
        if abs(ic - expected) > 1:
            return False
    return True


@_register(
    "Working Capital = CurrentAssets - CurrentLiabilities", "workingCapital", "currentAssets", "currentLiabilities"
)
def _invWorkingCapital(m: dict) -> bool:
    wc, ca, cl = m.get("workingCapital"), m.get("currentAssets"), m.get("currentLiabilities")
    if all(x is not None for x in (wc, ca, cl)):
        expected = ca - cl
        if expected != 0 and abs(wc - expected) / abs(expected) > 0.10:
            return False
    return True


@_register("Debt/EBITDA 3배 초과 = leverage warning", "totalDebt", "ebitda")
def _invDebtEbitda(m: dict) -> bool:
    debt, ebitda = m.get("totalDebt"), m.get("ebitda")
    if debt is not None and ebitda is not None and ebitda > 0:
        if debt / ebitda > 3:
            return False
    return True


@_register("Free Float × 주가 = Market Cap (sanity)", "marketCap", "price", "sharesOutstanding")
def _invMarketCap(m: dict) -> bool:
    mc, px, shares = m.get("marketCap"), m.get("price"), m.get("sharesOutstanding")
    if all(x is not None for x in (mc, px, shares)):
        expected = px * shares
        if expected != 0 and abs(mc - expected) / abs(expected) > 0.20:
            return False
    return True


@_register("Goodwill / TotalAssets > 30% = M&A 집중 (goodwill impairment risk)", "goodwill", "totalAssets")
def _invGoodwillRatio(m: dict) -> bool:
    gw, ta = m.get("goodwill"), m.get("totalAssets")
    if gw is not None and ta is not None and ta > 0:
        if gw / ta > 0.30:
            return False
    return True


@_register("Tax Rate 통상 범위 (5~40%)", "effectiveTaxRate")
def _invTaxRate(m: dict) -> bool:
    tax_rate = m.get("effectiveTaxRate")
    if tax_rate is not None:
        if tax_rate < 0.05 or tax_rate > 0.40:
            return False
    return True


@_register("NI > 0 인데 OCF < 0 (accrual 경고. 이익품질)", "netIncome", "ocf")
def _invNiOcfBridge(m: dict) -> bool:
    ni, ocf = m.get("netIncome"), m.get("ocf")
    if ni is not None and ocf is not None and ni > 0 and ocf < 0:
        return False
    return True


@_register("CCC (DSO + DIO - DPO) 200일 초과", "ccc")
def _invCccReasonable(m: dict) -> bool:
    ccc = m.get("ccc")
    if ccc is not None and ccc > 200:  # 극단 case
        return False
    return True


@_register("매출채권회전 < 3회 (DSO > 120일) = 회수 부실", "dso")
def _invArTurnover(m: dict) -> bool:
    dso = m.get("dso")
    if dso is not None and dso > 120:
        return False
    return True


@_register("재고회전 < 2회 (DIO > 180일) = 재고 과다", "dio")
def _invInventoryTurnover(m: dict) -> bool:
    dio = m.get("dio")
    if dio is not None and dio > 180:
        return False
    return True


@_register("ROIC < WACC (가치 파괴)", "roic", "wacc")
def _invRoicWaccSpread(m: dict) -> bool:
    roic, wacc = m.get("roic"), m.get("wacc")
    if roic is not None and wacc is not None and roic < wacc:
        return False
    return True


def _commonSenseTest(company, metrics: dict | None) -> TestResult:
    """경제학적 불변량 위반 체크."""
    if metrics is None:
        try:
            from dartlab.analysis.financial.scenarioSensitivity import calcScenarioSensitivity

            ss = calcScenarioSensitivity(company)
            metrics = ss.get("baseCase", {}) if ss else {}
        except (ImportError, AttributeError, ValueError):
            metrics = {}

    if not metrics:
        # 검사할 자료가 없는 것은 통과가 아니다. 예전에는 여기서 passed=True 를 돌려줘서
        # 지표를 하나도 못 구한 회사가 Damodaran 3-test 한 칸을 공짜로 가져갔다.
        return TestResult(name="CommonSense", passed=False, detail="검증 대상 지표 없음 (데이터 부족)")

    violations: list[str] = []
    evaluated = 0
    errored = 0
    for desc, keys, check in _INVARIANTS:
        try:
            if any(metrics.get(key) is None for key in keys):
                continue
            passed = check(metrics)
        except (KeyError, TypeError, ValueError):
            # 예전에는 조용히 넘어가서, 스무 개가 전부 터져도 "20개 전부 통과" 가 찍혔다.
            errored += 1
            continue
        evaluated += 1
        if not passed:
            violations.append(desc)

    if not evaluated:
        return TestResult(
            name="CommonSense",
            passed=False,
            detail=f"검사 가능한 항목 없음 (지표 부족 {len(_INVARIANTS) - errored}개, 오류 {errored}개)",
        )
    if violations:
        return TestResult(
            name="CommonSense",
            passed=False,
            detail=f"{evaluated}개 중 {len(violations)}개 위반: {'; '.join(violations[:3])}",
        )
    skipped = len(_INVARIANTS) - evaluated
    detail = f"검사한 {evaluated}개 항목 전부 통과"
    if skipped:
        detail += f" (지표 부족 등으로 {skipped}개 미검사)"
    return TestResult(name="CommonSense", passed=True, detail=detail)
