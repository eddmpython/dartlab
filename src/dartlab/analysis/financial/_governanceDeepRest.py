"""governance.py 깊이 분석. CEO 교체 + 특수관계자 + 법적 이벤트.

_governanceDeep.py 분할 추가: calcCEOTurnover · calcRelatedPartyIntensity ·
calcLegalEventRisk 3 calc 약 445 줄. governance.py · _governanceDeep.py 의
facade 책임 (소유/이사회/감사의견/플래그/오너집중도) 유지.

BC: governance 모듈에서 3 calc 모두 import 가능 (re-export).
헬퍼 lazy import: _governanceDeep.py 의 _loadExecutiveDocs · _loadSanction ·
_loadContingentLiability · _loadRelatedPartyTx 등을 함수 내부 import.
"""

from __future__ import annotations

import logging

from dartlab.core.memory import memoizedCalc
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.core.utils.helpers import MAX_RATIO_YEARS, annualColsFromPeriods, toDictBySnakeId

_log = logging.getLogger(__name__)

CEO_TURNOVER_WINDOW_YEARS = 5
RELATED_PARTY_PARSER_UNIT = 1_000_000
LEGAL_EVENT_WINDOW_YEARS = 3


@memoizedCalc
def calcCEOTurnover(company, *, basePeriod: str | None = None) -> dict | None:
    """대표이사 교체. 최근 5년 교체 건수·평균 재임·현 CEO.

    사업보고서 「임원의 현황」 섹션 개인별 테이블에서 "대표이사" 담당업무
    문자열로 CEO 식별, 연도별 CEO 이름 집합 변동을 교체 이벤트로 카운트한다.
    MSCI Board refreshment 와 SSRN CEO tenure inverted-U 이론(취임 3년 이내
    고위험) 에 대응하는 축.

    Capabilities:
        - 5년 윈도우 CEO 이름 집합 변동을 교체 횟수와 재임으로 환산.

    When:
        지배구조 리스크 점검, 경영진 안정성 평가 시점.

    How:
        executive docs 개인별 테이블 → isCeo 필터 → 연도별 집합 diff.

    Requires:
        DART 사업보고서 임원의 현황 파서 결과 (_loadExecutiveDocs).

    AIContext:
        turnoverCount 단독으로 경영 위기 단정 금지. 재임·맥락 함께.

    Parameters
    ----------
    company : Company
        분석 대상 기업 (DART).
    basePeriod : str, optional
        기준 기간. 현재 구현에서는 참고만. 최근 5년 시계열 반환.

    Returns
    -------
    dict | None
        None : executive docs 파서 데이터 없음 또는 DART 외 provider.
        windowYears : int. 집계 윈도우 (년). 상수 5.
        turnoverCount : int. 윈도우 내 CEO 교체 건수 (건). 전기에 없던
            새 CEO가 등장하거나 전기 CEO가 사라지면 1로 카운트한다.
        currentCeos : list[str]. 최근 연도 대표이사 이름.
        lastChangeYear : int | None. 마지막 교체가 감지된 연도.
        avgTenureYears : float | None. 시계열에서 관찰된 평균 재임 (년).
            한 CEO의 첫·마지막 출현 연도 차이 + 1 의 평균.
        history : list[dict]. 연도별 스냅샷
            year : int. 연도
            ceos : list[str]. 해당 연도 대표이사 이름
            added : list[str]. 전기 대비 새로 등장
            removed : list[str]. 전기 대비 빠진 이름

    Raises
    ------
    없음. 데이터 없음은 None 반환.

    Examples
    --------
    >>> c = dartlab.Company("005930")
    >>> c.analysis("지배구조")["ceoTurnover"]

    Notes
    -----
    - CEO 식별은 임원 표의 "대표이사" / "CEO" 문자열 매칭 기반. 표기가 다른
      케이스(예: "각자 대표집행임원")는 파서 키워드에 포함되지 않으면 놓칠 수 있다.
    - 첫 연도는 비교 기준이 없어 교체 판정에서 제외된다.
    - 공동대표 체제에서는 동일 연도에 여러 이름이 등장하므로 `currentCeos`
      도 리스트로 반환한다.

    Guide
    -----
    `turnoverCount >= 2` 이면 5년간 경영진 불안정 신호. `avgTenureYears < 3`
    은 SSRN 연구의 bad-news hoarding 구간으로 crash risk 상승 경고.

    See Also
    --------
    calcGovernanceFlags : 교체 빈도를 warning 플래그로 소비.
    calcBoardComposition : 이사회 구성 (최신 스냅샷).
    """
    import polars as pl

    from dartlab.analysis.financial._governanceDeep import _loadExecutiveDocs

    result = _loadExecutiveDocs(company)
    if result is None or result.individualDf is None or result.individualDf.is_empty():
        return None

    df = result.individualDf.filter(pl.col("isCeo"))
    if df.is_empty():
        return None

    years = sorted(df["year"].unique().to_list())
    recent = years[-CEO_TURNOVER_WINDOW_YEARS:]
    if not recent:
        return None

    ceosByYear: dict[int, set[str]] = {}
    for y in recent:
        names = [n for n in df.filter(pl.col("year") == y)["name"].to_list() if n]
        ceosByYear[int(y)] = set(names)

    history: list[dict] = []
    turnoverCount = 0
    lastChangeYear: int | None = None
    prev: set[str] | None = None
    for y in sorted(ceosByYear.keys()):
        current = ceosByYear[y]
        added: list[str] = []
        removed: list[str] = []
        if prev is not None:
            added = sorted(current - prev)
            removed = sorted(prev - current)
            if added or removed:
                turnoverCount += 1
                lastChangeYear = y
        history.append({"year": y, "ceos": sorted(current), "added": added, "removed": removed})
        prev = current

    # 평균 재임. 윈도우 내 CEO별 (first, last) 연도 차이
    tenures: list[int] = []
    for ceo in {c for s in ceosByYear.values() for c in s}:
        presentYears = [y for y, s in ceosByYear.items() if ceo in s]
        if presentYears:
            tenures.append(max(presentYears) - min(presentYears) + 1)
    avgTenure = round(sum(tenures) / len(tenures), 1) if tenures else None

    latestYear = sorted(ceosByYear.keys())[-1]
    currentCeos = sorted(ceosByYear[latestYear])

    return {
        "windowYears": CEO_TURNOVER_WINDOW_YEARS,
        "turnoverCount": turnoverCount,
        "currentCeos": currentCeos,
        "lastChangeYear": lastChangeYear,
        "avgTenureYears": avgTenure,
        "history": history,
    }


