"""현금흐름 패턴 분류 — OCF/ICF/FCF + 라이프사이클 패턴.

Note: 여기서 FCF는 OCF + ICF (투자활동 후 잔여현금)이다.
analysis의 FCF(OCF - CAPEX)와 다르다.
프리빌드 parquet에서 CAPEX를 개별 추출할 수 없으므로 ICF 전체를 사용한다.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan.io.parquet import (
    _ensureScanData,
    collectScan,
    financeScanPath,
    lazyParquet,
    parseNumStr,
)

# ── 영업활동CF ──

OCF_IDS = {
    "CashFlowsFromUsedInOperatingActivities",
    "CashFlowsFromOperatingActivities",
    "cashFlowsFromUsedInOperatingActivities",
    "ifrs-full_CashFlowsFromUsedInOperatingActivities",
    "OperatingCashFlows",
    "CashFromOperations",
}
OCF_NMS = {"영업활동현금흐름", "영업활동으로인한현금흐름", "영업활동현금흐름합계"}

# ── 투자활동CF ──

ICF_IDS = {
    "CashFlowsFromUsedInInvestingActivities",
    "CashFlowsFromInvestingActivities",
    "cashFlowsFromUsedInInvestingActivities",
    "ifrs-full_CashFlowsFromUsedInInvestingActivities",
    "InvestingCashFlows",
    "CashFromInvesting",
}
ICF_NMS = {"투자활동현금흐름", "투자활동으로인한현금흐름", "투자활동현금흐름합계"}

# ── 재무활동CF ──

FINCF_IDS = {
    "CashFlowsFromUsedInFinancingActivities",
    "CashFlowsFromFinancingActivities",
    "cashFlowsFromUsedInFinancingActivities",
    "ifrs-full_CashFlowsFromUsedInFinancingActivities",
    "FinancingCashFlows",
    "CashFromFinancing",
}
FINCF_NMS = {"재무활동현금흐름", "재무활동으로인한현금흐름", "재무활동현금흐름합계"}


# ── CF 패턴 분류 ──

_PATTERNS = {
    ("P", "N", "N"): "성장투자형",  # OCF+, ICF-, FINCF- → 자체CF로 투자+상환
    ("P", "N", "P"): "공격성장형",  # OCF+, ICF-, FINCF+ → 차입까지 동원해서 투자
    ("P", "P", "N"): "구조재편형",  # OCF+, ICF+, FINCF- → 자산매각+부채상환
    ("P", "P", "P"): "현금축적형",  # OCF+, ICF+, FINCF+ → 모든 채널에서 현금 유입
    ("N", "N", "P"): "외부의존형",  # OCF-, ICF-, FINCF+ → 차입으로 버팀
    ("N", "P", "N"): "축소정리형",  # OCF-, ICF+, FINCF- → 자산매각으로 부채상환
    ("N", "P", "P"): "위기대응형",  # OCF-, ICF+, FINCF+ → 자산매각+차입
    ("N", "N", "N"): "현금위기형",  # OCF-, ICF-, FINCF- → 모든 채널 유출
}


def _classifyPattern(ocf: float, icf: float, finCf: float) -> str:
    """OCF/ICF/FINCF 부호 조합 → 라이프사이클 패턴 라벨.

    Parameters
    ----------
    ocf : float
        영업활동현금흐름 (원).
    icf : float
        투자활동현금흐름 (원).
    finCf : float
        재무활동현금흐름 (원).

    Returns
    -------
    str
        패턴명. 다음 중 하나:
        성장투자형 / 공격성장형 / 구조재편형 / 현금축적형 /
        외부의존형 / 축소정리형 / 위기대응형 / 현금위기형 / 미분류.
    """
    key = (
        "P" if ocf >= 0 else "N",
        "P" if icf >= 0 else "N",
        "P" if finCf >= 0 else "N",
    )
    return _PATTERNS.get(key, "미분류")


def _scanFromMerged(scanPath: Path) -> pl.DataFrame:
    """프리빌드 finance.parquet → 종목별 CF 패턴.

    Parameters
    ----------
    scanPath : Path
        프리빌드 finance.parquet 파일 경로.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        ocf : int — 영업활동현금흐름 (원)
        icf : int | None — 투자활동현금흐름 (원)
        finCf : int | None — 재무활동현금흐름 (원)
        fcf : int — 잉여현금흐름, OCF + ICF (원)
        pattern : str — 라이프사이클 패턴명
    """
    scCol = "stockCode"

    allIds = list(OCF_IDS | ICF_IDS | FINCF_IDS)
    allNms = list(OCF_NMS | ICF_NMS | FINCF_NMS)

    target = collectScan(
        lazyParquet(scanPath).filter(
            pl.col("sj_div").is_in(["CF"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("account_id").is_in(allIds) | pl.col("account_nm").is_in(allNms))
        )
    )
    if target.is_empty():
        return pl.DataFrame()

    # 연결 우선
    cfs = target.filter(pl.col("fs_nm").str.contains("연결"))
    if not cfs.is_empty():
        target = cfs

    # 종목별 최신 연도
    latestYear = target.group_by(scCol).agg(pl.col("bsns_year").max().alias("_maxYear"))
    target = target.join(latestYear, on=scCol).filter(pl.col("bsns_year") == pl.col("_maxYear")).drop("_maxYear")

    rows: list[dict] = []
    for code in target[scCol].unique().to_list():
        sub = target.filter(pl.col(scCol) == code)
        ocf, icf, finCf = None, None, None
        for row in sub.iter_rows(named=True):
            aid = row.get("account_id", "")
            anm = row.get("account_nm", "")
            val = parseNumStr(row.get("thstrm_amount"))
            if val is None:
                continue
            if (aid in OCF_IDS or anm in OCF_NMS) and ocf is None:
                ocf = val
            elif (aid in ICF_IDS or anm in ICF_NMS) and icf is None:
                icf = val
            elif (aid in FINCF_IDS or anm in FINCF_NMS) and finCf is None:
                finCf = val

        if ocf is None:
            continue

        fcf = ocf + (icf or 0)
        rows.append(
            {
                "stockCode": code,
                "ocf": round(ocf),
                "icf": round(icf) if icf is not None else None,
                "finCf": round(finCf) if finCf is not None else None,
                "fcf": round(fcf),
                "pattern": _classifyPattern(ocf, icf or 0, finCf or 0),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()


def _scanPerFile() -> pl.DataFrame:
    """종목별 finance parquet 순회 fallback.

    프리빌드 finance.parquet가 없을 때 개별 종목 parquet을 순회하여
    최신 연도 CF 데이터를 추출한다.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        ocf : int — 영업활동현금흐름 (원)
        icf : int | None — 투자활동현금흐름 (원)
        finCf : int | None — 재무활동현금흐름 (원)
        fcf : int — 잉여현금흐름, OCF + ICF (원)
        pattern : str — 라이프사이클 패턴명
    """
    from dartlab.core.dataLoader import _dataDir

    financeDir = Path(_dataDir("finance"))
    parquetFiles = sorted(financeDir.glob("*.parquet"))

    rows: list[dict] = []
    for pf in parquetFiles:
        code = pf.stem
        try:
            cfDf = (
                pl.scan_parquet(str(pf))
                .filter(
                    pl.col("sj_div").is_in(["CF"])
                    & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
                )
                .collect(engine="streaming")
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        if cfDf.is_empty() or "account_id" not in cfDf.columns:
            continue
        cfs = cfDf.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else cfDf

        years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = target.filter(pl.col("bsns_year") == years[0])

        ocf, icf, finCf = None, None, None
        for row in latest.iter_rows(named=True):
            aid = row.get("account_id", "")
            anm = row.get("account_nm", "")
            val = parseNumStr(row.get("thstrm_amount"))
            if val is None:
                continue
            if (aid in OCF_IDS or anm in OCF_NMS) and ocf is None:
                ocf = val
            elif (aid in ICF_IDS or anm in ICF_NMS) and icf is None:
                icf = val
            elif (aid in FINCF_IDS or anm in FINCF_NMS) and finCf is None:
                finCf = val

        if ocf is None:
            continue

        fcf = ocf + (icf or 0)
        rows.append(
            {
                "stockCode": code,
                "ocf": round(ocf),
                "icf": round(icf) if icf is not None else None,
                "finCf": round(finCf) if finCf is not None else None,
                "fcf": round(fcf),
                "pattern": _classifyPattern(ocf, icf or 0, finCf or 0),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()


def scanCashflow(*, verbose: bool = True) -> pl.DataFrame:
    """종목별 OCF/ICF/FCF + 현금흐름 패턴 분류.

    프리빌드 finance.parquet 우선, 없으면 per-file fallback.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        ocf : int — 영업활동현금흐름 (원)
        icf : int | None — 투자활동현금흐름 (원)
        finCf : int | None — 재무활동현금흐름 (원)
        fcf : int — 잉여현금흐름, OCF + ICF (원)
        pattern : str — 라이프사이클 패턴명

    Raises
    ------
    polars.PolarsError
        프리빌드 finance.parquet 손상 또는 per-file fallback 도 실패할 때.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("cashflow")
    >>> df.filter(pl.col("패턴") == "성장기").select(["종목코드", "종목명"]).head()

    Capabilities:
        - 전종목 finance.parquet 에서 종목별 OCF/ICF/FCF 추출 + 라이프사이클 패턴 분류
          (성장기/안정기/구조조정/위기/등). FCF = OCF + ICF (CAPEX 부호 음수 반영).
        - 부호 조합 (OCF+/-, ICF+/-, finCf+/-) 으로 패턴 결정.

    AIContext:
        Agent 가 ``dartlab.scan("cashflow")`` 호출 시 본 함수 dispatch. 라이프사이클 단계 비교
        (성장기 vs 성숙기), 외부의존형 / 현금위기형 watchlist source.

    Guide:
        - 패턴 분류는 1 년 단면 — 2~3 년 시계열 비교는 호출자가 별도.
        - CAPEX 큰 성장기 종목은 FCF 음수일 수 있음 — 부정적 평가 X.

    When:
        대시보드 cashflow 카드 빌드 시. 라이프사이클 cross-company 분석 시.

    How:
        ``_ensureScanData`` → finance.parquet 합본 우선 ``_scanFromMerged`` (CF 3 계정 wide +
        FCF + 패턴 분기). 합본 없으면 ``_scanPerFile``.

    Requires:
        - 로컬 ``data/dart/scan/finance.parquet`` (``buildFinance`` 산출)
        - CF 3 계정 (영업/투자/재무) snakeId

    SeeAlso:
        - :func:`dartlab.scan.financial.quality.scanQuality` — CF/NI 회계 품질 보완
        - :func:`dartlab.scan.builders.kr.payload.capitalToInsight` — capital axis 와 결합
    """
    scanDir = _ensureScanData()
    scanPath = financeScanPath(scanDir)
    if scanPath.exists():
        return _scanFromMerged(scanPath)
    return _scanPerFile()
