"""Analysis owner가 Data Workbench에 제공하는 stable composite assets."""

from __future__ import annotations

import hmac
import re
from collections.abc import Sequence
from hashlib import sha256
from io import BytesIO
from typing import Any

import polars as pl

_PERIOD_RE = re.compile(r"^(?P<year>\d{4})(?:-?Q(?P<quarter>[1-4]))?$")


def _periodKey(period: str) -> tuple[int, int]:
    """재무 기간 문자열을 비교 가능한 ``(year, quarter)`` 로 정규화한다.

    연도만 있으면 연말 Q4 로 취급한다. 공개 ``asOf`` 는 ``YYYY`` 또는 ``YYYY[-]Qn`` 만
    허용해 날짜 라벨이 데이터 vintage 인 것처럼 보이는 오해를 차단한다.

    simulate 의 driver registry 가 같은 본문을 갖고 있었다. 판정 기준이 갈리면 같은
    ``asOf`` 가 한쪽에서는 통과하고 다른 쪽에서는 범위 밖이 된다.
    """
    match = _PERIOD_RE.fullmatch(str(period).strip().upper())
    if not match:
        raise ValueError(f"asOf/period 형식 오류: {period!r} (YYYY 또는 YYYY-Qn)")
    return int(match.group("year")), int(match.group("quarter") or 4)


def _periodLabel(key: tuple[int, int]) -> str:
    return f"{key[0]:04d}-Q{key[1]}"


def sliceFinanceSeries(
    series: dict,
    periods: list[str],
    asOf: str | None,
) -> tuple[dict, str, str, str]:
    """분기 재무 시리즈를 요청 fiscal period까지 절단한다.

    Args:
        series: Statement와 account별 분기 value sequence.
        periods: Value sequence와 정렬된 fiscal period labels.
        asOf: 포함할 마지막 fiscal period.

    Returns:
        절단된 series, effective, latest, requested period tuple.

    Raises:
        ValueError: Period 형식이 잘못됐거나 가용 범위 밖일 때.

    Example:
        ``sliceFinanceSeries(series, ["2024-Q4"], "2024-Q4")``.
    """
    if not periods:
        requested = str(asOf) if asOf is not None else "latest"
        return series, requested, "latest", requested

    keyed = [(_periodKey(period), index) for index, period in enumerate(periods)]
    latestKey = max(key for key, _ in keyed)
    requestedKey = latestKey if asOf is None else _periodKey(asOf)
    earliestKey = min(key for key, _ in keyed)
    if requestedKey < earliestKey or requestedKey > latestKey:
        raise ValueError(f"asOf={asOf!r} 는 가용 기간 {_periodLabel(earliestKey)}~{_periodLabel(latestKey)} 밖입니다.")

    kept = [index for key, index in keyed if key <= requestedKey]
    effectiveKey = max(key for key, _ in keyed if key <= requestedKey)
    sliced: dict[str, dict[str, list]] = {}
    for statement, accounts in series.items():
        sliced[statement] = {}
        for account, values in accounts.items():
            sliced[statement][account] = [values[index] if index < len(values) else None for index in kept]
    return sliced, _periodLabel(effectiveKey), _periodLabel(latestKey), _periodLabel(requestedKey)


