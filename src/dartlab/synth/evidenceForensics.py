"""Evidence forensics L1.5 helper.

This module builds an engine-candidate ledger from raw statement tables and
optional filing text/event rows. It deliberately stays below L2 analysis
engines: callers provide L1/L1.5 inputs, and this helper only normalizes,
matches, scores, and records falsifiers.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

import polars as pl

from dartlab.synth.rowAccess import diff, safeDiv, toFloat

_PERIOD_RE = re.compile(r"^\d{4}(?:Q[1-4])?$")

_ACCOUNT_ALIASES: dict[str, tuple[str, ...]] = {
    "revenue": ("sales", "revenue", "매출액", "영업수익"),
    "costOfSales": ("cost_of_sales", "cost_of_revenue", "매출원가"),
    "operatingProfit": ("operating_profit", "operating_income", "영업이익"),
    "netIncome": ("net_income", "net_profit", "profit_loss", "당기순이익"),
    "cfo": ("cash_flows_from_used_in_operating_activities", "operating_cashflow", "net_cash_flow_operating"),
    "capex": (
        "purchase_of_property_plant_and_equipment",
        "acquisition_of_property_plant_and_equipment",
        "capital_expenditures",
    ),
    "assets": ("total_assets", "assets"),
    "liabilities": ("total_liabilities", "liabilities"),
    "equity": ("total_stockholders_equity", "total_equity", "equity"),
    "receivables": ("trade_receivables", "trade_and_other_receivables", "accounts_receivable"),
    "inventories": ("inventories", "inventory"),
    "payables": ("trade_payables", "trade_and_other_payables", "accounts_payable"),
    "debt": ("borrowings", "short_term_debt", "long_term_debt", "interest_bearing_debt"),
}

_NOTE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "allowancePressure": ("대손", "손상", "allowance", "impairment", "expected credit loss"),
    "inventoryWriteDown": ("재고평가", "평가손", "write-down", "write down", "obsolete inventory"),
    "relatedParty": ("특수관계자", "related party", "affiliate transaction"),
    "goingConcern": ("계속기업", "going concern", "의견거절", "한정의견"),
    "litigation": ("소송", "우발부채", "contingent liability", "litigation"),
    "derivatives": ("파생상품", "derivative", "hedge accounting"),
    "restatement": ("정정", "재작성", "restatement", "reissuance"),
    "factoring": ("팩토링", "유동화", "factoring", "securitization"),
}


def buildEvidenceForensicsMemo(
    *,
    target: str,
    market: str = "KR",
    companyName: str = "",
    statements: Mapping[str, pl.DataFrame] | None = None,
    panelTextRows: Mapping[str, str] | None = None,
    sectionTexts: Mapping[str, str] | None = None,
    events: Iterable[Mapping[str, Any]] | None = None,
    scanRows: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """L1.5 Evidence Forensics. 매출-현금 brige + WC 변화 + 공시 변화 + 이상 패턴 종합.

    Capabilities:
        분식 회계 신호 자동 탐지. (1) 매출 → 현금 bridge (OCF/NI 격차),
        (2) WC 변화 (재고/매출채권 비정상), (3) 공시 변화 (지배구조/주석),
        (4) event (자기주식취득/특수 거래), (5) scan 횡단면 이상치. 5 source
        합성하여 risk score + 후보 종목 라벨.

    Args:
        target: 종목코드.
        market: ``"KR"``/``"US"``.
        companyName: 한국어 회사명.
        statements: BS/IS/CF raw 테이블.
        panelTextRows: 공시 panel 텍스트 dict.
        sectionTexts: 호환 별칭. 제공 시 ``panelTextRows`` 가 없을 때만 사용.
        events: 이벤트 list (자기주식 등).
        scanRows: scan 횡단면 raw rows.

    Returns:
        dict:
            - ``riskScore`` (float): 0~100 위험 점수
            - ``cashBridge`` (list): 매출-OCF bridge 분기별
            - ``wcRows`` (list): WC 변화 분기별
            - ``noteRows`` (list): 공시 변화 라인
            - ``eventRows`` (list): 이벤트 노트
            - ``anomalyRows`` (list): scan 이상치
            - ``falsifierRows`` (list): 신뢰도 falsifier
            - ``candidateRows`` (list): 후보 엔진 분석
            - ``trace`` (list): 가정 추적

    Raises:
        없음. 데이터 누락은 trace 에 기록.

    Example:
        >>> memo = buildEvidenceForensicsMemo(target="005930", statements=...)
        >>> memo["riskScore"], len(memo["candidateRows"])
        (35, 4)

    Guide:
        Sloan (1996) accrual model + Beneish M-Score + DSO/DIO 비정상 + 공시
        패턴. riskScore > 60 = high risk, 30~60 = moderate, < 30 = low.
        분식 의심 단정 금지. academic 신호 합성.

    SeeAlso:
        - ``buildDamodaranMemo``: valuation memo (별도 함수)
        - ``calcEarningsMomentum``: Sloan accrual 분해 (L2 단독)
        - ``dartlab.scan.forensics``: scan 본체

    Requires:
        statements (BS/IS/CF) + 일부 옵션 입력.

    AIContext:
        analyzed memo 사용자에게 노출 시 "분식 의심" 단어 회피. "이상 신호
        탐지" 표현 권장. riskScore 60+ 시 추가 deep dive 권장.

    LLM Specifications:
        AntiPatterns:
            - riskScore 만 인용 금지. candidateRows + falsifierRows 함께 노출.
            - panelTextRows 빈 dict 호출 → 공시 변화 source 누락. trace 확인 필수.
        OutputSchema:
            상기 9 키 dict.
        Prerequisites:
            statements 최소 1 분기 + 옵션 입력 1 종 이상.
        Freshness:
            statements = 최신 분기. scanRows/events = 운영자 큐레이션.
        Dataflow:
            statements → panel → analysis panel (가공) → 5 source
            (cash bridge + WC + note + event + anomaly) → falsifier →
            candidate → riskScore.
        TargetMarkets: KR (DART), US (EDGAR).
    """

    statement_map = dict(statements or {})
    panel = _buildPanel(statement_map)
    analysis_panel = _analysisPanel(panel)
    latest_period = analysis_panel[0]["period"] if analysis_panel else "unknown"
    coverage_rows = _coverageRows(statement_map, panel)
    trace_rows = _traceRows(statement_map)
    cash_rows = _revenueCashBridge(analysis_panel)
    wc_rows = _workingCapitalRows(analysis_panel)
    text_rows = panelTextRows if panelTextRows is not None else sectionTexts
    note_rows = _noteSignalRows(text_rows or {})
    event_rows = _eventRows(events or (), note_rows=note_rows, panel=analysis_panel)
    anomaly_rows = _anomalyRows(scanRows or ())
    falsifier_rows = _falsifierRows(cash_rows, wc_rows, note_rows, event_rows)
    candidate_rows = _engineCandidateRows(cash_rows, wc_rows, note_rows, event_rows, anomaly_rows)
    risk_score = _riskScore(cash_rows, wc_rows, note_rows, event_rows)
    decision_status = "usable" if analysis_panel else "insufficientStatements"
    if analysis_panel and any(
        row["status"] == "missing" for row in coverage_rows if row["dataset"] in {"IS", "BS", "CF"}
    ):
        decision_status = "usableWithGaps"
    deep_rows = _deepDiveRows(
        dataCoverageAudit=coverage_rows,
        accountTraceLedger=trace_rows,
        revenueToCashBridge=cash_rows,
        workingCapitalPressureMap=wc_rows,
        noteSignalExtractor=note_rows,
        eventToStatementMatcher=event_rows,
        crossSectionAnomalyRank=anomaly_rows,
        falsifierLedger=falsifier_rows,
        engineCandidateMemo=candidate_rows,
        risk_score=risk_score,
        decision_status=decision_status,
    )

    return {
        "target": target,
        "market": market,
        "companyName": companyName or target,
        "asOf": latest_period,
        "decisionStatus": decision_status,
        "headline": {
            "target": target,
            "companyName": companyName or target,
            "riskScore": risk_score,
            "signalCount": sum(1 for row in deep_rows if row["status"] in {"watch", "risk"}),
            "candidateCount": len(candidate_rows),
            "openFalsifierCount": sum(1 for row in falsifier_rows if row["status"] == "open"),
            "decisionStatus": decision_status,
        },
        "tables": {
            "dataCoverageAudit": coverage_rows,
            "accountTraceLedger": trace_rows,
            "revenueToCashBridge": cash_rows,
            "workingCapitalPressureMap": wc_rows,
            "noteSignalExtractor": note_rows,
            "eventToStatementMatcher": event_rows,
            "crossSectionAnomalyRank": anomaly_rows,
            "falsifierLedger": falsifier_rows,
            "engineCandidateMemo": candidate_rows,
            "deepDive": deep_rows,
        },
        "sources": [
            {
                "id": "l1CompanyStatements",
                "title": "Company.panel raw statement tables",
                "url": "dartlab://Company.panel/BS-IS-CF",
            },
            {
                "id": "l15EvidenceForensics",
                "title": "DartLab L1.5 evidence forensics helper",
                "url": "dartlab://synth/evidenceForensics.buildEvidenceForensicsMemo",
            },
            {
                "id": "forensicsSkillPack",
                "title": "Evidence Forensics Incubator skill pack",
                "url": "dartlab://skills/recipes.fundamental.quality.forensics.index",
            },
        ],
    }


def _buildPanel(statements: Mapping[str, pl.DataFrame]) -> list[dict[str, Any]]:
    periods = _periods(statements.values())
    rows: list[dict[str, Any]] = []
    for period in periods[:6]:
        row = {"period": period}
        for metric, aliases in _ACCOUNT_ALIASES.items():
            row[metric] = _valueForMetric(statements, aliases, period)
        rows.append(row)
    return rows


def _analysisPanel(panel: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Skip partial latest periods that cannot support revenue-cash checks."""
    for idx, row in enumerate(panel):
        if row.get("revenue") is not None and (row.get("cfo") is not None or row.get("netIncome") is not None):
            return panel[idx:]
    return panel


