"""PeerCompareN — N (default 5) 종목 wide-format 비교 + peer-internal percentile rank.

마스터 플랜 트랙 1 PR-2 (cryptic-discovering-kettle.md). 옛 max 3 한계 +
peer ranking 부재 회귀 차단. 재무 추출 SSOT 재사용 — companyMetrics.companyMetrics
그대로 호출 (N 처리만 추가) + percentile rank helper 신규. 2~12 종목 단일 비교 도구.

신뢰도 80 (ratio method) — 결정적 비율 계산.

graph 회귀 방지: agent.py 본체·노드 추가 0. LLM 자율 호출 도구.
"""

from __future__ import annotations

from typing import Any

from dartlab.ai.contracts import Ref
from dartlab.core.confidence import baseScore

from .companyMetrics import companyMetrics
from .companyResolve import resolveCompanyOrNone
from .creditBadge import getDcrBadge
from .industryContext import getIndustryBadge
from .types import ToolResult

_MAX_SLOTS = 12
_DEFAULT_METRICS = (
    "revenue",
    "operatingProfit",
    "netIncome",
    "totalAssets",
    "totalEquity",
    "totalLiabilities",
    "debtRatio",
    "roe",
)

# percentile rank 방향 — higher_is_better (높을수록 1.0 에 근접) 인지 lower_is_better 인지.
# 부채는 낮을수록 좋고, ROE 는 높을수록 좋음.
_HIGHER_IS_BETTER: set[str] = {
    "revenue",
    "operatingProfit",
    "netIncome",
    "totalAssets",
    "totalEquity",
    "roe",
}
_LOWER_IS_BETTER: set[str] = {
    "totalLiabilities",
    "debtRatio",
}
_INCOME_METRICS = frozenset({"revenue", "operatingProfit", "netIncome"})


def _calcPercentileRanks(rows: list[dict[str, Any]], metric: str) -> dict[str, float]:
    """주어진 N rows 안에서 metric 별 percentile rank (0.0 ~ 1.0, 1.0 = best).

    metric 이 None / 비숫자인 row 는 제외. higher_is_better 방향 자동 적용.
    반환 dict: stockCode → rank (제외된 row 는 키 부재).
    """
    valid: list[tuple[str, float]] = []
    for r in rows:
        code = r.get("stockCode")
        v = r.get(metric)
        if not code or v is None or not isinstance(v, (int, float)):
            continue
        valid.append((str(code), float(v)))
    if not valid:
        return {}
    reverse = metric in _HIGHER_IS_BETTER  # True 면 큰 값이 best
    sorted_vals = sorted(valid, key=lambda x: x[1], reverse=reverse)
    n = len(sorted_vals)
    out: dict[str, float] = {}
    if n == 1:
        out[sorted_vals[0][0]] = 1.0
        return out
    for i, (code, _v) in enumerate(sorted_vals):
        # rank 1 = best → percentile 1.0, last → 0.0
        out[code] = round(1.0 - (i / (n - 1)), 4)
    return out


