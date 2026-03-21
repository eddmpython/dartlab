"""Company 핵심 API 도구 — show/topics/trace/diff/sections/block/info."""

from __future__ import annotations

from typing import Any

import polars as pl

from .helpers import df_to_md, format_tool_value, maybe_int


def register_company_tools(company: Any, register_tool) -> None:
    """Company 바인딩 핵심 도구를 등록한다."""
    from dartlab.core.capabilities import CapabilityKind

    def show_topic(topic: str, block: str = "") -> str:
        if not hasattr(company, "show"):
            return "show() 인터페이스가 없습니다."
        block_idx = maybe_int(block)
        try:
            result = company.show(topic) if block_idx is None else company.show(topic, block_idx)
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            return f"show('{topic}') 실패: {e}"
        return format_tool_value(result, max_rows=30, max_chars=6000)

    register_tool(
        "show_topic",
        show_topic,
        "공시 topic의 데이터를 조회합니다. 공시 원문(텍스트/테이블)을 읽을 때 가장 먼저 사용하세요. "
        "block 없이 호출 → 블록 목차(block번호, type, source, preview). "
        "block=N → 해당 블록의 실제 데이터(원문 텍스트 또는 수치 테이블). "
        "사용 시점: 사업 내용, 리스크, 배당 정책 등 공시 원문이 필요할 때. "
        "사용하지 말 것: 단순 재무 수치만 필요하면 get_data(BS/IS/CF)가 더 빠릅니다. "
        "topic을 모르면 먼저 list_topics를 호출하세요.",
        {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "조회할 topic (예: businessOverview, riskFactor, BS, IS, CF, dividend)",
                },
                "block": {
                    "type": "string",
                    "description": "블록 인덱스. 비워두면 블록 목차, 숫자면 해당 블록 데이터",
                    "default": "",
                },
            },
            "required": ["topic"],
        },
    )

    def list_topics() -> str:
        topics = getattr(company, "topics", None)
        if topics is None:
            return "topics 속성이 없습니다."
        topic_list = list(topics) if not isinstance(topics, list) else topics
        if not topic_list:
            return "사용 가능한 topic이 없습니다."
        index_df = getattr(company, "index", None)
        if isinstance(index_df, pl.DataFrame) and index_df.height > 0:
            return df_to_md(index_df, max_rows=60)
        return "\n".join(f"- {t}" for t in topic_list)

    register_tool(
        "list_topics",
        list_topics,
        "이 기업에서 조회 가능한 모든 공시 topic 목록을 반환합니다. "
        "각 topic의 라벨, 데이터 종류(docs/finance/report), 기간 수를 포함합니다. "
        "사용 시점: show_topic에 넣을 topic을 모를 때, '어떤 공시가 있어?' 질문에 답할 때. "
        "사용하지 말 것: 이미 topic을 알고 있으면 바로 show_topic을 호출하세요.",
        {"type": "object", "properties": {}},
    )

    def trace_topic(topic: str) -> str:
        if not hasattr(company, "trace"):
            return "trace() 인터페이스가 없습니다."
        try:
            result = company.trace(topic)
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            return f"trace('{topic}') 실패: {e}"
        return format_tool_value(result, max_rows=20, max_chars=3000)

    register_tool(
        "trace_topic",
        trace_topic,
        "topic 데이터의 출처를 추적합니다. "
        "각 블록이 docs(공시원문), finance(재무제표), report(정기보고서) 중 어디서 왔는지 확인합니다. "
        "사용 시점: 데이터 신뢰성을 확인할 때, 수치의 원본 소스를 밝힐 때. "
        "사용하지 말 것: 데이터 내용 자체를 보려면 show_topic을 사용하세요.",
        {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "추적할 topic (예: businessOverview, IS, dividend)",
                },
            },
            "required": ["topic"],
        },
    )

    def diff_topic(topic: str = "") -> str:
        if not hasattr(company, "diff"):
            return "diff() 인터페이스가 없습니다."
        try:
            result = company.diff(topic) if topic else company.diff()
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            return f"diff('{topic}') 실패: {e}"
        return format_tool_value(result, max_rows=20, max_chars=4000)

    register_tool(
        "diff_topic",
        diff_topic,
        "공시 텍스트의 기간간 변화를 분석합니다. "
        "topic 없이 호출 → 전체 topic의 변화율 요약 (어디가 많이 바뀌었는지). "
        "topic 지정 → 해당 topic의 기간별 상세 변화(추가/삭제/수정). "
        "사용 시점: '뭐가 바뀌었어?', '리스크 변화', '사업 구조 변경' 같은 변화 감지 질문. "
        "사용하지 말 것: 현재 시점의 데이터만 필요하면 show_topic이 적절합니다.",
        {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "분석할 topic. 비워두면 전체 요약",
                    "default": "",
                },
            },
        },
    )

    def get_sections() -> str:
        sec = company.sections
        if sec is None:
            return "sections 데이터가 없습니다."
        topics = []
        seen: set[str] = set()
        for row in sec.to_dicts():
            t = row.get("topic", "")
            if t not in seen:
                seen.add(t)
                src = row.get("source", "docs")
                ch = row.get("chapter", "")
                topics.append(f"| {ch} | `{t}` | {src} |")
        lines = ["| 장 | topic | source |", "| --- | --- | --- |"] + topics
        return "\n".join(lines)

    register_tool(
        "get_sections",
        get_sections,
        "기업의 전체 공시 지도(sections)를 조회합니다. "
        "어떤 topic이 어떤 장(chapter)에 있는지, source(docs/finance/report)가 무엇인지 확인. "
        "show(topic, block)으로 접근하기 전에 먼저 이 도구로 전체 구조를 파악하세요.",
        {"type": "object", "properties": {}},
    )

    def show_block(topic: str, block: int | None = None) -> str:
        if block is None:
            result = company.show(topic)
        else:
            result = company.show(topic, block)
        if result is None:
            return f"'{topic}' block={block} 데이터가 없습니다."
        if isinstance(result, pl.DataFrame):
            return df_to_md(result, max_rows=30)
        return str(result)[:3000]

    register_tool(
        "show_block",
        show_block,
        "sections의 특정 topic/block 데이터를 조회합니다. "
        "block=null이면 블록 목차(block, type, source, preview)를 반환. "
        "block=N이면 해당 블록의 실제 데이터(text 또는 수평화 table)를 반환. "
        "get_sections로 topic 목록을 확인한 뒤 사용하세요.",
        {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "topic명 (예: companyOverview, dividend, BS)",
                },
                "block": {
                    "type": "integer",
                    "description": "blockOrder (null이면 블록 목차, 숫자면 해당 블록 데이터)",
                },
            },
            "required": ["topic"],
        },
    )

    def get_company_info() -> str:
        info_parts = [
            f"기업명: {company.corpName}",
            f"종목코드: {getattr(company, 'stockCode', getattr(company, 'ticker', ''))}",
        ]
        overview = company.show("companyOverview") if hasattr(company, "show") else None
        if isinstance(overview, dict):
            for key in ("ceo", "mainBusiness", "indutyName", "foundedDate"):
                if overview.get(key):
                    info_parts.append(f"{key}: {overview[key]}")
        return "\n".join(info_parts)

    register_tool(
        "get_company_info",
        get_company_info,
        "기업의 기본 정보(기업명, 종목코드, 대표자, 주요사업, 업종)를 조회합니다. "
        "사용 시점: 기업 개요 파악, 분석 시작 시 기본 정보 확인. "
        "사용하지 말 것: 재무 수치가 필요하면 get_data, 공시 원문은 show_topic을 사용하세요.",
        {"type": "object", "properties": {}},
        kind=CapabilityKind.DATA,
        requires_company=True,
    )

    # ── 중복 등록: search / download / data_status (company-bound) ──

    def search_company(keyword: str) -> str:
        from dartlab.core.kindList import searchName

        results = searchName(keyword)
        if results is None or (isinstance(results, pl.DataFrame) and results.is_empty()):
            return f"'{keyword}' 검색 결과가 없습니다."
        if isinstance(results, pl.DataFrame):
            return df_to_md(results, max_rows=20)
        return str(results)[:2000]

    register_tool(
        "search_company",
        search_company,
        "종목명/종목코드로 기업을 검색합니다. 종목코드를 모를 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "검색 키워드 (예: '삼성', '현대차', '반도체')",
                },
            },
            "required": ["keyword"],
        },
    )

    def download_data(stock_code: str = "", category: str = "docs") -> str:
        from dartlab.core.dataLoader import downloadAll, loadData

        if category == "edgarDocs" and not stock_code:
            return (
                "EDGAR docs는 ticker를 지정한 개별 수집 경로를 사용하세요. 예: stock_code='AAPL', category='edgarDocs'"
            )
        if stock_code:
            loadData(stock_code, category=category)
            return f"{stock_code} {category} 데이터 다운로드 완료."
        downloadAll(category)
        return f"{category} 전체 데이터 다운로드 완료."

    register_tool(
        "download_data",
        download_data,
        "데이터를 다운로드합니다. "
        "stock_code를 지정하면 해당 종목만, 비워두면 카테고리 전체를 다운로드합니다. "
        "category: docs(공시문서), finance(재무), report(정기보고서), edgarDocs(미국 공시문서, ticker 필요).",
        {
            "type": "object",
            "properties": {
                "stock_code": {
                    "type": "string",
                    "description": "종목코드 또는 ticker (비워두면 전체)",
                    "default": "",
                },
                "category": {
                    "type": "string",
                    "description": "카테고리 (docs, finance, report, edgarDocs)",
                    "default": "docs",
                },
            },
        },
    )

    def data_status() -> str:
        from dartlab.core.dataLoader import DATA_RELEASES, _dataDir

        lines = ["| 카테고리 | 라벨 | 파일 수 |", "| --- | --- | --- |"]
        for cat, conf in DATA_RELEASES.items():
            dataDir = _dataDir(cat)
            count = len(list(dataDir.glob("*.parquet"))) if dataDir.exists() else 0
            lines.append(f"| {cat} | {conf['label']} | {count} |")
        return "\n".join(lines)

    register_tool(
        "data_status",
        data_status,
        "로컬에 저장된 데이터 현황(카테고리별 파일 수)을 조회합니다. "
        "'데이터 몇 개 있어?', '어떤 데이터가 있지?' 같은 질문에 사용하세요.",
        {"type": "object", "properties": {}},
    )

    # ── batch_query ──

    def batch_query(codes: str, topic: str = "BS") -> str:
        """복수 종목에 동일 topic을 일괄 조회하여 비교 테이블을 반환한다."""
        import dartlab as _dl

        code_list = [c.strip() for c in codes.split(",") if c.strip()]
        if not code_list:
            return "종목코드를 쉼표로 구분하여 입력하세요. 예: 005930,000660,035420"
        if len(code_list) > 10:
            return "최대 10개 종목까지 조회 가능합니다."

        results: list[str] = []
        for code in code_list:
            try:
                comp = _dl.Company(code)
                name = getattr(comp, "corpName", code) or code
                val = comp.show(topic)
                preview = format_tool_value(val, max_rows=5, max_chars=1500)
                results.append(f"### {name} ({code})\n{preview}")
            except (KeyError, ValueError, RuntimeError, OSError) as e:
                results.append(f"### {code}\n조회 실패: {e}")
        return "\n\n".join(results)

    register_tool(
        "batch_query",
        batch_query,
        "복수 종목에 동일한 topic을 일괄 조회하여 비교합니다. "
        "사용자가 '삼성전자와 SK하이닉스 재무 비교', '여러 종목 배당 비교' 같은 요청을 할 때 사용하세요. "
        "codes는 쉼표로 구분된 종목코드(최대 10개), topic은 조회할 데이터 모듈입니다.",
        {
            "type": "object",
            "properties": {
                "codes": {
                    "type": "string",
                    "description": "쉼표로 구분된 종목코드 (예: 005930,000660,035420)",
                },
                "topic": {
                    "type": "string",
                    "description": "조회할 topic (예: BS, IS, ratios, companyOverview)",
                    "default": "BS",
                },
            },
            "required": ["codes"],
        },
    )
