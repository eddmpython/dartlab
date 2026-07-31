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


def _pick(rowsByTag: dict[str, list[dict]], conceptId: str, tags: tuple[str, ...], *, kind: str) -> FactEvidence | None:
    """한 접수의 태그 색인에서 우선순위가 가장 높은 관측을 고른다.

    ``_quarterEvidence`` 와 같은 규약이다. Polars 는 색인을 만들 때 한 번만 지나가고,
    태그 선택은 파이썬 dict 조회로 끝낸다. 접수 하나의 대차 행은 수십 줄이라 태그마다
    ``filter`` 를 부르면 실제 연산이 아니라 Polars 호출 고정비가 비용의 전부가 된다.

    Args:
        rowsByTag: 한 접수의 행을 태그별로 묶은 색인. 값은 원본 프레임 순서를 지킨다.
        conceptId: 생성할 evidence 의 개념 id.
        tags: 우선순위 순 태그 목록. 먼저 매칭되는 태그를 채택한다.
        kind: 생성할 evidence 종류.

    Returns:
        채택한 단일 관측. 어떤 태그도 없으면 ``None``.

    Raises:
        EdgarStateError: 통화가 USD 하나로 닫히지 않거나 한 접수 안에 값이 두 개일 때.

    Example:
        ``_pick(rowsByTag, "totalAssets", ("Assets",), kind="stock")``.

    Guide:
        색인은 ``__end``, ``accn``, ``__filed`` 세 값이 같은 행만 담으므로 접수 하나다.

    Requires:
        ``_normalize`` 를 통과한 행이어야 한다. ``__value`` 는 결측도 비유한도 아니다.

    AIContext:
        같은 접수에서 같은 태그가 서로 다른 값을 들고 있으면 고르지 않고 실패한다.
        조용히 하나를 택하면 어느 값이 쓰였는지 evidence 로 되짚을 수 없다.
    """

    for tag in tags:
        rows = rowsByTag.get(tag)
        if not rows:
            continue
        units = {str(row["unit"]) for row in rows if row["unit"] is not None}
        if units != {"USD"}:
            raise EdgarStateError(f"unit conflict for {conceptId}: {sorted(units)}")
        values = {float(row["__value"]) for row in rows}
        if len(values) != 1:
            raise EdgarStateError(f"conflicting values for {conceptId} in one accession")
        # 색인 한 칸은 ``__filed`` 가 같은 접수 하나라 최신 선택은 첫 행이다.
        return _rawEvidence(conceptId, rows[0], kind=kind)
    return None


def _indexStockRows(stock: pl.DataFrame) -> dict[tuple[str, str, str], dict[str, list[dict]]]:
    """stock 행을 접수별, 태그별로 한 번에 색인한다.

    Args:
        stock: 기간 시작이 없는 대차 관측만 남긴 정규화 프레임.

    Returns:
        ``(fiscalEnd, accession, filedAt)`` 을 키로, 태그별 행 목록을 값으로 갖는 색인.
        각 목록은 원본 프레임 순서를 지킨다.

    Raises:
        없음. 순수 재배치다.

    Example:
        ``groups[("20241231", "0000036270-25-000030", "20250221")]["Assets"]``.

    Guide:
        후보 순회 전에 한 번만 부른다. 후보마다 부르면 이 함수의 목적이 사라진다.

    Requires:
        ``__end``, ``accn``, ``__filed``, ``tag`` 열이 있어야 한다.

    AIContext:
        후보 수와 태그 수의 곱만큼 Polars 에 재진입하던 경로를 한 번의 순회로 바꾼다.
    """

    grouped: dict[tuple[str, str, str], dict[str, list[dict]]] = {}
    for row in stock.iter_rows(named=True):
        key = (str(row["__end"]), str(row["accn"]), str(row["__filed"]))
        grouped.setdefault(key, {}).setdefault(str(row["tag"]), []).append(row)
    return grouped


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
        | set(_NONCONTROLLING_INTEREST_TAGS)
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
    groups = _indexStockRows(stock)
    for candidate in candidates.iter_rows(named=True):
        rowsByTag = groups.get(
            (str(candidate["__end"]), str(candidate["accn"]), str(candidate["__filed"])),
            {},
        )
        try:
            picked = _stockConceptEvidence(rowsByTag)
            if picked is None:
                continue
            evidence, imputed = picked
            evidence["totalDebt"] = _stockDebtEvidence(rowsByTag, candidate, evidence, imputed)
            values = {conceptId: item.value for conceptId, item in evidence.items()}
            for conceptId in imputed:
                values.setdefault(conceptId, 0.0)
            warnings = []
            if str(candidate["__end"]) != latestCandidateEnd:
                warnings.append(f"latestIncompleteFiling:{latestCandidateEnd}")
            if imputed:
                warnings.append(f"imputedZeroComponents:{','.join(sorted(imputed))}")
            yield values, tuple(evidence.values()), str(candidate["__end"]), tuple(warnings)
        except EdgarStateError as error:
            # 한 접수의 단위나 값 충돌이 회사 전체를 죽이지 않는다. 다음 후보 접수로 넘어가고,
            # 어떤 후보도 성립하지 않으면 마지막에 첫 충돌 원인을 그대로 올린다.
            if firstConflict is None:
                firstConflict = error
            continue
    if firstConflict is not None:
        raise firstConflict


