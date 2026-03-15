"""텍스트 분석 도구.

한국어 재무 공시 텍스트에서 키워드 추출, 감성 분석, 숫자 추출 등을 수행한다.
LLM 의존성 없이 순수 Python으로 동작. 한국어 재무 키워드 사전 내장.

사용법::

    from dartlab.tools import text

    keywords = text.extract_keywords(c.mdna)
    sentiment = text.sentiment_indicators(c.mdna)
    numbers = text.extract_numbers(c.mdna)
"""

from __future__ import annotations

import re
from collections import Counter

# ══════════════════════════════════════
# 키워드 사전
# ══════════════════════════════════════

_POSITIVE_KW = [
    "증가",
    "성장",
    "개선",
    "흑자",
    "회복",
    "상승",
    "확대",
    "호조",
    "강화",
    "증대",
    "신장",
    "양호",
    "안정",
    "도약",
    "혁신",
    "흑자전환",
    "최고",
    "최대",
    "신규",
    "수주",
    "호실적",
    "확장",
]

_NEGATIVE_KW = [
    "감소",
    "하락",
    "적자",
    "악화",
    "위축",
    "부진",
    "위험",
    "저하",
    "감축",
    "축소",
    "불황",
    "손실",
    "둔화",
    "약화",
    "부실",
    "적자전환",
    "최저",
    "감액",
    "철수",
    "축소",
    "불확실",
]

_RISK_KW = [
    "소송",
    "우발",
    "충당",
    "제재",
    "환율",
    "불확실",
    "파산",
    "부도",
    "채무불이행",
    "횡령",
    "배임",
    "과징금",
    "시정명령",
    "경고",
    "영업정지",
    "계속기업",
    "감사의견",
    "부적정",
    "한정의견",
    "의견거절",
    "특기사항",
]

_STOPWORDS = {
    "있습니다",
    "것입니다",
    "됩니다",
    "합니다",
    "하였습니다",
    "하고",
    "있는",
    "하는",
    "되는",
    "위한",
    "의한",
    "대한",
    "등의",
    "에서",
    "으로",
    "에는",
    "이며",
    "또는",
    "및",
    "등",
    "약",
    "현재",
    "당사",
    "회사",
    "기업",
    "사업",
    "보고서",
    "공시",
    "전자",
    "기간",
    "연도",
    "분기",
    "반기",
    "사업년도",
    "결산",
}


# ══════════════════════════════════════
# 키워드 추출
# ══════════════════════════════════════


def extract_keywords(
    text: str,
    *,
    top_n: int = 20,
    min_length: int = 2,
    stopwords: list[str] | None = None,
) -> list[tuple[str, int]]:
    """한국어 재무 텍스트에서 빈도 기반 키워드 추출.

    Args:
            text: 분석 대상 텍스트
            top_n: 상위 N개 키워드 반환
            min_length: 최소 글자 수
            stopwords: 추가 불용어 목록

    Returns:
            [(키워드, 빈도)] 리스트, 빈도 내림차순
    """
    if not text:
        return []

    stop = _STOPWORDS | set(stopwords or [])

    # 한국어 단어 + 영문 단어 추출
    words = re.findall(r"[가-힣]{2,}|[A-Za-z]{2,}", text)
    words = [w for w in words if len(w) >= min_length and w not in stop]

    counter = Counter(words)
    return counter.most_common(top_n)


# ══════════════════════════════════════
# 감성 분석
# ══════════════════════════════════════


def sentiment_indicators(text: str) -> dict:
    """규칙 기반 감성 분석.

    한국어 재무 키워드 사전으로 긍정/부정/리스크 지표 계산.

    Returns:
            {
                    "positive_count": int,
                    "negative_count": int,
                    "risk_count": int,
                    "positive_keywords": list[str],
                    "negative_keywords": list[str],
                    "risk_keywords": list[str],
                    "score": float,  # -1.0 ~ 1.0
            }
    """
    if not text:
        return {
            "positive_count": 0,
            "negative_count": 0,
            "risk_count": 0,
            "positive_keywords": [],
            "negative_keywords": [],
            "risk_keywords": [],
            "score": 0.0,
        }

    pos_found = [kw for kw in _POSITIVE_KW if kw in text]
    neg_found = [kw for kw in _NEGATIVE_KW if kw in text]
    risk_found = [kw for kw in _RISK_KW if kw in text]

    pos_count = sum(text.count(kw) for kw in pos_found)
    neg_count = sum(text.count(kw) for kw in neg_found)
    risk_count = sum(text.count(kw) for kw in risk_found)

    total = pos_count + neg_count
    score = (pos_count - neg_count) / total if total > 0 else 0.0

    return {
        "positive_count": pos_count,
        "negative_count": neg_count,
        "risk_count": risk_count,
        "positive_keywords": pos_found,
        "negative_keywords": neg_found,
        "risk_keywords": risk_found,
        "score": round(score, 3),
    }


# ══════════════════════════════════════
# 숫자 추출
# ══════════════════════════════════════

_NUMBER_PATTERN = re.compile(
    r"([\d,]+(?:\.\d+)?)\s*"
    r"(조원|억원|백만원|만원|원|%|백만달러|억달러|천원|주|명|건)?"
)


def extract_numbers(
    text: str,
    *,
    context_chars: int = 30,
) -> list[dict]:
    """텍스트에서 숫자와 단위·맥락 추출.

    Args:
            text: 분석 대상 텍스트
            context_chars: 숫자 주변 맥락 문자 수

    Returns:
            [{"value": float, "unit": str, "context": str}]
    """
    if not text:
        return []

    results = []
    for m in _NUMBER_PATTERN.finditer(text):
        raw_num = m.group(1).replace(",", "")
        try:
            value = float(raw_num)
        except ValueError:
            continue

        unit = m.group(2) or ""

        # 맥락 추출
        start = max(0, m.start() - context_chars)
        end = min(len(text), m.end() + context_chars)
        context = text[start:end].strip()
        context = re.sub(r"\s+", " ", context)

        results.append(
            {
                "value": value,
                "unit": unit,
                "context": context,
            }
        )

    return results


# ══════════════════════════════════════
# 섹션 비교
# ══════════════════════════════════════


def section_diff(
    sections_a: list,
    sections_b: list,
    *,
    key_attr: str = "key",
    text_attr: str = "text",
) -> dict:
    """두 섹션 리스트의 변동 비교.

    BusinessSection 같은 객체 리스트를 비교하여
    추가/삭제/변경/유지 구분.

    Returns:
            {
                    "added": [key],
                    "removed": [key],
                    "changed": [{"key": str, "change_pct": float}],
                    "unchanged": [key],
            }
    """
    import difflib

    map_a = {}
    for s in sections_a:
        k = getattr(s, key_attr, None) or str(s)
        t = getattr(s, text_attr, None) or str(s)
        map_a[k] = t

    map_b = {}
    for s in sections_b:
        k = getattr(s, key_attr, None) or str(s)
        t = getattr(s, text_attr, None) or str(s)
        map_b[k] = t

    keys_a = set(map_a.keys())
    keys_b = set(map_b.keys())

    added = sorted(keys_b - keys_a)
    removed = sorted(keys_a - keys_b)
    common = keys_a & keys_b

    changed = []
    unchanged = []
    for k in sorted(common):
        ratio = difflib.SequenceMatcher(None, map_a[k], map_b[k]).ratio()
        if ratio < 0.95:
            changed.append({"key": k, "change_pct": round((1 - ratio) * 100, 1)})
        else:
            unchanged.append(k)

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }
