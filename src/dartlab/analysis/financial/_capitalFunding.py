"""capital.py 헬퍼 — 자금 출처 + 플래그 분리.

calcFundingSources + calcCapitalFlags 본체.
"""

from __future__ import annotations

from dartlab.analysis.financial.accountSums import sumBorrowings
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId

_MAX_QUARTERS = 5
_MAX_YEARS = 8


def _quarterlyCols(*args, **kwargs):
    from dartlab.analysis.financial.capital import _quarterlyCols as _q

    return _q(*args, **kwargs)


def _getRatios(*args, **kwargs):
    from dartlab.analysis.financial.capital import _getRatios as _g

    return _g(*args, **kwargs)


def _calcRetainedPct(*args, **kwargs):
    from dartlab.analysis.financial.capital import _calcRetainedPct as _f

    return _f(*args, **kwargs)


def _calcFinDebtPct(*args, **kwargs):
    from dartlab.analysis.financial.capital import _calcFinDebtPct as _f

    return _f(*args, **kwargs)


def _calcNetDebtEbitda(*args, **kwargs):
    from dartlab.analysis.financial.capital import _calcNetDebtEbitda as _f

    return _f(*args, **kwargs)


def _calcImpliedBorrowingRate(*args, **kwargs):
    from dartlab.analysis.financial.capital import _calcImpliedBorrowingRate as _f

    return _f(*args, **kwargs)


def _fmtAmt(*args, **kwargs):
    from dartlab.analysis.financial.capital import _fmtAmt as _f

    return _f(*args, **kwargs)


def _latestAnnualVal(*args, **kwargs):
    from dartlab.analysis.financial.capital import _latestAnnualVal as _f

    return _f(*args, **kwargs)


def _sign(*args, **kwargs):
    from dartlab.analysis.financial.capital import _sign as _f

    return _f(*args, **kwargs)


def _classifyCfPattern(*args, **kwargs):
    from dartlab.analysis.financial.capital import _classifyCfPattern as _f

    return _f(*args, **kwargs)


def _isFinancialCompany(*args, **kwargs):
    from dartlab.analysis.financial.capital import _isFinancialCompany as _f

    return _f(*args, **kwargs)