def _stockConceptEvidence(rowsByTag: dict[str, list[dict]]) -> tuple[dict[str, FactEvidence], list[str]] | None:
    """한 접수의 대차 개념을 골라 evidence 와 imputed 목록을 만든다.

    반환 ``None`` 은 앵커 개념(자산·부채·자본)이 없어 이 후보로는 상태를 세울 수 없다는 뜻이다.
    dict 삽입 순서가 그대로 evidence tuple 순서가 되므로 키 교체와 추가 위치를 지킨다.
    """
    evidence: dict[str, FactEvidence] = {}
    imputed: list[str] = []
    for conceptId, tags in _STOCK_TAGS.items():
        selected = _pick(rowsByTag, conceptId, tags, kind="stock")
        if selected is None:
            if conceptId in _STOCK_ANCHOR_CONCEPTS:
                return None
            # 미태깅 구성요소는 결측이 아니라 세분성 부족이다. 0 으로 두면 그 금액이
            # `otherNetAssets` 잔차 플러그로 흡수되고 대차 항등식은 그대로 닫힌다.
            # 재고 개념이 없는 소프트웨어, 서비스, 금융, REIT 를 실패로 처리하지 않는다.
            imputed.append(conceptId)
            continue
        evidence[conceptId] = selected

    equity = evidence["equityIncludingNci"]
    if equity.tag == "StockholdersEquity":
        # 지배주주 자본만 태깅됐다면 비지배지분을 더해야 항등식이 닫힌다.
        # 더하지 않으면 비지배지분이 있는 회사가 구조적으로 항등식 검사에 걸린다.
        noncontrolling = _pick(rowsByTag, "noncontrollingInterest", _NONCONTROLLING_INTEREST_TAGS, kind="stock")
        if noncontrolling is not None:
            evidence["noncontrollingInterest"] = noncontrolling
            evidence["equityIncludingNci"] = _combinedEquity(equity, noncontrolling)
    return evidence, imputed


