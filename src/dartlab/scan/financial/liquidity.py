"""유동성 스캔 -- 유동비율 + 당좌비율 + 등급."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan.io.parquet import (
    _ensureScanData,
    collectScan,
    extractAccount,
    financeScanPath,
    lazyParquet,
    parquetColumns,
    preferConsolidatedPerCompany,
)

# ── 유동자산 ──

CA_IDS = {
    "CurrentAssets",
    "currentAssets",
    "ifrs-full_CurrentAssets",
    "dart_CurrentAssets",
}
CA_NMS = {"유동자산", "유동자산 합계"}

# ── 유동부채 ──

CL_IDS = {
    "CurrentLiabilities",
    "currentLiabilities",
    "ifrs-full_CurrentLiabilities",
    "dart_CurrentLiabilities",
}
CL_NMS = {"유동부채", "유동부채 합계"}

# ── 재고자산 ──

INV_IDS = {
    "Inventories",
    "inventories",
    "ifrs-full_Inventories",
    "dart_Inventories",
}
INV_NMS = {"재고자산"}


def _gradeLiquidity(currentRatio: float) -> str:
    """유동비율 → 유동성 등급 변환.

    우수(200%+) / 양호(150%+) / 보통(100%+) / 주의(50%+) / 위험(50% 미만).

    Parameters
    ----------
    currentRatio : float
        유동비율 (%)

    Returns
    -------
    str
        유동성 등급 (우수 | 양호 | 보통 | 주의 | 위험)
    """
    if currentRatio >= 200:
        return "우수"
    if currentRatio >= 150:
        return "양호"
    if currentRatio >= 100:
        return "보통"
    if currentRatio >= 50:
        return "주의"
    return "위험"


_extractVal = extractAccount  # backward compat alias


def _scanFromMerged(scanPath: Path) -> pl.DataFrame:
    """프리빌드 finance.parquet에서 종목별 유동성 지표 산출.

    연결재무제표 우선, 없으면 별도재무제표를 사용한다.
    종목별 최신 연도의 유동자산·유동부채·재고자산을 추출하여
    유동비율·당좌비율·등급을 계산한다.

    Parameters
    ----------
    scanPath : Path
        finance.parquet 파일 경로

    Returns
    -------
    pl.DataFrame
        컬럼:
            stockCode : str — 종목코드
            currentAssets : int — 유동자산 (원)
            currentLiabilities : int — 유동부채 (원)
            inventories : int | None — 재고자산 (원)
            currentRatio : float — 유동비율 (%)
            quickRatio : float | None — 당좌비율 (%)
            grade : str — 유동성 등급
        빈 DataFrame — 데이터 없음
    """
    schema = parquetColumns(scanPath)
    scCol = "stockCode"

    allIds = list(CA_IDS | CL_IDS | INV_IDS)
    allNms = list(CA_NMS | CL_NMS | INV_NMS)

    target = collectScan(
        lazyParquet(scanPath).filter(
            (pl.col("sj_div") == "BS")
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("account_id").is_in(allIds) | pl.col("account_nm").is_in(allNms))
        )
    )
    if target.is_empty():
        return pl.DataFrame()

    # 회사별 연결 우선. 유니버스 전체로 한 번에 좁히면 별도만 내는 회사가
    # 다른 회사 때문에 사라진다.
    target = preferConsolidatedPerCompany(target, scCol)

    latestYear = target.group_by(scCol).agg(pl.col("bsns_year").max().alias("_maxYear"))
    target = target.join(latestYear, on=scCol).filter(pl.col("bsns_year") == pl.col("_maxYear")).drop("_maxYear")

    rows: list[dict] = []
    for code in target[scCol].unique().to_list():
        sub = target.filter(pl.col(scCol) == code)

        ca = _extractVal(sub, CA_IDS, CA_NMS)
        cl = _extractVal(sub, CL_IDS, CL_NMS)
        inv = _extractVal(sub, INV_IDS, INV_NMS)

        if ca is None or cl is None or cl == 0:
            continue

        currentRatio = ca / cl * 100
        quickAssets = ca - inv if inv is not None else None
        quickRatio = quickAssets / cl * 100 if quickAssets is not None and cl > 0 else None

        rows.append(
            {
                "stockCode": code,
                "currentAssets": round(ca),
                "currentLiabilities": round(cl),
                "inventories": round(inv) if inv is not None else None,
                "currentRatio": round(currentRatio, 1),
                "quickRatio": round(quickRatio, 1) if quickRatio is not None else None,
                "grade": _gradeLiquidity(currentRatio),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()


def _scanPerFile() -> pl.DataFrame:
    """종목별 finance parquet 개별 순회 fallback.

    프리빌드 finance.parquet이 없을 때 종목별 parquet 파일을 하나씩 읽어
    유동성 지표를 산출한다. 반환 구조는 ``_scanFromMerged``와 동일.

    Returns
    -------
    pl.DataFrame
        컬럼:
            stockCode : str — 종목코드
            currentAssets : int — 유동자산 (원)
            currentLiabilities : int — 유동부채 (원)
            inventories : int | None — 재고자산 (원)
            currentRatio : float — 유동비율 (%)
            quickRatio : float | None — 당좌비율 (%)
            grade : str — 유동성 등급
        빈 DataFrame — 데이터 없음
    """
    from dartlab.core.dataLoader import _dataDir

    financeDir = Path(_dataDir("finance"))
    parquetFiles = sorted(financeDir.glob("*.parquet"))

    rows: list[dict] = []
    for pf in parquetFiles:
        code = pf.stem
        try:
            df = (
                pl.scan_parquet(str(pf))
                .filter(
                    (pl.col("sj_div") == "BS")
                    & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
                )
                .collect(engine="streaming")
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        if df.is_empty() or "account_id" not in df.columns:
            continue

        cfs = df.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else df

        years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = target.filter(pl.col("bsns_year") == years[0])

        ca = _extractVal(latest, CA_IDS, CA_NMS)
        cl = _extractVal(latest, CL_IDS, CL_NMS)
        inv = _extractVal(latest, INV_IDS, INV_NMS)

        if ca is None or cl is None or cl == 0:
            continue

        currentRatio = ca / cl * 100
        quickAssets = ca - inv if inv is not None else None
        quickRatio = quickAssets / cl * 100 if quickAssets is not None and cl > 0 else None

        rows.append(
            {
                "stockCode": code,
                "currentAssets": round(ca),
                "currentLiabilities": round(cl),
                "inventories": round(inv) if inv is not None else None,
                "currentRatio": round(currentRatio, 1),
                "quickRatio": round(quickRatio, 1) if quickRatio is not None else None,
                "grade": _gradeLiquidity(currentRatio),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()


def scanLiquidity(*, verbose: bool = True) -> pl.DataFrame:
    """전종목 유동성 스캔 — 유동비율 + 당좌비율 + 등급.

    Parameters
    ----------
    verbose : bool, default True
        진행 라인을 ``logger.info`` 로 출력.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        currentRatio : float | None — 유동비율 (%, 유동자산/유동부채×100)
        quickRatio : float | None — 당좌비율 (%, (유동자산-재고)/유동부채×100)
        grade : str — 유동성 등급 (우수/보통/주의/위험)

    Raises
    ------
    polars.PolarsError
        scan finance.parquet 손상 또는 per-file fallback 실패.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("liquidity")
    >>> df.sort("유동비율", descending=True).head()

    Notes
    -----
    금융업 (은행/보험/증권) 은 유동자산/유동부채 계정 없어 결과 없음.

    Capabilities:
        - 전종목 finance.parquet 에서 종목별 유동자산 / 유동부채 / 재고 합산 → 유동비율 + 당좌
          비율 + 4 단계 등급 (우수/보통/주의/위험).
        - 금융업 종목은 BS 계정 부재로 결과 0 (silent skip).

    AIContext:
        Agent 가 ``dartlab.scan("liquidity")`` 호출 시 본 함수 dispatch. 단기 지급능력 비교,
        파산 리스크 사전 감지 source. 부채 axis (`scanDebt`) 와 보완 관계.

    Guide:
        - 유동비율 100 % 미만 = 단기 지급능력 부족 가능 신호. 당좌비율은 재고를 제외한 보수 지표.
        - 금융업 0 row 는 데이터 결여이지 "양호" 가 아님.

    When:
        대시보드 liquidity 카드 빌드 시. 단기 지급 위험 스크리닝 시.

    How:
        ``_ensureScanData`` → ``finance.parquet`` 합본 있으면 ``_scanFromMerged`` (BS 계정
        wide + 유동/당좌 비율 + 등급 분기). 합본 없으면 ``_scanPerFile`` fallback.

    Requires:
        - 로컬 ``data/dart/scan/finance.parquet`` (``buildFinance`` 산출)

    SeeAlso:
        - :func:`dartlab.scan.debt.scanDebt` — 부채 구조 axis (본 함수의 보완)
        - :func:`dartlab.scan.financial.efficiency.scanEfficiency` — CCC 등 운영 효율
    """
    scanDir = _ensureScanData()
    scanPath = financeScanPath(scanDir)
    if scanPath.exists():
        return _scanFromMerged(scanPath)
    return _scanPerFile()
