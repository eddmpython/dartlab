"""Event radar L1.5 helper.

The helper deliberately stays below L2 analysis engines. Callers pass raw
Company/gather/scan rows, and this module only normalizes, matches, scores,
and records falsifiers for a near-term catalyst radar.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

import polars as pl

from dartlab.synth.rowAccess import (
    evidenceSummary,
    firstValue,
    latestDate,
    pctChange,
    rowsOf,
    safeDiv,
    toFloat,
)

_DATE_KEYS = ("date", "rcept_dt", "datetime", "publishedAt", "filedAt", "tradingDate")

_EVENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "earnings": ("잠정", "실적", "earnings", "guidance", "preliminary"),
    "capitalAction": ("배당", "자사주", "소각", "유상증자", "무상증자", "split", "dividend", "buyback"),
    "financing": ("전환사채", "신주인수권", "cb", "bw", "convertible", "warrant"),
    "governance": ("최대주주", "임원", "대표이사", "insider", "ownership", "management"),
    "regulatory": ("소송", "제재", "불성실", "조사", "litigation", "sanction", "investigation"),
    "filingRisk": ("정정", "감사의견", "의견거절", "한정의견", "restatement", "qualified opinion"),
    "deal": ("합병", "분할", "영업양수", "인수", "merger", "acquisition", "spin-off"),
}

_RISK_CATEGORIES = {"filingRisk", "regulatory", "financing"}
_WATCH_CATEGORIES = {"earnings", "capitalAction", "governance", "deal"}


def buildEventRadarMemo(
    *,
    target: str,
    market: str = "KR",
    companyName: str = "",
    filings: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    newsRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    priceRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    flowRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    insiderRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    ownershipRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    dividendRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    splitRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    consensusRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    scanRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    asOf: str | None = None,
) -> dict[str, Any]:
    """Build an L1.5 event/catalyst radar memo from raw rows."""

    raw_sets = {
        "filings": rowsOf(filings),
        "newsRows": rowsOf(newsRows),
        "priceRows": rowsOf(priceRows),
        "flowRows": rowsOf(flowRows),
        "insiderRows": rowsOf(insiderRows),
        "ownershipRows": rowsOf(ownershipRows),
        "dividendRows": rowsOf(dividendRows),
        "splitRows": rowsOf(splitRows),
        "consensusRows": rowsOf(consensusRows),
        "scanRows": rowsOf(scanRows),
    }
    coverage_rows = _coverageRows(raw_sets)
    event_rows = _eventInbox(raw_sets["filings"], raw_sets["newsRows"])
    reaction_rows = _priceFlowReaction(raw_sets["priceRows"], raw_sets["flowRows"])
    insider_rows = _insiderOwnershipSignal(raw_sets["insiderRows"], raw_sets["ownershipRows"])
    capital_rows = _capitalActionMonitor(raw_sets["dividendRows"], raw_sets["splitRows"], event_rows)
    consensus_rows = _consensusDriftWatch(raw_sets["consensusRows"])
    scan_rows = _scanContext(raw_sets["scanRows"])
    falsifier_rows = _falsifierRows(event_rows, reaction_rows, insider_rows, capital_rows, consensus_rows)
    candidate_rows = _engineCandidateRows(
        event_rows,
        reaction_rows,
        insider_rows,
        capital_rows,
        consensus_rows,
        scan_rows,
    )
    score = _radarScore(event_rows, reaction_rows, insider_rows, capital_rows, consensus_rows, scan_rows)
    visual_rows = _visualDecisionRows(
        has_price=bool(raw_sets["priceRows"]),
        has_coverage=any(row["status"] == "ok" for row in coverage_rows),
        signal_count=sum(1 for row in candidate_rows if row["status"] in {"watch", "risk"}),
    )
    decision_status = "usable" if any(row["status"] == "ok" for row in coverage_rows) else "insufficientInputs"
    latest_date = asOf or _latestDate(
        event_rows,
        reaction_rows,
        insider_rows,
        capital_rows,
        consensus_rows,
        scan_rows,
    )
    deep_rows = _deepDiveRows(
        sourceCoverageAudit=coverage_rows,
        eventInbox=event_rows,
        priceFlowReaction=reaction_rows,
        insiderOwnershipSignal=insider_rows,
        capitalActionMonitor=capital_rows,
        consensusDriftWatch=consensus_rows,
        scanContext=scan_rows,
        falsifierLedger=falsifier_rows,
        engineCandidateMemo=candidate_rows,
        visualDecisionPack=visual_rows,
        radar_score=score,
        decision_status=decision_status,
    )

    return {
        "target": target,
        "market": market,
        "companyName": companyName or target,
        "asOf": latest_date,
        "decisionStatus": decision_status,
        "headline": {
            "target": target,
            "market": market,
            "companyName": companyName or target,
            "radarScore": score,
            "eventCount": sum(1 for row in event_rows if row["status"] != "missing"),
            "reactionCount": sum(1 for row in reaction_rows if row["status"] in {"watch", "risk"}),
            "insiderSignalCount": sum(1 for row in insider_rows if row["status"] in {"watch", "risk"}),
            "capitalActionCount": sum(1 for row in capital_rows if row["status"] in {"watch", "risk"}),
            "consensusSignalCount": sum(1 for row in consensus_rows if row["status"] in {"watch", "risk"}),
            "openFalsifierCount": sum(1 for row in falsifier_rows if row["status"] == "open"),
            "decisionStatus": decision_status,
        },
        "tables": {
            "sourceCoverageAudit": coverage_rows,
            "eventInbox": event_rows,
            "priceFlowReaction": reaction_rows,
            "insiderOwnershipSignal": insider_rows,
            "capitalActionMonitor": capital_rows,
            "consensusDriftWatch": consensus_rows,
            "scanContext": scan_rows,
            "falsifierLedger": falsifier_rows,
            "engineCandidateMemo": candidate_rows,
            "visualDecisionPack": visual_rows,
            "deepDive": deep_rows,
        },
        "sources": [
            {
                "id": "l1CompanyFilings",
                "title": "Company.disclosure/liveFilings raw filing rows",
                "url": "dartlab://Company.disclosure",
            },
            {
                "id": "l1GatherMarketData",
                "title": "Company.gather raw price/flow/news/consensus rows",
                "url": "dartlab://Company.gather",
            },
            {
                "id": "l15EventRadar",
                "title": "DartLab L1.5 event radar helper",
                "url": "dartlab://synth/eventRadar.buildEventRadarMemo",
            },
            {
                "id": "eventRadarSkillPack",
                "title": "Event Radar Incubator skill pack",
                "url": "dartlab://skills/recipes.fundamental.disclosure.eventRadar.index",
            },
        ],
    }


def _coverageRows(raw_sets: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    required_for = {
        "filings": "event inbox",
        "newsRows": "event inbox",
        "priceRows": "price reaction",
        "flowRows": "flow reaction",
        "insiderRows": "insider signal",
        "ownershipRows": "ownership signal",
        "dividendRows": "capital action",
        "splitRows": "capital action",
        "consensusRows": "consensus drift",
        "scanRows": "cross-section context",
    }
    rows: list[dict[str, Any]] = []
    for name, data_rows in raw_sets.items():
        rows.append(
            {
                "dataset": name,
                "status": "ok" if data_rows else "missing",
                "rowCount": len(data_rows),
                "latestDate": _latestDate(data_rows),
                "requiredFor": required_for.get(name, "optional context"),
                "evidence": "raw L1/L1.5 rows supplied by caller" if data_rows else "no rows supplied",
            }
        )
    return rows


def _eventInbox(filings: list[dict[str, Any]], news_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for row in filings:
        events.append(_eventRow(row, source="filing"))
    for row in news_rows:
        events.append(_eventRow(row, source="news"))
    events.sort(key=lambda row: str(row.get("date") or ""), reverse=True)
    if events:
        return events[:20]
    return [
        {
            "date": None,
            "source": "none",
            "title": "no filing/news rows supplied",
            "category": None,
            "status": "missing",
            "evidence": "Company.disclosure/liveFilings or gather.news is needed",
        }
    ]


def _eventRow(row: Mapping[str, Any], *, source: str) -> dict[str, Any]:
    title = str(firstValue(row, "report_nm", "title", "headline", "event", "summary") or "")
    date = firstValue(row, "rcept_dt", "date", "datetime", "publishedAt", "filedAt")
    text = " ".join(str(row.get(key) or "") for key in row)
    category = _eventCategory(f"{title} {text}")
    status = "risk" if category in _RISK_CATEGORIES else "watch" if category in _WATCH_CATEGORIES else "ok"
    return {
        "date": str(date) if date is not None else None,
        "source": source,
        "title": title[:160] or f"{source} event",
        "category": category or "uncategorized",
        "status": status,
        "evidence": "keyword match on raw title/body",
    }


def _priceFlowReaction(
    price_rows: list[dict[str, Any]],
    flow_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    price = _sortRows(price_rows)
    flow = _sortRows(flow_rows)
    latest = price[0] if price else {}
    previous = price[1] if len(price) > 1 else {}
    latest_flow = flow[0] if flow else {}
    close = toFloat(firstValue(latest, "close", "종가", "price", "last"))
    prev_close = toFloat(firstValue(previous, "close", "종가", "price", "last"))
    volume = toFloat(firstValue(latest, "volume", "거래량"))
    prev_volume = toFloat(firstValue(previous, "volume", "거래량"))
    price_change = pctChange(close, prev_close)
    volume_ratio = safeDiv(volume, prev_volume)
    foreign_net = toFloat(firstValue(latest_flow, "foreignNetBuy", "foreignNet", "외국인순매수", "foreign"))
    institution_net = toFloat(
        firstValue(latest_flow, "institutionNetBuy", "institutionNet", "기관순매수", "institution")
    )
    net_flow = sum(value for value in (foreign_net, institution_net) if value is not None) or None
    status = "missing"
    if latest:
        status = "ok"
        if (price_change is not None and abs(price_change) >= 0.08) or (volume_ratio is not None and volume_ratio >= 3):
            status = "risk"
        elif (price_change is not None and abs(price_change) >= 0.04) or (
            volume_ratio is not None and volume_ratio >= 1.8
        ):
            status = "watch"
    return [
        {
            "date": _dateOf(latest) or _dateOf(latest_flow),
            "close": close,
            "priceChangePct": _roundPct(price_change),
            "volumeRatio": _round(volume_ratio),
            "foreignNetBuy": foreign_net,
            "institutionNetBuy": institution_net,
            "netFlow": net_flow,
            "status": status,
            "evidence": "latest and previous raw price/flow rows",
        }
    ]


def _insiderOwnershipSignal(
    insider_rows: list[dict[str, Any]],
    ownership_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(_sortRows(insider_rows)[:10], start=1):
        text = " ".join(str(row.get(key) or "") for key in row)
        amount = toFloat(firstValue(row, "amount", "shares", "changeShares", "수량", "변동주식수"))
        direction = _direction(text, amount)
        status = "watch" if direction in {"buy", "sell"} else "ok"
        rows.append(
            {
                "rank": idx,
                "date": _dateOf(row),
                "holder": firstValue(row, "name", "holder", "person", "성명") or "unknown",
                "direction": direction,
                "amount": amount,
                "status": status,
                "evidence": "raw insider transaction row",
            }
        )
    for idx, row in enumerate(_sortRows(ownership_rows)[:5], start=len(rows) + 1):
        pct_change = toFloat(firstValue(row, "changePct", "ownershipChange", "지분변동", "delta"))
        status = "watch" if pct_change is not None and abs(pct_change) >= 1 else "ok"
        rows.append(
            {
                "rank": idx,
                "date": _dateOf(row),
                "holder": firstValue(row, "holder", "name", "shareholder", "주주명") or "major holder",
                "direction": "ownershipChange" if pct_change else "snapshot",
                "amount": pct_change,
                "status": status,
                "evidence": "raw ownership row",
            }
        )
    if rows:
        return rows
    return [
        {
            "rank": None,
            "date": None,
            "holder": "no insider/ownership rows supplied",
            "direction": None,
            "amount": None,
            "status": "missing",
            "evidence": "Company.gather insiderTrading/ownership or majorShareholders is needed",
        }
    ]


def _capitalActionMonitor(
    dividend_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _sortRows(dividend_rows):
        value = toFloat(firstValue(row, "dividend", "dps", "cashDividend", "배당금", "value"))
        rows.append(
            {
                "date": _dateOf(row),
                "action": "dividend",
                "value": value,
                "status": "watch",
                "evidence": "raw dividend row",
            }
        )
    for row in _sortRows(split_rows):
        ratio = firstValue(row, "ratio", "splitRatio", "분할비율")
        rows.append(
            {
                "date": _dateOf(row),
                "action": "split",
                "value": ratio,
                "status": "watch",
                "evidence": "raw split row",
            }
        )
    for event in event_rows:
        if event.get("category") == "capitalAction":
            rows.append(
                {
                    "date": event.get("date"),
                    "action": "filingCapitalAction",
                    "value": event.get("title"),
                    "status": event.get("status", "watch"),
                    "evidence": "capital action keyword in filing/news event",
                }
            )
    if rows:
        return rows[:12]
    return [
        {
            "date": None,
            "action": "no capital action rows supplied",
            "value": None,
            "status": "missing",
            "evidence": "gather.dividends/splits or filing capital action is needed",
        }
    ]


def _consensusDriftWatch(consensus_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = _sortRows(consensus_rows)
    if len(rows) < 2:
        return [
            {
                "date": _dateOf(rows[0]) if rows else None,
                "metric": "consensus",
                "latest": None,
                "previous": None,
                "revisionPct": None,
                "status": "missing" if not rows else "ok",
                "evidence": "at least two consensus rows are needed for drift",
            }
        ]
    latest, previous = rows[0], rows[1]
    out: list[dict[str, Any]] = []
    for metric, keys in {
        "revenue": ("revenueConsensus", "salesConsensus", "revenue", "매출컨센서스"),
        "operatingProfit": ("opConsensus", "operatingProfitConsensus", "operatingProfit", "영업이익컨센서스"),
        "eps": ("epsConsensus", "eps", "EPS"),
        "targetPrice": ("targetPrice", "priceTarget", "목표주가"),
    }.items():
        latest_value = toFloat(firstValue(latest, *keys))
        previous_value = toFloat(firstValue(previous, *keys))
        revision = pctChange(latest_value, previous_value)
        status = "ok"
        if revision is not None and revision <= -0.10:
            status = "risk"
        elif revision is not None and abs(revision) >= 0.05:
            status = "watch"
        out.append(
            {
                "date": _dateOf(latest),
                "metric": metric,
                "latest": latest_value,
                "previous": previous_value,
                "revisionPct": _roundPct(revision),
                "status": status if latest_value is not None and previous_value is not None else "missing",
                "evidence": "latest two raw consensus rows",
            }
        )
    return out


def _scanContext(scan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(scan_rows[:10], start=1):
        score = toFloat(firstValue(row, "score", "value", "rankScore", "riskScore"))
        rows.append(
            {
                "rank": idx,
                "target": firstValue(row, "stockCode", "ticker", "target") or "",
                "axis": firstValue(row, "axis", "metric", "screen") or "scanPrimitive",
                "score": score,
                "status": "watch" if score is not None and score > 0 else "ok",
                "evidence": "optional scan primitive row",
            }
        )
    if rows:
        return rows
    return [
        {
            "rank": None,
            "target": "",
            "axis": "no scan rows supplied",
            "score": None,
            "status": "missing",
            "evidence": "scan primitive is optional context",
        }
    ]


def _falsifierRows(
    event_rows: list[dict[str, Any]],
    reaction_rows: list[dict[str, Any]],
    insider_rows: list[dict[str, Any]],
    capital_rows: list[dict[str, Any]],
    consensus_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _falsifier("filing/news catalyst", _maxStatus(event_rows), "routine filing or duplicated news headline"),
        _falsifier("price/flow reaction", _maxStatus(reaction_rows), "market-wide move or stale flow source"),
        _falsifier(
            "insider/ownership change", _maxStatus(insider_rows), "planned sale, treasury transfer, or data lag"
        ),
        _falsifier("capital action", _maxStatus(capital_rows), "ordinary recurring dividend or mechanical split"),
        _falsifier("consensus drift", _maxStatus(consensus_rows), "single stale broker update or currency/unit change"),
    ]


def _falsifier(claim: str, status: str, counter_evidence: str) -> dict[str, Any]:
    return {
        "claim": claim,
        "supportingEvidence": status,
        "counterEvidenceNeeded": counter_evidence,
        "status": "open" if status in {"watch", "risk"} else "notTriggered",
    }


def _engineCandidateRows(
    event_rows: list[dict[str, Any]],
    reaction_rows: list[dict[str, Any]],
    insider_rows: list[dict[str, Any]],
    capital_rows: list[dict[str, Any]],
    consensus_rows: list[dict[str, Any]],
    scan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates = [
        ("eventInbox", _maxStatus(event_rows), "filing/news event classifier"),
        ("priceFlowReaction", _maxStatus(reaction_rows), "price-volume-flow reaction bridge"),
        ("insiderOwnershipSignal", _maxStatus(insider_rows), "insider/holder change monitor"),
        ("capitalActionMonitor", _maxStatus(capital_rows), "capital action calendar"),
        ("consensusDriftWatch", _maxStatus(consensus_rows), "consensus revision ledger"),
        ("scanContext", _maxStatus(scan_rows), "cross-section scan context"),
    ]
    rows: list[dict[str, Any]] = []
    for signal_id, status, owner in candidates:
        rows.append(
            {
                "signalId": signal_id,
                "status": status,
                "recommendedEngineOwner": owner,
                "promotionGate": "3+ selfRuns, falsifier pass, observed visualization binding",
                "keepAsSkillAfterPromotion": True,
            }
        )
    return rows


def _visualDecisionRows(*, has_price: bool, has_coverage: bool, signal_count: int) -> list[dict[str, Any]]:
    return [
        {
            "visualRef": "engines.viz.priceChart",
            "status": "ready" if has_price else "blocked",
            "requiredBinding": "priceRows with date/close/volume",
            "evidence": "use only when raw price table is present",
        },
        {
            "visualRef": "engines.viz.kpiRibbon",
            "status": "ready" if has_coverage else "blocked",
            "requiredBinding": "headline radarScore/eventCount/openFalsifierCount",
            "evidence": "small metric strip for the radar headline",
        },
        {
            "visualRef": "engines.viz.evidenceCoverage",
            "status": "ready" if has_coverage else "blocked",
            "requiredBinding": "sourceCoverageAudit rows",
            "evidence": "coverage table exists",
        },
        {
            "visualRef": "engines.viz.mermaidDiagram",
            "status": "ready" if signal_count >= 2 else "blocked",
            "requiredBinding": "8 nodes or fewer with tableRef/sourceRef per edge",
            "evidence": "multiple signal ledgers triggered",
        },
    ]


def _deepDiveRows(
    *,
    radar_score: int,
    decision_status: str,
    **tables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for order, (name, table) in enumerate(tables.items(), start=1):
        rows.append(
            {
                "order": order,
                "step": name,
                "status": _maxStatus(table),
                "rowCount": len(table),
                "evidence": evidenceSummary(table),
                "nextAction": _nextAction(name, _maxStatus(table)),
            }
        )
    rows.append(
        {
            "order": len(rows) + 1,
            "step": "finalDecision",
            "status": "watch" if radar_score else "ok" if decision_status == "usable" else "missing",
            "rowCount": len(rows),
            "evidence": f"radarScore={radar_score}; decisionStatus={decision_status}",
            "nextAction": "open falsifiers and observed visual bindings must be shown with the answer",
        }
    )
    return rows


def _radarScore(*tables: list[dict[str, Any]]) -> int:
    score = 0
    for table in tables:
        status = _maxStatus(table)
        score += 3 if status == "risk" else 1 if status == "watch" else 0
    return score


def _eventCategory(text: str) -> str | None:
    lowered = text.lower()
    compacted = _compact(text)
    for category, keywords in _EVENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in lowered or _compact(keyword) in compacted:
                return category
    return None


def _direction(text: str, amount: float | None) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("buy", "acquire", "매수", "취득")):
        return "buy"
    if any(token in lowered for token in ("sell", "dispose", "매도", "처분")):
        return "sell"
    if amount is not None and amount > 0:
        return "buy"
    if amount is not None and amount < 0:
        return "sell"
    return "unknown"


def _sortRows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: str(_dateOf(row) or ""), reverse=True)


def _latestDate(*items: Any) -> str | None:
    """이 판독기가 날짜로 보는 key 목록을 공유 접근자에 넘긴다."""
    return latestDate(items, keys=_DATE_KEYS)


def _dateOf(row: Mapping[str, Any]) -> str | None:
    value = firstValue(row, *_DATE_KEYS)
    return str(value) if value is not None else None


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 4)


def _roundPct(value: float | None) -> float | None:
    return None if value is None else round(float(value) * 100, 2)


def _maxStatus(rows: list[dict[str, Any]]) -> str:
    rank = {"missing": 0, "blocked": 0, "ok": 1, "ready": 1, "watch": 2, "risk": 3, "open": 2}
    if not rows:
        return "missing"
    return max((str(row.get("status") or "missing") for row in rows), key=lambda item: rank.get(item, 0))


def _nextAction(step: str, status: str) -> str:
    if status in {"risk", "watch", "open"}:
        return f"{step} falsifier and source freshness check"
    if status == "missing":
        return f"supply L1/L1.5 rows for {step}"
    return "preserve evidence refs and continue"


def _compact(text: str) -> str:
    return re.sub(r"[\s,()\-_/·]", "", str(text or "").lower())


__all__ = ["buildEventRadarMemo"]
