"""이자보상배율(ICR) + 단기비중 교차 → 부채 위험등급."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan.io.parquet import parseNumStr

# ── 영업이익 ──

OP_IDS = {
    "ProfitLossFromOperatingActivities",
    "profitLossFromOperatingActivities",
    "ifrs-full_ProfitLossFromOperatingActivities",
    "dart_OperatingIncomeLoss",
}
OP_NMS = {"영업이익", "영업이익(손실)"}


# ── 이자비용 ──

INTEREST_IDS = {
    "FinanceCosts",
    "financeCosts",
    "ifrs-full_FinanceCosts",
    "InterestExpense",
    "interestExpense",
}
INTEREST_NMS = {"이자비용", "금융비용", "금융원가", "이자비용(수익)"}


def _scanIcrFromMerged(scanPath: Path) -> dict[str, float]:
    """프리빌드 finance.parquet → 종목별 ICR.

    Parameters
    ----------
    scanPath : Path
        프리빌드 finance.parquet 경로.

    Returns
    -------
    dict[str, float]
        {종목코드: ICR(배)} — 영업이익/이자비용. 종목별 최신 연도 기준.
    """
    scCol = "stockCode"

    allIds = list(OP_IDS | INTEREST_IDS)
    allNms = list(OP_NMS | INTEREST_NMS)

    from dartlab.scan.io.parquet import collectScan, lazyParquet

    target = collectScan(
        lazyParquet(scanPath).filter(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("account_id").is_in(allIds) | pl.col("account_nm").is_in(allNms))
        )
    )
    if target.is_empty():
        return {}

    # 연결 우선
    cfs = target.filter(pl.col("fs_nm").str.contains("연결"))
    if not cfs.is_empty():
        target = cfs

    # 종목별 최신 연도만
    latestYear = target.group_by(scCol).agg(pl.col("bsns_year").max().alias("_maxYear"))
    target = target.join(latestYear, on=scCol).filter(pl.col("bsns_year") == pl.col("_maxYear")).drop("_maxYear")

    result: dict[str, float] = {}
    for code in target[scCol].unique().to_list():
        sub = target.filter(pl.col(scCol) == code)
        opIncome = None
        interest = None
        for row in sub.iter_rows(named=True):
            aid = row.get("account_id", "")
            anm = row.get("account_nm", "")
            val = parseNumStr(row.get("thstrm_amount"))
            if val is None:
                continue
            if (aid in OP_IDS or anm in OP_NMS) and opIncome is None:
                opIncome = val
            elif (aid in INTEREST_IDS or anm in INTEREST_NMS) and interest is None:
                interest = abs(val) if val != 0 else None
        if opIncome is not None and interest and interest > 0:
            result[code] = round(opIncome / interest, 2)

    return result


def _scanIcrPerFile() -> dict[str, float]:
    """종목별 finance parquet 순회 fallback.

    Returns
    -------
    dict[str, float]
        {종목코드: ICR(배)} — 영업이익/이자비용.
    """
    from dartlab.core.dataLoader import _dataDir

    financeDir = Path(_dataDir("finance"))
    parquetFiles = sorted(financeDir.glob("*.parquet"))

    result: dict[str, float] = {}
    for pf in parquetFiles:
        code = pf.stem
        try:
            isDf = (
                pl.scan_parquet(str(pf))
                .filter(
                    pl.col("sj_div").is_in(["IS", "CIS"])
                    & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
                )
                .collect(engine="streaming")
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        if isDf.is_empty() or "account_id" not in isDf.columns:
            continue
        cfs = isDf.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else isDf

        years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = target.filter(pl.col("bsns_year") == years[0])

        opIncome = None
        interest = None
        for row in latest.iter_rows(named=True):
            aid = row.get("account_id", "")
            anm = row.get("account_nm", "")
            val = parseNumStr(row.get("thstrm_amount"))
            if val is None:
                continue
            if (aid in OP_IDS or anm in OP_NMS) and opIncome is None:
                opIncome = val
            elif (aid in INTEREST_IDS or anm in INTEREST_NMS) and interest is None:
                interest = abs(val) if val != 0 else None

        if opIncome is not None and interest and interest > 0:
            result[code] = round(opIncome / interest, 2)

    return result


def scanIcr() -> dict[str, float]:
    """전종목 ICR (이자보상배율) 스캔.

    프리빌드 finance.parquet 우선, 없으면 per-file fallback. 영업이익 / 이자비용
    공식을 적용해 종목별 ICR 을 산출한다.

    Returns
    -------
    dict[str, float]
        {종목코드: ICR(배)}. 이자비용 0 이거나 매칭 실패면 제외.

    Capabilities:
        - scanIcr: finance IS 의 영업이익 / 이자비용 → ICR (배). 종목별 latest 단면.
        - classifyRisk: ICR + 단기비중 + 단기채무합계 → 4 단계 위험등급 (안전/관찰/주의/고위험).

    AIContext:
        ``scanDebt`` 의 sub-scanner + classifier. AI agent 가 단독 호출하지 않음.

    Guide:
        - ICR < 1 = 영업이익으로 이자조차 못 갚는 상태 (고위험).
        - 단기비중 50 % 초과 = 리파이낸싱 리스크 신호.

    When:
        호출 컨텍스트 안에서.

    How:
        ``scanDebt`` 내부에서. scanIcr → finance 단면 추출. classifyRisk → 임계 분기 chain.

    Requires:
        - 로컬 ``data/dart/scan/finance.parquet`` (scanIcr 만)

    SeeAlso:
        - :func:`dartlab.scan.debt.scanDebt` — 본 함수들 통합 호출

    Raises
    ------
    polars.PolarsError
        scan finance.parquet 손상 시 per-file fallback 전환.

    Examples
    --------
    >>> from dartlab.scan.debt.risk import scanIcr
    >>> icrMap = scanIcr()
    >>> icrMap.get("005930")
    """
    from dartlab.scan.io.parquet import _ensureScanData, financeScanPath

    scanDir = _ensureScanData()
    scanPath = financeScanPath(scanDir)
    if scanPath.exists():
        return _scanIcrFromMerged(scanPath)
    return _scanIcrPerFile()


def classifyRisk(
    icr: float | None,
    shortRatio: float | None,
    shortDebtTotal: float | None = None,
) -> str:
    """ICR x 단기비중 x 단기채무 → 위험등급.

    Parameters
    ----------
    icr : float | None
        이자보상배율 (배).
    shortRatio : float | None
        단기 부채 비중 (%, 단기/사채).
    shortDebtTotal : float | None, optional
        단기사채 + CP 합계 (백만원).

    Returns
    -------
    str
        위험등급. 다음 분기:

        - 고위험: (단기비중 >= 50% AND ICR < 1) OR (ICR < 1 AND 단기채무 존재)
        - 주의:   단기비중 >= 50% OR ICR < 1 OR 단기채무 존재
        - 관찰:   ICR < 3
        - 안전:   그 외

    Capabilities:
        - scanIcr: finance IS 의 영업이익 / 이자비용 → ICR (배). 종목별 latest 단면.
        - classifyRisk: ICR + 단기비중 + 단기채무합계 → 4 단계 위험등급 (안전/관찰/주의/고위험).

    AIContext:
        ``scanDebt`` 의 sub-scanner + classifier. AI agent 가 단독 호출하지 않음.

    Guide:
        - ICR < 1 = 영업이익으로 이자조차 못 갚는 상태 (고위험).
        - 단기비중 50 % 초과 = 리파이낸싱 리스크 신호.

    When:
        호출 컨텍스트 안에서.

    How:
        ``scanDebt`` 내부에서. scanIcr → finance 단면 추출. classifyRisk → 임계 분기 chain.

    Requires:
        - 로컬 ``data/dart/scan/finance.parquet`` (scanIcr 만)

    SeeAlso:
        - :func:`dartlab.scan.debt.scanDebt` — 본 함수들 통합 호출

    Raises
    ------
    없음 — 순수 분기 함수.

    Examples
    --------
    >>> from dartlab.scan.debt.risk import classifyRisk
    >>> classifyRisk(icr=0.5, shortRatio=60)
    '고위험'
    >>> classifyRisk(icr=5.0, shortRatio=10)
    '안전'
    """
    sr = shortRatio if shortRatio is not None else 0
    hasShortDebt = shortDebtTotal is not None and shortDebtTotal > 0

    if icr is None:
        if sr >= 50 or hasShortDebt:
            return "주의"
        return "관찰"
    if (sr >= 50 and icr < 1) or (icr < 1 and hasShortDebt):
        return "고위험"
    if sr >= 50 or icr < 1 or hasShortDebt:
        return "주의"
    if icr < 3:
        return "관찰"
    return "안전"