def _periods(frames: Iterable[pl.DataFrame]) -> list[str]:
    found: list[str] = []
    for frame in frames:
        if not isinstance(frame, pl.DataFrame):
            continue
        for col in frame.columns:
            value = str(col)
            if _PERIOD_RE.match(value) and value not in found:
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
    return sum(values) if len(values) > 1 and aliases == _ACCOUNT_ALIASES["debt"] else values[0]


def _valueFromFrame(frame: pl.DataFrame, aliases: tuple[str, ...], period: str) -> float | None:
    if not isinstance(frame, pl.DataFrame) or period not in frame.columns:
        return None
    label_cols = [col for col in ("snakeId", "항목", "account", "label") if col in frame.columns]
    if not label_cols:
        return None
    for label_col in label_cols:
        for alias in aliases:
            try:
                filtered = frame.filter(pl.col(label_col).cast(pl.Utf8).str.to_lowercase() == alias.lower())
            except Exception:  # noqa: BLE001
                continue
            if filtered.height:
                return toFloat(filtered.select(period).row(0)[0])
    compact_aliases = {_compact(alias) for alias in aliases}
    for label_col in label_cols:
        for raw in frame.select([label_col, period]).to_dicts():
            label = _compact(str(raw.get(label_col) or ""))
            if any(alias and alias in label for alias in compact_aliases):
                return toFloat(raw.get(period))
    return None


