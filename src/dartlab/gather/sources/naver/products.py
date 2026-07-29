"""네이버 ETF·ETN 상품 목록 수집 (JSON API, euc-kr) — 로컬 개인용.

⚠ 데이터 출처 고지
    네이버 금융 데이터다. 로컬 개인 분석은 무방하나 재배포·공개(HF 적재·서비스 배포·제3자
    공개)는 데이터베이스제작자의 권리(저작권법 제4장)·저작권 문제가 발생할 수 있다.

구조 (실측 2026-06-29)
    그룹(테마/업종)과 달리 단일 JSON 호출 → 상품 목록 + 현재가 스냅샷.
    ETF ``api/sise/etfItemList.nhn`` (약 1142), ETN ``api/sise/etnItemList.nhn`` (약 377).
    응답은 euc-kr 인코딩. 가격은 장중 변동이라 freshness 저장 없이 매 호출 라이브.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import polars as pl

from ...infra.http import GatherHttpClient

_ETF_URL = "https://finance.naver.com/api/sise/etfItemList.nhn"
_ETN_URL = "https://finance.naver.com/api/sise/etnItemList.nhn"
_HEADERS = {"Referer": "https://finance.naver.com/sise/"}

# raw JSON 키 → 정리된 컬럼명.
_ETF_COLS: dict[str, str] = {
    "itemcode": "code",
    "itemname": "name",
    "nowVal": "price",
    "changeRate": "changeRate",
    "nav": "nav",
    "threeMonthEarnRate": "return3m",
    "quant": "volume",
    "amonut": "amount",
    "marketSum": "marketCap",
    "etfTabCode": "tabCode",
}
_ETN_COLS: dict[str, str] = {
    "itemcode": "code",
    "itemname": "name",
    "nowVal": "price",
    "changeRate": "changeRate",
    "accQuant": "volume",
    "accAmount": "amount",
    "marketSum": "marketCap",
    "listedStockCount": "listedShares",
    "prevClose": "prevClose",
    "highVal": "high",
    "lowVal": "low",
}


async def _fetchProducts(client: GatherHttpClient, url: str, listKey: str, columns: dict[str, str], target):
    """JSON API(euc-kr) → 정리 컬럼 DataFrame, target 있으면 name contains 필터."""
    resp = await client.get(url, headers=_HEADERS)
    data = json.loads(resp.content.decode("euc-kr"))
    if not isinstance(data, dict) or not isinstance(data.get("result"), dict):
        raise TypeError("Naver 상품 응답의 result는 JSON object여야 합니다")
    result = data["result"]
    if listKey not in result:
        raise KeyError(f"Naver 상품 응답에 {listKey}가 없습니다")
    rows = result[listKey]
    if not isinstance(rows, list):
        raise TypeError(f"Naver 상품 응답의 {listKey}는 list여야 합니다")
    provenanceSchema = {"source": pl.Utf8, "fetchedAt": pl.Utf8}
    if not rows:
        valueSchema = {v: pl.Utf8 if v in ("code", "name") else pl.Float64 for v in columns.values()}
        return pl.DataFrame(schema={**valueSchema, **provenanceSchema})
    df = (
        pl.DataFrame(rows)
        .select([pl.col(k).alias(v) for k, v in columns.items()])
        .with_columns(
            pl.lit("naver").alias("source"),
            pl.lit(datetime.now(timezone.utc).isoformat()).alias("fetchedAt"),
        )
    )
    if target:
        df = df.filter(pl.col("name").str.contains(str(target), literal=True))
    return df


async def collectEtf(client: GatherHttpClient, target: str | None = None) -> pl.DataFrame:
    """네이버 ETF 상품 목록 + 현재가 스냅샷 수집 (단일 JSON, 라이브).

    Capabilities: etfItemList.nhn(euc-kr) → code/name/price/changeRate/nav/return3m/volume/amount/marketCap/tabCode.
    AIContext: gather('naverEtf') 본체 — 그룹과 달리 단일 호출(저장 없음, 장중 가격 라이브).
    Guide: target 있으면 종목명 contains 필터. 약 1142 종목.
    When: handleNaverEtf 가 호출.
    How: client.get(_ETF_URL) → euc-kr decode → json → 컬럼 정리 → (옵션) name 필터.

    Args:
        client: GatherHttpClient.
        target: 종목명 부분 일치 필터 (None=전체).

    Returns:
        pl.DataFrame — 가격 필드 + source/fetchedAt.

    Raises:
        ValueError / TypeError / KeyError — JSON 또는 응답 schema 오류.

    Example::

        await collectEtf(client)          # 전체 ETF
        await collectEtf(client, "KODEX")  # KODEX 계열

    Requires:
        네트워크 (finance.naver.com 무인증). 산출물 재배포 금지(DB권/저작권).

    See Also:
        collectEtn : ETN 상품 목록.
    """
    return await _fetchProducts(client, _ETF_URL, "etfItemList", _ETF_COLS, target)


async def collectEtn(client: GatherHttpClient, target: str | None = None) -> pl.DataFrame:
    """네이버 ETN 상품 목록 + 현재가 스냅샷 수집 (단일 JSON, 라이브).

    Capabilities: etnItemList.nhn(euc-kr) → code/name/price/changeRate/volume/amount/marketCap/listedShares/prevClose/high/low.
    AIContext: gather('naverEtn') 본체 — 단일 호출(저장 없음, 장중 가격 라이브).
    Guide: target 있으면 종목명 contains 필터. 약 377 종목.
    When: handleNaverEtn 가 호출.
    How: client.get(_ETN_URL) → euc-kr decode → json → 컬럼 정리 → (옵션) name 필터.

    Args:
        client: GatherHttpClient.
        target: 종목명 부분 일치 필터 (None=전체).

    Returns:
        pl.DataFrame — 가격 필드 + source/fetchedAt.

    Raises:
        ValueError / TypeError / KeyError — JSON 또는 응답 schema 오류.

    Example::

        await collectEtn(client)          # 전체 ETN
        await collectEtn(client, "원유")   # 원유 ETN

    Requires:
        네트워크 (finance.naver.com 무인증). 산출물 재배포 금지(DB권/저작권).

    See Also:
        collectEtf : ETF 상품 목록.
    """
    return await _fetchProducts(client, _ETN_URL, "etnItemList", _ETN_COLS, target)