def _stockDebtEvidence(
    rowsByTag: dict[str, list[dict]],
    candidate: dict,
    evidence: dict[str, FactEvidence],
    imputed: list[str],
) -> FactEvidence:
    """차입금 블록을 조립한다. 채택한 구성요소는 ``evidence`` 에 그 자리에서 얹는다.

    term debt 는 유동+비유동 우선, 없으면 보고 총액, 둘 다 없으면 0 이다. 단기 조달은
    term debt 와 겹치지 않으므로 항상 더한다.
    """
    current = _pick(rowsByTag, "currentTermDebt", _DEBT_CURRENT_TERM, kind="stock")
    shortFunding = _pick(rowsByTag, "shortTermFunding", _DEBT_SHORT_FUNDING, kind="stock")
    noncurrent = _pick(rowsByTag, "interestBearingDebtNoncurrent", _DEBT_NONCURRENT, kind="stock")
    total = _pick(rowsByTag, "reportedTotalDebt", _DEBT_TOTAL, kind="stock")
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
    return FactEvidence(
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

    # 후보는 접수 단위라서 같은 회계 기간말을 여러 접수가 공유한다. 흐름 컴파일은
    # ``pit`` 과 기간말만 읽는 순수 함수이므로 기간말이 같으면 결과도 오류도 같다.
    # 기간말별로 한 번만 부르지 않으면 같은 계산을 접수 수만큼 되풀이한다.
    compiled: dict[str, _FlowResult | EdgarStateError] = {}
    firstFlowError: EdgarStateError | None = None
    for candidate in _stockCandidates(pit, requestedFiscalThrough=requestedFiscalThrough):
        fiscalThrough = candidate[2]
        if fiscalThrough not in compiled:
            try:
                compiled[fiscalThrough] = flowCompiler(pit, fiscalThrough)
            except EdgarStateError as error:
                compiled[fiscalThrough] = error
        outcome = compiled[fiscalThrough]
        if isinstance(outcome, EdgarStateError):
            if firstFlowError is None:
                firstFlowError = outcome
            continue
        return candidate, outcome
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

    out = dict(_selectQuarterFacts(flowEnds, flowRowsByEnd, quarterSelectionCache, tags, conceptId))
    for end in sorted(annualRowsByEnd, reverse=True):
        if end in out:
            continue
        annual = _selectLatestRow(
            annualRowsByEnd[end],
            tags,
            conceptId,
            conflictKind="annual",
            fiscalEnd=end,
            kind="flowAnnual",
        )
        if annual is None or annual.fiscalStart is None:
            continue
        # 4분기는 단독 공시가 드물어 두 경로로 유도한다. 연간에서 9개월 누계를 빼는 쪽이
        # 우선이고, 누계가 없거나 기간이 안 맞으면 앞 세 분기 합을 빼는 쪽으로 넘어간다.
        residual = _q4FromYearToDate(annual, yearToDateRowsByStart, tags, conceptId)
        if residual is None:
            asKnownAtAnnual = _selectQuarterFacts(
                flowEnds,
                flowRowsByEnd,
                quarterSelectionCache,
                tags,
                conceptId,
                filedThrough=annual.filedAt,
            )
            residual = _q4FromFirstThreeQuarters(annual, asKnownAtAnnual, conceptId)
        if residual is not None:
            out[str(end)] = residual
    return out


def _selectLatestRow(
    rows: list[dict],
    tags: tuple[str, ...],
    conceptId: str,
    *,
    conflictKind: str,
    fiscalEnd: str,
    kind: str,
) -> FactEvidence | None:
    """태그 우선순위와 최신 filing 기준으로 한 관측을 선택한다.

    Args:
        rows: 동일 기간 후보 행.
        tags: 우선순위 순 태그 목록.
        conceptId: 생성할 evidence 의 개념 id.
        conflictKind: 충돌 오류에 표시할 관측 종류.
        fiscalEnd: 충돌 오류에 표시할 회계 기간말.
        kind: 생성할 evidence 종류.

    Returns:
        최신 단일 관측. 후보가 없으면 ``None``.

    Raises:
        EdgarStateError: 최신 접수 안에 서로 다른 값이 있으면 발생한다.

    Example:
        ``_selectLatestRow(rows, tags, cid, conflictKind="quarterly", fiscalEnd=end, kind="flowQuarter")``.
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


def _selectQuarterFacts(
    flowEnds: tuple[str, ...],
    flowRowsByEnd: dict[str, list[dict]],
    cache: dict[str | None, dict[str, FactEvidence]],
    tags: tuple[str, ...],
    conceptId: str,
    filedThrough: str | None = None,
) -> dict[str, FactEvidence]:
    """주어진 filing cutoff 안에서 분기별 최신 단독 흐름을 선택한다.

    Args:
        flowEnds: 최신순 분기말 목록.
        flowRowsByEnd: 분기말별 후보 행.
        cache: cutoff 별 선택 결과 캐시. 같은 cutoff 재계산을 막는다.
        tags: 우선순위 순 태그 목록.
        conceptId: 생성할 evidence 의 개념 id.
        filedThrough: 포함할 최신 filing 날짜. ``None``이면 전체를 포함한다.

    Returns:
        분기말별 최신 ``FactEvidence`` 매핑.

    Raises:
        EdgarStateError: 같은 분기와 최신 접수에 서로 다른 값이 있으면 발생한다.

    Example:
        ``_selectQuarterFacts(ends, rows, cache, tags, cid, filedThrough="20250131")``.
    """

    cached = cache.get(filedThrough)
    if cached is not None:
        return cached
    selected: dict[str, FactEvidence] = {}
    for end in flowEnds:
        endRows = flowRowsByEnd[end]
        if filedThrough is not None:
            endRows = [row for row in endRows if str(row["__filed"]) <= filedThrough]
        evidence = _selectLatestRow(
            endRows,
            tags,
            conceptId,
            conflictKind="quarterly",
            fiscalEnd=end,
            kind="flowQuarter",
        )
        if evidence is not None:
            selected[end] = evidence
    cache[filedThrough] = selected
    return selected


def _q4FromYearToDate(
    annual: FactEvidence,
    yearToDateRowsByStart: dict[str, list[dict]],
    tags: tuple[str, ...],
    conceptId: str,
) -> FactEvidence | None:
    """연간에서 같은 접수의 9개월 누계를 빼 4분기 잔차를 만든다.

    누계가 없거나 남은 구간이 한 분기(60~120 일) 를 벗어나면 ``None`` 을 돌려주고
    호출자가 세 분기 합 경로로 넘어간다.
    """

    ytdCandidates = [
        row
        for row in yearToDateRowsByStart.get(annual.fiscalStart, ())
        if str(row["__end"]) < annual.fiscalEnd and str(row["__filed"]) <= annual.filedAt
    ]
    if not ytdCandidates:
        return None
    latestEnd = max(str(row["__end"]) for row in ytdCandidates)
    ytd = _selectLatestRow(
        [row for row in ytdCandidates if str(row["__end"]) == latestEnd],
        tags,
        conceptId,
        conflictKind="year-to-date",
        fiscalEnd=latestEnd,
        kind="flowYearToDate",
    )
    if ytd is None:
        return None
    q4Start = (datetime.strptime(ytd.fiscalEnd, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    q4Days = (datetime.strptime(annual.fiscalEnd, "%Y%m%d") - datetime.strptime(q4Start, "%Y%m%d")).days
    if not 60 <= q4Days <= 120:
        return None
    return FactEvidence(
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


def _q4FromFirstThreeQuarters(
    annual: FactEvidence,
    asKnownAtAnnual: dict[str, FactEvidence],
    conceptId: str,
) -> FactEvidence | None:
    """연간에서 앞 세 단독 분기 합을 빼 4분기 잔차를 만든다.

    세 분기가 회계연도 시작에 붙어 있고 서로 14 일 이내로 이어져야 같은 연도의 연속
    구간으로 인정한다. 조건이 하나라도 어긋나면 유도하지 않는다.
    """

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
        return None
    annualStart = datetime.strptime(annual.fiscalStart, "%Y%m%d")
    firstStart = datetime.strptime(str(firstThree[0].fiscalStart), "%Y%m%d")
    gaps = [
        (datetime.strptime(str(current.fiscalStart), "%Y%m%d") - datetime.strptime(previous.fiscalEnd, "%Y%m%d")).days
        for previous, current in zip(firstThree, firstThree[1:])
    ]
    if not 0 <= (firstStart - annualStart).days <= 14 or any(gap < 0 or gap > 14 for gap in gaps):
        return None
    q4Start = (datetime.strptime(firstThree[-1].fiscalEnd, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    q4Days = (datetime.strptime(annual.fiscalEnd, "%Y%m%d") - datetime.strptime(q4Start, "%Y%m%d")).days
    if q4Days < 60 or q4Days > 120:
        return None
    return FactEvidence(
        conceptId=conceptId,
        value=annual.value - sum(item.value for item in firstThree),
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
        derivationInputs=tuple(
            f"{item.accession}|{item.tag}|{item.fiscalStart}|{item.fiscalEnd}" for item in (annual, *firstThree)
        ),
    )


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

    def _priorQuarter(currentEnd: str) -> str | None:
        """현재 분기 시작일과 연속되는 직전 공통 분기말을 찾는다.

        Args:
            currentEnd: 현재 분기말. ``YYYYMMDD`` 형식이다.

        Returns:
            연속되는 직전 공통 분기말. 없으면 ``None``.

        Raises:
            ValueError: 분기 날짜 문자열이 올바르지 않으면 발생한다.

        Example:
            ``_priorQuarter("20241231")`` 로 직전 공통 분기말을 찾는다.
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
        prior = _priorQuarter(commonEnds[-1])
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

    def _priorQuarter(currentEnd: str) -> str | None:
        """연속되는 직전 매출 분기말을 찾는다. 없으면 ``None``."""
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
        prior = _priorQuarter(commonEnds[-1])
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