@memoizedCalc
def calcRelatedPartyIntensity(company, *, basePeriod: str | None = None) -> dict | None:
    """특수관계자 거래 집중도. 매출·매입·보증의 내부거래 비율 시계열.

    사업보고서 「X. 대주주 등과의 거래내용」에서 특수관계자 매출·매입·
    채무보증을 추출하고 전사 매출·자산 대비 비율을 산출한다. tunneling
    (자산·수익 이전) 문헌과 ISS Audit&Risk pillar 에 대응하는 축으로,
    지주·계열 중심 기업의 이해충돌 가능성을 포착한다.

    Capabilities:
        - 특수관계자 매출·매입·보증의 전사 대비 비율과 추세 산출.

    When:
        지주·계열 의존도 평가, tunneling 의심 점검 시점.

    How:
        relatedPartyTx 파서 → 연도별 합산 → IS/BS 대비 비율 + 추세 분류.

    Requires:
        DART 「대주주 등과의 거래내용」 파서 결과 + IS/BS 데이터.

    AIContext:
        절대 수치보다 피어 대비·추세 해석. 단위 오류 가능성 (1%↓, 10000%↑) 경고.

    Parameters
    ----------
    company : Company
        분석 대상 기업 (DART).
    basePeriod : str, optional
        비율 계산용 기준 기간. 미지정 시 최신.

    Returns
    -------
    dict | None
        None : relatedPartyTx 데이터 없음 또는 DART 외 provider.
        latest : dict. 최근 연도 비율
            year : int. 연도
            relatedSales : int. 특수관계 매출 (원)
            relatedPurchases : int. 특수관계 매입 (원)
            relatedGuarantee : int. 특수관계 보증 잔액 (원)
            totalRevenue : int | None. 전사 매출 (원)
            totalEquity : int | None. 자기자본 (원)
            relatedRevenueRatio : float | None. 전사 매출 대비 매출 (%)
            relatedPurchaseRatio : float | None. 전사 매출 대비 매입 (%)
            relatedGuaranteeRatio : float | None. 자기자본 대비 보증 (%)
        history : list[dict]. 연도별 추이 (최근 5년)
            year : int
            relatedSales : int. 금액 (원)
            relatedPurchases : int. 금액 (원)
        trend : str. "increasing" | "stable" | "decreasing" | "unknown"
            최근 3년 매출 비율 추이. 데이터 부족 시 "unknown".

    Raises
    ------
    없음. 데이터 없음은 None 반환.

    Examples
    --------
    >>> c = dartlab.Company("005930")
    >>> c.analysis("지배구조")["relatedPartyIntensity"]

    Notes
    -----
    - 파서가 반환하는 금액은 사업보고서 표기 단위(백만원) 가정. calc 내부
      에서 원 단위로 환산 후 IS/BS 와 비율 계산.
    - 파서가 단위를 자동 감지하지 않으므로 공시 표 단위가 "천원"이나 "원"
      이면 비율이 과대/과소 추정된다. 1% 미만·10000% 초과 값은 단위 오류
      가능성이 있으니 원본 (`c.panel("relatedPartyTx")`) 확인 권장.
    - 매입 비율은 전사 매출 대비로 일관성 유지 (매출원가 분해가 기업별
      일정치 않아 비교 가능성 우선).

    Guide
    -----
    `relatedRevenueRatio >= 30%` + `trend == "increasing"` 은 매출의 내부
    계열 의존도가 커지는 tunneling 신호. 지주·계열사 기업은 구조상 높게
    나올 수 있어 절대 수치보다 **피어 대비·추세**로 해석한다.

    See Also
    --------
    calcOwnerConcentration : 소유-지배 괴리 (별도 축).
    calcLegalEventRisk : 제재·소송 (별도 축).
    """
    from dartlab.analysis.financial._governanceDeep import (
        _fetchLatestEquity,
        _loadRelatedPartyTx,
    )

    rpt = _loadRelatedPartyTx(company)
    if rpt is None:
        return None
    if rpt.revenueTxDf is None and rpt.guaranteeDf is None:
        return None

    # 연도별 매출·매입·보증 합계 (백만원 → 원 환산)
    salesByYear, purchasesByYear = _amountsByYear(rpt.revenueTxDf, ("sales", "purchases"))
    (guaranteeByYear,) = _amountsByYear(rpt.guaranteeDf, ("amount",))

    allYears = sorted(set(salesByYear) | set(purchasesByYear) | set(guaranteeByYear))
    if not allYears:
        return None

    revenueMap = _annualRevenueMap(company, basePeriod)
    totalEquity = _fetchLatestEquity(company, basePeriod=basePeriod)

    history: list[dict] = []
    for y in allYears[-MAX_RATIO_YEARS:]:
        history.append(
            {
                "year": y,
                "relatedSales": salesByYear.get(y, 0),
                "relatedPurchases": purchasesByYear.get(y, 0),
            }
        )

    latestYear = allYears[-1]
    relatedSales = salesByYear.get(latestYear, 0)
    relatedPurchases = purchasesByYear.get(latestYear, 0)
    relatedGuarantee = guaranteeByYear.get(latestYear, 0)
    totalRevenue = revenueMap.get(latestYear)

    relatedRevenueRatio: float | None = None
    relatedPurchaseRatio: float | None = None
    relatedGuaranteeRatio: float | None = None
    if totalRevenue and totalRevenue > 0:
        relatedRevenueRatio = round(relatedSales / totalRevenue * 100, 1)
        relatedPurchaseRatio = round(relatedPurchases / totalRevenue * 100, 1)
    if totalEquity and totalEquity > 0:
        relatedGuaranteeRatio = round(relatedGuarantee / totalEquity * 100, 1)

    return {
        "latest": {
            "year": latestYear,
            "relatedSales": relatedSales,
            "relatedPurchases": relatedPurchases,
            "relatedGuarantee": relatedGuarantee,
            "totalRevenue": totalRevenue,
            "totalEquity": totalEquity,
            "relatedRevenueRatio": relatedRevenueRatio,
            "relatedPurchaseRatio": relatedPurchaseRatio,
            "relatedGuaranteeRatio": relatedGuaranteeRatio,
        },
        "history": history,
        "trend": _relatedSalesTrend(history, revenueMap),
    }


