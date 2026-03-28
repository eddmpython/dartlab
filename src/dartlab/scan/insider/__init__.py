"""내부자 지분 변동 + 자기주식 — 경영권 안정성 분석."""

from __future__ import annotations

import polars as pl

from dartlab.scan._helpers import find_latest_year, parse_num, scan_parquets


def _scanHolderChange() -> dict[str, dict]:
    """majorHolder 2개년 비교 → 종목별 최대주주 지분 변동."""
    raw = scan_parquets(
        "majorHolder",
        ["stockCode", "year", "quarter", "bsis_posesn_stock_qota_rt"],
    )
    if raw.is_empty():
        return {}

    years = sorted(raw["year"].unique().to_list(), reverse=True)
    # 유효 데이터 있는 최신 2개 연도
    validYears: list[str] = []
    for y in years:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(
            pl.col("bsis_posesn_stock_qota_rt").is_not_null() & (pl.col("bsis_posesn_stock_qota_rt") != "-")
        ).shape[0]
        if ok >= 500:
            validYears.append(y)
            if len(validYears) == 2:
                break

    if not validYears:
        return {}

    def _maxPct(group: pl.DataFrame) -> float | None:
        vals = []
        for row in group.iter_rows(named=True):
            v = parse_num(row.get("bsis_posesn_stock_qota_rt"))
            if v is not None and 0 <= v <= 100:
                vals.append(v)
        return max(vals) if vals else None

    result: dict[str, dict] = {}
    for code in raw["stockCode"].unique().to_list():
        sub = raw.filter(pl.col("stockCode") == code)
        newSub = sub.filter(pl.col("year") == validYears[0])
        newPct = _maxPct(newSub) if not newSub.is_empty() else None
        if newPct is None:
            continue

        entry: dict = {"pct": round(newPct, 2)}

        if len(validYears) >= 2:
            oldSub = sub.filter(pl.col("year") == validYears[1])
            oldPct = _maxPct(oldSub) if not oldSub.is_empty() else None
            if oldPct is not None:
                entry["prevPct"] = round(oldPct, 2)
                entry["change"] = round(newPct - oldPct, 2)

        result[code] = entry

    return result


def _scanTreasuryStock() -> dict[str, dict]:
    """treasuryStock → 종목별 자기주식 현황."""
    raw = scan_parquets(
        "treasuryStock",
        ["stockCode", "year", "quarter", "stock_knd", "acqs_mth1", "acqs_mth2", "acqs_mth3", "bsis_posesn_stock_co"],
    )
    if raw.is_empty():
        return {}

    latestYear = find_latest_year(raw, "bsis_posesn_stock_co", 100)
    if latestYear is None:
        return {}

    result: dict[str, dict] = {}
    sub = raw.filter(pl.col("year") == latestYear)
    for code in sub["stockCode"].unique().to_list():
        grp = sub.filter(pl.col("stockCode") == code)
        totalShares = 0
        for row in grp.iter_rows(named=True):
            v = parse_num(row.get("bsis_posesn_stock_co"))
            if v is not None and v > 0:
                totalShares += int(v)
        if totalShares > 0:
            result[code] = {"treasuryShares": totalShares}

    return result


def scanInsider() -> pl.DataFrame:
    """종목별 내부자 지분 변동 + 자기주식 종합.

    컬럼: stockCode, holderPct, holderChange, treasuryShares, stability
    """
    holderMap = _scanHolderChange()
    treasuryMap = _scanTreasuryStock()

    allCodes = set(holderMap.keys()) | set(treasuryMap.keys())
    if not allCodes:
        return pl.DataFrame()

    rows: list[dict] = []
    for code in allCodes:
        h = holderMap.get(code, {})
        t = treasuryMap.get(code, {})

        pct = h.get("pct")
        change = h.get("change")
        treasuryShares = t.get("treasuryShares")

        # 경영권 안정성 판단
        if pct is not None and pct >= 50:
            stability = "안정"
        elif pct is not None and pct >= 30:
            stability = "보통"
        elif pct is not None and pct >= 20:
            stability = "취약"
        elif pct is not None:
            stability = "위험"
        else:
            stability = "미확인"

        # 대규모 변동 시 경고
        if change is not None and change <= -5:
            stability = "경고"

        rows.append(
            {
                "stockCode": code,
                "holderPct": pct,
                "holderChange": change,
                "treasuryShares": treasuryShares,
                "stability": stability,
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()
