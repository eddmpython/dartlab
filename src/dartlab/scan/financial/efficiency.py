"""운영 효율 스캔 -- 자산/재고/매출채권 회전율 + CCC(현금전환주기)."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


from dartlab.scan.io.parquet import (
    NI_IDS as _NI_IDS,  # noqa: F401 (호환 alias 일부 호출 대비)
)
from dartlab.scan.io.parquet import (
    OP_IDS as _OP_IDS,  # noqa: F401
)
from dartlab.scan.io.parquet import (
    REVENUE_IDS as _REVENUE_IDS,
)
from dartlab.scan.io.parquet import (
    REVENUE_NMS as _REVENUE_NMS,
)
from dartlab.scan.io.parquet import (
    TA_IDS as _TA_IDS,
)
from dartlab.scan.io.parquet import (
    TA_NMS as _TA_NMS,
)
from dartlab.scan.io.parquet import ScanDataError, _ensureScanData, financeScanPath, scanLatestAccountValues

# ── 계정 매핑 (모듈 고유) ──

_INV_IDS = {"Inventories", "inventories", "ifrs-full_Inventories", "dart_Inventories"}
_INV_NMS = {"재고자산"}

_AR_IDS = {
    "ShortTermTradeReceivables",
    "TradeAndOtherCurrentReceivables",
    "ifrs-full_TradeAndOtherCurrentReceivables",
}
_AR_NMS = {"매출채권"}

_PPE_IDS = {"PropertyPlantAndEquipment", "ifrs-full_PropertyPlantAndEquipment"}
_PPE_NMS = {"유형자산"}

_COGS_IDS = {"CostOfSales", "ifrs-full_CostOfSales", "dart_CostOfGoodsAndServicesSold"}
_COGS_NMS = {"매출원가"}

_AP_IDS = {"TradeAndOtherCurrentPayables", "ifrs-full_TradeAndOtherCurrentPayables"}
_AP_NMS = {"매입채무"}

_MIN_REVENUE = 1e8  # 매출 1억 미만 제외
_CCC_CAP = 3000.0  # CCC +-3000일 초과 클램핑


def _gradeEfficiency(ccc: float | None) -> str:
    """현금전환주기(CCC) → 운영 효율 등급 변환.

    우수(90일 미만) / 양호(180일 미만) / 보통(365일 미만) / 비효율(365일 이상).
    None이면 '해당없음'을 반환한다.

    Parameters
    ----------
    ccc : float | None
        현금전환주기 (일)

    Returns
    -------
    str
        효율 등급 (우수 | 양호 | 보통 | 비효율 | 해당없음)
    """
    if ccc is None:
        return "해당없음"
    if ccc < 90:
        return "우수"
    if ccc < 180:
        return "양호"
    if ccc < 365:
        return "보통"
    return "비효율"


def _scanFromMerged(scanPath: Path) -> pl.DataFrame:
    """finance prebuild 1회 scan으로 최신 기간 운영 효율을 계산한다."""

    values = scanLatestAccountValues(
        scanPath,
        {
            "revenue": (_REVENUE_IDS, _REVENUE_NMS, {"IS", "CIS"}),
            "totalAssets": (_TA_IDS, _TA_NMS, {"BS"}),
            "inventories": (_INV_IDS, _INV_NMS, {"BS"}),
            "receivables": (_AR_IDS, _AR_NMS, {"BS"}),
            "ppe": (_PPE_IDS, _PPE_NMS, {"BS"}),
            "costOfSales": (_COGS_IDS, _COGS_NMS, {"IS", "CIS"}),
            "payables": (_AP_IDS, _AP_NMS, {"BS"}),
        },
    )
    if values.is_empty():
        return pl.DataFrame()

    revenue = pl.col("revenue")
    assets = pl.col("totalAssets")
    inventory = pl.col("inventories")
    receivables = pl.col("receivables")
    ppe = pl.col("ppe")
    cogs = pl.col("costOfSales")
    payables = pl.col("payables")

    assetTurnover = pl.when(assets > 0).then(revenue / assets).otherwise(None)
    invTurnover = pl.when((inventory > 0) & (cogs > 0)).then(cogs / inventory).otherwise(None)
    arTurnover = pl.when(receivables > 0).then(revenue / receivables).otherwise(None)
    ppeTurnover = pl.when(ppe > 0).then(revenue / ppe).otherwise(None)
    invDays = pl.when((inventory >= 0) & (cogs > 0)).then(365 * inventory / cogs).otherwise(None)
    arDays = pl.when(receivables >= 0).then(365 * receivables / revenue).otherwise(None)
    apDays = pl.when((payables >= 0) & (cogs > 0)).then(365 * payables / cogs).otherwise(None)

    return (
        values.filter(revenue.is_not_null() & (revenue >= _MIN_REVENUE))
        .with_columns(
            assetTurnover.alias("_assetTurnover"),
            invTurnover.alias("_invTurnover"),
            arTurnover.alias("_arTurnover"),
            ppeTurnover.alias("_ppeTurnover"),
            invDays.alias("_invDays"),
            arDays.alias("_arDays"),
            apDays.alias("_apDays"),
        )
        .with_columns(
            pl.when(
                pl.col("_invDays").is_not_null() & pl.col("_arDays").is_not_null() & pl.col("_apDays").is_not_null()
            )
            .then(
                (pl.col("_invDays") + pl.col("_arDays") - pl.col("_apDays")).clip(
                    -_CCC_CAP,
                    _CCC_CAP,
                )
            )
            .otherwise(None)
            .alias("_ccc")
        )
        .with_columns(
            pl.col("_assetTurnover").round(2).alias("assetTurnover"),
            pl.col("_invTurnover").round(2).alias("invTurnover"),
            pl.col("_arTurnover").round(2).alias("arTurnover"),
            pl.col("_ppeTurnover").round(2).alias("ppeTurnover"),
            pl.col("_invDays").round(0).alias("invDays"),
            pl.col("_arDays").round(0).alias("arDays"),
            pl.col("_ccc").round(0).alias("ccc"),
            pl.when(pl.col("_ccc").is_null())
            .then(pl.lit("해당없음"))
            .when(pl.col("_ccc") < 90)
            .then(pl.lit("우수"))
            .when(pl.col("_ccc") < 180)
            .then(pl.lit("양호"))
            .when(pl.col("_ccc") < 365)
            .then(pl.lit("보통"))
            .otherwise(pl.lit("비효율"))
            .alias("grade"),
        )
        .select(
            "stockCode",
            "assetTurnover",
            "invTurnover",
            "arTurnover",
            "ppeTurnover",
            "invDays",
            "arDays",
            "ccc",
            "grade",
        )
    )


def scanEfficiency(*, verbose: bool = True) -> pl.DataFrame:
    """전종목 운영 효율 스캔 — 자산/재고/매출채권 회전율 + CCC + 등급.

    Parameters
    ----------
    verbose : bool, default True
        진행 라인을 ``logger.info`` 로 출력.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        assetTurnover : float — 자산회전율 (배, 매출/총자산)
        invTurnover : float — 재고회전율 (배, COGS/재고)
        arTurnover : float — 매출채권회전율 (배, 매출/매출채권)
        ppeTurnover : float — 유형자산회전율 (배, 매출/PP&E)
        invDays : float — 재고일수 (일)
        arDays : float — 매출채권일수 (일)
        ccc : float — 현금전환주기 (일, 재고일수 + AR일수 - AP일수)
        grade : str — 효율성 등급

    Raises
    ------
    polars.PolarsError
        scan finance.parquet 누락 또는 손상 시 (Auto-download 로 회복 시도).

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("efficiency")
    >>> df.sort("자산회전율", descending=True).head()

    Capabilities:
        - 전종목 finance.parquet 에서 종목별 자산/재고/매출채권/매입채무 회전율 + 일수 +
          CCC (현금전환주기) 계산 → 4 단계 효율성 등급.
        - CCC = invDays + arDays - apDays. 짧을수록 운영자본 효율 양호.

    AIContext:
        Agent 가 ``dartlab.scan("efficiency")`` 호출 시 본 함수 dispatch. 운영자본 회전 비교,
        재고 적체 위험 감지 (invDays 급증), CCC 변화로 매출 회수 / 매입 결제 정책 분석 source.

    Guide:
        - 업종 차이 큰 — 유통업 CCC 30 일 vs 제조업 CCC 180 일 normal. 단순 비교 시 업종 보정.
        - 재고/매출채권 없는 서비스업은 회전율 None.

    When:
        대시보드 efficiency 카드 빌드 시. 운영자본 효율 cross-company 비교 시.

    How:
        finance.parquet lazy filter → IS (매출/COGS) + BS (재고/매출채권/매입채무/유형자산/총자산)
        wide pivot → 회전율 / 일수 / CCC 계산 → 등급 분기.

    Requires:
        - 로컬 ``data/dart/scan/finance.parquet`` (``buildFinance`` 산출)
        - 매출 + COGS + BS 5 계정 + 매입채무

    SeeAlso:
        - :func:`dartlab.scan.financial.profitability.scanProfitability` — 절대 수익성 (분자)
        - :func:`dartlab.scan.financial.liquidity.scanLiquidity` — 유동성 보완
    """
    if verbose:
        _log.info("효율성 스캔: 계정 수집 중...")

    scanDir = _ensureScanData()
    scanPath = financeScanPath(scanDir)
    if not scanPath.exists():
        raise ScanDataError(
            "finance_prebuild_missing",
            "finance prebuild is required after _ensureScanData",
            source=scanPath,
        )
    result = _scanFromMerged(scanPath)

    if verbose:
        _log.info(f"효율성 스캔 완료: {result.height}종목")
    return result


__all__ = ["scanEfficiency"]
