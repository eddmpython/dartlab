"""텍스트 비교 / 변화 추적 헬퍼.

company.py에서 분리된 모듈-레벨 헬퍼.
_buildTopicChangeLedger, _buildTopicEvidence 등이 핵심.
"""

from __future__ import annotations

import difflib
import hashlib
import re
from typing import Any

import polars as pl


def _normalizeTextCell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return re.sub(r"\s+", " ", text)


def _stableFingerprint(*parts: Any) -> str:
    raw = "||".join(_normalizeTextCell(part) for part in parts if part is not None)
    return hashlib.md5(raw.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]


def _tableMetrics(text: str) -> tuple[int, int, str, str]:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return 0, 0, "", ""

    parsed: list[list[str]] = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        parsed.append(cells)

    header = parsed[0] if parsed else []
    body = parsed[2:] if len(parsed) > 2 else []
    rowLabels = [row[0] for row in body if row]
    return len(body), max((len(row) for row in parsed), default=0), "/".join(header), "/".join(rowLabels[:12])


def _textSimilarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, _normalizeTextCell(left), _normalizeTextCell(right)).ratio()


def _canonicalBlockRecord(record: dict[str, Any]) -> dict[str, Any]:
    rawText = str(record.get("blockText") or "")
    blockType = str(record.get("blockType") or "")
    if blockType == "table":
        normalizedText = "\n".join(line.strip() for line in rawText.splitlines() if line.strip())
    else:
        normalizedText = _normalizeTextCell(rawText)
    blockLabel = _normalizeTextCell(record.get("blockLabel"))
    semanticTopic = _normalizeTextCell(record.get("semanticTopic"))
    detailTopic = _normalizeTextCell(record.get("detailTopic"))
    tableRows, tableCols, tableHeader, tableLabels = (0, 0, "", "")
    if blockType == "table":
        tableRows, tableCols, tableHeader, tableLabels = _tableMetrics(normalizedText)
    tableShape = (
        f"rows={tableRows}|cols={tableCols}|header={tableHeader}|labels={tableLabels}" if blockType == "table" else None
    )
    anchorKey = "|".join(
        [
            blockType,
            detailTopic,
            semanticTopic,
            blockLabel,
        ]
    )
    structureKey = "|".join(
        [
            anchorKey,
            tableShape or "",
        ]
    )
    textHash = _stableFingerprint(normalizedText)
    blockKey = _stableFingerprint(structureKey, normalizedText)
    evidenceRef = f"{record.get('cellKey')}#{int(record.get('blockIdx', 0))}"
    return {
        "topic": str(record.get("topic") or ""),
        "period": str(record.get("period") or ""),
        "periodOrder": int(record.get("periodOrder") or 0),
        "sectionOrder": int(record.get("sectionOrder") or 0),
        "blockIdx": int(record.get("blockIdx") or 0),
        "blockType": blockType,
        "blockLabel": blockLabel,
        "semanticTopic": semanticTopic or None,
        "detailTopic": detailTopic or None,
        "isPlaceholder": bool(record.get("isPlaceholder")),
        "cellKey": str(record.get("cellKey") or ""),
        "evidenceRef": evidenceRef,
        "blockText": rawText,
        "normalizedText": normalizedText,
        "textHash": textHash,
        "tableShape": tableShape,
        "tableRows": tableRows,
        "tableCols": tableCols,
        "anchorKey": anchorKey,
        "structureKey": structureKey,
        "blockKey": blockKey,
    }


