"""capital.py 현금흐름 + 부실 calc 분리.

분리 이유: capital.py 873 줄. calcCashFlowStructure (98) + _sign + _classifyCfPattern
+ _isFinancialCompany + calcDistressIndicators (67) 등 약 240 줄. 별도 모듈로 빼서
capital.py 의 facade (자본/부채/이자/유동성) 책임 유지.

BC: capital 모듈에서 두 calc + 헬퍼 모두 import 가능 (re-export).
순환 import 회피: capital.py 의 _quarterlyCols / _getRatios / _MAX_QUARTERS 는
함수 내부 lazy import 또는 인자 전달로 처리.
"""

from __future__ import annotations

from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId

_MAX_QUARTERS = 5
_MAX_YEARS = 8


def _cashFlowTableRows(
    ocfRow: dict,
    icfRow: dict | None,
    fcfRow: dict | None,
    capexRow: dict | None,
    qCols: list[str],
) -> list[dict]:
    """영업/투자/재무 CF 와 FCF 행 조립. 없는 행은 넣지 않는다.

    Parameters
    ----------
    ocfRow : dict
        영업활동현금흐름 행.
    icfRow, fcfRow, capexRow : dict | None
        투자 / 재무 CF, 유형자산 취득 행.
    qCols : list[str]
        분기 컬럼 (최신 먼저).

    Returns
    -------
    list[dict]
        표 행 목록.
    """
    rawRows: list[dict] = []
    rawRows.append({"": "영업CF", **{c: ocfRow.get(c) for c in qCols}})
    if icfRow:
        rawRows.append({"": "투자CF", **{c: icfRow.get(c) for c in qCols}})
    if fcfRow:
        rawRows.append({"": "재무CF", **{c: fcfRow.get(c) for c in qCols}})
    if capexRow:
        freeRow: dict = {"": "FCF"}
        for c in qCols:
            ocf = ocfRow.get(c)
            capex = capexRow.get(c)
            if ocf is not None and capex is not None:
                freeRow[c] = ocf + capex if capex < 0 else ocf - capex
            else:
                freeRow[c] = None
        rawRows.append(freeRow)
    return rawRows


def _resolveCfPattern(
    ocfRow: dict,
    icfRow: dict | None,
    fcfRow: dict | None,
    qCols: list[str],
    allPeriods: list[str],
) -> str | None:
    """최신 분기 부호 조합으로 CF 패턴 분류. 실패하면 최근 Q4 세 개로 재시도.

    Parameters
    ----------
    ocfRow : dict
        영업활동현금흐름 행.
    icfRow, fcfRow : dict | None
        투자 / 재무 CF 행.
    qCols : list[str]
        분기 컬럼 (최신 먼저).
    allPeriods : list[str]
        전체 기간 컬럼.

    Returns
    -------
    str | None
        패턴 라벨.
    """
    latestCol = qCols[0]
    ocfSign = _sign(ocfRow.get(latestCol))
    icfSign = _sign((icfRow or {}).get(latestCol))
    fcfSign = _sign((fcfRow or {}).get(latestCol))
    pattern = _classifyCfPattern(ocfSign, icfSign, fcfSign)
    if pattern is not None:
        return pattern
    # Q4 기준으로 재시도 (재무CF가 특정 분기에만 있는 기업 대응)
    q4Cols = sorted([c for c in allPeriods if c.endswith("Q4")], reverse=True)
    for qc in q4Cols[:3]:
        pattern = _classifyCfPattern(
            _sign(ocfRow.get(qc)),
            _sign((icfRow or {}).get(qc)),
            _sign((fcfRow or {}).get(qc)),
        )
        if pattern is not None:
            break
    return pattern


def _cashFlowMetrics(ratios) -> list[tuple[str, str]] | None:
    """비율 결과에서 CF 관련 보조 지표 3 종을 뽑는다.

    Parameters
    ----------
    ratios : Any
        RatioResult 또는 None.

    Returns
    -------
    list[tuple[str, str]] | None
        (라벨, 값) 쌍. 하나도 없으면 None.
    """
    if ratios is None:
        return None
    extra = []
    ocfm = getattr(ratios, "operatingCfMargin", None)
    if ocfm is not None:
        extra.append(("영업CF 마진", f"{ocfm:.1f}%"))
    cxr = getattr(ratios, "capexRatio", None)
    if cxr is not None:
        extra.append(("CAPEX/매출", f"{cxr:.1f}%"))
    ftor = getattr(ratios, "fcfToOcfRatio", None)
    if ftor is not None:
        extra.append(("FCF/OCF", f"{ftor:.0f}%"))
    return extra or None