def simulationInputs(
    *,
    subject: str | None = None,
    company: Any | None = None,
    asOf: str | None = None,
) -> dict[str, Any]:
    """Company 분기 재무를 한 번 읽고 valid-time 절단한 data asset을 반환한다.

    Args:
        subject: Company facade가 해소할 종목 identity.
        company: 이미 해소된 read-once Company.
        asOf: 포함할 마지막 fiscal period.

    Returns:
        Series와 effective, latest, requested as-of metadata mapping.

    Raises:
        ValueError: Subject와 company가 모두 없거나 period가 유효하지 않을 때.

    Example:
        ``simulationInputs(subject="005930", asOf="2024-Q4")``.
    """
    if company is None:
        if not subject:
            raise ValueError("simulationInputs는 subject 또는 company가 필요합니다")
        import dartlab

        companyFactory = getattr(dartlab, "Company")
        company = companyFactory(subject)
    if asOf is not None:
        _periodKey(asOf)
    resolvedCompany: Any = company
    quarterly = resolvedCompany._buildFinanceSeries(freq="Q")
    if not isinstance(quarterly, tuple) or len(quarterly) < 2:
        raise ValueError("분기 재무 owner 결과가 (series, periods) 계약을 지키지 않았습니다")
    rawSeries, rawPeriods = quarterly[:2]
    if not isinstance(rawSeries, dict) or not rawSeries:
        raise ValueError("분기 재무 series가 비었습니다")
    if not isinstance(rawPeriods, Sequence) or isinstance(rawPeriods, (str, bytes)):
        raise ValueError("분기 재무 periods가 sequence가 아닙니다")
    periods = list(rawPeriods)
    if not periods or any(type(period) is not str for period in periods):
        raise ValueError("분기 재무 periods가 비었거나 유효하지 않습니다")
    series, effectiveAsOf, latestAsOf, requestedAsOf = sliceFinanceSeries(rawSeries, periods, asOf)
    from dartlab.analysis.financial._companyLookup import _getSharesOutstandingInput

    sharesEvidence = _getSharesOutstandingInput(resolvedCompany, basePeriod=asOf)
    return {
        "series": series,
        "shares": sharesEvidence["value"] if sharesEvidence is not None else None,
        "sharesEvidence": sharesEvidence,
        "asOf": effectiveAsOf,
        "latestAsOf": latestAsOf,
        "requestedAsOf": requestedAsOf,
    }


def edgarFinancialFeatures(
    *,
    subject: str | None = None,
    sourceEntityId: str | None = None,
    sourcePayload: bytes | None = None,
    sourceIntegrityDigest: str | None = None,
    company: Any | None = None,
    knownAt: str,
    measures: Sequence[str] = (),
) -> dict[str, Any]:
    """로컬 EDGAR evidence에서 operating-company PIT feature envelope를 만든다.

    Args:
        subject: US ticker 또는 Company가 해소할 수 있는 EDGAR identity.
        sourceEntityId: Workbench universe가 이미 해소한 SEC CIK.
        sourcePayload: Workbench가 pinned digest로 검증한 동일 parquet bytes.
        sourceIntegrityDigest: ``sourcePayload``의 full-file SHA-256.
        company: 테스트와 read-once 조합을 위한 기존 EDGAR Company.
        knownAt: SEC filing knowledge cutoff.
        measures: Owner가 실제 생성할 factor measure ID.

    Returns:
        Data Workbench가 검증하고 FactorProjection으로 변환할 plain mapping.

    Raises:
        ValueError: Subject가 없거나 EDGAR Company가 아니거나 coherent reduced state가 없을 때.
        FileNotFoundError: 현재 runtime에 local companyfacts shard가 없을 때.

    Example:
        ``payload = edgarFinancialFeatures(subject="AAPL", knownAt="20250201")``
    """

    directTicker = ""
    if subject:
        market, separator, entity = str(subject).strip().partition(":")
        if separator:
            if market.strip().upper() != "US" or not entity.strip():
                raise ValueError("edgarFinancialFeatures subject market은 US여야 합니다")
            directTicker = entity.strip().upper()
        else:
            directTicker = market.strip().upper()
    if company is None and sourceEntityId is not None:
        normalizedCik = str(sourceEntityId).strip()
        if not directTicker or directTicker.isdigit() or not normalizedCik.isdigit():
            raise ValueError("직접 EDGAR feature 실행에는 canonical ticker와 CIK가 필요합니다")
        cik = normalizedCik.zfill(10)
        ticker = directTicker
    elif company is None:
        if not subject:
            raise ValueError("edgarFinancialFeatures는 subject 또는 company가 필요합니다")
        import dartlab

        companyFactory = getattr(dartlab, "Company")
        company = companyFactory(subject)
        resolvedCompany: Any = company
        cik = getattr(resolvedCompany, "cik", None)
        ticker = str(getattr(resolvedCompany, "ticker", directTicker)).strip().upper()
    else:
        resolvedCompany = company
        cik = getattr(resolvedCompany, "cik", None)
        ticker = str(getattr(resolvedCompany, "ticker", directTicker)).strip().upper()
    if not cik or not ticker or ticker.isdigit():
        raise ValueError("edgarFinancialFeatures는 canonical ticker가 있는 EDGAR Company가 필요합니다")
    from dartlab.analysis.financial.filingFeatures import buildEdgarFinancialFeatureInput
    from dartlab.providers.edgar.finance.facts import readCompanyFactsLocal

    facts = readCompanyFactsLocal(
        str(cik),
        sourcePayload=sourcePayload,
        expectedIntegrityDigest=sourceIntegrityDigest,
    )
    return buildEdgarFinancialFeatureInput(
        facts,
        entityId=f"US:{ticker}",
        knownAt=knownAt,
        measures=measures,
    )


