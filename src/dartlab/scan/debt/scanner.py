"""부채 구조 스캔 — corporateBond 만기 + finance BS 부채비율."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan.io.parquet import latestDataRows, parseNumStr, scanParquets


def scanBonds() -> dict[str, dict]:
    """전종목 사채 잔액 스캔.

    합계(remndr_exprtn2) 행 기준. 잔액이 0보다 큰 기업만 반환.

    Returns
    -------
    dict[str, dict]
        {종목코드: info} 매핑. 각 info:
            사채잔액 : float — 사채 총잔액 (백만원)
            단기잔액 : float — 1년 이내 만기 잔액 (백만원)
            단기비중 : float — 단기잔액/사채잔액 (%)

    Capabilities:
        - 종목별 사채잔액 / 단기사채 (CP 포함) / 부채비율 추출. ``scanDebt`` 의 sub-scanner.

    AIContext:
        ``scanDebt`` 내부 사용. AI agent 가 직접 호출하지 않음.

    Guide:
        - 사채잔액 0 인 종목은 결과 dict 에서 제외.
        - 단기비중 = 단기잔액 / 사채잔액 (%). > 50 % 면 단기 리파이낸싱 리스크.

    When:
        ``scanDebt`` 진행 단계 안에서.

    How:
        report parquet → 종목별 group → 합계 row 또는 만기별 row 합산.

    Requires:
        - 로컬 ``data/dart/scan/report/{corporateBond,shortTermBond}.parquet`` 또는
          ``data/dart/scan/finance.parquet``

    SeeAlso:
        - :func:`dartlab.scan.debt.scanDebt` — sub-scanner 통합

    Raises
    ------
    polars.PolarsError
        corporateBond report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.debt.scanner import scanBonds
    >>> bonds = scanBonds()
    >>> bonds.get("005930", {}).get("사채잔액")
    """
    raw = scanParquets(
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
            sm = parseNumStr(row.get("sm"))
            y1 = parseNumStr(row.get("yy1_below"))
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


def scanDebtSecurities() -> dict[str, dict]:
    """전종목 채무증권 발행실적 스캔 (조달활동 강도 + 조달비용).

    debtSecurities apiType 에서 종목별 최신 연도 채무증권(회사채 등) 발행 액면총액 합계와
    평균 표면이자율을 집계한다. 발행액이 클수록 시장성 차입 조달 의존이 크고, 이자율은 조달비용.

    Returns
    -------
    dict[str, dict]
        {종목코드: {채무증권발행액(원), 채무증권평균이자율(%)|None}}. 발행 없는 종목 제외.

    Capabilities:
        - debtSecurities report 프리빌드에서 종목별 최신연도 액면총액 합산 + 이자율 평균. scanDebt sub-scanner.

    AIContext:
        ``scanDebt`` 내부. 시장성 차입 조달 규모/비용 스크리닝 source.

    Guide:
        - 액면총액 0 종목 제외. 이자율은 0~30% 범위만 (이상치 방어).

    When:
        ``scanDebt`` 진행 단계 안에서.

    How:
        report parquet 종목별 최신연도 group 후 facvalu_totamt 합산 + intrt 평균.

    Requires:
        - 로컬 ``data/dart/scan/report/debtSecurities.parquet`` (``buildReport``)

    SeeAlso:
        - :func:`dartlab.scan.debt.scanDebt` (sub-scanner 통합)

    Raises
    ------
    polars.PolarsError
        debtSecurities report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.debt.scanner import scanDebtSecurities
    >>> scanDebtSecurities().get("005930", {}).get("채무증권발행액")
    """
    raw = scanParquets(
        "debtSecurities",
        ["stockCode", "year", "facvalu_totamt", "intrt", "scrits_knd_nm"],
    )
    if raw.is_empty() or "facvalu_totamt" not in raw.columns:
        return {}
    result: dict[str, dict] = {}
    for code, group in raw.group_by("stockCode"):
        codeVal = code[0]
        latest = latestDataRows(group, "facvalu_totamt")
        if latest.is_empty():
            continue
        total = 0.0
        rates: list[float] = []
        for row in latest.iter_rows(named=True):
            amt = parseNumStr(row.get("facvalu_totamt"))
            if amt and amt > 0:
                total += amt
            rate = parseNumStr(row.get("intrt"))
            if rate is not None and 0 < rate < 30:
                rates.append(rate)
        if total > 0:
            result[codeVal] = {
                "채무증권발행액": total,
                "채무증권평균이자율": round(sum(rates) / len(rates), 2) if rates else None,
            }
    return result


# ── finance BS 부채비율 ──

LIABILITIES_IDS = {"Liabilities", "liabilities", "ifrs-full_Liabilities", "dart_Liabilities"}
LIABILITIES_NMS = {"부채총계", "부채 총계"}
EQUITY_IDS = {"Equity", "equity", "ifrs-full_Equity", "dart_Equity"}
EQUITY_NMS = {"자본총계", "자본 총계"}


def scanShortDebt() -> dict[str, dict]:
    """전종목 단기사채 + 기업어음 스캔.

    회사채(corporateBond)와 별도로, 기업어음/단기사채의 실질 단기 부채 노출을 측정한다.

    Returns
    -------
    dict[str, dict]
        {종목코드: info} 매핑. 각 info:
            단기사채잔액 : float — 단기사채 잔액 (백만원)
            CP잔액 : float — 기업어음 잔액 (백만원)
            단기채무합계 : float — 단기사채 + CP 합산 (백만원)

    Capabilities:
        - 종목별 사채잔액 / 단기사채 (CP 포함) / 부채비율 추출. ``scanDebt`` 의 sub-scanner.

    AIContext:
        ``scanDebt`` 내부 사용. AI agent 가 직접 호출하지 않음.

    Guide:
        - 사채잔액 0 인 종목은 결과 dict 에서 제외.
        - 단기비중 = 단기잔액 / 사채잔액 (%). > 50 % 면 단기 리파이낸싱 리스크.

    When:
        ``scanDebt`` 진행 단계 안에서.

    How:
        report parquet → 종목별 group → 합계 row 또는 만기별 row 합산.

    Requires:
        - 로컬 ``data/dart/scan/report/{corporateBond,shortTermBond}.parquet`` 또는
          ``data/dart/scan/finance.parquet``

    SeeAlso:
        - :func:`dartlab.scan.debt.scanDebt` — sub-scanner 통합

    Raises
    ------
    polars.PolarsError
        shortTermBond · commercialPaper report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.debt.scanner import scanShortDebt
    >>> short = scanShortDebt()
    >>> short.get("005930", {}).get("단기채무합계")
    """
    stb = scanParquets(
        "shortTermBond",
        ["stockCode", "year", "quarter", "sm"],
    )
    cp = scanParquets(
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
                val = parseNumStr(row.get("sm"))
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
                val = parseNumStr(row.get("sm"))
                if val and val > best:
                    best = val
            if best > 0:
                result.setdefault(codeVal, {})["CP잔액"] = best

    # 합산
    for code, d in result.items():
        d["단기채무합계"] = (d.get("단기사채잔액") or 0) + (d.get("CP잔액") or 0)

    return result


def scanDebtMix() -> dict[str, dict]:
    """전종목 부채 구성 스캔.

    부채비율 = 총부채 / 자본총계 x 100.
    scan/finance.parquet 프리빌드 우선, 없으면 종목별 순회.

    Returns
    -------
    dict[str, dict]
        {종목코드: info} 매핑. 각 info:
            총부채 : float — 부채총계 (원)
            부채비율 : float | None — 부채비율 (%)

    Capabilities:
        - 종목별 사채잔액 / 단기사채 (CP 포함) / 부채비율 추출. ``scanDebt`` 의 sub-scanner.

    AIContext:
        ``scanDebt`` 내부 사용. AI agent 가 직접 호출하지 않음.

    Guide:
        - 사채잔액 0 인 종목은 결과 dict 에서 제외.
        - 단기비중 = 단기잔액 / 사채잔액 (%). > 50 % 면 단기 리파이낸싱 리스크.

    When:
        ``scanDebt`` 진행 단계 안에서.

    How:
        report parquet → 종목별 group → 합계 row 또는 만기별 row 합산.

    Requires:
        - 로컬 ``data/dart/scan/report/{corporateBond,shortTermBond}.parquet`` 또는
          ``data/dart/scan/finance.parquet``

    SeeAlso:
        - :func:`dartlab.scan.debt.scanDebt` — sub-scanner 통합

    Raises
    ------
    polars.PolarsError
        scan finance.parquet 손상 시 per-file fallback 전환.

    Examples
    --------
    >>> from dartlab.scan.debt.scanner import scanDebtMix
    >>> mix = scanDebtMix()
    >>> mix.get("005930", {}).get("부채비율")
    """
    from dartlab.scan.io.parquet import _ensureScanData

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
                .collect(engine="streaming")
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
            val = parseNumStr(row.get("thstrm_amount"))
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
    """합산 finance parquet에서 부채/자본 추출.

    Parameters
    ----------
    scanPath : Path
        프리빌드 finance.parquet 경로.

    Returns
    -------
    dict[str, dict]
        {종목코드: {총부채(원), 부채비율(%)}} — 종목별 최신 연도 기준.
    """
    scCol = "stockCode"

    bs = (
        pl.scan_parquet(str(scanPath))
        .filter(
            (pl.col("sj_div") == "BS")
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
        )
        .collect(engine="streaming")
    )
    if bs.is_empty() or "account_id" not in bs.columns:
        return {}

    cfs = bs.filter(pl.col("fs_nm").str.contains("연결"))
    target = cfs if not cfs.is_empty() else bs

    # 종목별 최신 연도
    latestYear = target.group_by(scCol).agg(pl.col("bsns_year").max().alias("_maxYear"))
    target = target.join(latestYear, on=scCol).filter(pl.col("bsns_year") == pl.col("_maxYear")).drop("_maxYear")

    liabRows = target.filter(
        pl.col("account_id").is_in(list(LIABILITIES_IDS)) | pl.col("account_nm").is_in(list(LIABILITIES_NMS))
    )
    eqRows = target.filter(pl.col("account_id").is_in(list(EQUITY_IDS)) | pl.col("account_nm").is_in(list(EQUITY_NMS)))

    liabMap: dict[str, float] = {}
    for row in liabRows.iter_rows(named=True):
        code = row.get(scCol, "")
        val = parseNumStr(row.get("thstrm_amount"))
        if code and val and (code not in liabMap or val > liabMap[code]):
            liabMap[code] = val

    eqMap: dict[str, float] = {}
    for row in eqRows.iter_rows(named=True):
        code = row.get(scCol, "")
        val = parseNumStr(row.get("thstrm_amount"))
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
