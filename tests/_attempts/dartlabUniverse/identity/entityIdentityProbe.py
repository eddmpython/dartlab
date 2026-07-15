"""Universe legal entity, security, filing identity와 alias admission을 검증한다.

Capabilities
    DART corpCode, KRX ISIN, SEC CIK, filing identifier를 분리하고 exact alias만 fail closed로 해소한다.

AIContext
    AI 역할: stockCode, ticker, fuzzy name을 legal entity SSOT로 승격하지 않고 ambiguity를 보존한다.

Guide
    Synthetic ambiguity contract와 local KR, US source census의 live readiness를 분리한다.

When
    U0-I01 canonical identity와 historical alias 가능성을 검증할 때 사용한다.

How
    Canonical ID builder를 먼저 검증하고 :func:`inspectIdentitySources`로 source gap을 측정한다.

Requires
    Live census 실행 시 Polars와 local DART, KRX, SEC parquet가 필요하다.

Raises
    ValueError: provider identifier, security, filing, alias validity 또는 target kind가 잘못됐을 때.

Example
    ``entityId = canonicalLegalEntityId("KR", "00126380")``

See Also
    :mod:`tests._attempts.dartlabUniverse.workflow.workflowProjectionProbe`.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
KR_STOCK_PATTERN = re.compile(r"^[0-9A-Z]{6}$")
US_TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9./-]{0,9}$")
US_ACCESSION_PATTERN = re.compile(r"^(\d{10})-?(\d{2})-?(\d{6})$")
VALIDITY_FIELDS = {"validFrom", "validTo", "tickerValidFrom", "tickerValidTo"}


def _market(value: str) -> str:
    market = str(value).strip().upper()
    if market not in {"KR", "US"}:
        raise ValueError(f"unsupported identity market: {value}")
    return market


def _isoDate(value: str, label: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"invalid {label}: {value}") from exc


def _normalizedAlias(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(normalized.split())


def canonicalLegalEntityId(market: str, providerId: str) -> str:
    """Provider legal identifier를 Universe canonical entity ID로 만든다.

    Capabilities
        KR corpCode 8자리와 US CIK10을 stockCode 또는 ticker와 분리한다.

    AIContext
        AI 역할: presentation key를 legal entity identity로 오인하지 않게 한다.

    Args
        market: KR 또는 US.
        providerId: DART corpCode 또는 SEC CIK.

    Returns
        Market과 provider namespace를 포함한 canonical entity ID.

    Example
        ``canonicalLegalEntityId("US", "320193")``

    Guide
        US CIK는 10자리로 zero pad하고 KR corpCode는 정확히 8자리만 받는다.

    When
        Legal entity node 또는 entity alias target을 만들 때 호출한다.

    How
        Market별 exact identifier syntax를 검증한 뒤 controlled prefix를 붙인다.

    Requires
        Provider가 발급한 exact identifier가 필요하다.

    See Also
        :func:`canonicalSecurityId`.

    Raises
        ValueError: market 또는 provider identifier 형식이 잘못됐을 때.
    """

    normalizedMarket = _market(market)
    identifier = str(providerId).strip()
    if normalizedMarket == "KR":
        if not re.fullmatch(r"\d{8}", identifier):
            raise ValueError("KR legal entity requires 8-digit corpCode")
        return f"kr:dart:corp:{identifier}"
    if not identifier.isdigit() or len(identifier) > 10:
        raise ValueError("US legal entity requires a CIK of at most 10 digits")
    return f"us:sec:cik:{identifier.zfill(10)}"


def canonicalSecurityId(
    market: str,
    *,
    isin: str = "",
    stockCode: str = "",
    ticker: str = "",
    exchange: str = "",
) -> str:
    """Legal entity와 분리한 KR 또는 US security ID를 만든다.

    Capabilities
        KR은 ISIN 우선과 stock fallback을 구분하고 US는 exchange와 ticker를 함께 묶는다.

    AIContext
        AI 역할: share class와 issuer를 하나의 node로 합치지 않게 한다.

    Args
        market: KR 또는 US.
        isin: KR security의 ISO 6166 identity.
        stockCode: ISIN이 없을 때 명시하는 KR presentation fallback.
        ticker: US current security ticker.
        exchange: US current exchange label.

    Returns
        Entity prefix와 겹치지 않는 canonical security ID.

    Example
        ``canonicalSecurityId("KR", isin="KR7005930003")``

    Guide
        Foreign issuer의 KRX listed ISIN도 country prefix를 보존해 수용한다.

    When
        Security node 또는 filing subject security를 만들 때 호출한다.

    How
        ISIN, fallback stockCode, exchange ticker 순으로 market contract를 검증한다.

    Requires
        KR은 ISIN 또는 stockCode, US는 ticker와 exchange가 필요하다.

    See Also
        :func:`canonicalLegalEntityId`.

    Raises
        ValueError: security identifier 또는 exchange 형식이 잘못됐을 때.
    """

    normalizedMarket = _market(market)
    if normalizedMarket == "KR":
        normalizedIsin = str(isin).strip().upper()
        if normalizedIsin:
            if not ISIN_PATTERN.fullmatch(normalizedIsin):
                raise ValueError("KR security ISIN is invalid")
            return f"kr:krx:security:{normalizedIsin}"
        normalizedStockCode = str(stockCode).strip().upper()
        if not KR_STOCK_PATTERN.fullmatch(normalizedStockCode):
            raise ValueError("KR security fallback requires a 6-character stockCode")
        return f"kr:krx:stock:{normalizedStockCode}"

    normalizedTicker = str(ticker).strip().upper()
    normalizedExchange = re.sub(r"[^a-z0-9]", "", str(exchange).strip().lower())
    if not US_TICKER_PATTERN.fullmatch(normalizedTicker) or not normalizedExchange:
        raise ValueError("US security requires exact ticker and exchange")
    return f"us:{normalizedExchange}:ticker:{normalizedTicker}"


def canonicalFilingId(market: str, providerFilingId: str) -> str:
    """DART receipt 또는 SEC accession을 canonical filing ID로 만든다.

    Capabilities
        KR 14자리 receipt와 US dashed accession을 market namespace로 분리한다.

    AIContext
        AI 역할: filing을 entity 또는 security identity와 혼합하지 않게 한다.

    Args
        market: KR 또는 US.
        providerFilingId: DART rcept_no 또는 SEC accession number.

    Returns
        원문 deep link에 사용할 canonical filing ID.

    Example
        ``canonicalFilingId("US", "0001193125-09-153165")``

    Guide
        US dash 없는 18자리 입력은 canonical dashed accession으로 정규화한다.

    When
        EvidencePointer와 filing node identity를 만들 때 호출한다.

    How
        Market별 exact syntax를 검증하고 provider namespace를 붙인다.

    Requires
        Provider가 발급한 receipt 또는 accession이 필요하다.

    See Also
        :func:`canonicalLegalEntityId`.

    Raises
        ValueError: filing identifier 형식이 잘못됐을 때.
    """

    normalizedMarket = _market(market)
    filingId = str(providerFilingId).strip()
    if normalizedMarket == "KR":
        if not re.fullmatch(r"\d{14}", filingId):
            raise ValueError("DART filing requires a 14-digit receipt number")
        return f"kr:dart:filing:{filingId}"
    match = US_ACCESSION_PATTERN.fullmatch(filingId)
    if match is None:
        raise ValueError("SEC filing requires a valid accession number")
    accession = "-".join(match.groups())
    return f"us:sec:filing:{accession}"


@dataclass(frozen=True)
class AliasRecord:
    """Alias가 가리키는 entity 또는 security와 validity source를 보존한다."""

    alias: str
    entityId: str
    securityId: str = ""
    validFrom: str = ""
    validTo: str = ""
    sourceRef: str = ""

    def __post_init__(self) -> None:
        if not self.alias or not self.entityId:
            raise ValueError("alias and entityId are required")
        validFrom = _isoDate(self.validFrom, "validFrom") if self.validFrom else ""
        validTo = _isoDate(self.validTo, "validTo") if self.validTo else ""
        if validFrom and validTo and validFrom > validTo:
            raise ValueError("validFrom cannot be newer than validTo")
        object.__setattr__(self, "validFrom", validFrom)
        object.__setattr__(self, "validTo", validTo)


@dataclass(frozen=True)
class AliasResolution:
    """Exact alias 결과를 resolved, ambiguous, unresolved validity로 구분한다."""

    query: str
    targetKind: str
    status: str
    matchedIds: tuple[str, ...]
    selectedId: str
    exactMatch: bool
    requiresValidity: bool

    def toDict(self) -> dict[str, Any]:
        """JSON compatible alias resolution payload를 반환한다.

        Returns
            Alias resolution dataclass를 mapping으로 바꾼 값.

        Example
            ``payload = resolution.toDict()``

        Requires
            Dataclass fields가 JSON compatible scalar를 가져야 한다.

        Raises
            TypeError: 향후 JSON 비호환 field가 추가됐을 때 encoder가 발생시킬 수 있다.
        """

        return asdict(self)


def resolveAlias(
    records: Iterable[AliasRecord],
    query: str,
    *,
    targetKind: str = "entity",
    validAt: str = "",
) -> AliasResolution:
    """Fuzzy match 없이 exact alias와 historical validity를 fail closed로 해소한다.

    Capabilities
        같은 alias의 다중 entity 또는 security를 ambiguous로 반환하고 selectedId를 비운다.

    AIContext
        AI 역할: 회사명 유사도나 첫 행을 근거로 cross-market entity를 자동 연결하지 않게 한다.

    Args
        records: Alias, identity, validity, source를 가진 records.
        query: Exact alias query.
        targetKind: entity 또는 security.
        validAt: Historical alias를 요청하는 ISO date.

    Returns
        Resolution status와 모든 matched identity를 가진 :class:`AliasResolution`.

    Example
        ``resolution = resolveAlias(records, "Apple Inc.", targetKind="entity")``

    Guide
        Unicode와 whitespace만 정규화하며 부분 문자열, edit distance, 번역은 사용하지 않는다.

    When
        Presentation alias를 canonical identity로 바꿀 때 호출한다.

    How
        Exact normalized alias를 찾고 validity completeness를 먼저 확인한 뒤 target identity를 deduplicate한다.

    Requires
        Historical query는 모든 matched record의 validFrom과 validTo가 필요하다.

    See Also
        :func:`canonicalLegalEntityId`.

    Raises
        ValueError: targetKind 또는 validAt 형식이 잘못됐을 때.
    """

    if targetKind not in {"entity", "security"}:
        raise ValueError(f"unsupported alias targetKind: {targetKind}")
    normalizedQuery = _normalizedAlias(query)
    if not normalizedQuery:
        return AliasResolution(str(query), targetKind, "unresolved", (), "", False, bool(validAt))
    matched = tuple(record for record in records if _normalizedAlias(record.alias) == normalizedQuery)
    if not matched:
        return AliasResolution(str(query), targetKind, "unresolved", (), "", False, bool(validAt))

    requestedDate = _isoDate(validAt, "validAt") if validAt else ""
    if requestedDate:
        if any(not record.validFrom or not record.validTo for record in matched):
            return AliasResolution(
                str(query),
                targetKind,
                "unresolvedValidity",
                (),
                "",
                True,
                True,
            )
        matched = tuple(record for record in matched if record.validFrom <= requestedDate < record.validTo)
        if not matched:
            return AliasResolution(str(query), targetKind, "unresolved", (), "", True, True)

    candidateValues = tuple(record.entityId if targetKind == "entity" else record.securityId for record in matched)
    values = tuple(sorted({value for value in candidateValues if value}))
    if not values:
        status = "unresolved"
        selectedId = ""
    elif len(values) == 1:
        status = "resolved"
        selectedId = values[0]
    else:
        status = "ambiguous"
        selectedId = ""
    return AliasResolution(str(query), targetKind, status, values, selectedId, True, bool(validAt))


@dataclass(frozen=True)
class IdentitySourceCensus:
    """Local KR, US identity source의 exact coverage와 historical blocker를 기록한다."""

    schemaVersion: str
    representative: bool
    krDartRowCount: int
    krListedLegalEntityRowCount: int
    krUniqueCorpCodeCount: int
    krUniqueStockCodeCount: int
    krLegalSampleCount: int
    krLegalSampleCanonicalCount: int
    krAmbiguousNameCount: int
    krAmbiguousStockCodeCount: int
    krHistoricalValidityFieldCount: int
    krxSecurityRowCount: int
    krxIsinCanonicalCount: int
    krxIssuerLinkCount: int
    krxIssuerGapCount: int
    usTickerRowCount: int
    usUniqueCikCount: int
    usUniqueTickerCount: int
    usLegalSampleCount: int
    usLegalSampleCanonicalCount: int
    usAmbiguousTitleCount: int
    usAmbiguousTickerCount: int
    usMultiSecurityEntityCount: int
    usHistoricalValidityFieldCount: int
    krFilingSourceFileCount: int
    krFilingSampleCount: int
    krFilingCanonicalCount: int
    usFilingSourceFileCount: int
    usFilingEntityCount: int
    usFilingSampleCount: int
    usFilingCanonicalCount: int
    exactIdentifierCoverage: float
    historicalAliasReady: bool
    liveReady: bool
    blockerReasons: tuple[str, ...]

    def toDict(self) -> dict[str, Any]:
        """JSON compatible identity census payload를 반환한다.

        Returns
            Census dataclass를 mapping으로 바꾼 값.

        Example
            ``payload = census.toDict()``

        Requires
            Dataclass fields가 JSON compatible scalar를 가져야 한다.

        Raises
            TypeError: 향후 JSON 비호환 field가 추가됐을 때 encoder가 발생시킬 수 있다.
        """

        return asdict(self)


def _ambiguousCount(frame, aliasColumn: str, identityColumn: str) -> int:
    import polars as pl

    return (
        frame.with_columns(
            pl.col(aliasColumn)
            .fill_null("")
            .cast(pl.Utf8)
            .str.to_lowercase()
            .str.replace_all(r"\s+", "")
            .alias("_alias")
        )
        .filter(pl.col("_alias") != "")
        .group_by("_alias")
        .agg(pl.col(identityColumn).n_unique().alias("identityCount"))
        .filter(pl.col("identityCount") > 1)
        .height
    )


def _filingSamples(financePath: Path, edgarPath: Path) -> tuple[tuple[str, ...], int, tuple[str, ...], int]:
    import polars as pl

    krFiles = tuple(sorted(financePath.glob("*.parquet"), key=lambda path: path.name)[:30])
    krReceipts: set[str] = set()
    for path in krFiles:
        schema = set(pl.scan_parquet(path).collect_schema().names())
        if "rcept_no" in schema:
            krReceipts.update(
                str(value)
                for value in pl.scan_parquet(path)
                .select("rcept_no")
                .unique()
                .collect()["rcept_no"]
                .drop_nulls()
                .to_list()
            )

    usFiles = tuple(
        path
        for path in sorted(edgarPath.glob("*.parquet"), key=lambda path: path.name)
        if re.fullmatch(r"\d{10}\.parquet", path.name)
    )
    usAccessions: set[str] = set()
    usEntities: set[str] = set()
    for path in usFiles:
        schema = set(pl.scan_parquet(path).collect_schema().names())
        if {"cik", "accn"}.issubset(schema):
            frame = pl.scan_parquet(path).select("cik", "accn").unique().collect()
            usAccessions.update(str(value) for value in frame["accn"].drop_nulls().to_list())
            usEntities.update(str(value) for value in frame["cik"].drop_nulls().to_list())
    return tuple(sorted(krReceipts)[:50]), len(krFiles), tuple(sorted(usAccessions)[:30]), len(usEntities)


def inspectIdentitySources(
    dartListPath: str | Path,
    krxListPath: str | Path,
    usTickersPath: str | Path,
    financePath: str | Path,
    edgarPath: str | Path,
    *,
    krSampleSize: int = 50,
    usSampleSize: int = 30,
) -> IdentitySourceCensus:
    """Local KR 50, US 30 legal identity와 security, filing source를 센서스한다.

    Capabilities
        Exact ID syntax, name ambiguity, share class, issuer link, filing과 historical validity coverage를 계수한다.

    AIContext
        AI 역할: current ticker lookup 성공을 historical legal identity 성공으로 확대하지 않는다.

    Args
        dartListPath: DART corpCode master parquet.
        krxListPath: KRX ISIN security parquet.
        usTickersPath: SEC ticker CIK parquet.
        financePath: KR filing receipt를 가진 finance directory.
        edgarPath: US company facts parquet directory.
        krSampleSize: 정렬된 listed DART legal entity sample 크기.
        usSampleSize: 정렬되고 deduplicate된 SEC legal entity sample 크기.

    Returns
        Exact identity coverage와 live blocker를 가진 census.

    Example
        ``census = inspectIdentitySources(dart, krx, us, finance, edgar)``

    Guide
        표본은 대표성을 주장하지 않는 deterministic schema sample이다.

    When
        Identity source나 listing resolver가 갱신된 뒤 U0-I01을 재심사할 때 호출한다.

    How
        CorpCode와 CIK sample을 canonicalize하고 KRX, DART join과 filing syntax를 별도 계수한다.

    Requires
        Polars와 local parquet source가 필요하다.

    See Also
        :func:`resolveAlias`.

    Raises
        ValueError: sample size가 양수가 아니거나 exact sample이 부족할 때.
        OSError: parquet source를 읽지 못할 때.
    """

    if krSampleSize <= 0 or usSampleSize <= 0:
        raise ValueError("identity sample sizes must be positive")
    import polars as pl

    dart = pl.read_parquet(dartListPath)
    krx = pl.read_parquet(krxListPath)
    us = pl.read_parquet(usTickersPath)
    dartListed = dart.filter(pl.col("stock_code").fill_null("").str.strip_chars() != "")
    krSample = dartListed.sort("corp_code").head(krSampleSize)
    usSample = us.sort("cik", "ticker").unique(subset=["cik"], keep="first").head(usSampleSize)
    if krSample.height != krSampleSize or usSample.height != usSampleSize:
        raise ValueError("identity sources do not contain the requested samples")

    krCanonicalCount = sum(bool(canonicalLegalEntityId("KR", value)) for value in krSample["corp_code"].to_list())
    usCanonicalCount = sum(bool(canonicalLegalEntityId("US", value)) for value in usSample["cik"].to_list())
    krxIsinCanonicalCount = sum(bool(canonicalSecurityId("KR", isin=value)) for value in krx["full_code"].to_list())
    issuerJoin = krx.join(
        dartListed.select("stock_code", "corp_code"),
        left_on="short_code",
        right_on="stock_code",
        how="left",
    )
    issuerLinkCount = issuerJoin.filter(pl.col("corp_code").is_not_null()).height

    krFilingSample, krFilingSourceFileCount, usFilingSample, usFilingEntityCount = _filingSamples(
        Path(financePath), Path(edgarPath)
    )
    krFilingCanonicalCount = sum(bool(canonicalFilingId("KR", value)) for value in krFilingSample)
    usFilingCanonicalCount = sum(bool(canonicalFilingId("US", value)) for value in usFilingSample)
    usFilingSourceFileCount = len(
        [path for path in Path(edgarPath).glob("*.parquet") if re.fullmatch(r"\d{10}\.parquet", path.name)]
    )

    krValidityFieldCount = len(set(dart.schema) & VALIDITY_FIELDS)
    usValidityFieldCount = len(set(us.schema) & VALIDITY_FIELDS)
    exactDenominator = krSampleSize + usSampleSize + len(krFilingSample) + len(usFilingSample)
    exactNumerator = krCanonicalCount + usCanonicalCount + krFilingCanonicalCount + usFilingCanonicalCount
    blockerReasons = []
    if exactNumerator != exactDenominator:
        blockerReasons.append("exactIdentifierCoverageBelowOne")
    if issuerLinkCount != krx.height:
        blockerReasons.append("krSecurityIssuerLinksIncomplete")
    if krValidityFieldCount == 0:
        blockerReasons.append("krAliasValidityMissing")
    if usValidityFieldCount == 0:
        blockerReasons.append("usTickerValidityMissing")
    if usFilingEntityCount < usSampleSize:
        blockerReasons.append("usLocalFilingEntitySampleBelow30")
    blockerReasons.append("identitySpecialCaseGoldNotReviewed")

    return IdentitySourceCensus(
        schemaVersion="identitySourceCensus.v1",
        representative=False,
        krDartRowCount=dart.height,
        krListedLegalEntityRowCount=dartListed.height,
        krUniqueCorpCodeCount=dart.select(pl.col("corp_code").n_unique()).item(),
        krUniqueStockCodeCount=dartListed.select(pl.col("stock_code").n_unique()).item(),
        krLegalSampleCount=krSampleSize,
        krLegalSampleCanonicalCount=krCanonicalCount,
        krAmbiguousNameCount=_ambiguousCount(dart, "corp_name", "corp_code"),
        krAmbiguousStockCodeCount=_ambiguousCount(dartListed, "stock_code", "corp_code"),
        krHistoricalValidityFieldCount=krValidityFieldCount,
        krxSecurityRowCount=krx.height,
        krxIsinCanonicalCount=krxIsinCanonicalCount,
        krxIssuerLinkCount=issuerLinkCount,
        krxIssuerGapCount=krx.height - issuerLinkCount,
        usTickerRowCount=us.height,
        usUniqueCikCount=us.select(pl.col("cik").n_unique()).item(),
        usUniqueTickerCount=us.select(pl.col("ticker").n_unique()).item(),
        usLegalSampleCount=usSampleSize,
        usLegalSampleCanonicalCount=usCanonicalCount,
        usAmbiguousTitleCount=_ambiguousCount(us, "title", "cik"),
        usAmbiguousTickerCount=_ambiguousCount(us, "ticker", "cik"),
        usMultiSecurityEntityCount=(
            us.group_by("cik")
            .agg(pl.col("ticker").n_unique().alias("securityCount"))
            .filter(pl.col("securityCount") > 1)
            .height
        ),
        usHistoricalValidityFieldCount=usValidityFieldCount,
        krFilingSourceFileCount=krFilingSourceFileCount,
        krFilingSampleCount=len(krFilingSample),
        krFilingCanonicalCount=krFilingCanonicalCount,
        usFilingSourceFileCount=usFilingSourceFileCount,
        usFilingEntityCount=usFilingEntityCount,
        usFilingSampleCount=len(usFilingSample),
        usFilingCanonicalCount=usFilingCanonicalCount,
        exactIdentifierCoverage=exactNumerator / exactDenominator if exactDenominator else 0.0,
        historicalAliasReady=krValidityFieldCount > 0 and usValidityFieldCount > 0,
        liveReady=not blockerReasons,
        blockerReasons=tuple(blockerReasons),
    )


def main() -> int:
    """Local KR, US identity source census를 JSON으로 출력한다.

    Capabilities
        U0-I01 deterministic 50, 30 identity sample과 issuer, validity blocker를 재측정한다.

    AIContext
        AI 역할: exact canonicalization 성공과 historical registry admission 실패를 분리한다.

    Returns
        성공 시 0.

    Example
        ``python entityIdentityProbe.py``

    Guide
        stdout을 원장에 기록하고 name 또는 ticker validity를 추정하지 않는다.

    When
        DART, KRX, SEC identity artifact가 갱신된 뒤 실행한다.

    How
        Repository local source path를 :func:`inspectIdentitySources`에 전달한다.

    Requires
        Polars와 local identity, filing parquet가 필요하다.

    See Also
        :func:`inspectIdentitySources`.

    Raises
        ValueError: identity sample이 부족하거나 identifier가 잘못됐을 때.
        OSError: local parquet를 읽지 못할 때.
    """

    repoRoot = Path(__file__).resolve().parents[4]
    census = inspectIdentitySources(
        repoRoot / "data" / "dartList" / "dartList.parquet",
        repoRoot / "data" / "krxList" / "corpList.parquet",
        repoRoot / "data" / "edgar" / "tickers.parquet",
        repoRoot / "data" / "dart" / "finance",
        repoRoot / "data" / "edgar",
    )
    print(json.dumps(census.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
