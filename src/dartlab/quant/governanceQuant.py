"""거버넌스 품질 정량화.

학술 근거: Gompers et al. (2003), Bebchuk et al. (2009).
데이터: scan report parquet (majorHolder, auditOpinion, executive, executivePayAllTotal).
"""

from __future__ import annotations

import logging

import polars as pl

from dartlab.quant._helpers import load_scan_parquet, resolve_market

log = logging.getLogger(__name__)


def _filter_stock(lf, stockCode: str):
    """LazyFrame에서 종목코드 필터링 → DataFrame."""
    if lf is None:
        return None
    schema = lf.collect_schema().names()
    for col in ("stockCode", "종목코드", "corp_code"):
        if col in schema:
            try:
                df = lf.filter(pl.col(col) == stockCode).collect()
                if not df.is_empty():
                    return df
            except pl.exceptions.ComputeError:
                continue
    return None


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        s = str(val).replace(",", "").replace("%", "").strip()
        return float(s) if s and s != "-" else None
    except (ValueError, TypeError):
        return None


def analyze_governance_quant(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """거버넌스 품질 정량화."""
    market = resolve_market(stockCode, market)
    result: dict = {"stockCode": stockCode, "market": market}
    sub_scores: dict[str, float | None] = {}
    available = []

    # 1) majorHolder — 소유집중도
    mh = _filter_stock(load_scan_parquet("majorHolder", market), stockCode)
    if mh is not None:
        available.append("majorHolder")
        # 최대주주 지분율 찾기
        for col in mh.columns:
            if "지분" in col or "율" in col or "percent" in col.lower():
                vals = [_safe_float(v) for v in mh.get_column(col).to_list()]
                vals = [v for v in vals if v is not None]
                if vals:
                    max_pct = max(vals)
                    # 30-50% = 양호, >70% = 과도 집중, <20% = 분산
                    if 25 <= max_pct <= 55:
                        sub_scores["ownership"] = 80
                    elif max_pct > 70:
                        sub_scores["ownership"] = 30
                    elif max_pct < 15:
                        sub_scores["ownership"] = 50
                    else:
                        sub_scores["ownership"] = 60
                    result["maxHolderPct"] = round(max_pct, 2)
                    break

    # 2) auditOpinion — 감사의견 품질
    ao = _filter_stock(load_scan_parquet("auditOpinion", market), stockCode)
    if ao is not None:
        available.append("auditOpinion")
        for col in ao.columns:
            if "의견" in col or "opinion" in col.lower():
                opinions = ao.get_column(col).to_list()
                latest = str(opinions[-1]) if opinions else ""
                if "적정" in latest or "unqualified" in latest.lower():
                    sub_scores["audit"] = 100
                elif "한정" in latest or "qualified" in latest.lower():
                    sub_scores["audit"] = 40
                elif "부적정" in latest or "거절" in latest:
                    sub_scores["audit"] = 0
                else:
                    sub_scores["audit"] = 70
                result["auditOpinion"] = latest[:20]
                break

    # 3) executive — 이사회 구성
    ex = _filter_stock(load_scan_parquet("executive", market), stockCode)
    if ex is not None:
        available.append("executive")
        n_total = len(ex)
        # 사외이사 비율 추정
        outside = 0
        for col in ex.columns:
            if "사외" in col or "outside" in col.lower():
                outside = sum(1 for v in ex.get_column(col).to_list() if v and "사외" in str(v))
                break
        if n_total > 0:
            ratio = outside / n_total * 100
            sub_scores["boardIndependence"] = min(ratio * 2, 100)  # 50%면 100점
            result["outsideDirectorRatio"] = round(ratio, 1)

    # 4) executivePayAllTotal — 보수
    ep = _filter_stock(load_scan_parquet("executivePayAllTotal", market), stockCode)
    if ep is not None:
        available.append("executivePayAllTotal")
        # 보수 데이터가 있으면 적정 수준 평가 (존재 자체가 투명성)
        sub_scores["payTransparency"] = 70

    result["availableData"] = available

    # 복합 점수
    if sub_scores:
        composite = sum(sub_scores.values()) / len(sub_scores)
        result["governanceScore"] = round(composite, 1)
        result["subScores"] = {k: round(v, 1) for k, v in sub_scores.items()}
        if composite >= 80:
            result["grade"] = "A"
        elif composite >= 60:
            result["grade"] = "B"
        elif composite >= 40:
            result["grade"] = "C"
        elif composite >= 20:
            result["grade"] = "D"
        else:
            result["grade"] = "F"
    else:
        result["governanceScore"] = None
        result["grade"] = "N/A"
        result["error"] = "거버넌스 데이터 불충분"

    return result
