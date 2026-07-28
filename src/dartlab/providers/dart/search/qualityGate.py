"""Query-log gold and miss-ledger gates for product search."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from dartlab.providers.dart.search.coerce import _ratio

REAL_GOLD_ORIGINS = {"real", "operator", "operatorReal", "userLog", "production"}
REVIEWED_STATUSES = {"reviewed", "approved", "accepted", "gold"}
DEFAULT_REQUIRED_TARGETS = ("filing", "news", "noAnswer")
MAXIMUM_THRESHOLD_METRICS = {
    "noAnswerFalseAcceptRate",
    "forbiddenTop1Rate",
    "forbiddenTop3Rate",
    "forbiddenTop10Rate",
    "sourceIntentLeakRate",
    "constraintViolationRate",
}


def loadQueryGold(path: str | Path) -> list[dict[str, Any]]:
    """Load query-log gold rows from JSON or JSONL.

    Args:
        path: Gold file path. JSON arrays, ``{"rows": [...]}``, and JSONL are supported.

    Returns:
        list[dict[str, Any]]: Gold rows in file order.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If the file shape is unsupported.

    Example:
        >>> callable(loadQueryGold)
        True
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text) if text.strip() else []
    if isinstance(data, list):
        return [dict(row) for row in data]
    if isinstance(data, dict):
        rows = data.get("rows") or data.get("gold") or data.get("queryLogGold")
        if isinstance(rows, list):
            return [dict(row) for row in rows]
    raise ValueError(f"unsupported query gold shape: {p}")