def _amountsByYear(df, fields: tuple[str, ...]) -> list[dict[int, int]]:
    """연도별 금액 합계를 필드 수만큼 만들어 돌려준다 (백만원 → 원 환산).

    매출·매입 테이블과 보증 테이블이 컬럼명만 다른 같은 누적을 하고 있었다.
    반환 리스트 순서는 ``fields`` 순서와 같다. df 가 없거나 비면 전부 빈 dict.
    """
    totals: list[dict[int, int]] = [{} for _ in fields]
    if df is None or df.is_empty():
        return totals
    for row in df.iter_rows(named=True):
        y = row.get("year")
        if y is None:
            continue
        y = int(y)
        for slot, field in zip(totals, fields):
            amount = row.get(field) or 0
            slot[y] = slot.get(y, 0) + int(amount) * RELATED_PARTY_PARSER_UNIT
    return totals


def _annualRevenueMap(company, basePeriod: str | None) -> dict[int, int]:
    """전사 매출 연간 시계열을 {연도: 금액} 으로. 조회 불가는 빈 dict."""
    revenueMap: dict[int, int] = {}
    try:
        parsed = toDictBySnakeId(company.select("IS", ["sales"]))
    except (AttributeError, ValueError, KeyError, TypeError) as exc:
        # 원인을 남긴다. 조용히 빈 dict 을 돌려주면 "매출이 0 이었다" 와 "매출을 못 읽었다"
        # 가 관계자 거래 비중 계산에서 같은 결과가 된다.
        _log.debug("전사 매출 조회 실패로 관계자 거래 비중을 못 낸다 (%s: %s)", type(exc).__name__, exc)
        parsed = None
    if parsed is None:
        return revenueMap

    isData, periods = parsed
    yCols = annualColsFromPeriods(periods, basePeriod=basePeriod, maxYears=10)
    salesRow = isData.get("sales", {})
    for col in yCols:
        try:
            yr = int(col[:4])
        except (ValueError, TypeError) as exc:
            # 연도를 못 읽는 기간 열은 건너뛰되 흔적은 남긴다. 결과 dict 만 보면 그 해가
            # 원래 없었는지 열 이름을 못 읽어 빠졌는지 구분되지 않는다.
            _log.debug("기간 열에서 연도를 못 읽어 건너뛴다 (%s, %s)", col, type(exc).__name__)
            continue
        v = salesRow.get(col)
        if v is not None:
            revenueMap[yr] = int(v)
    return revenueMap


