"""주주환원 3축 report 스캔 — 배당, 자사주, 증자/감자."""

from __future__ import annotations

import polars as pl

from dartlab.scan._helpers import (
    parse_date_year,
    parse_num,
    scan_parquets,
)

# ── 배당 ──

DPS_KEYS = {"주당 현금배당금(원)", "주당현금배당금(원)", "주당현금배당금", "현금배당금(원)"}
YIELD_KEYS = {"현금배당수익률(%)", "현금배당수익률"}
TOTAL_KEYS = {"현금배당금총액(백만원)", "현금배당금총액"}


def scan_dividend() -> dict[str, dict]:
    """dividend → {종목코드: {배당여부, DPS, 배당수익률, 배당총액_백만}}.

    최신 연도 Q4 기준.  DPS 행이 100개 이상인 연도를 선택.
    """
    raw = scan_parquets(
        "dividend",
        ["stockCode", "year", "quarter", "se", "thstrm"],
    )
    if raw.is_empty():
        return {}

    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        q4 = sub.filter(pl.col("quarter") == "4분기")
        target = q4 if not q4.is_empty() else sub
        dps_ok = target.filter(
            pl.col("se").is_in(list(DPS_KEYS))
            & pl.col("thstrm").is_not_null()
            & (pl.col("thstrm") != "-")
            & (pl.col("thstrm") != "")
        ).shape[0]
        if dps_ok >= 100:
            latest_year = y
            break
    if latest_year is None:
        return {}

    latest = raw.filter(pl.col("year") == latest_year)
    q4 = latest.filter(pl.col("quarter") == "4분기")
    if not q4.is_empty():
        latest = q4

    result: dict[str, dict] = {}
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        dps = None
        div_yield = None
        total_div = None

        for row in group.iter_rows(named=True):
            se = row.get("se", "")
            if not se:
                continue
            val = parse_num(row.get("thstrm"))
            if se in DPS_KEYS and val is not None and val > 0:
                if dps is None or val > dps:
                    dps = val
            elif se in YIELD_KEYS and val is not None and val > 0:
                if div_yield is None or val > div_yield:
                    div_yield = val
            elif se in TOTAL_KEYS and val is not None and val > 0:
                total_div = val

        result[code_val] = {
            "배당여부": dps is not None and dps > 0,
            "DPS": dps or 0.0,
            "배당수익률": div_yield or 0.0,
            "배당총액_백만": total_div or 0.0,
        }
    return result


# ── 자사주 ──


def scan_treasury_stock() -> dict[str, dict]:
    """treasuryStock → {종목코드: {자사주보유, 당기취득}}."""
    raw = scan_parquets(
        "treasuryStock",
        ["stockCode", "year", "quarter", "trmend_qy", "change_qy_acqs"],
    )
    if raw.is_empty():
        return {}

    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col("trmend_qy").is_not_null() & (pl.col("trmend_qy") != "-")).shape[0]
        if ok >= 300:
            latest_year = y
            break
    if latest_year is None:
        return {}

    latest = raw.filter(pl.col("year") == latest_year)
    result: dict[str, dict] = {}
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        total_held = 0
        total_acqs = 0
        for row in group.iter_rows(named=True):
            held = parse_num(row.get("trmend_qy"))
            acqs = parse_num(row.get("change_qy_acqs"))
            if held and held > 0:
                total_held += int(held)
            if acqs and acqs > 0:
                total_acqs += int(acqs)
        result[code_val] = {
            "자사주보유": total_held > 0,
            "당기취득": total_acqs > 0,
        }
    return result


# ── 증자/감자 ──

INCREASE_TYPES = {
    "유상증자(주주배정)",
    "유상증자(제3자배정)",
    "유상증자(일반공모)",
    "전환권행사",
    "신주인수권행사",
    "주식매수선택권행사",
    "무상증자",
}


def scan_capital_change() -> dict[str, dict]:
    """capitalChange → {종목코드: {최근증자: bool}}.

    최근 3년(2023~) 이내 증자(INCREASE_TYPES) 여부.
    """
    raw = scan_parquets(
        "capitalChange",
        ["stockCode", "year", "quarter", "isu_dcrs_stle", "isu_dcrs_de"],
    )
    if raw.is_empty():
        return {}

    valid = raw.filter(
        pl.col("isu_dcrs_stle").is_not_null() & (pl.col("isu_dcrs_stle") != "-") & (pl.col("isu_dcrs_stle") != "")
    )

    result: dict[str, dict] = {}
    for code, group in valid.group_by("stockCode"):
        code_val = code[0]
        recent_increase = False
        for row in group.iter_rows(named=True):
            stle = row.get("isu_dcrs_stle", "")
            event_year = parse_date_year(row.get("isu_dcrs_de"))
            if stle in INCREASE_TYPES and event_year and event_year >= 2023:
                recent_increase = True
                break
        result[code_val] = {"최근증자": recent_increase}
    return result