def evaluateQueryGoldRows(
    goldRows: Iterable[Mapping[str, Any]],
    resultsByQuery: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    minRows: int = 100,
    requiredTargets: Iterable[str] = DEFAULT_REQUIRED_TARGETS,
    requireRealReviewed: bool = True,
    thresholds: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Evaluate product search results against query-log gold.

    Args:
        goldRows: Iterable of query gold rows.
        resultsByQuery: Mapping from query text to ranked result rows.
        minRows: Minimum real reviewed rows required for release eligibility.
        requiredTargets: Target kinds that must be represented.
        requireRealReviewed: True blocks release if rows are proxy/generated/unreviewed.
        thresholds: Optional metric thresholds overriding defaults.

    Returns:
        dict[str, Any]: Metrics, blockers, and release eligibility.

    Raises:
        None.

    Example:
        >>> evaluateQueryGoldRows([], {}, minRows=0)["totalRows"]
        0
    """
    rows = [dict(row) for row in goldRows]
    targetCounts: dict[str, int] = {}
    originCounts: dict[str, int] = {}
    reviewCounts: dict[str, int] = {}
    docHit10Hits = 0
    docHit10Rows = 0
    exactDocHit10Hits = 0
    top3Hits = 0
    top3Rows = 0
    exactTop3Hits = 0
    readyRows = 0
    newsPrecisionSum = 0.0
    newsPrecisionRows = 0
    noAnswerRows = 0
    noAnswerFalseAccepts = 0
    hardNegativeRows = 0
    hardNegativeExactDocHit10Hits = 0
    hardNegativeWins = 0
    forbiddenTop1Violations = 0
    forbiddenTop3Violations = 0
    forbiddenTop10Violations = 0
    sourceIntentLeakRows = 0
    sourceIntentLeaks = 0

    rowEvaluations: list[dict[str, Any]] = []
    for gold in rows:
        query = str(gold.get("query") or "")
        target = normalizeTargetKind(gold)
        targetCounts[target] = targetCounts.get(target, 0) + 1
        origin = str(gold.get("goldOrigin") or "")
        review = str(gold.get("reviewStatus") or "")
        originCounts[origin] = originCounts.get(origin, 0) + 1
        reviewCounts[review] = reviewCounts.get(review, 0) + 1
        results = [dict(row) for row in _resultsForGold(gold, resultsByQuery)]
        hasHardNegative = target != "noAnswer" and _hasForbiddenGold(gold)
        forbiddenTop1 = _anyForbiddenMatch(gold, results[:1])
        forbiddenTop3 = _anyForbiddenMatch(gold, results[:3])
        forbiddenTop10 = _anyForbiddenMatch(gold, results[:10])
        sourceIntentLeak = _sourceIntentLeak(gold, results[:10])
        if target == "noAnswer":
            noAnswerRows += 1
            falseAccept = any(_isAnswerable(row) for row in results[:10])
            if falseAccept:
                noAnswerFalseAccepts += 1
            else:
                readyRows += 1
            rowEvaluations.append(
                {
                    "query": query,
                    "target": target,
                    "ready": not falseAccept,
                    "falseAccept": falseAccept,
                    "docHit10": None,
                    "memoryCitationTop3Exact": None,
                    "newsSourcePrecision10": None,
                    "forbiddenTop1": None,
                    "forbiddenTop3": None,
                    "forbiddenTop10": None,
                    "sourceIntentLeak": None,
                    "constraintViolation": None,
                    "hardNegativeWin": None,
                }
            )
            continue

        docHit10Rows += 1
        top3Rows += 1
        exactHit10 = _anyExpectedMatch(gold, results[:10])
        exactHit3 = _anyExpectedMatch(gold, results[:3])
        hit10 = exactHit10 or _anySemanticMatch(gold, results[:10])
        hit3 = exactHit3 or _anySemanticMatch(gold, results[:3])
        if hit10:
            docHit10Hits += 1
            readyRows += 1
        if exactHit10:
            exactDocHit10Hits += 1
        if hit3:
            top3Hits += 1
        if exactHit3:
            exactTop3Hits += 1
        hardNegativeWin = None
        if hasHardNegative:
            hardNegativeRows += 1
            if exactHit10:
                hardNegativeExactDocHit10Hits += 1
            if forbiddenTop1:
                forbiddenTop1Violations += 1
            if forbiddenTop3:
                forbiddenTop3Violations += 1
            if forbiddenTop10:
                forbiddenTop10Violations += 1
            expectedRank = _expectedRank(gold, results[:10])
            forbiddenRanks = _forbiddenRanks(gold, results[:10])
            hardNegativeWin = bool(expectedRank is not None and all(expectedRank < rank for rank in forbiddenRanks))
            if hardNegativeWin:
                hardNegativeWins += 1
        if _forbiddenSourceFamilies(gold):
            sourceIntentLeakRows += 1
            if sourceIntentLeak:
                sourceIntentLeaks += 1
        precision = None
        if target == "news":
            newsPrecisionRows += 1
            precision = _sourcePrecision(results[:10], expectedSource="news")
            newsPrecisionSum += precision
        rowEvaluations.append(
            {
                "query": query,
                "target": target,
                "ready": hit10,
                "falseAccept": None,
                "docHit10": hit10,
                "exactDocHit10": exactHit10,
                "memoryCitationTop3Exact": hit3,
                "exactMemoryCitationTop3": exactHit3,
                "newsSourcePrecision10": precision,
                "matchMode": "exact" if exactHit10 else ("semantic" if hit10 else "miss"),
                "forbiddenTop1": forbiddenTop1 if hasHardNegative else None,
                "forbiddenTop3": forbiddenTop3 if hasHardNegative else None,
                "forbiddenTop10": forbiddenTop10 if hasHardNegative else None,
                "sourceIntentLeak": sourceIntentLeak if _forbiddenSourceFamilies(gold) else None,
                "constraintViolation": forbiddenTop1 if hasHardNegative else None,
                "hardNegativeWin": hardNegativeWin,
            }
        )

    metricThresholds = _thresholds(thresholds)
    totalRows = len(rows)
    realReviewedRows = sum(1 for row in rows if _isRealReviewed(row))
    metrics = {
        "overallReadyRate": _ratio(readyRows, totalRows),
        "docHit10": _ratio(docHit10Hits, docHit10Rows),
        "exactDocHit10": _ratio(exactDocHit10Hits, docHit10Rows),
        "memoryCitationTop3Exact": _ratio(top3Hits, top3Rows),
        "exactMemoryCitationTop3": _ratio(exactTop3Hits, top3Rows),
        "newsSourcePrecision10": _ratio(newsPrecisionSum, newsPrecisionRows),
        "noAnswerFalseAcceptRate": _ratio(noAnswerFalseAccepts, noAnswerRows),
        "noAnswerNegativeRejectRate": _ratio(noAnswerRows - noAnswerFalseAccepts, noAnswerRows),
        "hardNegativeRows": float(hardNegativeRows),
        "hardNegativeExactDocHit10": _ratio(hardNegativeExactDocHit10Hits, hardNegativeRows),
        "hardNegativeWinRate": _ratio(hardNegativeWins, hardNegativeRows),
        "forbiddenTop1Rate": _ratio(forbiddenTop1Violations, hardNegativeRows),
        "forbiddenTop3Rate": _ratio(forbiddenTop3Violations, hardNegativeRows),
        "forbiddenTop10Rate": _ratio(forbiddenTop10Violations, hardNegativeRows),
        "sourceIntentLeakRate": _ratio(sourceIntentLeaks, sourceIntentLeakRows),
        "constraintViolationRate": _ratio(forbiddenTop1Violations, hardNegativeRows),
    }
    blockers = _releaseBlockers(
        rows=rows,
        targetCounts=targetCounts,
        hardNegativeRows=hardNegativeRows,
        realReviewedRows=realReviewedRows,
        minRows=minRows,
        requiredTargets=requiredTargets,
        requireRealReviewed=requireRealReviewed,
        metrics=metrics,
        thresholds=metricThresholds,
    )
    return {
        "totalRows": totalRows,
        "realReviewedRows": realReviewedRows,
        "coverageByKind": targetCounts,
        "goldOriginCounts": originCounts,
        "reviewStatusCounts": reviewCounts,
        "metrics": metrics,
        "metricsByKind": _metricsByKind(rowEvaluations),
        "thresholds": metricThresholds,
        "releaseEligible": not blockers,
        "blockers": blockers,
        "rows": rowEvaluations,
    }


def buildMissLedgerRows(
    goldRows: Iterable[Mapping[str, Any]],
    resultsByQuery: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    """Build a policy-oriented miss ledger from query-log gold results.

    Args:
        goldRows: Iterable of query gold rows.
        resultsByQuery: Mapping from query text to ranked result rows.

    Returns:
        list[dict[str, Any]]: Rows requiring review or product-policy work.

    Raises:
        None.

    Example:
        >>> buildMissLedgerRows([], {})
        []
    """
    misses: list[dict[str, Any]] = []
    for gold in goldRows:
        row = dict(gold)
        query = str(row.get("query") or "")
        target = normalizeTargetKind(row)
        results = [dict(result) for result in _resultsForGold(row, resultsByQuery)]
        topRefs = [_sourceRef(result) for result in results[:10] if _sourceRef(result)]
        failureTypes = _rowFailureTypes(row, results)
        if not _isRealReviewed(row):
            failureTypes.append("goldReviewRequired")
        for failureType in _dedupe(failureTypes):
            misses.append(
                {
                    "query": query,
                    "targetKind": target,
                    "expectedSourceRef": _expectedSourceRefText(row),
                    "expectedRceptNo": str(row.get("rceptNo") or row.get("rcept_no") or ""),
                    "topSourceRefs": topRefs,
                    "topSources": [str(result.get("source") or "") for result in results[:10]],
                    "failureType": failureType,
                    "sourceDataAsOf": str((results[0].get("dataAsOf") if results else "") or ""),
                    "decision": "blockRelease" if failureType != "goldReviewRequired" else "reviewGold",
                    "policyCandidate": _policyCandidate(failureType),
                    "reviewStatus": str(row.get("reviewStatus") or ""),
                    "goldOrigin": str(row.get("goldOrigin") or ""),
                }
            )
    return misses


def writeMissLedger(path: str | Path, rows: Iterable[Mapping[str, Any]]) -> None:
    """Write a JSONL miss ledger.

    Args:
        path: Output path.
        rows: Miss ledger rows.

    Returns:
        None.

    Raises:
        OSError: If the file cannot be written.

    Example:
        >>> callable(writeMissLedger)
        True
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(dict(row), ensure_ascii=False, sort_keys=True) for row in rows]
    p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def normalizeTargetKind(row: Mapping[str, Any]) -> str:
    """Normalize a query-log target kind.

    Args:
        row: Query gold row.

    Returns:
        str: Normalized target kind.

    Raises:
        None.

    Example:
        >>> normalizeTargetKind({"target": "allFilings"})
        'filing'
    """
    target = str(row.get("targetKind") or row.get("target") or row.get("kind") or "").strip()
    aliases = {
        "allFilings": "filing",
        "dart": "filing",
        "dartPanel": "filing",
        "panel": "filing",
        "edgarPanel": "edgar",
        "edgar-panel": "edgar",
        "negative": "noAnswer",
        "no-answer": "noAnswer",
        "noanswer": "noAnswer",
    }
    return aliases.get(target, target or "filing")