def _relatedSalesTrend(history: list[dict], revenueMap: dict[int, int]) -> str:
    """추세 판정: 전사 매출 대비 특수관계 매출 비율의 최근 3년 변화."""
    ratios: list[float] = []
    for h in history[-3:]:
        rev = revenueMap.get(h["year"])
        if rev and rev > 0:
            ratios.append(h["relatedSales"] / rev * 100)
    if len(ratios) < 2:
        return "unknown"
    delta = ratios[-1] - ratios[0]
    if delta > 5:
        return "increasing"
    if delta < -5:
        return "decreasing"
    return "stable"


@memoizedCalc
def calcLegalEventRisk(company, *, basePeriod: str | None = None) -> dict | None:
    """법적 이벤트 리스크. 최근 3년 제재·소송 + 채무보증/자기자본 집계.

    사업보고서 「III. 제재 현황」· 「2. 우발부채」 섹션에서 제재 건수·금액,
    소송 건수·금액, 자기자본 대비 채무보증 비율을 추출한다. 이벤트 스터디
    실증(벌칙공시 이후 누적초과수익률 음)과 ISS Governance QualityScore
    Audit&Risk 필러에 대응하는 축.

    Capabilities:
        - 제재·소송·채무보증을 3 년 윈도우로 집계해 자기자본 대비 비율 산출.

    When:
        Audit&Risk 평가, 우발부채 부담 점검 시점.

    How:
        sanction/contingent 파서 결과 → 윈도우 합산 → 자기자본 대비 비율.

    Requires:
        DART 「제재 현황」·「우발부채」 파서 결과 + 자기자본 (BS).

    AIContext:
        이벤트 0 건은 None 아닌 count=0. 미보고 가능성도 함께 언급.

    Parameters
    ----------
    company : Company
        분석 대상 기업. DART Company만 지원 (EDGAR는 None 반환).
    basePeriod : str, optional
        자기자본 조회 기준 기간 (예: "2024Q4"). 미지정 시 최신.

    Returns
    -------
    dict | None
        None : sanction/contingent 데이터 없음 또는 DART 외 provider.
        sanctionCount : int. 최근 3년 제재 건수 (건)
        sanctionAmount : int. 최근 3년 제재 금액 합계 (원)
        lawsuitCount : int. 최근 3년 소송 건수 (건)
        lawsuitAmount : int. 최근 3년 소송 청구 금액 합계 (원)
        guaranteeAmount : int | None. 최근연도 채무보증 총액 (원)
        totalEquity : int | None. 최근연도 자기자본 (원)
        guaranteeToEquity : float | None. 자기자본 대비 채무보증 비율 (%)
        windowYears : int. 집계 윈도우 (년). 상수 3.
        recentEvents : list[dict]. 최근 이벤트 상위 5건
            year : int. 발생 연도
            kind : str. "sanction" 또는 "lawsuit"
            date : str. 발생일 (YYYY-MM-DD 또는 부분 문자열)
            party : str. 제재 기관 또는 소송 당사자
            description : str. 사건 내용·사유
            amount : int | None. 금액 (원). 미기재 시 None.

    Raises
    ------
    없음. 데이터 없음은 None 반환.

    Examples
    --------
    >>> c = dartlab.Company("005930")
    >>> c.analysis("지배구조")["legalEventRisk"]

    Notes
    -----
    - 집계 윈도우 3년은 이벤트 스터디 연구의 표준 관측 구간.
    - 제재·소송은 사업보고서 텍스트 섹션 기반이라 기업별 표 구조 차이로
      금액 추출이 실패하면 ``amount``는 None으로 두고 건수만 집계한다.
    - 채무보증은 최신 연도 stock 기준 (연결 또는 개별, 표기 기준 그대로).
    - EDGAR Company는 DART parquet을 가정하는 파이프라인 특성상 None 반환.

    Guide
    -----
    이벤트가 없으면 count=0, recentEvents=[] 반환 (None 아님).
    guaranteeToEquity >= 50%는 우발채무 부담이 큰 기업의 경고 신호로 본다.

    See Also
    --------
    calcGovernanceFlags : 본 calc 결과를 warning 플래그로 소비.
    """
    import datetime

    from dartlab.analysis.financial._governanceDeep import (
        _fetchLatestEquity,
        _loadContingentLiability,
        _loadSanction,
    )

    sanc = _loadSanction(company)
    cont = _loadContingentLiability(company)

    if sanc is None and cont is None:
        return None

    thisYear = datetime.datetime.now().year
    cutoff = thisYear - LEGAL_EVENT_WINDOW_YEARS

    # 제재와 소송은 컬럼명만 다른 같은 집계 (윈도우 필터 → 건수·금액 → 최근 5 건).
    sanctionCount, sanctionAmount, sanctionEvents = _legalEventRows(
        sanc.sanctionDf if sanc is not None else None,
        cutoff,
        kind="sanction",
        dateKeys=("date",),
        partyKeys=("agency", "subject"),
        descriptionKeys=("action", "reason"),
    )
    lawsuitCount, lawsuitAmount, lawsuitEvents = _legalEventRows(
        cont.lawsuitDf if cont is not None else None,
        cutoff,
        kind="lawsuit",
        dateKeys=("filingDate",),
        partyKeys=("parties",),
        descriptionKeys=("description",),
    )

    guaranteeAmount = _latestGuaranteeAmount(cont.guaranteeDf if cont is not None else None)
    totalEquity = _fetchLatestEquity(company, basePeriod=basePeriod)

    guaranteeToEquity: float | None = None
    if guaranteeAmount is not None and totalEquity and totalEquity > 0:
        guaranteeToEquity = round(guaranteeAmount / totalEquity * 100, 1)

    recentEvents = sorted(
        sanctionEvents + lawsuitEvents,
        key=lambda e: (e.get("year") or 0),
        reverse=True,
    )[:5]

    return {
        "sanctionCount": sanctionCount,
        "sanctionAmount": sanctionAmount,
        "lawsuitCount": lawsuitCount,
        "lawsuitAmount": lawsuitAmount,
        "guaranteeAmount": guaranteeAmount,
        "totalEquity": totalEquity,
        "guaranteeToEquity": guaranteeToEquity,
        "windowYears": LEGAL_EVENT_WINDOW_YEARS,
        "recentEvents": recentEvents,
    }