def peerCompareN(
    stockCodes: list[str] | str | None = None,
    metrics: list[str] | None = None,
) -> ToolResult:
    """N 종목 비교 + peer-internal percentile rank.

    Capabilities:
        2~12 종목 단일 비교 도구 + peer-internal percentile rank
        (각 metric 별 0.0 ~ 1.0, 1.0 = best). higher_is_better/lower_is_better
        방향 자동 적용. 동종 업종 peer 자동 추가 옵션은 별 PR.

    Parameters
    ----------
    stockCodes : list[str] | str
        2~12 개 종목 코드. 초과 시 앞 12 개만.
    metrics : list[str] | None
        기본 8 종 — revenue, operatingProfit, netIncome, totalAssets, totalEquity,
        totalLiabilities, debtRatio, roe. 일부만 필요 시 명시.

    Returns
    -------
    ToolResult
        - data.stockCodes : list[str]
        - data.metrics : list[str]
        - data.rows : list[dict] — 각 종목 metric + percentileRanks
        - data.badges : list[dict] — dCR + industry
        - data.confidence : 80 (ratio method)
        - refs : tableRef (N × metric wide + percentile)

    Example
    -------
        PeerCompareN(stockCodes=["005930", "000660", "035420", "035720", "207940"])

    Raises
    ------
    없음 — 모든 실패 경로는 ToolResult(ok=False, error=...) 로 반환.

    Guide
    -----
        N=2 도 허용. 각 종목 companyMetrics 호출 (Company.panel 의 IS/BS 1 회씩).
        percentile rank 는 N 종목 *내부* — 외부 sector peer 자동 비교는 후속 PR.

    SeeAlso
    -------
        - companyMetrics.companyMetrics : 재무 추출 SSOT (본 도구가 재사용)
        - industry.taxonomy.getIndustry : sector peer 자동 추가 (후속 PR)
        - DCFValuation : 단일 종목 가치평가

    Requires
    --------
        DART/EDGAR 사전 다운로드 (자동). Company.panel("IS"|"BS") 가 정상 동작.

    AIContext
    ---------
        "5 개 회사 비교", "삼성 vs SK vs LG vs ...", "A·B 비교", "peer 분석" 류 질문에
        본 도구 1 회 호출 (2~12 종목). percentile rank + dCR/industry badge 자동 부착.

    LLM Specifications
    ------------------
        AntiPatterns:
            - stockCodes=[1개만] — peer 비교 의미 0, 단일 종목은 DCFValuation 사용.
            - stockCodes > 12 — 앞 12 개만 처리, 경고.
        OutputSchema:
            rows[i] = {stockCode, corpName, ...metrics, percentileRanks: {metric: 0.0~1.0}}.
        Prerequisites:
            DART/EDGAR 사전 다운로드. Company.panel 정상 동작.
        Freshness:
            분기 결산 발표 후 갱신.
        Dataflow:
            stockCodes → Company × N → IS/BS show × N → companyMetrics × N →
            _calcPercentileRanks × M metric → tableRef.
        TargetMarkets:
            KR (DART) · US (EDGAR). JP (EDINET) 미가용.
    """
    if isinstance(stockCodes, str):
        stockCodes = [stockCodes]
    codes = [str(c).strip() for c in (stockCodes or []) if str(c).strip()]
    if len(codes) < 2:
        return ToolResult(
            False,
            "stockCodes 필수 (2~12 개). 단일 종목은 DCFValuation 사용.",
            error="insufficient_stock_codes",
        )
    if len(codes) > _MAX_SLOTS:
        codes = codes[:_MAX_SLOTS]

    requested_metrics = tuple(metrics) if metrics else _DEFAULT_METRICS

    rows: list[dict[str, Any]] = []
    badges: list[dict[str, Any]] = []
    for code in codes:
        company = resolveCompanyOrNone(code)
        if company is None:
            rows.append({"stockCode": code, "corpName": None, "error": "company_not_resolved"})
            continue
        corpName = str(getattr(company, "corpName", None) or "")
        row: dict[str, Any] = {"stockCode": code, "corpName": corpName}
        row.update(companyMetrics(company))
        rows.append(row)
        badges.append(
            {
                "stockCode": code,
                "corpName": corpName,
                "dcr": getDcrBadge(company),
                "industry": getIndustryBadge(company),
            }
        )

    # peer-internal percentile rank — 각 metric 별 0.0 ~ 1.0.
    rank_by_metric: dict[str, dict[str, float]] = {}
    for m in requested_metrics:
        rank_by_metric[m] = _calcPercentileRanks(rows, m)

    # rows 에 percentileRanks 부착
    for r in rows:
        code = r.get("stockCode")
        if not code:
            continue
        r["percentileRanks"] = {m: rank_by_metric.get(m, {}).get(str(code)) for m in requested_metrics}

    confidence = baseScore("ratio")
    payload = {
        "stockCodes": codes,
        "metrics": list(requested_metrics),
        "rows": rows,
        "badges": badges,
        "confidence": confidence,
        "confidenceMethod": "ratio",
    }
    missingCells = _peerMissingCells(rows, requested_metrics)
    payload["missingCells"] = missingCells
    payload["complete"] = not missingCells and len(rows) == len(codes)
    title = f"{len(codes)} 종목 peer 비교"
    refs = _peerEvidenceRefs(codes, rows, requested_metrics, payload, title)
    return ToolResult(
        True,
        f"{len(codes)} 종목 peer 비교 + percentile rank — {', '.join(r.get('corpName') or r['stockCode'] for r in rows[:5])}",
        refs=refs,
        data=payload,
    )


