"""건설업 KPI. 수주잔고/도급vs자체/PF노출/시공안전.

DART report(constructionOrders) + panel(productService) + panel(provisions/borrowings) 활용.
"""

from __future__ import annotations

from dartlab.core.memory import memoizedCalc

_CONTRACT_KEYWORDS = ["도급", "시공", "건축"]
_SELF_DEV_KEYWORDS = ["자체", "분양", "개발", "매각"]


def _orderBacklog(company, basePeriod: str | None) -> dict | None:
    """매출 시계열 기반 수주잔고 대용 지표.

    Parameters
    ----------
    company : Any
        기업 객체.
    basePeriod : str | None
        기준 기간.

    Returns
    -------
    dict | None
        revenueHistory + note. 산출 불가 시 None.
    """
    from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId

    try:
        parsed = toDictBySnakeId(company.select("IS", ["sales"]))
        if not parsed:
            return None
        isData, periods = parsed
        yCols = annualColsFromPeriods(periods, basePeriod=basePeriod, maxYears=5)
        salesRow = isData.get("sales", {})
        revenues = [(c, salesRow.get(c)) for c in yCols if salesRow.get(c)]
        if not revenues:
            return None
        return {
            "revenueHistory": [{"period": c, "revenue": v} for c, v in revenues],
            "note": "수주잔고는 사업보고서 수주상황 항목에서 추출 필요 (현재 매출 시계열만)",
        }
    except (AttributeError, ValueError, TypeError):
        # 원본과 같은 자리에서 삼킨다. 섹션이 없으면 KPI 하나를 비워 둔다.
        return None


def _contractMix(company) -> dict | None:
    """제품/부문 표 키워드로 도급 vs 자체개발 매출 비중 추정.

    Parameters
    ----------
    company : Any
        기업 객체 (stockCode 사용).

    Returns
    -------
    dict | None
        contractRatio / selfDevRatio / note. 합계가 0 이면 None.
    """
    try:
        from dartlab.providers.dart.panel.text import panelXmlTables
        from dartlab.providers.dart.tableRows import parseAmount

        code = getattr(company, "stockCode", None)
        tables = (
            (panelXmlTables(code, sectionPattern="제품") or panelXmlTables(code, sectionPattern="부문")) if code else []
        )
        contractRev = 0.0
        selfDevRev = 0.0
        for table in tables:
            for row in table[1:]:
                text = " ".join(row)
                amt = next((a for a in (parseAmount(c) for c in row) if a), None) or 0.0
                if any(k in text for k in _CONTRACT_KEYWORDS):
                    contractRev += abs(amt)
                elif any(k in text for k in _SELF_DEV_KEYWORDS):
                    selfDevRev += abs(amt)
        total = contractRev + selfDevRev
        if total <= 0:
            return None
        return {
            "contractRatio": round(contractRev / total * 100, 1),
            "selfDevRatio": round(selfDevRev / total * 100, 1),
            "note": "도급=시공/건축 키워드, 자체개발=분양/매각 키워드 기반 추정",
        }
    except (AttributeError, ValueError, TypeError, KeyError):
        # 원본과 같은 자리에서 삼킨다. 섹션이 없으면 KPI 하나를 비워 둔다.
        return None


def _pfExposure(company) -> dict | None:
    """충당부채 섹션 본문에서 PF 관련 항목 수를 센다.

    Parameters
    ----------
    company : Any
        기업 객체 (stockCode 사용).

    Returns
    -------
    dict | None
        pfRelatedItems / note. 하나도 없으면 None.
    """
    try:
        import polars as pl

        from dartlab.providers.dart.panel.text import panelTextRows

        code = getattr(company, "stockCode", None)
        texts = panelTextRows(code) if code else None
        if texts is None or texts.is_empty():
            return None
        sub = texts.filter(pl.col("sectionLeaf").str.contains("충당부채"))
        pfCount = sum(1 for cr in sub["contentRaw"].to_list() if cr and ("PF" in cr or "프로젝트" in cr))
        if not pfCount:
            return None
        return {"pfRelatedItems": pfCount, "note": "충당부채 섹션 내 PF 관련 본문 수"}
    except (AttributeError, ValueError, TypeError, KeyError):
        # 원본과 같은 자리에서 삼킨다. 섹션이 없으면 KPI 하나를 비워 둔다.
        return None


@memoizedCalc
def calcConstructionKpis(company, *, basePeriod: str | None = None) -> dict | None:
    """건설업 핵심 KPI 통합 반환.

    Capabilities:
        - 수주잔고·도급비중·PF 노출 3 종 KPI 통합 산출.

    Guide:
        DART report(constructionOrders) + panel(productService) + panel(provisions) 결합.

    When:
        건설사 (현대건설·GS건설 등) 펀더멘털 분석 시.

    How:
        매출 시계열·productService 키워드 매칭·충당부채 PF 항목 카운트.

    Requires:
        company.select("IS") + panel("productService") + panel("provisions") 가능.

    Raises:
        없음. 내부 예외 (AttributeError·ValueError·TypeError·KeyError) try 흡수.

    Returns:
        dict | None
            orderBacklog : dict | None. 수주잔고 시계열 + 회전
            contractMix : dict | None. 도급 vs 자체개발 비중 + 마진 갭
            pfExposure : dict | None. PF 보증·채무 노출

    Example:
        >>> calcConstructionKpis(현대건설)
        {"orderBacklog": {...}, "contractMix": {...}, "pfExposure": {...}}

    See Also:
        - dispatcher.sectorKpi : 섹터 자동 라우팅 진입점.

    AIContext:
        건설업 펀더멘털 질문 시 도급/자체개발 비중·PF 노출 인용.
    """
    result: dict = {}

    # ── 수주잔고 추정 (매출 대비 기전수주/당기수주/기말수주 추출) ──
    backlog = _orderBacklog(company, basePeriod)
    if backlog is not None:
        result["orderBacklog"] = backlog

    # ── 도급 vs 자체개발 비중 (공통파서 panel 제품/부문 표 키워드 + 금액) ──
    mix = _contractMix(company)
    if mix is not None:
        result["contractMix"] = mix

    # ── PF 노출 (공통파서 panel 충당부채 섹션 본문 PF 키워드) ──
    pf = _pfExposure(company)
    if pf is not None:
        result["pfExposure"] = pf

    return result if result else None