def calcFundingSources(company, *, basePeriod: str | None = None) -> dict | None:
    """자금조달 4 원천 분해 (내부유보 + 외부주주 + 금융차입 + 영업조달).

    Capabilities:
        BS 의 자본 + 부채를 4 원천으로 분해 — 내부유보 (이익잉여금), 외부
        주주 (납입자본), 금융차입 (총차입금), 영업조달 (매입채무 + 미지급금
        등). 시계열로 비중 변화를 추적해 자본구조 변화 진단. analysis()
        의 자금조달 축 핵심 함수.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``latest`` (dict): 9 키 (totalAssets + 4 원천 × 절대값/비중)
            - ``history`` (list[dict]): 연도별 비중 시계열
            - ``diagnosis`` (str): 조달구조 한국어 진단

    Raises:
        없음.

    Example:
        >>> r = calcFundingSources(Company("005930"))
        >>> r["latest"]["retainedPct"], r["latest"]["finDebtPct"]
        (45, 15)  # 내부유보 45%, 금융차입 15% (안정적 자본구조)

    Guide:
        retainedPct > 40% = 내부 현금 우위 (자립 성장). finDebtPct < 30% =
        안정적 레버리지. paidInPct 큰 신규 IPO 회사 — 운영 안정화 후 retained
        증가 추세 확인. opFundingPct 30%+ = 매입채무 의존 (B2B 산업 특성).

    When:
        자본구조 변화·차입 의존도 추세 진단 시점.

    How:
        BS 자본·부채를 4 원천으로 분해 후 시계열 비중 + 한국어 diagnosis.

    SeeAlso:
        - ``calcDebtTimeline``: 차입금 시계열
        - ``calcCapitalOverview``: 자본구조 종합
        - ``analyzeHealth``: 재무건전성 (자금조달 결합)

    Requires:
        BS 시계열 (자산총계 + 자본총계 + 차입금 + 매입채무).

    AIContext:
        4 원천 비중 시계열 (history) 의 변화 방향 함께 노출 — retainedPct
        상승 추세 = 좋은 신호, finDebtPct 상승 = 차입 증가 (capex 또는
        부실 신호).

    LLM Specifications:
        AntiPatterns:
            - 단년도 비중만 인용 — 시계열 추세 (3~5 년) 함께 확인 필수.
            - paidInPct 큰 신규 IPO 를 "재무 불안" 으로 단정 — 운영 안정화
              기간 (3~5 년) 정상.
        OutputSchema:
            ``{latest: dict 9키, history: list[dict], diagnosis: str}``.
        Prerequisites:
            BS 시계열 + 자본/부채 standardAccounts.
        Freshness:
            최신 분기 + 5 년 시계열.
        Dataflow:
            BS → 자본총계 (retained + paidIn) + 부채총계 분해 (finDebt +
            opFunding) → 비중 계산 → diagnosis.
        TargetMarkets: KR (DART), US (EDGAR 표준 자본구조 동일).
    """
    accounts = [
        "자산총계",
        "자본총계",
        "이익잉여금",
        "미처분이익잉여금(결손금)",
        "자본금",
        "자본잉여금",
        "부채총계",
        "단기차입금",
        "장기차입금",
        "차입금단기",  # short_term_borrowings 한국어 변형
        "long_term_borrowings",  # 영문만 있는 회사 (한화오션)
        "short_term_borrowings",
        "차입부채",  # 통합 차입금 (SK하이닉스)
        "장기차입부채",  # noncurrent_borrowings (LG에솔)
        "유동성장기차입금",  # current_portion_of_longterm_borrowings
        "사채",
        "매입채무",
        "선수금",
        "계약부채",
        "선수수익",
    ]
    result = company.select("BS", accounts)
    parsed = toDictBySnakeId(result)
    if parsed is None:
        return None

    data, allPeriods = parsed
    taRow = data.get("total_assets")
    if taRow is None:
        return None

    from dartlab.core.utils.helpers import mergeRows

    reRow = mergeRows(data.get("retained_earnings"), data.get("unappropriated_retained_earnings_deficit"))
    pcRow = data.get("paidin_capital", {})
    csRow = data.get("capital_surplus", {})
    eqRow = data.get("total_stockholders_equity", {})
    liabRow = data.get("total_liabilities", {})
    apRow = data.get("trade_and_other_payables", {})
    advRow = data.get("advance_from_customers", {})
    clRow = data.get("contract_liabilities", {})
    diRow = data.get("deferred_income", {})

    yCols = annualColsFromPeriods(allPeriods, basePeriod, _MAX_YEARS)
    if not yCols:
        yCols = _quarterlyCols(allPeriods, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    latest = None

    for col in yCols:
        ta = taRow.get(col)
        if ta is None or ta <= 0:
            continue

        # 핵심 자본구조 항목은 모든 회사가 보유 — None = 미수집. 가짜 0 출력 회피 위해 skip.
        retained = reRow.get(col)
        equity = eqRow.get(col)
        liab = liabRow.get(col)
        if retained is None or equity is None or liab is None:
            continue

        # 합산 항목 (자본잉여금/자본금, 영업관련 부채) 의 개별 component 는 0 fallback OK
        # — 그 항목이 회사에 없을 수 있음 (선택적 항목)
        paidIn = (pcRow.get(col) or 0) + (csRow.get(col) or 0)
        # 차입금: 회사 키 패턴 무관 헬퍼 (분리/통합/언더스코어/noncurrent 변형 모두 처리)
        finDebt = sumBorrowings(data, col)
        opFunding = (apRow.get(col) or 0) + (advRow.get(col) or 0) + (clRow.get(col) or 0) + (diRow.get(col) or 0)

        otherEquity = max(0, equity - retained - paidIn)
        otherLiab = max(0, liab - finDebt - opFunding)

        entry = {
            "period": col,
            "retainedPct": retained / ta * 100,
            "paidInPct": paidIn / ta * 100,
            "finDebtPct": finDebt / ta * 100,
            "opFundingPct": opFunding / ta * 100,
            "otherLiabPct": otherLiab / ta * 100,
            "otherEquityPct": otherEquity / ta * 100,
        }
        history.append(entry)

        if latest is None:
            latest = {
                "totalAssets": ta,
                "retained": retained,
                "retainedPct": entry["retainedPct"],
                "paidIn": paidIn,
                "paidInPct": entry["paidInPct"],
                "finDebt": finDebt,
                "finDebtPct": entry["finDebtPct"],
                "opFunding": opFunding,
                "opFundingPct": entry["opFundingPct"],
                "otherLiab": otherLiab,
                "otherLiabPct": entry["otherLiabPct"],
                "otherEquity": otherEquity,
                "otherEquityPct": entry["otherEquityPct"],
            }

    if latest is None:
        return None

    # 진단: 내부유보 vs 금융차입 비중으로 자금조달 성격 판단
    rPct = latest["retainedPct"]
    fPct = latest["finDebtPct"]
    if rPct >= 50:
        diagnosis = "자기 힘으로 성장 — 이익잉여금이 자산의 절반 이상"
    elif rPct >= 30 and fPct < 30:
        diagnosis = "내부유보 중심 — 차입 의존도 낮음"
    elif fPct >= 40:
        diagnosis = "차입 의존 — 금융부채가 자산의 40% 이상"
    elif fPct >= rPct:
        diagnosis = "외부 조달 우위 — 금융차입이 내부유보를 초과"
    else:
        diagnosis = "균형 조달 — 내부유보와 외부 조달이 혼합"

    # 보충 지표: 순차입금/EBITDA, 암묵적 차입금리
    netDebtEbitda = _calcNetDebtEbitda(company, latest["finDebt"])
    impliedRate = _calcImpliedBorrowingRate(company, latest["finDebt"])

    result = {"latest": latest, "history": history, "diagnosis": diagnosis}
    if netDebtEbitda is not None:
        result["netDebtEbitda"] = netDebtEbitda
    if impliedRate is not None:
        result["impliedBorrowingRate"] = impliedRate

    # 비중 변화 방향 (금융차입 비중이 늘고 있는가)
    if len(history) >= 2:
        newest = history[0]["finDebtPct"]
        oldest = history[-1]["finDebtPct"]
        diff = newest - oldest
        if diff > 5:
            result["leverageTrend"] = (
                f"금융차입 비중 +{diff:.0f}pp 증가 ({history[-1]['period']}→{history[0]['period']})"
            )
        elif diff < -5:
            result["leverageTrend"] = (
                f"금융차입 비중 {diff:.0f}pp 감소 ({history[-1]['period']}→{history[0]['period']})"
            )

    # notes enrichment — 차입금 주석 (이자율, 만기, 담보 등)
    from dartlab.analysis.financial.companyContext import fetchNotesDetail

    notesDetail = fetchNotesDetail(company, ["borrowings"])
    if notesDetail:
        result["notesDetail"] = notesDetail

    return result


def calcCapitalFlags(company, *, basePeriod: str | None = None) -> list[tuple[str, str]]:
    """자금조달 관련 경고/기회 플래그.

    Capabilities:
        - 부채비율·이자보상·유동성·Altman/Piotroski 등 신호 플래그화.

    Returns
    -------
    list[tuple[str, str]]
        각 원소는 (플래그 텍스트, "warning" | "opportunity").

    Guide:
        금융업과 비금융업 임계 분리. 순현금/고 이자보상은 완화 어조.

    When:
        자금조달 축 종합 진단 후 사용자 노출 직전.

    How:
        ratios + BS 직접 계산 → 임계 비교 → 한국어 플래그 텍스트 생성.

    Requires:
        capital._getRatios 결과 + BS 부채/차입 항목.

    Raises:
        없음 — ratios 부재 시 빈 리스트.

    Example:
        >>> calcCapitalFlags(company)
        [('고부채 (부채비율 220%)', 'warning')]

    See Also:
        - calcFundingSources : 자금조달 4 원천.

    AIContext:
        warning 라벨은 정성 신호 — 즉시 위기 단정 금지, 맥락 함께.
    """
    flags: list[tuple[str, str]] = []

    ratios = _getRatios(company)
    if ratios is None:
        return flags

    isFinancial = _isFinancialCompany(company)

    dr = getattr(ratios, "debtRatio", None)
    if dr is not None:
        if isFinancial:
            # 금융업은 예수부채로 부채비율이 구조적으로 높음
            if dr > 2000:
                flags.append((f"금융업 부채비율 {dr:.0f}% — 과다", "warning"))
        elif dr > 200:
            flags.append((f"고부채 (부채비율 {dr:.0f}%)", "warning"))

    ic = getattr(ratios, "interestCoverage", None)
    if not isFinancial and ic is not None and ic < 3:
        severity = "심각" if ic < 1.5 else "주의"
        flags.append((f"이자보상 {severity} ({ic:.1f}배)", "warning"))

    cr = getattr(ratios, "currentRatio", None)
    nd = getattr(ratios, "netDebt", None)
    isNetCash = nd is not None and nd < 0
    if not isFinancial and cr is not None and cr < 100:
        if isNetCash:
            # 순현금이면 유동비율 낮아도 실질 유동성 위험 낮음 (IFRS16 리스부채 등)
            flags.append((f"유동비율 주의 ({cr:.0f}%) — 순현금이므로 실질 위험 낮음", "warning"))
        elif ic is not None and ic > 5:
            # 이자보상배율 양호하면 실질 유동성 위험 낮음
            flags.append((f"유동비율 주의 ({cr:.0f}%) — 이자보상 {ic:.0f}배로 양호", "warning"))
        else:
            flags.append((f"유동성 위기 (유동비율 {cr:.0f}%)", "warning"))

    z = getattr(ratios, "altmanZScore", None)
    zpp = getattr(ratios, "altmanZppScore", None)
    if not isFinancial and zpp is not None:
        if zpp < 1.1:
            flags.append((f"Altman Z'' 부실 경계 ({zpp:.2f})", "warning"))
    elif not isFinancial and z is not None and z < 1.81:
        flags.append((f"Altman Z 부실 경계 ({z:.2f})", "warning"))

    pf = getattr(ratios, "piotroskiFScore", None)
    if pf is not None and pf < 3:
        flags.append((f"Piotroski F 재무 약화 ({pf}/9)", "warning"))

    # 금융부채 비중 (BS에서 직접 계산)
    flagResult = company.select(
        "BS",
        [
            "부채총계",
            "단기차입금",
            "장기차입금",
            "차입부채",
            "사채",
            "자본총계",
            "이익잉여금",
            "미처분이익잉여금(결손금)",
        ],
    )
    flagParsed = toDictBySnakeId(flagResult)
    if flagParsed is not None and "total_liabilities" in flagParsed[0]:
        data = flagParsed[0]
        liabRow = data["total_liabilities"]
        stbRow = data.get("shortterm_borrowings")
        ltbRow = data.get("longterm_borrowings")
        unifiedBorrowRow = data.get("borrowings")  # 통합 차입금 fallback
        bondRow = data.get("debentures")
        # stb/ltb 둘 다 None → unifiedBorrow 를 stb 위치로
        if stbRow is None and ltbRow is None and unifiedBorrowRow is not None:
            stbRow = unifiedBorrowRow
        finDebtPct = _calcFinDebtPct(liabRow, stbRow, ltbRow, bondRow)
        if finDebtPct is not None and finDebtPct > 50:
            flags.append((f"금융부채 비중 {finDebtPct:.0f}% — 이자 부담 부채 높음", "warning"))

        equityRow = data.get("total_stockholders_equity")
        from dartlab.core.utils.helpers import mergeRows

        retainedRow = mergeRows(data.get("retained_earnings"), data.get("unappropriated_retained_earnings_deficit"))
        retainedPct = _calcRetainedPct(equityRow, retainedRow)
        if retainedPct is not None and retainedPct > 70:
            flags.append((f"내부유보 비중 {retainedPct:.0f}% — 자기 힘으로 성장", "opportunity"))

    nd = getattr(ratios, "netDebt", None)
    if nd is not None and nd < 0:
        flags.append(("순현금 상태", "opportunity"))

    if ic is not None and ic > 10:
        flags.append((f"이자보상 우수 ({ic:.0f}배)", "opportunity"))

    if pf is not None and pf >= 7:
        flags.append((f"Piotroski F 재무 건전 ({pf}/9)", "opportunity"))

    return flags
