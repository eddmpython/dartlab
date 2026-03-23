"""OpenAPI 도구 — DART/EDGAR Open API 직접 호출."""

from __future__ import annotations

from dartlab.engines.ai.context.dartOpenapi import (
    formatDartFilingContext,
    getDartFilingText,
    searchDartFilings,
)

from .helpers import csv_list, format_tool_value, maybe_int


def register_openapi_tools(register_tool) -> None:
    """OpenAPI 관련 도구를 등록한다."""

    def get_openapi_capabilities(market: str = "all") -> str:
        from dartlab import OpenDart

        sections: list[str] = []
        target = (market or "all").lower()

        if target in {"all", "dart", "kr"}:
            sections.extend(
                [
                    "## DART OpenAPI",
                    "- facade: `OpenDart()`",
                    "- action: `search`, `company`, `corp_code`, `corp_codes`",
                    "- action: `filings`, `document_text`, `finstate`, `report`",
                    "- action: `major_shareholders`, `executive_shares`",
                    "- action: `report_types`, `filing_types`, `markets`, `xbrl_taxonomy`",
                    "- AI retrieval: `search_dart_filings`, `get_dart_filing_text`",
                    "- recent filings / 수주공시 / 계약공시 검색은 DART API 키가 필요",
                    "- save: `finance`, `report`, `filings`, `xbrl`",
                    f"- report type count: {len(OpenDart.reportTypes())}",
                ]
            )

        if target in {"all", "edgar", "us"}:
            sections.extend(
                [
                    "## EDGAR OpenAPI",
                    "- facade: `OpenEdgar()`",
                    "- action: `search`, `company`, `submissions`, `filings`",
                    "- action: `company_facts`, `company_concept`, `frame`",
                    "- save: `docs`, `finance`",
                ]
            )

        if not sections:
            return "market은 `all`, `dart`, `edgar` 중 하나여야 합니다."

        sections.extend(
            [
                "",
                "## 예시",
                "- `call_dart_openapi(action='report_types')`",
                "- `call_dart_openapi(action='document_text', query='20240312000736')`",
                "- `call_dart_openapi(action='report', corp='삼성전자', report_type='배당', start='2023')`",
                "- `search_dart_filings(days=7, keywords='단일판매공급계약,공급계약')`",
                "- `call_edgar_openapi(action='filings', identifier='AAPL', forms='10-K,10-Q')`",
                "- `openapi_save(market='edgar', identifier='AAPL', dataset='docs', since_year=2018)`",
            ]
        )
        return "\n".join(["# OpenAPI 기능 범위", *sections])

    register_tool(
        "get_openapi_capabilities",
        get_openapi_capabilities,
        "DART/EDGAR OpenAPI surface를 요약합니다. "
        "사용자가 OpenDart, OpenEdgar, 공개 API로 뭘 할 수 있는지 물을 때 먼저 호출하세요.",
        {
            "type": "object",
            "properties": {
                "market": {
                    "type": "string",
                    "description": "all, dart, edgar 중 하나",
                    "default": "all",
                }
            },
        },
        category="global",
        priority=50,
    )

    def call_dart_openapi(
        action: str,
        corp: str = "",
        query: str = "",
        start: str = "",
        end: str = "",
        quarter: int | None = None,
        report_type: str = "",
        listed: bool = False,
        disclosure_type: str = "",
        final: bool = False,
        market_code: str = "",
        consolidated: bool = True,
        full: bool = False,
        taxonomy_category: str = "",
        rcept_no: str = "",
        max_chars: int = 4000,
    ) -> str:
        from dartlab import OpenDart

        dart = OpenDart()
        action_key = (action or "").strip().lower()
        start_arg = start or None
        end_arg = maybe_int(end)
        receipt_no = rcept_no or query

        if action_key == "search":
            if not query:
                return "query가 필요합니다."
            return format_tool_value(dart.search(query, listed=listed))

        if action_key == "company":
            if not corp:
                return "corp가 필요합니다."
            return format_tool_value(dart.company(corp))

        if action_key == "corp_code":
            target = corp or query
            if not target:
                return "corp 또는 query가 필요합니다."
            return format_tool_value({"corpCode": dart.corpCode(target)})

        if action_key == "corp_codes":
            return format_tool_value(dart.corpCodes())

        if action_key == "filings":
            corp_arg = corp or None
            result = dart.filings(
                corp_arg,
                start_arg,
                end or None,
                type=disclosure_type or None,
                final=final,
                market=market_code or None,
            )
            return format_tool_value(result)

        if action_key == "document_text":
            if not receipt_no:
                return "rcept_no 또는 query에 접수번호가 필요합니다."
            return getDartFilingText(receipt_no, maxChars=max_chars)

        if action_key == "finstate":
            if not corp:
                return "corp가 필요합니다."
            result = dart.finstate(
                corp,
                start_arg,
                end=end_arg,
                q=quarter,
                consolidated=consolidated,
                full=full,
            )
            return format_tool_value(result)

        if action_key == "report":
            if not corp or not report_type:
                return "corp와 report_type이 필요합니다."
            result = dart.report(
                corp,
                report_type,
                start_arg,
                end=end_arg,
                q=quarter,
            )
            return format_tool_value(result)

        if action_key == "major_shareholders":
            if not corp:
                return "corp가 필요합니다."
            return format_tool_value(dart.majorShareholders(corp))

        if action_key == "executive_shares":
            if not corp:
                return "corp가 필요합니다."
            return format_tool_value(dart.executiveShares(corp))

        if action_key == "report_types":
            return format_tool_value(OpenDart.reportTypes())

        if action_key == "filing_types":
            return format_tool_value(OpenDart.filingTypes())

        if action_key == "markets":
            return format_tool_value(OpenDart.markets())

        if action_key == "xbrl_taxonomy":
            if not taxonomy_category:
                return "taxonomy_category가 필요합니다. 예: BS1, IS1, CF1"
            return format_tool_value(dart.xbrlTaxonomy(taxonomy_category))

        return (
            "지원하지 않는 action입니다. "
            "search, company, corp_code, corp_codes, filings, document_text, finstate, report, "
            "major_shareholders, executive_shares, report_types, filing_types, markets, xbrl_taxonomy"
        )

    register_tool(
        "call_dart_openapi",
        call_dart_openapi,
        "DART OpenAPI를 직접 호출합니다. "
        "action 예시: search, company, corp_code, corp_codes, filings, document_text, finstate, report, "
        "major_shareholders, executive_shares, report_types, filing_types, markets, xbrl_taxonomy.",
        {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "호출할 DART action"},
                "corp": {"type": "string", "description": "회사명/종목코드/corp_code"},
                "query": {"type": "string", "description": "search용 검색어"},
                "start": {"type": "string", "description": "시작일 또는 연도"},
                "end": {"type": "string", "description": "종료일 또는 종료 연도"},
                "quarter": {"type": "integer", "description": "분기. 0~4 또는 null"},
                "report_type": {"type": "string", "description": "예: 배당, 직원, 임원"},
                "listed": {"type": "boolean", "description": "상장사만 검색", "default": False},
                "disclosure_type": {"type": "string", "description": "공시유형 예: A"},
                "final": {"type": "boolean", "description": "최종보고서만", "default": False},
                "market_code": {"type": "string", "description": "법인구분 Y/K/N/E"},
                "consolidated": {"type": "boolean", "description": "연결 기준", "default": True},
                "full": {"type": "boolean", "description": "전체 계정", "default": False},
                "taxonomy_category": {"type": "string", "description": "xbrl taxonomy 카테고리"},
                "rcept_no": {"type": "string", "description": "document_text용 접수번호"},
                "max_chars": {"type": "integer", "description": "document_text 최대 글자수", "default": 4000},
            },
            "required": ["action"],
        },
        ai_hint="OpenDART raw API 래퍼. 최근 공시목록, 계약공시, 원문 본문 확인에 사용",
        questionTypes=("공시", "사업"),
        category="global",
        priority=70,
    )

    def search_dart_filings(
        corp: str = "",
        start: str = "",
        end: str = "",
        days: int | None = None,
        weeks: int | None = None,
        disclosure_type: str = "",
        market_code: str = "",
        final_only: bool = False,
        keywords: str = "",
        limit: int = 20,
    ) -> str:
        keyword_list = csv_list(keywords) or None
        filings = searchDartFilings(
            corp=corp or None,
            start=start or None,
            end=end or None,
            days=days,
            weeks=weeks,
            disclosureType=disclosure_type or None,
            market=market_code or None,
            finalOnly=final_only,
            titleKeywords=keyword_list,
            limit=limit,
        )
        intent = {
            "corp": corp or None,
            "start": start or "",
            "end": end or "",
            "disclosureType": disclosure_type or None,
            "market": market_code or None,
            "finalOnly": final_only,
            "titleKeywords": tuple(keyword_list or ()),
            "limit": limit,
        }
        from dartlab.engines.ai.context.dartOpenapi import DartFilingIntent

        return formatDartFilingContext(
            filings,
            DartFilingIntent(
                matched=True,
                corp=intent["corp"],
                start=intent["start"] or (f"최근 {days}일" if days else (f"최근 {weeks}주" if weeks else "")),
                end=intent["end"] or ("현재" if days or weeks else ""),
                disclosureType=intent["disclosureType"],
                market=intent["market"],
                finalOnly=intent["finalOnly"],
                limit=intent["limit"],
                titleKeywords=intent["titleKeywords"],
            ),
        )

    register_tool(
        "search_dart_filings",
        search_dart_filings,
        "OpenDART 전체 시장 공시목록을 검색합니다. 최근 며칠 공시, 수주공시, 계약공시, 단일판매공급계약 질문에 우선 사용하세요.",
        {
            "type": "object",
            "properties": {
                "corp": {"type": "string", "description": "회사명/종목코드/corp_code. 비우면 전체 시장"},
                "start": {"type": "string", "description": "시작일 YYYYMMDD"},
                "end": {"type": "string", "description": "종료일 YYYYMMDD"},
                "days": {"type": "integer", "description": "최근 N일"},
                "weeks": {"type": "integer", "description": "최근 N주"},
                "disclosure_type": {"type": "string", "description": "공시유형 A~J"},
                "market_code": {"type": "string", "description": "법인구분 Y/K/N/E"},
                "final_only": {"type": "boolean", "description": "최종보고서만", "default": False},
                "keywords": {"type": "string", "description": "제목 키워드 쉼표 목록"},
                "limit": {"type": "integer", "description": "최대 건수", "default": 20},
            },
        },
        ai_hint="최근 공시목록, 수주공시, 단일판매공급계약, 계약공시 검색",
        questionTypes=("공시", "사업"),
        category="global",
        priority=85,
    )

    def get_dart_filing_text(rcept_no: str, max_chars: int = 4000) -> str:
        return getDartFilingText(rcept_no, maxChars=max_chars)

    register_tool(
        "get_dart_filing_text",
        get_dart_filing_text,
        "OpenDART 접수번호(rcept_no) 기준으로 공시 원문 텍스트를 가져옵니다. 목록에서 중요 공시를 골라 본문을 읽을 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "rcept_no": {"type": "string", "description": "접수번호"},
                "max_chars": {"type": "integer", "description": "최대 글자수", "default": 4000},
            },
            "required": ["rcept_no"],
        },
        ai_hint="공시 원문 본문 조회",
        questionTypes=("공시", "사업"),
        category="global",
        priority=75,
    )

    def call_edgar_openapi(
        action: str,
        identifier: str = "",
        query: str = "",
        forms: str = "",
        since: str = "",
        until: str = "",
        taxonomy: str = "",
        tag: str = "",
        unit: str = "",
        period: str = "",
    ) -> str:
        from dartlab import OpenEdgar

        edgar = OpenEdgar()
        action_key = (action or "").strip().lower()

        if action_key == "search":
            if not query:
                return "query가 필요합니다."
            return format_tool_value(edgar.search(query))

        if action_key == "company":
            if not identifier:
                return "identifier가 필요합니다."
            return format_tool_value(edgar.company(identifier))

        if action_key == "submissions":
            if not identifier:
                return "identifier가 필요합니다."
            return format_tool_value(edgar.submissionsJson(identifier))

        if action_key == "filings":
            if not identifier:
                return "identifier가 필요합니다."
            return format_tool_value(
                edgar.filings(
                    identifier,
                    forms=csv_list(forms),
                    since=since or None,
                    until=until or None,
                )
            )

        if action_key == "company_facts":
            if not identifier:
                return "identifier가 필요합니다."
            return format_tool_value(edgar.companyFactsJson(identifier))

        if action_key == "company_concept":
            if not identifier or not taxonomy or not tag:
                return "identifier, taxonomy, tag가 필요합니다."
            return format_tool_value(edgar.companyConceptJson(identifier, taxonomy, tag))

        if action_key == "frame":
            if not taxonomy or not tag or not unit or not period:
                return "taxonomy, tag, unit, period가 필요합니다."
            return format_tool_value(edgar.frameJson(taxonomy, tag, unit, period))

        return (
            "지원하지 않는 action입니다. search, company, submissions, filings, company_facts, company_concept, frame"
        )

    register_tool(
        "call_edgar_openapi",
        call_edgar_openapi,
        "EDGAR OpenAPI를 직접 호출합니다. "
        "action 예시: search, company, submissions, filings, company_facts, company_concept, frame.",
        {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "호출할 EDGAR action"},
                "identifier": {"type": "string", "description": "ticker 또는 CIK"},
                "query": {"type": "string", "description": "search용 검색어"},
                "forms": {"type": "string", "description": "쉼표 구분 form 목록 예: 10-K,10-Q"},
                "since": {"type": "string", "description": "시작일"},
                "until": {"type": "string", "description": "종료일"},
                "taxonomy": {"type": "string", "description": "taxonomy 예: us-gaap"},
                "tag": {"type": "string", "description": "tag 예: RevenueFromContractWithCustomerExcludingAssessedTax"},
                "unit": {"type": "string", "description": "frame unit 예: USD"},
                "period": {"type": "string", "description": "frame period 예: CY2024Q4I"},
            },
            "required": ["action"],
        },
        category="global",
        priority=40,
    )

    def openapi_save(
        market: str,
        identifier: str,
        dataset: str,
        start: str = "",
        end: str = "",
        quarter: int | None = None,
        since_year: int = 2009,
        full: bool = True,
        categories: str = "",
    ) -> str:
        from dartlab import OpenDart, OpenEdgar

        market_key = (market or "").strip().lower()
        dataset_key = (dataset or "").strip().lower()
        end_arg = maybe_int(end)

        if market_key in {"dart", "kr"}:
            if not identifier:
                return "identifier가 필요합니다."
            company_api = OpenDart()(identifier)
            if dataset_key == "finance":
                return format_tool_value(company_api.saveFinance(start or None, end=end_arg, q=quarter, full=full))
            if dataset_key == "report":
                return format_tool_value(
                    company_api.saveReport(
                        start or None,
                        end=end_arg,
                        q=quarter,
                        categories=csv_list(categories),
                    )
                )
            if dataset_key == "filings":
                return format_tool_value(company_api.saveFilings(start or None, end or None))
            if dataset_key == "xbrl":
                return format_tool_value(company_api.xbrl(start or None, q=quarter))
            return "DART dataset은 finance, report, filings, xbrl 중 하나여야 합니다."

        if market_key in {"edgar", "us"}:
            if not identifier:
                return "identifier가 필요합니다."
            company_api = OpenEdgar()(identifier)
            if dataset_key == "docs":
                return format_tool_value(company_api.saveDocs(sinceYear=since_year))
            if dataset_key == "finance":
                return format_tool_value(company_api.saveFinance())
            return "EDGAR dataset은 docs, finance 중 하나여야 합니다."

        return "market은 dart 또는 edgar여야 합니다."

    register_tool(
        "openapi_save",
        openapi_save,
        "DART/EDGAR OpenAPI saver를 실행해 로컬 parquet를 생성합니다. "
        "DART dataset: finance, report, filings, xbrl. EDGAR dataset: docs, finance.",
        {
            "type": "object",
            "properties": {
                "market": {"type": "string", "description": "dart 또는 edgar"},
                "identifier": {"type": "string", "description": "회사명/종목코드/ticker/CIK"},
                "dataset": {"type": "string", "description": "저장할 데이터 종류"},
                "start": {"type": "string", "description": "DART 시작 연도/일자"},
                "end": {"type": "string", "description": "DART 종료 연도/일자"},
                "quarter": {"type": "integer", "description": "DART 분기"},
                "since_year": {"type": "integer", "description": "EDGAR docs 시작 연도", "default": 2009},
                "full": {"type": "boolean", "description": "DART finance 전체 계정", "default": True},
                "categories": {"type": "string", "description": "DART report 카테고리 목록"},
            },
            "required": ["market", "identifier", "dataset"],
        },
        category="global",
        priority=35,
    )