def _matchTopicBlocks(
    previousBlocks: list[dict[str, Any]] | None,
    currentBlocks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    previousBlocks = previousBlocks or []
    previousByStructure: dict[str, list[dict[str, Any]]] = {}
    previousByAnchor: dict[str, list[dict[str, Any]]] = {}
    previousByText: dict[str, list[dict[str, Any]]] = {}
    for block in previousBlocks:
        previousByStructure.setdefault(block["structureKey"], []).append(block)
        previousByAnchor.setdefault(block["anchorKey"], []).append(block)
        previousByText.setdefault(block["textHash"], []).append(block)

    matches: list[dict[str, Any]] = []
    counts = {
        "kept": 0,
        "added": 0,
        "removed": 0,
        "edited": 0,
        "moved": 0,
        "restated": 0,
        "placeholder": 0,
    }

    for current in currentBlocks:
        if current["isPlaceholder"]:
            anchorCandidates = previousByAnchor.get(current["anchorKey"], [])
            if anchorCandidates:
                previous = anchorCandidates.pop(0)
                previousByStructure[previous["structureKey"]].remove(previous)
                previousByText[previous["textHash"]].remove(previous)
            else:
                previous = None
            counts["placeholder"] += 1
            matches.append({"changeType": "placeholder", "current": current, "previous": previous})
            continue

        structureCandidates = previousByStructure.get(current["structureKey"], [])
        exactIdx = next(
            (idx for idx, block in enumerate(structureCandidates) if block["blockKey"] == current["blockKey"]),
            None,
        )
        if exactIdx is not None:
            previous = structureCandidates.pop(exactIdx)
            previousByText[previous["textHash"]].remove(previous)
            previousByAnchor[previous["anchorKey"]].remove(previous)
            counts["kept"] += 1
            matches.append({"changeType": "unchanged", "current": current, "previous": previous})
            continue

        if structureCandidates:
            previous = structureCandidates.pop(0)
            previousByText[previous["textHash"]].remove(previous)
            previousByAnchor[previous["anchorKey"]].remove(previous)
            similarity = _textSimilarity(previous["normalizedText"], current["normalizedText"])
            if similarity >= 0.95:
                counts["restated"] += 1
                matches.append({"changeType": "restated", "current": current, "previous": previous})
            else:
                counts["edited"] += 1
                matches.append({"changeType": "edited", "current": current, "previous": previous})
            continue

        anchorCandidates = previousByAnchor.get(current["anchorKey"], [])
        if anchorCandidates:
            previous = anchorCandidates.pop(0)
            previousByStructure[previous["structureKey"]].remove(previous)
            previousByText[previous["textHash"]].remove(previous)
            if current["blockType"] == "table":
                if current["tableRows"] > previous["tableRows"] or current["tableCols"] > previous["tableCols"]:
                    counts["added"] += 1
                    matches.append({"changeType": "added", "current": current, "previous": previous})
                elif current["tableRows"] < previous["tableRows"] or current["tableCols"] < previous["tableCols"]:
                    counts["removed"] += 1
                    matches.append({"changeType": "removed", "current": current, "previous": previous})
                else:
                    counts["edited"] += 1
                    matches.append({"changeType": "edited", "current": current, "previous": previous})
            else:
                similarity = _textSimilarity(previous["normalizedText"], current["normalizedText"])
                if similarity >= 0.95:
                    counts["restated"] += 1
                    matches.append({"changeType": "restated", "current": current, "previous": previous})
                else:
                    counts["edited"] += 1
                    matches.append({"changeType": "edited", "current": current, "previous": previous})
            continue

        textCandidates = previousByText.get(current["textHash"], [])
        if textCandidates:
            previous = textCandidates.pop(0)
            previousByStructure[previous["structureKey"]].remove(previous)
            previousByAnchor[previous["anchorKey"]].remove(previous)
            counts["moved"] += 1
            matches.append({"changeType": "moved", "current": current, "previous": previous})
            continue

        counts["added"] += 1
        matches.append({"changeType": "added", "current": current, "previous": None})

    for remaining in previousByStructure.values():
        for previous in remaining:
            counts["removed"] += 1
            matches.append({"changeType": "removed", "current": None, "previous": previous})

    return matches, counts


def _summarizeTopicChange(matches: list[dict[str, Any]], counts: dict[str, int]) -> tuple[str, str]:
    nonPlaceholder = sum(counts[key] for key in ("added", "removed", "edited", "moved", "restated"))
    if nonPlaceholder == 0 and counts["placeholder"] > 0:
        changeType = "placeholder"
    elif counts["moved"] > 0 and counts["added"] == counts["removed"] == counts["edited"] == counts["restated"] == 0:
        changeType = "moved"
    elif counts["restated"] > 0 and counts["added"] == counts["removed"] == counts["edited"] == counts["moved"] == 0:
        changeType = "restated"
    elif counts["added"] > 0 and counts["removed"] == counts["edited"] == counts["moved"] == counts["restated"] == 0:
        changeType = "added"
    elif counts["removed"] > 0 and counts["added"] == counts["edited"] == counts["moved"] == counts["restated"] == 0:
        changeType = "removed"
    elif (
        counts["edited"] > 0
        or counts["restated"] > 0
        or counts["moved"] > 0
        or (counts["added"] > 0 and counts["removed"] > 0)
    ):
        changeType = "edited"
    else:
        changeType = "unchanged"

    labels: list[str] = []
    for match in matches:
        block = match.get("current") or match.get("previous")
        if block is None:
            continue
        label = (
            block.get("detailTopic") or block.get("semanticTopic") or block.get("blockLabel") or block.get("blockType")
        )
        if label and label not in labels:
            labels.append(str(label))
        if len(labels) >= 3:
            break

    parts: list[str] = []
    for key, label in (
        ("added", "추가"),
        ("removed", "삭제"),
        ("edited", "수정"),
        ("moved", "이동"),
        ("restated", "재기재"),
        ("placeholder", "placeholder"),
    ):
        if counts[key] > 0:
            parts.append(f"{label} {counts[key]}")
    if not parts:
        parts.append("변경 없음")
    if labels:
        parts.append(", ".join(labels))
    return changeType, " · ".join(parts)


def _buildTopicChangeLedger(topicBlocks: pl.DataFrame | None) -> pl.DataFrame:
    schema = {
        "topic": pl.Utf8,
        "period": pl.Utf8,
        "previousPeriod": pl.Utf8,
        "changeType": pl.Utf8,
        "change": pl.Utf8,
        "summary": pl.Utf8,
        "evidenceRef": pl.Utf8,
        "text": pl.Utf8,
        "addedBlocks": pl.Int64,
        "removedBlocks": pl.Int64,
        "editedBlocks": pl.Int64,
        "movedBlocks": pl.Int64,
        "restatedBlocks": pl.Int64,
        "placeholderBlocks": pl.Int64,
    }
    if topicBlocks is None or topicBlocks.is_empty():
        return pl.DataFrame(schema=schema)

    from dartlab.engines.dart.docs.sections import sortPeriods

    canonicalBlocks = [_canonicalBlockRecord(record) for record in topicBlocks.to_dicts()]
    periods = sortPeriods(sorted({block["period"] for block in canonicalBlocks}), descending=False)
    statesByPeriod: dict[str, list[dict[str, Any]]] = {
        period: sorted(
            [block for block in canonicalBlocks if block["period"] == period],
            key=lambda row: (row["sectionOrder"], row["blockIdx"]),
        )
        for period in periods
    }

    rows: list[dict[str, Any]] = []
    previousState: list[dict[str, Any]] | None = None
    previousPeriod: str | None = None
    previousFingerprint: str | None = None

    for period in periods:
        currentState = statesByPeriod[period]
        currentFingerprint = _stableFingerprint(*(block["blockKey"] for block in currentState))
        if previousFingerprint is not None and currentFingerprint == previousFingerprint:
            continue

        if previousState is None:
            changeType = "initial"
            summary = "초기 기준점"
            evidenceRef = f"{currentState[0]['cellKey']}#period" if currentState else f"{period}"
            text = "\n\n".join(block["blockText"] for block in currentState if block["blockText"]).strip()
            rows.append(
                {
                    "topic": currentState[0]["topic"] if currentState else None,
                    "period": period,
                    "previousPeriod": None,
                    "changeType": changeType,
                    "change": changeType,
                    "summary": summary,
                    "evidenceRef": evidenceRef,
                    "text": text,
                    "addedBlocks": len(currentState),
                    "removedBlocks": 0,
                    "editedBlocks": 0,
                    "movedBlocks": 0,
                    "restatedBlocks": 0,
                    "placeholderBlocks": sum(1 for block in currentState if block["isPlaceholder"]),
                }
            )
        else:
            matches, counts = _matchTopicBlocks(previousState, currentState)
            if counts["kept"] == len(currentState) and counts["removed"] == 0 and counts["placeholder"] == 0:
                previousFingerprint = currentFingerprint
                previousState = currentState
                previousPeriod = period
                continue

            changeType, summary = _summarizeTopicChange(matches, counts)
            evidenceRef = (
                f"{currentState[0]['cellKey']}#period" if currentState else f"{previousState[0]['cellKey']}#removed"
            )
            text = "\n\n".join(block["blockText"] for block in currentState if block["blockText"]).strip()
            rows.append(
                {
                    "topic": currentState[0]["topic"] if currentState else previousState[0]["topic"],
                    "period": period,
                    "previousPeriod": previousPeriod,
                    "changeType": changeType,
                    "change": changeType,
                    "summary": summary,
                    "evidenceRef": evidenceRef,
                    "text": text,
                    "addedBlocks": counts["added"],
                    "removedBlocks": counts["removed"],
                    "editedBlocks": counts["edited"],
                    "movedBlocks": counts["moved"],
                    "restatedBlocks": counts["restated"],
                    "placeholderBlocks": counts["placeholder"],
                }
            )

        previousFingerprint = currentFingerprint
        previousState = currentState
        previousPeriod = period

    result = pl.DataFrame(rows, schema=schema, strict=False)
    if result.is_empty():
        return result
    from dartlab.engines.dart.docs.sections import sortPeriods

    ordered = sortPeriods(result.get_column("period").to_list())
    orderMap = {period: idx for idx, period in enumerate(ordered)}
    return result.with_columns(pl.col("period").replace(orderMap).alias("_order")).sort("_order").drop("_order")


def _buildTopicEvidence(topicBlocks: pl.DataFrame | None, period: str) -> pl.DataFrame:
    from dartlab.engines.dart.docs.sections import rawPeriod

    period = rawPeriod(period)
    schema = {
        "topic": pl.Utf8,
        "period": pl.Utf8,
        "previousPeriod": pl.Utf8,
        "changeType": pl.Utf8,
        "evidenceRef": pl.Utf8,
        "blockType": pl.Utf8,
        "blockLabel": pl.Utf8,
        "semanticTopic": pl.Utf8,
        "detailTopic": pl.Utf8,
        "currentText": pl.Utf8,
        "previousText": pl.Utf8,
        "tableShape": pl.Utf8,
        "previousTableShape": pl.Utf8,
    }
    if topicBlocks is None or topicBlocks.is_empty():
        return pl.DataFrame(schema=schema)

    from dartlab.engines.dart.docs.sections import sortPeriods

    canonicalBlocks = [_canonicalBlockRecord(record) for record in topicBlocks.to_dicts()]
    periods = sortPeriods(sorted({block["period"] for block in canonicalBlocks}), descending=False)
    if period not in periods:
        return pl.DataFrame(schema=schema)

    periodIndex = periods.index(period)
    previousPeriod = periods[periodIndex - 1] if periodIndex > 0 else None
    currentState = sorted(
        [block for block in canonicalBlocks if block["period"] == period],
        key=lambda row: (row["sectionOrder"], row["blockIdx"]),
    )
    previousState = None
    if previousPeriod is not None:
        previousState = sorted(
            [block for block in canonicalBlocks if block["period"] == previousPeriod],
            key=lambda row: (row["sectionOrder"], row["blockIdx"]),
        )

    matches, _ = _matchTopicBlocks(previousState, currentState)
    rows: list[dict[str, Any]] = []
    for match in matches:
        current = match.get("current")
        previous = match.get("previous")
        block = current or previous
        if block is None:
            continue
        rows.append(
            {
                "topic": block["topic"],
                "period": period,
                "previousPeriod": previousPeriod,
                "changeType": match["changeType"],
                "evidenceRef": (current or previous)["evidenceRef"],
                "blockType": block["blockType"],
                "blockLabel": block["blockLabel"],
                "semanticTopic": block.get("semanticTopic"),
                "detailTopic": block.get("detailTopic"),
                "currentText": None if current is None else current["blockText"],
                "previousText": None if previous is None else previous["blockText"],
                "tableShape": None if current is None else current.get("tableShape"),
                "previousTableShape": None if previous is None else previous.get("tableShape"),
            }
        )

    if not rows and currentState:
        for current in currentState:
            rows.append(
                {
                    "topic": current["topic"],
                    "period": period,
                    "previousPeriod": previousPeriod,
                    "changeType": "initial",
                    "evidenceRef": current["evidenceRef"],
                    "blockType": current["blockType"],
                    "blockLabel": current["blockLabel"],
                    "semanticTopic": current.get("semanticTopic"),
                    "detailTopic": current.get("detailTopic"),
                    "currentText": current["blockText"],
                    "previousText": None,
                    "tableShape": current.get("tableShape"),
                    "previousTableShape": None,
                }
            )

    return pl.DataFrame(rows, schema=schema, strict=False)
