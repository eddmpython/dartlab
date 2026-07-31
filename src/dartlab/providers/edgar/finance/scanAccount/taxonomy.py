"""snakeId <-> XBRL concept key 해소와 ticker universe 정규화.

계정 이름 해석과 회사 identity 부착만 소유한다. parquet 실행은 ``pipeline`` 이 맡는다."""

from __future__ import annotations

import polars as pl

from dartlab.core.accounts.aliases import SNAKEID_ALIASES
from dartlab.core.accounts.data import loadAccounts
from dartlab.providers.edgar.finance.mapper import EDGAR_TO_DART_ALIASES, EdgarMapper
from dartlab.providers.edgar.finance.scanAccount.types import (
    EdgarScanMappingError,
    _TaxonomyTagKeys,
    _TickerUniverse,
)


def _canonicalSnakeId(snakeId: str) -> str:
    seen: set[str] = set()
    current = snakeId
    while current not in seen and current in SNAKEID_ALIASES:
        seen.add(current)
        current = SNAKEID_ALIASES[current]
    return current


def _buildEdgarTagKeys(dartSnakeId: str) -> _TaxonomyTagKeys:
    """snakeId에 대응하는 US GAAP과 IFRS concept key를 SSOT에서 파생."""
    try:
        tagMap = EdgarMapper.tagMap()
        mappings = loadAccounts().get("mappings", {})
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        raise EdgarScanMappingError(
            "account_mapping",
            f"account SSOT load failed: {type(exc).__name__}: {exc}",
        ) from exc
    target = _canonicalSnakeId(dartSnakeId)

    edgarIds = {dartSnakeId, target}
    for edgarSid, dartSid in EDGAR_TO_DART_ALIASES.items():
        if _canonicalSnakeId(dartSid) == target:
            edgarIds.add(edgarSid)

    usGaap: set[str] = set()
    for tag, sid in tagMap.items():
        if sid in edgarIds or _canonicalSnakeId(sid) == target:
            usGaap.add(tag.lower())

    ifrsFull: set[str] = set()
    for concept, sid in mappings.items():
        if (
            concept
            and concept[0].isupper()
            and concept.isascii()
            and concept.isalnum()
            and _canonicalSnakeId(str(sid)) == target
        ):
            ifrsFull.add(concept.lower())

    preferred: list[str] = []
    for account in loadAccounts().get("edgar", {}).get("accounts", []):
        if _canonicalSnakeId(str(account.get("snakeId", ""))) != target:
            continue
        for tag in account.get("commonTags", []):
            tagLower = str(tag).lower()
            if tagLower not in preferred:
                preferred.append(tagLower)
    usGaap.update(preferred)
    ifrsFull.update(preferred)

    def prioritized(tags: set[str]) -> tuple[str, ...]:
        """common tag를 먼저 두고 learned tag를 결정적으로 뒤에 둔다.

        Args:
            tags: 한 taxonomy에서 모은 소문자 concept key 집합.

        Returns:
            tuple[str, ...]: 표준 tag가 앞, 나머지는 사전순. 같은 입력은 같은 순서를
                내므로 tag 우선순위가 실행마다 흔들리지 않는다.

        Raises:
            없음. 순수 정렬이다.

        Example:
            >>> sorted({"b", "a"}) == ["a", "b"]
            True
        """
        primary = [tag for tag in preferred if tag in tags]
        return tuple([*primary, *sorted(tags - set(primary))])

    common = frozenset(preferred)
    return _TaxonomyTagKeys(
        prioritized(usGaap),
        prioritized(ifrsFull),
        common,
        common,
    )


def _loadTickerUniverse() -> _TickerUniverse:
    """SEC ticker universe를 검증하고 CIK 기준 대표 ticker로 정규화."""
    try:
        from dartlab.core.edgarClient import loadTickers

        tickerFrame = loadTickers()
    except (ImportError, OSError, RuntimeError, pl.exceptions.PolarsError) as exc:
        raise EdgarScanMappingError(
            "ticker_universe",
            f"ticker universe load failed: {type(exc).__name__}: {exc}",
        ) from exc

    if not isinstance(tickerFrame, pl.DataFrame):
        raise EdgarScanMappingError(
            "ticker_universe",
            f"ticker universe must be DataFrame, got {type(tickerFrame).__name__}",
        )
    required = {"ticker", "cik", "title"}
    missing = sorted(required - set(tickerFrame.columns))
    if missing:
        raise EdgarScanMappingError("ticker_universe", f"missing columns: {missing}")
    if tickerFrame.is_empty():
        raise EdgarScanMappingError("ticker_universe", "ticker universe is empty")

    cikToTicker: dict[str, str] = {}
    tickerToTitle: dict[str, str] = {}
    for rowIndex, row in enumerate(tickerFrame.select("ticker", "cik", "title").iter_rows(named=True)):
        ticker = str(row["ticker"] or "").strip().upper()
        cikRaw = str(row["cik"] or "").strip()
        if not ticker or not cikRaw.isdigit() or len(cikRaw) > 10:
            raise EdgarScanMappingError(
                "ticker_universe",
                f"invalid row={rowIndex}, ticker={ticker!r}, cik={cikRaw!r}",
            )
        cik = cikRaw.zfill(10)
        title = str(row["title"] or ticker).strip() or ticker
        cikToTicker.setdefault(cik, ticker)
        tickerToTitle.setdefault(ticker, title)

    return _TickerUniverse(cikToTicker, tickerToTitle)


def _joinCorpName(
    df: pl.DataFrame,
    tickerToTitle: dict[str, str] | None = None,
) -> pl.DataFrame:
    """검증된 ticker universe로 corpName을 추가."""
    if df.is_empty():
        return df
    if "stockCode" not in df.columns:
        raise EdgarScanMappingError("corp_name_join", "result has no stockCode column")
    if tickerToTitle is None:
        tickerToTitle = _loadTickerUniverse().tickerToTitle

    missing = sorted(set(df["stockCode"].drop_nulls().to_list()) - set(tickerToTitle))
    if missing:
        raise EdgarScanMappingError(
            "corp_name_join",
            f"result tickers are absent from ticker universe: {missing[:10]}",
        )
    titles = pl.DataFrame(
        {
            "stockCode": list(tickerToTitle),
            "corpName": list(tickerToTitle.values()),
        }
    )
    periodCols = [column for column in df.columns if column != "stockCode"]
    return df.join(titles, on="stockCode", how="left").select(["stockCode", "corpName", *periodCols])
