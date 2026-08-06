"""Generated-spec validated DartLab engine call tool."""

from __future__ import annotations

import heapq
import json
import logging
import math
import os
import re
import time
from collections.abc import Mapping
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from io import StringIO
from typing import Any

import polars as pl

from dartlab.ai.contracts import Ref
from dartlab.core.confidence import baseScore as _baseScore
from dartlab.reference.capability import execution as _capabilityExecution
from dartlab.reference.capability.execution import (
    CANONICAL_AXIS_ENGINES as _AXIS_ENGINES,
)
from dartlab.reference.capability.execution import (
    CANONICAL_COMPANY_CAPABILITY_REFS as _CANONICAL_COMPANY_CAPABILITY_REFS,
)
from dartlab.reference.capability.execution import isEngineCallableRef

from .creditBadge import getDcrBadge
from .engineResult import engineResultMarkdown, engineResultRefs
from .filingDeepLink import attachDocRef, buildPeriodToFiling
from .formatting import formatMoney, formatPercent
from .industryContext import getIndustryBadge, getSectorPosition
from .panelInsight import contextMarkdown, insightMarkdown
from .types import ToolResult

_CANONICAL_TOP_LEVEL_CAPABILITY_REFS = _capabilityExecution.CANONICAL_TOP_LEVEL_CAPABILITY_REFS

_FILING_DIRECT_CONFIDENCE = _baseScore("filing_direct")

_JSON_PREVIEW_ROWS = 20
_JSON_PREVIEW_BYTES = 4_000
_JSON_MAX_BYTES = 128 * 1024
_JSON_METADATA_RESERVE = 2_048
_JSON_MAX_DEPTH = 20
_JSON_MAX_CONTAINER_ITEMS = 200
_JSON_MAX_STRING_BYTES = 16 * 1024

_AUTO_GATHER_ENABLED = os.environ.get("DARTLAB_AUTO_GATHER", "1") not in {"0", "false", "False"}

_PERIOD_RE = re.compile(r"^\d{4}(?:Q[1-4])?$")
_STMT_LABELS = {"BS": "재무상태표", "IS": "손익계산서", "CF": "현금흐름표"}
_PANEL_TOPIC_ALIASES = {
    "감사": "auditOpinion",
    "감사의견": "auditOpinion",
    "핵심감사": "auditOpinion",
    "핵심감사사항": "auditOpinion",
}
# 컬럼 alias SSOT 는 dartlab.ai.tools.columnAlias 에 있다. 여기서는 priority list 만
# 호환 dict 로 변환해 사용 - IS/CF/BS 5+ 표준 컬럼 + 한국어 label.
from dartlab.synth.rowAccess import toFloat

from .columnAlias import topicAccountPriority as _topicAccountPriority

_ACCOUNT_PRIORITY = {
    "BS": _topicAccountPriority("BS"),
    "IS": _topicAccountPriority("IS"),
    "CF": _topicAccountPriority("CF"),
}


def engineCall(plan: dict[str, Any] | None = None, **kwargs: Any) -> ToolResult:
    """Validate and execute a public DartLab API call plan."""

    call_plan = dict(plan or kwargs or {})
    _normalizeArgsDict(call_plan)
    apiRef = _apiRef(call_plan)
    if not apiRef:
        return ToolResult(False, "apiRef를 확인하지 못했습니다.", error="missing_api_ref")
    if apiRef.startswith("_") or "._" in apiRef or "internal" in apiRef.lower():
        return ToolResult(False, f"private/internal API는 차단됩니다: {apiRef}", error="private_api_blocked")
    # alias 정규화 - `dartlab.scan` → `scan`, `dartlab.capabilities` → `capabilities`,
    # `scan.growth` → `scan` (axis="growth" 흡수). CAPABILITIES 에는 canonical form 만 있어서
    # 정규화 없이 capability check 가 unreachable 핸들러 (line ~ scan/capabilities) 차단했던 회귀.
    apiRef = _aliasToCanonical(apiRef, call_plan)
    call_plan["apiRef"] = apiRef
    if not _capabilityExists(apiRef):
        return ToolResult(False, f"generated spec에 없는 API입니다: {apiRef}", error="unknown_api_ref")
    if not _isCanonicalExecutableApiRef(apiRef):
        return ToolResult(False, f"실행 계약에 없는 API입니다: {apiRef}", error="non_public_api_ref")

    if apiRef == "Company.panel":
        # stdio MCP stdout은 프로토콜 프레임 전용이다. Company 하위 badge/filing
        # 로더의 진단 출력까지 전체 호출 경계에서 흡수해 전송 손상을 막는다.
        with _quietExecutionNoise():
            return _companyShow(call_plan)
    if apiRef == "scan" or apiRef.startswith("scan."):
        if apiRef.startswith("scan.") and not call_plan.get("axis"):
            call_plan["axis"] = apiRef.split(".", 1)[1]
        return _scan(call_plan)
    if apiRef == "capabilities":
        return _capabilities(call_plan)
    if apiRef.startswith("dataHub."):
        return _dataHubAxisCall(apiRef.split(".", 1)[1], call_plan)
    # gather 표준 {engine}.{axis} 일반 디스패치 (gather.price·industry.theme·credit.grade·quant.모멘텀).
    head = apiRef.split(".", 1)[0]
    if "." in apiRef and head in _AXIS_ENGINES:
        return _axisEngineCall(head, apiRef.split(".", 1)[1], call_plan)
    return _genericPublicCall(apiRef, call_plan)


def _isCanonicalExecutableApiRef(apiRef: str) -> bool:
    """발견 catalog와 독립된 실제 실행 allowlist를 검사한다."""
    return isEngineCallableRef(apiRef)


def _dataHubAxisCall(axis: str, plan: dict[str, Any]) -> ToolResult:
    """Canonical ``dataHub.catalog`` 및 ``dataHub.query``를 public facade로 위임한다."""

    import dartlab

    args = list(plan.get("args") or [])
    target = plan.get("target")
    if target is None and args:
        target = args.pop(0)
    if args:
        return ToolResult(False, "dataHub axis는 positional target을 하나만 받습니다.", error="invalid_args")
    dataHub = getattr(dartlab, "dataHub", None)
    if dataHub is None or not callable(dataHub):
        return ToolResult(False, "dataHub facade를 찾지 못했습니다.", error="unknown_engine")
    # _scan 과 같은 경계 계약: 잘못된 kwargs(TypeError)나 무효 질의(ValueError)가
    # uncaught traceback 으로 새지 않고 typed ToolResult 로 돌아온다.
    try:
        with _quietExecutionNoise():
            result = dataHub(axis, target, **dict(plan.get("kwargs") or {}))
    except (ValueError, KeyError, TypeError) as exc:
        return ToolResult(False, f"dataHub('{axis}') 실행 실패: {exc}", error="invalid_args")
    if axis == "catalog":
        catalog = _dataHubCatalogResult(result)
        if catalog is not None:
            return catalog
    return _resultToRefs(f"dataHub.{axis}", result, target=str(plan.get("target") or ""))


# 카탈로그 자산에서 사용자가 확인할 수 있는 열만 고른다. executorModule·subjectParam 같은
# 실행 배선과 assetVersionId·metadata 는 내부 구현이라 공개 결과에 싣지 않는다.
# 열 폭보다 목록 완전성을 택했다. 8 열(universeKind·temporalSupport 포함)이면 344 행이
# 68,881 byte 라 예산을 넘어 32 행으로 잘리고, 6 열이면 52 KB 로 344 행이 전부 남는다.
# "데이터셋 목록" 질문의 답은 열 넓이가 아니라 자산 전수다.
_CATALOG_PUBLIC_COLUMNS = (
    "assetId",
    "owner",
    "layer",
    "kind",
    "label",
    "queryable",
)


def _dataHubCatalogResult(result: Any) -> ToolResult | None:
    """dataHub.catalog 를 인용 가능한 표 근거로 투영한다.

    카탈로그는 본질적으로 자산 표다. 옛 경로는 이것을 실행 영수증 하나로만 감싸고
    자산 원본(실행 배선 필드 포함)을 통째로 실었다. 실측(2026-08-05): 그 결과가
    175,841 byte 라 소비 CLI 가 tool result 를 통째로 거부했고, 그 턴은 2,345 자를
    쓰고도 근거 0 건으로 끝났다. 공개 열만 남기면 344 행이 전부 살아남고 답변이
    인용할 표 근거도 생긴다.
    """
    if not is_dataclass(result) or isinstance(result, type):
        return None
    payload = {field.name: getattr(result, field.name) for field in fields(result)}
    assets = payload.get("assets")
    if not isinstance(assets, (list, tuple)):
        return None
    rows = [_catalogRow(asset) for asset in assets]
    rows = [row for row in rows if row]
    if not rows:
        return None
    owners = sorted({str(row.get("owner") or "") for row in rows if row.get("owner")})
    tableRef = Ref(
        id="table:dataHub.catalog:assets",
        kind="tableRef",
        title=f"dataHub 데이터셋 카탈로그 {len(rows)}건",
        source="dartlab.dataHub('catalog')",
        payload={
            "rowCount": len(rows),
            "columns": list(_CATALOG_PUBLIC_COLUMNS),
            "rows": rows[:_JSON_PREVIEW_ROWS],
            "previewTruncated": len(rows) > _JSON_PREVIEW_ROWS,
            "status": payload.get("status"),
            "universe": owners,
        },
    )
    executionRef = Ref(
        id="execution:dataHub.catalog:result",
        kind="executionRef",
        title="dataHub.catalog 실행 영수증",
        source="dataHub.catalog",
        payload={
            "apiRef": "dataHub.catalog",
            "rowCount": len(rows),
            "status": payload.get("status"),
            "coverage": _jsonableResult(payload.get("coverage")),
            "gaps": _jsonableResult(payload.get("gaps")),
            "snapshotId": payload.get("snapshotId"),
        },
    )
    return ToolResult(
        True,
        f"dataHub.catalog 실행 완료 (자산 {len(rows)}건, owner {len(owners)}종)",
        refs=[tableRef, executionRef],
        data={
            "tableRef": tableRef.id,
            "rowCount": len(rows),
            "columns": list(_CATALOG_PUBLIC_COLUMNS),
            "rows": rows,
            "owners": owners,
            "status": payload.get("status"),
            # 카탈로그는 자산 정의 표라 자산별 최신 관측일을 싣지 않는다. 관측 시점은
            # dataHub.query 로 자산을 실제 조회했을 때의 결과 계약이 소유한다.
            "observedAsOfAvailable": False,
        },
    )


def _catalogRow(asset: Any) -> dict[str, Any]:
    """카탈로그 자산 하나를 공개 열만 남긴 표 행으로 만든다."""
    if is_dataclass(asset) and not isinstance(asset, type):
        source = {field.name: getattr(asset, field.name) for field in fields(asset)}
    elif isinstance(asset, Mapping):
        source = dict(asset)
    else:
        return {}
    row: dict[str, Any] = {}
    for column in _CATALOG_PUBLIC_COLUMNS:
        value = source.get(column)
        if isinstance(value, (list, tuple)):
            value = [str(item) for item in value]
        elif value is not None and not isinstance(value, (str, bool, int, float)):
            value = str(value)
        row[column] = value
    return row if row.get("assetId") else {}