def _peerMissingCells(rows: list[dict[str, Any]], metrics: list[str]) -> list[dict[str, str]]:
    """요청한 비교축에서 값이 비어 있는 종목·지표 쌍을 반환한다."""
    return [
        {"stockCode": str(row.get("stockCode") or ""), "metric": metric}
        for row in rows
        for metric in metrics
        if row.get(metric) is None
    ]


def _peerEvidenceRefs(
    codes: list[str],
    rows: list[dict[str, Any]],
    metrics: list[str],
    payload: dict[str, Any],
    title: str,
) -> list[Ref]:
    """peer 표, 값, 기간, 실행 영수증을 하나의 ref 묶음으로 만든다."""
    tableRef = Ref(
        id=f"peer:{':'.join(codes)}",
        kind="tableRef",
        title=title,
        source="peerCompareN",
        payload=payload,
    )
    refs: list[Ref] = [tableRef]
    for row in rows:
        refs.extend(_peerRowValueRefs(row, metrics, tableRef))
        refs.extend(_peerRowDateRefs(row, tableRef))
    refs.append(_peerExecutionRef(codes, metrics, payload))
    return refs


def _peerRowValueRefs(row: dict[str, Any], metrics: list[str], tableRef: Ref) -> list[Ref]:
    """peer 한 행의 scalar 비교 지표를 value ref로 만든다."""
    stockCode = str(row.get("stockCode") or "")
    sourcePeriods = row.get("sourcePeriods") if isinstance(row.get("sourcePeriods"), dict) else {}
    refs: list[Ref] = []
    for metric in metrics:
        value = row.get(metric)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        statement = "IS" if metric in _INCOME_METRICS else "BS"
        period = sourcePeriods.get(statement)
        refs.append(
            Ref(
                id=f"value:peer:{stockCode}:{period or 'unknown'}:{metric}",
                kind="valueRef",
                title=f"{row.get('corpName') or stockCode} {metric}",
                source=tableRef.id,
                payload={
                    "stockCode": stockCode,
                    "metric": metric,
                    "value": value,
                    "period": period,
                    "statement": statement,
                },
            )
        )
    return refs


def _peerRowDateRefs(row: dict[str, Any], tableRef: Ref) -> list[Ref]:
    """peer 한 행의 재무제표별 기준시점을 date ref로 만든다."""
    stockCode = str(row.get("stockCode") or "")
    sourcePeriods = row.get("sourcePeriods") if isinstance(row.get("sourcePeriods"), dict) else {}
    refs: list[Ref] = []
    for statement, period in sourcePeriods.items():
        if not period:
            continue
        refs.append(
            Ref(
                id=f"date:peer:{stockCode}:{statement}:{period}",
                kind="dateRef",
                title=f"{row.get('corpName') or stockCode} {statement} 기준시점",
                source=tableRef.id,
                payload={"stockCode": stockCode, "period": period, "statement": statement},
            )
        )
    return refs


def _peerExecutionRef(codes: list[str], metrics: list[str], payload: dict[str, Any]) -> Ref:
    """peer 비교의 대상·지표·결손을 실행 영수증으로 만든다."""
    return Ref(
        id=f"execution:PeerCompareN:{':'.join(codes)}",
        kind="executionRef",
        title="PeerCompareN 실행 영수증",
        source="PeerCompareN",
        payload={
            "apiRef": "PeerCompareN",
            "stockCodes": codes,
            "metrics": list(metrics),
            "complete": payload["complete"],
            "missingCells": payload["missingCells"],
        },
    )


__all__ = ["peerCompareN"]
