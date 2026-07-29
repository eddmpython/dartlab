"""이익의 질 (Earnings Quality) -- Accrual Ratio 기반 전종목 스캔."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan.io.parquet import (
    ScanDataError,
    _ensureScanData,
    extractAccount,
    financeScanPath,
    scanLatestAccountValues,
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
    values = scanLatestAccountValues(
        scanPath,
        {
            "netIncome": (NI_IDS, NI_NMS, {"IS", "CIS"}),
            "operatingCf": (OCF_IDS, OCF_NMS, {"CF"}),
            "totalAssets": (TA_IDS, TA_NMS, {"BS"}),
        },
    )
    if values.is_empty():
        return pl.DataFrame()

    accrualRatio = (pl.col("netIncome") - pl.col("operatingCf")) / pl.col("totalAssets").abs()
    cfToNi = pl.col("operatingCf") / pl.col("netIncome")
    return (
        values.filter(
            pl.col("netIncome").is_not_null()
            & pl.col("operatingCf").is_not_null()
            & pl.col("totalAssets").is_not_null()
            & (pl.col("totalAssets") != 0)
        )
        .with_columns(
            accrualRatio.alias("_accrualRatio"),
            pl.when((pl.col("netIncome") != 0) & (cfToNi.abs() <= 5)).then(cfToNi).otherwise(None).alias("_cfToNi"),
        )
        .with_columns(
            pl.col("netIncome").round(0).cast(pl.Int64),
            pl.col("operatingCf").round(0).cast(pl.Int64),
            pl.col("totalAssets").round(0).cast(pl.Int64),
            pl.col("_accrualRatio").round(4).alias("accrualRatio"),
            pl.col("_cfToNi").round(4).alias("cfToNi"),
            pl.when(pl.col("_accrualRatio") <= -0.05)
            .then(pl.lit("우수"))
            .when(pl.col("_accrualRatio") <= 0.05)
            .then(pl.lit("양호"))
            .when(pl.col("_accrualRatio") <= 0.15)
            .then(pl.lit("보통"))
            .when(pl.col("_accrualRatio") <= 0.25)
            .then(pl.lit("주의"))
            .otherwise(pl.lit("위험"))
            .alias("grade"),
        )
        .select(
            "stockCode",
            "netIncome",
            "operatingCf",
            "totalAssets",
            "accrualRatio",
            "cfToNi",
            "grade",
        )
    )


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
    if not scanPath.exists():
        raise ScanDataError(
            "finance_prebuild_missing",
            "finance prebuild is required after _ensureScanData",
            source=scanPath,
        )
    return _scanFromMerged(scanPath)