def _axisEngineCall(engine: str, axis: str, plan: dict[str, Any]) -> ToolResult:
    """``{engine}.{axis}`` → ``dartlab.{engine}(axis, target, **kwargs)`` 위임 (gather 표준 통일)."""
    import dartlab

    fn = getattr(dartlab, engine, None)
    if fn is None or not callable(fn):
        return ToolResult(False, f"axis-engine 을 찾지 못했습니다: {engine}", error="unknown_engine")
    target = plan.get("target") or plan.get("stockCode") or None
    kwargs = dict(plan.get("kwargs") or {})
    if engine == "analysis":
        if not target and not kwargs.get("stockCode") and kwargs.get("company") is None:
            return ToolResult(
                False,
                "analysis 축 실행에는 stockCode 또는 company가 필요합니다.",
                error="company_not_resolved",
            )
        if target:
            kwargs.setdefault("stockCode", target)
        try:
            with _quietExecutionNoise():
                result = fn(axis, **kwargs)
        except (ValueError, KeyError, TypeError) as exc:
            return ToolResult(False, f"{engine}('{axis}') 실행 실패: {exc}", error="invalid_args")
        if isinstance(result, pl.DataFrame):
            return ToolResult(
                False,
                "analysis 계산 결과 대신 항목 목록이 반환되어 실행을 차단했습니다.",
                error="analysis_not_executed",
            )
        return _resultToRefs(f"{engine}.{axis}", result, target=str(target or ""))
    # _scan 과 같은 경계 계약: 무효 axis 어휘·kwargs 가 traceback 으로 새지 않는다.
    try:
        with _quietExecutionNoise():
            result = fn(axis, target, **kwargs)
    except (ValueError, KeyError, TypeError) as exc:
        return ToolResult(False, f"{engine}('{axis}') 실행 실패: {exc}", error="invalid_args")
    return _resultToRefs(f"{engine}.{axis}", result, target=str(target or ""))


_RESERVED_PLAN_KEYS = frozenset({"apiRef", "engine", "method", "target", "stockCode", "args", "kwargs", "apiKey"})


def _normalizeArgsDict(plan: dict[str, Any]) -> None:
    """ToolSpec schema 가 args 를 dict 로 정의 - 모델 양식 그대로 flatten.

    LLM 표준 호출: `{"apiRef": "Company.panel", "args": {"stockCode": "005930", "topic": "IS"}}`.
    이전 핸들러들은 `plan["args"]` 를 list 로 가정 (옛 형식) → dict 면 `list(dict)` 가 *키* 만
    뽑아 회귀 (`company_not_resolved`). dict 면 키들을 plan root 로 흡수 + args 를 빈 list 로.

    비-reserved 키 (axis/sub/topic/freq 등) 는 kwargs 에도 옮긴다. _companyShow 처럼 plan root
    직접 읽는 경로 외, _genericCompanyMethod 가 `c.analysis(*args, **kwargs)` 식으로 전달
    하려면 kwargs 가 채워져야. 2026-05-20 회귀: Company.analysis/gather/macro 가 root flatten
    까지만 받고 kwargs 빈 채로 호출 → c.analysis() guide DataFrame 만 반환 → LLM 이 valuation
    결과 못 받아 "가격 데이터 부재" 한계로 회피.
    """
    raw = plan.get("args")
    if not isinstance(raw, dict):
        return
    existing_kwargs: dict[str, Any] = dict(plan.get("kwargs") or {})
    for key, value in raw.items():
        # plan root 에 이미 명시된 키는 우선 (옛 호환). 그 외 setdefault 로 흡수.
        plan.setdefault(key, value)
        # method args/kwargs 로 전달할 키만 kwargs 에 - apiRef/engine/method/target/args 등 제외.
        if key not in _RESERVED_PLAN_KEYS:
            existing_kwargs.setdefault(key, value)
    plan["args"] = []
    plan["kwargs"] = existing_kwargs


def _apiRef(plan: dict[str, Any]) -> str:
    raw = str(plan.get("apiRef") or "").strip()
    # 방어적 파서 - 모델이 'Company.panel TSLA IS freq=Q' 처럼 인자까지 apiRef 에 합쳐
    # 보내는 회귀 케이스. 첫 토큰을 apiRef 로, 나머지는 args/kwargs 로 흡수.
    if raw and " " in raw:
        parts = raw.split()
        apiRef = parts[0]
        plan["apiRef"] = apiRef
        existing_args: list[Any] = list(plan.get("args") or [])
        existing_kwargs: dict[str, Any] = dict(plan.get("kwargs") or {})
        # 첫 인자가 종목코드 또는 ticker 면 target 으로 우선 흡수.
        target_set = bool(plan.get("target") or plan.get("stockCode"))
        for token in parts[1:]:
            if "=" in token:
                key, value = token.split("=", 1)
                existing_kwargs[key.strip()] = value.strip()
            elif not target_set and _looksLikeStockOrTicker(token):
                plan["target"] = token
                target_set = True
            else:
                existing_args.append(token)
        plan["args"] = existing_args
        plan["kwargs"] = existing_kwargs
        return apiRef
    if raw:
        return raw
    engine = str(plan.get("engine") or "").strip()
    method = str(plan.get("method") or "").strip()
    if engine.lower() == "company" and method:
        return f"Company.{method}"
    if engine.lower() == "dartlab" and method:
        return f"dartlab.{method}"
    return ""


def _looksLikeStockOrTicker(token: str) -> bool:
    from dartlab.core.market import isKrStockCode

    if not token:
        return False
    # KRX 단축코드 (6자리 숫자 또는 숫자 선두 영숫자, 예 0008Z0)
    if isKrStockCode(token):
        return True
    return bool(re.match(r"^[A-Z]{1,6}$", token))


def _capabilityExists(apiRef: str) -> bool:
    from dartlab.reference.capability import loadCapabilities

    return apiRef in loadCapabilities()


def _aliasToCanonical(apiRef: str, plan: dict[str, Any]) -> str:
    """LLM 이 흔히 쓰는 alias 를 CAPABILITIES canonical form 으로 정규화.

    - `dartlab.scan` / `scan.<axis>` → `scan` (+ plan["axis"] = <axis>)
    - `dartlab.capabilities` → `capabilities`
    - `dartlab.<name>` (capabilities 에 있으면 `<name>`)
    """
    from dartlab.reference.capability import loadCapabilities

    CAPABILITIES = loadCapabilities()
    if apiRef == "dartlab.scan":
        return "scan"
    if apiRef.startswith("scan.") and apiRef not in CAPABILITIES:
        plan.setdefault("axis", apiRef.split(".", 1)[1])
        return "scan"
    if apiRef == "dartlab.capabilities":
        return "capabilities"
    if apiRef.startswith("dartlab.") and apiRef not in CAPABILITIES:
        short = apiRef.split(".", 1)[1]
        if short in CAPABILITIES:
            return short
    return apiRef


def _companyShow(plan: dict[str, Any]) -> ToolResult:
    """Company.panel - 5 책임 분할 (topic 해결 / company 해결 / table fetch / refs / data)."""
    # 본체를 가져오는 데 든 시간을 잰다. 곁들이는 재료가 본체보다 오래 걸리면 안 된다.
    started = time.perf_counter()
    target = str(plan.get("target") or plan.get("stockCode") or "").strip()
    topic = _resolveTopic(plan)
    if topic not in _STMT_LABELS:
        return _companyPanelTopic(target, topic, period=str(plan.get("period") or ""))
    company = _resolveCompany(target or str(plan.get("question") or ""))
    if company is None:
        return ToolResult(
            False,
            "stockCode 누락 - EngineCall 호출 시 args dict 안에 stockCode 를 반드시 포함. 예: "
            '{"apiRef":"Company.panel","args":{"stockCode":"005930","topic":"IS"}} '
            "(plan root 가 아닌 args 안에).",
            error="company_not_resolved",
        )
    companyName = str(getattr(company, "corpName", None) or "")
    stockCode = str(getattr(company, "stockCode", None) or target or "")
    table, autoGatherUsed = _fetchTableWithAutoGather(company, topic)
    if not isinstance(table, pl.DataFrame) or table.height == 0:
        msg = f"{companyName or stockCode} {topic} 데이터를 찾지 못했습니다."
        if autoGatherUsed:
            msg += " (자동 update 후에도 빈 결과 - 미공시 분기 또는 폐상장 가능성)."
        return ToolResult(False, msg, error="empty_result")
    requestedPeriod, annualYears = _requestedStatementPeriod(plan, table, topic)
    if str(plan.get("period") or "").strip() and requestedPeriod is None and not annualYears:
        available = [str(column) for column in table.columns if _PERIOD_RE.match(str(column))]
        return ToolResult(
            False,
            f"요청 기간 {plan.get('period')}을 찾지 못했습니다. 사용 가능 기간: {', '.join(available[:12])}",
            error="period_not_found",
        )
    summary = _summarizeStatement(
        topic,
        table,
        selectedPeriod=requestedPeriod,
        annualYears=annualYears,
    )
    if not summary:
        return ToolResult(
            False, f"{companyName or stockCode} {topic} 표를 요약하지 못했습니다.", error="unreadable_table"
        )
    refs = _buildShowRefs(stockCode, companyName, topic, summary, company)
    summaryMsg = _showSummaryMessage(companyName, stockCode, topic, summary, autoGatherUsed)
    data = _buildShowData(
        company, companyName, stockCode, topic, summary, autoGatherUsed, time.perf_counter() - started
    )
    return ToolResult(True, summaryMsg, refs=refs, data=data)


def _companyPanelTopic(target: str, topic: str, *, period: str = "") -> ToolResult:
    """재무제표 밖 Company.panel topic을 기간 필터와 정형 근거로 반환한다."""
    topic = _PANEL_TOPIC_ALIASES.get(topic, topic)
    company = _resolveCompany(target)
    if company is None:
        return ToolResult(
            False, "종목을 먼저 특정해야 Company.panel을 호출할 수 있습니다.", error="company_not_resolved"
        )
    with _quietExecutionNoise():
        result = company.panel(topic)
    if isinstance(result, pl.DataFrame) and period.strip():
        result = _filterPanelPeriod(result, period)
        if result.is_empty():
            return ToolResult(
                False, f"Company.panel('{topic}')에서 요청 기간 {period}를 찾지 못했습니다.", error="period_not_found"
            )
    return _resultToRefs(
        "Company.panel",
        result,
        target=str(getattr(company, "stockCode", None) or target),
    )


def _filterPanelPeriod(frame: pl.DataFrame, period: str) -> pl.DataFrame:
    """long 또는 wide panel 표를 요청 연도/분기로 bounded 필터한다."""
    normalized = period.strip().upper().replace("FY", "").replace("-", "")
    if not normalized:
        return frame
    if "period" in frame.columns:
        return frame.filter(pl.col("period").cast(pl.String).str.to_uppercase().str.starts_with(normalized))
    periodColumns = [column for column in frame.columns if str(column).upper().startswith(normalized)]
    if not periodColumns:
        return frame.head(0)
    identityColumns = [column for column in frame.columns if not _PERIOD_RE.match(str(column))]
    return frame.select([*identityColumns, *periodColumns])


