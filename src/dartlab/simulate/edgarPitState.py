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
_DEBT_CURRENT = ("LongTermDebtCurrent", "ShortTermDebtCurrent")
_DEBT_NONCURRENT = ("LongTermDebtNoncurrent",)
_DEBT_TOTAL = ("LongTermDebt", "LongTermDebtAndFinanceLeaseObligations")
_REVENUE_TAGS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
)
_OPERATING_PROFIT_TAGS = ("OperatingIncomeLoss",)


def _dateText(value) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise EdgarStateError(f"invalid date: {value}")
    return text


def _hash(payload) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()


def _normalize(facts: pl.DataFrame, knowledgeAsOf: str) -> pl.DataFrame:
    required = {"namespace", "tag", "unit", "val", "form", "filed", "start", "end", "accn"}
    if not required.issubset(facts.columns):
        raise EdgarStateError(f"EDGAR facts missing columns: {sorted(required - set(facts.columns))}")
    cutoff = _dateText(knowledgeAsOf)
    normalized = facts.with_columns(
        pl.col("filed").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8).alias("__filed"),
        pl.col("start").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8).alias("__start"),
        pl.col("end").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8).alias("__end"),
        pl.col("val").cast(pl.Float64, strict=False).alias("__value"),
    ).filter(
        (pl.col("namespace") == "us-gaap")
        & (pl.col("__filed") <= cutoff)
        & pl.col("form").cast(pl.Utf8).str.contains(r"^10-[KQ](?:/A)?$")
    )
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


def _compileStock(pit: pl.DataFrame) -> tuple[dict[str, float], tuple[FactEvidence, ...], str, tuple[str, ...]]:
    allTags = (
        {tag for tags in _STOCK_TAGS.values() for tag in tags}
        | set(_DEBT_CURRENT)
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
                current = _pick(group, "interestBearingDebtCurrent", _DEBT_CURRENT, kind="stock")
                noncurrent = _pick(group, "interestBearingDebtNoncurrent", _DEBT_NONCURRENT, kind="stock")
                total = _pick(group, "reportedTotalDebt", _DEBT_TOTAL, kind="stock")
                if current is not None and noncurrent is not None:
                    debt = current.value + noncurrent.value
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
                        tag=f"{current.tag}+{noncurrent.tag}",
                        status="derived",
                        derivation="currentDebt+noncurrentDebt; reported total excluded",
                    )
                    evidence[current.conceptId] = current
                    evidence[noncurrent.conceptId] = noncurrent
                elif total is not None:
                    debt = total.value
                    debtEvidence = FactEvidence(**{**asdict(total), "conceptId": "totalDebt", "status": "observed"})
                else:
                    continue
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
    flows = tagged.filter(pl.col("__days").is_between(60, 120))
    out: dict[str, FactEvidence] = {}
    for end in sorted(flows["__end"].unique().to_list(), reverse=True):
        endRows = flows.filter(pl.col("__end") == end).sort("__filed", descending=True)
        for tag in tags:
            tagRows = endRows.filter(pl.col("tag") == tag)
            if tagRows.height == 0:
                continue
            latestFiled = str(tagRows["__filed"].max())
            latest = tagRows.filter(pl.col("__filed") == latestFiled)
            values = set(float(value) for value in latest["__value"].to_list())
            if len(values) != 1:
                raise EdgarStateError(f"conflicting quarterly values for {conceptId}:{end}")
            out[str(end)] = _rawEvidence(conceptId, latest.row(0, named=True), kind="flowQuarter")
            break
    annuals = tagged.filter(pl.col("__days").is_between(300, 400))
    for end in sorted(annuals["__end"].unique().to_list() if annuals.height else [], reverse=True):
        if str(end) in out:
            continue
        endRows = annuals.filter(pl.col("__end") == end).sort("__filed", descending=True)
        annual: FactEvidence | None = None
        for tag in tags:
            tagRows = endRows.filter(pl.col("tag") == tag)
            if tagRows.height:
                latestFiled = str(tagRows["__filed"].max())
                latest = tagRows.filter(pl.col("__filed") == latestFiled)
                values = set(float(value) for value in latest["__value"].to_list())
                if len(values) != 1:
                    raise EdgarStateError(f"conflicting annual values for {conceptId}:{end}")
                annual = _rawEvidence(conceptId, latest.row(0, named=True), kind="flowAnnual")
                break
        if annual is None or annual.fiscalStart is None:
            continue
        firstThree = sorted(
            (
                item
                for item in out.values()
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
        q4Value = annual.value - sum(item.value for item in firstThree)
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
        )
    return out


def _compileTtm(pit: pl.DataFrame, fiscalThrough: str) -> tuple[float, float, tuple[FactEvidence, ...]]:
    revenue = _quarterEvidence(pit, "revenueQuarter", _REVENUE_TAGS, fiscalThrough=fiscalThrough)
    operating = _quarterEvidence(
        pit,
        "operatingProfitQuarter",
        _OPERATING_PROFIT_TAGS,
        fiscalThrough=fiscalThrough,
    )
    commonEnds = sorted(set(revenue) & set(operating), reverse=True)[:4]
    if len(commonEnds) != 4:
        raise EdgarStateError("four common standalone revenue and operating-profit quarters are required")
    if commonEnds[0] != fiscalThrough:
        raise EdgarStateError("TTM flow quarters must end at the stock fiscalThrough date")
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
    revenueTtm = sum(revenue[end].value for end in commonEnds)
    operatingTtm = sum(operating[end].value for end in commonEnds)
    underlying = tuple(item for end in reversed(commonEnds) for item in (revenue[end], operating[end]))
    return revenueTtm, operatingTtm, underlying


def compileEdgarFinancialState(facts: pl.DataFrame, *, knowledgeAsOf: str) -> CompiledFinancialState:
    """Compile a coherent as-known state after filtering facts by filing date."""

    cutoff = _dateText(knowledgeAsOf)
    pit = _normalize(facts, cutoff)
    values, stockEvidence, fiscalThrough, warnings = _compileStock(pit)
    revenueTtm, operatingTtm, flowEvidence = _compileTtm(pit, fiscalThrough)
    if revenueTtm <= 0:
        raise EdgarStateError("TTM revenue must be positive")
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
    otherNetAssets = otherAssets - otherLiabilities
    state = FinancialState(
        revenue=revenueTtm,
        operatingMargin=operatingTtm / revenueTtm,
        cash=values["cashAndEquivalents"],
        debt=values["totalDebt"],
        receivables=values["tradeReceivables"],
        inventories=values["inventories"],
        payables=values["tradePayables"],
        ppe=values["netPpe"],
        otherNetAssets=otherNetAssets,
        equity=equity,
    )
    evidence = stockEvidence + flowEvidence
    payload = {
        "state": asdict(state),
        "knowledgeAsOf": cutoff,
        "fiscalThrough": fiscalThrough,
        "reportingCurrency": "USD",
        "revisionPolicy": "asKnown",
        "evidence": [asdict(item) for item in evidence],
        "warnings": warnings,
    }
    return CompiledFinancialState(
        state=state,
        knowledgeAsOf=cutoff,
        fiscalThrough=fiscalThrough,
        reportingCurrency="USD",
        revisionPolicy="asKnown",
        evidence=evidence,
        warnings=warnings,
        stateHash=_hash(payload),
    )
