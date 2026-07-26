"""Compile a coherent operating-company state from EDGAR filing vintages."""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from typing import TypeVar

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


_STOCK_ANCHOR_CONCEPTS = ("totalAssets", "totalLiabilities", "equityIncludingNci")
_NONCONTROLLING_INTEREST_TAGS = ("MinorityInterest",)
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
    # 앞 4개는 `reference/data/accountMappings.json` 의 edgar `revenue.commonTags` 정본이다.
    # 뒤 2개는 그 정본에 없는 업종 전용 총매출 태그로, 일반 태그가 하나도 없을 때만 닿는다.
    # 순서가 곧 우선순위다. `selectLatest` 가 먼저 매칭되는 태그를 채택한다.
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
    "SalesRevenueGoodsNet",
    "RevenuesNetOfInterestExpense",
    "RealEstateRevenueNet",
)
_OPERATING_PROFIT_TAGS = ("OperatingIncomeLoss",)
# 영업이익 유도용 구성요소. 기준이 서로 달라 한 태그 목록으로 합치지 않는다.
# `OperatingExpenses` 는 매출원가를 제외한 판관비 계열이라 매출총이익에서 빼고,
# `CostsAndExpenses` 는 매출원가를 포함한 총비용이라 매출에서 뺀다.
_GROSS_PROFIT_TAGS = ("GrossProfit",)
_OPERATING_EXPENSE_TAGS = ("OperatingExpenses",)
_TOTAL_COSTS_TAGS = ("CostsAndExpenses",)


def _tagRuleDigest(payload: object) -> str:
    """태그 선택 규칙을 canonical JSON digest로 고정한다."""

    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def flowSelectionRuleDigest() -> str:
    """분기 흐름 선택에 실제로 쓰는 태그 우선순위의 digest를 반환한다.

    Capabilities:
        매출과 영업이익 태그 우선순위를 계약 identity로 노출한다.

    Returns:
        태그 목록과 순서를 결박한 SHA-256 hex digest.

    Example:
        ``digest = flowSelectionRuleDigest()``.

    Guide:
        adapter의 normalization rule hash에 합성해 태그 변경이 계약 identity를 바꾸게 한다.

    Requires:
        태그 순서가 우선순위이므로 순서 변경도 다른 digest여야 한다.

    AIContext:
        같은 원천에서 다른 태그 규칙으로 만든 관측을 같은 계약으로 착각하지 않게 한다.
    """

    return _tagRuleDigest(
        {
            "revenue": list(_REVENUE_TAGS),
            "operatingProfit": list(_OPERATING_PROFIT_TAGS),
            "operatingProfitFallback": {
                "grossProfit": list(_GROSS_PROFIT_TAGS),
                "operatingExpenses": list(_OPERATING_EXPENSE_TAGS),
                "totalCosts": list(_TOTAL_COSTS_TAGS),
            },
        }
    )


def stateSelectionRuleDigest() -> str:
    """전체 재무상태 선택에 쓰는 stock과 흐름 태그 규칙의 digest를 반환한다.

    Capabilities:
        대차 항목, 차입금 블록, 흐름 태그 우선순위를 하나의 계약 identity로 묶는다.

    Returns:
        stock과 flow 태그 규칙 전체를 결박한 SHA-256 hex digest.

    Example:
        ``digest = stateSelectionRuleDigest()``.

    Guide:
        full-state adapter의 normalization rule hash에 합성한다.

    Requires:
        차입금 구성 태그도 값에 영향을 주므로 함께 결박해야 한다.

    AIContext:
        태그 테이블 변경이 캐시된 generation을 조용히 통과시키지 않게 한다.
    """

    return _tagRuleDigest(
        {
            "flow": {
                "revenue": list(_REVENUE_TAGS),
                "operatingProfit": list(_OPERATING_PROFIT_TAGS),
                "operatingProfitFallback": {
                    "grossProfit": list(_GROSS_PROFIT_TAGS),
                    "operatingExpenses": list(_OPERATING_EXPENSE_TAGS),
                    "totalCosts": list(_TOTAL_COSTS_TAGS),
                },
            },
            "stock": {key: list(value) for key, value in _STOCK_TAGS.items()},
            "stockAnchors": list(_STOCK_ANCHOR_CONCEPTS),
            "noncontrollingInterest": list(_NONCONTROLLING_INTEREST_TAGS),
            "debt": {
                "currentTerm": list(_DEBT_CURRENT_TERM),
                "shortFunding": list(_DEBT_SHORT_FUNDING),
                "noncurrent": list(_DEBT_NONCURRENT),
                "total": list(_DEBT_TOTAL),
            },
        }
    )


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


