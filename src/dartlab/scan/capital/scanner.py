"""주주환원 3축 report 스캔 — 배당, 자사주, 증자/감자."""

from __future__ import annotations

import polars as pl

from dartlab.scan.io.parquet import (
    latestDataRows,
    parseDateYear,
    parseNumStr,
    scanParquets,
)

# ── 배당 ──

DPS_KEYS = {"주당 현금배당금(원)", "주당현금배당금(원)", "주당현금배당금", "현금배당금(원)"}
YIELD_KEYS = {"현금배당수익률(%)", "현금배당수익률"}
TOTAL_KEYS = {"현금배당금총액(백만원)", "현금배당금총액"}


def scanDividend() -> dict[str, dict]:
    """전종목 배당 스캔.

    최신 연도 Q4 기준. DPS 행이 100개 이상인 연도를 선택.

    Returns
    -------
    dict[str, dict]
        {종목코드: info} 매핑. 각 info:
            배당여부 : bool — DPS > 0 여부
            DPS : float — 주당 현금배당금 (원)
            배당수익률 : float — 현금배당수익률 (%)
            배당총액_백만 : float — 현금배당금 총액 (백만원)

    Capabilities:
        - dividend / treasuryStock / capitalChange report → 종목별 주주환원 핵심 지표 추출.
          ``scanCapital`` 의 sub-scanner.

    AIContext:
        ``scanCapital`` 의 3 sub-scanner. AI agent 가 단독 호출하지 않음 — scanCapital dispatch.

    Guide:
        - 각 sub-scanner 가 같은 stockCode key 의 dict 반환. ``scanCapital`` 이 union 후 merge.

    When:
        ``scanCapital`` 진행 단계 안에서. 단독은 prototype.

    How:
        report parquet → 종목별 group → 단면 값 추출. 임계 검증 + 최신 연도 우선.

    Requires:
        - 로컬 ``data/dart/scan/report/{dividend,treasuryStock,capitalChange}.parquet`` (``buildReport``)

    SeeAlso:
        - :func:`dartlab.scan.capital.scanCapital` — 3 sub-scanner 통합 호출
        - :func:`classifyReturn` — 결과를 분류로

    Raises
    ------
    polars.PolarsError
        dividend report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.capital.scanner import scanDividend
    >>> div = scanDividend()
    >>> div.get("005930", {}).get("DPS")
    """
    raw = scanParquets(
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
            val = parseNumStr(row.get("thstrm"))
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


def scanTreasuryStock() -> dict[str, dict]:
    """전종목 자사주 스캔.

    Returns
    -------
    dict[str, dict]
        {종목코드: info} 매핑. 각 info:
            자사주보유 : bool — 기말 보유 여부
            당기취득 : bool — 당기 취득 여부
            당기처분 : bool — 당기 처분 여부
            당기소각 : bool — 당기 소각 여부
            취득수량 : int — 당기 취득 주식수 (주)
            처분수량 : int — 당기 처분 주식수 (주)
            소각수량 : int — 당기 소각 주식수 (주)

    Capabilities:
        - dividend / treasuryStock / capitalChange report → 종목별 주주환원 핵심 지표 추출.
          ``scanCapital`` 의 sub-scanner.

    AIContext:
        ``scanCapital`` 의 3 sub-scanner. AI agent 가 단독 호출하지 않음 — scanCapital dispatch.

    Guide:
        - 각 sub-scanner 가 같은 stockCode key 의 dict 반환. ``scanCapital`` 이 union 후 merge.

    When:
        ``scanCapital`` 진행 단계 안에서. 단독은 prototype.

    How:
        report parquet → 종목별 group → 단면 값 추출. 임계 검증 + 최신 연도 우선.

    Requires:
        - 로컬 ``data/dart/scan/report/{dividend,treasuryStock,capitalChange}.parquet`` (``buildReport``)

    SeeAlso:
        - :func:`dartlab.scan.capital.scanCapital` — 3 sub-scanner 통합 호출
        - :func:`classifyReturn` — 결과를 분류로

    Raises
    ------
    polars.PolarsError
        treasuryStock report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.capital.scanner import scanTreasuryStock
    >>> ts = scanTreasuryStock()
    >>> ts.get("005930", {}).get("자사주보유")
    """
    raw = scanParquets(
        "treasuryStock",
        ["stockCode", "year", "quarter", "trmend_qy", "change_qy_acqs", "change_qy_dsps", "change_qy_incnr"],
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
        total_dsps = 0
        total_incnr = 0
        for row in group.iter_rows(named=True):
            held = parseNumStr(row.get("trmend_qy"))
            acqs = parseNumStr(row.get("change_qy_acqs"))
            dsps = parseNumStr(row.get("change_qy_dsps"))
            incnr = parseNumStr(row.get("change_qy_incnr"))
            if held and held > 0:
                total_held += int(held)
            if acqs and acqs > 0:
                total_acqs += int(acqs)
            if dsps and dsps > 0:
                total_dsps += int(dsps)
            if incnr and incnr > 0:
                total_incnr += int(incnr)
        result[code_val] = {
            "자사주보유": total_held > 0,
            "당기취득": total_acqs > 0,
            "당기처분": total_dsps > 0,
            "당기소각": total_incnr > 0,
            "취득수량": total_acqs,
            "처분수량": total_dsps,
            "소각수량": total_incnr,
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


def scanCapitalChange() -> dict[str, dict]:
    """전종목 증자/감자 스캔.

    최근 3년(2023~) 이내 증자(INCREASE_TYPES) 여부.

    Returns
    -------
    dict[str, dict]
        {종목코드: info} 매핑. 각 info:
            최근증자 : bool — 최근 3년 내 증자 여부

    Capabilities:
        - dividend / treasuryStock / capitalChange report → 종목별 주주환원 핵심 지표 추출.
          ``scanCapital`` 의 sub-scanner.

    AIContext:
        ``scanCapital`` 의 3 sub-scanner. AI agent 가 단독 호출하지 않음 — scanCapital dispatch.

    Guide:
        - 각 sub-scanner 가 같은 stockCode key 의 dict 반환. ``scanCapital`` 이 union 후 merge.

    When:
        ``scanCapital`` 진행 단계 안에서. 단독은 prototype.

    How:
        report parquet → 종목별 group → 단면 값 추출. 임계 검증 + 최신 연도 우선.

    Requires:
        - 로컬 ``data/dart/scan/report/{dividend,treasuryStock,capitalChange}.parquet`` (``buildReport``)

    SeeAlso:
        - :func:`dartlab.scan.capital.scanCapital` — 3 sub-scanner 통합 호출
        - :func:`classifyReturn` — 결과를 분류로

    Raises
    ------
    polars.PolarsError
        capitalChange report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.capital.scanner import scanCapitalChange
    >>> cc = scanCapitalChange()
    >>> cc.get("005930", {}).get("최근증자")
    """
    raw = scanParquets(
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
        recentIncrease = False
        for row in group.iter_rows(named=True):
            stle = row.get("isu_dcrs_stle", "")
            event_year = parseDateYear(row.get("isu_dcrs_de"))
            if stle in INCREASE_TYPES and event_year and event_year >= 2023:
                recentIncrease = True
                break
        result[code_val] = {"최근증자": recentIncrease}
    return result


def scanShareTotal() -> dict[str, dict]:
    """전종목 주식총수 현황 스캔 (발행주식총수 + 자기주식 비율).

    stockTotal apiType 에서 종목별 최신 연도 발행주식총수와 자기주식 수를 뽑아 자기주식 비율을
    산출한다. ``se`` 구분행 중 합계(없으면 보통주)를 채택. 발행주식총수는 희석 baseline,
    자기주식비율은 잠재 환원 여력.

    Returns
    -------
    dict[str, dict]
        {종목코드: {발행주식총수(주), 자기주식비율(%)|None}}. 데이터 없는 종목 제외.

    Capabilities:
        - stockTotal 프리빌드에서 종목별 최신연도 발행주식총수 + 자기주식비율. scanCapital sub-scanner.

    AIContext:
        ``scanCapital`` 내부. 발행주식 baseline / 자기주식 환원여력 스크리닝 source.

    Guide:
        - se 우선순위 합계 > 보통주. 발행주식총수 0 종목 제외.

    When:
        ``scanCapital`` 진행 단계 안에서.

    How:
        report parquet 종목별 최신연도 group 후 se 구분행 선택, isu_stock_totqy + tesstk_co 파싱.

    Requires:
        - 로컬 ``data/dart/scan/report/stockTotal.parquet`` (``buildReport``)

    SeeAlso:
        - :func:`dartlab.scan.capital.scanCapital` (sub-scanner 통합)

    Raises
    ------
    polars.PolarsError
        stockTotal report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.capital.scanner import scanShareTotal
    >>> scanShareTotal().get("005930", {}).get("발행주식총수")
    """
    raw = scanParquets("stockTotal", ["stockCode", "year", "se", "isu_stock_totqy", "tesstk_co"])
    if raw.is_empty() or "isu_stock_totqy" not in raw.columns:
        return {}
    result: dict[str, dict] = {}
    for code, group in raw.group_by("stockCode"):
        codeVal = code[0]
        latest = latestDataRows(group, "isu_stock_totqy")
        if latest.is_empty():
            continue
        issued: float | None = None
        treasury: float | None = None
        for pref in ("합계", "보통주"):
            rows = latest.filter(pl.col("se").cast(pl.Utf8).fill_null("").str.contains(pref, literal=True))
            for row in rows.iter_rows(named=True):
                v = parseNumStr(row.get("isu_stock_totqy"))
                if v and v > 0:
                    issued = v
                    t = parseNumStr(row.get("tesstk_co"))
                    treasury = t if (t and t > 0) else treasury
                    break
            if issued is not None:
                break
        if issued is not None:
            result[codeVal] = {
                "발행주식총수": issued,
                "자기주식비율": round(treasury / issued * 100, 2) if treasury else None,
            }
    return result


def scanOfferingUsage() -> dict[str, dict]:
    """전종목 공모/사모 자금사용 스캔 (조달 규모 + 목적외 전용 신호).

    publicOfferingUsage + privateOfferingUsage apiType 에서 종목별 최신 연도 조달금액 합계와
    목적외 사용(차이발생사유 기재) 여부를 뽑는다. 목적외 전용은 강한 거버넌스 forensic 신호.

    Returns
    -------
    dict[str, dict]
        {종목코드: {조달금액(원), 목적외사용(bool)}}. 조달 기록 없는 종목 제외.

    Capabilities:
        - public/privateOfferingUsage 프리빌드에서 조달금액 합산 + 목적외사용 플래그. scanCapital sub-scanner.

    AIContext:
        ``scanCapital`` 내부. 조달 후 목적외 전용 종목 감지 source.

    Guide:
        - pay_amount 합산(최신연도). dffrnc_occrrnc_resn 이 "-"/공백 아니면 목적외사용 True.

    When:
        ``scanCapital`` 진행 단계 안에서.

    How:
        public/private report parquet 종목별 최신연도 group 후 조달금액 합산 + 차이사유 플래그.

    Requires:
        - 로컬 ``data/dart/scan/report/{publicOfferingUsage,privateOfferingUsage}.parquet`` (``buildReport``)

    SeeAlso:
        - :func:`dartlab.scan.capital.scanCapital` (sub-scanner 통합)

    Raises
    ------
    polars.PolarsError
        offering usage report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.capital.scanner import scanOfferingUsage
    >>> scanOfferingUsage().get("005930", {}).get("조달금액")
    """
    _cols = ["stockCode", "year", "pay_amount", "dffrnc_occrrnc_resn"]
    result: dict[str, dict] = {}
    _accumulateOffering(scanParquets("publicOfferingUsage", _cols), result)
    _accumulateOffering(scanParquets("privateOfferingUsage", _cols), result)
    return result


def _accumulateOffering(raw: pl.DataFrame, result: dict[str, dict]) -> None:
    """자금사용 raw(공모 또는 사모)를 종목별 최신연도 조달금액 + 목적외사용 플래그로 result 에 누적."""
    if raw.is_empty() or "pay_amount" not in raw.columns:
        return
    for code, group in raw.group_by("stockCode"):
        codeVal = code[0]
        latest = latestDataRows(group, "pay_amount")
        if latest.is_empty():
            continue
        raised = 0.0
        misuse = False
        for row in latest.iter_rows(named=True):
            amt = parseNumStr(row.get("pay_amount"))
            if amt and amt > 0:
                raised += amt
            resn = str(row.get("dffrnc_occrrnc_resn") or "").strip()
            if resn and resn != "-":
                misuse = True
        if raised > 0:
            cur = result.setdefault(codeVal, {"조달금액": 0.0, "목적외사용": False})
            cur["조달금액"] += raised
            cur["목적외사용"] = cur["목적외사용"] or misuse