def _resolveTopic(plan: dict[str, Any]) -> str:
    """plan → topic 결정. args (list/dict) · kwargs · topic 키 검사 후 한글 별칭 정규화."""
    args = list(plan.get("args") or [])
    kwargs = dict(plan.get("kwargs") or {})
    raw = str(plan.get("topic") or (args[0] if args else "") or kwargs.get("topic") or "").strip() or "BS"
    return _normalizeStatement(raw)


def _requestedStatementPeriod(
    plan: dict[str, Any],
    table: pl.DataFrame,
    statement: str,
) -> tuple[str | None, tuple[str, ...]]:
    """명시 기간을 검증하고 연간 projection 대상 연도를 반환한다."""
    raw = str(plan.get("period") or "").strip().upper()
    columns = {str(column) for column in table.columns}
    if not raw:
        limit = plan.get("limit")
        freq = str(plan.get("freq") or "").strip().upper()
        if isinstance(limit, int) and 1 <= limit <= 20 and freq in {"Y", "FY", "YEAR", "ANNUAL"}:
            years = _completeStatementYears(columns, statement)
            return None, tuple(years[:limit])
        return None, ()
    recent = re.fullmatch(r"RECENT\s*:?\s*(\d{1,2})\s*Y", raw)
    if recent:
        years = _completeStatementYears(columns, statement)
        return None, tuple(years[: int(recent.group(1))])
    periodRange = re.fullmatch(r"(20\d{2})\s*(?:-|~|TO|부터)\s*(20\d{2})", raw)
    if periodRange:
        start, end = (int(value) for value in periodRange.groups())
        if start > end or end - start >= 20:
            return None, ()
        requested = tuple(str(year) for year in range(end, start - 1, -1))
        complete = set(_completeStatementYears(columns, statement))
        return (None, requested) if all(year in complete for year in requested) else (None, ())
    if raw.startswith("FY") and len(raw) == 6:
        raw = raw[2:]
    if raw in columns:
        return raw, ()
    if re.fullmatch(r"\d{4}", raw):
        if raw in _completeStatementYears(columns, statement):
            return None, (raw,)
        if f"{raw}Q4" in columns:
            return f"{raw}Q4", ()
    return None, ()


def _completeStatementYears(columns: set[str], statement: str) -> list[str]:
    """연간 projection이 가능한 회계연도를 최신순으로 반환한다."""
    years = sorted({period[:4] for period in columns if re.fullmatch(r"20\d{2}Q[1-4]", period)}, reverse=True)
    if statement in {"IS", "CF"}:
        return [year for year in years if all(f"{year}Q{quarter}" in columns for quarter in range(1, 5))]
    return [year for year in years if f"{year}Q4" in columns]


def _fetchTableWithAutoGather(company: Any, topic: str) -> tuple[pl.DataFrame | None, bool]:
    """company.panel(topic) + 빈 결과 시 자동 update 1회 재시도. (table, autoGatherUsed) 반환."""
    with _quietExecutionNoise():
        table = company.panel(topic)
    if isinstance(table, pl.DataFrame) and table.height > 0:
        return table, False
    if not _AUTO_GATHER_ENABLED or not _tryAutoUpdate(company, "finance"):
        return table, False
    with _quietExecutionNoise():
        table = company.panel(topic)
    return table, True


def _buildShowRefs(stockCode: str, companyName: str, topic: str, summary: dict[str, Any], company: Any) -> list[Ref]:
    """tableRef + valueRef × n + dateRef + (선택) creditRef. enrich closure 가 docRef + confidence + provenance 부착.

    creditRef 신규 - dcrBadge.axes (7축 신용 점수) 가 Company.panel 의 부수 data 라 옛 코드는
    별도 ref 없이 data 만 노출. 답안 작성 시 "신용 7축" 류 질문에 IS tableRef 부적합 인용 회귀.
    creditRef 발행으로 시맨틱 정합 - `[evidenceRef:creditRef:credit:005930:dcr:axes]` 인용 가능.
    """
    filingMap = buildPeriodToFiling(company)
    latestPeriod = summary["latestPeriod"]

    def enrich(base: dict[str, Any], period: str = latestPeriod) -> dict[str, Any]:
        """payload 에 docRef + confidence (filing_direct=95) + confidenceMethod 부착."""
        out = attachDocRef(base, period, filingMap)
        out.setdefault("confidence", _FILING_DIRECT_CONFIDENCE)
        out.setdefault("confidenceMethod", "filing_direct")
        return out

    tableRef = Ref(
        id=f"table:{stockCode}:{topic}:{latestPeriod}",
        kind="tableRef",
        title=f"{companyName or stockCode} {_STMT_LABELS[topic]} {latestPeriod}",
        source=f"Company({stockCode}).panel('{topic}')",
        payload=enrich({**summary, "stockCode": stockCode}),
    )
    refs: list[Ref] = [
        tableRef,
        Ref(
            id=f"execution:Company.panel:{stockCode}:{topic}:{latestPeriod}",
            kind="executionRef",
            title=f"{companyName or stockCode} Company.panel 실행 영수증",
            source="Company.panel",
            payload={
                "apiRef": "Company.panel",
                "stockCode": stockCode,
                "period": latestPeriod,
                "metric": topic,
                "status": "complete",
            },
        ),
    ]
    if summary.get("projection") == "annual":
        for row in summary.get("timeseries") or []:
            for period, value in (row.get("values") or {}).items():
                metricId = str(row.get("snakeId") or "value")
                refs.append(
                    Ref(
                        id=f"value:{stockCode}:{topic}:{period}:{metricId}",
                        kind="valueRef",
                        title=f"{row['item']} {period}",
                        source=tableRef.id,
                        payload={
                            **enrich(
                                {
                                    "stockCode": stockCode,
                                    "snakeId": metricId,
                                    "canonicalMetricId": _canonicalStatementMetric(metricId),
                                    "metric": _canonicalStatementMetric(metricId),
                                    "item": row["item"],
                                    "period": period,
                                    "value": value,
                                    "formatted": (row.get("formatted") or {}).get(period),
                                    "unit": "KRW",
                                    "currency": "KRW",
                                    "basis": "fiscal_year",
                                },
                                period,
                            ),
                            "provenance": [tableRef.id],
                        },
                    )
                )
    else:
        refs.extend(
            Ref(
                id=f"value:{stockCode}:{topic}:{latestPeriod}:{row['snakeId']}",
                kind="valueRef",
                title=f"{row['item']} {latestPeriod}",
                source=tableRef.id,
                payload={
                    **enrich(
                        {
                            **row,
                            "stockCode": stockCode,
                            "canonicalMetricId": _canonicalStatementMetric(str(row["snakeId"])),
                            "metric": _canonicalStatementMetric(str(row["snakeId"])),
                        }
                    ),
                    "provenance": [tableRef.id],
                },
            )
            for row in summary["rows"]
        )
    creditRef = _buildCreditRef(stockCode, companyName, company)
    if creditRef is not None:
        refs.append(creditRef)
    industryRef = _buildIndustryRef(stockCode, companyName, company)
    if industryRef is not None:
        refs.append(industryRef)
    for period in summary.get("periods") or [latestPeriod]:
        refs.append(
            Ref(
                id=f"date:{stockCode}:{topic}:{period}",
                kind="dateRef",
                title=f"{_STMT_LABELS[topic]} {period} 기준시점",
                source=tableRef.id,
                payload={
                    **enrich({"stockCode": stockCode, "period": period, "basis": "fiscal_year"}, period),
                    "provenance": [tableRef.id],
                },
            )
        )
    return refs


def _canonicalStatementMetric(snakeId: str) -> str:
    """재무제표 snake ID를 품질 검증용 canonical metric으로 정규화한다."""
    aliases = {
        "sales": "revenue",
        "revenue": "revenue",
        "operating_income": "operating_profit",
        "operating_profit": "operating_profit",
        "net_income": "net_income",
        "total_assets": "total_assets",
        "total_liabilities": "total_liabilities",
        "total_equity": "total_equity",
        "operating_cash_flow": "operating_cash_flow",
    }
    return aliases.get(snakeId, snakeId)


def _buildCreditRef(stockCode: str, companyName: str, company: Any) -> Ref | None:
    """dcrBadge.axes (7축 신용 점수) 를 시맨틱 ref 로 분리.

    옛 코드는 dcrBadge 를 data 에만 inline → 답안에서 "신용 7축" 류 질문에 IS tableRef 인용
    회귀. creditRef 발행으로 정합 매칭 가능 (id: credit:<stockCode>:dcr:axes).
    """
    badge = getDcrBadge(company)
    if badge is None:
        return None
    axes = badge.get("axes") or []
    weakest = _findWeakestAxis(axes)
    payload: dict[str, Any] = {
        "stockCode": stockCode,
        "grade": badge.get("grade"),
        "axes": axes,
    }
    if weakest is not None:
        payload["weakestAxis"] = weakest
    return Ref(
        id=f"credit:{stockCode}:dcr:axes",
        kind="creditRef",
        title=f"{companyName or stockCode} dCR 7축",
        source=f"Company({stockCode}).creditDcr()",
        payload=payload,
    )


def _findWeakestAxis(axes: list[dict[str, Any]]) -> dict[str, Any] | None:
    """7축 중 score 가장 높은 (= 가장 약한) 축 1개 추출. None 점수 제외."""
    scored: list[tuple[Any, float, Any]] = []
    for axis in axes:
        score = axis.get("score")
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            scored.append((axis.get("name"), float(score), axis.get("weight")))
    if not scored:
        return None
    name, score, weight = max(scored, key=lambda x: x[1])
    return {"name": name, "score": score, "weight": weight}


def _buildIndustryRef(stockCode: str, companyName: str, company: Any) -> Ref | None:
    """industryBadge (산업 분류 + lifecycle phase + peers) 를 시맨틱 ref 로 분리.

    creditRef 와 같은 패턴. 산업 phase / peers / stage 류 질문 답안 인용 정합.
    id: industry:<stockCode>:<industryId>:phase.
    """
    badge = getIndustryBadge(company)
    if badge is None:
        return None
    industryId = badge.get("industryId") or "unknown"
    payload: dict[str, Any] = {
        "stockCode": stockCode,
        "industryId": industryId,
        "industryName": badge.get("industryName"),
        "phase": badge.get("phase"),
        "stageName": badge.get("stageName"),
        "role": badge.get("role"),
        "stream": badge.get("stream"),
        "peers": badge.get("peers") or [],
        "confidence": badge.get("confidence"),
        "confidenceMethod": badge.get("confidenceMethod"),
    }
    return Ref(
        id=f"industry:{stockCode}:{industryId}:phase",
        kind="industryRef",
        title=f"{companyName or stockCode} {badge.get('industryName') or industryId} {badge.get('phase') or ''}".strip(),
        source=f"Company({stockCode}).industry()",
        payload=payload,
    )


def _showSummaryMessage(
    companyName: str, stockCode: str, topic: str, summary: dict[str, Any], autoGatherUsed: bool
) -> str:
    """tool result summary 문자열 - 기간 range + auto-gather 표기."""
    periods = summary.get("periods") or [summary["latestPeriod"]]
    unit = "연도" if summary.get("projection") == "annual" else "분기"
    periodLabel = f"{periods[-1]}~{periods[0]} ({len(periods)} {unit})" if len(periods) > 1 else periods[0]
    msg = f"{companyName or stockCode} {_STMT_LABELS[topic]} {periodLabel} 확인"
    if autoGatherUsed:
        msg += " (자동 update 후 재조회 성공)"
    return msg


