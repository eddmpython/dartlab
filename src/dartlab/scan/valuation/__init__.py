"""밸류에이션 횡단 스캔 -- PER/PBR/PSR + 등급 (네이버 실시간)."""

from __future__ import annotations

import asyncio

import polars as pl

from dartlab.scan._helpers import scan_finance_parquets

_REVENUE_IDS = {"Revenue", "revenue", "ifrs-full_Revenue", "dart_Revenue"}
_REVENUE_NMS = {"매출액", "수익(매출액)", "영업수익"}

_CONCURRENCY = 50  # 동시 요청 제한


def _gradeValuation(pbr: float | None) -> str:
    """PBR 기준 밸류에이션 등급."""
    if pbr is None:
        return "해당없음"
    if pbr < 0:
        return "해당없음"
    if pbr < 0.5:
        return "저평가"
    if pbr <= 1.5:
        return "적정"
    if pbr <= 3.0:
        return "고평가"
    return "과열"


async def _fetchAll(codes: list[str], verbose: bool) -> dict[str, dict]:
    """네이버 API 배치 수집."""
    import httpx

    from dartlab.gather.domains.naver import fetch_price

    result: dict[str, dict] = {}
    sem = asyncio.Semaphore(_CONCURRENCY)

    async def _fetch(code: str, client: httpx.AsyncClient) -> None:
        async with sem:
            try:
                snap = await fetch_price(code, client)
                if snap and snap.market_cap and snap.market_cap > 0:
                    result[code] = {
                        "marketCap": snap.market_cap,
                        "per": snap.per if snap.per else None,
                        "pbr": snap.pbr if snap.pbr else None,
                        "dividendYield": snap.dividend_yield if snap.dividend_yield else None,
                        "current": snap.current,
                    }
            except (httpx.HTTPError, ValueError, AttributeError):
                pass

    async with httpx.AsyncClient(timeout=10) as client:
        total = len(codes)
        batch = 200
        for i in range(0, total, batch):
            chunk = codes[i : i + batch]
            tasks = [_fetch(c, client) for c in chunk]
            await asyncio.gather(*tasks)
            if verbose:
                print(f"  {min(i + batch, total)}/{total} 수집...")

    return result


def scanValuation(*, verbose: bool = True) -> pl.DataFrame:
    """전종목 밸류에이션 스캔 -- PER/PBR/PSR + 등급.

    네이버 API에서 실시간 수집. 2700종목 기준 2-3분 소요.
    """
    if verbose:
        print("밸류에이션 스캔: 상장사 목록 수집...")

    # 상장사 코드 목록
    import dartlab as _dl

    listing = _dl.listing()
    codes = listing["종목코드"].to_list() if "종목코드" in listing.columns else []
    if not codes:
        return pl.DataFrame()

    if verbose:
        print(f"  {len(codes)}종목 → 네이버 API 수집 시작")

    # 매출 데이터 (PSR 계산용)
    revMap = scan_finance_parquets("IS", _REVENUE_IDS, _REVENUE_NMS)

    # async 수집
    priceMap = asyncio.run(_fetchAll(codes, verbose))

    if verbose:
        print(f"  수집 완료: {len(priceMap)}종목")

    rows: list[dict] = []
    for code, data in priceMap.items():
        mc = data["marketCap"]
        per = data["per"]
        pbr = data["pbr"]
        dy = data["dividendYield"]

        # PSR = 시가총액(원) / 매출(원) — 둘 다 원 단위
        rev = revMap.get(code)
        psr = round(mc / rev, 2) if rev and rev > 0 and mc > 0 else None

        rows.append(
            {
                "stockCode": code,
                "marketCap": round(mc),
                "per": per,
                "pbr": pbr,
                "psr": psr,
                "dividendYield": dy,
                "grade": _gradeValuation(pbr),
            }
        )

    if verbose:
        print(f"밸류에이션 스캔 완료: {len(rows)}종목")

    if not rows:
        return pl.DataFrame()

    schema = {
        "stockCode": pl.Utf8,
        "marketCap": pl.Float64,
        "per": pl.Float64,
        "pbr": pl.Float64,
        "psr": pl.Float64,
        "dividendYield": pl.Float64,
        "grade": pl.Utf8,
    }
    return pl.DataFrame(rows, schema=schema)


__all__ = ["scanValuation"]
