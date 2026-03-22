"""EDGAR issuer identity 해석."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

from dartlab.core.dataLoader import loadEdgarListedUniverse
from dartlab.engines.company.edgar.openapi.client import DEFAULT_SEC_URL, EdgarClient

_TICKERS_URL = f"{DEFAULT_SEC_URL}/files/company_tickers.json"


def _tickersPath() -> Path:
    from dartlab import config

    return Path(config.dataDir) / "edgar" / "tickers.parquet"


def loadTickers(
    client: EdgarClient | None = None,
    *,
    refresh: bool = False,
) -> pl.DataFrame:
    path = _tickersPath()
    if path.exists() and not refresh:
        return pl.read_parquet(path)

    api = client or EdgarClient()
    payload = api.getJson(_TICKERS_URL)
    rows: list[dict[str, Any]] = []
    for record in payload.values():
        rows.append(
            {
                "ticker": str(record.get("ticker") or "").upper().strip(),
                "cik": str(record.get("cik_str") or "").zfill(10),
                "title": str(record.get("title") or "").strip(),
            }
        )

    df = pl.DataFrame(rows).filter(pl.col("ticker") != "")

    try:
        listed = loadEdgarListedUniverse()
        if not listed.is_empty():
            listedSlim = listed.select(
                [col for col in ("ticker", "exchange", "is_exchange_listed", "is_otc") if col in listed.columns]
            )
            df = df.join(listedSlim, on="ticker", how="left")
    except (FileNotFoundError, OSError, RuntimeError):
        pass

    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    return df


def resolveIssuer(
    query: str,
    client: EdgarClient | None = None,
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    if not query or not str(query).strip():
        raise ValueError("tickerOrCik가 비어 있음")

    text = str(query).strip()
    normalized = text.upper()
    cikQuery = text.zfill(10) if text.isdigit() else ""

    df = loadTickers(client, refresh=refresh)
    row = None

    if cikQuery:
        match = df.filter(pl.col("cik") == cikQuery)
        if match.height > 0:
            row = match.row(0, named=True)
    else:
        match = df.filter(pl.col("ticker") == normalized)
        if match.height > 0:
            row = match.row(0, named=True)

    if row is None:
        raise ValueError(f"{query}에 해당하는 CIK를 찾을 수 없음")

    return {
        "ticker": str(row.get("ticker") or normalized),
        "cik": str(row.get("cik") or "").zfill(10),
        "title": str(row.get("title") or normalized),
        "exchange": row.get("exchange"),
        "is_exchange_listed": row.get("is_exchange_listed"),
        "is_otc": row.get("is_otc"),
    }


def searchIssuers(
    query: str,
    client: EdgarClient | None = None,
    *,
    refresh: bool = False,
) -> pl.DataFrame:
    if not query or not str(query).strip():
        return pl.DataFrame(schema={"ticker": pl.Utf8, "cik": pl.Utf8, "title": pl.Utf8})

    df = loadTickers(client, refresh=refresh)
    text = str(query).strip()
    upper = text.upper()

    if text.isdigit():
        return df.filter(pl.col("cik").str.contains(text))

    return df.filter(
        pl.col("ticker").str.contains(upper, literal=True)
        | pl.col("title").str.to_uppercase().str.contains(upper, literal=True)
    ).sort(["ticker", "cik"])
