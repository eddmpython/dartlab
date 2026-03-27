"""research Super Tool -- 웹 검색 + URL 추출 통합 dispatcher.

통합 대상: webSearch, newsSearch, readUrl (gather/search, gather/reader)
LLM이 실시간 외부 정보를 직접 수집할 수 있게 해주는 8번째 Super Tool.
"""

from __future__ import annotations

from typing import Callable


def registerResearchTool(registerTool: Callable, *, company=None) -> None:
    """research Super Tool 등록."""

    def _search(query: str = "", maxResults: str = "8", days: str = "", **_kw) -> str:
        if not query:
            return "query(검색어)를 지정하세요."
        try:
            from dartlab.gather.search import formatResults, searchAvailable, webSearch

            avail = searchAvailable()
            if not avail["any"]:
                return (
                    "[안내] 검색 패키지가 설치되지 않았습니다.\n"
                    "`pip install dartlab[search]` 또는 `uv add dartlab[search]`로 설치하세요.\n"
                    "Tavily(TAVILY_API_KEY 필요) 또는 DuckDuckGo를 사용합니다."
                )
            daysInt = int(days) if days else None
            results = webSearch(query, maxResults=int(maxResults), days=daysInt)
            if not results:
                return f"'{query}' 검색 결과가 없습니다."
            return formatResults(results)
        except (ImportError, OSError, ValueError, RuntimeError) as e:
            return f"[오류] 웹 검색 실패: {e}"

    def _news(query: str = "", maxResults: str = "8", days: str = "7", **_kw) -> str:
        if not query:
            return "query(검색어)를 지정하세요."
        try:
            from dartlab.gather.search import formatResults, newsSearch, searchAvailable

            avail = searchAvailable()
            if not avail["any"]:
                return (
                    "[안내] 검색 패키지가 설치되지 않았습니다.\n"
                    "`pip install dartlab[search]`로 설치하세요."
                )
            daysInt = int(days) if days else 7
            results = newsSearch(query, maxResults=int(maxResults), days=daysInt)
            if not results:
                return f"'{query}' 관련 뉴스가 없습니다."
            return formatResults(results)
        except (ImportError, OSError, ValueError, RuntimeError) as e:
            return f"[오류] 뉴스 검색 실패: {e}"

    def _readUrl(url: str = "", **_kw) -> str:
        if not url:
            return "url을 지정하세요."
        try:
            from dartlab.gather.reader import readUrl

            return readUrl(url)
        except (ImportError, OSError, ValueError, RuntimeError) as e:
            return f"[오류] URL 읽기 실패: {e}"

    def _industry(query: str = "", region: str = "kr", maxResults: str = "8", **_kw) -> str:
        """산업/규제 검색 -- 도메인 필터링된 검색."""
        if not query:
            return "query(검색어)를 지정하세요."
        try:
            from dartlab.gather.search import formatResults, searchAvailable, webSearch

            avail = searchAvailable()
            if not avail["any"]:
                return "[안내] 검색 패키지가 설치되지 않았습니다. `pip install dartlab[search]`"

            # 지역별 검색어 보강
            suffix = ""
            if region == "kr":
                suffix = " 산업동향 규제"
            elif region == "us":
                suffix = " industry regulation SEC"
            elif region == "jp":
                suffix = " 業界動向 規制"

            results = webSearch(query + suffix, maxResults=int(maxResults))
            if not results:
                return f"'{query}' 산업 관련 검색 결과가 없습니다."
            return formatResults(results)
        except (ImportError, OSError, ValueError, RuntimeError) as e:
            return f"[오류] 산업 검색 실패: {e}"

    _ACTIONS = {
        "search": _search,
        "news": _news,
        "read_url": _readUrl,
        "industry": _industry,
    }

    def research(
        action: str,
        query: str = "",
        url: str = "",
        maxResults: str = "8",
        days: str = "",
        region: str = "kr",
    ) -> str:
        """외부 리서치 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(query=query, url=url, maxResults=maxResults, days=days, region=region)

    registerTool(
        "research",
        research,
        "외부 웹 검색 + URL 추출 -- 실시간 뉴스, 산업 동향, 규제 변화 조사.\n"
        "\n"
        "이 도구를 쓰는 경우:\n"
        "- '최근 뉴스는?', '반도체 산업 동향은?', '이 기사 내용 알려줘'\n"
        "- 기업 분석에 최신 외부 정보가 필요할 때\n"
        "- 공시 데이터만으로 부족한 맥락이 필요할 때\n"
        "\n"
        "이 도구를 쓰지 않는 경우:\n"
        "- 재무제표 숫자 -> finance 도구\n"
        "- 공시 원문/sections -> explore 도구\n"
        "- 주가/컨센서스 -> market 도구\n"
        "\n"
        "action별 동작:\n"
        "- search: 일반 웹 검색 (query 필수)\n"
        "- news: 뉴스 검색 (query 필수, days 선택 기본 7일)\n"
        "- read_url: URL 본문을 마크다운으로 추출 (url 필수)\n"
        "- industry: 산업/규제 검색 (query 필수, region 선택 kr/us/jp)\n"
        "\n"
        "반환: 마크다운 텍스트. 검색 패키지 미설치 시 안내 메시지.",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "news", "read_url", "industry"],
                    "description": "search=웹검색, news=뉴스, read_url=URL추출, industry=산업검색",
                },
                "query": {
                    "type": "string",
                    "description": "검색어 (action=search/news/industry)",
                    "default": "",
                },
                "url": {
                    "type": "string",
                    "description": "읽을 URL (action=read_url)",
                    "default": "",
                },
                "maxResults": {
                    "type": "string",
                    "description": "최대 결과 수. 기본 8",
                    "default": "8",
                },
                "days": {
                    "type": "string",
                    "description": "검색 기간(일). news 기본 7",
                    "default": "",
                },
                "region": {
                    "type": "string",
                    "enum": ["kr", "us", "jp"],
                    "description": "산업검색 지역 (action=industry). 기본 kr",
                    "default": "kr",
                },
            },
            "required": ["action"],
        },
        category="global",
        questionTypes=("뉴스", "산업", "규제", "동향", "실시간", "종합", "리스크"),
        priority=65,
    )
