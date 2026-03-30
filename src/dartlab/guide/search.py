"""CAPABILITIES 키워드 검색 엔진 — ms 단위 질문 기반 API 탐색.

외부 의존성 없음 (re, math만 사용). 모듈 레벨 캐시로 첫 호출 ~1ms.
"""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# 토큰화
# ---------------------------------------------------------------------------

_HANGUL_RE = re.compile(r"[가-힣]+")
_ALPHA_RE = re.compile(r"[a-zA-Z]{2,}")
_STOP_WORDS = frozenset(
    {
        "이",
        "가",
        "을",
        "를",
        "의",
        "에",
        "는",
        "은",
        "로",
        "와",
        "과",
        "해",
        "해줘",
        "해주세요",
        "하고",
        "하는",
        "있는",
        "없는",
        "대한",
        "좀",
        "어떻게",
        "뭐",
        "무엇",
        "어떤",
        "알려",
        "분석",
        "the",
        "a",
        "an",
        "is",
        "are",
        "of",
        "in",
        "to",
        "for",
        "and",
    }
)


def _tokenize(text: str) -> list[str]:
    """한글 바이그램 + 영어 소문자 토큰."""
    tokens: list[str] = []
    # 한글: 2글자 슬라이딩 윈도우
    for m in _HANGUL_RE.finditer(text):
        word = m.group()
        if len(word) >= 2:
            for i in range(len(word) - 1):
                bi = word[i : i + 2]
                if bi not in _STOP_WORDS:
                    tokens.append(bi)
        if word not in _STOP_WORDS:
            tokens.append(word)
    # 영어: 소문자 변환
    for m in _ALPHA_RE.finditer(text):
        w = m.group().lower()
        if w not in _STOP_WORDS:
            tokens.append(w)
    return tokens


# ---------------------------------------------------------------------------
# 인덱스
# ---------------------------------------------------------------------------

_index: dict | None = None
_idf: dict[str, float] = {}
_keys: list[str] = []


def _buildIndex() -> None:
    """CAPABILITIES를 토큰화하여 역인덱스 + IDF 구축."""
    global _index, _idf, _keys

    from dartlab.guide._generated import CAPABILITIES

    _keys = list(CAPABILITIES.keys())
    n = len(_keys)

    # 문서별 토큰 집합
    docTokenSets: list[set[str]] = []
    # 역인덱스: token → [(keyIdx, weight), ...]
    inverted: dict[str, list[tuple[int, float]]] = {}

    for idx, key in enumerate(_keys):
        entry = CAPABILITIES[key]
        tokenSet: set[str] = set()

        # key name 토큰 (보너스 2.0x)
        keyTokens = _tokenize(key.replace(".", " "))
        for t in keyTokens:
            tokenSet.add(t)
            inverted.setdefault(t, []).append((idx, 2.0))

        # summary + aicontext (가중치 1.5x)
        highText = " ".join(filter(None, [entry.get("summary", ""), entry.get("aicontext", "")]))
        for t in _tokenize(highText):
            tokenSet.add(t)
            inverted.setdefault(t, []).append((idx, 1.5))

        # guide + capabilities + seeAlso (가중치 1.0x)
        lowText = " ".join(
            filter(
                None,
                [
                    entry.get("guide", ""),
                    entry.get("capabilities", ""),
                    entry.get("seeAlso", ""),
                ],
            )
        )
        for t in _tokenize(lowText):
            tokenSet.add(t)
            inverted.setdefault(t, []).append((idx, 1.0))

        docTokenSets.append(tokenSet)

    # IDF 계산
    df: dict[str, int] = {}
    for tSet in docTokenSets:
        for t in tSet:
            df[t] = df.get(t, 0) + 1

    _idf = {t: math.log((n + 1) / (cnt + 1)) + 1.0 for t, cnt in df.items()}
    _index = inverted


def _ensureIndex() -> None:
    """인덱스가 없으면 빌드."""
    if _index is None:
        _buildIndex()


# ---------------------------------------------------------------------------
# 검색
# ---------------------------------------------------------------------------


def searchCapabilities(
    query: str,
    *,
    topK: int = 10,
    minScore: float = 0.5,
) -> list[tuple[str, dict, float]]:
    """질문에서 관련 CAPABILITIES를 검색.

    Args:
        query: 자연어 질문.
        topK: 최대 반환 수.
        minScore: 최소 점수 (이하 제외).

    Returns:
        [(key, entry_dict, score), ...] — score 내림차순.
    """
    _ensureIndex()
    assert _index is not None

    from dartlab.guide._generated import CAPABILITIES

    queryTokens = _tokenize(query)
    if not queryTokens:
        return []

    # 점수 누적
    scores: dict[int, float] = {}
    for t in queryTokens:
        idf = _idf.get(t, 0.0)
        if idf == 0.0:
            continue
        for keyIdx, weight in _index.get(t, []):
            scores[keyIdx] = scores.get(keyIdx, 0.0) + idf * weight

    if not scores:
        return []

    # 정렬 + 필터
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    results: list[tuple[str, dict, float]] = []
    for keyIdx, score in ranked[:topK]:
        if score < minScore:
            break
        key = _keys[keyIdx]
        results.append((key, CAPABILITIES[key], score))

    return results


def formatSearchResults(results: list[tuple[str, dict, float]]) -> str:
    """검색 결과를 LLM 프롬프트용 마크다운으로 포맷."""
    if not results:
        return ""

    lines: list[str] = ["## 사용 가능한 dartlab API\n"]
    for key, entry, _score in results:
        lines.append(f"### `{key}`")
        if summary := entry.get("summary"):
            lines.append(f"  {summary}")
        if guide := entry.get("guide"):
            lines.append(f"  **Guide:** {guide}")
        if seeAlso := entry.get("seeAlso"):
            lines.append(f"  **See also:** {seeAlso}")
        lines.append("")

    return "\n".join(lines)
