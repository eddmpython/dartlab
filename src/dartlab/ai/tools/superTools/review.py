"""review Super Tool -- 분석 결과 구조화 보고서 dispatcher.

dartlab.review 공개 API와 1:1 대응.
blocks/section/full 3단계 접근.
"""

from __future__ import annotations

from typing import Any

from ..defaults.helpers import format_tool_value


def registerReviewTool(company: Any, registerTool) -> None:
    """review Super Tool 등록."""

    def _blocks(**_kw) -> str:
        """사용 가능한 분석 블록 카탈로그."""
        try:
            from dartlab.review import blocks

            b = blocks(company)
            # catalog 테이블 반환
            catalog = getattr(b, "catalog", None)
            if catalog is not None:
                return format_tool_value(catalog, max_rows=40, max_chars=4000)
            return str(b)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"[오류] blocks 조회 실패: {e}"

    def _block(key: str = "", **_kw) -> str:
        """특정 분석 블록 데이터 조회."""
        if not key:
            return "key(블록명)를 지정하세요. blocks action으로 카탈로그를 확인하세요."
        try:
            from dartlab.review import blocks

            b = blocks(company)
            result = b.get(key)
            if result is None:
                return f"[데이터 없음] '{key}' 블록이 없습니다. blocks action으로 카탈로그를 확인하세요."
            return format_tool_value(result, max_rows=30, max_chars=4000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"[오류] block('{key}') 조회 실패: {e}"

    def _section(section: str = "", **_kw) -> str:
        """특정 섹션의 리뷰 렌더링."""
        try:
            from dartlab.review import buildReview

            rev = buildReview(company)
            if section:
                # 특정 섹션만 필터
                matched = [s for s in rev.sections if s.name == section]
                if not matched:
                    available = [s.name for s in rev.sections]
                    return f"[데이터 없음] '{section}' 섹션 없음. 가용: {', '.join(available)}"
                lines = []
                for s in matched:
                    lines.append(f"## {s.name}")
                    for blk in s.blocks:
                        lines.append(str(blk))
                return "\n\n".join(lines)
            # 전체 섹션 목록
            lines = ["## Review 섹션 목록"]
            for s in rev.sections:
                nBlocks = len(s.blocks)
                lines.append(f"- {s.name} ({nBlocks}개 블록)")
            return "\n".join(lines)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"[오류] section 조회 실패: {e}"

    def _full(fmt: str = "markdown", **_kw) -> str:
        """전체 리뷰 보고서 렌더링."""
        try:
            from dartlab.review import buildReview

            rev = buildReview(company)
            rendered = rev.render(fmt)
            if len(rendered) > 8000:
                rendered = rendered[:8000] + "\n\n... (truncated)"
            return rendered
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"[오류] full review 실패: {e}"

    _ACTIONS = {
        "blocks": _blocks,
        "block": _block,
        "section": _section,
        "full": _full,
    }

    def review(action: str, key: str = "", section: str = "", fmt: str = "markdown") -> str:
        """분석 결과 구조화 보고서 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(key=key, section=section, fmt=fmt)

    registerTool(
        "review",
        review,
        "분석 결과 구조화 보고서 -- blocks/section/full 3단계.\n"
        "\n"
        "- blocks: 사용 가능한 분석 블록 카탈로그 (key별 라벨/설명)\n"
        "- block: 특정 블록 데이터 조회 (key 필수)\n"
        "- section: 특정 섹션 리뷰 (section 지정) 또는 전체 섹션 목록\n"
        "- full: 전체 리뷰 보고서 (fmt=markdown/html/json)\n"
        "\n"
        "반환: 마크다운 텍스트. 실패 시 '[오류]' 메시지.",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["blocks", "block", "section", "full"],
                    "description": "blocks=카탈로그, block=단일블록, section=섹션, full=전체보고서",
                },
                "key": {
                    "type": "string",
                    "description": "블록 key (action=block). blocks action으로 가용 key를 확인",
                    "default": "",
                },
                "section": {
                    "type": "string",
                    "description": "섹션명 (action=section). 비워두면 섹션 목록 반환",
                    "default": "",
                },
                "fmt": {
                    "type": "string",
                    "description": "렌더링 포맷 (action=full): markdown/html/json",
                    "default": "markdown",
                },
            },
            "required": ["action"],
        },
        category="analysis",
        questionTypes=("종합", "리스크", "투자"),
        priority=75,
    )
