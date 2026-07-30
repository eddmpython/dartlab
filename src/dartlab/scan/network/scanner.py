"""한국 상장사 관계 그래프의 listing과 report prebuild 입력 로더."""

from __future__ import annotations

import re

import polars as pl

from dartlab.scan.io.calendar import filterLatestPeriodPerStock
from dartlab.scan.io.parquet import scanParquets

_INVESTED_COLUMNS = [
    "stockCode",
    "year",
    "quarter",
    "inv_prm",
    "invstmnt_purps",
    "trmend_blce_qota_rt",
    "trmend_blce_acntbk_amount",
    "trmend_blce_qy",
]

_MAJOR_HOLDER_COLUMNS = [
    "stockCode",
    "year",
    "quarter",
    "nm",
    "relate",
    "trmend_posesn_stock_co",
    "trmend_posesn_stock_qota_rt",
]


def _normalizeCompanyName(name: str) -> str:
    """회사명의 법인 표기를 제거해 listing 이름과 비교할 수 있게 한다."""

    if not name:
        return name
    normalized = name.strip()
    for pattern in (
        r"^\(주\)\s*",
        r"^㈜\s*",
        r"^주식회사\s*",
        r"\s*\(주\)$",
        r"\s*㈜$",
        r"\s*주식회사$",
        r"\s*\(유\)$",
        r"^유한회사\s*",
        r"\s*유한회사$",
        r"\s*㈜",
        r"\(주\)",
    ):
        normalized = re.sub(pattern, "", normalized)
    return normalized.strip()


def loadListing() -> tuple[dict[str, str], dict[str, str], set[str], dict[str, dict]]:
    """상장사 이름과 종목코드의 양방향 mapping 및 표시 metadata를 만든다.

    Capabilities:
        회사명 alias와 종목코드의 양방향 mapping 및 시장 metadata를 만든다.

    AIContext:
        network edge와 panel 회사명을 현재 상장 종목코드로 정규화하는 기준이다.

    Guide:
        listing 필수 컬럼이 없으면 불완전 mapping을 반환하지 않고 즉시 실패한다.

    When:
        network graph 또는 affiliateDocs prebuild 시작 시 한 번 호출한다.

    How:
        listing 행마다 원문 회사명, 정규화명, 법인 표기 alias를 같은 코드에 연결한다.

    Requires:
        정상적인 KR listing 공급자와 회사명, 종목코드 컬럼.

    Args:
        없음.

    Returns:
        ``(nameToCode, codeToName, listingCodes, listingMeta)``.

    Raises:
        polars.exceptions.ColumnNotFoundError: listing 필수 컬럼이 없을 때.

    Example:
        >>> _, codeToName, _, _ = loadListing()  # doctest: +SKIP
        >>> codeToName["005930"]
        '삼성전자'

    SeeAlso:
        ``scanInvested`` · ``scanMajorHolders``.
    """

    from dartlab._listingDispatch import listing as loadMarketListing

    listing = loadMarketListing()
    required = {"회사명", "종목코드"}
    missing = sorted(required - set(listing.columns))
    if missing:
        raise pl.exceptions.ColumnNotFoundError(f"listing 필수 컬럼 누락: {', '.join(missing)}")

    nameToCode: dict[str, str] = {}
    codeToName: dict[str, str] = {}
    listingMeta: dict[str, dict] = {}

    for row in listing.iter_rows(named=True):
        name = row["회사명"]
        code = row["종목코드"]
        codeToName[code] = name
        aliases = {
            name,
            _normalizeCompanyName(name),
            *(f"{prefix}{name}" for prefix in ("㈜", "(주)", "주식회사 ", "주식회사")),
            *(f"{name}{suffix}" for suffix in (" ㈜", "㈜", " (주)", "(주)", " 주식회사", "주식회사")),
        }
        nameToCode.update({alias: code for alias in aliases if alias})
        listingMeta[code] = {
            "name": name,
            "market": row.get("시장구분", ""),
            "industry": row.get("업종", ""),
        }

    return nameToCode, codeToName, set(codeToName), listingMeta


