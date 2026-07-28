"""Generated-spec validated DartLab engine call tool."""

from __future__ import annotations

import logging
import math
import os
import re
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from io import StringIO
from typing import Any

import polars as pl

from dartlab.ai.contracts import Ref
from dartlab.core.confidence import baseScore as _baseScore

from .creditBadge import getDcrBadge
from .filingDeepLink import attachDocRef, buildPeriodToFiling
from .formatting import formatMoney, formatPercent
from .industryContext import getIndustryBadge
from .types import ToolResult

_FILING_DIRECT_CONFIDENCE = _baseScore("filing_direct")

_JSON_PREVIEW_ROWS = 20
_JSON_MAX_DEPTH = 50

_AUTO_GATHER_ENABLED = os.environ.get("DARTLAB_AUTO_GATHER", "1") not in {"0", "false", "False"}

_PERIOD_RE = re.compile(r"^\d{4}(?:Q[1-4])?$")
_STMT_LABELS = {"BS": "재무상태표", "IS": "손익계산서", "CF": "현금흐름표"}
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

    if apiRef == "Company.panel":
        return _companyShow(call_plan)
    if apiRef == "scan" or apiRef.startswith("scan."):
        if apiRef.startswith("scan.") and not call_plan.get("axis"):
            call_plan["axis"] = apiRef.split(".", 1)[1]
        return _scan(call_plan)
    if apiRef == "capabilities":
        return _capabilities(call_plan)
    # gather 표준 {engine}.{axis} 일반 디스패치 (gather.price·industry.theme·credit.grade·quant.모멘텀).
    head = apiRef.split(".", 1)[0]
    if "." in apiRef and head in _AXIS_ENGINES:
        return _axisEngineCall(head, apiRef.split(".", 1)[1], call_plan)
    return _genericPublicCall(apiRef, call_plan)


# gather 표준 axis-dispatch 엔진 (scan 은 위 전용 핸들러). credit/analysis 는 함수형이나 axis-first 동일.
_AXIS_ENGINES = frozenset({"gather", "macro", "industry", "quant", "credit", "analysis"})


def _axisEngineCall(engine: str, axis: str, plan: dict[str, Any]) -> ToolResult:
    """``{engine}.{axis}`` → ``dartlab.{engine}(axis, target, **kwargs)`` 위임 (gather 표준 통일)."""
    import dartlab

    fn = getattr(dartlab, engine, None)
    if fn is None or not callable(fn):
        return ToolResult(False, f"axis-engine 을 찾지 못했습니다: {engine}", error="unknown_engine")
    target = plan.get("target") or plan.get("stockCode") or None
    kwargs = dict(plan.get("kwargs") or {})
    with _quietExecutionNoise():
        result = fn(axis, target, **kwargs)
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
    target = str(plan.get("target") or plan.get("stockCode") or "").strip()
    topic = _resolveTopic(plan)
    if topic not in _STMT_LABELS:
        # 공개 show 은퇴 - docs/report 토픽은 panel facade 로 (finance/report 주입 + raw 검색).
        return _genericCompanyMethod("panel", target, [topic], {})
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
    summary = _summarizeStatement(topic, table)
    if not summary:
        return ToolResult(
            False, f"{companyName or stockCode} {topic} 표를 요약하지 못했습니다.", error="unreadable_table"
        )
    refs = _buildShowRefs(stockCode, companyName, topic, summary, company)
    summaryMsg = _showSummaryMessage(companyName, stockCode, topic, summary, autoGatherUsed)
    data = _buildShowData(company, companyName, stockCode, topic, summary, autoGatherUsed)
    return ToolResult(True, summaryMsg, refs=refs, data=data)


