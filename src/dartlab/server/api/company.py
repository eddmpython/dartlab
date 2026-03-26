from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, Response
from sse_starlette.sse import EventSourceResponse

import dartlab

from ..services.ai_analysis import stream_topic_summary
from ..services.company_api import (
    build_diff_summary,
    build_toc,
    build_viewer,
    filter_blocks_by_period,
    get_company,
    safe_topic_label,
)
from .common import (
    HANDLED_API_ERRORS,
    etag_response,
    normalize_provider_name,
    sanitize_error,
    serialize_payload,
)

router = APIRouter()


@router.get("/api/search")
def api_search(q: str = Query(..., min_length=1)):
    """종목 검색 — substring 우선, 결과 없으면 fuzzy(초성/Levenshtein) fallback."""
    try:
        df = dartlab.search(q)
        rows = df.to_dicts() if len(df) > 0 else []
        fuzzy_used = False

        if not rows:
            from dartlab.gather.listing import fuzzySearch

            df = fuzzySearch(q, maxResults=20)
            rows = df.to_dicts() if len(df) > 0 else []
            fuzzy_used = bool(rows)

        mapped = []
        for row in rows[:20]:
            mapped.append(
                {
                    "corpName": row.get("회사명", row.get("corpName", "")),
                    "stockCode": row.get("종목코드", row.get("stockCode", "")),
                    "market": row.get("시장구분", ""),
                    "sector": row.get("업종", ""),
                }
            )
        return {"results": mapped, "fuzzy": fuzzy_used}
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=400, detail=sanitize_error(exc)) from exc


@router.get("/api/company/{code}")
def api_company(code: str):
    try:
        company = get_company(code)
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "surface": {
                "index": f"/api/company/{company.stockCode}/index",
                "show": f"/api/company/{company.stockCode}/show/{{topic}}",
                "trace": f"/api/company/{company.stockCode}/trace/{{topic}}",
            },
            "profile": {
                "status": "roadmap",
                "description": "변화 지점을 문서처럼 읽는 company report view가 추후 추가될 예정입니다.",
            },
        }
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc


@router.get("/api/company/{code}/index")
def api_company_index(code: str, request: Request, response: Response):
    try:
        company = get_company(code)
        data = {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "payload": serialize_payload(company.index),
        }
        return etag_response(request, response, data, max_age=300, swr=1800)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc


@router.get("/api/company/{code}/sections")
def api_company_sections(code: str, request: Request, response: Response):
    try:
        company = get_company(code)
        data = {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "payload": serialize_payload(company.sections, max_rows=5000),
        }
        return etag_response(request, response, data, max_age=300, swr=1800)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc


@router.get("/api/company/{code}/init")
def api_company_init(code: str, request: Request, response: Response):
    try:
        company = get_company(code)
        toc_data = build_toc(company)

        first_topic: str | None = None
        first_chapter: str | None = None
        chapters = toc_data.get("chapters", [])
        if chapters:
            topics = chapters[0].get("topics", [])
            if topics:
                first_topic = topics[0]["topic"]
                first_chapter = chapters[0]["chapter"]

        viewer_data = None
        diff_data = None
        if first_topic:
            viewer_data = build_viewer(company, first_topic)
            diff_data = build_diff_summary(company, first_topic)

        result = {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "toc": toc_data,
            "firstTopic": first_topic,
            "firstChapter": first_chapter,
            "viewer": viewer_data,
            "diffSummary": diff_data,
        }
        return etag_response(request, response, result, max_age=300, swr=1800)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc


@router.get("/api/company/{code}/toc")
def api_company_toc(code: str, request: Request, response: Response):
    try:
        company = get_company(code)
        data = build_toc(company)
        return etag_response(request, response, data, max_age=300, swr=1800)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc


@router.get("/api/company/{code}/viewer/{topic}")
def api_company_viewer_topic(
    code: str,
    topic: str,
    request: Request,
    period: str | None = Query(None, description="특정 기간만 반환 (타임라인 클릭 최적화)"),
    response: Response = None,
):
    try:
        company = get_company(code)

        if period is not None:
            from dartlab.providers.dart.docs.viewer import (
                serializeViewerBlock,
                serializeViewerTextDocument,
                viewerBlocks,
                viewerTextDocument,
            )

            if not hasattr(company, "_viewer_cache"):
                company._viewer_cache = {}
            if topic in company._viewer_cache:
                blocks = company._viewer_cache[topic]
            else:
                blocks = viewerBlocks(company, topic)
                company._viewer_cache[topic] = blocks
            blocks = filter_blocks_by_period(blocks, period)
            data = {
                "stockCode": company.stockCode,
                "corpName": company.corpName,
                "topic": topic,
                "topicLabel": safe_topic_label(company, topic),
                "period": period,
                "blocks": [serializeViewerBlock(block) for block in blocks],
                "textDocument": serializeViewerTextDocument(viewerTextDocument(topic, blocks)),
            }
        else:
            data = build_viewer(company, topic)

        return etag_response(request, response, data, max_age=120, swr=600)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc


