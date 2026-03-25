"""전종목 EDGAR 단일 계정/비율 시계열 배치 추출.

EDGAR finance parquet({cik}.parquet)를 병렬 스캔하여
특정 snakeId 하나의 전종목 × 기간 시계열 DataFrame을 반환한다.

연간: FY 직접값 (IS/CF=연간합계, BS=시점잔액)
분기: FY + Q1-Q3 standalone (기존 pivot 로직 재활용)
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import polars as pl

from dartlab.engines.company.edgar.finance.mapper import EDGAR_TO_DART_ALIASES, EdgarMapper

_log = logging.getLogger(__name__)


def _buildEdgarTagKeys(dartSnakeId: str) -> set[str]:
    """dartSnakeId에 매핑되는 모든 EDGAR XBRL tag를 수집."""
    EdgarMapper._ensureLoaded()
    tagMap = EdgarMapper._tagMap or {}

    # DART alias → EDGAR snakeId 역매핑
    edgarIds = {dartSnakeId}
    for edgarSid, dartSid in EDGAR_TO_DART_ALIASES.items():
        if dartSid == dartSnakeId:
            edgarIds.add(edgarSid)

    tags: set[str] = set()
    for tag, sid in tagMap.items():
        if sid in edgarIds:
            tags.add(tag)

    return tags


def _joinCorpName(df: pl.DataFrame) -> pl.DataFrame:
    """ticker에 회사명(corpName) 매핑."""
    try:
        from dartlab.engines.company.edgar.openapi.identity import loadTickers

        tickers = loadTickers().select(
            pl.col("ticker").alias("stockCode"),
            pl.col("title").alias("corpName"),
        )
        periodCols = [c for c in df.columns if c != "stockCode"]
        return df.join(tickers, on="stockCode", how="left").select(["stockCode", "corpName"] + periodCols)
    except (ImportError, OSError, pl.exceptions.PolarsError):
        return df


class _EdgarFileProcessor:
    """EDGAR parquet 파일별 처리."""

    __slots__ = ("tagKeys", "annual", "cikToTicker")

    def __init__(self, tagKeys: set[str], *, annual: bool, cikToTicker: dict[str, str]):
        self.tagKeys = list(tagKeys)
        self.annual = annual
        self.cikToTicker = cikToTicker

    def __call__(self, pf: Path) -> pl.DataFrame | None:
        cik = pf.stem
        ticker = self.cikToTicker.get(cik)
        if ticker is None:
            return None

        try:
            df = (
                pl.scan_parquet(str(pf))
                .filter(
                    (pl.col("namespace") == "us-gaap")
                    & pl.col("tag").str.to_lowercase().is_in(self.tagKeys)
                    & pl.col("unit").str.starts_with("USD")
                    & pl.col("fy").is_not_null()
                    & (pl.col("fy") >= 2000)
                    & (pl.col("fy") <= 2030)
                )
                .select(["tag", "val", "fy", "fp"])
                .collect()
            )
        except (pl.exceptions.PolarsError, OSError):
            return None

        if df.is_empty():
            return None

        if self.annual:
            return self._parseAnnual(df, ticker)
        return self._parseQuarterly(df, ticker)

    def _parseAnnual(self, df: pl.DataFrame, ticker: str) -> pl.DataFrame | None:
        """연간: FY 값."""
        fy = df.filter(pl.col("fp") == "FY")
        if fy.is_empty():
            return None

        # 연도별 첫 값
        agg = fy.group_by("fy").agg(pl.col("val").first()).sort("fy")
        rows = []
        for row in agg.iter_rows(named=True):
            if row["val"] is not None:
                rows.append(
                    {
                        "stockCode": ticker,
                        "period": str(row["fy"]),
                        "amount": float(row["val"]),
                    }
                )
        return pl.DataFrame(rows) if rows else None

    def _parseQuarterly(self, df: pl.DataFrame, ticker: str) -> pl.DataFrame | None:
        """분기: FY + frame 기반 standalone Q1-Q3 → Q4 역산."""
        rows: list[dict] = []

        for fy in df["fy"].unique().sort().to_list():
            yearDf = df.filter(pl.col("fy") == fy)

            # Q1-Q3: standalone = frame이 있는 행 (CYxxxxQn 형태)
            qVals: dict[str, float] = {}
            for fp in ["Q1", "Q2", "Q3"]:
                fpDf = yearDf.filter(pl.col("fp") == fp)
                if fpDf.is_empty():
                    continue
                # standalone 선택: 기간이 짧은(~90일) 행 우선
                vals = fpDf["val"].drop_nulls().to_list()
                if vals:
                    # 가장 작은 양수값이 standalone일 가능성 높음 (YTD > standalone)
                    absVals = [(abs(v), v) for v in vals if v is not None]
                    if absVals:
                        standalone = min(absVals)[1]
                        qNum = fp[1]
                        qVals[f"Q{qNum}"] = standalone
                        rows.append({"stockCode": ticker, "period": f"{fy}Q{qNum}", "amount": standalone})

            # Q4 = FY - Q1 - Q2 - Q3
            fyDf = yearDf.filter(pl.col("fp") == "FY")
            if not fyDf.is_empty():
                fyVal = fyDf["val"].drop_nulls().to_list()
                if fyVal:
                    annual = fyVal[0]
                    if len(qVals) == 3:
                        q4 = annual - sum(qVals.values())
                        rows.append({"stockCode": ticker, "period": f"{fy}Q4", "amount": q4})
                    else:
                        rows.append({"stockCode": ticker, "period": f"{fy}Q4", "amount": annual})

        return pl.DataFrame(rows) if rows else None


def scanAccount(
    dartSnakeId: str,
    *,
    annual: bool = False,
) -> pl.DataFrame:
    """전종목 EDGAR 단일 계정 시계열.

    Args:
        dartSnakeId: DART canonical snakeId (예: "sales", "total_assets").
        annual: True면 연간 (기본 False=분기별).

    Returns:
        stockCode(=ticker) | corpName | 기간컬럼들... (최신 먼저)
    """
    from dartlab.core.dataLoader import _dataDir

    edgarDir = Path(_dataDir("edgar"))
    parquetFiles = sorted(edgarDir.glob("*.parquet"))

    if not parquetFiles:
        _log.warning("EDGAR finance parquet 없음: %s", edgarDir)
        return pl.DataFrame({"stockCode": []})

    # CIK → ticker 매핑
    try:
        from dartlab.engines.company.edgar.openapi.identity import loadTickers

        tickerDf = loadTickers()
        cikToTicker = dict(
            zip(
                tickerDf["cik"].to_list(),
                tickerDf["ticker"].to_list(),
            )
        )
    except (ImportError, OSError):
        cikToTicker = {}

    tagKeys = _buildEdgarTagKeys(dartSnakeId)
    if not tagKeys:
        _log.warning("EDGAR에서 '%s'에 매핑되는 tag 없음", dartSnakeId)
        return pl.DataFrame({"stockCode": []})

    processor = _EdgarFileProcessor(tagKeys, annual=annual, cikToTicker=cikToTicker)

    _log.info("scanAccount(edgar, '%s', annual=%s): %d 파일 스캔", dartSnakeId, annual, len(parquetFiles))

    with ThreadPoolExecutor(max_workers=min(os.cpu_count() or 4, 8)) as pool:
        chunks = [r for r in pool.map(processor, parquetFiles) if r is not None]

    if not chunks:
        return pl.DataFrame({"stockCode": []})

    allDf = pl.concat(chunks)
    allDf = allDf.group_by(["stockCode", "period"]).agg(pl.col("amount").first())

    result = allDf.pivot(on="period", index="stockCode", values="amount")
    periodCols = sorted(
        (c for c in result.columns if c != "stockCode"),
        reverse=True,
    )
    result = result.select(["stockCode"] + periodCols)

    result = _joinCorpName(result)

    _log.info("scanAccount(edgar): %d종목 × %d기간", result.height, len(periodCols))
    return result


# ── scanRatio (EDGAR) ─────────────────────────────────────────

# DART 비율 정의 재활용
from dartlab.engines.company.dart.finance.scanAccount import _RATIO_DEFS


def scanRatio(
    ratioName: str,
    *,
    annual: bool = False,
) -> pl.DataFrame:
    """전종목 EDGAR 재무비율 시계열.

    Args:
        ratioName: 비율 식별자. scanRatioList() 참조.
        annual: True면 연간 (기본 False=분기별).
    """
    if ratioName not in _RATIO_DEFS:
        available = ", ".join(sorted(_RATIO_DEFS))
        msg = f"지원하지 않는 비율: '{ratioName}'. 사용 가능: {available}"
        raise ValueError(msg)

    defn = _RATIO_DEFS[ratioName]

    if defn.get("yoy"):
        return _calcYoyRatio(defn, annual=annual)
    return _calcSimpleRatio(defn, annual=annual)


def _calcSimpleRatio(defn: dict, *, annual: bool = False) -> pl.DataFrame:
    """분자/분모 비율 계산."""
    numer = scanAccount(defn["numer"], annual=annual)
    denom = scanAccount(defn["denom"], annual=annual)

    numerCols = [c for c in numer.columns if c not in ("stockCode", "corpName")]
    denomCols = [c for c in denom.columns if c not in ("stockCode", "corpName")]
    commonCols = sorted(set(numerCols) & set(denomCols), reverse=True)

    if not commonCols:
        return pl.DataFrame({"stockCode": []})

    joined = numer.select(["stockCode"] + commonCols).join(
        denom.select(["stockCode"] + commonCols),
        on="stockCode",
        suffix="_d",
    )

    isPct = defn.get("pct", False)
    multiplier = 100.0 if isPct else 1.0

    resultExprs = [pl.col("stockCode")]
    for y in commonCols:
        expr = (
            pl.when((pl.col(f"{y}_d") != 0) & pl.col(f"{y}_d").is_not_null() & pl.col(y).is_not_null())
            .then((pl.col(y) / pl.col(f"{y}_d") * multiplier).round(2))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias(y)
        )
        resultExprs.append(expr)

    result = joined.select(resultExprs)
    return _joinCorpName(result)


def _calcYoyRatio(defn: dict, *, annual: bool = False) -> pl.DataFrame:
    """YoY 성장률 계산."""
    base = scanAccount(defn["base"], annual=annual)
    periodCols = sorted(c for c in base.columns if c not in ("stockCode", "corpName"))

    if len(periodCols) < 2:
        return pl.DataFrame({"stockCode": []})

    resultExprs = [pl.col("stockCode")]
    for i in range(1, len(periodCols)):
        cur = periodCols[i]
        prev = periodCols[i - 1]
        expr = (
            pl.when((pl.col(prev) != 0) & pl.col(prev).is_not_null() & pl.col(cur).is_not_null())
            .then(((pl.col(cur) - pl.col(prev)) / pl.col(prev).abs() * 100).round(2))
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias(cur)
        )
        resultExprs.append(expr)

    yoyCols = [periodCols[i] for i in range(1, len(periodCols))]
    result = base.select(resultExprs).select(["stockCode"] + list(reversed(yoyCols)))
    return _joinCorpName(result)
