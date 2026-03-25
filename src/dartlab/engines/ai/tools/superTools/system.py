"""system Super Tool — 메타/시스템 통합 dispatcher.

통합 대상: get_system_spec, get_tool_catalog, discover_features,
search_company, download_data, data_status, suggest_questions
"""

from __future__ import annotations

from typing import Any, Callable


def registerSystemTool(registerTool: Callable, *, company: Any | None = None) -> None:
    """system Super Tool 등록."""

    def _spec(**_kw) -> str:
        try:
            from dartlab.engines.ai.spec import getSystemSpec

            return getSystemSpec()
        except (ImportError, AttributeError) as e:
            return f"시스템 스펙 조회 실패: {e}"

    def _features(**_kw) -> str:
        try:
            from dartlab.core.registry import buildFeatureDescription

            return buildFeatureDescription("all")
        except (ImportError, AttributeError) as e:
            return f"기능 목록 조회 실패: {e}"

    def _searchCompany(keyword: str = "", **_kw) -> str:
        if not keyword:
            return "keyword를 지정하세요."
        try:
            import dartlab

            df = dartlab.search(keyword)
            if df is None or len(df) == 0:
                return f"'{keyword}'와 일치하는 종목이 없습니다."
            from ..defaults.helpers import df_to_md

            return df_to_md(df.head(10), max_rows=10)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"종목 검색 실패: {e}"

    def _dataStatus(**_kw) -> str:
        try:
            from dartlab.core.dataLoader import DATA_RELEASES, _dataDir

            lines = ["| 카테고리 | 라벨 | 파일 수 |", "| --- | --- | --- |"]
            for cat, conf in DATA_RELEASES.items():
                dataDir = _dataDir(cat)
                count = len(list(dataDir.glob("*.parquet"))) if dataDir.exists() else 0
                lines.append(f"| {cat} | {conf['label']} | {count} |")
            return "\n".join(lines)
        except (ImportError, AttributeError, OSError) as e:
            return f"데이터 상태 조회 실패: {e}"

    def _suggest(**_kw) -> str:
        if company is None:
            return "회사를 먼저 선택하면 맞춤 질문을 추천합니다."
        try:
            from dartlab.engines.ai.conversation.suggestions import suggestQuestions

            questions = suggestQuestions(company)
            if not questions:
                return "추천 질문을 만들 수 있는 데이터가 부족합니다."
            corpName = getattr(company, "corpName", "선택 기업")
            lines = [f"## {corpName} 추천 질문", ""]
            for i, q in enumerate(questions, 1):
                lines.append(f"{i}. {q}")
            return "\n".join(lines)
        except (ImportError, AttributeError) as e:
            return f"질문 추천 실패: {e}"

    _ACTIONS = {
        "spec": _spec,
        "features": _features,
        "searchCompany": _searchCompany,
        "dataStatus": _dataStatus,
        "suggest": _suggest,
    }

    def system(action: str, keyword: str = "") -> str:
        """시스템/메타 정보 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(keyword=keyword)

    registerTool(
        "system",
        system,
        "시스템 정보/메타 도구. 스펙, 기능목록, 종목검색, 데이터상태.\n"
        "action별 동작:\n"
        "- spec: 시스템 스펙 조회\n"
        "- features: 사용 가능한 기능 목록\n"
        "- searchCompany: 종목 검색 (keyword 필수)\n"
        "- dataStatus: 데이터 다운로드 상태\n"
        "- suggest: 질문 추천",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["spec", "features", "searchCompany", "dataStatus", "suggest"],
                    "description": "spec=시스템스펙, features=기능목록, searchCompany=종목검색, dataStatus=데이터상태, suggest=질문추천",
                },
                "keyword": {
                    "type": "string",
                    "description": "검색어 (action=searchCompany일 때)",
                    "default": "",
                },
            },
            "required": ["action"],
        },
        category="meta",
        questionTypes=("종합",),
        priority=60,
    )
