"""DART와 EDGAR 상장 entity universe의 owner-level resolver."""

from __future__ import annotations

import polars as pl


def listedEquityUniverse(
    *,
    market: str,
    membership: str = "listed",
    asOf: str | None = None,
) -> pl.DataFrame:
    """시장별 현재 상장 entity를 공통 identity schema로 반환한다.

    수집과 원천 해석은 lower owner에 남기고 Data Workbench에는 정규 identity만
    제공한다. 과거 membership과 상장폐지 포함 universe는 아직 원천 snapshot이
    없으므로 최신 목록으로 위장하지 않고 거부한다.
    """

    normalizedMarket = str(market).strip().upper()
    if membership != "listed":
        raise ValueError("UNIVERSE_MEMBERSHIP_UNSUPPORTED")
    if asOf is not None:
        raise ValueError("UNIVERSE_PIT_UNSUPPORTED")
    if normalizedMarket == "KR":
        from dartlab.core.listingResolver import getListingResolver

        resolver = getListingResolver()
        if resolver is None:
            raise RuntimeError("UNIVERSE_RESOLVER_UNAVAILABLE")
        frame = resolver.kindList()
        return (
            frame.select(
                pl.col("종목코드").cast(pl.Utf8).str.to_uppercase().str.zfill(6).alias("entityId"),
                pl.col("종목코드").cast(pl.Utf8).str.to_uppercase().str.zfill(6).alias("sourceEntityId"),
                pl.col("회사명").cast(pl.Utf8).alias("name"),
                pl.col("시장구분").cast(pl.Utf8).alias("exchange"),
                pl.col("결산월")
                .cast(pl.Utf8)
                .str.extract(r"(\d{1,2})", 1)
                .cast(pl.Int16, strict=False)
                .alias("param_fiscalYearEndMonth"),
            )
            .filter(
                pl.col("entityId").str.contains(r"^[0-9A-Z]{6}$") & pl.col("param_fiscalYearEndMonth").is_between(1, 12)
            )
            .with_columns(
                pl.lit("KR").alias("market"),
                pl.lit("dart").alias("provider"),
            )
            .unique("entityId", keep="first")
            .sort("entityId")
        )
    if normalizedMarket == "US":
        from dartlab.core.dataLoader import loadEdgarTargetUniverse

        # Data Workbench query는 관측 중 source를 갱신하지 않는다. 이미 존재하는
        # owner snapshot만 읽고 digest로 pin한다. 갱신은 gather/pipeline이 소유한다.
        frame = loadEdgarTargetUniverse("all", localOnly=True)
        return (
            frame.select(
                pl.col("ticker").cast(pl.Utf8).str.to_uppercase().alias("entityId"),
                pl.col("cik").cast(pl.Utf8).str.zfill(10).alias("sourceEntityId"),
                pl.col("title").cast(pl.Utf8).alias("name"),
                pl.col("exchange").cast(pl.Utf8).alias("exchange"),
            )
            .filter(pl.col("entityId").str.len_chars() > 0)
            .with_columns(
                pl.lit("US").alias("market"),
                pl.lit("edgar").alias("provider"),
            )
            .unique("entityId", keep="first")
            .sort("entityId")
        )
    raise ValueError("UNIVERSE_MARKET_UNSUPPORTED")


__all__ = ["listedEquityUniverse"]
