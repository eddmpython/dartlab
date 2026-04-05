"""공시 텍스트 감성 분석 — Loughran-McDonald 사전 기반.

학술 근거: Loughran & McDonald (2011).
"""

from __future__ import annotations

import logging

from dartlab.quant._helpers import load_docs_for_stock, resolve_market

log = logging.getLogger(__name__)


def analyze_sentiment(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """공시 텍스트 감성 스코어링."""
    market = resolve_market(stockCode, market)
    result: dict = {"stockCode": stockCode, "market": market}

    docs = load_docs_for_stock(stockCode)
    if docs is None or docs.is_empty():
        return {**result, "error": "docs 데이터 없음"}

    from dartlab.quant._lm_dict import NEGATIVE_KR, POSITIVE_KR, UNCERTAINTY_KR

    text_col = next((c for c in ["content", "section_content", "text", "body"] if c in docs.columns), None)
    if text_col is None:
        return {**result, "error": "텍스트 컬럼 없음", "columns": docs.columns}

    period_col = next((c for c in ["period", "bsns_year", "year", "rcept_dt"] if c in docs.columns), None)

    scores = []
    total_pos = total_neg = total_unc = total_words = 0
    neg_counts: dict[str, int] = {}

    texts = docs.get_column(text_col).to_list()
    periods = docs.get_column(period_col).to_list() if period_col else [None] * len(texts)

    for text, period in zip(texts, periods):
        if not isinstance(text, str) or not text.strip():
            continue
        words = text.split()
        nw = len(words)
        if nw == 0:
            continue

        pc = sum(1 for w in words if any(p in w for p in POSITIVE_KR))
        nc = sum(1 for w in words if any(n in w for n in NEGATIVE_KR))
        uc = sum(1 for w in words if any(u in w for u in UNCERTAINTY_KR))

        for w in words:
            for kw in NEGATIVE_KR:
                if kw in w:
                    neg_counts[kw] = neg_counts.get(kw, 0) + 1

        sc = (pc - nc) / (pc + nc + 1)
        scores.append({"period": str(period)[:10] if period else None, "score": round(sc, 4), "pos": pc, "neg": nc, "words": nw})
        total_pos += pc
        total_neg += nc
        total_unc += uc
        total_words += nw

    if not scores:
        return {**result, "error": "분석 가능한 텍스트 없음"}

    overall = (total_pos - total_neg) / (total_pos + total_neg + 1)
    result["sentimentScore"] = round(float(overall), 4)
    result["positiveCount"] = total_pos
    result["negativeCount"] = total_neg
    result["uncertaintyCount"] = total_unc
    result["totalWords"] = total_words
    result["positiveRatio"] = round(total_pos / max(total_words, 1), 6)
    result["negativeRatio"] = round(total_neg / max(total_words, 1), 6)
    result["topNegativeWords"] = [{"word": w, "count": c} for w, c in sorted(neg_counts.items(), key=lambda x: -x[1])[:10]]
    result["timeSeries"] = scores[-20:]
    result["sentimentVerdict"] = "positive" if overall > 0.1 else "negative" if overall < -0.1 else "neutral"
    return result
