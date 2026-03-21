from __future__ import annotations

import hashlib
import re
from functools import lru_cache
from typing import Any, Literal

from dartlab.engines.dart.docs.sections.mapper import mapSectionTitle, stripSectionPrefix

TextNodeType = Literal["heading", "body"]

_MULTISPACE_RE = re.compile(r"\s+")
_TRAILING_PUNCT_RE = re.compile(r"[\s\-–—:：;,]+$")
_RE_ROMAN = re.compile(r"^(?:[IVXivx]+)\.\s+(.+)$")
_RE_NUMERIC = re.compile(r"^(?:\d+)\.\s+(.+)$")
_RE_KOREAN = re.compile(r"^(?:[가-힣])\.\s+(.+)$")
_RE_PAREN_NUM = re.compile(r"^\((\d+)\)\s*(.+)$")
_RE_PAREN_KOR = re.compile(r"^\(([가-힣])\)\s*(.+)$")
_RE_CIRCLED = re.compile(r"^([①-⑳])\s*(.+)$")
_RE_BRACKET = re.compile(r"^\[(.+?)\]$|^【(.+?)】$")
_RE_SHORT_PAREN = re.compile(r"^\(([^)]+)\)$")
_RE_HEADING_NOISE = re.compile(
    r"^(?:"
    r"단위|주\d|참고|출처|비고"
    r"|계속|전문|요약|이하\s*여백"
    r"|연결|별도|연결기준|별도기준"
    r"|첨부|주석\s*참조"
    r")\b"
)
_RE_NONWORD = re.compile(r"[^0-9A-Za-z가-힣]+")
_RE_TEMPORAL_MARKER = re.compile(
    r"^(?:"
    r"\d{4}년(?:\s*\d{1,2}월(?:\s*\d{1,2}일)?)?"
    r"|\d{4}[./]\d{1,2}(?:[./]\d{1,2})?"
    r"|제\s*\d+\s*기(?:\s*\d*\s*분기)?"
    r"|(?:당|전|전전)(?:기|반기|분기)"
    r"|\d{4}년\s*(?:\d분기|상반기|하반기)"
    r"|FY\s*\d{4}"
    r")$"
)
_RE_SUFFIX_EGWANHAN = re.compile(r"에관한사항$")

_TOPIC_SEGMENT_ALIASES: dict[str, dict[str, str]] = {
    "companyOverview": {
        "연결대상종속기업개황": "연결대상종속사현황",
        "연결대상종속회사개황": "연결대상종속사현황",
        "연결대상종속기업현황": "연결대상종속사현황",
        "연결대상종속회사현황": "연결대상종속사현황",
        "연결대상종속회사현황요약": "연결대상종속사현황",
        "연결대상종속회사개황요약": "연결대상종속사현황",
        "연결대상종속기업개황요약": "연결대상종속사현황",
        "연결대상종속기업현황요약": "연결대상종속사현황",
        "연결대상회사의변동내용": "연결대상변동내용",
        "연결대상회사의변동현황": "연결대상변동내용",
        "당기중종속기업변동내용": "연결대상변동내용",
        "당기연결대상회사의변동내용": "연결대상변동내용",
        "본사의주소전화번호및홈페이지": "본사의주소전화번호홈페이지",
        "본사의주소전화번호및홈페이지주소": "본사의주소전화번호홈페이지",
        "본사의주소전화번호홈페이지주소": "본사의주소전화번호홈페이지",
    },
    "businessOverview": {
        "생산및설비에관한사항": "생산및설비",
        "매출에관한사항": "매출",
        "주요원재료에관한사항": "주요원재료",
        "영업의개황등": "영업현황",
        "국내외시장여건등": "시장여건",
        "산업의특성등": "산업의특성",
        "사업부문별현황": "사업부문현황",
    },
    "mdna": {
        "재무상태및영업실적연결기준": "재무상태및영업실적",
        "조직개편": "조직변경",
        "조직의변경": "조직변경",
        "조직변경등": "조직변경",
        "자산손상인식": "자산손상",
        "유동성및자금조달과지출": "유동성및자금조달",
        "환율변동영향": "환율변동",
    },
    "auditSystem": {
        "감사위원회에관한사항": "감사위원회",
        "감사위원회의위원의독립성": "감사위원회위원의독립성",
        "감사위원회의주요활동내역": "감사위원회주요활동내역",
        "준법지원인등지원조직현황": "준법지원인지원조직현황",
    },
}


def _clean_line(line: str) -> str:
    return line.replace("\u00a0", " ").replace("\t", " ").rstrip()