def _combinedEquity(parent: FactEvidence, noncontrolling: FactEvidence) -> FactEvidence:
    """지배주주 자본에 비지배지분을 더해 연결 자본 관측을 만든다."""

    components = (parent, noncontrolling)
    return FactEvidence(
        conceptId="equityIncludingNci",
        value=parent.value + noncontrolling.value,
        unit=parent.unit,
        currency=parent.currency,
        kind="stock",
        fiscalStart=parent.fiscalStart,
        fiscalEnd=parent.fiscalEnd,
        filedAt=max(parent.filedAt, noncontrolling.filedAt),
        accession=parent.accession,
        form=parent.form,
        tag=f"{parent.tag}+{noncontrolling.tag}",
        status="derived",
        derivation="parent stockholders equity plus noncontrolling interest",
        derivationInputs=tuple(
            f"{item.accession}|{item.tag}|{item.fiscalStart}|{item.fiscalEnd}" for item in components
        ),
    )


_StockCandidate = tuple[dict[str, float], tuple[FactEvidence, ...], str, tuple[str, ...]]
_FlowResult = TypeVar("_FlowResult")


def _stockCandidates(
    pit: pl.DataFrame,
    *,
    requestedFiscalThrough: str | None = None,
) -> Iterator[_StockCandidate]:
    """접수 후보를 최신순으로 순회하며 성립하는 stock state를 모두 내놓는다.

    한 후보만 반환하면 대차는 있으나 분기 흐름이 없는 최신 filing 에 걸려 회사 전체가
    실패한다. 소비자가 흐름 창까지 성립하는 첫 후보를 고를 수 있도록 지연 순회한다.
    """
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
    firstConflict: EdgarStateError | None = None
    for candidate in candidates.iter_rows(named=True):
        group = stock.filter(
            (pl.col("__end") == candidate["__end"])
            & (pl.col("accn") == candidate["accn"])
            & (pl.col("__filed") == candidate["__filed"])
        )
        evidence: dict[str, FactEvidence] = {}
        try:
            imputed: list[str] = []
            for conceptId, tags in _STOCK_TAGS.items():
                selected = _pick(group, conceptId, tags, kind="stock")
                if selected is None:
                    if conceptId in _STOCK_ANCHOR_CONCEPTS:
                        break
                    # 미태깅 구성요소는 결측이 아니라 세분성 부족이다. 0 으로 두면 그 금액이
                    # `otherNetAssets` 잔차 플러그로 흡수되고 대차 항등식은 그대로 닫힌다.
                    # 재고 개념이 없는 소프트웨어, 서비스, 금융, REIT 를 실패로 처리하지 않는다.
                    imputed.append(conceptId)
                    continue
                evidence[conceptId] = selected
            else:
                equity = evidence["equityIncludingNci"]
                if equity.tag == "StockholdersEquity":
                    # 지배주주 자본만 태깅됐다면 비지배지분을 더해야 항등식이 닫힌다.
                    # 더하지 않으면 비지배지분이 있는 회사가 구조적으로 항등식 검사에 걸린다.
                    noncontrolling = _pick(group, "noncontrollingInterest", _NONCONTROLLING_INTEREST_TAGS, kind="stock")
                    if noncontrolling is not None:
                        evidence["noncontrollingInterest"] = noncontrolling
                        evidence["equityIncludingNci"] = _combinedEquity(equity, noncontrolling)
                current = _pick(group, "currentTermDebt", _DEBT_CURRENT_TERM, kind="stock")
                shortFunding = _pick(group, "shortTermFunding", _DEBT_SHORT_FUNDING, kind="stock")
                noncurrent = _pick(group, "interestBearingDebtNoncurrent", _DEBT_NONCURRENT, kind="stock")
                total = _pick(group, "reportedTotalDebt", _DEBT_TOTAL, kind="stock")
                termComponents: tuple[FactEvidence, ...]
                if current is not None and noncurrent is not None:
                    termDebt = current.value + noncurrent.value
                    termComponents = (current, noncurrent)
                    evidence[current.conceptId] = current
                    evidence[noncurrent.conceptId] = noncurrent
                elif total is not None:
                    termDebt = total.value
                    termComponents = (total,)
                    evidence[total.conceptId] = total
                elif shortFunding is not None:
                    # 리볼버나 기업어음만 쓰는 회사는 term debt 태그가 없다.
                    termDebt = 0.0
                    termComponents = ()
                else:
                    # 이자부부채 태그가 하나도 없다. 무차입이 실제로 흔하므로 실패로 보지 않고
                    # 0 으로 두되 imputed 로 남긴다. 미태깅 차입금이면 그 금액은 플러그로 간다.
                    termDebt = 0.0
                    termComponents = ()
                    imputed.append("totalDebt")
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
                    tag="+".join(item.tag for item in components) if components else "none",
                    status="derived" if len(components) != 1 else "observed",
                    derivation=(
                        "no interest-bearing debt tagged in this accession"
                        if not components
                        else "term debt plus non-overlapping short-term funding; reported total excluded"
                    ),
                    derivationInputs=tuple(
                        f"{item.accession}|{item.tag}|{item.fiscalStart}|{item.fiscalEnd}" for item in components
                    ),
                )
                evidence["totalDebt"] = debtEvidence
                values = {conceptId: item.value for conceptId, item in evidence.items()}
                for conceptId in imputed:
                    values.setdefault(conceptId, 0.0)
                warnings = []
                if str(candidate["__end"]) != latestCandidateEnd:
                    warnings.append(f"latestIncompleteFiling:{latestCandidateEnd}")
                if imputed:
                    warnings.append(f"imputedZeroComponents:{','.join(sorted(imputed))}")
                yield values, tuple(evidence.values()), str(candidate["__end"]), tuple(warnings)
                continue
        except EdgarStateError as error:
            # 한 접수의 단위나 값 충돌이 회사 전체를 죽이지 않는다. 다음 후보 접수로 넘어가고,
            # 어떤 후보도 성립하지 않으면 마지막에 첫 충돌 원인을 그대로 올린다.
            if firstConflict is None:
                firstConflict = error
            continue
    if firstConflict is not None:
        raise firstConflict