@router.get("/api/company/{code}/viewer2/{topic}")
def apiViewerDoc(
    code: str,
    topic: str,
    request: Request,
    base: str | None = Query(None),
    compare: str | None = Query(None),
    response: Response = None,
):
    """sections 기반 신구대조 뷰어 — viewer() dict 반환."""
    import re

    try:
        company = get_company(code)
        sec = company.docs.sections.raw
        if sec is None:
            raise HTTPException(status_code=404, detail="sections 없음")

        if not base:
            periodRe = re.compile(r"^\d{4}(Q[1-4])?$")
            periods = sorted(
                [c for c in sec.columns if periodRe.fullmatch(c)],
                reverse=True,
            )
            base = periods[0] if periods else None

        from dartlab.core.docs.viewer import viewer

        doc = viewer(sec, topic, base, compare)
        doc["stockCode"] = company.stockCode
        doc["corpName"] = company.corpName
        doc["topicLabel"] = safe_topic_label(company, topic)
        return etag_response(request, response, doc, max_age=120, swr=600)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc


@router.post("/api/company/{code}/viewer/batch")
async def api_company_viewer_batch(code: str, request: Request, response: Response):
    """여러 topic의 viewer 데이터를 한 번에 반환 — chapter 확장 시 N+1 제거."""
    body = await request.json()
    topics = body.get("topics", [])
    if not topics or not isinstance(topics, list):
        raise HTTPException(status_code=400, detail="topics 배열 필요")
    topics = topics[:20]  # 최대 20개 제한

    try:
        company = get_company(code)
        results = {}
        for topic in topics:
            if not isinstance(topic, str):
                continue
            try:
                results[topic] = build_viewer(company, topic)
            except HANDLED_API_ERRORS:
                results[topic] = None
        return etag_response(request, response, {"results": results}, max_age=120, swr=600)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc


@router.get("/api/company/{code}/show/{topic}/all")
def api_company_show_all(code: str, topic: str, raw: bool = Query(False)):
    try:
        from dartlab.providers.dart.docs.viewer import (
            serializeViewerBlock,
            serializeViewerTextDocument,
            viewerBlocks,
            viewerTextDocument,
        )

        company = get_company(code)
        blocks = viewerBlocks(company, topic)
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "topic": topic,
            "blocks": [serializeViewerBlock(block) for block in blocks],
            "textDocument": serializeViewerTextDocument(viewerTextDocument(topic, blocks)),
        }
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc


@router.post("/api/company/{code}/show/{topic}/{block_idx}/parse")
async def api_parse_raw_table(code: str, topic: str, block_idx: int):
    try:
        from dartlab.providers.dart.docs.tableAI import parseRawMarkdownBlock
        from dartlab.providers.dart.docs.viewer import viewerBlocks

        company = get_company(code)
        blocks = viewerBlocks(company, topic)
        target = None
        for block in blocks:
            if block.block == block_idx and block.kind == "raw_markdown":
                target = block
                break
        if target is None:
            raise HTTPException(status_code=404, detail="raw_markdown 블록이 아님")

        result = await parseRawMarkdownBlock(target.rawMarkdown, topic, block_idx)
        return {
            "stockCode": company.stockCode,
            "topic": topic,
            "block": block_idx,
            "parsed": result,
        }
    except HTTPException:
        raise
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=500, detail=sanitize_error(exc)) from exc


@router.get("/api/company/{code}/show/{topic}")
def api_company_show(code: str, topic: str, block: int | None = Query(None), raw: bool = Query(False)):
    try:
        company = get_company(code)
        if block is not None:
            result = company.show(topic, block, period=None, raw=raw)
        else:
            result = company.show(topic)
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "topic": topic,
            "block": block,
            "payload": serialize_payload(result),
        }
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc


@router.get("/api/company/{code}/trace/{topic}")
def api_company_trace(code: str, topic: str):
    try:
        company = get_company(code)
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "topic": topic,
            "payload": serialize_payload(company.trace(topic)),
        }
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc


@router.get("/api/company/{code}/summary/{topic}")
async def api_company_topic_summary(
    code: str,
    topic: str,
    provider: str | None = None,
    model: str | None = None,
):
    try:
        company = get_company(code)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc

    try:
        overview = company.show(topic)
    except (AttributeError, KeyError, TypeError, ValueError):
        overview = None
    if overview is None:
        raise HTTPException(status_code=404, detail=f"topic '{topic}' 데이터 없음")

    return EventSourceResponse(
        stream_topic_summary(
            company,
            topic,
            provider=normalize_provider_name(provider) or provider,
            model=model,
        )
    )


