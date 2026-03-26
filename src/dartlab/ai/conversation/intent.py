"""의도 분류 — 분석/메타/순수대화 판별.

server/resolve.py에서 추출한 순수 문자열 매칭 로직.
서버 의존성 없음.
"""

from __future__ import annotations

import re as _re

_META_KEYWORDS = frozenset(
    {
        "버전",
        "version",
        "도움말",
        "도움",
        "help",
        "사용법",
        "사용방법",
        "뭘할수있",
        "뭐할수있",
        "뭘 할 수",
        "뭐 할 수",
        "할수있",
        "기능",
        "데이터",
        "몇개",
        "몇 개",
        "개수",
        "목록",
        "리스트",
        "상태",
        "원본",
        "raw",
        "모듈",
        "module",
        "다운로드",
        "설치",
        "업데이트",
        "안녕",
        "반가",
        "고마",
        "안녕하세요",
        "hello",
        "hi",
        "thanks",
        "어떻게",
        "how",
        "what",
        "why",
        "설정",
        "config",
        "provider",
        "모델",
        "ollama",
        "문서",
        "docs",
        "파일",
        "저장",
        "opendart",
        "openedgar",
        "openapi",
        "api",
        "dart api",
        "edgar api",
        "엔진",
        "engine",
        "spec",
        "스펙",
        "tool",
        "도구",
        "런타임",
        "runtime",
        "codex",
        "gpt",
        "claude",
        "mcp",
        "서버",
        "server",
        "종목검색",
        "search",
    }
)

_ANALYSIS_KEYWORDS = frozenset(
    {
        "분석",
        "건전성",
        "수익성",
        "성장성",
        "배당",
        "실적",
        "재무",
        "매출",
        "영업이익",
        "순이익",
        "부채",
        "자산",
        "현금흐름",
        "ROE",
        "ROA",
        "PER",
        "PBR",
        "EPS",
        "EBITDA",
        "FCF",
        "리스크",
        "위험",
        "감사",
        "지배구조",
        "임원",
        "주주",
        "비교",
        "추세",
        "추이",
        "트렌드",
        "전망",
        "어때",
        "어떤가",
        "괜찮",
        "좋은가",
        "분석해",
        "알려줘",
        "알려 줘",
        "보여줘",
        "보여 줘",
        "해줘",
        "해 줘",
        "평가",
    }
)

_SYSTEM_ENTITIES = frozenset(
    {
        "opendart",
        "openedgar",
        "dartlab",
        "dart api",
        "edgar api",
        "openapi",
        "dart 시스템",
        "edgar 시스템",
        "mcp",
        "codex",
        "claude",
        "gpt",
        "ollama",
    }
)

_GREETING_ONLY_PATTERNS = frozenset(
    {
        "안녕",
        "안녕하세요",
        "반갑",
        "반갑습니다",
        "고마",
        "고맙습니다",
        "감사합니다",
        "감사해요",
        "hello",
        "hi",
        "thanks",
        "thank you",
    }
)

_ANALYSIS_CONTEXT_OVERRIDES = {
    "감사": ["감사의견", "감사보고서", "감사인", "감사위원", "내부감사", "외부감사"],
    "비교": ["비교해", "비교분석", "비교하"],
}

_TENTATIVE_PATTERNS = (
    "싶은데",
    "싶어",
    "할까",
    "할 수 있",
    "가능",
    "뭐가 있",
    "어떤 것",
    "어떤게",
    "어떤 게",
    "궁금",
    "뭘 볼",
    "뭘 봐",
    "무엇을",
)

_PURE_CONVERSATION_TOKENS = frozenset(
    {
        "응",
        "ㅇㅇ",
        "ㅇ",
        "그래",
        "넵",
        "네",
        "뭐해",
        "ㅋㅋ",
        "ㅎㅎ",
        "좋아",
        "오키",
        "ok",
        "yes",
        "no",
        "yeah",
        "알겠어",
        "그렇구나",
        "아하",
        "오",
        "와",
        "ㅠㅠ",
        "ㅜㅜ",
        "ㄴㄴ",
        "아니",
        "됐어",
    }
)

_PURE_CONVERSATION_RE = _re.compile(
    r"대화.*계속|계속.*대화|대화.*안.*되|이어서.*얘기|잡담|그냥.*얘기"
    r"|얘기.*하자|말.*걸어|채팅|아까.*말|다른.*얘기",
)


def is_meta_question(question: str) -> bool:
    """라이브러리/시스템에 대한 메타 질문인지 판별."""
    q = question.lower().replace(" ", "")
    q_raw = question.lower()

    for entity in _SYSTEM_ENTITIES:
        if entity.replace(" ", "") in q:
            return True

    q_stripped = question.strip().rstrip("!?.~")
    if q_stripped in _GREETING_ONLY_PATTERNS or q_stripped.lower() in _GREETING_ONLY_PATTERNS:
        return True

    for ambiguous, analysis_contexts in _ANALYSIS_CONTEXT_OVERRIDES.items():
        if ambiguous in q_raw:
            if any(ctx in q_raw for ctx in analysis_contexts):
                return False

    for kw in _META_KEYWORDS:
        if kw.replace(" ", "") in q:
            return True
    return False


def has_analysis_intent(question: str) -> bool:
    """분석 의도가 있는 질문인지 판별."""
    q_lower = question.lower().replace(" ", "")
    for entity in _SYSTEM_ENTITIES:
        if entity.replace(" ", "") in q_lower:
            return False

    q_stripped = question.strip().rstrip("!?.~")
    if q_stripped in _GREETING_ONLY_PATTERNS or q_stripped.lower() in _GREETING_ONLY_PATTERNS:
        return False

    has_kw = False
    for kw in _ANALYSIS_KEYWORDS:
        if kw in question:
            if kw == "감사":
                analysis_contexts = _ANALYSIS_CONTEXT_OVERRIDES.get("감사", [])
                if not any(ctx in question for ctx in analysis_contexts):
                    continue
            has_kw = True
            break
    if not has_kw:
        return False
    for pat in _TENTATIVE_PATTERNS:
        if pat in question:
            return False
    return True


def is_pure_conversation(question: str) -> bool:
    """순수 대화 패턴인지 판별."""
    q = question.strip()
    q_low = q.lower()

    if q_low in _PURE_CONVERSATION_TOKENS:
        return True
    if _PURE_CONVERSATION_RE.search(q_low):
        return True
    if len(q) <= 6:
        for kw in _ANALYSIS_KEYWORDS:
            if kw in q:
                return False
        return True
    return False