def _compileStock(
    pit: pl.DataFrame,
    *,
    requestedFiscalThrough: str | None = None,
) -> _StockCandidate:
    """최신 접수 기준으로 성립하는 첫 stock state를 반환한다."""

    for candidate in _stockCandidates(pit, requestedFiscalThrough=requestedFiscalThrough):
        return candidate
    raise EdgarStateError("no single accession contains a coherent stock state")


def _compileStockWithFlow(
    pit: pl.DataFrame,
    flowCompiler: Callable[[pl.DataFrame, str], _FlowResult],
    *,
    requestedFiscalThrough: str | None = None,
) -> tuple[_StockCandidate, _FlowResult]:
    """대차와 분기 흐름 창이 함께 성립하는 첫 접수 후보를 선택한다.

    Args:
        pit: 지식 시점으로 절단한 정규화 facts.
        flowCompiler: 선택한 회계 기간말로 흐름을 컴파일하는 호출자.
        requestedFiscalThrough: 명시한 회계 기간말.

    Returns:
        선택한 stock 후보와 그 후보 기준 흐름 컴파일 결과.

    Raises:
        EdgarStateError: 어떤 후보도 대차와 흐름을 동시에 만족하지 못할 때.

    Example:
        ``candidate, flows = _compileStockWithFlow(pit, _compileQuarterWindow)``.

    Guide:
        대차만 있는 최신 filing 때문에 흐름이 있는 직전 filing 을 놓치지 않게 한다.

    Requires:
        후보 순회는 최신 접수부터 시작해야 한다.

    AIContext:
        검증을 낮추지 않고 후보 탐색 범위만 넓힌다. 각 후보의 계약 검사는 그대로다.
    """

    firstFlowError: EdgarStateError | None = None
    for candidate in _stockCandidates(pit, requestedFiscalThrough=requestedFiscalThrough):
        try:
            flows = flowCompiler(pit, candidate[2])
        except EdgarStateError as error:
            if firstFlowError is None:
                firstFlowError = error
            continue
        return candidate, flows
    if firstFlowError is not None:
        raise firstFlowError
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


def _lineageAccessions(item: FactEvidence) -> tuple[str, ...]:
    """한 관측이 실제로 의존하는 접수 집합을 반환한다.

    관측값은 자기 접수 하나에, 유도값은 유도 입력이 가리키는 접수 집합에 의존한다.
    집합으로 비교해야 같은 접수 안에서 태그 두 개를 쓴 유도와 그 접수의 단일 관측을
    같은 filing lineage 로 인정할 수 있다.
    """

    if not item.derivationInputs:
        return (item.accession,)
    return tuple(sorted({entry.split("|", 1)[0] for entry in item.derivationInputs}))


