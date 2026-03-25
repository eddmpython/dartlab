"""explore Super Tool — 공시/문서 탐색 통합 dispatcher.

통합 대상: show_topic, show_block, list_topics, get_sections,
trace_topic, diff_topic, get_company_info, list_filings,
list_live_filings, read_filing, batch_query, get_evidence,
get_topic_coverage, get_notes, search_data
"""

from __future__ import annotations

from typing import Any

import polars as pl

from dartlab.engines.common.topicLabels import buildTopicEnumDescription

from ..defaults.helpers import df_to_md, format_tool_value, maybe_int


def registerExploreTool(company: Any, registerTool) -> None:
    """explore Super Tool 등록."""

    # ── 동적 topic enum 생성 ──
    topicEnum: list[str] = []
    try:
        topicsDf = getattr(company, "topics", None)
        if topicsDf is not None:
            if isinstance(topicsDf, pl.DataFrame):
                topicEnum = topicsDf["topic"].to_list()
            else:
                topicEnum = list(topicsDf)
    except (AttributeError, KeyError, TypeError, ValueError):
        pass

    topicEnumDesc = buildTopicEnumDescription(topicEnum) if topicEnum else ""

    # ── action 핸들러 ──

    def _show(target: str, block: str = "", **_kw) -> str:
        """topic 데이터 조회. block 비어있으면 목차, 숫자면 해당 블록."""
        if not hasattr(company, "show"):
            return "show() 인터페이스가 없습니다."
        blockIdx = maybe_int(block)
        try:
            result = company.show(target) if blockIdx is None else company.show(target, blockIdx)
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            return f"show('{target}') 실패: {e}"
        return format_tool_value(result, max_rows=50, max_chars=8000)

    def _topics(**_kw) -> str:
        """사용 가능한 topic 목록."""
        topics = getattr(company, "topics", None)
        if topics is None:
            return "topics 속성이 없습니다."
        topicList = list(topics) if not isinstance(topics, list) else topics
        if not topicList:
            return "사용 가능한 topic이 없습니다."
        indexDf = getattr(company, "index", None)
        if isinstance(indexDf, pl.DataFrame) and indexDf.height > 0:
            return df_to_md(indexDf, max_rows=60)
        return "\n".join(f"- {t}" for t in topicList)

    def _trace(target: str, **_kw) -> str:
        """topic 출처 추적."""
        if not hasattr(company, "trace"):
            return "trace() 인터페이스가 없습니다."
        try:
            result = company.trace(target)
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            return f"trace('{target}') 실패: {e}"
        return format_tool_value(result, max_rows=20, max_chars=3000)

    def _diff(target: str = "", **_kw) -> str:
        """기간간 변화 분석."""
        if not hasattr(company, "diff"):
            return "diff() 인터페이스가 없습니다."
        try:
            result = company.diff(target) if target else company.diff()
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            return f"diff('{target}') 실패: {e}"
        return format_tool_value(result, max_rows=20, max_chars=4000)

    def _info(**_kw) -> str:
        """기업 기본 정보."""
        stockCode = getattr(company, "stockCode", getattr(company, "ticker", ""))
        parts = [f"기업명: {company.corpName}", f"종목코드: {stockCode}"]
        try:
            from dartlab.engines.gather.listing import getKindList

            df = getKindList()
            match = df.filter(pl.col("종목코드") == stockCode)
            if match.height > 0:
                row = match.row(0, named=True)
                labels = {
                    "업종": "업종",
                    "주요제품": "주요제품",
                    "대표자명": "대표자",
                    "상장일": "상장일",
                    "결산월": "결산월",
                    "홈페이지": "홈페이지",
                    "지역": "지역",
                }
                for col, label in labels.items():
                    val = row.get(col)
                    if val:
                        parts.append(f"{label}: {val}")
        except (ImportError, FileNotFoundError):
            pass
        return "\n".join(parts)

    def _filings(target: str = "", **_kw) -> str:
        """공시 문서 목록."""
        if not hasattr(company, "filings"):
            return "filings() 인터페이스가 없습니다."
        try:
            result = company.filings()
            if result is None or (isinstance(result, pl.DataFrame) and result.is_empty()):
                return "공시 문서가 없습니다."
            if isinstance(result, pl.DataFrame):
                return df_to_md(result.head(20), max_rows=20)
            return str(result)[:3000]
        except (AttributeError, KeyError, TypeError, ValueError, RuntimeError) as e:
            return f"공시 목록 조회 실패: {e}"

    def _search(keyword: str = "", **_kw) -> str:
        """sections + topicLabels aliases 기반 키워드 검색 — topic 찾기."""
        if not keyword:
            return "keyword를 지정하세요."

        from dartlab.engines.common.topicLabels import TOPIC_LABELS, topicLabel

        results: list[str] = []
        seen: set[str] = set()

        # 1) topicLabels aliases 검색 (가장 빠름)
        for topic, info in TOPIC_LABELS.items():
            if topic in seen:
                continue
            label = info["label"]
            aliases = info.get("aliases", [])
            if keyword in label or any(keyword in a for a in aliases):
                # 이 company에 해당 topic이 실제 존재하는지 확인
                if topicEnum and topic in topicEnum:
                    seen.add(topic)
                    results.append(f"- `{topic}` ({label}) — 라벨/별칭 매칭")

        # 2) sections 내 title/content 검색 (원문 기반)
        sec = getattr(company, "sections", None)
        if sec is not None and isinstance(sec, pl.DataFrame):
            for row in sec.to_dicts():
                topic = row.get("topic", "")
                if topic in seen:
                    continue
                title = str(row.get("sectionTitle", ""))
                content = str(row.get("content", ""))[:500]
                if keyword in title or keyword in content:
                    seen.add(topic)
                    label = topicLabel(topic)
                    matchLoc = "제목" if keyword in title else "본문"
                    results.append(f"- `{topic}` ({label}) — {matchLoc}에서 발견: {title[:60]}")

        if not results:
            return f"'{keyword}'와 관련된 topic을 찾지 못했습니다. explore(action='topics')로 전체 목록을 확인하세요."
        return f"'{keyword}' 검색 결과 ({len(results)}건):\n" + "\n".join(results)

    # ── action dispatch ──
    _ACTIONS = {
        "show": _show,
        "topics": _topics,
        "trace": _trace,
        "diff": _diff,
        "info": _info,
        "filings": _filings,
        "search": _search,
    }

    def explore(action: str, target: str = "", block: str = "", keyword: str = "") -> str:
        """기업 공시 데이터 탐색 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(target=target, block=block, keyword=keyword)

    # ── schema 구성 ──
    targetSchema: dict[str, Any] = {
        "type": "string",
        "description": f"대상 topic. {topicEnumDesc}" if topicEnumDesc else "대상 topic",
    }
    if topicEnum:
        targetSchema["enum"] = topicEnum

    registerTool(
        "explore",
        explore,
        "기업 공시 데이터 탐색 — 사업보고서, 리스크, 배당, 주석 등 공시 원문 조회.\n"
        "\n"
        "✓ 이 도구를 쓰는 경우: 사업개요, 리스크, 원재료, 부문정보, 경영진분석, 주석 등 서술형/공시 질문\n"
        "✗ 이 도구를 쓰지 않는 경우: 매출·영업이익·ROE 등 재무 숫자 → finance 사용\n"
        "\n"
        "action별 동작:\n"
        "- show: topic 데이터 조회 (target 필수). 예: explore(action='show', target='businessOverview')\n"
        "- topics: 사용 가능한 전체 topic 목록. topic을 모를 때 먼저 호출\n"
        "- trace: topic 출처 추적 (target 필수)\n"
        "- diff: 기간간 변화 분석 (target 선택). 예: explore(action='diff', target='riskFactor')\n"
        "- info: 기업 기본 정보 (업종, 대표자, 상장일)\n"
        "- filings: 공시 문서 목록\n"
        "- search: 키워드로 topic 검색 (keyword 필수). 예: explore(action='search', keyword='비용의 성격별분류')",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["show", "topics", "trace", "diff", "info", "filings", "search"],
                    "description": "show=데이터조회, topics=topic목록, trace=출처추적, diff=변화비교, info=기업정보, filings=공시목록, search=키워드검색",
                },
                "target": targetSchema,
                "block": {
                    "type": "string",
                    "description": "블록번호 (action=show일 때). 비워두면 목차, 숫자면 해당 블록",
                    "default": "",
                },
                "keyword": {
                    "type": "string",
                    "description": "검색어 (action=search일 때)",
                    "default": "",
                },
            },
            "required": ["action"],
        },
        category="company",
        questionTypes=("건전성", "수익성", "성장성", "배당", "리스크", "지배구조", "투자", "공시", "사업", "종합"),
        priority=95,
    )