def _releaseBlockers(
    *,
    rows: Sequence[Mapping[str, Any]],
    targetCounts: Mapping[str, int],
    hardNegativeRows: int,
    realReviewedRows: int,
    minRows: int,
    requiredTargets: Iterable[str],
    requireRealReviewed: bool,
    metrics: Mapping[str, float],
    thresholds: Mapping[str, float],
) -> list[str]:
    blockers: list[str] = []
    if len(rows) < minRows:
        blockers.append(f"minRows:{len(rows)}/{minRows}")
    if requireRealReviewed and realReviewedRows < minRows:
        blockers.append(f"realReviewedRows:{realReviewedRows}/{minRows}")
    for target in requiredTargets:
        normalized = normalizeTargetKind({"target": target})
        if targetCounts.get(normalized, 0) == 0:
            blockers.append(f"missingTarget:{normalized}")
    if requireRealReviewed:
        proxyCount = sum(1 for row in rows if not _isRealOrigin(row))
        unreviewedCount = sum(1 for row in rows if not _isReviewed(row))
        if proxyCount:
            blockers.append(f"proxyGoldRows:{proxyCount}")
        if unreviewedCount:
            blockers.append(f"unreviewedGoldRows:{unreviewedCount}")
    for metric, minimum in thresholds.items():
        if _skipMetricThreshold(metric, targetCounts, hardNegativeRows):
            continue
        value = metrics.get(metric, 0.0)
        if metric in MAXIMUM_THRESHOLD_METRICS:
            if value > minimum:
                blockers.append(f"metric:{metric}:{value:.4f}>{minimum:.4f}")
        elif value < minimum:
            blockers.append(f"metric:{metric}:{value:.4f}<{minimum:.4f}")
    return blockers


