"""이벤트 기반 신호 — allFilings 공시 유형 분류.

학술 근거: Tetlock (2007), Boudoukh et al. (2019).
"""

from __future__ import annotations

import logging

from dartlab.quant._helpers import load_allfilings_for_stock, resolve_market

log = logging.getLogger(__name__)

_EVENT_RULES = [
    ("risk", 5, ["소송", "제재", "행정처분", "과징금", "횡령", "배임", "벌금", "위반"]),
    ("mna", 5, ["합병", "인수", "분할", "영업양수", "영업양도"]),
    ("governance", 4, ["대표이사", "이사회", "임원", "사외이사", "감사위원"]),
    ("audit", 4, ["감사", "회계", "내부통제", "감사의견"]),
    ("capital", 3, ["유상증자", "전환사채", "자사주", "감자", "무상증자", "신주인수권", "교환사채"]),
    ("disclosure", 2, ["공시변경", "정정", "기재정정"]),
]


def _classify(report_name: str) -> tuple[str, int]:
    """공시 유형 분류 + 임팩트 스코어."""
    if not report_name:
        return "routine", 1
    for etype, impact, keywords in _EVENT_RULES:
        if any(kw in report_name for kw in keywords):
            return etype, impact
    return "routine", 1


def analyze_event_signal(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """allFilings 이벤트 기반 신호 분석."""
    market = resolve_market(stockCode, market)
    result: dict = {"stockCode": stockCode, "market": market}

    filings = load_allfilings_for_stock(stockCode)
    if filings is None or filings.is_empty():
        return {**result, "error": "allFilings 데이터 없음"}

    report_col = next((c for c in ["report_nm", "report_name", "title"] if c in filings.columns), None)
    date_col = next((c for c in ["rcept_dt", "date", "filing_date"] if c in filings.columns), None)

    if report_col is None:
        return {**result, "error": "공시명 컬럼 없음", "columns": filings.columns}

    events = []
    type_counts: dict[str, int] = {}
    impact_sum = 0

    for row in filings.iter_rows(named=True):
        rname = str(row.get(report_col, ""))
        rdate = str(row.get(date_col, ""))[:10] if date_col else None
        etype, impact = _classify(rname)
        events.append({"date": rdate, "report": rname[:60], "type": etype, "impact": impact})
        type_counts[etype] = type_counts.get(etype, 0) + 1
        impact_sum += impact

    n = len(events)
    result["totalEvents"] = n
    result["eventTypes"] = type_counts
    result["impactScore"] = round(impact_sum / max(n, 1), 2)
    result["events"] = events[-20:]
    result["recentHighImpact"] = [e for e in events[-20:] if e["impact"] >= 4]

    # 종합
    high_impact = sum(1 for e in events if e["impact"] >= 4)
    result["highImpactCount"] = high_impact
    result["eventVerdict"] = "high_activity" if high_impact >= 3 else "moderate" if high_impact >= 1 else "quiet"
    return result
