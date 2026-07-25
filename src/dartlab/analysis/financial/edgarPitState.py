"""Compile a coherent operating-company state from EDGAR filing vintages."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from hashlib import sha256

import polars as pl

from dartlab.analysis.financial.stepProjection import FinancialState


class EdgarStateError(ValueError):
    """Raised when a coherent filing-vintage state cannot be compiled."""


@dataclass(frozen=True)
class FactEvidence:
    """One observed or derived financial concept with filing provenance."""

    conceptId: str
    value: float
    unit: str
    currency: str
    kind: str
    fiscalStart: str | None
    fiscalEnd: str
    filedAt: str
    accession: str
    form: str
    tag: str
    status: str
    derivation: str = ""
    derivationInputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompiledFinancialState:
    """A coherent reduced state known at one filing cutoff."""

    state: FinancialState
    knowledgeAsOf: str
    fiscalThrough: str
    reportingCurrency: str
    revisionPolicy: str
    evidence: tuple[FactEvidence, ...]
    warnings: tuple[str, ...]
    stateHash: str


@dataclass(frozen=True)
class QuarterFlow:
    """동일 분기와 동일 접수에서 관측된 매출과 영업이익 흐름을 보존한다."""

    fiscalStart: str
    fiscalEnd: str
    revenue: FactEvidence
    operatingProfit: FactEvidence


@dataclass(frozen=True)
class CompiledQuarterlyFinancialState:
    """분기 규모의 최신 흐름과 네 분기 이력을 filing-vintage stock에 결합한다."""

    state: FinancialState
    quarters: tuple[QuarterFlow, ...]
    ttmRevenue: float
    ttmOperatingProfit: float
    knowledgeAsOf: str
    fiscalThrough: str
    reportingCurrency: str
    revisionPolicy: str
    frequency: str
    evidence: tuple[FactEvidence, ...]
    warnings: tuple[str, ...]
    stateHash: str


@dataclass(frozen=True)
class CompiledQuarterlyFlowState:
    """Stock 결합 없이 최신 coherent 분기 흐름과 네 분기 이력을 보존한다."""

    quarters: tuple[QuarterFlow, ...]
    quarterRevenue: float
    quarterOperatingProfit: float
    ttmRevenue: float
    ttmOperatingProfit: float
    knowledgeAsOf: str
    fiscalThrough: str
    reportingCurrency: str
    revisionPolicy: str
    frequency: str
    evidence: tuple[FactEvidence, ...]
    warnings: tuple[str, ...]
    stateHash: str


@dataclass(frozen=True)
class CompiledQuarterlyRevenueState:
    """영업이익 dependency 없이 최신 coherent 매출 네 분기를 보존한다."""

    quarters: tuple[FactEvidence, ...]
    quarterRevenue: float
    ttmRevenue: float
    knowledgeAsOf: str
    fiscalThrough: str
    reportingCurrency: str
    revisionPolicy: str
    frequency: str
    evidence: tuple[FactEvidence, ...]
    warnings: tuple[str, ...]
    stateHash: str


_STOCK_TAGS: dict[str, tuple[str, ...]] = {
    "cashAndEquivalents": (
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ),
    "tradeReceivables": ("AccountsReceivableNetCurrent", "AccountsNotesAndLoansReceivableNetCurrent"),
    "inventories": ("InventoryNet",),
    "tradePayables": ("AccountsPayableCurrent",),
    "netPpe": ("PropertyPlantAndEquipmentNet",),
    "totalAssets": ("Assets",),
    "totalLiabilities": ("Liabilities",),
    "equityIncludingNci": (
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "StockholdersEquity",
    ),
}
_DEBT_CURRENT_TERM = ("LongTermDebtCurrent",)
_DEBT_SHORT_FUNDING = ("CommercialPaper", "ShortTermBorrowings", "ShortTermDebtCurrent")
_DEBT_NONCURRENT = ("LongTermDebtNoncurrent",)
_DEBT_TOTAL = ("LongTermDebt", "LongTermDebtAndFinanceLeaseObligations")
_REVENUE_TAGS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
)
_OPERATING_PROFIT_TAGS = ("OperatingIncomeLoss",)


def _dateText(value) -> str:
    raw = str(value)
    if len(raw) == 8 and raw.isdigit():
        text = raw
    elif len(raw) == 10 and raw[4] == raw[7] == "-" and raw.replace("-", "").isdigit():
        text = raw.replace("-", "")
    else:
        raise EdgarStateError(f"invalid date: {value}")
    try:
        datetime.strptime(text, "%Y%m%d")
    except ValueError as error:
        raise EdgarStateError(f"invalid date: {value}") from error
    return text


def _hash(payload) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()


def _normalizedDateExpr(column: str) -> pl.Expr:
    raw = pl.col(column).cast(pl.Utf8)
    validShape = raw.str.contains(r"^(?:\d{8}|\d{4}-\d{2}-\d{2})$")
    parsed = (
        raw.str.replace_all("-", "").str.strptime(pl.Date, "%Y%m%d", strict=False, exact=True).dt.strftime("%Y%m%d")
    )
    return (
        pl.when(raw.is_null())
        .then(pl.lit(None, dtype=pl.Utf8))
        .when(validShape)
        .then(parsed)
        .otherwise(pl.lit(None, dtype=pl.Utf8))
    )


def _normalize(facts: pl.DataFrame, knowledgeAsOf: str) -> pl.DataFrame:
    required = {"namespace", "tag", "unit", "val", "form", "filed", "start", "end", "accn"}
    if not required.issubset(facts.columns):
        raise EdgarStateError(f"EDGAR facts missing columns: {sorted(required - set(facts.columns))}")
    cutoff = _dateText(knowledgeAsOf)
    periodic = facts.filter(
        (pl.col("namespace") == "us-gaap") & pl.col("form").cast(pl.Utf8).str.contains(r"^10-[KQ](?:/A)?$")
    )
    normalized = periodic.with_columns(
        _normalizedDateExpr("filed").alias("__filed"),
        _normalizedDateExpr("start").alias("__start"),
        _normalizedDateExpr("end").alias("__end"),
        pl.col("val").cast(pl.Float64, strict=False).alias("__value"),
    )
    invalidDates = []
    for source, normalizedName, requiredValue in (
        ("filed", "__filed", True),
        ("start", "__start", False),
        ("end", "__end", True),
    ):
        invalid = (
            pl.col(normalizedName).is_null()
            if requiredValue
            else pl.col(source).is_not_null() & pl.col(normalizedName).is_null()
        )
        if normalized.filter(invalid).height:
            invalidDates.append(source)
    if invalidDates:
        raise EdgarStateError(f"EDGAR facts contain invalid dates: {', '.join(invalidDates)}")
    normalized = normalized.filter(pl.col("__filed") <= cutoff)
    if normalized.height == 0:
        raise EdgarStateError("no periodic EDGAR facts are available by knowledgeAsOf")
    if normalized["__value"].null_count() or any(
        not math.isfinite(float(value)) for value in normalized["__value"].drop_nulls()
    ):
        raise EdgarStateError("EDGAR facts contain non-finite values")
    return normalized


def _rawEvidence(conceptId: str, row: dict, *, kind: str) -> FactEvidence:
    return FactEvidence(
        conceptId=conceptId,
        value=float(row["__value"]),
        unit=str(row["unit"]),
        currency=str(row["unit"]),
        kind=kind,
        fiscalStart=str(row["__start"]) if row.get("__start") else None,
        fiscalEnd=str(row["__end"]),
        filedAt=str(row["__filed"]),
        accession=str(row["accn"]),
        form=str(row["form"]),
        tag=str(row["tag"]),
        status="observed",
    )


def _pick(group: pl.DataFrame, conceptId: str, tags: tuple[str, ...], *, kind: str) -> FactEvidence | None:
    for tag in tags:
        rows = group.filter(pl.col("tag") == tag)
        if rows.height == 0:
            continue
        units = set(rows["unit"].drop_nulls().cast(pl.Utf8).to_list())
        if units != {"USD"}:
            raise EdgarStateError(f"unit conflict for {conceptId}: {sorted(units)}")
        values = set(float(value) for value in rows["__value"].to_list())
        if len(values) != 1:
            raise EdgarStateError(f"conflicting values for {conceptId} in one accession")
        return _rawEvidence(conceptId, rows.sort("__filed", descending=True).row(0, named=True), kind=kind)
    return None


def _compileStock(
    pit: pl.DataFrame,
    *,
    requestedFiscalThrough: str | None = None,
) -> tuple[dict[str, float], tuple[FactEvidence, ...], str, tuple[str, ...]]:
    allTags = (
        {tag for tags in _STOCK_TAGS.values() for tag in tags}
        | set(_DEBT_CURRENT_TERM)
        | set(_DEBT_SHORT_FUNDING)
        | set(_DEBT_NONCURRENT)
        | set(_DEBT_TOTAL)
    )
    stock = pit.filter(pl.col("tag").is_in(list(allTags)) & pl.col("start").is_null() & pl.col("end").is_not_null())
    if stock.height == 0:
        raise EdgarStateError("no stock facts are available")
    candidates = (
        stock.select("__end", "__filed", "accn", "form").unique().sort(["__end", "__filed"], descending=[True, True])
    )
    latestCandidateEnd = str(candidates["__end"].max())
    if requestedFiscalThrough is not None:
        target = _dateText(requestedFiscalThrough)
        candidates = candidates.filter(pl.col("__end") == target)
        if candidates.height == 0:
            raise EdgarStateError(f"requested fiscalThrough is unavailable: {target}")
    for candidate in candidates.iter_rows(named=True):
        group = stock.filter(
            (pl.col("__end") == candidate["__end"])
            & (pl.col("accn") == candidate["accn"])
            & (pl.col("__filed") == candidate["__filed"])
        )
        evidence: dict[str, FactEvidence] = {}
        try:
            for conceptId, tags in _STOCK_TAGS.items():
                selected = _pick(group, conceptId, tags, kind="stock")
                if selected is None:
                    break
                evidence[conceptId] = selected
            else:
                current = _pick(group, "currentTermDebt", _DEBT_CURRENT_TERM, kind="stock")
                shortFunding = _pick(group, "shortTermFunding", _DEBT_SHORT_FUNDING, kind="stock")
                noncurrent = _pick(group, "interestBearingDebtNoncurrent", _DEBT_NONCURRENT, kind="stock")
                total = _pick(group, "reportedTotalDebt", _DEBT_TOTAL, kind="stock")
                if current is not None and noncurrent is not None:
                    termDebt = current.value + noncurrent.value
                    termComponents = (current, noncurrent)
                    evidence[current.conceptId] = current
                    evidence[noncurrent.conceptId] = noncurrent
                elif total is not None:
                    termDebt = total.value
                    termComponents = (total,)
                    evidence[total.conceptId] = total
                else:
                    continue
                debt = termDebt + (shortFunding.value if shortFunding is not None else 0.0)
                if shortFunding is not None:
                    evidence[shortFunding.conceptId] = shortFunding
                components = termComponents + ((shortFunding,) if shortFunding is not None else ())
                debtEvidence = FactEvidence(
                    conceptId="totalDebt",
                    value=debt,
                    unit="USD",
                    currency="USD",
                    kind="stock",
                    fiscalStart=None,
                    fiscalEnd=str(candidate["__end"]),
                    filedAt=str(candidate["__filed"]),
                    accession=str(candidate["accn"]),
                    form=str(candidate["form"]),
                    tag="+".join(item.tag for item in components),
                    status="derived" if len(components) > 1 else "observed",
                    derivation="term debt plus non-overlapping short-term funding; reported total excluded",
                    derivationInputs=tuple(
                        f"{item.accession}|{item.tag}|{item.fiscalStart}|{item.fiscalEnd}" for item in components
                    ),
                )
                evidence["totalDebt"] = debtEvidence
                values = {conceptId: item.value for conceptId, item in evidence.items()}
                warnings = []
                if str(candidate["__end"]) != latestCandidateEnd:
                    warnings.append(f"latestIncompleteFiling:{latestCandidateEnd}")
                return values, tuple(evidence.values()), str(candidate["__end"]), tuple(warnings)
        except EdgarStateError:
            raise
    raise EdgarStateError("no single accession contains a coherent stock state")


def _quarterEvidence(
    pit: pl.DataFrame,
    conceptId: str,
    tags: tuple[str, ...],
    *,
    fiscalThrough: str,
) -> dict[str, FactEvidence]:
    tagged = pit.filter(
        pl.col("tag").is_in(list(tags))
        & pl.col("start").is_not_null()
        & pl.col("end").is_not_null()
        & (pl.col("__end") <= fiscalThrough)
        & (pl.col("unit") == "USD")
    ).with_columns((pl.col("end").cast(pl.Date) - pl.col("start").cast(pl.Date)).dt.total_days().alias("__days"))
    flowRowsByEnd: dict[str, list[dict]] = {}
    annualRowsByEnd: dict[str, list[dict]] = {}
    yearToDateRowsByStart: dict[str, list[dict]] = {}
    for row in tagged.iter_rows(named=True):
        days = int(row["__days"])
        end = str(row["__end"])
        if 60 <= days <= 120:
            flowRowsByEnd.setdefault(end, []).append(row)
        if 300 <= days <= 400:
            annualRowsByEnd.setdefault(end, []).append(row)
        if 200 <= days <= 300:
            yearToDateRowsByStart.setdefault(str(row["__start"]), []).append(row)
    flowEnds = tuple(sorted(flowRowsByEnd, reverse=True))
    quarterSelectionCache: dict[str | None, dict[str, FactEvidence]] = {}

    def selectLatest(
        rows: list[dict],
        *,
        conflictKind: str,
        fiscalEnd: str,
        kind: str,
    ) -> FactEvidence | None:
        """태그 우선순위와 최신 filing 기준으로 한 관측을 선택한다.

        Args:
            rows: 동일 기간 후보 행.
            conflictKind: 충돌 오류에 표시할 관측 종류.
            fiscalEnd: 충돌 오류에 표시할 회계 기간말.
            kind: 생성할 evidence 종류.

        Returns:
            최신 단일 관측. 후보가 없으면 ``None``.

        Raises:
            EdgarStateError: 최신 접수 안에 서로 다른 값이 있으면 발생한다.

        Example:
            ``selectLatest(rows, conflictKind="quarterly", fiscalEnd=end, kind="flowQuarter")``.
        """

        for tag in tags:
            tagRows = [row for row in rows if row["tag"] == tag]
            if not tagRows:
                continue
            latestFiled = max(str(row["__filed"]) for row in tagRows)
            latest = [row for row in tagRows if str(row["__filed"]) == latestFiled]
            values = {float(row["__value"]) for row in latest}
            if len(values) != 1:
                raise EdgarStateError(f"conflicting {conflictKind} values for {conceptId}:{fiscalEnd}")
            return _rawEvidence(conceptId, latest[0], kind=kind)
        return None

    def selectQuarterFacts(filedThrough: str | None = None) -> dict[str, FactEvidence]:
        """주어진 filing cutoff 안에서 분기별 최신 단독 흐름을 선택한다.

        Args:
            filedThrough: 포함할 최신 filing 날짜. ``None``이면 전체를 포함한다.

        Returns:
            분기말별 최신 ``FactEvidence`` 매핑.

        Raises:
            EdgarStateError: 같은 분기와 최신 접수에 서로 다른 값이 있으면 발생한다.

        Example:
            ``selectQuarterFacts("20250131")`` 로 cutoff 안의 분기 흐름을 선택한다.
        """

        cached = quarterSelectionCache.get(filedThrough)
        if cached is not None:
            return cached
        selected: dict[str, FactEvidence] = {}
        for end in flowEnds:
            endRows = flowRowsByEnd[end]
            if filedThrough is not None:
                endRows = [row for row in endRows if str(row["__filed"]) <= filedThrough]
            evidence = selectLatest(
                endRows,
                conflictKind="quarterly",
                fiscalEnd=end,
                kind="flowQuarter",
            )
            if evidence is not None:
                selected[end] = evidence
        quarterSelectionCache[filedThrough] = selected
        return selected

    out = dict(selectQuarterFacts())
    for end in sorted(annualRowsByEnd, reverse=True):
        if end in out:
            continue
        annual = selectLatest(
            annualRowsByEnd[end],
            conflictKind="annual",
            fiscalEnd=end,
            kind="flowAnnual",
        )
        if annual is None or annual.fiscalStart is None:
            continue
        ytdCandidates = [
            row
            for row in yearToDateRowsByStart.get(annual.fiscalStart, ())
            if str(row["__end"]) < annual.fiscalEnd and str(row["__filed"]) <= annual.filedAt
        ]
        ytd: FactEvidence | None = None
        if ytdCandidates:
            latestEnd = max(str(row["__end"]) for row in ytdCandidates)
            ytd = selectLatest(
                [row for row in ytdCandidates if str(row["__end"]) == latestEnd],
                conflictKind="year-to-date",
                fiscalEnd=latestEnd,
                kind="flowYearToDate",
            )
        if ytd is not None:
            q4Start = (datetime.strptime(ytd.fiscalEnd, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
            q4Days = (datetime.strptime(annual.fiscalEnd, "%Y%m%d") - datetime.strptime(q4Start, "%Y%m%d")).days
            if 60 <= q4Days <= 120:
                out[str(end)] = FactEvidence(
                    conceptId=conceptId,
                    value=annual.value - ytd.value,
                    unit=annual.unit,
                    currency=annual.currency,
                    kind="flowQuarter",
                    fiscalStart=q4Start,
                    fiscalEnd=annual.fiscalEnd,
                    filedAt=annual.filedAt,
                    accession=annual.accession,
                    form=annual.form,
                    tag=f"{annual.tag}:Q4Residual",
                    status="derived",
                    derivation="annual minus nine-month year-to-date flow",
                    derivationInputs=tuple(
                        f"{item.accession}|{item.tag}|{item.fiscalStart}|{item.fiscalEnd}" for item in (annual, ytd)
                    ),
                )
                continue
        asKnownAtAnnual = selectQuarterFacts(annual.filedAt)
        firstThree = sorted(
            (
                item
                for item in asKnownAtAnnual.values()
                if item.fiscalStart is not None
                and item.fiscalStart >= annual.fiscalStart
                and item.fiscalEnd < annual.fiscalEnd
            ),
            key=lambda item: item.fiscalEnd,
        )[:3]
        if len(firstThree) != 3:
            continue
        annualStart = datetime.strptime(annual.fiscalStart, "%Y%m%d")
        firstStart = datetime.strptime(str(firstThree[0].fiscalStart), "%Y%m%d")
        gaps = [
            (
                datetime.strptime(str(current.fiscalStart), "%Y%m%d") - datetime.strptime(previous.fiscalEnd, "%Y%m%d")
            ).days
            for previous, current in zip(firstThree, firstThree[1:])
        ]
        if not 0 <= (firstStart - annualStart).days <= 14 or any(gap < 0 or gap > 14 for gap in gaps):
            continue
        q4Start = (datetime.strptime(firstThree[-1].fiscalEnd, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
        q4Days = (datetime.strptime(annual.fiscalEnd, "%Y%m%d") - datetime.strptime(q4Start, "%Y%m%d")).days
        if q4Days < 60 or q4Days > 120:
            continue
        q4Value = annual.value - sum(item.value for item in firstThree)
        derivationInputs = tuple(
            f"{item.accession}|{item.tag}|{item.fiscalStart}|{item.fiscalEnd}" for item in (annual, *firstThree)
        )
        out[str(end)] = FactEvidence(
            conceptId=conceptId,
            value=q4Value,
            unit=annual.unit,
            currency=annual.currency,
            kind="flowQuarter",
            fiscalStart=q4Start,
            fiscalEnd=annual.fiscalEnd,
            filedAt=annual.filedAt,
            accession=annual.accession,
            form=annual.form,
            tag=f"{annual.tag}:Q4Residual",
            status="derived",
            derivation="annual minus first three standalone fiscal quarters",
            derivationInputs=derivationInputs,
        )
    return out


def _compileQuarterWindow(pit: pl.DataFrame, fiscalThrough: str) -> tuple[QuarterFlow, ...]:
    revenue = _quarterEvidence(pit, "revenueQuarter", _REVENUE_TAGS, fiscalThrough=fiscalThrough)
    operating = _quarterEvidence(
        pit,
        "operatingProfitQuarter",
        _OPERATING_PROFIT_TAGS,
        fiscalThrough=fiscalThrough,
    )
    candidates = sorted(set(revenue) & set(operating), reverse=True)
    if fiscalThrough not in candidates:
        raise EdgarStateError("TTM flow quarters must end at the stock fiscalThrough date")

    def priorQuarter(currentEnd: str) -> str | None:
        """현재 분기 시작일과 연속되는 직전 공통 분기말을 찾는다.

        Args:
            currentEnd: 현재 분기말. ``YYYYMMDD`` 형식이다.

        Returns:
            연속되는 직전 공통 분기말. 없으면 ``None``.

        Raises:
            ValueError: 분기 날짜 문자열이 올바르지 않으면 발생한다.

        Example:
            ``priorQuarter("20241231")`` 로 직전 공통 분기말을 찾는다.
        """

        currentStart = revenue[currentEnd].fiscalStart
        if currentStart is None or currentStart != operating[currentEnd].fiscalStart:
            return None
        startDate = datetime.strptime(currentStart, "%Y%m%d")
        for candidateEnd in candidates:
            if candidateEnd >= currentEnd:
                continue
            candidateRevenue = revenue[candidateEnd]
            candidateOperating = operating[candidateEnd]
            if candidateRevenue.fiscalStart != candidateOperating.fiscalStart:
                continue
            gap = (startDate - datetime.strptime(candidateEnd, "%Y%m%d")).days
            if 0 <= gap <= 14:
                return candidateEnd
        return None

    commonEnds = [fiscalThrough]
    while len(commonEnds) < 4:
        prior = priorQuarter(commonEnds[-1])
        if prior is None:
            break
        commonEnds.append(prior)
    if len(commonEnds) != 4:
        raise EdgarStateError("four common standalone revenue and operating-profit quarters are required")
    chronological = [revenue[end] for end in reversed(commonEnds)]
    gaps = [
        (datetime.strptime(str(current.fiscalStart), "%Y%m%d") - datetime.strptime(previous.fiscalEnd, "%Y%m%d")).days
        for previous, current in zip(chronological, chronological[1:])
    ]
    if any(gap < 0 or gap > 14 for gap in gaps):
        raise EdgarStateError("TTM quarters are not contiguous")
    start = min(item.fiscalStart for end in commonEnds for item in (revenue[end], operating[end]) if item.fiscalStart)
    span = (pl.Series([fiscalThrough]).str.to_date("%Y%m%d")[0] - pl.Series([start]).str.to_date("%Y%m%d")[0]).days
    if span < 270 or span > 400:
        raise EdgarStateError("TTM quarters do not form one fiscal year")
    flows: list[QuarterFlow] = []
    for end in reversed(commonEnds):
        revenueItem = revenue[end]
        operatingItem = operating[end]
        if revenueItem.accession != operatingItem.accession:
            raise EdgarStateError(f"quarter flow concepts do not share one accession: {end}")
        if revenueItem.fiscalStart != operatingItem.fiscalStart:
            raise EdgarStateError(f"quarter flow concepts do not share one fiscal interval: {end}")
        if revenueItem.status == "derived" or operatingItem.status == "derived":
            revenueAccessions = tuple(item.split("|", 1)[0] for item in revenueItem.derivationInputs)
            operatingAccessions = tuple(item.split("|", 1)[0] for item in operatingItem.derivationInputs)
            if revenueAccessions != operatingAccessions:
                raise EdgarStateError(f"derived quarter concepts do not share one filing lineage: {end}")
        fiscalStart = str(revenueItem.fiscalStart)
        flows.append(QuarterFlow(fiscalStart, end, revenueItem, operatingItem))
    return tuple(flows)


def _compileRevenueQuarterWindow(
    pit: pl.DataFrame,
    fiscalThrough: str,
) -> tuple[FactEvidence, ...]:
    """한 fiscal end까지 연속된 매출 단독 네 분기를 컴파일한다."""

    revenue = _quarterEvidence(
        pit,
        "revenueQuarter",
        _REVENUE_TAGS,
        fiscalThrough=fiscalThrough,
    )
    candidates = sorted(revenue, reverse=True)
    if fiscalThrough not in candidates:
        raise EdgarStateError("revenue flow quarters must end at the requested fiscalThrough date")

    def priorQuarter(currentEnd: str) -> str | None:
        currentStart = revenue[currentEnd].fiscalStart
        if currentStart is None:
            return None
        startDate = datetime.strptime(currentStart, "%Y%m%d")
        for candidateEnd in candidates:
            if candidateEnd >= currentEnd:
                continue
            gap = (startDate - datetime.strptime(candidateEnd, "%Y%m%d")).days
            if 0 <= gap <= 14:
                return candidateEnd
        return None

    commonEnds = [fiscalThrough]
    while len(commonEnds) < 4:
        prior = priorQuarter(commonEnds[-1])
        if prior is None:
            break
        commonEnds.append(prior)
    if len(commonEnds) != 4:
        raise EdgarStateError("four standalone revenue quarters are required")
    chronological = tuple(revenue[end] for end in reversed(commonEnds))
    gaps = [
        (datetime.strptime(str(current.fiscalStart), "%Y%m%d") - datetime.strptime(previous.fiscalEnd, "%Y%m%d")).days
        for previous, current in zip(
            chronological,
            chronological[1:],
        )
    ]
    if any(gap < 0 or gap > 14 for gap in gaps):
        raise EdgarStateError("revenue quarters are not contiguous")
    start = chronological[0].fiscalStart
    assert start is not None
    span = (pl.Series([fiscalThrough]).str.to_date("%Y%m%d")[0] - pl.Series([start]).str.to_date("%Y%m%d")[0]).days
    if span < 270 or span > 400:
        raise EdgarStateError("revenue quarters do not form one fiscal year")
    return chronological


def _compileTtm(pit: pl.DataFrame, fiscalThrough: str) -> tuple[float, float, tuple[FactEvidence, ...]]:
    flows = _compileQuarterWindow(pit, fiscalThrough)
    revenueTtm = sum(flow.revenue.value for flow in flows)
    operatingTtm = sum(flow.operatingProfit.value for flow in flows)
    underlying = tuple(item for flow in flows for item in (flow.revenue, flow.operatingProfit))
    return revenueTtm, operatingTtm, underlying


def _financialState(values: dict[str, float], *, revenue: float, operatingProfit: float) -> FinancialState:
    if revenue <= 0:
        raise EdgarStateError("financial state revenue must be positive")
    identity = values["totalAssets"] - values["totalLiabilities"]
    equity = values["equityIncludingNci"]
    tolerance = max(1e-6, abs(equity) * 1e-8)
    if abs(identity - equity) > tolerance:
        raise EdgarStateError("consolidated balance identity does not close")
    otherAssets = (
        values["totalAssets"]
        - values["cashAndEquivalents"]
        - values["tradeReceivables"]
        - values["inventories"]
        - values["netPpe"]
    )
    otherLiabilities = values["totalLiabilities"] - values["tradePayables"] - values["totalDebt"]
    return FinancialState(
        revenue=revenue,
        latentDemandRevenue=revenue,
        operatingMargin=operatingProfit / revenue,
        cash=values["cashAndEquivalents"],
        debt=values["totalDebt"],
        receivables=values["tradeReceivables"],
        inventories=values["inventories"],
        payables=values["tradePayables"],
        ppe=values["netPpe"],
        otherNetAssets=otherAssets - otherLiabilities,
        equity=equity,
    )


def compileEdgarFinancialState(
    facts: pl.DataFrame,
    *,
    knowledgeAsOf: str,
    fiscalThrough: str | None = None,
) -> CompiledFinancialState:
    """Compile a coherent as-known state after filtering facts by filing date.

    Args:
        facts: Normalized EDGAR company facts rows.
        knowledgeAsOf: Filing knowledge cutoff in ``YYYYMMDD`` form.
        fiscalThrough: Optional fiscal-end date to select explicitly.

    Returns:
        Coherent financial state with evidence, warnings, and a deterministic hash.

    Raises:
        EdgarStateError: Facts cannot form one coherent point-in-time state.

    Example:
        ``compileEdgarFinancialState(facts, knowledgeAsOf="20250228")``.
    """

    cutoff = _dateText(knowledgeAsOf)
    pit = _normalize(facts, cutoff)
    values, stockEvidence, effectiveFiscalThrough, warnings = _compileStock(
        pit,
        requestedFiscalThrough=fiscalThrough,
    )
    revenueTtm, operatingTtm, flowEvidence = _compileTtm(pit, effectiveFiscalThrough)
    state = _financialState(values, revenue=revenueTtm, operatingProfit=operatingTtm)
    evidence = stockEvidence + flowEvidence
    payload = {
        "state": asdict(state),
        "knowledgeAsOf": cutoff,
        "fiscalThrough": effectiveFiscalThrough,
        "reportingCurrency": "USD",
        "revisionPolicy": "asKnown",
        "evidence": [asdict(item) for item in evidence],
        "warnings": warnings,
    }
    return CompiledFinancialState(
        state=state,
        knowledgeAsOf=cutoff,
        fiscalThrough=effectiveFiscalThrough,
        reportingCurrency="USD",
        revisionPolicy="asKnown",
        evidence=evidence,
        warnings=warnings,
        stateHash=_hash(payload),
    )


def compileEdgarQuarterlyFlowState(
    facts: pl.DataFrame,
    *,
    knowledgeAsOf: str,
    fiscalThrough: str | None = None,
) -> CompiledQuarterlyFlowState:
    """Stock facts 없이 coherent revenue와 operating-profit 분기 흐름을 컴파일한다.

    Args:
        facts: Normalized EDGAR company facts rows.
        knowledgeAsOf: Filing knowledge cutoff in ``YYYYMMDD`` form.
        fiscalThrough: Optional fiscal-end date to select explicitly.

    Returns:
        Latest coherent quarter, four-quarter history, evidence, and a state hash.

    Raises:
        EdgarStateError: Facts cannot form a coherent four-quarter flow state.

    Example:
        ``compileEdgarQuarterlyFlowState(facts, knowledgeAsOf="20250228")``.
    """

    cutoff = _dateText(knowledgeAsOf)
    pit = _normalize(facts, cutoff)
    warnings: tuple[str, ...] = ()
    if fiscalThrough is not None:
        effectiveFiscalThrough = _dateText(fiscalThrough)
        quarters = _compileQuarterWindow(pit, effectiveFiscalThrough)
    else:
        latestEnd = max(str(value) for value in pit["__end"].drop_nulls().to_list() if str(value))
        revenue = _quarterEvidence(
            pit,
            "revenueQuarter",
            _REVENUE_TAGS,
            fiscalThrough=latestEnd,
        )
        operating = _quarterEvidence(
            pit,
            "operatingProfitQuarter",
            _OPERATING_PROFIT_TAGS,
            fiscalThrough=latestEnd,
        )
        candidates = tuple(sorted(set(revenue) & set(operating), reverse=True))
        if not candidates:
            raise EdgarStateError("four common standalone revenue and operating-profit quarters are required")
        firstError: EdgarStateError | None = None
        quarters = ()
        effectiveFiscalThrough = ""
        for candidate in candidates:
            try:
                candidateQuarters = _compileQuarterWindow(pit, candidate)
                if candidateQuarters[-1].revenue.value <= 0:
                    raise EdgarStateError("financial state revenue must be positive")
                quarters = candidateQuarters
                effectiveFiscalThrough = candidate
                if candidate != candidates[0]:
                    warnings = (f"latestIncompleteFlow:{candidates[0]}",)
                break
            except EdgarStateError as error:
                if firstError is None:
                    firstError = error
        if not quarters:
            assert firstError is not None
            raise firstError
    latest = quarters[-1]
    quarterRevenue = latest.revenue.value
    if quarterRevenue <= 0:
        raise EdgarStateError("financial state revenue must be positive")
    quarterOperatingProfit = latest.operatingProfit.value
    ttmRevenue = sum(flow.revenue.value for flow in quarters)
    ttmOperatingProfit = sum(flow.operatingProfit.value for flow in quarters)
    evidence = tuple(item for flow in quarters for item in (flow.revenue, flow.operatingProfit))
    payload = {
        "quarters": [asdict(flow) for flow in quarters],
        "quarterRevenue": quarterRevenue,
        "quarterOperatingProfit": quarterOperatingProfit,
        "ttmRevenue": ttmRevenue,
        "ttmOperatingProfit": ttmOperatingProfit,
        "knowledgeAsOf": cutoff,
        "fiscalThrough": effectiveFiscalThrough,
        "reportingCurrency": "USD",
        "revisionPolicy": "asKnown",
        "frequency": "quarter",
        "evidence": [asdict(item) for item in evidence],
        "warnings": warnings,
    }
    return CompiledQuarterlyFlowState(
        quarters=quarters,
        quarterRevenue=quarterRevenue,
        quarterOperatingProfit=quarterOperatingProfit,
        ttmRevenue=ttmRevenue,
        ttmOperatingProfit=ttmOperatingProfit,
        knowledgeAsOf=cutoff,
        fiscalThrough=effectiveFiscalThrough,
        reportingCurrency="USD",
        revisionPolicy="asKnown",
        frequency="quarter",
        evidence=evidence,
        warnings=warnings,
        stateHash=_hash(payload),
    )


def compileEdgarQuarterlyRevenueState(
    facts: pl.DataFrame,
    *,
    knowledgeAsOf: str,
    fiscalThrough: str | None = None,
) -> CompiledQuarterlyRevenueState:
    """영업이익이나 stock facts 없이 coherent revenue 네 분기를 컴파일한다."""

    cutoff = _dateText(knowledgeAsOf)
    pit = _normalize(facts, cutoff)
    warnings: tuple[str, ...] = ()
    if fiscalThrough is not None:
        effectiveFiscalThrough = _dateText(fiscalThrough)
        quarters = _compileRevenueQuarterWindow(
            pit,
            effectiveFiscalThrough,
        )
    else:
        latestEnd = max(str(value) for value in pit["__end"].drop_nulls().to_list() if str(value))
        revenue = _quarterEvidence(
            pit,
            "revenueQuarter",
            _REVENUE_TAGS,
            fiscalThrough=latestEnd,
        )
        candidates = tuple(sorted(revenue, reverse=True))
        if not candidates:
            raise EdgarStateError("four standalone revenue quarters are required")
        firstError: EdgarStateError | None = None
        quarters = ()
        effectiveFiscalThrough = ""
        for candidate in candidates:
            try:
                candidateQuarters = _compileRevenueQuarterWindow(
                    pit,
                    candidate,
                )
                if candidateQuarters[-1].value <= 0:
                    raise EdgarStateError("financial state revenue must be positive")
                quarters = candidateQuarters
                effectiveFiscalThrough = candidate
                if candidate != candidates[0]:
                    warnings = (f"latestIncompleteFlow:{candidates[0]}",)
                break
            except EdgarStateError as error:
                if firstError is None:
                    firstError = error
        if not quarters:
            assert firstError is not None
            raise firstError
    quarterRevenue = quarters[-1].value
    if quarterRevenue <= 0:
        raise EdgarStateError("financial state revenue must be positive")
    ttmRevenue = sum(item.value for item in quarters)
    payload = {
        "quarters": [asdict(item) for item in quarters],
        "quarterRevenue": quarterRevenue,
        "ttmRevenue": ttmRevenue,
        "knowledgeAsOf": cutoff,
        "fiscalThrough": effectiveFiscalThrough,
        "reportingCurrency": "USD",
        "revisionPolicy": "asKnown",
        "frequency": "quarter",
        "evidence": [asdict(item) for item in quarters],
        "warnings": warnings,
    }
    return CompiledQuarterlyRevenueState(
        quarters=quarters,
        quarterRevenue=quarterRevenue,
        ttmRevenue=ttmRevenue,
        knowledgeAsOf=cutoff,
        fiscalThrough=effectiveFiscalThrough,
        reportingCurrency="USD",
        revisionPolicy="asKnown",
        frequency="quarter",
        evidence=quarters,
        warnings=warnings,
        stateHash=_hash(payload),
    )


def compileEdgarQuarterlyFinancialState(
    facts: pl.DataFrame,
    *,
    knowledgeAsOf: str,
    fiscalThrough: str | None = None,
) -> CompiledQuarterlyFinancialState:
    """Compile the latest standalone quarter with a coherent four-quarter history.

    Args:
        facts: Normalized EDGAR company facts rows.
        knowledgeAsOf: Filing knowledge cutoff in ``YYYYMMDD`` form.
        fiscalThrough: Optional fiscal-end date to select explicitly.

    Returns:
        Latest quarter, four-quarter history, evidence, warnings, and a state hash.

    Raises:
        EdgarStateError: Facts cannot form a coherent four-quarter state.

    Example:
        ``compileEdgarQuarterlyFinancialState(facts, knowledgeAsOf="20250228")``.
    """

    cutoff = _dateText(knowledgeAsOf)
    pit = _normalize(facts, cutoff)
    values, stockEvidence, effectiveFiscalThrough, warnings = _compileStock(
        pit,
        requestedFiscalThrough=fiscalThrough,
    )
    quarters = _compileQuarterWindow(pit, effectiveFiscalThrough)
    latest = quarters[-1]
    state = _financialState(
        values,
        revenue=latest.revenue.value,
        operatingProfit=latest.operatingProfit.value,
    )
    ttmRevenue = sum(flow.revenue.value for flow in quarters)
    ttmOperatingProfit = sum(flow.operatingProfit.value for flow in quarters)
    flowEvidence = tuple(item for flow in quarters for item in (flow.revenue, flow.operatingProfit))
    evidence = stockEvidence + flowEvidence
    payload = {
        "state": asdict(state),
        "quarters": [asdict(flow) for flow in quarters],
        "ttmRevenue": ttmRevenue,
        "ttmOperatingProfit": ttmOperatingProfit,
        "knowledgeAsOf": cutoff,
        "fiscalThrough": effectiveFiscalThrough,
        "reportingCurrency": "USD",
        "revisionPolicy": "asKnown",
        "frequency": "quarter",
        "evidence": [asdict(item) for item in evidence],
        "warnings": warnings,
    }
    return CompiledQuarterlyFinancialState(
        state=state,
        quarters=quarters,
        ttmRevenue=ttmRevenue,
        ttmOperatingProfit=ttmOperatingProfit,
        knowledgeAsOf=cutoff,
        fiscalThrough=effectiveFiscalThrough,
        reportingCurrency="USD",
        revisionPolicy="asKnown",
        frequency="quarter",
        evidence=evidence,
        warnings=warnings,
        stateHash=_hash(payload),
    )
