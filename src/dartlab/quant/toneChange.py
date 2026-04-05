"""기간별 공시 톤 변화 감지.

학술 근거: Loughran & McDonald (2016) — Textual Analysis in Accounting and Finance.
"""

from __future__ import annotations

import logging

from dartlab.quant._helpers import load_changes_for_stock, resolve_market

log = logging.getLogger(__name__)


def analyze_tone_change(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """기간별 공시 톤 변화 분석."""
    market = resolve_market(stockCode, market)
    result: dict = {"stockCode": stockCode, "market": market}

    changes = load_changes_for_stock(stockCode)
    if changes is None or changes.is_empty():
        return {**result, "error": "changes 데이터 없음"}

    from dartlab.quant._lm_dict import NEGATIVE_KR, POSITIVE_KR

    text_col = next((c for c in ["preview", "content", "text", "sectionTitle"] if c in changes.columns), None)
    if text_col is None:
        return {**result, "error": "텍스트 컬럼 없음", "columns": changes.columns}

    period_col = next((c for c in ["toPeriod", "period", "bsns_year"] if c in changes.columns), None)

    # 기간별 감성 점수
    period_scores: dict[str, dict] = {}
    texts = changes.get_column(text_col).to_list()
    periods = changes.get_column(period_col).to_list() if period_col else [str(i) for i in range(len(texts))]

    for text, period in zip(texts, periods):
        if not isinstance(text, str) or not text.strip():
            continue
        pkey = str(period)[:10] if period else "unknown"
        words = text.split()
        pc = sum(1 for w in words if any(p in w for p in POSITIVE_KR))
        nc = sum(1 for w in words if any(n in w for n in NEGATIVE_KR))
        sc = (pc - nc) / (pc + nc + 1)

        if pkey not in period_scores:
            period_scores[pkey] = {"score": 0.0, "count": 0, "neg_words": set()}
        period_scores[pkey]["score"] += sc
        period_scores[pkey]["count"] += 1
        for w in words:
            for kw in NEGATIVE_KR:
                if kw in w:
                    period_scores[pkey]["neg_words"].add(kw)

    if len(period_scores) < 2:
        return {**result, "error": f"기간 부족 ({len(period_scores)}개)", "periods": list(period_scores.keys())}

    # 평균 점수로 정규화
    sorted_periods = sorted(period_scores.keys())
    for p in sorted_periods:
        s = period_scores[p]
        s["avgScore"] = s["score"] / max(s["count"], 1)

    # 연속 기간 톤 변화
    shifts = []
    for i in range(1, len(sorted_periods)):
        prev_p = sorted_periods[i - 1]
        curr_p = sorted_periods[i]
        prev_sc = period_scores[prev_p]["avgScore"]
        curr_sc = period_scores[curr_p]["avgScore"]
        shift = curr_sc - prev_sc
        new_neg = period_scores[curr_p]["neg_words"] - period_scores[prev_p]["neg_words"]
        shifts.append({
            "from": prev_p, "to": curr_p,
            "shift": round(shift, 4),
            "newNegatives": list(new_neg)[:10],
        })

    latest_shift = shifts[-1]["shift"] if shifts else 0
    result["toneShift"] = round(latest_shift, 4)
    result["magnitude"] = round(abs(latest_shift), 4)
    result["direction"] = "악화" if latest_shift < -0.05 else "개선" if latest_shift > 0.05 else "유지"
    result["periods"] = shifts[-5:]
    result["totalPeriods"] = len(sorted_periods)
    return result
