"""Company 분석 엔드포인트 — diff, bridge, graph, search, modules."""

from __future__ import annotations

import re as _re
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response

from ..services.company_api import (
    build_diff_summary,
    get_company,
    safe_topic_label,
)
from .common import (
    HANDLED_API_ERRORS,
    etag_response,
    guideDetail,
    serialize_payload,
)

router = APIRouter()


@router.get("/api/company/{code}/diff")
def api_company_diff(code: str):
    """Company sections 전체 diff 요약."""
    try:
        c = get_company(code)
        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "payload": serialize_payload(c.diff()),
        }
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))


@router.get("/api/company/{code}/diff/matrix")
def api_company_diff_matrix(
    code: str,
    textOnly: bool = Query(False),
    topN: int = Query(20),
):
    """topic × period 변화 매트릭스 + 히트맵 스펙."""
    try:
        c = get_company(code)
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    from dartlab.core.docs.diff import build_diff_matrix, build_heatmap_spec

    try:
        sections = c.docs.sections.raw
        matrix_data = build_diff_matrix(sections, textOnly=textOnly)
        heatmap = build_heatmap_spec(matrix_data, c.corpName, top_n=topN)
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    return {
        "stockCode": c.stockCode,
        "corpName": c.corpName,
        "matrix": matrix_data,
        "heatmap": heatmap,
    }


@router.get("/api/company/{code}/diff/{topic}/summary")
def api_company_diff_topic_summary(code: str, topic: str):
    """뷰어용 diff 요약 — changeRate + 최신 변경의 added/removed 미리보기."""
    try:
        c = get_company(code)
        result = build_diff_summary(c, topic)
        if result is None:
            raise HTTPException(status_code=404, detail="sections 없음")
        return result
    except HTTPException:
        raise
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))


@router.get("/api/company/{code}/diff/{topic}")
def api_company_diff_topic(
    code: str,
    topic: str,
    fromPeriod: str = Query(..., alias="from"),
    toPeriod: str = Query(..., alias="to"),
):
    """Company 특정 topic의 두 기간 줄+글자 단위 diff."""
    try:
        c = get_company(code)
        result = c.diff(topic, fromPeriod, toPeriod)

        diff_chunks: list[dict] = []
        if result is not None:
            from dartlab.core.docs.diff import charDiff

            rows = result.to_dicts()
            i = 0
            while i < len(rows):
                row = rows[i]
                status = row.get("status", " ")
                text = row.get("text", "")

                if status == " ":
                    diff_chunks.append({"kind": "same", "text": text})
                    i += 1
                elif status == "-":
                    del_lines = [text]
                    j = i + 1
                    while j < len(rows) and rows[j].get("status") == "-":
                        del_lines.append(rows[j].get("text", ""))
                        j += 1
                    add_lines = []
                    while j < len(rows) and rows[j].get("status") == "+":
                        add_lines.append(rows[j].get("text", ""))
                        j += 1

                    if add_lines:
                        from_text = "\n".join(del_lines)
                        to_text = "\n".join(add_lines)
                        parts = [{"kind": p.kind, "text": p.text} for p in charDiff(from_text, to_text)]
                        diff_chunks.append({"kind": "removed", "text": from_text, "parts": parts})
                        diff_chunks.append({"kind": "added", "text": to_text, "parts": parts})
                    else:
                        for line in del_lines:
                            diff_chunks.append({"kind": "removed", "text": line})
                    i = j
                elif status == "+":
                    diff_chunks.append({"kind": "added", "text": text})
                    i += 1
                else:
                    i += 1

        return {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "topic": topic,
            "fromPeriod": fromPeriod,
            "toPeriod": toPeriod,
            "diff": diff_chunks,
        }
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))


@router.get("/api/company/{code}/bridge/{topic}")
def api_company_bridge(
    code: str,
    topic: str,
    period: str = Query("latest"),
    tolerance: float = Query(0.05),
):
    """텍스트-재무 숫자 교차 참조."""
    try:
        c = get_company(code)
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    import polars as pl

    from dartlab.core.docs.bridge import (
        extract_amounts_from_text,
        get_finance_amounts,
        match_amounts,
    )

    try:
        sections = c.docs.sections.raw
        periods = sorted(
            [col for col in sections.columns if _re.fullmatch(r"\d{4}(Q[1-4])?", col)],
            reverse=True,
        )
        if not periods:
            raise HTTPException(status_code=404, detail="기간 없음")

        target_period = periods[0] if period == "latest" else period
        if target_period not in sections.columns:
            raise HTTPException(status_code=400, detail=f"기간 {target_period} 없음")

        topic_rows = sections.filter((pl.col("topic") == topic) & (pl.col("blockType") == "text"))
        if topic_rows.height == 0:
            raise HTTPException(status_code=404, detail=f"topic {topic} 텍스트 없음")

        texts = topic_rows[target_period].drop_nulls().to_list()
        full_text = "\n".join(str(t) for t in texts if t)

        text_amounts = extract_amounts_from_text(full_text)
        finance_amounts = get_finance_amounts(c, target_period)
        matched = match_amounts(text_amounts, finance_amounts, tolerance=tolerance)
    except HTTPException:
        raise
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    return {
        "stockCode": c.stockCode,
        "corpName": c.corpName,
        "topic": topic,
        "period": target_period,
        "extracted": len(text_amounts),
        "matched": len(matched),
        "matchRate": round(len(matched) / max(len(text_amounts), 1), 3),
        "matches": matched,
    }