def _componentDerivedOperatingProfit(
    minuend: dict[str, FactEvidence],
    subtrahend: dict[str, FactEvidence],
    *,
    derivation: str,
) -> dict[str, FactEvidence]:
    """같은 접수와 같은 회계 구간의 두 구성요소에서 영업이익을 유도한다.

    Args:
        minuend: 피감수 분기 관측. 매출총이익 또는 매출이다.
        subtrahend: 감수 분기 관측. 영업비용 또는 총비용이다.
        derivation: 유도 근거 문장.

    Returns:
        분기말별 유도 영업이익 ``FactEvidence`` 매핑.

    Example:
        ``_componentDerivedOperatingProfit(gross, opex, derivation="...")``.

    Guide:
        접수나 회계 구간이 다르면 유도하지 않는다. 서로 다른 filing 을 섞으면
        PIT 계약이 깨진다.

    Requires:
        두 구성요소는 같은 통화 단위여야 한다.

    AIContext:
        `OperatingIncomeLoss` 소계를 제시하지 않는 금융, REIT, 자산운용 filer 를
        검증 완화 없이 수용한다.
    """

    derived: dict[str, FactEvidence] = {}
    for end, lead in minuend.items():
        follow = subtrahend.get(end)
        if follow is None:
            continue
        if lead.accession != follow.accession:
            continue
        if lead.fiscalStart != follow.fiscalStart or lead.fiscalEnd != follow.fiscalEnd:
            continue
        if lead.unit != follow.unit or lead.currency != follow.currency:
            continue
        components = (lead, follow)
        derived[end] = FactEvidence(
            conceptId="operatingProfitQuarter",
            value=lead.value - follow.value,
            unit=lead.unit,
            currency=lead.currency,
            kind="flowQuarter",
            fiscalStart=lead.fiscalStart,
            fiscalEnd=lead.fiscalEnd,
            filedAt=max(lead.filedAt, follow.filedAt),
            accession=lead.accession,
            form=lead.form,
            tag=f"{lead.tag}-{follow.tag}",
            status="derived",
            derivation=derivation,
            derivationInputs=tuple(
                f"{item.accession}|{item.tag}|{item.fiscalStart}|{item.fiscalEnd}" for item in components
            ),
        )
    return derived


def _operatingProfitEvidence(
    pit: pl.DataFrame,
    revenue: dict[str, FactEvidence],
    *,
    fiscalThrough: str,
) -> dict[str, FactEvidence]:
    """관측 영업이익을 우선하고 없는 분기만 구성요소에서 유도한다."""

    observed = _quarterEvidence(
        pit,
        "operatingProfitQuarter",
        _OPERATING_PROFIT_TAGS,
        fiscalThrough=fiscalThrough,
    )
    missing = set(revenue) - set(observed)
    if not missing:
        return observed
    gross = _quarterEvidence(pit, "grossProfitQuarter", _GROSS_PROFIT_TAGS, fiscalThrough=fiscalThrough)
    operatingExpenses = _quarterEvidence(
        pit,
        "operatingExpensesQuarter",
        _OPERATING_EXPENSE_TAGS,
        fiscalThrough=fiscalThrough,
    )
    totalCosts = _quarterEvidence(pit, "totalCostsQuarter", _TOTAL_COSTS_TAGS, fiscalThrough=fiscalThrough)
    fallbacks = (
        _componentDerivedOperatingProfit(
            gross,
            operatingExpenses,
            derivation="gross profit minus operating expenses in one accession",
        ),
        _componentDerivedOperatingProfit(
            revenue,
            totalCosts,
            derivation="revenue minus total costs and expenses in one accession",
        ),
    )
    resolved = dict(observed)
    for candidate in fallbacks:
        for end in missing - set(resolved):
            item = candidate.get(end)
            if item is not None:
                resolved[end] = item
    return resolved


def _compileQuarterWindow(pit: pl.DataFrame, fiscalThrough: str) -> tuple[QuarterFlow, ...]:
    revenue = _quarterEvidence(pit, "revenueQuarter", _REVENUE_TAGS, fiscalThrough=fiscalThrough)
    operating = _operatingProfitEvidence(pit, revenue, fiscalThrough=fiscalThrough)
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
            if _lineageAccessions(revenueItem) != _lineageAccessions(operatingItem):
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
    candidate, ttm = _compileStockWithFlow(
        pit,
        _compileTtm,
        requestedFiscalThrough=fiscalThrough,
    )
    values, stockEvidence, effectiveFiscalThrough, warnings = candidate
    revenueTtm, operatingTtm, flowEvidence = ttm
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
    candidate, quarters = _compileStockWithFlow(
        pit,
        _compileQuarterWindow,
        requestedFiscalThrough=fiscalThrough,
    )
    values, stockEvidence, effectiveFiscalThrough, warnings = candidate
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
