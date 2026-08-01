"""거버넌스 품질 정량화.

학술 근거: Gompers et al. (2003), Bebchuk et al. (2009).
데이터: scan report parquet (majorHolder, auditOpinion, executive, executivePayAllTotal).
"""

from __future__ import annotations

import logging

import polars as pl

from dartlab.core.market import resolveMarket
from dartlab.providers._common.auditOpinion import normalizeAuditOpinion
from dartlab.quant.screen.dataAccess import loadScanParquet

log = logging.getLogger(__name__)


def _filterStock(lf, stockCode: str):
    """LazyFrame에서 종목코드 필터링 → DataFrame."""
    if lf is None:
        return None
    schema = lf.collect_schema().names()
    for col in ("stockCode", "종목코드", "corp_code"):
        if col in schema:
            try:
                df = lf.filter(pl.col(col) == stockCode).collect(engine="streaming")
                if not df.is_empty():
                    return df
            except pl.exceptions.ComputeError:
                continue
    return None


def _safeFloat(val) -> float | None:
    if val is None:
        return None
    try:
        s = str(val).replace(",", "").replace("%", "").strip()
        return float(s) if s and s != "-" else None
    except (ValueError, TypeError):
        return None


def _latestAuditOpinion(df: pl.DataFrame | None) -> dict | None:
    """정렬되지 않은 scan 행에서 최신 연간 구조화 감사의견을 고른다."""
    if df is None or df.is_empty() or "adt_opinion" not in df.columns:
        return None
    rows = df.to_dicts()
    if "quarter" in df.columns:
        q4 = [row for row in rows if str(row.get("quarter") or "") == "4분기"]
        if q4:
            rows = q4
    current = [row for row in rows if "당기" in str(row.get("bsns_year") or "")]
    if current:
        rows = current

    observed = []
    for row in rows:
        opinion = normalizeAuditOpinion(row.get("adt_opinion"))
        if opinion is None:
            continue
        observed.append((str(row.get("stlm_dt") or ""), str(row.get("rcept_no") or ""), row, opinion))
    if not observed:
        return None
    _, _, row, opinion = max(observed, key=lambda item: (item[0], item[1]))
    return {
        "status": "observed",
        "opinion": opinion,
        "rawOpinion": row.get("adt_opinion"),
        "fiscalPeriod": row.get("stlm_dt") or row.get("year"),
        "rceptNo": row.get("rcept_no"),
        "source": "DART.adt_opinion",
    }


def calcGovernanceQuant(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """거버넌스 품질 정량화.

    소유집중도·감사의견·이사회 독립성·보수 투명성 4개 하위 점수를 산출하고
    복합 거버넌스 점수(0~100) + 등급(A~F)을 부여한다.

    Parameters
    ----------
    stockCode : str
        종목코드.
    market : str
        "KR" | "US" | "auto". 기본 "auto".

    Returns
    -------
    dict
        stockCode : str — 종목코드
        market : str — 시장
        governanceScore : float | None — 복합 점수 (점, 0~100)
        grade : str — "A" | "B" | "C" | "D" | "F" | "N/A"
        subScores : dict — 하위 점수 (점, 0~100)
            ownership : float — 소유집중도
            audit : float — 감사의견
            boardIndependence : float — 사외이사 비율
            payTransparency : float — 보수 투명성
        maxHolderPct : float — 최대주주 지분율 (%)
        auditOpinion : str — 감사의견 요약
        outsideDirectorRatio : float — 사외이사 비율 (%)
        availableData : list[str] — 사용된 데이터 목록

    Capabilities:
        - 4 sub-축 (소유집중도/감사의견/사외이사 비율/보수 투명성) 점수 → 복합 0~100
        - DART scan 데이터 가용한 sub-축만 사용 (부분 평가 허용)

    Guide:
        한국 governance 4 축. 30~50% 최대주주 = optimal, ≥ 70% = 과집중, < 20% = 분산.

    When:
        Text governance + AI 거버넌스 답변.

    How:
        4 scan parquet (majorHolder/auditOpinion/director/pay) 로드 → sub-점수 → 가중 평균.

    Requires:
        DART scan parquet 가용 (최소 1).

    Raises:
        없음 — 데이터 부재 시 governanceScore=None.

    Example:
        >>> calcGovernanceQuant("005930")["grade"]
        'B'

    See Also:
        - calcSentiment / calcRiskText : 자매 text
        - composite.calcTextComposite : 통합

    AIContext:
        "거버넌스 정량 평가" 답변 시 grade + sub-점수 인용.
    """
    market = resolveMarket(stockCode, market)
    result: dict = {"stockCode": stockCode, "market": market}
    sub_scores: dict[str, float | None] = {}
    available = []

    # 1) majorHolder — 소유집중도
    mh = _filterStock(loadScanParquet("majorHolder", market), stockCode)
    if mh is not None:
        available.append("majorHolder")
        # 최대주주 지분율 찾기
        for col in mh.columns:
            if "지분" in col or "율" in col or "percent" in col.lower():
                vals = [_safeFloat(v) for v in mh.get_column(col).to_list()]
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
    ao = _filterStock(loadScanParquet("auditOpinion", market), stockCode) if market == "KR" else None
    auditEvidence = _latestAuditOpinion(ao)
    if auditEvidence is not None:
        available.append("auditOpinion")
        latest = auditEvidence["opinion"]
        if latest == "적정의견":
            sub_scores["audit"] = 100
        elif latest == "한정의견":
            sub_scores["audit"] = 40
        elif latest in ("부적정의견", "의견거절"):
            sub_scores["audit"] = 0
        result["auditOpinion"] = latest
        result["auditOpinionEvidence"] = auditEvidence

    # 3) executive — 이사회 구성
    ex = _filterStock(loadScanParquet("executive", market), stockCode)
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
    ep = _filterStock(loadScanParquet("executivePayAllTotal", market), stockCode)
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