def scanInvested() -> pl.DataFrame:
    """회사별 최신 공시의 타법인 출자 report 행을 읽는다.

    공통 report prebuild 로더가 정상 부재와 artifact 손상을 구분한다. 최신 기간은
    회사별로 고르므로 일부 회사가 전역 최신 연도에 공시하지 않았다는 이유로 사라지지 않는다.

    Args:
        없음.

    Returns:
        회사별 최신 타법인 출자 report 행.

    Raises:
        ScanDataError: report artifact가 없거나 손상됐을 때.

    Requires:
        ``scan/report/investedCompany.parquet``와 공통 scan data root.

    Example:
        >>> scanInvested()  # doctest: +SKIP

    Capabilities:
        타법인 출자 report를 회사별 최신 기간 단면으로 축약한다.

    AIContext:
        network 투자 edge의 runtime 입력을 준비한다.

    Guide:
        전역 최신 연도가 아니라 각 회사의 최신 연도와 분기를 유지한다.

    When:
        ``buildGraph``의 투자 edge 단계.

    How:
        공통 parquet loader와 calendar filter를 순서대로 적용한다.

    SeeAlso:
        ``scanMajorHolders`` · ``dartlab.scan.network.edges.buildInvestEdges``.
    """

    raw = scanParquets("investedCompany", _INVESTED_COLUMNS)
    return filterLatestPeriodPerStock(
        raw,
        scCol="stockCode",
        yearCol="year",
        periodCol="quarter",
    )


def scanMajorHolders() -> pl.DataFrame:
    """회사별 최신 공시의 최대주주 report 행을 읽는다.

    report artifact 오류는 공통 ``ScanDataError``로 전파하며 정상적인 0행만 빈
    DataFrame으로 유지한다.

    Args:
        없음.

    Returns:
        회사별 최신 최대주주 report 행.

    Raises:
        ScanDataError: report artifact가 없거나 손상됐을 때.

    Requires:
        ``scan/report/majorHolder.parquet``와 공통 scan data root.

    Example:
        >>> scanMajorHolders()  # doctest: +SKIP

    Capabilities:
        최대주주 report를 회사별 최신 기간 단면으로 축약한다.

    AIContext:
        network 법인 및 개인 보유 edge의 runtime 입력을 준비한다.

    Guide:
        정상적인 0행과 artifact 오류를 구분한다.

    When:
        ``buildGraph``의 최대주주 edge 단계.

    How:
        공통 parquet loader로 좁은 컬럼만 읽고 calendar filter를 적용한다.

    SeeAlso:
        ``scanInvested`` · ``dartlab.scan.network.edges.buildHolderEdges``.
    """

    raw = scanParquets("majorHolder", _MAJOR_HOLDER_COLUMNS)
    return filterLatestPeriodPerStock(
        raw,
        scCol="stockCode",
        yearCol="year",
        periodCol="quarter",
    )


def scanAffiliateDocs(
    nameToCode: dict[str, str],
    codeToName: dict[str, str],
) -> dict[str, str]:
    """기존 scanner 호출 계약을 유지하며 prebuild 계열회사 mapping을 읽는다.

    Capabilities:
        과거 scanner 표면을 raw panel 순회 없는 bounded artifact loader에 연결한다.

    AIContext:
        ``scanAffiliateDocs``를 직접 부르던 소비자가 1.0 전환 후에도 같은 dict를 받게 한다.

    Guide:
        새 코드는 ``loadAffiliateGroups``를 직접 사용하고 이 함수는 호환 호출에만 둔다.

    When:
        기존 소비자가 회사명 mapping 인자와 함께 이 함수를 직접 호출할 때.

    How:
        이전 인자는 호환 목적으로 받고 canonical prebuild loader에 위임한다.

    Requires:
        유효한 ``network/affiliateDocs.parquet`` 또는 이를 받을 scan data source.

    Args:
        nameToCode: 이전 호출자가 전달하던 회사명별 종목코드 mapping.
        codeToName: 이전 호출자가 전달하던 종목코드별 회사명 mapping.

    Returns:
        affiliate 종목코드별 기업집단 label.

    Raises:
        ScanDataError: artifact 다운로드, read 또는 schema 검증이 실패했을 때.

    Example:
        >>> scanAffiliateDocs({}, {})  # doctest: +SKIP
        {'005930': '삼성'}

    SeeAlso:
        ``dartlab.scan.network.affiliates.loadAffiliateGroups``.
    """

    del nameToCode, codeToName
    from dartlab.scan.network.affiliates import loadAffiliateGroups

    return loadAffiliateGroups()