def _buildShowData(
    company: Any,
    companyName: str,
    stockCode: str,
    topic: str,
    summary: dict[str, Any],
    autoGatherUsed: bool,
    fetchSeconds: float = 0.0,
) -> dict[str, Any]:
    """ToolResult.data - 호출자 종합 페이로드 (summary + markdown + dcr/industry badge)."""
    data: dict[str, Any] = {
        "companyName": companyName,
        "stockCode": stockCode,
        "statement": topic,
        "label": _STMT_LABELS[topic],
        "summary": summary,
        "markdown": _statementMarkdown(companyName, stockCode, topic, summary),
        "autoGatherUsed": autoGatherUsed,
    }
    badge = getDcrBadge(company)
    if badge is not None:
        data["dcrBadge"] = badge
    industryBadge = getIndustryBadge(company)
    if industryBadge is not None:
        data["industryBadge"] = industryBadge
    # 두 뱃지는 오래전부터 payload 에 실려 있었지만 본문에 없어 답변에 한 번도 쓰이지
    # 않았다. 모델이 읽는 것은 markdown 이다. 수치 하나에 판단 기준이 생긴다.
    # 맺음말 뒤에 붙이면 마무리 문장이 본문 중간에 끼므로 그 앞에 넣는다.
    sectorPosition = getSectorPosition(company, budgetSeconds=fetchSeconds)
    if sectorPosition:
        data["sectorPosition"] = sectorPosition
    context = contextMarkdown(badge, industryBadge, sectorPosition, summary)
    if context:
        body = str(data["markdown"])
        marker = "근거는 tableRef"
        index = body.rfind(marker)
        data["markdown"] = f"{body[:index]}{context}\n{body[index:]}" if index >= 0 else f"{body}\n{context}"
    return data


def _tryAutoUpdate(company: Any, category: str) -> bool:
    """company.update(categories=[category]) 자동 호출. 예외/지연 발생 시 False.

    실패 정책: 어떤 예외든 잡아서 False 반환 (호출자가 기존 empty_result 처리).
    DART API 호출이라 5~30s 소요 가능 - 환경에 따라 timeout 보호 필요 시 별도 thread/signal.
    """
    if not hasattr(company, "update"):
        return False
    try:
        with _quietExecutionNoise():
            result = company.update(categories=[category])
        if isinstance(result, dict):
            return any(v > 0 for v in result.values() if isinstance(v, int))
    except Exception as exc:
        logging.getLogger(__name__).debug("auto_gather update failed: %s", exc)
        return False
    return False


def _scan(plan: dict[str, Any]) -> ToolResult:
    rawArgs = list(plan.get("args") or [])
    explicitAxis = plan.get("axis")
    axis = str(explicitAxis or plan.get("target") or (rawArgs[0] if rawArgs else "") or "").strip() or "growth"
    target = None
    if explicitAxis:
        target = plan.get("target") or plan.get("metric") or (rawArgs[0] if rawArgs else None)
    elif plan.get("metric"):
        target = plan.get("metric")
    callKwargs = dict(plan.get("kwargs") or {})
    for reserved in ("axis", "target", "metric", "apiRef", "stockCode", "question"):
        callKwargs.pop(reserved, None)
    for key in ("spec", "explain", "market", "source", "universe"):
        if key in plan:
            callKwargs[key] = plan[key]
    import dartlab

    # 회귀 가드: CAPABILITIES 에는 `scan.industry` 등이 있지만 underlying `dartlab.scan(axis)` 가
    # 다른 axis 어휘를 쓰면 ValueError → uncaught traceback 노출. try/except 로 친절한 에러.
    try:
        scan = getattr(dartlab, "scan", None)
        if scan is None or not callable(scan):
            return ToolResult(False, "dartlab.scan facade를 찾지 못했습니다.", error="unknown_engine")
        with _quietExecutionNoise():
            result = scan(axis, target, **callKwargs)
    except (ValueError, KeyError, TypeError) as exc:
        return ToolResult(False, f"dartlab.scan('{axis}') 실행 실패: {exc}", error="invalid_scan_axis")
    if isinstance(result, dict):
        return _resultToRefs(f"scan.{axis}", result, target=str(target or ""))
    if not isinstance(result, pl.DataFrame) or result.height == 0:
        return ToolResult(False, f"dartlab.scan('{axis}') 결과가 비어 있습니다.", error="empty_scan")
    if axis.lower() == "growth" or "성장" in axis:
        rows = _rankGrowthRows(result)
        if not rows:
            return ToolResult(
                False,
                "growth scan은 실행됐지만 순위를 만들 핵심 지표가 부족합니다.",
                error="scan_growth_no_rankable_rows",
            )
        dataset_ref = Ref(
            id="dataset:scan:growth",
            kind="datasetRef",
            title="scan growth universe",
            source='dartlab.scan("growth")',
            payload={"rowCount": result.height, "columns": list(result.columns)},
        )
        table_ref = Ref(
            id="table:scan:growth:top",
            kind="tableRef",
            title="성장성 상위 후보",
            source=dataset_ref.id,
            payload={"axis": "growth", "rows": rows, "filter": "매출/영업이익/순이익 CAGR + 매출 규모 + 기간"},
        )
        refs = [dataset_ref, table_ref]
        refs.extend(
            Ref(
                id=f"value:scan:growth:{row['stockCode']}:score",
                kind="valueRef",
                title=f"{row['name']} growth score",
                source=table_ref.id,
                payload=row,
            )
            for row in rows
        )
        return ToolResult(
            True,
            f"growth scan 후보 {len(rows)}개",
            refs=refs,
            data={
                "axis": "growth",
                "rowCount": result.height,
                "rows": rows,
                "markdown": _growthMarkdown(result.height, rows),
            },
        )
    rows, rowsTruncated = _boundedFrameRows(result, maxBytes=_SCAN_ROWS_MAX_BYTES)
    table_ref = Ref(
        id=f"table:scan:{axis}:preview",
        kind="tableRef",
        title=f"scan {axis} {result.height}행",
        source=f"dartlab.scan('{axis}')",
        payload={
            "rowCount": result.height,
            "columns": list(result.columns),
            "rows": rows[:10],
            "returnedRowCount": len(rows),
            "previewTruncated": rowsTruncated,
        },
    )
    return ToolResult(
        True,
        f"scan {axis} 실행 완료 ({result.height}행 중 {len(rows)}행 반환)",
        refs=[table_ref],
        data={
            "rowCount": result.height,
            "columns": list(result.columns),
            # 옛 계약은 rowCount 와 columns 만 돌려줘 표 본문이 아예 없었다. 실측
            # (2026-08-05 brokerReach): 스크리닝 질문이 scan 을 제대로 부르고도 결과
            # 표를 못 받아 종목마다 다시 조회하다 도구 56 회, 358 초를 썼다. 표를
            # 요구한 질문에 표를 주지 않으면 회사별 반복 호출은 막을 수 없다.
            "rows": rows,
            "returnedRowCount": len(rows),
            "rowsTruncated": rowsTruncated,
        },
    )


# scan 표 본문에 허용하는 바이트다. MCP payload 예산(64 KiB) 안에서 ref 와 메타데이터
# 자리를 남긴 값이다. 스크리닝 결과 수백 행은 통째로 들어가고, 전종목 wide 표처럼
# 예산을 넘는 것만 잘리며 그 사실을 rowsTruncated 로 공개한다.
_SCAN_ROWS_MAX_BYTES = 48 * 1024


