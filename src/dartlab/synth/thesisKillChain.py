"""Thesis kill-chain L1.5 helper.

The helper builds a pre-mortem scenario from raw Company/gather/scan rows. It
does not call L2 engines. Callers provide evidence rows, and this module turns
them into assumption ledgers, fragility maps, triggers, propagation paths,
tripwires, falsifiers, and a scenario storyboard.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

import polars as pl

from dartlab.synth.rowAccess import (
    diff,
    evidenceSummary,
    firstValue,
    latestDate,
    pctChange,
    rowsOf,
    safeDiv,
    toFloat,
)

_DATE_KEYS = ("date", "rcept_dt", "datetime", "publishedAt", "filedAt", "period")

_ACCOUNT_ALIASES: dict[str, tuple[str, ...]] = {
    "revenue": ("sales", "revenue", "매출액", "영업수익"),
    "operatingProfit": ("operating_profit", "operating_income", "영업이익"),
    "netIncome": ("net_income", "net_profit", "profit_loss", "당기순이익"),
    "cfo": ("operating_cashflow", "net_cash_flow_operating", "cash_flows_from_used_in_operating_activities"),
    "capex": ("capital_expenditures", "purchase_of_property_plant_and_equipment", "capex"),
    "cash": ("cash_and_cash_equivalents", "cash", "현금및현금성자산"),
    "debt": ("short_term_debt", "long_term_debt", "borrowings", "interest_bearing_debt"),
    "equity": ("total_stockholders_equity", "total_equity", "equity"),
}

_ASSUMPTION_PATTERNS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("revenueGrowth", ("성장", "매출", "growth", "sales", "revenue"), "revenue growth keeps thesis alive"),
    ("marginDurability", ("마진", "수익성", "margin", "profitability"), "margin durability supports thesis"),
    ("cashConversion", ("현금", "cash", "fcf", "cfo"), "earnings convert into cash"),
    ("balanceSheet", ("부채", "leverage", "debt", "재무"), "balance sheet can absorb shocks"),
    ("valuationSupport", ("저평가", "valuation", "multiple", "dcf", "가치"), "valuation cushion remains"),
    ("eventFollowThrough", ("촉매", "공시", "event", "catalyst"), "expected catalyst follows through"),
    ("macroTolerance", ("금리", "환율", "macro", "매크로", "cycle"), "macro path does not break drivers"),
    ("governanceTrust", ("지배", "감사", "governance", "audit"), "governance does not impair trust"),
)

_FILING_RISK_KEYWORDS = {
    "financingStress": ("전환사채", "유상증자", "신주인수권", "convertible", "rights offering"),
    "restatementRisk": ("정정", "재작성", "restatement", "amendment"),
    "auditRisk": ("감사의견", "의견거절", "한정의견", "qualified opinion", "going concern"),
    "litigationRisk": ("소송", "제재", "조사", "litigation", "sanction", "investigation"),
    "governanceRisk": ("최대주주", "대표이사", "임원", "major shareholder", "management change"),
}


def buildThesisKillChainMemo(
    *,
    target: str,
    thesis: str = "",
    market: str = "KR",
    companyName: str = "",
    statements: Mapping[str, pl.DataFrame] | None = None,
    filings: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    priceRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    flowRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    consensusRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    scanRows: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None = None,
    assumptions: Iterable[str | Mapping[str, Any]] | None = None,
    asOf: str | None = None,
) -> dict[str, Any]:
    """Build a thesis pre-mortem scenario memo from L1/L1.5 inputs."""

    statement_map = dict(statements or {})
    panel = _statementPanel(statement_map)
    raw_sets = {
        "statements": panel,
        "filings": rowsOf(filings),
        "priceRows": rowsOf(priceRows),
        "flowRows": rowsOf(flowRows),
        "consensusRows": rowsOf(consensusRows),
        "scanRows": rowsOf(scanRows),
        "assumptions": _assumptionRows(assumptions),
    }
    thesis_rows = _thesisIntake(thesis, raw_sets["assumptions"])
    coverage_rows = _coverageRows(raw_sets)
    assumption_rows = _assumptionLedger(thesis_rows, raw_sets["assumptions"])
    fragility_rows = _fragilityMap(panel, raw_sets["priceRows"], raw_sets["flowRows"], raw_sets["consensusRows"])
    trigger_rows = _triggerCatalog(fragility_rows, raw_sets["filings"], raw_sets["scanRows"])
    propagation_rows = _propagationPath(trigger_rows, assumption_rows)
    tripwire_rows = _tripwireMonitor(fragility_rows, trigger_rows)
    falsifier_rows = _falsifierRows(propagation_rows, tripwire_rows)
    scenario_rows = _scenarioStoryboard(thesis_rows, propagation_rows, tripwire_rows, falsifier_rows)
    visual_rows = _visualDecisionRows(
        has_scenarios=bool(scenario_rows),
        has_paths=any(row["status"] in {"watch", "risk"} for row in propagation_rows),
        has_coverage=any(row["status"] == "ok" for row in coverage_rows),
    )
    quality_rows = _premortemQualityGate(
        thesis_rows=thesis_rows,
        coverage_rows=coverage_rows,
        assumption_rows=assumption_rows,
        fragility_rows=fragility_rows,
        trigger_rows=trigger_rows,
        propagation_rows=propagation_rows,
        tripwire_rows=tripwire_rows,
        falsifier_rows=falsifier_rows,
        scenario_rows=scenario_rows,
        visual_rows=visual_rows,
    )
    quality_score = _qualityScore(quality_rows)
    quality_gate_status = _qualityGateStatus(quality_score)
    score = _killRiskScore(fragility_rows, trigger_rows, tripwire_rows)
    decision_status = _decisionStatus(thesis_rows, quality_gate_status)
    latest_date = asOf or _latestDate(raw_sets["filings"], raw_sets["priceRows"], raw_sets["consensusRows"])
    deep_rows = _deepDiveRows(
        thesisIntake=thesis_rows,
        evidenceCoverageAudit=coverage_rows,
        assumptionLedger=assumption_rows,
        fragilityMap=fragility_rows,
        triggerCatalog=trigger_rows,
        propagationPath=propagation_rows,
        tripwireMonitor=tripwire_rows,
        falsifierLedger=falsifier_rows,
        scenarioStoryboard=scenario_rows,
        visualDecisionPack=visual_rows,
        premortemQualityGate=quality_rows,
        kill_score=score,
        quality_score=quality_score,
        quality_gate_status=quality_gate_status,
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
            "killRiskScore": score,
            "assumptionCount": len(assumption_rows),
            "fragilityCount": sum(1 for row in fragility_rows if row["status"] in {"watch", "risk"}),
            "triggerCount": sum(1 for row in trigger_rows if row["status"] in {"watch", "risk"}),
            "openTripwireCount": sum(1 for row in tripwire_rows if row["status"] in {"watch", "risk"}),
            "openFalsifierCount": sum(1 for row in falsifier_rows if row["status"] == "open"),
            "premortemQualityScore": quality_score,
            "qualityGateStatus": quality_gate_status,
            "decisionStatus": decision_status,
        },
        "tables": {
            "thesisIntake": thesis_rows,
            "evidenceCoverageAudit": coverage_rows,
            "assumptionLedger": assumption_rows,
            "fragilityMap": fragility_rows,
            "triggerCatalog": trigger_rows,
            "propagationPath": propagation_rows,
            "tripwireMonitor": tripwire_rows,
            "falsifierLedger": falsifier_rows,
            "scenarioStoryboard": scenario_rows,
            "visualDecisionPack": visual_rows,
            "premortemQualityGate": quality_rows,
            "deepDive": deep_rows,
        },
        "sources": [
            {
                "id": "l1CompanyStatements",
                "title": "Company.panel raw statement tables",
                "url": "dartlab://Company.panel/BS-IS-CF",
            },
            {
                "id": "l1CompanyGather",
                "title": "Company.gather raw price/flow/consensus rows",
                "url": "dartlab://Company.gather",
            },
            {
                "id": "l15ThesisKillChain",
                "title": "DartLab L1.5 thesis kill-chain helper",
                "url": "dartlab://synth/thesisKillChain.buildThesisKillChainMemo",
            },
            {
                "id": "thesisKillChainSkillPack",
                "title": "Thesis Kill-Chain Scenario skill pack",
                "url": "dartlab://skills/recipes.meta.thesisKillChain.index",
            },
        ],
    }


def _thesisIntake(thesis: str, assumption_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    text = thesis.strip() or "No explicit thesis supplied"
    themes = []
    lowered = text.lower()
    compacted = _compact(text)
    for assumption_id, keywords, _description in _ASSUMPTION_PATTERNS:
        if any(keyword.lower() in lowered or _compact(keyword) in compacted for keyword in keywords):
            themes.append(assumption_id)
    if not themes and assumption_rows:
        themes = [str(row.get("assumptionId") or "customAssumption") for row in assumption_rows]
    if not themes:
        themes = ["unstructuredThesis"]
    return [
        {
            "thesis": text,
            "themeCount": len(themes),
            "themes": ", ".join(dict.fromkeys(themes)),
            "status": "ok" if thesis.strip() else "missing",
            "evidence": "user thesis text and optional assumptions",
        }
    ]


def _assumptionRows(assumptions: Iterable[str | Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(assumptions or (), start=1):
        if isinstance(item, Mapping):
            text = str(item.get("claim") or item.get("assumption") or item.get("text") or "")
            assumption_id = str(item.get("assumptionId") or item.get("id") or f"customAssumption{idx}")
        else:
            text = str(item or "")
            assumption_id = f"customAssumption{idx}"
        if text.strip():
            rows.append({"assumptionId": assumption_id, "claim": text.strip(), "source": "user"})
    return rows


def _coverageRows(raw_sets: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    required_for = {
        "statements": "fragility map",
        "filings": "trigger catalog",
        "priceRows": "market tripwire",
        "flowRows": "market tripwire",
        "consensusRows": "expectation tripwire",
        "scanRows": "cross-section context",
        "assumptions": "assumption ledger",
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


def _assumptionLedger(
    thesis_rows: list[dict[str, Any]],
    explicit_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    thesis_text = str(thesis_rows[0]["thesis"] if thesis_rows else "")
    rows = []
    seen: set[str] = set()
    for assumption_id, keywords, description in _ASSUMPTION_PATTERNS:
        if _matchesAny(thesis_text, keywords):
            seen.add(assumption_id)
            rows.append(
                {
                    "assumptionId": assumption_id,
                    "claim": description,
                    "source": "parsedThesis",
                    "status": "untested",
                    "evidenceNeeded": _evidenceNeeded(assumption_id),
                }
            )
    for row in explicit_rows:
        assumption_id = str(row["assumptionId"])
        if assumption_id in seen:
            continue
        rows.append(
            {
                "assumptionId": assumption_id,
                "claim": row["claim"],
                "source": row["source"],
                "status": "untested",
                "evidenceNeeded": "bind to sourceCoverageAudit and fragilityMap",
            }
        )
    if rows:
        return rows
    return [
        {
            "assumptionId": "unstructuredThesis",
            "claim": "thesis must be split into testable assumptions",
            "source": "fallback",
            "status": "missing",
            "evidenceNeeded": "user thesis with drivers or explicit assumptions",
        }
    ]


def _fragilityMap(
    panel: list[dict[str, Any]],
    price_rows: list[dict[str, Any]],
    flow_rows: list[dict[str, Any]],
    consensus_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    latest = panel[0] if panel else {}
    previous = panel[1] if len(panel) > 1 else {}
    rows = [
        _metricRow(
            "revenueGrowth",
            pctChange(toFloat(latest.get("revenue")), toFloat(previous.get("revenue"))),
            "growth below 0 or above unsustainably high range",
            risk=lambda value: value is not None and value < -0.10,
            watch=lambda value: value is not None and (value < 0 or value > 0.35),
        ),
        _metricRow(
            "operatingMarginTrend",
            diff(
                safeDiv(toFloat(latest.get("operatingProfit")), toFloat(latest.get("revenue"))),
                safeDiv(toFloat(previous.get("operatingProfit")), toFloat(previous.get("revenue"))),
            ),
            "margin deterioration breaks operating leverage assumption",
            risk=lambda value: value is not None and value < -0.05,
            watch=lambda value: value is not None and value < -0.02,
        ),
        _metricRow(
            "cashConversion",
            safeDiv(toFloat(latest.get("cfo")), toFloat(latest.get("netIncome"))),
            "CFO does not support accounting earnings",
            risk=lambda value: value is not None and value < 0.60,
            watch=lambda value: value is not None and value < 0.85,
        ),
        _metricRow(
            "debtToEquity",
            safeDiv(toFloat(latest.get("debt")), toFloat(latest.get("equity"))),
            "leverage reduces scenario room",
            risk=lambda value: value is not None and value > 1.50,
            watch=lambda value: value is not None and value > 0.80,
        ),
        _metricRow(
            "cashToDebt",
            safeDiv(toFloat(latest.get("cash")), toFloat(latest.get("debt"))),
            "liquidity cushion is thin",
            risk=lambda value: value is not None and value < 0.20,
            watch=lambda value: value is not None and value < 0.40,
        ),
    ]
    rows.extend(_marketFragility(price_rows, flow_rows))
    rows.extend(_consensusFragility(consensus_rows))
    return rows


def _metricRow(
    metric: str,
    value: float | None,
    thesis_break: str,
    *,
    risk,
    watch,
) -> dict[str, Any]:
    status = "missing"
    if value is not None:
        status = "risk" if risk(value) else "watch" if watch(value) else "ok"
    return {
        "metric": metric,
        "value": _round(value),
        "status": status,
        "thesisBreak": thesis_break,
        "evidence": "raw statement or market row",
    }


def _marketFragility(price_rows: list[dict[str, Any]], flow_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prices = _sortRows(price_rows)
    latest = prices[0] if prices else {}
    previous = prices[1] if len(prices) > 1 else {}
    price_change = pctChange(
        toFloat(firstValue(latest, "close", "price", "종가")),
        toFloat(firstValue(previous, "close", "price", "종가")),
    )
    flows = _sortRows(flow_rows)
    latest_flow = flows[0] if flows else {}
    net_flow = sum(
        value
        for value in (
            toFloat(firstValue(latest_flow, "foreignNetBuy", "foreignNet", "외국인순매수")),
            toFloat(firstValue(latest_flow, "institutionNetBuy", "institutionNet", "기관순매수")),
        )
        if value is not None
    )
    return [
        _metricRow(
            "priceReaction",
            price_change,
            "market rejects the thesis before fundamentals update",
            risk=lambda value: value is not None and value < -0.08,
            watch=lambda value: value is not None and value < -0.04,
        ),
        _metricRow(
            "flowPressure",
            net_flow if latest_flow else None,
            "foreign/institution flow pressure persists",
            risk=lambda value: value is not None and value < 0,
            watch=lambda value: value is not None and value == 0,
        ),
    ]


def _consensusFragility(consensus_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = _sortRows(consensus_rows)
    if len(rows) < 2:
        return [
            {
                "metric": "consensusRevision",
                "value": None,
                "status": "missing",
                "thesisBreak": "expectations cannot be monitored without two consensus rows",
                "evidence": "consensus rows missing",
            }
        ]
    latest, previous = rows[0], rows[1]
    op_revision = pctChange(
        toFloat(firstValue(latest, "opConsensus", "operatingProfitConsensus", "operatingProfit")),
        toFloat(firstValue(previous, "opConsensus", "operatingProfitConsensus", "operatingProfit")),
    )
    return [
        _metricRow(
            "consensusRevision",
            op_revision,
            "sell-side expectation drift breaks the thesis clock",
            risk=lambda value: value is not None and value < -0.12,
            watch=lambda value: value is not None and value < -0.05,
        )
    ]


def _triggerCatalog(
    fragility_rows: list[dict[str, Any]],
    filing_rows: list[dict[str, Any]],
    scan_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in fragility_rows:
        if row["status"] in {"watch", "risk"}:
            rows.append(
                {
                    "triggerId": f"metric:{row['metric']}",
                    "trigger": row["metric"],
                    "source": "fragilityMap",
                    "status": row["status"],
                    "evidence": row["thesisBreak"],
                }
            )
    for filing in _sortRows(filing_rows)[:10]:
        text = " ".join(str(filing.get(key) or "") for key in filing)
        category = _filingCategory(text)
        if category:
            rows.append(
                {
                    "triggerId": f"filing:{category}",
                    "trigger": firstValue(filing, "report_nm", "title", "headline") or category,
                    "source": "filing",
                    "status": "risk" if category in {"auditRisk", "financingStress"} else "watch",
                    "evidence": category,
                }
            )
    for scan in scan_rows[:8]:
        score = toFloat(firstValue(scan, "score", "value", "riskScore"))
        if score is not None and score > 0:
            rows.append(
                {
                    "triggerId": f"scan:{firstValue(scan, 'axis', 'metric', 'screen') or 'primitive'}",
                    "trigger": firstValue(scan, "axis", "metric", "screen") or "scanPrimitive",
                    "source": "scan",
                    "status": "watch",
                    "evidence": "positive scan primitive score",
                }
            )
    if rows:
        return rows[:16]
    return [
        {
            "triggerId": "noTrigger",
            "trigger": "no triggered fragility supplied",
            "source": "fallback",
            "status": "missing",
            "evidence": "needs fragility, filing, or scan signal",
        }
    ]


def _propagationPath(
    trigger_rows: list[dict[str, Any]],
    assumption_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    assumption_ids = [str(row["assumptionId"]) for row in assumption_rows] or ["unstructuredThesis"]
    rows: list[dict[str, Any]] = []
    active = [row for row in trigger_rows if row["status"] in {"watch", "risk"}]
    for idx, trigger in enumerate(active[:8], start=1):
        assumption_id = _linkedAssumption(str(trigger["trigger"]), assumption_ids)
        rows.append(
            {
                "order": idx,
                "triggerId": trigger["triggerId"],
                "mechanism": _mechanismFor(str(trigger["triggerId"])),
                "affectedAssumption": assumption_id,
                "tripwire": _tripwireFor(str(trigger["triggerId"])),
                "status": trigger["status"],
                "evidence": trigger["evidence"],
            }
        )
    if rows:
        return rows
    return [
        {
            "order": 1,
            "triggerId": "noTrigger",
            "mechanism": "no propagation path until a trigger is observed",
            "affectedAssumption": assumption_ids[0],
            "tripwire": "supply evidence rows",
            "status": "missing",
            "evidence": "triggerCatalog missing",
        }
    ]


def _tripwireMonitor(
    fragility_rows: list[dict[str, Any]],
    trigger_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fragility in fragility_rows:
        metric = str(fragility["metric"])
        rows.append(
            {
                "tripwire": metric,
                "current": fragility.get("value"),
                "threshold": _thresholdFor(metric),
                "status": fragility["status"],
                "action": _tripwireAction(metric, str(fragility["status"])),
                "evidence": fragility["evidence"],
            }
        )
    if not rows and trigger_rows:
        rows.append(
            {
                "tripwire": "trigger count",
                "current": len(trigger_rows),
                "threshold": ">=1 watch trigger",
                "status": _maxStatus(trigger_rows),
                "action": "read triggerCatalog before answering",
                "evidence": "triggerCatalog",
            }
        )
    return rows


def _falsifierRows(
    propagation_rows: list[dict[str, Any]],
    tripwire_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in propagation_rows:
        status = str(path.get("status") or "missing")
        rows.append(
            {
                "claim": f"{path.get('triggerId')} can break {path.get('affectedAssumption')}",
                "supportingEvidence": status,
                "counterEvidenceNeeded": _counterEvidenceFor(str(path.get("triggerId") or "")),
                "status": "open" if status in {"watch", "risk"} else "notTriggered",
            }
        )
    if not rows:
        rows.append(
            {
                "claim": "no active kill-chain path",
                "supportingEvidence": _maxStatus(tripwire_rows),
                "counterEvidenceNeeded": "more evidence rows",
                "status": "notTriggered",
            }
        )
    return rows


def _scenarioStoryboard(
    thesis_rows: list[dict[str, Any]],
    propagation_rows: list[dict[str, Any]],
    tripwire_rows: list[dict[str, Any]],
    falsifier_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    thesis = thesis_rows[0]["thesis"] if thesis_rows else "No explicit thesis supplied"
    risk_count = sum(1 for row in tripwire_rows if row["status"] == "risk")
    watch_count = sum(1 for row in tripwire_rows if row["status"] == "watch")
    open_falsifiers = sum(1 for row in falsifier_rows if row["status"] == "open")
    leading_path = next((row for row in propagation_rows if row["status"] in {"risk", "watch"}), propagation_rows[0])
    kill_status = "risk" if risk_count or open_falsifiers >= 3 else "watch" if watch_count else "missing"
    return [
        {
            "scenario": "baseIntact",
            "status": "ok" if not open_falsifiers else "watch",
            "plot": f"Thesis remains intact: {thesis}",
            "requiredEvidence": "all open falsifiers closed",
            "monitoring": "keep tripwireMonitor green",
        },
        {
            "scenario": "erosionCase",
            "status": "watch" if watch_count or risk_count else "missing",
            "plot": f"Thesis erodes through {leading_path.get('mechanism')}",
            "requiredEvidence": "watch tripwire persists for two checks",
            "monitoring": str(leading_path.get("tripwire")),
        },
        {
            "scenario": "killChainCase",
            "status": kill_status,
            "plot": f"Thesis breaks when {leading_path.get('triggerId')} propagates to {leading_path.get('affectedAssumption')}",
            "requiredEvidence": "risk tripwire plus unresolved falsifier",
            "monitoring": "do not answer with buy/sell conclusion; show break path",
        },
    ]


def _visualDecisionRows(*, has_scenarios: bool, has_paths: bool, has_coverage: bool) -> list[dict[str, Any]]:
    return [
        {
            "visualRef": "engines.viz.scenarioVisuals",
            "status": "ready" if has_scenarios else "blocked",
            "requiredBinding": "scenarioStoryboard rows",
            "evidence": "scenario table exists",
        },
        {
            "visualRef": "engines.viz.mermaidDiagram",
            "status": "ready" if has_paths else "blocked",
            "requiredBinding": "propagationPath with <=8 edges",
            "evidence": "kill-chain path exists",
        },
        {
            "visualRef": "engines.viz.evidenceCoverage",
            "status": "ready" if has_coverage else "blocked",
            "requiredBinding": "evidenceCoverageAudit rows",
            "evidence": "coverage table exists",
        },
        {
            "visualRef": "engines.viz.kpiRibbon",
            "status": "ready" if has_scenarios else "blocked",
            "requiredBinding": "headline killRiskScore/openTripwireCount/openFalsifierCount",
            "evidence": "headline metrics exist",
        },
    ]


def _premortemQualityGate(
    *,
    thesis_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    assumption_rows: list[dict[str, Any]],
    fragility_rows: list[dict[str, Any]],
    trigger_rows: list[dict[str, Any]],
    propagation_rows: list[dict[str, Any]],
    tripwire_rows: list[dict[str, Any]],
    falsifier_rows: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    visual_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    ok_datasets = [row for row in coverage_rows if row.get("status") == "ok"]
    active_fragility = [row for row in fragility_rows if row.get("status") in {"watch", "risk"}]
    active_triggers = [row for row in trigger_rows if row.get("status") in {"watch", "risk"}]
    active_paths = [row for row in propagation_rows if row.get("status") in {"watch", "risk"}]
    active_tripwires = [row for row in tripwire_rows if row.get("status") in {"watch", "risk"}]
    open_falsifiers = [row for row in falsifier_rows if row.get("status") == "open"]
    scenarios = {str(row.get("scenario")) for row in scenario_rows}
    scenario_statuses = {str(row.get("status") or "missing") for row in scenario_rows}
    ready_visuals = [row for row in visual_rows if row.get("status") == "ready"]
    required_scenarios = {"baseIntact", "erosionCase", "killChainCase"}

    gates = [
        _qualityGateRow(
            "explicitThesis",
            bool(thesis_rows) and thesis_rows[0].get("status") == "ok",
            required="user thesis text or explicit assumptions",
            evidence=f"thesisStatus={thesis_rows[0].get('status') if thesis_rows else 'missing'}",
            failure_mode="no explicit thesis means the pack can only ask for input",
            next_action="collect thesis before building scenarios",
        ),
        _qualityGateRow(
            "sourceBreadth",
            len(ok_datasets) >= 4,
            required="at least four L1/L1.5 evidence sets",
            evidence=f"okDatasets={len(ok_datasets)}/{len(coverage_rows)}",
            failure_mode="single-source premortem becomes narrative",
            next_action="add Company.panel, filing, gather, or scan rows",
        ),
        _qualityGateRow(
            "assumptionDepth",
            sum(1 for row in assumption_rows if row.get("status") != "missing") >= 3,
            required="three or more testable assumptions",
            evidence=f"assumptions={len(assumption_rows)}",
            failure_mode="one broad claim cannot support a kill-chain",
            next_action="split thesis into growth, margin, cash, balance-sheet, or event assumptions",
        ),
        _qualityGateRow(
            "fragilityDetected",
            bool(active_fragility),
            required="at least one raw-data fragility or watch item",
            evidence=f"activeFragilities={len(active_fragility)}",
            failure_mode="no weak point means no kill-chain path",
            next_action="refresh statements, market rows, consensus, or scan primitives",
        ),
        _qualityGateRow(
            "triggerConnected",
            bool(active_triggers),
            required="triggerCatalog has watch/risk trigger",
            evidence=f"activeTriggers={len(active_triggers)}",
            failure_mode="fragility without a trigger cannot become a scenario",
            next_action="bind metric, filing, or scan trigger to the thesis",
        ),
        _qualityGateRow(
            "propagationConnected",
            bool(active_paths) and all(row.get("affectedAssumption") for row in active_paths),
            required="trigger to mechanism to assumption path",
            evidence=f"activePaths={len(active_paths)}",
            failure_mode="trigger list without mechanism is not an analysis skill",
            next_action="show triggerId, mechanism, affectedAssumption, tripwire together",
        ),
        _qualityGateRow(
            "tripwireOperational",
            bool(active_tripwires) and all(row.get("threshold") and row.get("action") for row in tripwire_rows),
            required="threshold and action for active tripwires",
            evidence=f"activeTripwires={len(active_tripwires)}",
            failure_mode="open risk without a threshold cannot be monitored",
            next_action="add threshold/action rows before answering",
        ),
        _qualityGateRow(
            "falsifierOpen",
            bool(open_falsifiers),
            required="open counter-evidence ledger",
            evidence=f"openFalsifiers={len(open_falsifiers)}",
            failure_mode="pre-mortem without counter-evidence becomes confirmation bias",
            next_action="state the exact evidence that would rescue the thesis",
        ),
        _qualityGateRow(
            "scenarioComplete",
            required_scenarios <= scenarios and "missing" not in scenario_statuses,
            required="baseIntact, erosionCase, killChainCase all active",
            evidence=f"scenarios={','.join(sorted(scenarios))}; statuses={','.join(sorted(scenario_statuses))}",
            failure_mode="storyboard that misses erosion or kill case is incomplete",
            next_action="complete all three scenarios before final answer",
        ),
        _qualityGateRow(
            "visualBindingReady",
            bool(visual_rows) and len(ready_visuals) == len(visual_rows),
            required="all selected observed viz refs are ready",
            evidence=f"readyVisuals={len(ready_visuals)}/{len(visual_rows)}",
            failure_mode="chart without bound table/value refs hides weak evidence",
            next_action="emit only ready visualRefs or fall back to tables",
        ),
    ]
    for order, row in enumerate(gates, start=1):
        row["order"] = order
    return gates


def _qualityGateRow(
    gate: str,
    passed: bool,
    *,
    required: str,
    evidence: str,
    failure_mode: str,
    next_action: str,
) -> dict[str, Any]:
    return {
        "gate": gate,
        "status": "ok" if passed else "risk",
        "required": required,
        "evidence": evidence,
        "failureMode": failure_mode,
        "nextAction": "preserve in answer" if passed else next_action,
    }


def _qualityScore(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    passed = sum(1 for row in rows if row.get("status") == "ok")
    return round(passed * 100 / len(rows))


def _qualityGateStatus(score: int) -> str:
    if score >= 90:
        return "flagshipReady"
    if score >= 70:
        return "operatorReview"
    return "weak"


def _decisionStatus(thesis_rows: list[dict[str, Any]], quality_gate_status: str) -> str:
    if quality_gate_status == "flagshipReady":
        return "usable"
    if not thesis_rows or thesis_rows[0].get("status") != "ok":
        return "needsThesis"
    if quality_gate_status == "operatorReview":
        return "needsReview"
    return "needsEvidence"


def _deepDiveRows(
    *,
    kill_score: int,
    quality_score: int,
    quality_gate_status: str,
    decision_status: str,
    **tables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for order, (name, table) in enumerate(tables.items(), start=1):
        status = _maxStatus(table)
        rows.append(
            {
                "order": order,
                "step": name,
                "status": status,
                "rowCount": len(table),
                "evidence": evidenceSummary(table),
                "nextAction": _nextAction(name, status),
            }
        )
    rows.append(
        {
            "order": len(rows) + 1,
            "step": "finalDecision",
            "status": _finalDecisionStatus(kill_score, quality_gate_status, decision_status),
            "rowCount": len(rows),
            "evidence": (
                f"killRiskScore={kill_score}; premortemQualityScore={quality_score}; "
                f"qualityGateStatus={quality_gate_status}; decisionStatus={decision_status}"
            ),
            "nextAction": "answer with assumption, propagation path, tripwire, and falsifier together",
        }
    )
    return rows


def _finalDecisionStatus(kill_score: int, quality_gate_status: str, decision_status: str) -> str:
    if quality_gate_status == "weak":
        return "risk"
    if quality_gate_status == "operatorReview" or kill_score:
        return "watch"
    return "ok" if decision_status == "usable" else "missing"


def _statementPanel(statements: Mapping[str, pl.DataFrame]) -> list[dict[str, Any]]:
    periods = _periods(statements.values())
    rows: list[dict[str, Any]] = []
    for period in periods[:6]:
        row: dict[str, Any] = {"period": period}
        for metric, aliases in _ACCOUNT_ALIASES.items():
            row[metric] = _valueForMetric(statements, aliases, period)
        rows.append(row)
    return rows


def _periods(frames: Iterable[pl.DataFrame]) -> list[str]:
    found: list[str] = []
    for frame in frames:
        if not isinstance(frame, pl.DataFrame):
            continue
        for col in frame.columns:
            value = str(col)
            if re.match(r"^\d{4}(?:Q[1-4])?$", value) and value not in found:
                found.append(value)
    return sorted(found, reverse=True)


def _valueForMetric(statements: Mapping[str, pl.DataFrame], aliases: tuple[str, ...], period: str) -> float | None:
    values: list[float] = []
    for frame in statements.values():
        value = _valueFromFrame(frame, aliases, period)
        if value is not None:
            values.append(value)
    if not values:
        return None
    return sum(values) if aliases == _ACCOUNT_ALIASES["debt"] else values[0]


def _valueFromFrame(frame: pl.DataFrame, aliases: tuple[str, ...], period: str) -> float | None:
    if not isinstance(frame, pl.DataFrame) or period not in frame.columns:
        return None
    label_cols = [col for col in ("snakeId", "항목", "account", "label") if col in frame.columns]
    for label_col in label_cols:
        for raw in frame.select([label_col, period]).to_dicts():
            label = _compact(str(raw.get(label_col) or ""))
            if any(_compact(alias) in label for alias in aliases):
                return toFloat(raw.get(period))
    return None


def _filingCategory(text: str) -> str | None:
    for category, keywords in _FILING_RISK_KEYWORDS.items():
        if _matchesAny(text, keywords):
            return category
    return None


def _matchesAny(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    compacted = _compact(text)
    return any(keyword.lower() in lowered or _compact(keyword) in compacted for keyword in keywords)


def _linkedAssumption(trigger: str, assumption_ids: list[str]) -> str:
    mapping = {
        "revenue": "revenueGrowth",
        "operating": "marginDurability",
        "cash": "cashConversion",
        "debt": "balanceSheet",
        "price": "valuationSupport",
        "consensus": "eventFollowThrough",
        "filing": "governanceTrust",
    }
    lowered = trigger.lower()
    for token, assumption_id in mapping.items():
        if token in lowered and assumption_id in assumption_ids:
            return assumption_id
    return assumption_ids[0]


def _mechanismFor(trigger_id: str) -> str:
    if "revenue" in trigger_id:
        return "growth disappointment compresses margin and expectation"
    if "operating" in trigger_id:
        return "margin pressure invalidates operating leverage"
    if "cash" in trigger_id:
        return "earnings fail to convert into cash"
    if "debt" in trigger_id or "cashToDebt" in trigger_id:
        return "balance sheet narrows response options"
    if "price" in trigger_id or "flow" in trigger_id:
        return "market reflexivity tightens the thesis clock"
    if "filing" in trigger_id:
        return "new filing changes the thesis evidence base"
    if "consensus" in trigger_id:
        return "expectation drift moves against the thesis"
    return "trigger propagates through the weakest open assumption"


def _tripwireFor(trigger_id: str) -> str:
    if "revenue" in trigger_id:
        return "revenueGrowth < 0 or >35% without cash support"
    if "operating" in trigger_id:
        return "operating margin change < -2pp"
    if "cash" in trigger_id:
        return "CFO/net income < 0.85"
    if "debt" in trigger_id:
        return "debt/equity > 0.8 or cash/debt < 0.4"
    if "price" in trigger_id:
        return "daily price reaction < -4%"
    if "flow" in trigger_id:
        return "foreign+institution net flow <= 0"
    if "consensus" in trigger_id:
        return "operating profit consensus revision < -5%"
    return "trigger remains watch/risk after evidence refresh"


def _thresholdFor(metric: str) -> str:
    return {
        "revenueGrowth": "risk < -10%; watch < 0 or >35%",
        "operatingMarginTrend": "risk < -5pp; watch < -2pp",
        "cashConversion": "risk < 0.60; watch < 0.85",
        "debtToEquity": "risk > 1.50; watch > 0.80",
        "cashToDebt": "risk < 0.20; watch < 0.40",
        "priceReaction": "risk < -8%; watch < -4%",
        "flowPressure": "risk < 0",
        "consensusRevision": "risk < -12%; watch < -5%",
    }.get(metric, "watch/risk status")


def _tripwireAction(metric: str, status: str) -> str:
    if status in {"watch", "risk"}:
        return f"open falsifier for {metric} before defending the thesis"
    if status == "missing":
        return f"supply raw rows for {metric}"
    return "monitor; no kill-chain action"


def _counterEvidenceFor(trigger_id: str) -> str:
    if "revenue" in trigger_id:
        return "contract backlog, seasonality, or one-off shipment timing"
    if "operating" in trigger_id:
        return "input cost pass-through or mix shift with margin recovery"
    if "cash" in trigger_id:
        return "working-capital timing reversal or one-off tax/payment item"
    if "debt" in trigger_id or "cashToDebt" in trigger_id:
        return "refinancing, unused credit line, or non-recourse debt detail"
    if "price" in trigger_id or "flow" in trigger_id:
        return "market-wide selloff or stale market data"
    if "filing" in trigger_id:
        return "routine filing, amendment without economic effect, or duplicated headline"
    if "consensus" in trigger_id:
        return "single stale broker update or unit/currency restatement"
    return "independent evidence that trigger is not thesis-relevant"


def _evidenceNeeded(assumption_id: str) -> str:
    return {
        "revenueGrowth": "IS revenue panel and consensus rows",
        "marginDurability": "IS operating profit panel",
        "cashConversion": "CF CFO and IS net income",
        "balanceSheet": "BS cash/debt/equity rows",
        "valuationSupport": "price rows and optional valuation primitive",
        "eventFollowThrough": "filings/news/consensus follow-through",
        "macroTolerance": "gather.macro or scan.market primitive",
        "governanceTrust": "filing/governance/audit primitive rows",
    }.get(assumption_id, "sourceCoverageAudit rows")


def _killRiskScore(*tables: list[dict[str, Any]]) -> int:
    score = 0
    for table in tables:
        for row in table:
            status = str(row.get("status") or "")
            score += 3 if status == "risk" else 1 if status == "watch" else 0
    return score


def _sortRows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: str(_dateOf(row) or ""), reverse=True)


def _dateOf(row: Mapping[str, Any]) -> str | None:
    value = firstValue(row, *_DATE_KEYS)
    return str(value) if value is not None else None


def _latestDate(*items: Any) -> str | None:
    """이 판독기가 날짜로 보는 key 목록을 공유 접근자에 넘긴다."""
    return latestDate(items, keys=_DATE_KEYS)


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 4)


def _maxStatus(rows: list[dict[str, Any]]) -> str:
    rank = {"missing": 0, "blocked": 0, "ok": 1, "ready": 1, "untested": 1, "watch": 2, "risk": 3}
    if not rows:
        return "missing"
    return max((str(row.get("status") or "missing") for row in rows), key=lambda item: rank.get(item, 0))


def _nextAction(step: str, status: str) -> str:
    if status in {"watch", "risk"}:
        return f"{step} counter-evidence and tripwire refresh"
    if status == "missing":
        return f"supply L1/L1.5 rows for {step}"
    return "preserve evidence refs and continue"


def _compact(text: str) -> str:
    return re.sub(r"[\s,()\-_/·]", "", str(text or "").lower())


__all__ = ["buildThesisKillChainMemo"]