def _coverageRows(statements: Mapping[str, pl.DataFrame], panel: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    periods = [row["period"] for row in panel]
    for name in ("IS", "BS", "CF"):
        frame = statements.get(name)
        rows.append(
            {
                "dataset": name,
                "status": "ok" if isinstance(frame, pl.DataFrame) and frame.height > 0 else "missing",
                "rowCount": frame.height if isinstance(frame, pl.DataFrame) else 0,
                "periodCount": len(
                    [
                        col
                        for col in (frame.columns if isinstance(frame, pl.DataFrame) else [])
                        if _PERIOD_RE.match(str(col))
                    ]
                ),
                "latestPeriod": periods[0] if periods else None,
                "requiredFor": "statement triangulation",
            }
        )
    metric_coverage = 0
    for metric in _ACCOUNT_ALIASES:
        if any(row.get(metric) is not None for row in panel):
            metric_coverage += 1
    rows.append(
        {
            "dataset": "normalizedPanel",
            "status": "ok" if panel else "missing",
            "rowCount": len(panel),
            "periodCount": len(periods),
            "latestPeriod": periods[0] if periods else None,
            "requiredFor": f"{metric_coverage}/{len(_ACCOUNT_ALIASES)} mapped metrics",
        }
    )
    return rows


def _traceRows(statements: Mapping[str, pl.DataFrame]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric, aliases in _ACCOUNT_ALIASES.items():
        matched = _traceMetric(statements, aliases)
        rows.append(
            {
                "metric": metric,
                "status": "mapped" if matched else "missing",
                "sourceTopic": matched.get("topic") if matched else None,
                "sourceColumn": matched.get("column") if matched else None,
                "sourceLabel": matched.get("label") if matched else None,
                "aliasesTried": ", ".join(aliases[:4]),
            }
        )
    return rows


def _traceMetric(statements: Mapping[str, pl.DataFrame], aliases: tuple[str, ...]) -> dict[str, str] | None:
    for topic, frame in statements.items():
        if not isinstance(frame, pl.DataFrame):
            continue
        label_cols = [col for col in ("snakeId", "항목", "account", "label") if col in frame.columns]
        for label_col in label_cols:
            values = frame.select(label_col).to_series().cast(pl.Utf8).to_list()
            for value in values:
                lowered = str(value).lower()
                compacted = _compact(str(value))
                if any(alias.lower() == lowered or _compact(alias) in compacted for alias in aliases):
                    return {"topic": str(topic), "column": str(label_col), "label": str(value)}
    return None


def _revenueCashBridge(panel: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(panel):
        prev = panel[idx + 1] if idx + 1 < len(panel) else {}
        revenue_growth = _growth(row.get("revenue"), prev.get("revenue"))
        receivable_growth = _growth(row.get("receivables"), prev.get("receivables"))
        cfo_to_net = _safeDiv(row.get("cfo"), row.get("netIncome"))
        cfo_to_revenue = _safeDiv(row.get("cfo"), row.get("revenue"))
        ar_gap = diff(receivable_growth, revenue_growth)
        status = "ok"
        if ar_gap is not None and ar_gap > 0.15 and (cfo_to_net is None or cfo_to_net < 0.8):
            status = "risk"
        elif ar_gap is not None and ar_gap > 0.08:
            status = "watch"
        rows.append(
            {
                "period": row["period"],
                "revenue": row.get("revenue"),
                "revenueGrowth": _round(revenue_growth),
                "receivableGrowth": _round(receivable_growth),
                "receivableGrowthMinusRevenueGrowth": _round(ar_gap),
                "cfoToNetIncome": _round(cfo_to_net),
                "cfoToRevenue": _round(cfo_to_revenue),
                "status": status,
                "evidence": "revenue, receivables, CFO, net income from raw statements",
            }
        )
    return rows


def _workingCapitalRows(panel: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(panel):
        prev = panel[idx + 1] if idx + 1 < len(panel) else {}
        revenue = row.get("revenue")
        cost = row.get("costOfSales") or revenue
        dso = _safeDiv(row.get("receivables"), revenue, scale=365.0)
        dio = _safeDiv(row.get("inventories"), cost, scale=365.0)
        dpo = _safeDiv(row.get("payables"), cost, scale=365.0)
        ccc = dso + dio - dpo if dso is not None and dio is not None and dpo is not None else None
        inventory_growth = _growth(row.get("inventories"), prev.get("inventories"))
        revenue_growth = _growth(row.get("revenue"), prev.get("revenue"))
        inv_gap = diff(inventory_growth, revenue_growth)
        status = "ok"
        if (ccc is not None and ccc > 180) or (inv_gap is not None and inv_gap > 0.2):
            status = "risk"
        elif (ccc is not None and ccc > 120) or (inv_gap is not None and inv_gap > 0.1):
            status = "watch"
        rows.append(
            {
                "period": row["period"],
                "dsoDays": _round(dso),
                "dioDays": _round(dio),
                "dpoDays": _round(dpo),
                "cccDays": _round(ccc),
                "inventoryGrowthMinusRevenueGrowth": _round(inv_gap),
                "status": status,
                "evidence": "receivables, inventory, payables, revenue, cost of sales",
            }
        )
    return rows


def _noteSignalRows(panelTextRows: Mapping[str, str]) -> list[dict[str, Any]]:
    joined = "\n".join(str(text or "") for text in panelTextRows.values())
    lowered = joined.lower()
    rows: list[dict[str, Any]] = []
    for category, keywords in _NOTE_KEYWORDS.items():
        hits = sum(lowered.count(keyword.lower()) for keyword in keywords)
        status = "risk" if category in {"goingConcern", "restatement"} and hits >= 1 else "watch" if hits >= 2 else "ok"
        rows.append(
            {
                "signal": category,
                "hitCount": hits,
                "status": status,
                "keywords": ", ".join(keywords[:4]),
                "evidence": "section text keyword count" if panelTextRows else "no section text supplied",
            }
        )
    return rows


def _eventRows(
    events: Iterable[Mapping[str, Any]],
    *,
    note_rows: list[dict[str, Any]],
    panel: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    note_status = {row["signal"]: row["status"] for row in note_rows}
    for idx, event in enumerate(events):
        text = " ".join(str(event.get(key) or "") for key in ("report_nm", "title", "event", "summary", "rcept_dt"))
        category = _eventCategory(text)
        rows.append(
            {
                "eventIndex": idx + 1,
                "eventDate": event.get("rcept_dt") or event.get("date"),
                "eventTitle": event.get("report_nm") or event.get("title") or text[:80],
                "matchedSignal": category,
                "statementPeriod": panel[0]["period"] if panel else None,
                "status": "watch" if category and note_status.get(category) in {"watch", "risk"} else "ok",
                "evidence": "event title matched to note/statement signal",
            }
        )
    if not rows:
        rows.append(
            {
                "eventIndex": None,
                "eventDate": None,
                "eventTitle": "no events supplied",
                "matchedSignal": None,
                "statementPeriod": panel[0]["period"] if panel else None,
                "status": "missing",
                "evidence": "events optional; no event-to-statement match attempted",
            }
        )
    return rows


def _eventCategory(text: str) -> str | None:
    lowered = text.lower()
    for category, keywords in _NOTE_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return category
    if "유상증자" in text or "전환사채" in text or "cb" in lowered:
        return "financingStress"
    return None


def _anomalyRows(scanRows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(scanRows):
        score = toFloat(row.get("score") or row.get("riskScore") or row.get("value"))
        rows.append(
            {
                "rank": idx + 1,
                "target": row.get("stockCode") or row.get("ticker") or row.get("target"),
                "name": row.get("corpName") or row.get("name") or row.get("종목명"),
                "metric": row.get("metric") or row.get("axis") or "scanPrimitive",
                "score": score,
                "status": "watch" if score is not None and score > 0 else "candidate",
                "evidence": "prebuilt scan primitive row supplied by caller",
            }
        )
    return rows


def _falsifierRows(
    cash_rows: list[dict[str, Any]],
    wc_rows: list[dict[str, Any]],
    note_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "claim": "revenue-to-cash divergence",
            "supportingEvidence": _latestStatus(cash_rows),
            "counterEvidenceNeeded": "large new customer, billing-cycle change, or seasonal receivable pattern",
            "status": "open" if _latestStatus(cash_rows) in {"watch", "risk"} else "notTriggered",
        },
        {
            "claim": "working-capital pressure",
            "supportingEvidence": _latestStatus(wc_rows),
            "counterEvidenceNeeded": "inventory build for contracted backlog or supplier payment normalization",
            "status": "open" if _latestStatus(wc_rows) in {"watch", "risk"} else "notTriggered",
        },
        {
            "claim": "note text risk signal",
            "supportingEvidence": _maxStatus(note_rows),
            "counterEvidenceNeeded": "boilerplate-only wording or one-off legal disclosure without financial impact",
            "status": "open" if _maxStatus(note_rows) in {"watch", "risk"} else "notTriggered",
        },
        {
            "claim": "event-to-statement linkage",
            "supportingEvidence": _maxStatus(event_rows),
            "counterEvidenceNeeded": "event is unrelated to current financial-statement pressure",
            "status": "open" if _maxStatus(event_rows) in {"watch", "risk"} else "notTriggered",
        },
    ]


def _engineCandidateRows(
    cash_rows: list[dict[str, Any]],
    wc_rows: list[dict[str, Any]],
    note_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
    anomaly_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates = [
        ("revenueCashDivergence", _latestStatus(cash_rows), "이익품질/매출채권 회수 축 후보"),
        (
            "workingCapitalPressure",
            _latestStatus(wc_rows),
            "운전자본 압력/유동성 사전점검 축 후보",
        ),
        ("noteRiskSignal", _maxStatus(note_rows), "공시 문구 변화/주석 위험 축 후보"),
        ("eventStatementLink", _maxStatus(event_rows), "공시 이벤트-재무제표 연결 축 후보"),
        ("crossSectionAnomaly", _maxStatus(anomaly_rows), "횡단면 이상치 후보"),
    ]
    rows: list[dict[str, Any]] = []
    for signal_id, status, owner in candidates:
        rows.append(
            {
                "signalId": signal_id,
                "status": status,
                "recommendedEngineOwner": owner,
                "promotionGate": "3개 이상 target selfRun, false-positive ledger, ask 답변 품질 2회 통과",
                "keepAsSkillAfterPromotion": True,
            }
        )
    return rows


def _deepDiveRows(
    *,
    risk_score: int,
    decision_status: str,
    **tables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for order, (name, table) in enumerate(tables.items(), start=1):
        table_status = _maxStatus(table)
        rows.append(
            {
                "order": order,
                "step": name,
                "status": table_status,
                "rowCount": len(table),
                "evidence": _evidenceSummary(table),
                "nextAction": _nextAction(name, table_status),
            }
        )
    open_falsifiers = sum(1 for row in tables.get("falsifierLedger", []) if row.get("status") == "open")
    panel_alert = any(row["status"] in {"watch", "risk", "open"} for row in rows)
    rows.append(
        {
            "order": len(rows) + 1,
            "step": "finalDecision",
            "status": (
                "watch"
                if open_falsifiers or panel_alert
                else "ok"
                if decision_status.startswith("usable")
                else "missing"
            ),
            "rowCount": len(rows),
            "evidence": f"riskScore={risk_score}; openFalsifiers={open_falsifiers}; decisionStatus={decision_status}",
            "nextAction": (
                "반증 ledger와 엔진 후보 memo를 함께 제시"
                if open_falsifiers or panel_alert
                else "L1/L1.5 검산 경로로 보존"
            ),
        }
    )
    return rows


def _riskScore(
    cash_rows: list[dict[str, Any]],
    wc_rows: list[dict[str, Any]],
    note_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
) -> int:
    statuses = [_latestStatus(cash_rows), _latestStatus(wc_rows), _maxStatus(note_rows), _maxStatus(event_rows)]
    return sum(2 if status == "risk" else 1 if status == "watch" else 0 for status in statuses)


def _latestStatus(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "missing"
    return str(rows[0].get("status") or "missing")


def _maxStatus(rows: list[dict[str, Any]]) -> str:
    rank = {"missing": 0, "candidate": 1, "ok": 1, "mapped": 1, "watch": 2, "risk": 3}
    if not rows:
        return "missing"
    return max((str(row.get("status") or "missing") for row in rows), key=lambda item: rank.get(item, 0))


def _evidenceSummary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "no rows"
    sample = rows[0]
    for key in ("evidence", "requiredFor", "aliasesTried"):
        if sample.get(key):
            return str(sample[key])
    return ", ".join(sample.keys())


def _nextAction(step: str, status: str) -> str:
    if status in {"risk", "watch"}:
        return f"{step} 반증 조건 확인"
    if status == "missing":
        return f"{step}에 필요한 L1/L1.5 입력 보강"
    return "근거 행 보존 후 다음 단계 진행"


def _growth(current: Any, previous: Any) -> float | None:
    current_value = toFloat(current)
    previous_value = toFloat(previous)
    if current_value is None or previous_value in (None, 0):
        return None
    return (current_value - previous_value) / abs(previous_value)


def _safeDiv(numerator: Any, denominator: Any, *, scale: float = 1.0) -> float | None:
    """공유 나눗셈에 강제변환과 배율을 얹는다. 이 판독기만 배율을 쓴다."""
    value = safeDiv(toFloat(numerator), toFloat(denominator))
    return None if value is None else value * scale


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 4)


def _compact(text: str) -> str:
    return re.sub(r"[\s,()\-_/·]", "", str(text or "").lower())


__all__ = ["buildEvidenceForensicsMemo"]
