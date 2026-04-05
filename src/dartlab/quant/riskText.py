"""리스크 텍스트 델타 — 리스크 팩터 출현/소멸 추적.

학술 근거: Campbell et al. (2014) — Information Content of Mandatory Risk Factor Disclosures.
"""

from __future__ import annotations

import logging

from dartlab.quant._helpers import load_docs_for_stock, resolve_market

log = logging.getLogger(__name__)

_RISK_KEYWORDS = {
    "위험", "리스크", "불확실", "소송", "분쟁", "제재", "우발", "충당",
    "손상", "감액", "부실", "부도", "파산", "유동성위기", "채무불이행",
    "횡령", "배임", "과징금", "제소", "손해배상",
}


def analyze_risk_text(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """리스크 팩터 텍스트 델타 분석."""
    market = resolve_market(stockCode, market)
    result: dict = {"stockCode": stockCode, "market": market}

    docs = load_docs_for_stock(stockCode)
    if docs is None or docs.is_empty():
        return {**result, "error": "docs 데이터 없음"}

    text_col = next((c for c in ["content", "section_content", "text", "body"] if c in docs.columns), None)
    if text_col is None:
        return {**result, "error": "텍스트 컬럼 없음"}

    period_col = next((c for c in ["period", "bsns_year", "year", "rcept_dt"] if c in docs.columns), None)

    # 기간별 리스크 키워드 집계
    period_risks: dict[str, dict[str, int]] = {}
    texts = docs.get_column(text_col).to_list()
    periods = docs.get_column(period_col).to_list() if period_col else [str(i) for i in range(len(texts))]

    total_mentions = 0
    for text, period in zip(texts, periods):
        if not isinstance(text, str):
            continue
        pkey = str(period)[:10] if period else "unknown"
        if pkey not in period_risks:
            period_risks[pkey] = {}
        for kw in _RISK_KEYWORDS:
            count = text.count(kw)
            if count > 0:
                period_risks[pkey][kw] = period_risks[pkey].get(kw, 0) + count
                total_mentions += count

    if not period_risks:
        return {**result, "error": "리스크 키워드 없음"}

    sorted_periods = sorted(period_risks.keys())
    # 기간별 총 멘션 수
    ts = [{"period": p, "mentions": sum(period_risks[p].values()), "keywords": list(period_risks[p].keys())} for p in sorted_periods]

    result["totalMentions"] = total_mentions
    result["riskTimeSeries"] = ts[-10:]

    # 추세 감지
    if len(ts) >= 3:
        counts = [t["mentions"] for t in ts]
        recent_avg = sum(counts[-2:]) / 2
        older_avg = sum(counts[:-2]) / max(len(counts) - 2, 1)
        if recent_avg > older_avg * 1.3:
            result["trend"] = "increasing"
        elif recent_avg < older_avg * 0.7:
            result["trend"] = "decreasing"
        else:
            result["trend"] = "stable"
    else:
        result["trend"] = "insufficient_data"

    # 신규 리스크: 최근에만 등장, 이전에 없던 키워드
    if len(sorted_periods) >= 2:
        latest_kw = set(period_risks[sorted_periods[-1]].keys())
        older_kw = set()
        for p in sorted_periods[:-1]:
            older_kw.update(period_risks[p].keys())
        new_risks = latest_kw - older_kw
        result["newRisks"] = list(new_risks)
    else:
        result["newRisks"] = []

    # 리스크 점수 (멘션 밀도 기반)
    total_words = sum(len(t.split()) for t in texts if isinstance(t, str))
    risk_density = total_mentions / max(total_words, 1) * 1000
    result["riskScore"] = round(risk_density, 4)
    result["riskGrade"] = "high" if risk_density > 5 else "medium" if risk_density > 2 else "low"
    return result
