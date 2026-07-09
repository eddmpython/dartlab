"""이익의 질 (Earnings Quality) -- Accrual Ratio 기반 전종목 스캔."""

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
)

# ── 순이익 ──

NI_IDS = {
    "ProfitLoss",
    "ProfitLossAttributableToOwnersOfParent",
    "ifrs-full_ProfitLoss",
    "ifrs-full_ProfitLossAttributableToOwnersOfParent",
    "NetIncomeLoss",
    "dart_ProfitLoss",
}
NI_NMS = {"당기순이익", "당기순이익(손실)", "지배기업소유주지분순이익"}

# ── 영업활동CF ──

OCF_IDS = {
    "CashFlowsFromUsedInOperatingActivities",
    "CashFlowsFromOperatingActivities",
    "cashFlowsFromUsedInOperatingActivities",
    "ifrs-full_CashFlowsFromUsedInOperatingActivities",
}
OCF_NMS = {"영업활동현금흐름", "영업활동으로인한현금흐름", "영업활동현금흐름합계"}

# ── 총자산 ──

TA_IDS = {
    "Assets",
    "ifrs-full_Assets",
    "TotalAssets",
}
TA_NMS = {"자산총계"}


# ── 등급 분류 ──


def _gradeQuality(accrualRatio: float) -> str:
    """Accrual Ratio 로 이익의 질 등급 분류.

    Parameters
    ----------
    accrualRatio : float
        발생액 비율. ``(순이익 - 영업CF) / |총자산|``.
        음수일수록 현금흐름이 이익을 상회하여 이익의 질이 높음.

    Returns
    -------
    grade : str
        이익의 질 등급. 다음 중 하나:
        - ``"우수"`` : accrualRatio <= -0.05 (CF가 이익보다 훨씬 큼)
        - ``"양호"`` : -0.05 < accrualRatio <= 0.05 (이익과 CF가 비슷)
        - ``"보통"`` : 0.05 < accrualRatio <= 0.15 (약간의 accrual)
        - ``"주의"`` : 0.15 < accrualRatio <= 0.25 (accrual 비중 높음)
        - ``"위험"`` : accrualRatio > 0.25 (이익 대부분이 accrual)
    """
    if accrualRatio <= -0.05:
        return "우수"  # CF가 이익보다 훨씬 큼
    if accrualRatio <= 0.05:
        return "양호"  # 이익과 CF가 비슷
    if accrualRatio <= 0.15:
        return "보통"  # 약간의 accrual
    if accrualRatio <= 0.25:
        return "주의"  # accrual 비중 높음
    return "위험"  # 이익 대부분이 accrual


_extractVal = extractAccount  # backward compat alias


