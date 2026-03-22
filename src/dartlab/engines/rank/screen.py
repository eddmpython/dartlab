"""시장 스크리닝 — rank 스냅샷 위에 프리셋 필터.

전체 종목의 재무비율을 기반으로 조건부 필터링.
rank.buildSnapshot() → ratios 수집 → 프리셋별 필터.

Example::

    from dartlab.engines.rank.screen import screen, presets
    df = screen("가치주")
    df = screen("고위험")
    print(presets())  # 사용 가능한 프리셋 목록
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict
from pathlib import Path

import polars as pl

logger = logging.getLogger(__name__)

from dartlab.core.dataConfig import DATA_RELEASES

# 스크리닝에 사용할 비율 필드
_RATIO_FIELDS = [
    "revenueTTM",
    "operatingIncomeTTM",
    "netIncomeTTM",
    "totalAssets",
    "totalEquity",
    "roe",
    "roa",
    "operatingMargin",
    "netMargin",
    "grossMargin",
    "ebitdaMargin",
    "costOfSalesRatio",
    "sgaRatio",
    "debtRatio",
    "currentRatio",
    "quickRatio",
    "equityRatio",
    "interestCoverage",
    "netDebtRatio",
    "noncurrentRatio",
    "totalAssetTurnover",
    "inventoryTurnover",
    "receivablesTurnover",
    "payablesTurnover",
    "fcf",
    "operatingCfMargin",
    "operatingCfToNetIncome",
    "capexRatio",
    "dividendPayoutRatio",
]

# ── 프리셋 정의 ──

PRESETS: dict[str, dict] = {
    "가치주": {
        "label": "우량 가치주",
        "description": "높은 수익성 + 낮은 부채 + 안정적",
        "conditions": [
            pl.col("roe") >= 10,
            pl.col("debtRatio") <= 100,
            pl.col("operatingMargin") >= 5,
            pl.col("currentRatio") >= 150,
        ],
    },
    "성장주": {
        "label": "고성장주",
        "description": "높은 수익성 + 대형 매출",
        "conditions": [
            pl.col("roe") >= 15,
            pl.col("operatingMargin") >= 10,
            pl.col("revenueTTM") >= 100_000_000_000,
        ],
    },
    "턴어라운드": {
        "label": "턴어라운드 후보",
        "description": "적자이나 부채 낮아 회복 여지",
        "conditions": [
            pl.col("roe") < 0,
            pl.col("roe") > -30,
            pl.col("debtRatio") <= 80,
            pl.col("currentRatio") >= 150,
            pl.col("totalAssets") >= 50_000_000_000,
        ],
    },
    "현금부자": {
        "label": "현금부자",
        "description": "FCF 풍부 + 낮은 부채",
        "conditions": [
            pl.col("fcf") > 0,
            pl.col("operatingCfMargin") >= 10,
            pl.col("debtRatio") <= 60,
        ],
    },
    "고위험": {
        "label": "고위험 고부채",
        "description": "높은 부채 + 이자 부담 큼",
        "conditions": [
            pl.col("debtRatio") >= 200,
            pl.col("interestCoverage").is_not_null(),
            pl.col("interestCoverage") < 3,
        ],
    },
    "자본잠식": {
        "label": "자본잠식 우려",
        "description": "자기자본비율 매우 낮음",
        "conditions": [
            pl.col("equityRatio") < 20,
            pl.col("roe") < 0,
        ],
    },
    "소형고수익": {
        "label": "초소형 고수익",
        "description": "총자산 작지만 수익성 높음",
        "conditions": [
            pl.col("totalAssets") < 100_000_000_000,
            pl.col("totalAssets") > 10_000_000_000,
            pl.col("roe") >= 15,
            pl.col("operatingMargin") >= 10,
        ],
    },
    "대형안정": {
        "label": "대형 안정주",
        "description": "대형주 + 안정적 재무",
        "conditions": [
            pl.col("totalAssets") >= 1_000_000_000_000,
            pl.col("debtRatio") <= 150,
            pl.col("roe") >= 5,
            pl.col("currentRatio") >= 100,
        ],
    },
}


def _financeExists(stockCode: str) -> bool:
    from dartlab import config

    dataDir = Path(config.dataDir) / DATA_RELEASES["finance"]["dir"]
    return (dataDir / f"{stockCode}.parquet").exists()


def buildMarketRatios(*, verbose: bool = True) -> pl.DataFrame:
    """전체 상장사 재무비율 DataFrame 생성.

    Returns:
        DataFrame (stockCode, corpName, sector, industryGroup, + 29 ratio columns).
    """
    from dartlab.engines.gather.listing import getKindList
    from dartlab.engines.common.finance.ratios import calcRatios
    from dartlab.engines.dart.finance.pivot import buildTimeseries
    from dartlab.engines.sector import classify

    kindDf = getKindList()
    codes = kindDf["종목코드"].to_list()
    names = kindDf["회사명"].to_list()
    industries = kindDf["업종"].to_list() if "업종" in kindDf.columns else [""] * len(codes)
    products = kindDf["주요제품"].to_list() if "주요제품" in kindDf.columns else [""] * len(codes)

    rows: list[dict] = []
    t0 = time.time()

    for i, code in enumerate(codes):
        if verbose and (i + 1) % 500 == 0:
            elapsed = time.time() - t0
            logger.info("[screen] %d/%d (%ds)", i + 1, len(codes), elapsed)

        row: dict = {"stockCode": code, "corpName": names[i]}

        info = classify(names[i], industries[i], products[i])
        row["sector"] = info.sector.value if info.sector else None
        row["industryGroup"] = info.industryGroup.value if info.industryGroup else None

        if not _financeExists(code):
            for f in _RATIO_FIELDS:
                row[f] = None
            rows.append(row)
            continue

        try:
            result = buildTimeseries(code)
            if result is None:
                for f in _RATIO_FIELDS:
                    row[f] = None
                rows.append(row)
                continue

            ts, _periods = result
            rr = calcRatios(ts)
            rd = asdict(rr)
            for f in _RATIO_FIELDS:
                row[f] = rd.get(f)
        except (FileNotFoundError, RuntimeError, ValueError):
            for f in _RATIO_FIELDS:
                row[f] = None

        rows.append(row)

    if verbose:
        elapsed = time.time() - t0
        logger.info("[screen] %d종목 완료 (%ds)", len(rows), elapsed)

    return pl.DataFrame(rows)


# ── 캐시 ──

_MARKET_RATIOS: pl.DataFrame | None = None


def _ensureMarketRatios(*, verbose: bool = True) -> pl.DataFrame:
    global _MARKET_RATIOS
    if _MARKET_RATIOS is not None:
        return _MARKET_RATIOS
    _MARKET_RATIOS = buildMarketRatios(verbose=verbose)
    return _MARKET_RATIOS


# ── 공개 API ──


def presets() -> dict[str, str]:
    """사용 가능한 스크리닝 프리셋 목록.

    Returns:
        {프리셋명: 설명} dict.
    """
    return {k: v["description"] for k, v in PRESETS.items()}


def screen(preset: str, *, verbose: bool = True) -> pl.DataFrame:
    """프리셋 기반 시장 스크리닝.

    Args:
        preset: 프리셋 이름 (presets() 참조).

    Returns:
        조건에 맞는 종목 DataFrame.

    Example::

        from dartlab.engines.rank.screen import screen
        df = screen("가치주")
    """
    if preset not in PRESETS:
        available = ", ".join(PRESETS.keys())
        raise ValueError(f"알 수 없는 프리셋: '{preset}'. 사용 가능: {available}")

    df = _ensureMarketRatios(verbose=verbose)
    result = df
    for cond in PRESETS[preset]["conditions"]:
        result = result.filter(cond)

    return result.sort("roe", descending=True, nulls_last=True)


def screenCustom(
    conditions: list[pl.Expr],
    *,
    verbose: bool = True,
) -> pl.DataFrame:
    """커스텀 조건 스크리닝.

    Args:
        conditions: Polars 필터 조건 리스트.

    Example::

        from dartlab.engines.rank.screen import screenCustom
        import polars as pl
        df = screenCustom([pl.col("roe") >= 20, pl.col("sector") == "IT"])
    """
    df = _ensureMarketRatios(verbose=verbose)
    result = df
    for cond in conditions:
        result = result.filter(cond)
    return result


def benchmark(*, verbose: bool = True) -> pl.DataFrame:
    """섹터별 핵심 비율 벤치마크 (P10, P25, median, P75, P90).

    Returns:
        섹터 × 비율 벤치마크 DataFrame.

    Example::

        from dartlab.engines.rank.screen import benchmark
        bm = benchmark()
    """
    df = _ensureMarketRatios(verbose=verbose)
    ratios = ["roe", "debtRatio", "operatingMargin", "currentRatio", "totalAssetTurnover", "grossMargin"]

    rows = []
    for sector in df["sector"].drop_nulls().unique().sort().to_list():
        sdf = df.filter(pl.col("sector") == sector)
        row: dict = {"sector": sector, "count": sdf.shape[0]}
        for r in ratios:
            if r not in sdf.columns:
                continue
            col = sdf[r].drop_nulls().cast(pl.Float64)
            if col.len() < 5:
                continue
            row[f"{r}_p10"] = col.quantile(0.10)
            row[f"{r}_median"] = col.median()
            row[f"{r}_p90"] = col.quantile(0.90)
        rows.append(row)

    return pl.DataFrame(rows)