@memoizedCalc
def calcCashFlowStructure(company, *, basePeriod: str | None = None) -> dict | None:
    """영업CF/투자CF/재무CF + FCF + CF 패턴.

    Capabilities:
        - 3 종 현금흐름 부호 패턴 분류와 FCF 계산.

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    basePeriod : str, optional
        기준 기간.

    Returns
    -------
    dict | None
        tableRows : list[dict] — CF 항목별 기간 매핑 행
        cols : list[str] — 기간 컬럼
        pattern : str | None — CF 패턴 진단
        metrics : list[tuple[str, str]] | None — FCF 등 요약 지표

    Guide:
        +/-/+ 패턴 = 성숙기, -/-/+ = 초기/위기 등 8 분류 참고.

    When:
        영업·투자·재무 자금흐름 종합 진단 시점.

    How:
        OCF/ICF/FCF 부호 매트릭스 분류 + FCF = OCF - CAPEX.

    Requires:
        CF 분기 또는 Q4, capex 식별 가능.

    Raises:
        없음 — 결측 시 None.

    Example:
        >>> calcCashFlowStructure(company)
        {'pattern': '성숙기', ...}

    See Also:
        - calcDistressIndicators : 재무 곤경 신호.

    AIContext:
        패턴 분류는 정성 라벨 — 단정 대신 신호로 인용.
    """
    from dartlab.analysis.financial.capital import _getRatios, _quarterlyCols

    result = company.select(
        "CF",
        ["영업활동현금흐름", "투자활동현금흐름", "재무활동으로인한현금흐름", "유형자산의취득"],
    )
    parsed = toDictBySnakeId(result)
    if parsed is None:
        return None

    data, allPeriods = parsed
    ocfRow = data.get("operating_cashflow") or data.get("cash_flows_from_operating_activities")
    if ocfRow is None:
        return None
    icfRow = data.get("investing_cashflow") or data.get("cash_flows_from_investing_activities")
    fcfRow = data.get("cash_flows_from_financing_activities") or data.get("financing_cashflow")
    capexRow = data.get("purchase_of_property_plant_and_equipment")

    qCols = _quarterlyCols(allPeriods, _MAX_QUARTERS)
    if not qCols:
        return None

    rawRows = _cashFlowTableRows(ocfRow, icfRow, fcfRow, capexRow, qCols)

    # CF 패턴 분류 (분기 우선, 분기 데이터 없으면 연간 fallback)
    pattern = _resolveCfPattern(ocfRow, icfRow, fcfRow, qCols, allPeriods)

    # 추가 지표
    metrics = _cashFlowMetrics(_getRatios(company))

    return {
        "tableRows": rawRows,
        "cols": qCols,
        "pattern": pattern,
        "metrics": metrics,
    }


def _sign(val) -> str:
    """양/음/0 부호.

    Returns
    -------
    str
        ``"+"``, ``"-"``, ``"0"``, 또는 ``"?"`` (None).
    """
    if val is None:
        return "?"
    if val > 0:
        return "+"
    if val < 0:
        return "-"
    return "0"


def _classifyCfPattern(ocf: str, icf: str, fcf: str) -> str | None:
    """영업/투자/재무 CF 부호 조합으로 패턴 분류.

    Parameters
    ----------
    ocf : str
        영업CF 부호 (``"+"``, ``"-"``, ``"0"``, ``"?"``).
    icf : str
        투자CF 부호.
    fcf : str
        재무CF 부호.

    Returns
    -------
    str | None
        CF 패턴 한국어 설명 (예: ``"성숙형 — 영업으로 벌어 투자하고 부채 상환"``).
        미분류 조합이면 None.
    """
    patterns = {
        ("+", "-", "-"): "성숙형 — 영업으로 벌어 투자하고 부채 상환",
        ("+", "-", "+"): "확장형 — 영업 + 외부 조달로 적극 투자",
        ("+", "+", "-"): "구조조정형 — 자산 매각하며 부채 상환",
        ("-", "-", "+"): "위기형 — 영업 적자를 외부 차입으로 메움",
        ("-", "+", "+"): "축소형 — 자산 매각 + 차입으로 영업 적자 보전",
        ("-", "+", "-"): "전환형 — 자산 매각으로 부채 상환, 영업 회복 필요",
        # 재무CF 미보고("?" 또는 "0") — 영업/투자만으로 부분 분류
        ("+", "-", "?"): "성숙형 — 영업으로 벌어 투자 (재무CF 미보고)",
        ("+", "-", "0"): "성숙형 — 영업으로 벌어 투자 (재무CF 미보고)",
        ("-", "-", "?"): "위기형 — 영업+투자 모두 유출 (재무CF 미보고)",
        ("-", "-", "0"): "위기형 — 영업+투자 모두 유출 (재무CF 미보고)",
    }
    return patterns.get((ocf, icf, fcf))