def _resolveTopic(plan: dict[str, Any]) -> str:
    """plan → topic 결정. args (list/dict) · kwargs · topic 키 검사 후 한글 별칭 정규화."""
    args = list(plan.get("args") or [])
    kwargs = dict(plan.get("kwargs") or {})
    raw = str(plan.get("topic") or (args[0] if args else "") or kwargs.get("topic") or "").strip() or "BS"
    return _normalizeStatement(raw)


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

    def enrich(base: dict[str, Any]) -> dict[str, Any]:
        """payload 에 docRef + confidence (filing_direct=95) + confidenceMethod 부착."""
        out = attachDocRef(base, latestPeriod, filingMap)
        out.setdefault("confidence", _FILING_DIRECT_CONFIDENCE)
        out.setdefault("confidenceMethod", "filing_direct")
        return out

    tableRef = Ref(
        id=f"table:{stockCode}:{topic}:{latestPeriod}",
        kind="tableRef",
        title=f"{companyName or stockCode} {_STMT_LABELS[topic]} {latestPeriod}",
        source=f"Company({stockCode}).panel('{topic}')",
        payload=enrich(summary),
    )
    refs: list[Ref] = [tableRef]
    refs.extend(
        Ref(
            id=f"value:{stockCode}:{topic}:{latestPeriod}:{row['snakeId']}",
            kind="valueRef",
            title=f"{row['item']} {latestPeriod}",
            source=tableRef.id,
            payload={**enrich(row), "provenance": [tableRef.id]},
        )
        for row in summary["rows"]
    )
    creditRef = _buildCreditRef(stockCode, companyName, company)
    if creditRef is not None:
        refs.append(creditRef)
    industryRef = _buildIndustryRef(stockCode, companyName, company)
    if industryRef is not None:
        refs.append(industryRef)
    refs.append(
        Ref(
            id=f"date:{stockCode}:{topic}:{latestPeriod}",
            kind="dateRef",
            title=f"{_STMT_LABELS[topic]} 기준시점",
            source=tableRef.id,
            payload={**enrich({"period": latestPeriod}), "provenance": [tableRef.id]},
        )
    )
    return refs


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
    scored = [(a.get("name"), a.get("score"), a.get("weight")) for a in axes if a.get("score") is not None]
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
    periodLabel = f"{periods[-1]}~{periods[0]} ({len(periods)} 분기)" if len(periods) > 1 else periods[0]
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
        with _quietExecutionNoise():
            result = dartlab.scan(axis, target, **callKwargs)
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
    table_ref = Ref(
        id=f"table:scan:{axis}:preview",
        kind="tableRef",
        title=f"scan {axis} preview",
        source=f"dartlab.scan('{axis}')",
        payload={"rowCount": result.height, "columns": list(result.columns), "rows": result.head(10).to_dicts()},
    )
    return ToolResult(
        True,
        f"scan {axis} 실행 완료",
        refs=[table_ref],
        data={"rowCount": result.height, "columns": list(result.columns)},
    )


def _capabilities(plan: dict[str, Any]) -> ToolResult:
    import dartlab

    args = list(plan.get("args") or [])
    path = str(plan.get("path") or (args[0] if args else "") or "").strip()
    data = dartlab.capabilities(path) if path else dartlab.capabilities()
    markdown = _capabilitiesMarkdown(data, path=path)
    ref = Ref(
        id=f"api:dartlab.capabilities:{path or 'root'}",
        kind="apiRef",
        title="dartlab.capabilities",
        source="dartlab.capabilities",
        payload={"path": path, "preview": str(data)[:4000]},
    )
    return ToolResult(True, "capabilities 조회 완료", refs=[ref], data={"result": str(data), "markdown": markdown})


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
    text = str(value or "").splitlines()[0]
    text = text.replace(" - 내부 구현", "").replace("(내부 구현)", "").replace("**", "")
    return text[:180]


def _genericPublicCall(apiRef: str, plan: dict[str, Any]) -> ToolResult:
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
        result = func(*list(plan.get("args") or []), **dict(plan.get("kwargs") or {}))
        return _resultToRefs(apiRef, result)
    return ToolResult(False, f"지원하지 않는 apiRef입니다: {apiRef}", error="unsupported_api_ref")


def _genericCompanyMethod(method: str, target: str, args: list[Any], kwargs: dict[str, Any]) -> ToolResult:
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
        table_ref = Ref(
            id=f"table:{apiRef}:{target or 'result'}",
            kind="tableRef",
            title=f"{apiRef} result",
            source=apiRef,
            payload={"rowCount": result.height, "columns": list(result.columns), "rows": result.head(20).to_dicts()},
        )
        return ToolResult(
            True,
            f"{apiRef} 실행 완료",
            refs=[table_ref],
            data={"rowCount": result.height, "columns": list(result.columns)},
        )
    if isinstance(result, dict | list | tuple) or is_dataclass(result):
        payload = _jsonableResult(result)
        refs = [
            Ref(
                id=f"execution:{apiRef}:{target or 'result'}",
                kind="executionRef",
                title=f"{apiRef} result",
                source=apiRef,
                payload={"result": payload, "preview": str(payload)[:4000]},
            )
        ]
        refs.extend(_lensRefs(apiRef, payload, target=target))
        return ToolResult(True, f"{apiRef} 실행 완료", refs=refs, data={"result": payload})
    ref = Ref(
        id=f"execution:{apiRef}:{target or 'result'}",
        kind="executionRef",
        title=f"{apiRef} result",
        source=apiRef,
        payload={"preview": str(result)[:4000]},
    )
    return ToolResult(True, f"{apiRef} 실행 완료", refs=[ref], data={"result": str(result)})


