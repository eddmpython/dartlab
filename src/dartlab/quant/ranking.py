"""멀티팩터 복합 순위 (횡단면).

학술 근거: Asness et al. (2013) — Value and Momentum Everywhere.
"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

from dartlab.quant._helpers import load_scan_parquet

log = logging.getLogger(__name__)


def _parse(val) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _load_account(lf: pl.LazyFrame, sj: str, account: str, year: str) -> dict[str, float]:
    """특정 계정의 전종목 금액 추출. LazyFrame 필터 → collect."""
    # 연결 + 해당 연도 + 계정
    try:
        df = (
            lf.filter(pl.col("bsns_year") == year)
            .filter(pl.col("fs_nm").str.contains("연결"))
            .filter(pl.col("sj_div") == sj)
            .filter(pl.col("account_nm") == account)
            .select("stockCode", "thstrm_amount")
            .collect()
        )
    except Exception:
        df = None

    # fallback: 연결 없으면 전체
    if df is None or df.is_empty():
        try:
            df = (
                lf.filter(pl.col("bsns_year") == year)
                .filter(pl.col("sj_div") == sj)
                .filter(pl.col("account_nm") == account)
                .select("stockCode", "thstrm_amount")
                .collect()
            )
        except Exception:
            return {}

    if df is None or df.is_empty():
        return {}

    result = {}
    for row in df.iter_rows(named=True):
        code = row.get("stockCode")
        val = _parse(row.get("thstrm_amount"))
        if code and val is not None and code not in result:
            result[code] = val
    return result


def analyze_ranking(*, market: str = "KR", stockCode: str | None = None, **kwargs) -> dict:
    """전종목 멀티팩터 복합 순위."""
    result: dict = {"market": market}

    lf = load_scan_parquet("finance", market)
    if lf is None:
        return {**result, "error": "finance.parquet 없음"}

    # 최신 연도 확인
    try:
        years = lf.select("bsns_year").unique().collect().to_series().sort(descending=True).to_list()
    except Exception as e:
        return {**result, "error": str(e)}

    if not years:
        return {**result, "error": "연도 데이터 없음"}

    # 데이터가 풍부한 연도 선택 (최신 → fallback)
    year = None
    for y in years:
        assets_test = _load_account(lf, "BS", "자산총계", y)
        if len(assets_test) >= 100:
            year = y
            break
    if year is None:
        year = years[0]
    result["year"] = year

    # 계정별 전종목 추출 (LazyFrame 필터로 메모리 안전)
    sales = _load_account(lf, "IS", "매출액", year)
    op = _load_account(lf, "IS", "영업이익", year)
    ni = _load_account(lf, "IS", "당기순이익", year)
    assets = _load_account(lf, "BS", "자산총계", year)
    debt = _load_account(lf, "BS", "부채총계", year)

    # 공통 종목
    all_codes = set(sales) & set(assets)
    if not all_codes:
        return {**result, "error": "공통 종목 없음"}

    # 지표 계산
    ranked = []
    for code in all_codes:
        s = sales.get(code, 0)
        o = op.get(code)
        n = ni.get(code)
        a = assets.get(code, 0)
        d = debt.get(code, 0)

        margin = (o / s * 100) if s > 0 and o is not None else None
        roa = (n / a * 100) if a > 0 and n is not None else None
        dr = (d / a * 100) if a > 0 else None

        if margin is not None or roa is not None:
            ranked.append({
                "stockCode": code,
                "opMargin": round(margin, 2) if margin else None,
                "ROA": round(roa, 2) if roa else None,
                "debtRatio": round(dr, 2) if dr else None,
            })

    if not ranked:
        return {**result, "error": "순위 산출 가능 종목 없음"}

    # 백분위 순위
    n = len(ranked)
    margins = np.array([r["opMargin"] or 0 for r in ranked])
    roas = np.array([r["ROA"] or 0 for r in ranked])
    debts = np.array([r["debtRatio"] or 100 for r in ranked])

    m_rank = np.argsort(np.argsort(-margins)) / max(n - 1, 1)
    r_rank = np.argsort(np.argsort(-roas)) / max(n - 1, 1)
    d_rank = np.argsort(np.argsort(debts)) / max(n - 1, 1)
    composites = (m_rank + r_rank + d_rank) / 3
    order = np.argsort(-composites)

    for i, idx in enumerate(order):
        ranked[idx]["compositeScore"] = round(float(composites[idx]), 4)
        ranked[idx]["rank"] = i + 1

    sorted_ranked = sorted(ranked, key=lambda x: x.get("rank", 9999))
    result["totalStocks"] = n

    if stockCode:
        target = [r for r in sorted_ranked if r["stockCode"] == stockCode]
        result["target"] = target[0] if target else None
        result["rankings"] = sorted_ranked[:10]
    else:
        result["rankings"] = sorted_ranked[:50]

    return result