def _skipMetricThreshold(metric: str, targetCounts: Mapping[str, int], hardNegativeRows: int) -> bool:
    docTargets = sum(count for target, count in targetCounts.items() if target != "noAnswer")
    if metric in {"docHit10", "memoryCitationTop3Exact"}:
        return docTargets <= 0
    if metric == "newsSourcePrecision10":
        return int(targetCounts.get("news") or 0) <= 0
    if metric == "noAnswerFalseAcceptRate":
        return int(targetCounts.get("noAnswer") or 0) <= 0
    if metric in {
        "hardNegativeExactDocHit10",
        "hardNegativeWinRate",
        "forbiddenTop1Rate",
        "forbiddenTop3Rate",
        "forbiddenTop10Rate",
        "sourceIntentLeakRate",
        "constraintViolationRate",
    }:
        return hardNegativeRows <= 0
    return False


def _thresholds(overrides: Mapping[str, float] | None) -> dict[str, float]:
    base = {
        "overallReadyRate": 0.9,
        "docHit10": 0.9,
        "memoryCitationTop3Exact": 0.9,
        "newsSourcePrecision10": 0.9,
        "noAnswerFalseAcceptRate": 0.1,
        "hardNegativeExactDocHit10": 0.95,
        "hardNegativeWinRate": 0.95,
        "forbiddenTop3Rate": 0.0,
        "forbiddenTop10Rate": 0.02,
        "sourceIntentLeakRate": 0.0,
        "constraintViolationRate": 0.05,
    }
    if overrides:
        base.update({str(k): float(v) for k, v in overrides.items()})
    return base


def _rowFailureTypes(gold: Mapping[str, Any], results: Sequence[Mapping[str, Any]]) -> list[str]:
    target = normalizeTargetKind(gold)
    if target == "noAnswer":
        return ["falseAccept"] if any(_isAnswerable(row) for row in results[:10]) else []
    failures = []
    if not results:
        failures.append("missingResults")
    if not (_anyExpectedMatch(gold, results[:10]) or _anySemanticMatch(gold, results[:10])):
        failures.append("docMiss10")
        failures.extend(_topResultFailureTypes(results[:10]))
    elif not (_anyExpectedMatch(gold, results[:3]) or _anySemanticMatch(gold, results[:3])):
        failures.append("citationMissTop3")
        failures.extend(_topResultFailureTypes(results[:3]))
    if target == "news" and _sourcePrecision(results[:10], expectedSource="news") < 1.0:
        failures.append("newsSourcePrecision10")
        failures.append("sourceIntentMiss")
    if _anyForbiddenMatch(gold, results[:3]):
        failures.append("hardNegativeForbiddenTop3")
    elif _anyForbiddenMatch(gold, results[:10]):
        failures.append("hardNegativeForbiddenTop10")
    if _sourceIntentLeak(gold, results[:10]):
        failures.append("sourceIntentLeak")
    return failures