def _jsonableResult(value: Any, _depth: int = 0) -> Any:
    """ToolResult payload를 bounded JSON-safe 구조로 변환한다.

    DataFrame과 Series는 전체 값을 문자열로 만들지 않는다. 실제 크기와 제한된 preview를
    함께 보존해 query의 ``truncated``와 ``continuation`` 의미를 덮어쓰지 않는다.
    """
    if _depth > _JSON_MAX_DEPTH:
        return {"_type": type(value).__name__, "previewTruncated": True, "reason": "maxDepth"}
    if value is None or isinstance(value, str | int | bool):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, pl.DataFrame):
        preview = value.head(_JSON_PREVIEW_ROWS)
        return {
            "_type": "DataFrame",
            "rowCount": value.height,
            "previewRowCount": preview.height,
            "columns": list(value.columns),
            "schema": [
                {"name": name, "dtype": str(dtype)} for name, dtype in zip(value.columns, value.dtypes, strict=True)
            ],
            "rows": [_jsonableResult(row, _depth + 1) for row in preview.to_dicts()],
            "previewTruncated": value.height > preview.height,
        }
    if isinstance(value, pl.Series):
        preview = value.head(_JSON_PREVIEW_ROWS)
        return {
            "_type": "Series",
            "name": value.name,
            "dtype": str(value.dtype),
            "length": value.len(),
            "previewLength": preview.len(),
            "values": [_jsonableResult(item, _depth + 1) for item in preview.to_list()],
            "previewTruncated": value.len() > preview.len(),
        }
    if isinstance(value, dict):
        return {str(k): _jsonableResult(v, _depth + 1) for k, v in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        items = sorted(value, key=str) if isinstance(value, set | frozenset) else value
        return [_jsonableResult(item, _depth + 1) for item in items]
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _jsonableResult(getattr(value, field.name), _depth + 1) for field in fields(value)}
    return str(value)


def _lensRefs(apiRef: str, payload: Any, *, target: str) -> list[Ref]:
    """Lens Product의 직접 결론과 시간 경계를 근거 ref로 만든다."""
    refs: list[Ref] = []
    for engine, product in _findLensProducts(payload):
        identity = product.get("identity") if isinstance(product.get("identity"), dict) else {}
        conclusion = product.get("conclusion") if isinstance(product.get("conclusion"), dict) else {}
        confidence = product.get("confidence") if isinstance(product.get("confidence"), dict) else {}
        time = product.get("time") if isinstance(product.get("time"), dict) else {}
        refTarget = str(identity.get("target") or target or "result")
        axis = str(identity.get("axis") or "representative")
        stem = _refStem(refTarget, engine, axis)
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
                    "label": conclusion.get("label"),
                    "summary": conclusion.get("summary"),
                    "confidence": confidence.get("score"),
                    "confidenceLevel": confidence.get("level"),
                    "confidenceMethod": confidence.get("method"),
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
        productMap = value.get("products") if isinstance(value.get("products"), dict) else value
        candidates.extend(row for row in productMap.values() if isinstance(row, dict))

    rows: list[tuple[str, dict[str, Any]]] = []
    seen: set[tuple[str, str, str]] = set()
    for product in candidates:
        identity = product.get("identity") if isinstance(product.get("identity"), dict) else {}
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
            with _quietExecutionNoise():
                return dartlab.Company(target)
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


def _summarizeStatement(statement: str, table: pl.DataFrame) -> dict[str, Any] | None:
    periods = [col for col in table.columns if _PERIOD_RE.match(str(col))]
    if not periods:
        return None
    priorityRows = _findPriorityRows(statement, table, periods)
    if not priorityRows:
        return None
    latest = periods[0]
    return {
        "statement": statement,
        "label": _STMT_LABELS[statement],
        "latestPeriod": latest,
        "periods": periods,
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
        f"{display} {_STMT_LABELS[statement]} 시계열을 확인했습니다 ({period_range}, {len(periods)} 분기).",
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
            lines.append(f"(직전 {len(header_periods)} 분기만 표기. 전체 {len(periods)} 분기는 timeseries 필드 참조)")
    else:
        lines.append("| 항목 | 값 |")
        lines.append("|---|---:|")
        for row in summary["rows"]:
            lines.append(f"| {row['item']} | {row['formatted']} |")
    lines.append("")
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
