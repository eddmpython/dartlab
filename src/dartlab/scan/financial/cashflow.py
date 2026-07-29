"""현금흐름 패턴 분류 — OCF/ICF/FCF + 라이프사이클 패턴.

Note: 여기서 FCF는 OCF + ICF (투자활동 후 잔여현금)이다.
analysis의 FCF(OCF - CAPEX)와 다르다.
프리빌드 parquet에서 CAPEX를 개별 추출할 수 없으므로 ICF 전체를 사용한다.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan.io.parquet import (
    ScanDataError,
    _ensureScanData,
    financeScanPath,
    scanLatestAccountValues,
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


def _classifyPattern(ocf: float | None, icf: float | None, finCf: float | None) -> str:
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
    if ocf is None or icf is None or finCf is None:
        return "자료부족"
    key = (
        "P" if ocf >= 0 else "N",
        "P" if icf >= 0 else "N",
        "P" if finCf >= 0 else "N",
    )
    return _PATTERNS.get(key, "미분류")


def _patternExpr() -> pl.Expr:
    """세 현금흐름 부호를 pattern label로 바꾸는 벡터식."""

    complete = pl.col("ocf").is_not_null() & pl.col("icf").is_not_null() & pl.col("finCf").is_not_null()
    return (
        pl.when(~complete)
        .then(pl.lit("자료부족"))
        .when((pl.col("ocf") >= 0) & (pl.col("icf") < 0) & (pl.col("finCf") < 0))
        .then(pl.lit("성장투자형"))
        .when((pl.col("ocf") >= 0) & (pl.col("icf") < 0) & (pl.col("finCf") >= 0))
        .then(pl.lit("공격성장형"))
        .when((pl.col("ocf") >= 0) & (pl.col("icf") >= 0) & (pl.col("finCf") < 0))
        .then(pl.lit("구조재편형"))
        .when((pl.col("ocf") >= 0) & (pl.col("icf") >= 0) & (pl.col("finCf") >= 0))
        .then(pl.lit("현금축적형"))
        .when((pl.col("ocf") < 0) & (pl.col("icf") < 0) & (pl.col("finCf") >= 0))
        .then(pl.lit("외부의존형"))
        .when((pl.col("ocf") < 0) & (pl.col("icf") >= 0) & (pl.col("finCf") < 0))
        .then(pl.lit("축소정리형"))
        .when((pl.col("ocf") < 0) & (pl.col("icf") >= 0) & (pl.col("finCf") >= 0))
        .then(pl.lit("위기대응형"))
        .otherwise(pl.lit("현금위기형"))
    )


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
    values = scanLatestAccountValues(
        scanPath,
        {
            "ocf": (OCF_IDS, OCF_NMS, {"CF"}),
            "icf": (ICF_IDS, ICF_NMS, {"CF"}),
            "finCf": (FINCF_IDS, FINCF_NMS, {"CF"}),
        },
    )
    if values.is_empty():
        return pl.DataFrame()

    return (
        values.filter(pl.col("ocf").is_not_null())
        .with_columns(
            pl.when(pl.col("icf").is_not_null()).then(pl.col("ocf") + pl.col("icf")).otherwise(None).alias("fcf"),
            _patternExpr().alias("pattern"),
        )
        .with_columns(
            pl.col("ocf").round(0).cast(pl.Int64),
            pl.col("icf").round(0).cast(pl.Int64),
            pl.col("finCf").round(0).cast(pl.Int64),
            pl.col("fcf").round(0).cast(pl.Int64),
        )
        .select("stockCode", "ocf", "icf", "finCf", "fcf", "pattern")
    )


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
    if not scanPath.exists():
        raise ScanDataError(
            "finance_prebuild_missing",
            "finance prebuild is required after _ensureScanData",
            source=scanPath,
        )
    return _scanFromMerged(scanPath)