def _isFinancialCompany(company) -> bool:
    """금융업 판별 (capital.py 내부용).

    Returns
    -------
    bool
        금융업/지주사이면 True.
    """
    try:
        sector = getattr(company, "sector", None)
        if sector is not None:
            from dartlab.frame.sector import Sector

            if sector.sector == Sector.FINANCIALS:
                return True
        name = getattr(company, "corpName", "") or ""
        if any(k in name for k in ("지주", "홀딩스", "Holdings")):
            return True
    except (AttributeError, ImportError):
        pass
    return False


@memoizedCalc
def calcDistressIndicators(company, *, basePeriod: str | None = None) -> dict | None:
    """Altman Z, Ohlson O, Piotroski F, Springate S.

    Capabilities:
        - 4 종 부실예측 모형 결과를 라벨링해 일괄 노출.

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    basePeriod : str, optional
        기준 기간.

    Returns
    -------
    dict | None
        metrics : list[tuple[str, str]] — (지표명, 값+판정 문자열) 쌍 목록

    Guide:
        금융업은 Altman 적용 제외. 4 지표 중복 신호 확인.

    When:
        부실 위험 종합 점검, 신용 평가 보조 시점.

    How:
        ratios 객체의 사전 계산된 4 지표를 임계 비교 후 라벨링.

    Requires:
        capital._getRatios 가 4 지표 계산 가능 (BS/IS/CF 시계열).

    Raises:
        없음 — ratios 부재 시 None.

    Example:
        >>> calcDistressIndicators(company)
        {'metrics': [('Altman Z', '3.10 — 안전'), ...]}

    See Also:
        - calcCashFlowStructure : 현금흐름 패턴.

    AIContext:
        4 지표 중 다수 일치할 때만 결론 인용 (단일 지표 단정 금지).
    """
    from dartlab.analysis.financial.capital import _getRatios

    ratios = _getRatios(company)
    if ratios is None:
        return None

    isFinancial = _isFinancialCompany(company)
    metrics = []

    # Altman Z-Score: 비금융 제조업용 모형 — 금융업에는 적용 불가
    if not isFinancial:
        az = getattr(ratios, "altmanZScore", None)
        if az is None:
            az = getattr(ratios, "altmanZppScore", None)
        if az is not None:
            if az > 2.99:
                quality = "안전"
            elif az > 1.81:
                quality = "회색지대"
            else:
                quality = "부실 위험"
            metrics.append(("Altman Z", f"{az:.2f} — {quality}"))

    op = getattr(ratios, "ohlsonProbability", None)
    if op is not None:
        metrics.append(("Ohlson 부실확률", f"{op:.1f}%"))
    else:
        os_ = getattr(ratios, "ohlsonOScore", None)
        if os_ is not None:
            metrics.append(("Ohlson O-Score", f"{os_:.2f}"))

    pf = getattr(ratios, "piotroskiFScore", None)
    if pf is not None:
        maxF = getattr(ratios, "piotroskiMaxScore", 9)
        if pf >= 7:
            quality = "재무 건전"
        elif pf >= 4:
            quality = "보통"
        else:
            quality = "재무 약화"
        metrics.append(("Piotroski F", f"{pf}/{maxF} — {quality}"))

    ss = getattr(ratios, "springateSScore", None)
    if ss is not None:
        quality = "안전" if ss > 0.862 else "부실 위험"
        metrics.append(("Springate S", f"{ss:.2f} — {quality}"))

    if not metrics:
        return None

    return {"metrics": metrics}