def _resultsForGold(
    gold: Mapping[str, Any], resultsByQuery: Mapping[str, Sequence[Mapping[str, Any]]]
) -> Sequence[Mapping[str, Any]]:
    for key in _goldResultKeys(gold):
        if key in resultsByQuery:
            return resultsByQuery.get(key) or []
    return []


def _goldResultKeys(gold: Mapping[str, Any]) -> list[str]:
    keys: list[str] = []
    for field in ("query", "queryId", "id"):
        key = str(gold.get(field) or "").strip()
        if key and key not in keys:
            keys.append(key)
    return keys


def _anyExpectedMatch(gold: Mapping[str, Any], results: Sequence[Mapping[str, Any]]) -> bool:
    refs = _expectedSourceRefs(gold)
    rceptNo = str(gold.get("rceptNo") or gold.get("rcept_no") or "").strip()
    title = str(gold.get("title") or "").strip()
    if not refs and not rceptNo and not title:
        return False
    for row in results:
        if not _isAnswerable(row):
            continue
        ref = _sourceRef(row)
        if refs and ref in refs:
            return True
        if rceptNo and (str(row.get("rcept_no") or "") == rceptNo or rceptNo in ref):
            return True
        if title and str(row.get("title") or row.get("section_title") or "") == title:
            return True
    return False


def _anySemanticFilingEventMatch(gold: Mapping[str, Any], results: Sequence[Mapping[str, Any]]) -> bool:
    if normalizeTargetKind(gold) != "filing" or not _isEventTitleQuery(str(gold.get("query") or "")):
        return False
    return any(_semanticFilingEventMatch(gold, row) for row in results)


def _anySemanticMatch(gold: Mapping[str, Any], results: Sequence[Mapping[str, Any]]) -> bool:
    target = normalizeTargetKind(gold)
    if target == "news":
        return _anySemanticNewsMatch(gold, results)
    return _anySemanticFilingEventMatch(gold, results)


def _semanticFilingEventMatch(gold: Mapping[str, Any], row: Mapping[str, Any]) -> bool:
    if not _isAnswerable(row):
        return False
    from dartlab.providers.dart.search.sourceIntent import sourceFamily

    if sourceFamily(str(row.get("source") or "")) != "filing":
        return False
    query = str(gold.get("query") or "")
    evidence = " ".join(str(row.get(key) or "") for key in ("report_nm", "section_title", "title", "snippet", "text"))
    return _queryEvidenceTokenCoverage(query, evidence) >= 0.5


def _anySemanticNewsMatch(gold: Mapping[str, Any], results: Sequence[Mapping[str, Any]]) -> bool:
    if normalizeTargetKind(gold) != "news":
        return False
    from dartlab.providers.dart.search.sourceIntent import sourceFamily

    query = str(gold.get("query") or "")
    for row in results:
        if not _isAnswerable(row) or sourceFamily(str(row.get("source") or "")) != "news":
            continue
        evidence = " ".join(
            str(row.get(key) or "") for key in ("report_nm", "section_title", "title", "snippet", "text")
        )
        if _queryEvidenceTokenCoverage(query, evidence) >= 0.6:
            return True
    return False


def _isEventTitleQuery(query: str) -> bool:
    text = " ".join(str(query or "").strip().lower().split())
    if not text:
        return False
    bodyTerms = (
        "본문",
        "주석",
        "사업의 내용",
        "위험",
        "리스크",
        "risk",
        "md&a",
        "유동성",
        "손상",
        "정책",
        "비중",
        "만기",
    )
    if any(term in text for term in bodyTerms) and "제출" not in text:
        return False
    eventTerms = (
        "공시",
        "원문",
        "결정",
        "변경",
        "제출",
        "체결",
        "발행",
        "취득",
        "처분",
        "소집",
        "결과",
        "합병",
        "분할",
        "양수",
        "양도",
        "소송",
        "횡령",
        "배임",
        "영업정지",
        "배당",
    )
    return any(term in text for term in eventTerms)