def _firstTruthy(row: dict, keys: tuple[str, ...]) -> str:
    """키 후보를 순서대로 훑어 처음 참인 값. 전부 비면 빈 문자열."""
    for key in keys:
        value = row.get(key)
        if value:
            return value
    return ""


def _legalEventRows(
    df,
    cutoff: int,
    *,
    kind: str,
    dateKeys: tuple[str, ...],
    partyKeys: tuple[str, ...],
    descriptionKeys: tuple[str, ...],
) -> tuple[int, int, list[dict]]:
    """윈도우 안 법적 이벤트를 건수·금액·최근 5 건으로 집계한다.

    제재 표와 소송 표는 컬럼 이름만 다르고 집계 절차가 같아서, 이름 매핑을 인자로
    받는 한 곳으로 합쳤다. 파서가 표 구조 차이로 금액을 못 뽑으면 amount 는 None 이고
    건수만 남는다.
    """
    import polars as pl

    if df is None or df.is_empty():
        return 0, 0, []

    recent = df.filter(pl.col("year") >= cutoff)
    count = recent.height
    amount = 0
    if "amountValue" in recent.columns and recent.height > 0:
        total = recent["amountValue"].sum()
        amount = int(total) if total is not None else 0

    events: list[dict] = []
    for row in recent.sort("year", descending=True).head(5).iter_rows(named=True):
        amt = row.get("amountValue")
        events.append(
            {
                "year": row.get("year"),
                "kind": kind,
                "date": _firstTruthy(row, dateKeys),
                "party": _firstTruthy(row, partyKeys),
                "description": _firstTruthy(row, descriptionKeys),
                "amount": int(amt) if amt is not None else None,
            }
        )
    return count, amount, events


def _latestGuaranteeAmount(df) -> int | None:
    """최신 연도 채무보증 총액 (stock 기준). 표나 컬럼이 없으면 None."""
    if df is None or df.is_empty():
        return None
    latest = df.sort("year", descending=True).head(1)
    if latest.height == 0 or "totalGuaranteeAmount" not in latest.columns:
        return None
    val = latest["totalGuaranteeAmount"].item()
    return int(val) if val is not None else None
