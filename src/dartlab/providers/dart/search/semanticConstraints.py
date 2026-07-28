"""Data-compiled semantic constraints for product search ranking."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import numpy as np
import polars as pl

from dartlab.providers.dart.search.coerce import _dateOrdinal
from dartlab.providers.dart.search.facetPlanner import QueryFacets, facetMismatchReason, planQueryFacets
from dartlab.providers.dart.search.sourceIntent import SourceIntent

_ASCII_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9.-]{0,15}|\d{4,14}")
_ALIAS_CLEAN_RE = re.compile(r"[^0-9a-z가-힣]+")
_YEAR_RE = re.compile(r"\b(20\d{2})년?\b")
_MAPPER_CACHE: dict[tuple[tuple[str, int, int], ...], "SemanticMapper"] = {}
_HANGUL_RUN_RE = re.compile(r"[가-힣]{2,}")

_EDGAR_TERMS: tuple[str, ...] = ("edgar", "10-k", "10k", "10-q", "10q", "8-k", "8k")
_PANEL_TERMS: tuple[str, ...] = ("panel", "파케", "parquet")
_BODY_SOURCE_TERMS: tuple[str, ...] = ("본문", "주석", "사업의 내용", "위험요인", "md&a", "risk")
_FILING_ORIGINAL_TERMS: tuple[str, ...] = ("공시 원문", "공시원문", "제출", "접수", "결정", "변경")
_PHASE_DECISION_TERMS: tuple[str, ...] = ("결정",)
_PHASE_RESULT_TERMS: tuple[str, ...] = ("결과", "완료", "종료보고서")
_PHASE_MEETING_NOTICE_TERMS: tuple[str, ...] = ("소집공고",)
_PHASE_MEETING_RESOLUTION_TERMS: tuple[str, ...] = ("소집결의",)
_PHASE_MAJOR_SHAREHOLDER_QUERY_TERMS: tuple[str, ...] = ("최대주주",)
_PHASE_MAJOR_SHAREHOLDER_REPORT_TERMS: tuple[str, ...] = ("최대주주등소유주식변동",)
_PHASE_SCORE_WEIGHT = 1.0
_EXPLICIT_PHASE_SCORE = 40.0
_TOPIC_STOP_TERMS: frozenset[str] = frozenset(
    {
        "공시",
        "원문",
        "본문",
        "주석",
        "보고서",
        "사업보고서",
        "분기보고서",
        "반기보고서",
        "정기보고서",
        "뉴스",
        "기사",
        "제출",
        "접수",
    }
)


@dataclass(frozen=True)
class AliasProfile:
    """Compiled entity alias profile."""

    alias: str
    companyName: str
    stockCode: str
    corpCode: str
    sourceCounts: Mapping[str, int]

    @property
    def dominantSourceClass(self) -> str:
        """Return the dominant concrete source class.

        Args:
            None.

        Returns:
            str: One of ``news``, ``allFilings``, ``panel``, ``edgar``, or empty.

        Raises:
            None.

        Example:
            >>> AliasProfile("aapl", "AAPL", "AAPL", "", {"edgar": 2}).dominantSourceClass
            'edgar'
        """
        if not self.sourceCounts:
            return ""
        return max(self.sourceCounts.items(), key=lambda item: (item[1], item[0]))[0]


@dataclass(frozen=True)
class SemanticMapper:
    """Runtime mapper compiled from current search metadata."""

    aliases: Mapping[str, AliasProfile]


@dataclass(frozen=True)
class SemanticConstraintPlan:
    """Constraint plan used by search ranking and answerability."""

    facets: QueryFacets
    sourceClasses: tuple[str, ...] = ()
    sourceReason: str = ""
    matchedAlias: str = ""
    year: str = ""
    topicTerms: tuple[str, ...] = ()

    @property
    def hasConstraints(self) -> bool:
        """Return whether the plan has ranking constraints.

        Args:
            None.

        Returns:
            bool: True when any facet or concrete source class is present.

        Raises:
            None.

        Example:
            >>> SemanticConstraintPlan(QueryFacets(stockCode="005930")).hasConstraints
            True
        """
        return bool(self.facets.hasConstraints or self.sourceClasses or self.year)


def compileSemanticMapper(segments: Mapping[str, tuple[dict, pl.DataFrame]]) -> SemanticMapper:
    """Compile a mapper from loaded content-index metadata.

    Args:
        segments: Search segments returned by ``fieldIndex._getSegments``.

    Returns:
        SemanticMapper: Alias profiles compiled from current index rows.

    Raises:
        None.

    Example:
        >>> compileSemanticMapper({}).aliases
        {}
    """
    key = tuple(sorted((name, id(meta), meta.height) for name, (_, meta) in segments.items()))
    cached = _MAPPER_CACHE.get(key)
    if cached is not None:
        return cached
    mapper = compileSemanticMapperFromRows(_iterSegmentRows(segments))
    if len(_MAPPER_CACHE) > 4:
        _MAPPER_CACHE.clear()
    _MAPPER_CACHE[key] = mapper
    return mapper


def compileActiveSemanticMapper() -> SemanticMapper:
    """Compile a mapper from the active local content index.

    Args:
        None.

    Returns:
        SemanticMapper: Current index mapper, or an empty mapper when no index is loaded.

    Raises:
        None.

    Example:
        >>> callable(compileActiveSemanticMapper)
        True
    """
    from dartlab.providers.dart.search.fieldIndex import _getSegments

    return compileSemanticMapper(_getSegments())


def compileSemanticMapperFromRows(rows: Iterable[Mapping[str, Any]]) -> SemanticMapper:
    """Compile alias profiles from row metadata.

    Args:
        rows: Iterable of search metadata rows.

    Returns:
        SemanticMapper: Mapper compiled without hand-maintained company tables.

    Raises:
        None.

    Example:
        >>> rows = [{"source": "edgar-panel", "corp_name": "AAPL", "stock_code": "AAPL"}]
        >>> compileSemanticMapperFromRows(rows).aliases["aapl"].dominantSourceClass
        'edgar'
    """
    accum: dict[str, dict[str, Any]] = {}
    for row in rows:
        sourceClass = rowSourceClass(row)
        companyName = _cleanText(row.get("corp_name") or row.get("companyName"))
        stockCode = _cleanText(row.get("stock_code") or row.get("stockCode"))
        corpCode = _cleanText(row.get("corp_code") or row.get("corpCode"))
        for alias in _rowAliases(companyName=companyName, stockCode=stockCode, corpCode=corpCode):
            item = accum.setdefault(
                alias,
                {
                    "companies": Counter(),
                    "stocks": Counter(),
                    "corps": Counter(),
                    "sources": Counter(),
                },
            )
            if companyName:
                item["companies"][companyName] += 1
            if stockCode:
                item["stocks"][stockCode] += 1
            if corpCode:
                item["corps"][corpCode] += 1
            if sourceClass:
                item["sources"][sourceClass] += 1

    aliases: dict[str, AliasProfile] = {}
    for alias, item in accum.items():
        sourceCounts = dict(item["sources"])
        if not sourceCounts:
            continue
        aliases[alias] = AliasProfile(
            alias=alias,
            companyName=_counterMode(item["companies"]),
            stockCode=_counterMode(item["stocks"]),
            corpCode=_counterMode(item["corps"]),
            sourceCounts=sourceCounts,
        )
    return SemanticMapper(aliases=aliases)


def planSemanticConstraints(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    sourceIntent: SourceIntent | str | None = None,
    mapper: SemanticMapper | None = None,
) -> SemanticConstraintPlan:
    """Build a constraint plan for ranking and answerability.

    Args:
        query: User search query.
        corpCode: Explicit DART corp code, if supplied by public API.
        stockCode: Explicit stock code or ticker, if supplied by public API.
        sourceIntent: Source family intent detected by ``sourceIntent``.
        mapper: Optional precompiled mapper.

    Returns:
        SemanticConstraintPlan: Query facets plus concrete source-class constraints.

    Raises:
        None.

    Example:
        >>> mapper = compileSemanticMapperFromRows([{"source": "edgar-panel", "stock_code": "ADI", "corp_name": "ADI"}])
        >>> planSemanticConstraints("ADI 2026 분기보고서", mapper=mapper).sourceClasses
        ('edgar',)
    """
    mapper = mapper or compileActiveSemanticMapper()
    base = planQueryFacets(query, corpCode=corpCode, stockCode=stockCode)
    alias = matchSemanticAlias(query, mapper)
    mergedStockCode = base.stockCode or (alias.stockCode if alias else None)
    aliasCorpCode = alias.corpCode if alias and not mergedStockCode else None
    mergedCorpCode = base.corpCode or aliasCorpCode
    mergedCompanyName = base.companyName or (alias.companyName if alias else None)
    year = _queryYear(query)
    facets = QueryFacets(
        receiptNumbers=base.receiptNumbers,
        dates=base.dates,
        years=base.years or ((year,) if year else ()),
        reportTerms=base.reportTerms,
        literalTerms=base.literalTerms,
        stockCode=mergedStockCode,
        corpCode=mergedCorpCode,
        companyName=mergedCompanyName,
        freshnessRequired=base.freshnessRequired,
    )
    sourceClasses, sourceReason = _sourceClassesForQuery(query, sourceIntent=sourceIntent, alias=alias)
    return SemanticConstraintPlan(
        facets=facets,
        sourceClasses=sourceClasses,
        sourceReason=sourceReason,
        matchedAlias=alias.alias if alias else "",
        year=year,
        topicTerms=_filterEntityTopicTerms(_topicTerms(query), alias=alias, facets=facets),
    )


def matchSemanticAlias(query: str, mapper: SemanticMapper) -> AliasProfile | None:
    """Return the best alias profile mentioned by a query.

    Args:
        query: Search query.
        mapper: Compiled metadata mapper.

    Returns:
        AliasProfile | None: Best alias profile or None.

    Raises:
        None.

    Example:
        >>> mapper = compileSemanticMapperFromRows([{"source": "edgar-panel", "stock_code": "ADI"}])
        >>> matchSemanticAlias("ADI 10-Q", mapper).stockCode
        'ADI'
    """
    if not query or not mapper.aliases:
        return None
    cleanQuery = _cleanAlias(query)
    asciiTokens = _asciiTokens(query)
    matches: list[tuple[int, int, AliasProfile]] = []
    for alias, profile in mapper.aliases.items():
        if not _aliasMatches(alias, cleanQuery=cleanQuery, asciiTokens=asciiTokens):
            continue
        matches.append((len(alias), sum(profile.sourceCounts.values()), profile))
    if not matches:
        return None
    matches.sort(key=lambda item: (item[0], item[1], item[2].dominantSourceClass), reverse=True)
    return matches[0][2]


def semanticScopeMask(meta: pl.DataFrame, plan: SemanticConstraintPlan | None) -> np.ndarray | None:
    """Return a source-class pre-rank mask for a semantic plan.

    Args:
        meta: Segment metadata aligned to score arrays.
        plan: Semantic constraint plan.

    Returns:
        np.ndarray | None: Boolean mask, or None when no concrete source class is required.

    Raises:
        None.

    Example:
        >>> semanticScopeMask(pl.DataFrame(), None) is None
        True
    """
    if plan is None or not plan.sourceClasses or meta.height == 0 or "source" not in meta.columns:
        return None
    allowed = set(plan.sourceClasses)
    return np.array([rowSourceClass({"source": value}) in allowed for value in meta["source"].to_list()], dtype=bool)


def scoreSemanticConstraintEvidence(
    meta: pl.DataFrame,
    plan: SemanticConstraintPlan | None,
    *,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """Build a structural candidate lane from metadata constraints.

    Args:
        meta: Segment metadata aligned to score arrays.
        plan: Semantic constraint plan.
        mask: Optional pre-rank mask already applied to BM25 lanes.

    Returns:
        np.ndarray: Constraint evidence scores aligned to ``meta`` rows.

    Raises:
        None.

    Example:
        >>> meta = pl.DataFrame({"source": ["edgar-panel"], "stock_code": ["AAPL"], "rcept_dt": ["20260101"]})
        >>> plan = SemanticConstraintPlan(QueryFacets(stockCode="AAPL", years=("2026",)), sourceClasses=("edgar",))
        >>> bool(scoreSemanticConstraintEvidence(meta, plan)[0] > 0)
        True
    """
    scores = np.zeros(meta.height, dtype=np.float32)
    if meta.height == 0 or plan is None or not plan.hasConstraints:
        return scores
    indices = np.nonzero(mask)[0] if mask is not None else np.arange(meta.height)
    if len(indices) > 10000 and not _hasNarrowEntityFacet(plan):
        return scores
    constraintCount = max(_constraintCount(plan), 1)
    for rawIndex in indices:
        index = int(rawIndex)
        row = meta.row(index, named=True)
        violations = semanticConstraintViolations(row, plan)
        if len(violations) >= constraintCount:
            continue
        satisfied = constraintCount - len(violations)
        topicCoverage = _topicCoverage(row, plan)
        scores[index] = np.float32(180.0 + 20.0 * satisfied + 80.0 * topicCoverage - 15.0 * len(violations))
    return scores


def rankBySemanticConstraints(hits: list[dict], plan: SemanticConstraintPlan | None) -> list[dict]:
    """Rank hits by constraint satisfaction before score tie-breaks.

    Args:
        hits: Candidate hits after BM25/RRF and optional rerank.
        plan: Semantic constraint plan.

    Returns:
        list[dict]: Ranked hits with constraint diagnostic columns.

    Raises:
        None.

    Example:
        >>> plan = SemanticConstraintPlan(QueryFacets(stockCode="AAPL"), sourceClasses=("edgar",))
        >>> rows = [{"source": "panel", "stock_code": "005930", "score": 9}, {"source": "edgar-panel", "stock_code": "AAPL", "score": 1}]
        >>> rankBySemanticConstraints(rows, plan)[0]["source"]
        'edgar-panel'
    """
    if not hits or plan is None or not plan.hasConstraints:
        return hits
    constraintCount = max(_constraintCount(plan), 1)
    scored: list[tuple[float, int, dict]] = []
    total = max(1, len(hits))
    dateValues = [_dateOrdinal(row.get("rcept_dt") or row.get("date")) for row in hits]
    maxDate = max(dateValues or [0])
    minDate = min([value for value in dateValues if value] or [maxDate])
    dateSpan = max(1, maxDate - minDate)
    for index, row in enumerate(hits):
        violations = semanticConstraintViolations(row, plan)
        satisfied = constraintCount - len(violations)
        originalScore = _float(row.get("score"))
        originalRank = 1.0 - (index / total)
        dateValue = dateValues[index]
        freshness = (dateValue - minDate) / dateSpan if dateValue else 0.0
        topicCoverage = _topicCoverage(row, plan)
        phaseScore = _phaseScore(row, plan, latestDate=maxDate)
        constraintScore = (
            (100.0 * satisfied)
            - (1000.0 * len(violations))
            + (50.0 * topicCoverage)
            + (_PHASE_SCORE_WEIGHT * phaseScore)
            + (35.0 * freshness)
            + originalRank
        )
        out = {
            **row,
            "score": constraintScore + (0.01 * originalScore),
            "semanticConstraintScore": constraintScore,
            "semanticPhaseScore": phaseScore,
            "constraintViolationReason": ",".join(violations),
        }
        scored.append((float(out["score"]), index, out))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return _markConstrainedSiblings([row for _, _, row in scored], plan)


def semanticConstraintViolations(row: Mapping[str, Any], plan: SemanticConstraintPlan | None) -> list[str]:
    """Return semantic constraint violations for one result row.

    Args:
        row: Search result row.
        plan: Semantic constraint plan.

    Returns:
        list[str]: Violation reason codes.

    Raises:
        None.

    Example:
        >>> plan = SemanticConstraintPlan(QueryFacets(stockCode="AAPL"), sourceClasses=("edgar",))
        >>> semanticConstraintViolations({"source": "panel", "stock_code": "005930"}, plan)
        ['constraintMismatch:sourceClass', 'facetMismatch:stockCode']
    """
    if plan is None or not plan.hasConstraints:
        return []
    violations: list[str] = []
    if plan.sourceClasses and rowSourceClass(row) not in set(plan.sourceClasses):
        violations.append("constraintMismatch:sourceClass")
    reason = facetMismatchReason(dict(row), plan.facets)
    if reason:
        violations.append(reason)
    if _requiresTopicConstraint(plan) and _topicCoverage(row, plan) <= 0.0:
        violations.append("constraintMismatch:topic")
    return violations


def rowSourceClass(row: Mapping[str, Any]) -> str:
    """Map a concrete row source into a source class.

    Args:
        row: Search metadata or result row.

    Returns:
        str: ``news``, ``allFilings``, ``panel``, ``edgar``, or empty.

    Raises:
        None.

    Example:
        >>> rowSourceClass({"source": "edgar-panel"})
        'edgar'
    """
    source = str(row.get("source") or row.get("sourceKind") or "")
    ref = str(row.get("sourceRef") or "")
    value = source.strip()
    lower = value.lower()
    if value == "news" or lower.startswith("news") or ref.startswith("news:"):
        return "news"
    if value in {"edgarPanel", "edgar-panel"} or lower.startswith("edgar") or ref.startswith("edgar:"):
        return "edgar"
    if value in {"dartPanel", "panel"} or "panel" in lower or ref.startswith("dart:panel:"):
        return "panel"
    if value == "allFilings" or ref.startswith("dart:allFilings:"):
        return "allFilings"
    return value


def _iterSegmentRows(segments: Mapping[str, tuple[dict, pl.DataFrame]]) -> Iterable[dict[str, Any]]:
    columns = (
        "source",
        "sourceRef",
        "corp_name",
        "corp_code",
        "stock_code",
    )
    for _, meta in segments.values():
        if meta.height == 0:
            continue
        existing = [column for column in columns if column in meta.columns]
        for row in meta.select(existing).unique().iter_rows(named=True):
            yield row


def _sourceClassesForQuery(
    query: str,
    *,
    sourceIntent: SourceIntent | str | None,
    alias: AliasProfile | None,
) -> tuple[tuple[str, ...], str]:
    text = " ".join(str(query or "").strip().lower().split())
    intentKind = sourceIntent.kind if isinstance(sourceIntent, SourceIntent) else str(sourceIntent or "")
    if intentKind == "news":
        return ("news",), "sourceIntent"
    if _hasAny(text, _EDGAR_TERMS):
        return ("edgar",), "explicitEdgar"
    if alias and alias.dominantSourceClass == "edgar":
        return ("edgar",), "aliasDominantEdgar"
    if _hasAny(text, _PANEL_TERMS):
        return ("panel",), "explicitPanel"
    if _hasAny(text, _BODY_SOURCE_TERMS):
        return ("panel",), "bodyEvidence"
    if _hasAny(text, _FILING_ORIGINAL_TERMS):
        return ("allFilings",), "filingOriginal"
    return (), ""


def _rowAliases(*, companyName: str, stockCode: str, corpCode: str) -> set[str]:
    aliases = {_cleanAlias(companyName), _cleanAlias(stockCode), _cleanAlias(corpCode)}
    if companyName.endswith("자동차") and len(companyName) > 3:
        aliases.add(_cleanAlias(companyName[: -len("자동차")] + "차"))
    return {alias for alias in aliases if _usableAlias(alias)}


def _usableAlias(alias: str) -> bool:
    if not alias:
        return False
    if alias.isdigit():
        return len(alias) >= 4
    if alias.isascii():
        return len(alias) >= 1
    return len(alias) >= 2


def _aliasMatches(alias: str, *, cleanQuery: str, asciiTokens: set[str]) -> bool:
    if not alias:
        return False
    if alias.isascii() and any(ch.isalpha() for ch in alias):
        if len(alias) <= 4:
            return alias in asciiTokens
        return alias in asciiTokens or alias in cleanQuery
    if alias.isdigit():
        return alias in asciiTokens or alias in cleanQuery
    return alias in cleanQuery


def _asciiTokens(query: str) -> set[str]:
    out: set[str] = set()
    for token in _ASCII_TOKEN_RE.findall(str(query or "")):
        clean = token.strip(".-").lower()
        if clean:
            out.add(clean)
            compact = _cleanAlias(clean)
            if compact:
                out.add(compact)
    return out


def _cleanAlias(value: Any) -> str:
    return _ALIAS_CLEAN_RE.sub("", str(value or "").lower())


def _cleanText(value: Any) -> str:
    return str(value or "").strip()


def _counterMode(counter: Counter[str]) -> str:
    if not counter:
        return ""
    return counter.most_common(1)[0][0]


def _queryYear(query: str) -> str:
    match = _YEAR_RE.search(str(query or ""))
    return match.group(1) if match else ""


def _hasAny(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _topicTerms(query: str) -> tuple[str, ...]:
    terms: list[str] = []
    for run in _HANGUL_RUN_RE.findall(str(query or "")):
        if run in _TOPIC_STOP_TERMS:
            continue
        if run.endswith("보고서") and run in _TOPIC_STOP_TERMS:
            continue
        if run not in terms:
            terms.append(run)
    return tuple(terms[:4])


def _filterEntityTopicTerms(
    terms: tuple[str, ...],
    *,
    alias: AliasProfile | None,
    facets: QueryFacets,
) -> tuple[str, ...]:
    entityAliases = {
        _cleanAlias(facets.companyName),
        _cleanAlias(facets.stockCode),
        _cleanAlias(facets.corpCode),
    }
    if alias is not None:
        entityAliases.update(
            {
                _cleanAlias(alias.alias),
                _cleanAlias(alias.companyName),
                _cleanAlias(alias.stockCode),
                _cleanAlias(alias.corpCode),
            }
        )
    out: list[str] = []
    for term in terms:
        clean = _cleanAlias(term)
        if not clean or clean in entityAliases:
            continue
        if term not in out:
            out.append(term)
    return tuple(out)


def _topicCoverage(row: Mapping[str, Any], plan: SemanticConstraintPlan) -> float:
    if not plan.topicTerms:
        return 0.0
    surface = " ".join(
        str(row.get(key) or "").lower()
        for key in (
            "report_nm",
            "reportName",
            "title",
            "section_title",
            "sectionTitle",
            "snippet",
            "evidenceText",
            "text",
        )
    )
    if not surface.strip():
        return 0.0
    hits = sum(1 for term in plan.topicTerms if term.lower() in surface)
    return hits / max(len(plan.topicTerms), 1)


def _phaseScore(row: Mapping[str, Any], plan: SemanticConstraintPlan, *, latestDate: int | None = None) -> float:
    if rowSourceClass(row) != "allFilings" or not _hasNarrowEntityFacet(plan):
        return 0.0
    surface = _reportSurface(row)
    if not surface:
        return 0.0
    asksDecision = _queryAsksDecision(plan)
    hasDecision = any(term in surface for term in _PHASE_DECISION_TERMS)
    hasResult = any(term in surface for term in _PHASE_RESULT_TERMS)
    if _queryAsksMajorShareholderChange(plan):
        return _EXPLICIT_PHASE_SCORE if any(term in surface for term in _PHASE_MAJOR_SHAREHOLDER_REPORT_TERMS) else 0.0
    if _queryMentionsShareholderMeeting(plan):
        if _queryAsksMeetingResolution(plan):
            return _EXPLICIT_PHASE_SCORE if any(term in surface for term in _PHASE_MEETING_RESOLUTION_TERMS) else 0.0
        return 1.0 if any(term in surface for term in _PHASE_MEETING_NOTICE_TERMS) else 0.0
    if asksDecision:
        return _EXPLICIT_PHASE_SCORE if hasDecision else 0.0
    if latestDate is not None and hasResult and _dateOrdinal(row.get("rcept_dt") or row.get("date")) < latestDate:
        return 0.0
    return 1.0 if hasResult else 0.0


def _queryAsksDecision(plan: SemanticConstraintPlan) -> bool:
    terms = plan.topicTerms + plan.facets.reportTerms
    return any("결정" in str(term) for term in terms)


def _queryMentionsShareholderMeeting(plan: SemanticConstraintPlan) -> bool:
    terms = plan.topicTerms + plan.facets.reportTerms
    return any("주주총회" in str(term) for term in terms)


def _queryAsksMeetingResolution(plan: SemanticConstraintPlan) -> bool:
    terms = plan.topicTerms + plan.facets.reportTerms
    return any("소집결의" in str(term) or str(term) == "결의" for term in terms)


def _queryAsksMajorShareholderChange(plan: SemanticConstraintPlan) -> bool:
    terms = plan.topicTerms + plan.facets.reportTerms
    return any(any(needle in str(term) for needle in _PHASE_MAJOR_SHAREHOLDER_QUERY_TERMS) for term in terms)


def _reportSurface(row: Mapping[str, Any]) -> str:
    return " ".join(
        str(row.get(key) or "")
        for key in (
            "report_nm",
            "reportName",
            "title",
            "section_title",
            "sectionTitle",
        )
    )


def _markConstrainedSiblings(rows: list[dict], plan: SemanticConstraintPlan) -> list[dict]:
    if not _shouldDedupeSiblings(plan):
        return rows
    seenPrimary = False
    out: list[dict] = []
    for row in rows:
        item = dict(row)
        if _isSiblingCandidate(item, plan):
            if seenPrimary:
                reason = str(item.get("constraintViolationReason") or "").strip()
                item["constraintViolationReason"] = (
                    f"{reason},constraintSiblingDedup" if reason else "constraintSiblingDedup"
                )
                item["semanticConstraintScore"] = _float(item.get("semanticConstraintScore")) - 1000.0
                item["score"] = _float(item.get("score")) - 1000.0
            else:
                seenPrimary = True
        out.append(item)
    out.sort(key=lambda row: _float(row.get("score")), reverse=True)
    return out


def _shouldDedupeSiblings(plan: SemanticConstraintPlan) -> bool:
    facets = plan.facets
    return bool(plan.sourceClasses and facets.stockCode and facets.years and (plan.topicTerms or facets.reportTerms))


def _isSiblingCandidate(row: Mapping[str, Any], plan: SemanticConstraintPlan) -> bool:
    if semanticConstraintViolations(row, plan):
        return False
    if plan.topicTerms and _topicCoverage(row, plan) <= 0.0:
        return False
    return True


def _requiresTopicConstraint(plan: SemanticConstraintPlan) -> bool:
    return bool(plan.topicTerms and plan.sourceClasses and _hasNarrowEntityFacet(plan))


def _constraintCount(plan: SemanticConstraintPlan) -> int:
    facets = plan.facets
    return sum(
        (
            int(bool(plan.sourceClasses)),
            int(bool(facets.receiptNumbers)),
            int(bool(facets.dates)),
            int(bool(facets.years)),
            int(bool(facets.reportTerms)),
            int(bool(facets.literalTerms)),
            int(bool(facets.stockCode)),
            int(bool(facets.corpCode)),
            int(bool(facets.companyName and not facets.stockCode and not facets.corpCode)),
        )
    )


def _hasNarrowEntityFacet(plan: SemanticConstraintPlan) -> bool:
    facets = plan.facets
    return bool(facets.receiptNumbers or facets.stockCode or facets.corpCode or facets.companyName)


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
