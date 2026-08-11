"""Source and no-answer canary pack evaluation for product search."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from dartlab.providers.dart.search.coerce import _asBool, _int, _ratio


def loadCanaryPack(path: str | Path) -> list[dict[str, Any]]:
    """Load a search canary pack from JSON or JSONL.

    Args:
        path: Canary pack file. JSON arrays, ``{"rows": [...]}``, and JSONL are supported.

    Returns:
        list[dict[str, Any]]: Canary rows in file order.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If the file shape is unsupported.

    Example:
        >>> callable(loadCanaryPack)
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
        rows = data.get("rows") or data.get("canaries") or data.get("canaryPack")
        if isinstance(rows, list):
            return [dict(row) for row in rows]
    raise ValueError(f"unsupported canary pack shape: {p}")


def evaluateCanaryPackRows(
    canaryRows: Iterable[Mapping[str, Any]],
    resultsByQuery: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    defaultTopK: int = 10,
    minPassRate: float = 1.0,
) -> dict[str, Any]:
    """Evaluate canary rows against ranked product search results.

    Args:
        canaryRows: Canary definitions.
        resultsByQuery: Mapping from query to ranked result rows.
        defaultTopK: Default result window when a row omits ``topK``.
        minPassRate: Minimum pass rate required for a valid canary run.

    Returns:
        dict[str, Any]: Canary metrics, row decisions, and failures.

    Raises:
        None.

    Example:
        >>> evaluateCanaryPackRows([], {})["valid"]
        True
    """
    rows = [dict(row) for row in canaryRows]
    decisions: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    sourceChecked = 0
    sourceHits = 0
    refChecked = 0
    refHits = 0
    noAnswerRows = 0
    falseAccepts = 0

    for row in rows:
        query = str(row.get("query") or row.get("q") or "")
        targetKind = _targetKind(row)
        topK = _int(row.get("topK"), defaultTopK)
        results = [dict(result) for result in resultsByQuery.get(query, [])[:topK]]
        expectedRefs = _expectedSourceRefs(row)
        expectedSource = str(row.get("expectedSource") or row.get("source") or "").strip()
        expectAnswerable = _expectedAnswerable(row)
        requireAnswerable = _asBool(row.get("requireAnswerable"), default=expectAnswerable)
        answerable = [result for result in results if _isAnswerable(result)]
        matchedResults = answerable if requireAnswerable else results
        rowFailures: list[str] = []
        injectionMode = str(row.get("_injectionMode") or "")
        injectionError = str(row.get("_injectionError") or "")

        if _asBool(row.get("_requireDeterministic"), default=False) and injectionMode != "deterministic":
            rowFailures.append("resolutionInjectionFailed")

        if not expectAnswerable:
            noAnswerRows += 1
            if answerable:
                rowFailures.append("falseAccept")
                falseAccepts += 1
        else:
            # 무결성(integrity) canary 면 호출자가 인덱스 아티팩트를 직독해 결정론 신호
            # (_sourceResolved·_refResolved)를 싣는다. bigram 토크나이저에선 보일러플레이트 doc 이
            # 자기 본문 BM25 로 top-K self-retrieval 이 불가 → answerable/source/ref 를 랭킹으로 재면
            # flaky. 신호가 있으면 그것을 신뢰(랭킹 무관), 없으면(gold/qualityGate 경로) BM25 폴백.
            sourceDet = row.get("_sourceResolved")
            refDet = row.get("_refResolved")
            hasDeterministic = ("_sourceResolved" in row) or ("_refResolved" in row)
            deterministicHit = bool(sourceDet) or bool(refDet)
            if requireAnswerable and not answerable and not (hasDeterministic and deterministicHit):
                rowFailures.append("missingAnswerable")
            if expectedSource:
                sourceChecked += 1
                if "_sourceResolved" in row:
                    sourceOk = bool(sourceDet)
                else:
                    sourceOk = any(str(result.get("source") or "") == expectedSource for result in matchedResults)
                if sourceOk:
                    sourceHits += 1
                else:
                    rowFailures.append("sourceMiss")
            if expectedRefs:
                refChecked += 1
                if "_refResolved" in row:
                    refOk = bool(refDet)
                else:
                    refOk = any(_sourceRef(result) in expectedRefs for result in matchedResults)
                if refOk:
                    refHits += 1
                else:
                    rowFailures.append("sourceRefMiss")

        passed = not rowFailures
        decision = {
            "query": query,
            "targetKind": targetKind,
            "expectedSource": expectedSource,
            "expectedSourceRefs": sorted(expectedRefs),
            "expectedAnswerable": expectAnswerable,
            "requireAnswerable": requireAnswerable,
            "passed": passed,
            "failures": rowFailures,
            "topSourceRefs": [_sourceRef(result) for result in results if _sourceRef(result)],
            "topSources": [str(result.get("source") or "") for result in results],
        }
        if injectionMode:
            decision["injectionMode"] = injectionMode
        if injectionError:
            decision["injectionError"] = injectionError
        if "_sourceResolved" in row:
            decision["_sourceResolved"] = bool(row.get("_sourceResolved"))
        if "_refResolved" in row:
            decision["_refResolved"] = bool(row.get("_refResolved"))
        decisions.append(decision)
        for failure in rowFailures:
            failures.append(
                {
                    "query": query,
                    "targetKind": targetKind,
                    "failureType": failure,
                    "expectedSource": expectedSource,
                    "expectedSourceRef": ",".join(sorted(expectedRefs)),
                    "topSourceRefs": decision["topSourceRefs"],
                    "policyCandidate": _policyCandidate(failure),
                    "injectionMode": injectionMode,
                    "injectionError": injectionError,
                }
            )

    passedRows = sum(1 for row in decisions if row["passed"])
    passRate = _ratio(passedRows, len(decisions))
    metrics = {
        "passRate": passRate,
        "sourceHitRate": _ratio(sourceHits, sourceChecked),
        "sourceRefHitRate": _ratio(refHits, refChecked),
        "noAnswerFalseAcceptRate": _ratio(falseAccepts, noAnswerRows),
    }
    return {
        "valid": passRate >= minPassRate,
        "totalRows": len(decisions),
        "passedRows": passedRows,
        "metrics": metrics,
        "minPassRate": minPassRate,
        "rows": decisions,
        "failures": failures,
    }


