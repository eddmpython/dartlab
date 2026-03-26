"""groundTruthFacts 자동 추출 — finance 엔진에서 수치를 harvest."""

from __future__ import annotations

import re
from typing import Any

# ── 질문 키워드 → 관련 계정 매핑 ─────────────────────────

_IS_ACCOUNTS = [
    ("sales", "매출액"),
    ("operating_profit", "영업이익"),
    ("net_profit", "당기순이익"),
    ("cost_of_sales", "매출원가"),
    ("sga", "판관비"),
]

_BS_ACCOUNTS = [
    ("total_assets", "자산총계"),
    ("total_liabilities", "부채총계"),
    ("total_equity", "자본총계"),
    ("current_assets", "유동자산"),
    ("current_liabilities", "유동부채"),
]

_CF_ACCOUNTS = [
    ("operating_cashflow", "영업활동CF"),
    ("investing_cashflow", "투자활동CF"),
    ("financing_cashflow", "재무활동CF"),
    ("free_cashflow", "잉여현금흐름"),
]

_RATIO_KEYWORDS = {
    "영업이익률": ("operatingMargin", "영업이익률"),
    "순이익률": ("netMargin", "순이익률"),
    "ROE": ("roe", "ROE"),
    "ROA": ("roa", "ROA"),
    "부채비율": ("debtRatio", "부채비율"),
    "유동비율": ("currentRatio", "유동비율"),
    "이자보상배율": ("interestCoverage", "이자보상배율"),
}

_QUESTION_HINTS: dict[str, list[str]] = {
    "IS": ["매출", "영업이익", "순이익", "이익률", "수익", "실적", "비용", "원가", "판관비"],
    "BS": ["자산", "부채", "자본", "유동", "건전", "부실"],
    "CF": ["현금흐름", "현금", "잉여", "배당", "FCF", "cashflow"],
    "ratios": ["비율", "이익률", "ROE", "ROA", "부채비율", "유동비율"],
}


def _detectStatements(question: str) -> list[str]:
    """질문에서 관련 재무제표를 식별."""
    q = question.lower()
    result = []
    for sj, keywords in _QUESTION_HINTS.items():
        if any(k.lower() in q for k in keywords):
            result.append(sj)
    if not result:
        result = ["IS"]  # 기본값
    return result


def _extractLatestPeriod(periods: list[str]) -> str | None:
    """periods 리스트에서 최신 연도 추출."""
    if not periods:
        return None
    # "2024-Q4" → "2024", "2024" → "2024"
    last = periods[-1]
    match = re.match(r"(\d{4})", last)
    return match.group(1) if match else last


_REPORT_HINTS: dict[str, list[str]] = {
    "dividend": ["배당", "DPS", "주주환원"],
    "employee": ["직원", "인력", "고용"],
    "audit": ["감사", "회계"],
    "majorHolder": ["주주", "지분", "대주주"],
    "executive": ["임원", "보수"],
    "treasuryStock": ["자기주식", "자사주"],
}


def _harvestReportFacts(company: Any, question: str) -> list[dict[str, Any]]:
    """report API에서 배당/직원/감사 등 정형 데이터 추출."""
    facts: list[dict[str, Any]] = []
    q = question.lower()
    report = getattr(company, "report", None)
    if report is None:
        return facts

    for apiType, keywords in _REPORT_HINTS.items():
        if not any(k.lower() in q for k in keywords):
            continue
        try:
            data = report.get(apiType)
            if data is None:
                continue
            import polars as pl

            if isinstance(data, pl.DataFrame) and len(data) > 0:
                facts.append(
                    {
                        "metric": f"report_{apiType}",
                        "label": apiType,
                        "value": len(data),
                        "statement": "report",
                        "period": "latest",
                    }
                )
        except (AttributeError, TypeError, ValueError, OSError):
            continue
    return facts


def _harvestSectionsFacts(company: Any, question: str) -> list[dict[str, Any]]:
    """sections topic 존재 여부 + 기간 수."""
    facts: list[dict[str, Any]] = []
    docs = getattr(company, "docs", None)
    if docs is None:
        return facts
    sections = getattr(docs, "sections", None)
    if sections is None:
        return facts
    raw = getattr(sections, "raw", None)
    if raw is None:
        return facts

    try:
        import polars as pl

        if not isinstance(raw, pl.DataFrame) or raw.is_empty():
            return facts
        topics = raw["topic"].unique().to_list() if "topic" in raw.columns else []
        periods = raw["period"].unique().to_list() if "period" in raw.columns else []
        facts.append(
            {
                "metric": "sections_topic_count",
                "label": "sections topic 수",
                "value": len(topics),
                "statement": "sections",
                "period": "all",
            }
        )
        facts.append(
            {
                "metric": "sections_period_count",
                "label": "sections 기간 수",
                "value": len(periods),
                "statement": "sections",
                "period": "all",
            }
        )
    except (ImportError, AttributeError, TypeError, ValueError):
        pass
    return facts


def _harvestInsightFacts(company: Any) -> list[dict[str, Any]]:
    """insight 7영역 등급 추출."""
    facts: list[dict[str, Any]] = []
    insights = getattr(company, "insights", None)
    if insights is None:
        return facts

    try:
        # insights는 dict 또는 object
        if isinstance(insights, dict):
            for area, grade in insights.items():
                if isinstance(grade, (str, int, float)):
                    facts.append(
                        {
                            "metric": f"insight_{area}",
                            "label": f"인사이트 {area}",
                            "value": str(grade),
                            "statement": "insight",
                            "period": "latest",
                        }
                    )
    except (AttributeError, TypeError, ValueError):
        pass
    return facts