def _boundedFrameRows(frame: pl.DataFrame, *, maxBytes: int) -> tuple[list[dict[str, Any]], bool]:
    """표 결과를 payload 예산이 허락하는 최대 행수까지 담고 잘렸는지 알려준다."""
    rows: list[dict[str, Any]] = []
    used = 0
    for row in frame.iter_rows(named=True):
        encoded = len(json.dumps(row, ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8"))
        if rows and used + encoded > maxBytes:
            return rows, True
        used += encoded
        rows.append(row)
    return rows, False


def _capabilities(plan: dict[str, Any]) -> ToolResult:
    import dartlab

    args = list(plan.get("args") or [])
    key = str(plan.get("key") or plan.get("path") or (args[0] if args else "") or "").strip()
    search = str(plan.get("search") or "").strip()
    if key and search:
        return ToolResult(False, "capabilities key와 search는 동시에 사용할 수 없습니다.", error="invalid_args")
    if search:
        data = dartlab.capabilities(search=search)
    elif key:
        data = dartlab.capabilities(key)
    else:
        data = dartlab.capabilities()
    markdown = _capabilitiesMarkdown(data, path=key or search)
    payload = _jsonableResult(data)
    ref = Ref(
        id=f"api:dartlab.capabilities:{key or search or 'root'}",
        kind="apiRef",
        title="dartlab.capabilities",
        source="dartlab.capabilities",
        payload={"key": key, "search": search, "preview": _jsonPreview(payload)},
    )
    return ToolResult(True, "capabilities 조회 완료", refs=[ref], data={"result": payload, "markdown": markdown})


def _capabilitiesMarkdown(data: Any, *, path: str = "") -> str:
    title = f"DartLab {path} 기능을 확인했습니다." if path else "DartLab이 할 수 있는 일을 확인했습니다."
    lines = [title, ""]
    if isinstance(data, dict):
        items = _capabilityItems(data, path=path)
        for key, value in items:
            if isinstance(value, dict):
                summary = value.get("summary") or value.get("guide") or ""
            else:
                summary = str(value)
            lines.append(f"- {key}: {_publicCapabilitySummary(summary)}")
    elif isinstance(data, list):
        for item in [item for item in data if _publicCapabilityKey(str(item))][:12]:
            lines.append(f"- {item}")
    else:
        lines.append(str(data)[:800])
    lines.append("")
    lines.append("이 결과는 generated capability/docstring 카탈로그를 근거로 한 기능 안내입니다.")
    return "\n".join(lines)


def _capabilityItems(data: dict[str, Any], *, path: str = "") -> list[tuple[str, Any]]:
    if path:
        return [(key, value) for key, value in data.items() if _publicCapabilityKey(str(key))][:12]
    preferred = ["Company", "scan", "analysis", "macro", "gather", "quant", "credit", "story"]
    picked = [(key, data[key]) for key in preferred if key in data and _publicCapabilityKey(key)]
    if len(picked) >= 6:
        return picked
    for key, value in data.items():
        if len(picked) >= 12:
            break
        if key in {item[0] for item in picked} or not _publicCapabilityKey(str(key)):
            continue
        picked.append((key, value))
    return picked


def _publicCapabilityKey(key: str) -> bool:
    lowered = key.lower()
    if lowered in {"ask", "company.ask", "chartresult"}:
        return False
    if lowered.startswith("aicontract.") or "._" in lowered or lowered.startswith("_"):
        return False
    return True


def _publicCapabilitySummary(value: Any) -> str:
    lines = str(value or "").splitlines()
    text = lines[0] if lines else ""
    text = text.replace(" - 내부 구현", "").replace("(내부 구현)", "").replace("**", "")
    return text[:180]


def _publicTargetParameter(method: str, func: Any) -> str | None:
    """공개 callable의 canonical target 인자명을 코드 계약에서 찾는다."""
    import importlib
    import inspect

    callableTarget = func
    try:
        import dartlab

        aliases = getattr(dartlab, "_ENGINE_ALIASES", {})
        canonical = aliases.get(method, method)
        contract = getattr(dartlab, "_CONTRACT_ENGINES", {}).get(canonical)
        if contract:
            modulePath, symbol, _patchTargets = contract
            declared = getattr(importlib.import_module(modulePath), symbol)
            callableTarget = declared.__call__ if inspect.isclass(declared) else declared
        parameters = inspect.signature(callableTarget).parameters
    except (ImportError, TypeError, ValueError, AttributeError):
        return None
    for candidate in ("stockCode", "target", "code"):
        if candidate in parameters:
            return candidate
    return None


def _genericPublicCall(apiRef: str, plan: dict[str, Any]) -> ToolResult:
    if not _isCanonicalExecutableApiRef(apiRef):
        return ToolResult(False, f"실행 계약에 없는 API입니다: {apiRef}", error="non_public_api_ref")
    if apiRef.startswith("Company."):
        return _genericCompanyMethod(
            apiRef.split(".", 1)[1],
            str(plan.get("target") or plan.get("stockCode") or ""),
            list(plan.get("args") or []),
            dict(plan.get("kwargs") or {}),
        )
    if apiRef.startswith("dartlab.") or "." not in apiRef:
        import dartlab

        method = apiRef.split(".", 1)[1] if apiRef.startswith("dartlab.") else apiRef
        if method.startswith("_") or not hasattr(dartlab, method):
            return ToolResult(False, f"공개 dartlab API를 찾지 못했습니다: {apiRef}", error="unknown_api_ref")
        func = getattr(dartlab, method)
        if not callable(func):
            return ToolResult(False, f"호출 가능한 API가 아닙니다: {apiRef}", error="not_callable")
        args = list(plan.get("args") or [])
        kwargs = dict(plan.get("kwargs") or {})
        target = plan.get("target") or plan.get("stockCode")
        if target is not None and not args:
            targetParameter = _publicTargetParameter(method, func)
            if targetParameter:
                kwargs.setdefault(targetParameter, target)
        result = func(*args, **kwargs)
        return _resultToRefs(apiRef, result, target=str(target or ""))
    return ToolResult(False, f"지원하지 않는 apiRef입니다: {apiRef}", error="unsupported_api_ref")


def _genericCompanyMethod(method: str, target: str, args: list[Any], kwargs: dict[str, Any]) -> ToolResult:
    apiRef = f"Company.{method}"
    if apiRef not in _CANONICAL_COMPANY_CAPABILITY_REFS:
        return ToolResult(False, f"실행 계약에 없는 API입니다: {apiRef}", error="non_public_api_ref")
    company = _resolveCompany(target)
    if company is None:
        return ToolResult(False, "종목을 먼저 특정해야 Company API를 호출할 수 있습니다.", error="company_not_resolved")
    if method.startswith("_") or not hasattr(company, method):
        return ToolResult(False, f"공개 Company API를 찾지 못했습니다: Company.{method}", error="unknown_api_ref")
    func = getattr(company, method)
    if not callable(func):
        return ToolResult(False, f"호출 가능한 API가 아닙니다: Company.{method}", error="not_callable")
    with _quietExecutionNoise():
        result = func(*args, **kwargs)
    return _resultToRefs(f"Company.{method}", result, target=str(getattr(company, "stockCode", None) or target))


def _resultToRefs(apiRef: str, result: Any, *, target: str = "") -> ToolResult:
    if isinstance(result, pl.DataFrame):
        payload = _jsonableResult(result)
        table_ref = Ref(
            id=f"table:{apiRef}:{target or 'result'}",
            kind="tableRef",
            title=f"{apiRef} result",
            source=apiRef,
            payload=payload,
        )
        executionRef = Ref(
            id=f"execution:{apiRef}:{target or 'result'}",
            kind="executionRef",
            title=f"{apiRef} 실행 영수증",
            source=apiRef,
            payload={
                "apiRef": apiRef,
                "target": target or None,
                "rowCount": result.height,
                "status": "complete",
            },
        )
        extraRefs = _dataFrameEvidenceRefs(apiRef, payload, target=target, tableRef=table_ref)
        return ToolResult(
            True,
            f"{apiRef} 실행 완료",
            refs=[table_ref, executionRef, *extraRefs],
            data={
                "tableRef": table_ref.id,
                "rowCount": result.height,
                "columns": list(result.columns),
                "previewTruncated": bool(payload.get("previewTruncated")) if isinstance(payload, dict) else False,
            },
        )
    if isinstance(result, Mapping | list | tuple | set | frozenset) or is_dataclass(result):
        payload = _jsonableResult(result)
        executionContract = _executionContractFields(payload)
        refs = [
            Ref(
                id=f"execution:{apiRef}:{target or 'result'}",
                kind="executionRef",
                title=f"{apiRef} result",
                source=apiRef,
                # 전체 result 는 ToolResult.data 가 정본이다. ref 안에 다시 복제하면 MCP
                # structuredContent 크기가 정확히 두 배가 되므로 감사용 계약 필드와 preview만 둔다.
                payload={**executionContract, "target": target or None, "preview": _jsonPreview(payload)},
            )
        ]
        refs.extend(_lensRefs(apiRef, payload, target=target))
        refs.extend(_simulationRefs(apiRef, payload, target=target))
        # 모델이 읽는 것은 본문이다. dict 안에만 있는 것은 없는 것과 같다. 판정 엔진의
        # 결과를 표로 펴고 그 표를 가리키는 근거를 함께 발급한다.
        refs.extend(engineResultRefs(apiRef, target, payload))
        body = engineResultMarkdown(apiRef, target, payload)
        data: dict[str, Any] = {"result": payload}
        if body:
            data["markdown"] = body
        return ToolResult(True, f"{apiRef} 실행 완료", refs=refs, data=data)
    payload = _jsonableResult(result)
    ref = Ref(
        id=f"execution:{apiRef}:{target or 'result'}",
        kind="executionRef",
        title=f"{apiRef} result",
        source=apiRef,
        payload={"preview": _jsonPreview(payload)},
    )
    return ToolResult(True, f"{apiRef} 실행 완료", refs=[ref], data={"result": payload})


def _dataFrameEvidenceRefs(apiRef: str, payload: Any, *, target: str, tableRef: Ref) -> list[Ref]:
    """DataFrame preview에서 문서, 값, 기간 근거를 bounded 개수로 분리한다."""
    if not isinstance(payload, dict):
        return []
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return []
    refs: list[Ref] = []
    valueCount = 0
    seenDates: set[tuple[str, str]] = set()
    for rowIndex, rawRow in enumerate(rows[:20]):
        if not isinstance(rawRow, dict):
            continue
        rowRefs, valueCount = _dataFrameRowEvidenceRefs(
            apiRef,
            rawRow,
            rowIndex=rowIndex,
            target=target,
            tableRef=tableRef,
            seenDates=seenDates,
            valueCount=valueCount,
        )
        refs.extend(rowRefs)
    return refs


def _dataFrameRowEvidenceRefs(
    apiRef: str,
    row: dict[str, Any],
    *,
    rowIndex: int,
    target: str,
    tableRef: Ref,
    seenDates: set[tuple[str, str]],
    valueCount: int,
) -> tuple[list[Ref], int]:
    """DataFrame 한 행을 독립된 doc/date/value ref로 투영한다."""
    stockCode = str(row.get("stockCode") or row.get("code") or target or "")
    period = str(row.get("period") or row.get("year") or "")
    dataAsOf = str(row.get("rceptDate") or row.get("rceptDt") or row.get("filedAt") or "")
    documentRef, dataAsOf = _dataFrameDocumentRef(
        apiRef,
        row,
        rowIndex=rowIndex,
        stockCode=stockCode,
        period=period,
        dataAsOf=dataAsOf,
        target=target,
    )
    refs = [documentRef] if documentRef is not None else []
    dateRef = _dataFrameDateRef(
        apiRef,
        rowIndex=rowIndex,
        stockCode=stockCode,
        period=period,
        dataAsOf=dataAsOf,
        target=target,
        tableRef=tableRef,
        seenDates=seenDates,
    )
    if dateRef is not None:
        refs.append(dateRef)
    valueRefs = _dataFrameValueRefs(
        apiRef,
        row,
        rowIndex=rowIndex,
        stockCode=stockCode,
        period=period,
        target=target,
        tableRef=tableRef,
        remaining=max(0, 24 - valueCount),
    )
    refs.extend(valueRefs)
    return refs, valueCount + len(valueRefs)


def _dataFrameDocumentRef(
    apiRef: str,
    row: dict[str, Any],
    *,
    rowIndex: int,
    stockCode: str,
    period: str,
    dataAsOf: str,
    target: str,
) -> tuple[Ref | None, str]:
    """공시 접수번호가 있는 행만 bounded 문서 근거로 만든다."""
    rceptNo = str(row.get("rceptNo") or row.get("rcept_no") or "")
    if not rceptNo:
        return None, dataAsOf
    inferredSection = "auditOpinion" if {"core_adt_matter", "adt_opinion"} & set(row) else "filing"
    section = str(row.get("section") or row.get("sectionLeaf") or row.get("reportType") or inferredSection)
    if not dataAsOf and re.fullmatch(r"20\d{6}\d{6}", rceptNo):
        dataAsOf = f"{rceptNo[:4]}-{rceptNo[4:6]}-{rceptNo[6:8]}"
    excerpt, documentFields = _rowDocumentPayload(row)
    return (
        Ref(
            id=f"doc:{_refStem(stockCode, rceptNo, section, str(rowIndex))}",
            kind="docRef",
            title=f"{stockCode or target} {section}",
            source=str(row.get("dartUrl") or row.get("url") or apiRef),
            payload={
                "stockCode": stockCode,
                "period": period or None,
                "dataAsOf": dataAsOf or None,
                "rceptNo": rceptNo,
                "filedAt": dataAsOf or None,
                "section": section,
                "reportType": row.get("reportType"),
                "excerpt": excerpt,
                "fields": documentFields,
            },
        ),
        dataAsOf,
    )


def _rowDocumentPayload(row: dict[str, Any]) -> tuple[str, dict[str, str]]:
    """감사 claim 검산에 필요한 문서 필드만 크기 제한해 보존한다."""
    excerptKeys = ("core_adt_matter", "adt_opinion", "content", "text", "summary")
    fieldKeys = (
        "adt_opinion",
        "core_adt_matter",
        "emphs_matter",
        "adt_reprt_spcmnt_matter",
        "content",
        "summary",
    )
    excerpt = next((str(row[key]) for key in excerptKeys if row.get(key) not in (None, "")), "")
    fields = {key: str(row[key])[:2_000] for key in fieldKeys if row.get(key) not in (None, "")}
    return excerpt[:2_000], fields


def _dataFrameDateRef(
    apiRef: str,
    *,
    rowIndex: int,
    stockCode: str,
    period: str,
    dataAsOf: str,
    target: str,
    tableRef: Ref,
    seenDates: set[tuple[str, str]],
) -> Ref | None:
    """중복되지 않은 기간/접수일을 date ref로 만든다."""
    dateKey = (period, dataAsOf)
    if not (period or dataAsOf) or dateKey in seenDates:
        return None
    seenDates.add(dateKey)
    return Ref(
        id=f"date:{_refStem(apiRef, stockCode or target, period or dataAsOf, str(rowIndex))}",
        kind="dateRef",
        title=f"{apiRef} 기준시점",
        source=tableRef.id,
        payload={"stockCode": stockCode, "period": period or None, "dataAsOf": dataAsOf or None},
    )


def _dataFrameValueRefs(
    apiRef: str,
    row: dict[str, Any],
    *,
    rowIndex: int,
    stockCode: str,
    period: str,
    target: str,
    tableRef: Ref,
    remaining: int,
) -> list[Ref]:
    """한 행의 scalar 값을 전역 budget 안에서 value ref로 만든다."""
    refs: list[Ref] = []
    for metric, value in row.items():
        if len(refs) >= remaining:
            break
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        refs.append(
            Ref(
                id=f"value:{_refStem(apiRef, stockCode or target, period or str(rowIndex), str(metric))}",
                kind="valueRef",
                title=f"{metric} {period or ''}".strip(),
                source=tableRef.id,
                payload={
                    "stockCode": stockCode,
                    "period": period or None,
                    "metric": str(metric),
                    "value": value,
                },
            )
        )
    return refs


def _simulationRefs(apiRef: str, payload: Any, *, target: str) -> list[Ref]:
    """SimulationResult의 경로, 값, 기준시점을 직접 인용 가능한 근거로 분리한다."""
    if apiRef not in {"simulate", "Company.simulate"} or not isinstance(payload, dict):
        return []
    pathKeys = ("revenuePath", "marginPath", "fcfPath")
    paths = {key: payload.get(key) for key in pathKeys if isinstance(payload.get(key), list)}
    period = str(payload.get("requestedAsOf") or payload.get("asOf") or payload.get("latestAsOf") or "")
    stockCode = str(payload.get("stockCode") or target or "")
    horizon = max((len(values) for values in paths.values()), default=0)
    rows = [
        {"step": step + 1, **{key: values[step] if step < len(values) else None for key, values in paths.items()}}
        for step in range(horizon)
    ]
    complete = str(payload.get("quality") or "").casefold() == "ok" and all(
        value is not None for values in paths.values() for value in values
    )
    tableRef = _simulationTableRef(apiRef, payload, target, stockCode, period, rows, complete)
    refs = [tableRef]
    refs.extend(_simulationPathValueRefs(apiRef, payload, paths, stockCode, period, tableRef))
    refs.extend(_simulationScalarValueRefs(apiRef, payload, stockCode, period, tableRef))
    dateRef = _simulationDateRef(apiRef, stockCode, period, tableRef)
    if dateRef is not None:
        refs.append(dateRef)
    return refs


def _simulationTableRef(
    apiRef: str,
    payload: dict[str, Any],
    target: str,
    stockCode: str,
    period: str,
    rows: list[dict[str, Any]],
    complete: bool,
) -> Ref:
    """시뮬레이션 경로와 결손을 한 bounded table ref에 보존한다."""
    scenario = payload.get("scenarioName") or "scenario"
    return Ref(
        id=f"table:{_refStem(apiRef, stockCode or 'result', scenario)}",
        kind="tableRef",
        title=f"{stockCode or target} {scenario} 경로",
        source=f"execution:{apiRef}:{target or 'result'}",
        payload={
            "stockCode": stockCode,
            "period": period or None,
            "rows": rows,
            "complete": complete,
            "status": payload.get("quality"),
            "gaps": payload.get("dataInputGaps") or payload.get("warnings") or [],
        },
    )


def _simulationPathValueRefs(
    apiRef: str,
    payload: dict[str, Any],
    paths: dict[str, list[Any]],
    stockCode: str,
    period: str,
    tableRef: Ref,
) -> list[Ref]:
    """시뮬레이션의 기간별 경로 값을 value ref로 만든다."""
    refs: list[Ref] = []
    for metric, values in paths.items():
        for step, value in enumerate(values[:8], start=1):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            refs.append(
                Ref(
                    id=f"value:{_refStem(apiRef, stockCode or 'result', period or 'latest', metric, str(step))}",
                    kind="valueRef",
                    title=f"{metric} {step}",
                    source=tableRef.id,
                    payload={
                        "stockCode": stockCode,
                        "period": period or None,
                        "metric": metric,
                        "value": value,
                        "scenario": payload.get("scenarioName"),
                        "step": step,
                    },
                )
            )
    return refs


def _simulationScalarValueRefs(
    apiRef: str,
    payload: dict[str, Any],
    stockCode: str,
    period: str,
    tableRef: Ref,
) -> list[Ref]:
    """DCF 등 시뮬레이션 scalar 결과를 value ref로 만든다."""
    refs: list[Ref] = []
    for metric in ("dcfPerShare", "enterpriseValue", "terminalRevenue"):
        value = payload.get(metric)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        refs.append(
            Ref(
                id=f"value:{_refStem(apiRef, stockCode or 'result', period or 'latest', metric)}",
                kind="valueRef",
                title=metric,
                source=tableRef.id,
                payload={
                    "stockCode": stockCode,
                    "period": period or None,
                    "metric": metric,
                    "value": value,
                    "scenario": payload.get("scenarioName"),
                },
            )
        )
    return refs


def _simulationDateRef(apiRef: str, stockCode: str, period: str, tableRef: Ref) -> Ref | None:
    """시뮬레이션 기준시점이 있을 때만 date ref를 만든다."""
    if not period:
        return None
    return Ref(
        id=f"date:{_refStem(apiRef, stockCode or 'result', period)}",
        kind="dateRef",
        title=f"{apiRef} 기준시점",
        source=tableRef.id,
        payload={"stockCode": stockCode, "period": period},
    )


_JSON_OMIT = object()
_EVIDENCE_FIELDS = (
    "schemaVersion",
    "status",
    "quality",
    "gaps",
    "coverage",
    "universeCoverage",
    "assets",
    "qualityAssertions",
    "asOf",
    "latestAsOf",
    "requestedAsOf",
    "dataAsOf",
    "period",
    "knowledgeBoundary",
    "snapshotId",
    "dataSnapshotId",
    "dataCatalogSnapshotId",
    "universeSnapshotId",
    "contractHash",
    "dataContractHash",
    "provenance",
    "lineageRefs",
    "dataLineageRefs",
    "sourceRefs",
    "evidenceRefs",
    "executionReceipts",
    "dataExecutionReceipts",
    "materializationReceipt",
    "materializationReceiptJson",
    "continuation",
    "dataInputGaps",
    "warnings",
    "dataEvidence",
    "nodes",
    "asset",
    "requestId",
    "projectionKind",
    "selector",
    "temporalStatus",
    "rowCount",
    "truncated",
    "lineage",
    "contentHash",
)
_EVIDENCE_PRIORITY = {
    key: index for index, key in enumerate((*_EVIDENCE_FIELDS, "product", "products", "lensProducts", "partitions"))
}
_PARTITION_EVIDENCE_FIELDS = (
    "asset",
    "requestId",
    "projectionKind",
    "selector",
    "temporalStatus",
    "rowCount",
    "truncated",
    "lineageRefs",
    "lineage",
    "qualityAssertions",
    "contentHash",
)


class _JsonBudget:
    def __init__(self, maxBytes: int) -> None:
        self.maxBytes = maxBytes
        self.remaining = max(0, maxBytes - _JSON_METADATA_RESERVE)
        self.reasons: set[str] = set()
        self.omittedItems = 0

    def charge(self, byteCount: int) -> bool:
        """직렬화 예산에서 바이트를 차감하고 허용 여부를 반환한다."""
        if byteCount > self.remaining:
            self.reasons.add("maxBytes")
            return False
        self.remaining -= byteCount
        return True

    def note(self, reason: str, omittedItems: int = 0) -> None:
        """잘림 사유와 생략 항목 수를 누적한다."""
        self.reasons.add(reason)
        self.omittedItems += max(0, omittedItems)


def _jsonableResult(value: Any, _depth: int = 0, *, maxBytes: int = _JSON_MAX_BYTES) -> Any:
    """결과를 deterministic, bounded JSON tree로 변환한다.

    전역 byte, 깊이, 컨테이너 길이, 문자열 길이 상한을 동시에 적용한다. 감사 계약 필드는
    큰 data field보다 먼저 직렬화하며 unsupported 객체를 주소 문자열로 바꾸지 않는다.
    """

    budget = _JsonBudget(maxBytes)
    payload = _serializeJsonTree(value, budget, _depth, set())
    if payload is _JSON_OMIT:
        payload = {"_type": type(value).__qualname__, "serializationError": "maxBytes"}
        budget.note("maxBytes", 1)
    return _attachSerializationMetadata(payload, budget)


def _serializeJsonTree(value: Any, budget: _JsonBudget, depth: int, active: set[int]) -> Any:
    if depth > _JSON_MAX_DEPTH:
        budget.note("maxDepth", 1)
        return _serializedMarker(value, "maxDepth", budget)
    if value is None or isinstance(value, bool | int):
        return value if budget.charge(_jsonSize(value)) else _JSON_OMIT
    if isinstance(value, str):
        return _boundedString(value, budget)
    if isinstance(value, float):
        if not math.isfinite(value):
            budget.note("nonFiniteFloat")
            return None if budget.charge(4) else _JSON_OMIT
        return value if budget.charge(_jsonSize(value)) else _JSON_OMIT
    if isinstance(value, datetime | date):
        return _boundedString(value.isoformat(), budget)
    if isinstance(value, pl.DataFrame):
        preview = value.head(_JSON_PREVIEW_ROWS)
        frame = {
            "_type": "DataFrame",
            "rowCount": value.height,
            "previewRowCount": preview.height,
            "columns": list(value.columns),
            "schema": [
                {"name": name, "dtype": str(dtype)} for name, dtype in zip(value.columns, value.dtypes, strict=True)
            ],
            "rows": preview.to_dicts(),
            "previewTruncated": value.height > preview.height,
        }
        return _serializeJsonTree(frame, budget, depth, active)
    if isinstance(value, pl.Series):
        preview = value.head(_JSON_PREVIEW_ROWS)
        series = {
            "_type": "Series",
            "name": value.name,
            "dtype": str(value.dtype),
            "length": value.len(),
            "previewLength": preview.len(),
            "values": preview.to_list(),
            "previewTruncated": value.len() > preview.len(),
        }
        return _serializeJsonTree(series, budget, depth, active)

    identity = id(value)
    if identity in active:
        budget.note("cycle", 1)
        return _serializedMarker(value, "cycle", budget)
    if isinstance(value, Mapping):
        active.add(identity)
        try:
            items, preOmitted = _boundedMappingItems(value)
            return _serializeMapping(items, budget, depth, active, preOmitted=preOmitted)
        finally:
            active.remove(identity)
    if is_dataclass(value) and not isinstance(value, type):
        active.add(identity)
        try:
            items = [(field.name, getattr(value, field.name)) for field in fields(value)]
            return _serializeMapping(items, budget, depth, active)
        finally:
            active.remove(identity)
    if isinstance(value, list | tuple):
        active.add(identity)
        try:
            return _serializeSequence(value, budget, depth, active)
        finally:
            active.remove(identity)
    if isinstance(value, set | frozenset):
        if not all(item is None or isinstance(item, str | int | float | bool | datetime | date) for item in value):
            budget.note("unsupportedUnorderedContainer", len(value))
            return _serializedMarker(value, "unsupportedUnorderedContainer", budget)
        ordered = heapq.nsmallest(_JSON_MAX_CONTAINER_ITEMS, value, key=_stableScalarKey)
        if len(value) > len(ordered):
            budget.note("maxContainerItems", len(value) - len(ordered))
        active.add(identity)
        try:
            return _serializeSequence(ordered, budget, depth, active)
        finally:
            active.remove(identity)
    budget.note("unsupportedType", 1)
    return _serializedMarker(value, "unsupportedType", budget)


def _serializeMapping(
    items: list[tuple[Any, Any]],
    budget: _JsonBudget,
    depth: int,
    active: set[int],
    *,
    preOmitted: int = 0,
) -> dict[str, Any] | object:
    if not budget.charge(2):
        return _JSON_OMIT
    if preOmitted:
        budget.note("maxContainerItems", preOmitted)
    indexed = list(enumerate(items))
    indexed.sort(key=lambda row: (_fieldPriority(row[1][0]), row[0]))
    output: dict[str, Any] = {}
    accepted = 0
    for position, (_, (key, item)) in enumerate(indexed):
        if accepted >= _JSON_MAX_CONTAINER_ITEMS:
            budget.note("maxContainerItems", len(indexed) - position)
            break
        if not isinstance(key, str):
            budget.note("nonStringMappingKey", 1)
            continue
        before = budget.remaining
        separatorBytes = 1 if output else 0
        if not budget.charge(separatorBytes + _jsonSize(key) + 1):
            budget.omittedItems += len(indexed) - position
            break
        child = _serializeJsonTree(item, budget, depth + 1, active)
        if child is _JSON_OMIT:
            budget.remaining = before
            budget.omittedItems += len(indexed) - position
            break
        output[key] = child
        accepted += 1
    return output


def _boundedMappingItems(value: Mapping[Any, Any]) -> tuple[list[tuple[Any, Any]], int]:
    """감사 필드를 우선 보존하면서 큰 mapping 전체 복제를 피한다."""

    items: list[tuple[Any, Any]] = []
    seen: set[Any] = set()
    for key in _EVIDENCE_PRIORITY:
        if key in value:
            items.append((key, value[key]))
            seen.add(key)
            if len(items) >= _JSON_MAX_CONTAINER_ITEMS:
                break
    if len(items) < _JSON_MAX_CONTAINER_ITEMS:
        for key, item in value.items():
            if key in seen:
                continue
            items.append((key, item))
            seen.add(key)
            if len(items) >= _JSON_MAX_CONTAINER_ITEMS:
                break
    try:
        omitted = max(0, len(value) - len(items))
    except TypeError:
        omitted = 1 if len(items) >= _JSON_MAX_CONTAINER_ITEMS else 0
    return items, omitted


def _serializeSequence(
    values: list[Any] | tuple[Any, ...], budget: _JsonBudget, depth: int, active: set[int]
) -> list[Any] | object:
    if not budget.charge(2):
        return _JSON_OMIT
    output: list[Any] = []
    for index, item in enumerate(values):
        if index >= _JSON_MAX_CONTAINER_ITEMS:
            budget.note("maxContainerItems", len(values) - index)
            break
        before = budget.remaining
        if output and not budget.charge(1):
            budget.omittedItems += len(values) - index
            break
        child = _serializeJsonTree(item, budget, depth + 1, active)
        if child is _JSON_OMIT:
            budget.remaining = before
            budget.omittedItems += len(values) - index
            break
        output.append(child)
    return output


def _boundedString(value: str, budget: _JsonBudget) -> str | object:
    encodedSize = _jsonSize(value)
    allowed = min(_JSON_MAX_STRING_BYTES, budget.remaining)
    if encodedSize <= allowed:
        budget.charge(encodedSize)
        return value
    budget.note("maxStringBytes", 1)
    suffix = "..."
    low = 0
    high = len(value)
    best: str | None = None
    while low <= high:
        middle = (low + high) // 2
        candidate = value[:middle] + suffix
        size = _jsonSize(candidate)
        if size <= allowed:
            best = candidate
            low = middle + 1
        else:
            high = middle - 1
    if best is None or not budget.charge(_jsonSize(best)):
        return _JSON_OMIT
    return best


def _serializedMarker(value: Any, reason: str, budget: _JsonBudget) -> dict[str, Any] | object:
    marker = {
        "_type": f"{type(value).__module__}.{type(value).__qualname__}",
        "serializationError": reason,
    }
    return marker if budget.charge(_jsonSize(marker)) else _JSON_OMIT


def _attachSerializationMetadata(payload: Any, budget: _JsonBudget) -> Any:
    if not budget.reasons:
        return payload
    metadata = {
        "truncated": True,
        "reasons": sorted(budget.reasons),
        "omittedItems": budget.omittedItems,
        "maxBytes": budget.maxBytes,
        "maxDepth": _JSON_MAX_DEPTH,
        "maxContainerItems": _JSON_MAX_CONTAINER_ITEMS,
        "maxStringBytes": _JSON_MAX_STRING_BYTES,
    }
    marker = {"_dartlabSerialization": metadata}
    if isinstance(payload, dict):
        payload = dict(payload)
        payload["_dartlabSerialization"] = metadata
        return payload
    if isinstance(payload, list):
        payload = list(payload)
        payload.append(marker)
        return payload
    return {"value": payload, **marker}


def _fieldPriority(key: Any) -> int:
    if not isinstance(key, str):
        return len(_EVIDENCE_PRIORITY) + 100
    if key == "data" or key in {"rows", "values", "payload"}:
        return len(_EVIDENCE_PRIORITY) + 100
    return _EVIDENCE_PRIORITY.get(key, len(_EVIDENCE_PRIORITY) + 10)


def _stableScalarKey(value: Any) -> tuple[str, str]:
    if isinstance(value, datetime | date):
        normalized: Any = value.isoformat()
    elif isinstance(value, float) and not math.isfinite(value):
        normalized = None
    else:
        normalized = value
    return type(value).__qualname__, json.dumps(normalized, ensure_ascii=False, sort_keys=True)


def _jsonSize(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _jsonPreview(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return encoded[:_JSON_PREVIEW_BYTES].decode("utf-8", errors="ignore")


def _executionContractFields(payload: Any) -> dict[str, Any]:
    """실행 ref가 payload 예산과 무관하게 보존해야 하는 감사 필드를 고른다."""
    if not isinstance(payload, dict):
        return {}
    contract: dict[str, Any] = {}
    for key in _EVIDENCE_FIELDS:
        if key in payload:
            contract[key] = payload[key]
    partitions = payload.get("partitions")
    if isinstance(partitions, list):
        contract["partitionEvidence"] = [
            {key: partition[key] for key in _PARTITION_EVIDENCE_FIELDS if key in partition}
            for partition in partitions
            if isinstance(partition, dict)
        ]
    if "_dartlabSerialization" in payload:
        contract["serialization"] = payload["_dartlabSerialization"]
    return _jsonableResult(contract, maxBytes=32 * 1024)


def _lensRefs(apiRef: str, payload: Any, *, target: str) -> list[Ref]:
    """Lens Product의 직접 결론과 시간 경계를 근거 ref로 만든다."""
    refs: list[Ref] = []
    for engine, product in _findLensProducts(payload):
        identityValue = product.get("identity")
        conclusionValue = product.get("conclusion")
        confidenceValue = product.get("confidence")
        timeValue = product.get("time")
        identity: dict[str, Any] = identityValue if isinstance(identityValue, dict) else {}
        conclusion: dict[str, Any] = conclusionValue if isinstance(conclusionValue, dict) else {}
        confidence: dict[str, Any] = confidenceValue if isinstance(confidenceValue, dict) else {}
        time: dict[str, Any] = timeValue if isinstance(timeValue, dict) else {}
        evidence = [row for row in (product.get("evidence") or []) if isinstance(row, dict)]
        evidenceRefs = [str(row["id"]) for row in evidence if row.get("id")]
        sourceRefs = list(dict.fromkeys(str(row["sourceRef"]) for row in evidence if row.get("sourceRef")))
        refTarget = str(identity.get("target") or target or "result")
        axis = str(identity.get("axis") or "representative")
        stem = _refStem(refTarget, engine, axis)
        conclusionValue = conclusion.get("label") or conclusion.get("summary")
        refs.append(
            Ref(
                id=f"value:{stem}:conclusion",
                kind="valueRef",
                title=f"{engine} 대표 판단",
                source=apiRef,
                payload={
                    "engine": engine,
                    "target": refTarget,
                    "axis": axis,
                    "status": product.get("status"),
                    # valueRef는 숫자만이 아니라 직접 관측된 정성 판단도 담는다. 품질
                    # 게이트가 빈 값으로 폐기하지 않도록 대표 결론을 정본 value로 둔다.
                    "value": conclusionValue,
                    "label": conclusion.get("label"),
                    "summary": conclusion.get("summary"),
                    "confidence": confidence.get("score"),
                    "confidenceLevel": confidence.get("level"),
                    "confidenceMethod": confidence.get("method"),
                    "gaps": _jsonableResult(product.get("gaps") or []),
                    "evidenceRefs": evidenceRefs,
                    "provenance": sourceRefs,
                },
            )
        )
        refs.append(
            Ref(
                id=f"date:{stem}:boundary",
                kind="dateRef",
                title=f"{engine} 기준시점",
                source=apiRef,
                payload={
                    "engine": engine,
                    "asOf": time.get("asOf"),
                    "dataAsOf": time.get("dataAsOf"),
                    "period": time.get("period"),
                    "knowledgeBoundary": time.get("knowledgeBoundary"),
                },
            )
        )
    return refs


def _findLensProducts(payload: Any) -> list[tuple[str, dict[str, Any]]]:
    if not isinstance(payload, dict):
        return []
    candidates: list[dict[str, Any]] = []
    direct = payload.get("product")
    if isinstance(direct, dict):
        candidates.append(direct)

    for key in ("products", "lensProducts"):
        value = payload.get(key)
        if not isinstance(value, dict):
            continue
        nestedProducts = value.get("products")
        productMap: dict[str, Any] = nestedProducts if isinstance(nestedProducts, dict) else value
        candidates.extend(row for row in productMap.values() if isinstance(row, dict))

    rows: list[tuple[str, dict[str, Any]]] = []
    seen: set[tuple[str, str, str]] = set()
    for product in candidates:
        identityValue = product.get("identity")
        identity: dict[str, Any] = identityValue if isinstance(identityValue, dict) else {}
        engine = str(identity.get("engine") or "")
        if engine not in {"analysis", "credit", "industry", "quant", "macro"}:
            continue
        key = (engine, str(identity.get("target") or ""), str(identity.get("axis") or ""))
        if key in seen:
            continue
        seen.add(key)
        rows.append((engine, product))
    return rows


def _refStem(*parts: str) -> str:
    value = ":".join(str(part) for part in parts)
    return re.sub(r"[^0-9A-Za-z가-힣_.:-]+", "_", value).strip("_:") or "lens"


def _resolveCompany(target: str):
    target = str(target or "").strip()
    if target:
        import dartlab

        try:
            companyFactory = getattr(dartlab, "Company", None)
            if companyFactory is None or not callable(companyFactory):
                raise TypeError("Company facade unavailable")
            with _quietExecutionNoise():
                return companyFactory(target)
        except (OSError, RuntimeError, TypeError, ValueError):
            pass
        from dartlab.company import resolveFromText

        try:
            with _quietExecutionNoise():
                company, _ = resolveFromText(target)
                return company
        except (OSError, RuntimeError, TypeError, ValueError):
            return None
    return None


def _normalizeStatement(value: str) -> str:
    q = str(value or "").strip().lower()
    if q in {"bs", "balance sheet", "재무상태표", "자산", "부채", "자본"}:
        return "BS"
    if q in {"is", "income statement", "손익계산서", "손익", "이익"}:
        return "IS"
    if q in {"cf", "cash flow", "현금흐름표", "현금흐름"}:
        return "CF"
    return str(value or "").strip()


def _summarizeStatement(
    statement: str,
    table: pl.DataFrame,
    *,
    selectedPeriod: str | None = None,
    annualYears: tuple[str, ...] = (),
) -> dict[str, Any] | None:
    periods = [col for col in table.columns if _PERIOD_RE.match(str(col))]
    if not periods:
        return None
    priorityRows = _findPriorityRows(statement, table, periods)
    if not priorityRows:
        return None
    projection = "period"
    if annualYears:
        annualPeriods = [f"{year}FY" for year in annualYears]
        annualRows: list[dict[str, Any]] = []
        for row in priorityRows:
            annualValues: dict[str, Any] = {}
            for year, annualPeriod in zip(annualYears, annualPeriods, strict=True):
                if statement in {"IS", "CF"}:
                    values = [row["values"].get(f"{year}Q{quarter}") for quarter in range(1, 5)]
                    if any(value is None for value in values):
                        continue
                    annualValues[annualPeriod] = sum(values)
                else:
                    value = row["values"].get(f"{year}Q4")
                    if value is not None:
                        annualValues[annualPeriod] = value
            if not annualValues:
                continue
            annualRows.append(
                {
                    "snakeId": row["snakeId"],
                    "item": row["item"],
                    "values": annualValues,
                }
            )
        if not annualRows:
            return None
        priorityRows = annualRows
        periods = annualPeriods
        latest = annualPeriods[0]
        projection = "annual"
    else:
        latest = selectedPeriod or periods[0]
    return {
        "statement": statement,
        "label": _STMT_LABELS[statement],
        "latestPeriod": latest,
        "periods": periods,
        "projection": projection,
        "rowCount": table.height,
        "columnCount": len(table.columns),
        "rows": _projectLatest(priorityRows, latest),
        "timeseries": _projectTimeseries(priorityRows),
    }


def _findPriorityRows(statement: str, table: pl.DataFrame, periods: list[str]) -> list[dict[str, Any]]:
    """priority list (IS 8 · BS 10 · CF 8) 순회 한 번. 매칭된 row 의 모든 period 값 보존.

    SSOT: _projectLatest / _projectTimeseries 가 같은 데이터를 두 형태로 가공. priority 순회 2번
    중복 (옛 _selectRows + _selectTimeseries) 제거. 모든 period 가 None 인 row 만 skip - 한 period
    이라도 값 있으면 보존 (latest None 이면 _projectLatest 에서 제외, timeseries 는 유지).
    """
    if "snakeId" not in table.columns:
        return []
    available_periods = [p for p in periods if p in table.columns]
    if not available_periods:
        return []
    labelCol = "항목" if "항목" in table.columns else table.columns[0]
    table_rows = table.select(["snakeId", labelCol] + available_periods).to_dicts()
    available = {str(row["snakeId"]): row for row in table_rows}
    out: list[dict[str, Any]] = []
    used: set[str] = set()
    limit = 10 if statement == "BS" else 8
    for snakeId, label in _ACCOUNT_PRIORITY[statement]:
        row = available.get(snakeId) or _findRowByLabel(table_rows, label, used, labelCol=labelCol)
        if row is None:
            continue
        resolvedSnake = str(row.get("snakeId") or snakeId)
        if resolvedSnake in used:
            continue
        values = {p: row.get(p) for p in available_periods if row.get(p) is not None}
        if not values:
            continue
        used.add(resolvedSnake)
        out.append(
            {
                "snakeId": resolvedSnake,
                "item": str(row.get(labelCol) or snakeId),
                "values": values,
            }
        )
        if len(out) >= limit:
            break
    return out


def _projectLatest(priorityRows: list[dict[str, Any]], latest: str) -> list[dict[str, Any]]:
    """latest period 단일 값 형태. valueRef refs 생성 + 단일 period markdown 용."""
    out: list[dict[str, Any]] = []
    for r in priorityRows:
        value = r["values"].get(latest)
        if value is None:
            continue
        out.append(
            {
                "snakeId": r["snakeId"],
                "item": r["item"],
                "period": latest,
                "value": value,
                "formatted": formatMoney(value),
            }
        )
    return out


def _projectTimeseries(priorityRows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """전 period 시계열 형태. 시계열 markdown + 시간축 질문 답안 용."""
    return [
        {
            "snakeId": r["snakeId"],
            "item": r["item"],
            "values": r["values"],
            "formatted": {p: formatMoney(v) for p, v in r["values"].items()},
        }
        for r in priorityRows
    ]


def _findRowByLabel(rows: list[dict[str, Any]], label: str, used: set[str], *, labelCol: str) -> dict[str, Any] | None:
    compact_label = _compact(label)
    for row in rows:
        snakeId = str(row.get("snakeId") or "")
        if snakeId in used:
            continue
        item = _compact(str(row.get(labelCol) or ""))
        if compact_label and compact_label in item:
            return row
    return None


def _compact(text: str) -> str:
    return re.sub(r"[\s,()\-_/·]", "", text)


def _statementMarkdown(companyName: str, stockCode: str, statement: str, summary: dict[str, Any]) -> str:
    display = f"{companyName}({stockCode})" if companyName and stockCode else companyName or stockCode
    periods = summary.get("periods") or [summary["latestPeriod"]]
    timeseries = summary.get("timeseries") or []
    period_range = f"{periods[-1]}~{periods[0]}" if len(periods) > 1 else periods[0]
    lines = [
        f"{display} {_STMT_LABELS[statement]} 시계열을 확인했습니다 ({period_range}, {len(periods)} {'연도' if summary.get('projection') == 'annual' else '분기'}).",
        "",
        f"## {_STMT_LABELS[statement]} ({period_range})",
    ]
    if timeseries:
        header_periods = periods[:12]
        lines.append("| 항목 | " + " | ".join(header_periods) + " |")
        lines.append("|---|" + "|".join(["---:"] * len(header_periods)) + "|")
        for row in timeseries:
            formatted = row.get("formatted") or {}
            cells = [formatted.get(p, "-") for p in header_periods]
            lines.append(f"| {row['item']} | " + " | ".join(cells) + " |")
        if len(periods) > 12:
            lines.append("")
            unit = "연도" if summary.get("projection") == "annual" else "분기"
            lines.append(
                f"(직전 {len(header_periods)} {unit}만 표기. 전체 {len(periods)} {unit}는 timeseries 필드 참조)"
            )
    else:
        lines.append("| 항목 | 값 |")
        lines.append("|---|---:|")
        for row in summary["rows"]:
            lines.append(f"| {row['item']} | {row['formatted']} |")
    lines.append("")
    # 원시 수치만 건네면 마진과 증감률과 기저효과 판별을 모델이 매번 손으로 해야 하고 그
    # 계산을 잘하는 모델과 못하는 모델 사이에서 답변이 갈린다. 손에 있는 시계열로 바로
    # 계산되는 것은 표에 실어 보낸다. 추가 조회가 없으므로 지연이 늘지 않는다.
    insight = insightMarkdown(summary)
    if insight:
        lines.append(insight)
    lines.append("근거는 tableRef, valueRef, dateRef로 남겼습니다.")
    return "\n".join(lines)


def _rankGrowthRows(df: pl.DataFrame) -> list[dict[str, Any]]:
    required = {"종목코드", "종목명", "매출CAGR", "영업이익CAGR", "순이익CAGR", "등급", "패턴"}
    if not required <= set(df.columns):
        return []
    scored: list[dict[str, Any]] = []
    for row in df.to_dicts():
        values = [toFloat(row.get(col)) for col in ("매출CAGR", "영업이익CAGR", "순이익CAGR")]
        valid = [value for value in values if value is not None]
        revenue = toFloat(row.get("revenue"))
        years = toFloat(row.get("years"))
        if len(valid) < 3 or any(value <= 10 for value in valid):
            continue
        if revenue is None or revenue < 100_000_000_000:
            continue
        if years is not None and years < 3:
            continue
        score = sum(valid) / len(valid)
        scored.append(
            {
                "stockCode": str(row.get("종목코드") or ""),
                "name": str(row.get("종목명") or ""),
                "revenue": formatMoney(row.get("revenue")),
                "salesCagr": values[0],
                "operatingProfitCagr": values[1],
                "netProfitCagr": values[2],
                "years": row.get("years"),
                "grade": str(row.get("등급") or ""),
                "pattern": str(row.get("패턴") or ""),
                "score": round(score, 2),
            }
        )
    scored.sort(key=lambda item: (item["score"], item["salesCagr"] or -9999), reverse=True)
    return scored[:5]


def _growthMarkdown(rowCount: int, rows: list[dict[str, Any]]) -> str:
    lines = [f'`dartlab.scan("growth")`로 {rowCount:,}개 기업의 성장성 스캔을 확인했습니다.', ""]
    lines.append("| 순위 | 기업 | 매출CAGR | 영업이익CAGR | 순이익CAGR | 등급 | 패턴 |")
    lines.append("|---:|---|---:|---:|---:|---|---|")
    for idx, row in enumerate(rows, start=1):
        lines.append(
            f"| {idx} | {row['name']}({row['stockCode']}) | {formatPercent(row['salesCagr'])} | {formatPercent(row['operatingProfitCagr'])} | {formatPercent(row['netProfitCagr'])} | {row['grade']} | {row['pattern']} |"
        )
    lines.append("")
    lines.append(
        "이 표는 후보 발굴 단계입니다. 투자 판단으로 확정하려면 각 후보를 Company/analysis/quant로 다시 검증해야 합니다."
    )
    lines.append("근거는 scan growth datasetRef, tableRef, valueRef로 남겼습니다.")
    return "\n".join(lines)


@contextmanager
def _quietExecutionNoise():
    noisy_loggers = [logging.getLogger("dartlab.providers.dart.finance.pivot")]
    previous = [(logger, logger.disabled, logger.level) for logger in noisy_loggers]
    try:
        for logger in noisy_loggers:
            logger.disabled = True
            logger.setLevel(logging.CRITICAL + 1)
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            yield
    finally:
        for logger, disabled, level in previous:
            logger.disabled = disabled
            logger.setLevel(level)