def _queryEvidenceTokenCoverage(query: str, evidence: str) -> float:
    from dartlab.providers.dart.search.curatedSyn import expandQuery
    from dartlab.providers.dart.search.fieldIndex import tokenizeContent

    stop = {"공시", "원문", "본문", "뉴스", "기사"}
    queryTokens = [token for token in dict.fromkeys(tokenizeContent(query)) if token not in stop]
    if not queryTokens:
        return 0.0
    evidenceTokens = set(tokenizeContent(evidence))
    coverage = _tokenCoverage(queryTokens, evidenceTokens)
    for term in expandQuery(query):
        expansionTokens = [token for token in dict.fromkeys(tokenizeContent(term)) if token not in stop]
        coverage = max(coverage, _tokenCoverage(expansionTokens, evidenceTokens))
    if len(queryTokens) <= 2 and coverage < 1.0:
        return 0.0
    return coverage


def _tokenCoverage(queryTokens: Sequence[str], evidenceTokens: set[str]) -> float:
    if not queryTokens:
        return 0.0
    hits = sum(1 for token in queryTokens if token in evidenceTokens)
    return hits / len(queryTokens)


def _expectedSourceRefs(gold: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    value = gold.get("expectedSourceRefs") or gold.get("expectedSourceRef")
    if isinstance(value, str):
        refs.add(value)
    elif isinstance(value, Sequence):
        refs.update(str(item) for item in value if item)
    sourceRef = str(gold.get("sourceRef") or "").strip()
    if sourceRef:
        refs.add(sourceRef)
    return refs


def _forbiddenSourceRefs(gold: Mapping[str, Any]) -> set[str]:
    return _stringSet(gold.get("forbiddenSourceRefs") or gold.get("forbiddenSourceRef"))


def _forbiddenSourceFamilies(gold: Mapping[str, Any]) -> set[str]:
    return _stringSet(gold.get("forbiddenSourceFamilies") or gold.get("forbiddenSourceFamily"))


def _hasForbiddenGold(gold: Mapping[str, Any]) -> bool:
    return bool(_forbiddenSourceRefs(gold) or _forbiddenSourceFamilies(gold))


def _anyForbiddenMatch(gold: Mapping[str, Any], results: Sequence[Mapping[str, Any]]) -> bool:
    return bool(_forbiddenRanks(gold, results))


def _forbiddenRanks(gold: Mapping[str, Any], results: Sequence[Mapping[str, Any]]) -> list[int]:
    refs = _forbiddenSourceRefs(gold)
    families = _forbiddenSourceFamilies(gold)
    if not refs and not families:
        return []
    out: list[int] = []
    for index, row in enumerate(results, start=1):
        if not _isAnswerable(row):
            continue
        ref = _sourceRef(row)
        if refs and ref in refs:
            out.append(index)
            continue
        if families and _rowSourceFamily(row) in families:
            out.append(index)
    return out


def _expectedRank(gold: Mapping[str, Any], results: Sequence[Mapping[str, Any]]) -> int | None:
    refs = _expectedSourceRefs(gold)
    if not refs:
        return None
    for index, row in enumerate(results, start=1):
        if _isAnswerable(row) and _sourceRef(row) in refs:
            return index
    return None


def _sourceIntentLeak(gold: Mapping[str, Any], results: Sequence[Mapping[str, Any]]) -> bool:
    families = _forbiddenSourceFamilies(gold)
    if not families:
        return False
    return any(_isAnswerable(row) and _rowSourceFamily(row) in families for row in results)


def _expectedSourceRefText(gold: Mapping[str, Any]) -> str:
    refs = sorted(_expectedSourceRefs(gold))
    return ",".join(refs)


def _sourcePrecision(results: Sequence[Mapping[str, Any]], *, expectedSource: str) -> float:
    if not results:
        return 0.0
    matched = sum(1 for row in results if str(row.get("source") or "") == expectedSource)
    return matched / len(results)


def _sourceRef(row: Mapping[str, Any]) -> str:
    return str(row.get("sourceRef") or row.get("rcept_no") or "")


def _rowSourceFamily(row: Mapping[str, Any]) -> str:
    from dartlab.providers.dart.search.sourceIntent import sourceFamily

    source = row.get("source") or row.get("sourceKind") or ""
    return sourceFamily(str(source))


def _stringSet(value: Any) -> set[str]:
    if isinstance(value, str):
        return {part.strip() for part in value.split(",") if part.strip()}
    if isinstance(value, Sequence):
        return {str(item).strip() for item in value if str(item).strip()}
    return set()


def _isAnswerable(row: Mapping[str, Any]) -> bool:
    value = row.get("answerable")
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return True
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "n"}
    return bool(value)