def harvestTruth(
    stockCode: str,
    question: str,
    *,
    company: Any = None,
) -> list[dict[str, Any]]:
    """질문에서 관련 모듈 식별 → finance에서 수치 추출.

    Returns:
        [{"metric": "operating_profit", "label": "영업이익",
          "value": 32726000000000, "statement": "IS", "period": "2024"}]
    """
    if company is None:
        from dartlab import Company

        company = Company(stockCode)

    facts: list[dict[str, Any]] = []
    statements = _detectStatements(question)

    # ── 연간 시계열에서 추출 ──────────────────────────────
    annualData = getattr(company, "annual", None)
    if annualData is not None:
        try:
            series, years = annualData
        except (TypeError, ValueError):
            series, years = {}, []

        period = _extractLatestPeriod(years)

        for sj in statements:
            if sj == "ratios":
                continue
            accounts = {"IS": _IS_ACCOUNTS, "BS": _BS_ACCOUNTS, "CF": _CF_ACCOUNTS}.get(sj, [])
            sjData = series.get(sj, {})
            for snakeId, label in accounts:
                vals = sjData.get(snakeId)
                if not vals:
                    continue
                # 최신 non-null 값
                latest = None
                for v in reversed(vals):
                    if v is not None:
                        latest = v
                        break
                if latest is not None:
                    facts.append(
                        {
                            "metric": snakeId,
                            "label": label,
                            "value": latest,
                            "statement": sj,
                            "period": period or "latest",
                        }
                    )

    # ── 분기별 시계열 (분기 질문용) ───────────────────────
    isQuarterly = any(k in question for k in ["분기", "quarterly", "QoQ", "전분기", "Q1", "Q2", "Q3", "Q4"])
    if isQuarterly:
        tsData = getattr(company, "timeseries", None)
        if tsData is not None:
            try:
                tsSeries, tsPeriods = tsData
            except (TypeError, ValueError):
                tsSeries, tsPeriods = {}, []

            if tsPeriods:
                latestQ = tsPeriods[-1]
                for sj in ["IS", "CF"]:
                    sjData = tsSeries.get(sj, {})
                    accounts = {"IS": _IS_ACCOUNTS, "CF": _CF_ACCOUNTS}.get(sj, [])
                    for snakeId, label in accounts:
                        vals = sjData.get(snakeId)
                        if not vals:
                            continue
                        latest = None
                        for v in reversed(vals):
                            if v is not None:
                                latest = v
                                break
                        if latest is not None:
                            facts.append(
                                {
                                    "metric": f"{snakeId}_quarterly",
                                    "label": f"{label}(분기)",
                                    "value": latest,
                                    "statement": f"{sj}_quarterly",
                                    "period": latestQ,
                                }
                            )

    # ── 비율 추출 ────────────────────────────────────────
    if "ratios" in statements:
        ratiosData = getattr(company, "ratios", None)
        if ratiosData is not None:
            try:
                import polars as pl

                if isinstance(ratiosData, pl.DataFrame):
                    # ratios DataFrame에서 최신 컬럼 추출
                    cols = [c for c in ratiosData.columns if c not in ("category", "metric", "label")]
                    if cols:
                        latestCol = cols[-1]
                        for keyword, (metricId, label) in _RATIO_KEYWORDS.items():
                            if keyword.lower() in question.lower():
                                row = ratiosData.filter(pl.col("metric") == metricId)
                                if len(row) > 0:
                                    val = row[0, latestCol]
                                    if val is not None:
                                        facts.append(
                                            {
                                                "metric": metricId,
                                                "label": label,
                                                "value": float(val),
                                                "statement": "ratios",
                                                "period": latestCol,
                                            }
                                        )
            except (ImportError, AttributeError, TypeError, ValueError):
                pass

    # ── report 추출 (배당/직원/감사) ─────────────────────
    facts.extend(_harvestReportFacts(company, question))

    # ── sections 존재 여부 ─────────────────────────────
    facts.extend(_harvestSectionsFacts(company, question))

    # ── insight 등급 ───────────────────────────────────
    facts.extend(_harvestInsightFacts(company))

    return facts


def harvestBatch(
    cases: list[dict[str, Any]],
    *,
    companyCache: dict[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """복수 케이스에 대해 배치 harvest. 종목코드별 Company 캐싱.

    Returns:
        {caseId: [facts]}
    """
    import gc

    if companyCache is None:
        companyCache = {}

    result: dict[str, list[dict[str, Any]]] = {}

    for case in cases:
        caseId = case.get("id", "unknown")
        stockCode = case.get("stockCode")
        question = case.get("question", "")

        if not stockCode:
            result[caseId] = []
            continue

        # Company 캐싱 (최대 3개)
        if stockCode not in companyCache:
            if len(companyCache) >= 3:
                oldest = next(iter(companyCache))
                del companyCache[oldest]
                gc.collect()
            from dartlab import Company

            companyCache[stockCode] = Company(stockCode)

        company = companyCache[stockCode]
        facts = harvestTruth(stockCode, question, company=company)
        result[caseId] = facts

    return result