@lru_cache(maxsize=32768)
def _normalize_heading_text(text: str) -> str:
    cleaned = stripSectionPrefix(text.strip())
    cleaned = cleaned.strip("[]【】")
    m = _RE_SHORT_PAREN.match(cleaned)
    if m:
        cleaned = m.group(1).strip()
    cleaned = cleaned.replace("ㆍ", "·")
    cleaned = _MULTISPACE_RE.sub(" ", cleaned)
    cleaned = _TRAILING_PUNCT_RE.sub("", cleaned)
    return cleaned.strip()


@lru_cache(maxsize=32768)
def _heading_key(text: str) -> str:
    normalized = _normalize_heading_text(text)
    normalized = normalized.replace("·", "").replace("ㆍ", "")
    normalized = _RE_NONWORD.sub("", normalized)
    return normalized.strip()


def _canonical_heading_key(
    labelText: str,
    labelKey: str,
    *,
    level: int,
    topic: str | None,
) -> str:
    if level <= 3 and isinstance(topic, str) and topic:
        mapped = mapSectionTitle(labelText)
        if mapped == topic:
            return f"@topic:{topic}"
    return labelKey


@lru_cache(maxsize=65536)
def _semantic_segment_key(labelKey: str, *, topic: str | None) -> str:
    if not labelKey or labelKey.startswith("@"):
        return labelKey

    key = labelKey

    aliasMap = _TOPIC_SEGMENT_ALIASES.get(str(topic or ""), {})
    if key in aliasMap:
        key = aliasMap[key]

    key = _RE_SUFFIX_EGWANHAN.sub("", key)
    key = key.replace("종속기업", "종속사").replace("종속회사", "종속사")

    if isinstance(topic, str) and topic == "businessOverview":
        key = key.replace("영업의개황", "영업현황")
    if isinstance(topic, str) and topic == "mdna":
        key = key.replace("환율변동영향", "환율변동")

    return key


@lru_cache(maxsize=32768)
def _is_temporal_marker(text: str) -> bool:
    normalized = _normalize_heading_text(text)
    return bool(_RE_TEMPORAL_MARKER.fullmatch(normalized))


@lru_cache(maxsize=32768)
def _body_anchor(text: str) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return "empty"
    anchor = normalized[:96]
    return hashlib.blake2b(anchor.encode("utf-8"), digest_size=8).hexdigest()[:12]


@lru_cache(maxsize=32768)
def _detect_heading(line: str) -> tuple[int, str, bool] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("|"):
        return None
    if len(stripped) > 120:
        return None

    m = _RE_BRACKET.match(stripped)
    if m:
        text = m.group(1) or m.group(2) or ""
        structural = not _is_temporal_marker(text)
        return (1, text.strip(), structural)

    m = _RE_ROMAN.match(stripped)
    if m:
        return (2, m.group(1).strip(), True)

    m = _RE_NUMERIC.match(stripped)
    if m:
        return (3, m.group(1).strip(), True)

    m = _RE_KOREAN.match(stripped)
    if m:
        return (4, m.group(1).strip(), True)

    m = _RE_PAREN_NUM.match(stripped)
    if m:
        return (5, m.group(2).strip(), True)

    m = _RE_PAREN_KOR.match(stripped)
    if m:
        return (6, m.group(2).strip(), True)

    m = _RE_CIRCLED.match(stripped)
    if m:
        return (6, m.group(2).strip(), True)

    m = _RE_SHORT_PAREN.match(stripped)
    if m:
        inner = m.group(1).strip()
        if inner and len(inner) <= 48 and not _RE_HEADING_NOISE.match(inner):
            structural = not _is_temporal_marker(inner)
            return (5, inner, structural)

    return None