def _scanFromMerged(scanPath: Path) -> pl.DataFrame:
    """프리빌드 finance.parquet 에서 전종목 이익의 질 지표 계산.

    Parameters
    ----------
    scanPath : Path
        ``finance.parquet`` 파일 경로.

    Returns
    -------
    pl.DataFrame
        종목별 이익의 질 지표. 컬럼:

        - stockCode : str — 종목코드
        - netIncome : float — 당기순이익 (원)
        - operatingCf : float — 영업활동 현금흐름 (원)
        - totalAssets : float — 총자산 (원)
        - accrualRatio : float — 발생액 비율 (순이익 - 영업CF) / |총자산| (비율)
        - cfToNi : float — 영업CF / 순이익 (배). 극단값(|x|>20) 은 None
        - grade : str — 이익의 질 등급 (우수/양호/보통/주의/위험)
    """
    schema = parquetColumns(scanPath)
    scCol = "stockCode"

    allIds = list(NI_IDS | OCF_IDS | TA_IDS)
    allNms = list(NI_NMS | OCF_NMS | TA_NMS)

    target = collectScan(
        lazyParquet(scanPath).filter(
            pl.col("sj_div").is_in(["IS", "CIS", "CF", "BS"])
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

        # IS/CIS에서 순이익
        isSub = sub.filter(pl.col("sj_div").is_in(["IS", "CIS"]))
        ni = _extractVal(isSub, NI_IDS, NI_NMS)

        # CF에서 영업CF
        cfSub = sub.filter(pl.col("sj_div") == "CF")
        ocf = _extractVal(cfSub, OCF_IDS, OCF_NMS)

        # BS에서 총자산
        bsSub = sub.filter(pl.col("sj_div") == "BS")
        ta = _extractVal(bsSub, TA_IDS, TA_NMS)

        if ni is None or ocf is None or ta is None or ta == 0:
            continue

        accrualRatio = (ni - ocf) / abs(ta)
        cfToNi = ocf / ni if ni != 0 else None
        # cfToNi 극단값 cap: ±5 초과는 분모(NI) 극소 신호 — None 처리해야 AI 가 "우수"로 오판하지 않음.
        # 일반 회사의 CF/NI 는 0.5~2배. 5배 이상은 일회성 이익/적자 직후 등 비정상.
        if cfToNi is not None and abs(cfToNi) > 5:
            cfToNi = None

        rows.append(
            {
                "stockCode": code,
                "netIncome": round(ni),
                "operatingCf": round(ocf),
                "totalAssets": round(ta),
                "accrualRatio": round(accrualRatio, 4),
                "cfToNi": round(cfToNi, 4) if cfToNi is not None else None,
                "grade": _gradeQuality(accrualRatio),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()


def _scanPerFile() -> pl.DataFrame:
    """종목별 finance parquet 파일을 순회하여 이익의 질 계산 (fallback).

    ``finance.parquet`` 통합 파일이 없을 때 개별 종목 parquet 을 순회한다.

    Returns
    -------
    pl.DataFrame
        ``_scanFromMerged`` 와 동일한 스키마. 컬럼:

        - stockCode : str — 종목코드
        - netIncome : float — 당기순이익 (원)
        - operatingCf : float — 영업활동 현금흐름 (원)
        - totalAssets : float — 총자산 (원)
        - accrualRatio : float — 발생액 비율 (비율)
        - cfToNi : float — 영업CF / 순이익 (배). 극단값(|x|>20) 은 None
        - grade : str — 이익의 질 등급 (우수/양호/보통/주의/위험)
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
                    pl.col("sj_div").is_in(["IS", "CIS", "CF", "BS"])
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

        isSub = latest.filter(pl.col("sj_div").is_in(["IS", "CIS"]))
        ni = _extractVal(isSub, NI_IDS, NI_NMS)

        cfSub = latest.filter(pl.col("sj_div") == "CF")
        ocf = _extractVal(cfSub, OCF_IDS, OCF_NMS)

        bsSub = latest.filter(pl.col("sj_div") == "BS")
        ta = _extractVal(bsSub, TA_IDS, TA_NMS)

        if ni is None or ocf is None or ta is None or ta == 0:
            continue

        accrualRatio = (ni - ocf) / abs(ta)
        cfToNi = ocf / ni if ni != 0 else None
        # cfToNi 극단값 cap: ±5 초과는 분모(NI) 극소 신호 — None 처리해야 AI 가 "우수"로 오판하지 않음.
        # 일반 회사의 CF/NI 는 0.5~2배. 5배 이상은 일회성 이익/적자 직후 등 비정상.
        if cfToNi is not None and abs(cfToNi) > 5:
            cfToNi = None

        rows.append(
            {
                "stockCode": code,
                "netIncome": round(ni),
                "operatingCf": round(ocf),
                "totalAssets": round(ta),
                "accrualRatio": round(accrualRatio, 4),
                "cfToNi": round(cfToNi, 4) if cfToNi is not None else None,
                "grade": _gradeQuality(accrualRatio),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()


def scanQuality(*, verbose: bool = True) -> pl.DataFrame:
    """전종목 이익의 질 스캔 -- Accrual Ratio + CF/NI 비율 + 등급 (**KR 전용**).

    AI 사용 가이드:
        - **KR 종목 컨텍스트에서만**. US/글로벌 종목은 지원하지 않는다.
        - 전종목 횡단분석. 단일 종목 이익품질 조사에는 ``Company.panel("CF")`` 사용.
        - ``sortBy`` 로 정렬할 때는 **한글 컬럼명 그대로** 전달
          (예: ``"발생액비율"``, ``"CF/NI"``, ``"등급"``). ``"영업현금흐름/순이익"``, ``"earnings_quality"`` 같은 임의 이름 금지.

    Returns
    -------
    pl.DataFrame
        다음 컬럼을 가진 회사 단위 행:

        - 종목코드 : str — 6자리 종목코드
        - 종목명   : str — 회사명
        - netIncome : float — 당기순이익 (원)
        - operatingCf : float — 영업활동현금흐름 (원)
        - totalAssets : float — 자산총계 (원)
        - 발생액비율 : float — (netIncome - operatingCf) / totalAssets. 0에 가까울수록 이익이 현금으로 뒷받침
        - CF/NI : float | None — operatingCf / netIncome (배). 1.0 이상이면 순이익 전부 현금 회수.
          ``|x|>5`` 인 극단값은 분모(NI) 가 극소이므로 None 처리. ``CF/NI=None`` 이면 "이익품질 양호"로 해석 금지.
        - 등급 : str — ``"우수"`` / ``"보통"`` / ``"주의"`` / ``"위험"``

    Raises
    ------
    polars.PolarsError
        scan finance.parquet 손상 또는 per-file fallback 실패.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("quality")
    >>> df.filter(pl.col("등급") == "우수").select(["종목코드", "발생액비율"]).head()

    Capabilities:
        - 전종목 finance.parquet 에서 종목별 당기순이익 / 영업현금흐름 / 자산총계 합산 → 발생액
          비율 ((NI-OCF)/TA) + CF/NI 비율 + 4 단계 등급 (우수/보통/주의/위험).
        - CF/NI |x|>5 극단값은 None — 분모 NI 극소가 만든 noise 거름.

    AIContext:
        Agent 가 ``dartlab.scan("quality")`` 호출 시 본 함수 dispatch. "이익이 현금으로 뒷받침되지
        않는 종목" 스크리닝, 회계 품질 cross-company 비교 source. 분식 회계 의심 신호 — 발생액
        비율 > 0.10 = 주의.

    When:
        대시보드 quality 카드 빌드 시. 이익 품질 스크리닝 시. 분식 회계 감지 prototype 시.

    How:
        ``_ensureScanData`` → finance.parquet 합본 있으면 ``_scanFromMerged`` (NI/OCF/TA wide
        + 발생액 비율 + CF/NI + 등급 분기). 합본 없으면 ``_scanPerFile`` fallback.

    Requires:
        - 로컬 ``data/dart/scan/finance.parquet`` (``buildFinance`` 산출) 또는
          ``data/dart/finance/{stockCode}.parquet`` (fallback)
        - **KR 종목 한정** — US/글로벌 종목은 별도 EDGAR axis 사용 (`_scanQuality`)

    SeeAlso:
        - :func:`dartlab.scan.financial.profitability.scanProfitability` — 절대 수익성
        - :func:`dartlab.scan.financial.cashflow.scanCashflow` — 현금흐름 패턴
        - :func:`dartlab.scan.builders.edgar.scan._scanQuality` — US 종목 (대칭 axis)
    """
    scanDir = _ensureScanData()
    scanPath = financeScanPath(scanDir)
    if scanPath.exists():
        return _scanFromMerged(scanPath)
    return _scanPerFile()