def _isRealReviewed(row: Mapping[str, Any]) -> bool:
    return _isRealOrigin(row) and _isReviewed(row)


def _isRealOrigin(row: Mapping[str, Any]) -> bool:
    return str(row.get("goldOrigin") or "") in REAL_GOLD_ORIGINS


def _isReviewed(row: Mapping[str, Any]) -> bool:
    return str(row.get("reviewStatus") or "") in REVIEWED_STATUSES


def _policyCandidate(failureType: str) -> str:
    return {
        "docMiss10": "rankingOrFacetPolicy",
        "citationMissTop3": "rerankWindowOrCitationPolicy",
        "falseAccept": "negativeAnswerabilityPolicy",
        "missingResults": "sourceFreshnessOrCoveragePolicy",
        "newsSourcePrecision10": "sourceIntentPolicy",
        "sourceIntentMiss": "sourceIntentPolicy",
        "entityFacetMiss": "facetPlannerPolicy",
        "dateFacetMiss": "facetPlannerPolicy",
        "reportFacetMiss": "facetPlannerPolicy",
        "bodyEvidenceMiss": "evidencePackPolicy",
        "staleSource": "sourceFreshnessOrCoveragePolicy",
        "goldReviewRequired": "queryGoldReview",
        "hardNegativeForbiddenTop3": "constraintRankingPolicy",
        "hardNegativeForbiddenTop10": "constraintRankingPolicy",
        "sourceIntentLeak": "sourceIntentPolicy",
    }.get(failureType, "policyReview")


def _metricsByKind(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        target = str(row.get("target") or "")
        grouped.setdefault(target, []).append(row)
    out: dict[str, dict[str, Any]] = {}
    for target, items in grouped.items():
        ready = sum(1 for item in items if item.get("ready") is True)
        docRows = [item for item in items if item.get("docHit10") is not None]
        top3Rows = [item for item in items if item.get("memoryCitationTop3Exact") is not None]
        falseAcceptRows = [item for item in items if item.get("falseAccept") is not None]
        newsRows = [item for item in items if item.get("newsSourcePrecision10") is not None]
        out[target] = {
            "rows": len(items),
            "readyRate": _ratio(ready, len(items)),
            "docHit10": _ratio(sum(1 for item in docRows if item.get("docHit10") is True), len(docRows)),
            "memoryCitationTop3Exact": _ratio(
                sum(1 for item in top3Rows if item.get("memoryCitationTop3Exact") is True),
                len(top3Rows),
            ),
            "falseAcceptRate": _ratio(
                sum(1 for item in falseAcceptRows if item.get("falseAccept") is True),
                len(falseAcceptRows),
            ),
            "newsSourcePrecision10": _ratio(
                sum(float(item.get("newsSourcePrecision10") or 0.0) for item in newsRows),
                len(newsRows),
            ),
        }
    return out


def _topResultFailureTypes(results: Sequence[Mapping[str, Any]]) -> list[str]:
    out: list[str] = []
    for row in results:
        reason = str(row.get("notAnswerableReason") or "")
        if not reason:
            continue
        if "source" in reason.lower():
            out.append("sourceIntentMiss")
        if "facetMismatch:company" in reason or "facetMismatch:corp" in reason:
            out.append("entityFacetMiss")
        if "facetMismatch:date" in reason:
            out.append("dateFacetMiss")
        if "facetMismatch:report" in reason or "facetMismatch:receipt" in reason:
            out.append("reportFacetMiss")
        if reason in {"missingSourceRef", "missingSnippet", "missingDataAsOf"}:
            out.append("bodyEvidenceMiss")
        if reason == "staleSource":
            out.append("staleSource")
    return out


def _dedupe(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value not in out:
            out.append(value)
    return out