@router.get("/api/company/{code}/insights")
def api_company_insights(code: str):
    try:
        company = get_company(code)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc

    from dartlab.analysis.financial.insight.pipeline import analyze as insight_analyze

    try:
        result = insight_analyze(company.stockCode, company=company)
    except HANDLED_API_ERRORS:
        result = None

    if result is None:
        return {"stockCode": company.stockCode, "corpName": company.corpName, "available": False}

    def _flag_dict(flag):
        return {"level": flag.level, "category": flag.category, "text": flag.text}

    def _insight_dict(insight):
        return {
            "grade": insight.grade,
            "summary": insight.summary,
            "details": insight.details,
            "risks": [_flag_dict(risk) for risk in insight.risks],
            "opportunities": [_flag_dict(opportunity) for opportunity in insight.opportunities],
        }

    def _anomaly_dict(anomaly):
        return {
            "severity": anomaly.severity,
            "category": anomaly.category,
            "text": anomaly.text,
            "value": anomaly.value,
        }

    return {
        "stockCode": company.stockCode,
        "corpName": company.corpName,
        "available": True,
        "isFinancial": result.isFinancial,
        "grades": result.grades(),
        "areas": {
            "performance": _insight_dict(result.performance),
            "profitability": _insight_dict(result.profitability),
            "health": _insight_dict(result.health),
            "cashflow": _insight_dict(result.cashflow),
            "governance": _insight_dict(result.governance),
            "risk": _insight_dict(result.risk),
            "opportunity": _insight_dict(result.opportunity),
        },
        "anomalies": [_anomaly_dict(anomaly) for anomaly in result.anomalies],
        "summary": result.summary,
        "profile": result.profile,
    }


@router.get("/api/company/{code}/network")
def api_company_network(code: str, hops: int = 1):
    hops = max(1, min(hops, 3))
    try:
        company = get_company(code)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc

    try:
        result = company._ensureNetwork()
        if result is None:
            return {"stockCode": company.stockCode, "corpName": company.corpName, "available": False}
        data, full = result

        from dartlab.market.network.export import export_ego

        ego = export_ego(data, full, company.stockCode, hops=hops)
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "available": True,
            **ego,
        }
    except HANDLED_API_ERRORS:
        return {"stockCode": company.stockCode, "corpName": company.corpName, "available": False}


@router.get("/api/company/{code}/scan/{axis}")
def api_company_scan(code: str, axis: str):
    try:
        company = get_company(code)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc

    valid_axes = {"governance", "workforce", "capital", "debt"}

    if axis == "all":
        results = {}
        for current_axis in valid_axes:
            method = getattr(company, current_axis, None)
            if method is None:
                continue
            try:
                df = method()
                if df is not None and not df.is_empty():
                    results[current_axis] = serialize_payload(df)
            except HANDLED_API_ERRORS:
                continue
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "available": bool(results),
            "scans": results,
        }

    if axis not in valid_axes:
        raise HTTPException(status_code=400, detail=f"유효한 축: {', '.join(sorted(valid_axes))}, all")

    method = getattr(company, axis, None)
    if method is None:
        return {"stockCode": company.stockCode, "corpName": company.corpName, "available": False}

    try:
        df = method()
        if df is None or df.is_empty():
            return {"stockCode": company.stockCode, "corpName": company.corpName, "available": False}
        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "available": True,
            "scanType": axis,
            "payload": serialize_payload(df),
        }
    except HANDLED_API_ERRORS:
        return {"stockCode": company.stockCode, "corpName": company.corpName, "available": False}


@router.get("/api/company/{code}/scan/position")
def api_company_scan_position(code: str):
    from dartlab.market.snapshot import getScanPosition

    position = getScanPosition(code)
    if position is None:
        raise HTTPException(status_code=404, detail="scan 스냅샷 없음 — buildScanSnapshot() 선행 필요")

    return {
        "stockCode": code,
        "available": True,
        "position": position,
    }


@router.get("/api/company/{code}/insights/unified")
def api_company_insights_unified(code: str):
    try:
        company = get_company(code)
    except HANDLED_API_ERRORS as exc:
        raise HTTPException(status_code=404, detail=sanitize_error(exc)) from exc

    from dartlab.market.payload import build_unified_payload

    try:
        unified = build_unified_payload(company)
    except HANDLED_API_ERRORS:
        unified = {}

    return {
        "stockCode": company.stockCode,
        "corpName": company.corpName,
        "available": bool(unified),
        "areas": unified,
    }
