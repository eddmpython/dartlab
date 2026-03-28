"""부채 구조 스캔 — corporateBond 만기 + finance BS 부채비율."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan._helpers import parse_num, scan_parquets


def scan_bonds() -> dict[str, dict]:
    """corporateBond → {종목코드: {사채잔액, 단기잔액, 단기비중}}.

    합계(remndr_exprtn2) 행 기준.  잔액이 0보다 큰 기업만 반환.
    """
    raw = scan_parquets(
        "corporateBond",
        ["stockCode", "year", "quarter", "remndr_exprtn2", "sm", "yy1_below"],
    )
    if raw.is_empty():
        return {}

    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col("sm").is_not_null() & (pl.col("sm") != "-") & (pl.col("sm") != "")).shape[0]
        if ok >= 200:
            latest_year = y
            break
    if latest_year is None:
        return {}

    latest = raw.filter(pl.col("year") == latest_year)
    totals = latest.filter(pl.col("remndr_exprtn2") == "합계")
    if totals.is_empty() or totals["stockCode"].n_unique() < 50:
        totals = latest

    result: dict[str, dict] = {}
    for code, group in totals.group_by("stockCode"):
        code_val = code[0]
        total_amount = 0
        short_term = 0
        for row in group.iter_rows(named=True):
            sm = parse_num(row.get("sm"))
            y1 = parse_num(row.get("yy1_below"))
            if sm and sm > 0:
                total_amount = max(total_amount, sm)
            if y1 and y1 > 0:
                short_term = max(short_term, y1)
        if total_amount > 0:
            result[code_val] = {
                "사채잔액": total_amount,
                "단기잔액": short_term,
                "단기비중": round(short_term / total_amount * 100, 1),
            }
    return result


# ── finance BS 부채비율 ──

LIABILITIES_IDS = {"Liabilities", "liabilities", "ifrs-full_Liabilities", "dart_Liabilities"}
LIABILITIES_NMS = {"부채총계", "부채 총계"}
EQUITY_IDS = {"Equity", "equity", "ifrs-full_Equity", "dart_Equity"}
EQUITY_NMS = {"자본총계", "자본 총계"}


def scan_short_debt() -> dict[str, dict]:
    """shortTermBond + commercialPaper → {종목코드: {단기사채잔액, CP잔액, 단기채무합계}}.

    회사채(corporateBond)와 별도로, 기업어음/단기사채의 실질 단기 부채 노출을 측정한다.
    """
    stb = scan_parquets(
        "shortTermBond",
        ["stockCode", "year", "quarter", "sm"],
    )
    cp = scan_parquets(
        "commercialPaper",
        ["stockCode", "year", "quarter", "sm"],
    )

    result: dict[str, dict] = {}

    # 단기사채
    if not stb.is_empty():
        for code, group in stb.group_by("stockCode"):
            codeVal = code[0]
            best = 0
            for row in group.iter_rows(named=True):
                val = parse_num(row.get("sm"))
                if val and val > best:
                    best = val
            if best > 0:
                result.setdefault(codeVal, {})["단기사채잔액"] = best

    # 기업어음
    if not cp.is_empty():
        for code, group in cp.group_by("stockCode"):
            codeVal = code[0]
            best = 0
            for row in group.iter_rows(named=True):
                val = parse_num(row.get("sm"))
                if val and val > best:
                    best = val
            if best > 0:
                result.setdefault(codeVal, {})["CP잔액"] = best

    # 합산
    for code, d in result.items():
        d["단기채무합계"] = (d.get("단기사채잔액") or 0) + (d.get("CP잔액") or 0)

    return result


def scan_debt_mix() -> dict[str, dict]:
    """finance BS → {종목코드: {총부채, 부채비율}}.

    부채비율 = 총부채 / 자본총계 x 100.
    scan/finance.parquet 프리빌드가 있으면 단일 파일에서 즉시 필터.
    """
    from dartlab.scan._helpers import _ensureScanData

    scanDir = _ensureScanData()
    scanPath = scanDir / "finance.parquet"

    if scanPath.exists():
        try:
            return _debtMixFromMerged(scanPath)
        except (pl.exceptions.PolarsError, OSError):
            pass

    # fallback: 종목별 순회
    from dartlab.core.dataLoader import _dataDir

    finance_dir = Path(_dataDir("finance"))
    parquet_files = sorted(finance_dir.glob("*.parquet"))

    result: dict[str, dict] = {}
    for pf in parquet_files:
        code = pf.stem
        try:
            bs = (
                pl.scan_parquet(str(pf))
                .filter(
                    (pl.col("sj_div") == "BS")
                    & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
                )
                .collect()
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        if bs.is_empty() or "account_id" not in bs.columns:
            continue
        cfs = bs.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else bs

        years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = target.filter(pl.col("bsns_year") == years[0])

        liab = None
        equity = None
        for row in latest.iter_rows(named=True):
            aid = row.get("account_id", "")
            anm = row.get("account_nm", "")
            val = parse_num(row.get("thstrm_amount"))
            if (aid in LIABILITIES_IDS or anm in LIABILITIES_NMS) and val:
                if liab is None or val > liab:
                    liab = val
            elif (aid in EQUITY_IDS or anm in EQUITY_NMS) and val:
                if equity is None or val > equity:
                    equity = val

        if liab and liab > 0:
            debt_ratio = (liab / equity * 100) if equity and equity > 0 else None
            result[code] = {
                "총부채": liab,
                "부채비율": round(debt_ratio, 1) if debt_ratio else None,
            }
    return result


def _debtMixFromMerged(scanPath: Path) -> dict[str, dict]:
    """합산 finance parquet에서 부채/자본 추출."""
    scCol = "stockCode" if "stockCode" in pl.scan_parquet(str(scanPath)).collect_schema().names() else "stock_code"

    bs = (
        pl.scan_parquet(str(scanPath))
        .filter(
            (pl.col("sj_div") == "BS")
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
        )
        .collect()
    )
    if bs.is_empty() or "account_id" not in bs.columns:
        return {}

    cfs = bs.filter(pl.col("fs_nm").str.contains("연결"))
    target = cfs if not cfs.is_empty() else bs

    # 종목별 최신 연도
    latestYear = target.group_by(scCol).agg(pl.col("bsns_year").max().alias("_maxYear"))
    target = target.join(latestYear, on=scCol).filter(pl.col("bsns_year") == pl.col("_maxYear")).drop("_maxYear")

    allLiabIds = LIABILITIES_IDS | LIABILITIES_NMS
    allEquityIds = EQUITY_IDS | EQUITY_NMS

    liabRows = target.filter(
        pl.col("account_id").is_in(list(LIABILITIES_IDS)) | pl.col("account_nm").is_in(list(LIABILITIES_NMS))
    )
    eqRows = target.filter(pl.col("account_id").is_in(list(EQUITY_IDS)) | pl.col("account_nm").is_in(list(EQUITY_NMS)))

    liabMap: dict[str, float] = {}
    for row in liabRows.iter_rows(named=True):
        code = row.get(scCol, "")
        val = parse_num(row.get("thstrm_amount"))
        if code and val and (code not in liabMap or val > liabMap[code]):
            liabMap[code] = val

    eqMap: dict[str, float] = {}
    for row in eqRows.iter_rows(named=True):
        code = row.get(scCol, "")
        val = parse_num(row.get("thstrm_amount"))
        if code and val and (code not in eqMap or val > eqMap[code]):
            eqMap[code] = val

    result: dict[str, dict] = {}
    for code, liab in liabMap.items():
        if liab > 0:
            equity = eqMap.get(code)
            debt_ratio = (liab / equity * 100) if equity and equity > 0 else None
            result[code] = {
                "총부채": liab,
                "부채비율": round(debt_ratio, 1) if debt_ratio else None,
            }
    return result