@router.get("/api/company/{code}/topics/graph")
def api_company_topics_graph(
    code: str,
    threshold: int = Query(3),
):
    """topic간 상호 참조 그래프."""
    try:
        c = get_company(code)
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    from dartlab.core.docs.topicGraph import (
        analyze_graph,
        build_mention_matrix,
    )

    try:
        sections = c.docs.sections.raw
        matrix = build_mention_matrix(sections)
        analysis = analyze_graph(matrix.get("adjacency", {}), threshold=threshold)

        edges = [{"source": src, "target": tgt, "weight": cnt} for (src, tgt), cnt in analysis.get("top_edges", [])]
        hubs = [{"topic": t, "degree": d} for t, d in analysis.get("hubs", [])]
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))

    return {
        "stockCode": c.stockCode,
        "corpName": c.corpName,
        "period": matrix.get("period"),
        "edges": analysis.get("edges", 0),
        "nodes": analysis.get("nodes", 0),
        "avgDegree": analysis.get("avg_degree", 0),
        "hubs": hubs,
        "topEdges": edges,
    }


@router.get("/api/company/{code}/search")
def api_company_search_sections(code: str, q: str = Query("", description="검색어")):
    """현재 회사의 sections 전체 텍스트에서 substring 검색."""
    try:
        c = get_company(code)
        sec = c.sections
        if sec is None or not q.strip():
            return {"stockCode": c.stockCode, "corpName": c.corpName, "results": []}

        query = q.strip().lower()
        period_re = _re.compile(r"^\d{4}(Q[1-4])?$")
        period_cols = [col for col in sec.columns if period_re.fullmatch(col)]

        results = []
        seen_topics: set[str] = set()
        for row in sec.iter_rows(named=True):
            topic = row.get("topic", "")
            if not topic or topic in seen_topics:
                continue
            bt = str(row.get("blockType", ""))
            if bt != "text":
                continue
            for p in period_cols:
                val = row.get(p)
                if not val or not isinstance(val, str):
                    continue
                lower_val = val.lower()
                if query in lower_val:
                    idx = lower_val.index(query)
                    start = max(0, idx - 40)
                    end = min(len(val), idx + len(query) + 60)
                    snippet = ("..." if start > 0 else "") + val[start:end].strip() + ("..." if end < len(val) else "")
                    match_count = lower_val.count(query)
                    results.append(
                        {
                            "topic": topic,
                            "label": safe_topic_label(c, topic),
                            "period": p,
                            "snippet": snippet,
                            "matchCount": match_count,
                        }
                    )
                    seen_topics.add(topic)
                    break
            if len(results) >= 30:
                break

        return {"stockCode": c.stockCode, "corpName": c.corpName, "query": q, "results": results}
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))


@router.get("/api/company/{code}/searchIndex")
def api_company_search_index(code: str, request: Request, response: Response):
    """MiniSearch 인덱스용 flat document list.

    회사의 sections 전체를 topic × period × blockType 단위 문서로 평탄화하여 반환.
    브라우저에서 MiniSearch.addAll() → 즉시 fuzzy/prefix/BM25 검색 가능.
    text는 300자로 제한, 문서 수는 최대 1000개로 경량화.
    """
    _MAX_DOCS = 1000
    _MAX_TEXT_LEN = 300

    try:
        c = get_company(code)
        sec = c.sections
        if sec is None:
            return {"stockCode": c.stockCode, "corpName": c.corpName, "documents": []}

        period_re = _re.compile(r"^\d{4}(Q[1-4])?$")
        period_cols = [col for col in sec.columns if period_re.fullmatch(col)]

        documents: list[dict[str, Any]] = []
        doc_id = 0
        for row in sec.iter_rows(named=True):
            if doc_id >= _MAX_DOCS:
                break
            topic = row.get("topic", "")
            block_type = str(row.get("blockType", ""))
            block_order = row.get("blockOrder", 0)
            chapter = row.get("chapter", "")
            label = safe_topic_label(c, topic)

            for p in period_cols:
                if doc_id >= _MAX_DOCS:
                    break
                val = row.get(p)
                if not val or not isinstance(val, str):
                    continue
                text = val[:_MAX_TEXT_LEN] if len(val) > _MAX_TEXT_LEN else val
                documents.append(
                    {
                        "id": doc_id,
                        "topic": topic,
                        "label": label,
                        "chapter": chapter,
                        "period": p,
                        "blockType": block_type,
                        "blockOrder": block_order,
                        "text": text,
                    }
                )
                doc_id += 1

        data = {
            "stockCode": c.stockCode,
            "corpName": c.corpName,
            "documentCount": len(documents),
            "truncated": doc_id >= _MAX_DOCS,
            "documents": documents,
        }
        return etag_response(request, response, data, max_age=600, swr=1800)
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))


@router.get("/api/company/{code}/modules")
def api_company_modules(code: str):
    """기업의 사용 가능한 데이터 모듈 목록."""
    try:
        c = get_company(code)
        # scan_available_modules 제거됨 — topics 목록으로 대체
        topics = getattr(c, "topics", None)
        modules = list(topics) if topics else []
        return {"stockCode": c.stockCode, "corpName": c.corpName, "modules": modules}
    except HANDLED_API_ERRORS as e:
        raise HTTPException(status_code=404, detail=guideDetail(e))