def parseTextStructureWithState(
    text: str,
    *,
    sourceBlockOrder: int,
    topic: str | None = None,
    initialHeadings: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, Any]]]:
    nodes: list[dict[str, object]] = []
    stack: list[dict[str, object]] = [dict(item) for item in (initialHeadings or [])]
    bodyLines: list[str] = []
    segmentOrder = 0

    def flush_body() -> None:
        nonlocal bodyLines, segmentOrder
        body = "\n".join(bodyLines).strip()
        bodyLines = []
        if not body:
            return

        pathLabels = [str(item["label"]) for item in stack]
        pathKeys = [str(item["key"]) for item in stack if str(item["key"])]
        semanticPathKeys = [str(item["semanticKey"]) for item in stack if str(item["semanticKey"])]
        pathText = " > ".join(pathLabels) if pathLabels else None
        pathKey = " > ".join(pathKeys) if pathKeys else None
        parentPathKey = " > ".join(pathKeys[:-1]) if len(pathKeys) > 1 else None
        semanticPathKey = " > ".join(semanticPathKeys) if semanticPathKeys else None
        semanticParentPathKey = " > ".join(semanticPathKeys[:-1]) if len(semanticPathKeys) > 1 else None
        level = int(stack[-1]["level"]) if stack else 0
        anchor = _body_anchor(body)
        # Text row identity should follow outline path first.
        # Raw coarse block order is preserved separately as sourceBlockOrder.
        stableKeyBase = f"body|p:{semanticPathKey}" if semanticPathKey else f"body|lv:{level}|a:{anchor}"
        nodes.append(
            {
                "textNodeType": "body",
                "textStructural": True,
                "textLevel": level,
                "textPath": pathText,
                "textPathKey": pathKey,
                "textParentPathKey": parentPathKey,
                "textSemanticPathKey": semanticPathKey,
                "textSemanticParentPathKey": semanticParentPathKey,
                "segmentOrder": segmentOrder,
                "segmentKeyBase": stableKeyBase,
                "text": body,
            }
        )
        segmentOrder += 1

    for rawLine in text.splitlines():
        line = _clean_line(rawLine)
        stripped = line.strip()
        if not stripped:
            if bodyLines:
                bodyLines.append("")
            continue

        heading = _detect_heading(stripped)
        if heading is None:
            bodyLines.append(stripped)
            continue

        flush_body()
        level, label, structural = heading
        labelText = _normalize_heading_text(label)
        labelKey = _heading_key(label)
        stackKey = _canonical_heading_key(labelText, labelKey, level=level, topic=topic)
        semanticStackKey = _semantic_segment_key(stackKey, topic=topic)
        redundantTopicAlias = (
            structural
            and bool(stack)
            and level <= 3
            and str(stackKey).startswith("@topic:")
            and int(stack[-1]["level"]) == level
            and str(stack[-1]["key"]) == stackKey
        )

        if structural and not redundantTopicAlias:
            while stack and int(stack[-1]["level"]) >= level:
                stack.pop()
            stack.append({"level": level, "label": labelText, "key": stackKey, "semanticKey": semanticStackKey})
            pathLabels = [str(item["label"]) for item in stack]
            pathKeys = [str(item["key"]) for item in stack if str(item["key"])]
            semanticPathKeys = [str(item["semanticKey"]) for item in stack if str(item["semanticKey"])]
            pathText = " > ".join(pathLabels) if pathLabels else None
            pathKey = " > ".join(pathKeys) if pathKeys else None
            parentPathKey = " > ".join(pathKeys[:-1]) if len(pathKeys) > 1 else None
            semanticPathKey = " > ".join(semanticPathKeys) if semanticPathKeys else None
            semanticParentPathKey = " > ".join(semanticPathKeys[:-1]) if len(semanticPathKeys) > 1 else None
            segmentKeyBase = f"heading|lv:{level}|p:{semanticPathKey or semanticStackKey}"
        else:
            currentPathKeys = [str(item["key"]) for item in stack if str(item["key"])]
            currentSemanticPathKeys = [str(item["semanticKey"]) for item in stack if str(item["semanticKey"])]
            pathText = labelText
            keyPrefix = "@alias" if redundantTopicAlias else "@marker"
            pathKey = f"{keyPrefix}:{labelKey}"
            parentPathKey = " > ".join(currentPathKeys) if currentPathKeys else None
            semanticPathKey = pathKey
            semanticParentPathKey = " > ".join(currentSemanticPathKeys) if currentSemanticPathKeys else None
            segmentKind = "alias" if redundantTopicAlias else "marker"
            segmentKeyBase = f"heading|{segmentKind}|lv:{level}|p:{pathKey}"
        nodes.append(
            {
                "textNodeType": "heading",
                "textStructural": structural and not redundantTopicAlias,
                "textLevel": level,
                "textPath": pathText,
                "textPathKey": pathKey,
                "textParentPathKey": parentPathKey,
                "textSemanticPathKey": semanticPathKey,
                "textSemanticParentPathKey": semanticParentPathKey,
                "segmentOrder": segmentOrder,
                "segmentKeyBase": segmentKeyBase,
                "text": stripped,
            }
        )
        segmentOrder += 1

    flush_body()
    return nodes, [dict(item) for item in stack]


def parseTextStructure(
    text: str,
    *,
    sourceBlockOrder: int,
    topic: str | None = None,
) -> list[dict[str, object]]:
    nodes, _stack = parseTextStructureWithState(text, sourceBlockOrder=sourceBlockOrder, topic=topic)
    return nodes


__all__ = ["TextNodeType", "parseTextStructure", "parseTextStructureWithState"]