def dartFinancialFeatures(
    *,
    subject: str | None = None,
    sourceEntityId: str | None = None,
    sourcePayload: bytes | None = None,
    sourceIntegrityDigest: str | None = None,
    knownAt: str,
    fiscalYearEndMonth: int | str,
    measures: Sequence[str] = (),
) -> dict[str, Any]:
    """검증된 DART finance shard에서 PIT quarterly feature envelope를 만든다.

    Args:
        subject: 6자리 영숫자 종목코드 또는 ``KR:종목코드`` identity.
        sourceEntityId: Workbench universe가 해소한 finance shard 종목코드.
        sourcePayload: Workbench가 source pin 아래 읽은 exact parquet bytes.
        sourceIntegrityDigest: ``sourcePayload``의 full-file SHA-256.
        knownAt: DART 접수 지식 cutoff.
        fiscalYearEndMonth: Universe snapshot이 결박한 회사별 결산월.
        measures: 요청 measure ID. 비어 있으면 전체를 계산한다.

    Returns:
        Data Workbench가 검증하고 FactorProjection으로 변환할 plain mapping.

    Raises:
        ValueError: Identity, source bytes, digest 또는 결산월이 유효하지 않을 때.

    Example:
        ``dartFinancialFeatures(subject="KR:005930", knownAt="20250520", fiscalYearEndMonth=12, ...)``.
    """

    rawSubject = str(subject or "").strip()
    market, separator, entity = rawSubject.partition(":")
    if separator:
        if market.strip().upper() != "KR":
            raise ValueError("dartFinancialFeatures subject market은 KR이어야 합니다")
        code = entity.strip()
    else:
        code = market.strip()
    code = code.upper()
    sourceCode = str(sourceEntityId or code).strip().upper()
    if (
        len(code) != 6
        or not code.isascii()
        or not code.isalnum()
        or len(sourceCode) != 6
        or not sourceCode.isascii()
        or not sourceCode.isalnum()
        or code != sourceCode
    ):
        raise ValueError("dartFinancialFeatures는 일치하는 6자리 영숫자 subject와 sourceEntityId가 필요합니다")
    if not isinstance(sourcePayload, bytes) or not sourcePayload:
        raise ValueError("dartFinancialFeatures는 pinned sourcePayload가 필요합니다")
    expectedDigest = str(sourceIntegrityDigest or "").strip().lower()
    actualDigest = sha256(sourcePayload).hexdigest()
    if len(expectedDigest) != 64 or not hmac.compare_digest(actualDigest, expectedDigest):
        raise ValueError("dartFinancialFeatures source payload integrity가 일치하지 않습니다")
    try:
        fiscalMonth = int(fiscalYearEndMonth)
    except (TypeError, ValueError) as error:
        raise ValueError("fiscalYearEndMonth는 1부터 12 사이 정수여야 합니다") from error
    if not 1 <= fiscalMonth <= 12:
        raise ValueError("fiscalYearEndMonth는 1부터 12 사이 정수여야 합니다")
    try:
        finance = pl.read_parquet(BytesIO(sourcePayload))
    except Exception as error:
        raise ValueError("DART finance sourcePayload가 유효한 parquet이 아닙니다") from error
    if "stock_code" in finance.columns:
        sourceCodes = {
            str(value).strip().upper().zfill(6)
            for value in finance["stock_code"].drop_nulls().to_list()
            if str(value).strip()
        }
        if sourceCodes and sourceCodes != {sourceCode}:
            raise ValueError("DART finance sourcePayload의 종목 identity가 요청과 다릅니다")
    from dartlab.analysis.financial.dartFilingFeatures import buildDartFinancialFeatureInput

    return buildDartFinancialFeatureInput(
        finance,
        entityId=f"KR:{code}",
        knownAt=knownAt,
        fiscalYearEndMonth=fiscalMonth,
        measures=measures,
    )
