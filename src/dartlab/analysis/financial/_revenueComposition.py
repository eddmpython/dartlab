"""revenue.py 내부 헬퍼 — 수익구조 분석용 dict/시계열 가공.

분리 이유: revenue.py 가 991 줄. 5 개 헬퍼 (161 줄) 를 별도 모듈로 분리해
revenue.py 의 facade 책임을 유지.

순환 import 회피: revenue.py 의 ``_SKIP_KEYWORDS`` · ``_MAX_YEARS`` ·
``_selectDocsRevenue`` · ``_selectDocsSalesOrder`` 는 함수 내부에서 lazy import.
"""

from __future__ import annotations

from dartlab.core.utils.helpers import (
    annualColsFromPeriods as _annualColsFromPeriods,
)
from dartlab.core.utils.helpers import (
    parseNumStr as _parseNumStr,
)


def _getDocsRevenueVals(company) -> list[float]:
    """productService에서 최신 기간 부문별 매출 양수 값 리스트.

    Returns
    -------
    list[float]
        부문별 매출 양수 값 리스트 (원). 데이터 없으면 빈 리스트.
    """
    from dartlab.analysis.financial.revenue import _selectDocsRevenue

    docsResult = _selectDocsRevenue(company)
    if docsResult is None:
        return []

    segData, yCols = docsResult
    latestYear = yCols[0]

    vals = []
    for _segName, segVals in segData.items():
        v = segVals.get(latestYear)
        if v is not None and v > 0:
            vals.append(v)
    return vals


def _calcCompositionHistory(segData: dict[str, dict[str, float]], yCols: list[str]) -> list[dict] | None:
    """연도별 부문 비중 변화.

    Returns
    -------
    list[dict] | None
        ``[{"year": str, "shares": {부문명: 비중(%)}}, ...]``.
        2개 연도 미만이면 None.
    """
    history = []
    for yc in yCols:
        yearVals = {s: segData[s].get(yc, 0) for s in segData}
        total = sum(yearVals.values())
        if total <= 0:
            continue
        shares = {s: v / total * 100 for s, v in yearVals.items() if v > 0}
        history.append({"year": yc, "shares": shares})
    return history if len(history) >= 2 else None


def _calcHhiHistory(company) -> tuple[list[dict], str] | None:
    """연도별 HHI 시계열 + 방향.

    Returns
    -------
    tuple[list[dict], str] | None
        ``([{"year": str, "hhi": float(점)}, ...], direction)`` 튜플.
        direction은 ``"다각화 진행"`` | ``"집중 심화"`` | ``"안정"``.
        데이터 없으면 None.
    """
    from dartlab.analysis.financial.revenue import _selectDocsRevenue

    docsResult = _selectDocsRevenue(company)
    if docsResult is None:
        return None
    segData, yCols = docsResult
    hhiList = []
    for yc in yCols:
        yearVals = [segData[s].get(yc, 0) for s in segData]
        total = sum(yearVals)
        if total <= 0:
            continue
        hhi = sum((v / total * 100) ** 2 for v in yearVals if v > 0)
        hhiList.append({"year": yc, "hhi": hhi})
    if not hhiList:
        return None
    direction = "안정"
    if len(hhiList) >= 2:
        newest = hhiList[0]["hhi"]
        oldest = hhiList[-1]["hhi"]
        diff = newest - oldest
        if diff < -300:
            direction = "다각화 진행"
        elif diff > 300:
            direction = "집중 심화"
    return hhiList, direction


def _calcBreakdownHistoryFromDocs(company, *, basePeriod: str | None = None) -> list[dict] | None:
    """salesOrder에서 다년간 비중 변화.

    Returns
    -------
    list[dict] | None
        ``[{"year": str, "shares": {항목명: 비중(%)}}, ...]``.
        2개 연도 미만이면 None.
    """
    from dartlab.analysis.financial.revenue import (
        _MAX_YEARS,
        _SKIP_KEYWORDS,
        _selectDocsSalesOrder,
    )

    result = _selectDocsSalesOrder(company)
    if result is None:
        return None

    df = result.df
    if df.is_empty():
        return None

    itemCol = df.columns[0]
    periodCols = [c for c in df.columns if c != itemCol]
    yCols = _annualColsFromPeriods(periodCols, basePeriod, _MAX_YEARS)
    if len(yCols) < 2:
        return None

    history = []
    for yc in yCols:
        shares: dict[str, float] = {}
        total = 0.0
        for row in df.iter_rows(named=True):
            name = str(row.get(itemCol, "")).strip()
            if any(kw in name for kw in _SKIP_KEYWORDS):
                continue
            v = _parseNumStr(row.get(yc))
            if v is not None and v > 0:
                shares[name] = v
                total += v
        if total > 0 and shares:
            history.append({"year": yc, "shares": {k: v / total * 100 for k, v in shares.items()}})

    return history if len(history) >= 2 else None


def _calcDomesticExportRatio(company) -> float | None:
    """내수 비중 — salesOrder에서 국내 키워드 매칭.

    Returns
    -------
    float | None
        내수 매출 비중 (%). 데이터 없으면 None.
    """
    from dartlab.analysis.financial.revenue import _SKIP_KEYWORDS, _selectDocsSalesOrder

    result = _selectDocsSalesOrder(company)
    if result is None:
        return None

    df = result.df
    if df.is_empty():
        return None

    itemCol = df.columns[0]
    periodCols = [c for c in df.columns if c != itemCol]
    yCols = _annualColsFromPeriods(periodCols, None, 1)
    if not yCols:
        return None

    latestYear = yCols[0]
    domesticKeywords = {"국내", "한국", "내수", "korea", "domestic"}

    domesticVal = 0.0
    totalVal = 0.0
    for row in df.iter_rows(named=True):
        name = str(row.get(itemCol, "")).strip()
        if any(kw in name for kw in _SKIP_KEYWORDS):
            continue
        v = _parseNumStr(row.get(latestYear))
        if v is not None and v > 0:
            totalVal += v
            if any(kw in name.lower() for kw in domesticKeywords):
                domesticVal += v

    return domesticVal / totalVal * 100 if totalVal > 0 else None