def evaluateCanaryPack(
    canaryRows: Iterable[Mapping[str, Any]],
    searchFn: Any,
    *,
    limit: int = 10,
    scope: str = "auto",
    minPassRate: float = 1.0,
) -> dict[str, Any]:
    """Run a canary pack through a search callable and evaluate it.

    Args:
        canaryRows: Canary definitions.
        searchFn: Callable accepting ``query, limit, scope`` and returning rows or DataFrame.
        limit: Search limit.
        scope: Search scope passed to the callable.
        minPassRate: Minimum pass rate required for validity.

    Returns:
        dict[str, Any]: Canary evaluation report.

    Raises:
        Exception: Propagates exceptions raised by ``searchFn``.

    Example:
        >>> callable(evaluateCanaryPack)
        True
    """
    rows = [dict(row) for row in canaryRows]
    results: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        query = str(row.get("query") or row.get("q") or "")
        if query in results:
            continue
        raw = searchFn(query, limit=limit, scope=scope)
        results[query] = _toDictRows(raw)
    return evaluateCanaryPackRows(rows, results, defaultTopK=limit, minPassRate=minPassRate)


def writeCanaryReport(path: str | Path, report: Mapping[str, Any]) -> None:
    """Write a canary report JSON file.

    Args:
        path: Output path.
        report: Canary report payload.

    Returns:
        None.

    Raises:
        OSError: If the file cannot be written.

    Example:
        >>> callable(writeCanaryReport)
        True
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(report), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _expectedAnswerable(row: Mapping[str, Any]) -> bool:
    for key in ("expectedAnswerable", "expectAnswerable", "answerable"):
        if key in row:
            return _asBool(row.get(key), default=True)
    return _targetKind(row) != "noAnswer"


def _targetKind(row: Mapping[str, Any]) -> str:
    target = str(row.get("targetKind") or row.get("target") or row.get("kind") or "").strip()
    aliases = {
        "negative": "noAnswer",
        "no-answer": "noAnswer",
        "noanswer": "noAnswer",
        "allFilings": "filing",
        "panel": "filing",
        "dartPanel": "filing",
        "edgar-panel": "edgar",
        "edgarPanel": "edgar",
    }
    return aliases.get(target, target or "filing")


def _expectedSourceRefs(row: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    value = row.get("expectedSourceRefs") or row.get("expectedSourceRef") or row.get("sourceRef")
    if isinstance(value, str) and value:
        refs.add(value)
    elif isinstance(value, (list, tuple, set)):
        refs.update(str(item) for item in value if item)
    return refs


def _sourceRef(row: Mapping[str, Any]) -> str:
    return str(row.get("sourceRef") or row.get("rcept_no") or "")


def _isAnswerable(row: Mapping[str, Any]) -> bool:
    return _asBool(row.get("answerable"), default=True)


def _toDictRows(raw: Any) -> list[dict[str, Any]]:
    if hasattr(raw, "to_dicts"):
        return [dict(row) for row in raw.to_dicts()]
    if isinstance(raw, list):
        return [dict(row) for row in raw if isinstance(row, Mapping)]
    return []


def _policyCandidate(failure: str) -> str:
    return {
        "falseAccept": "negativeAnswerabilityPolicy",
        "missingAnswerable": "sourceFreshnessOrCoveragePolicy",
        "sourceMiss": "sourceIntentPolicy",
        "sourceRefMiss": "citationIntegrityPolicy",
        "resolutionInjectionFailed": "candidateAtomicityPolicy",
    }.get(failure, "policyReview")
