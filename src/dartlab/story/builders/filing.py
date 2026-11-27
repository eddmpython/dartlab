"""story 블록 빌더 -- 사업보고서 문장과 재무 숫자를 연결한 이야기 (calcFilingLinks, calcNewFilingSentences).

숫자 계산은 analysis.financial.filingLink 가 하고, 여기서는 회사 문장을 인용 블록으로 옮긴다.
"""

from __future__ import annotations

import re

from dartlab.story.builders._shared import (
    HeadingBlock,
    MetricBlock,
    TextBlock,
    _fmtAmtShort,
    _meta,
)

_SENTENCE_CLIP = 300
_ACCOUNT_LIMIT = 8
_REASON_SHOWN = 2
_SEGMENT_LIMIT = 6
_FOLLOWING_SHOWN = 2
_NEW_SENTENCE_SHOWN = 6
_NO_REASON = "이 금액을 적은 절에서는 회사가 이유를 밝히지 않았다."
_SEGMENT_SUFFIX = re.compile(r"(?:Division|Segment|Business|Sector|Ltd|Co)$")
_SEGMENT_WORD = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


def _segmentName(token: str) -> str:
    """XBRL 부문 이름(DxDivision, Sdc)을 읽는 이름(DX, SDC)으로 바꾼다."""
    base = _SEGMENT_SUFFIX.sub("", token) or token
    words = _SEGMENT_WORD.findall(base) or [base]
    return " ".join(w.upper() if len(w) <= 2 or not set(w.lower()) & set("aeiou") else w for w in words)


def _segmentHead(names: list[str]) -> str:
    """'DxDivision 매출' 같은 맞춘 숫자 이름을 부문마다 'DX 매출·영업이익' 으로 묶는다."""
    grouped: dict[str, list[str]] = {}
    for name in names:
        token, _, metric = name.rpartition(" ")
        grouped.setdefault(_segmentName(token or metric), []).append(metric if token else "")
    return ", ".join(f"{seg} {'·'.join(m for m in metrics if m)}".strip() for seg, metrics in grouped.items())


def _accountHead(entry: dict) -> str:
    """계정 이름과 올해·전년 숫자 한 줄."""
    head = f"**{entry['account']}** {_won(entry.get('current'))}"
    if entry.get("previous") is not None:
        head += f" (전년 {_won(entry.get('previous'))})"
    return head


def _clip(sentence: str) -> str:
    """긴 회사 문장을 읽을 만한 길이로 자른다."""
    text = " ".join(str(sentence).split())
    return text if len(text) <= _SENTENCE_CLIP else text[: _SENTENCE_CLIP - 1] + "…"


def _where(item: dict) -> str:
    """문장이 나온 사업보고서 위치(장 > 절)."""
    parts = [p for p in (item.get("chapter"), item.get("section")) if p]
    return " > ".join(parts)


def _quote(item: dict) -> str:
    """회사 문장 하나를 위치와 함께 인용 줄로 만든다."""
    where = _where(item)
    return f"> {_clip(item['sentence'])}" + (f" ({where})" if where else "")


def _won(value) -> str:
    """원화 금액을 조·억 단위 글로 쓴다. 값이 없으면 '-'."""
    text = _fmtAmtShort(value)
    return text if text == "-" or text.startswith("$") else f"{text}원"


def filingCoverageBlock(data: dict | None) -> list:
    """calcFilingLinks 결과 -> 사업보고서 금액을 재무 숫자와 맞춘 규모."""
    if not data:
        return []
    explained = sum(1 for entry in data.get("accounts") or [] if entry.get("reasons"))
    return [
        HeadingBlock(
            _meta("filingCoverage").label,
            level=2,
            helper=f"{data['year']}년 사업보고서 글 전체에서 원화 금액을 읽어 재무제표·부문 숫자와 맞췄다",
        ),
        MetricBlock(
            [
                ("재무 숫자와 맞은 금액", f"{data['amountCount']:,}개 가운데 {data['matchedCount']:,}개"),
                ("회사가 이유를 붙인 계정", f"{data['accountCount']:,}개 가운데 {explained:,}개"),
                ("읽은 문장", f"{data['sentenceCount']:,}개"),
                ("부문 설명 문장", f"{len(data.get('segments') or []):,}개"),
            ]
        ),
    ]


def filingAccountStoryBlock(data: dict | None) -> list:
    """calcFilingLinks 결과 -> 계정마다 금액 문장과 회사가 밝힌 이유 인용."""
    accounts = (data or {}).get("accounts") or []
    if not accounts:
        return []
    ordered = [a for a in accounts if a.get("reasons")] + [a for a in accounts if not a.get("reasons")]
    blocks: list = [
        HeadingBlock(
            _meta("filingAccountStory").label,
            level=2,
            helper="금액이 나온 문장과, 같은 글에서 회사가 그 계정을 두고 밝힌 이유",
        )
    ]
    groups: dict[tuple, dict] = {}
    for entry in ordered:
        explained = bool(entry.get("reasons"))
        quotes = entry["reasons"][:_REASON_SHOWN] if explained else entry["mentions"][:1]
        key = (explained, *(q["sentence"] for q in quotes))
        group = groups.setdefault(key, {"heads": [], "quotes": quotes, "explained": explained})
        group["heads"].append(_accountHead(entry))
    for group in list(groups.values())[:_ACCOUNT_LIMIT]:
        lines = group["heads"] + [_quote(q) for q in group["quotes"]]
        if not group["explained"]:
            lines.append(_NO_REASON)
        blocks.append(TextBlock("\n\n".join(lines)))
    return blocks


def filingSegmentStoryBlock(data: dict | None) -> list:
    """calcFilingLinks 결과 -> 부문 숫자 문장과 그 뒤 회사 설명 인용."""
    segments = (data or {}).get("segments") or []
    if not segments:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("filingSegmentStory").label,
            level=2,
            helper="부문 매출·영업이익이 나온 문장과, 그 뒤에 회사가 붙인 시장·사업 설명",
        )
    ]
    for item in segments[:_SEGMENT_LIMIT]:
        lines = [f"**{_segmentHead(item['segments'])}**", _quote(item)]
        lines.extend(f"- {_clip(s)}" for s in (item.get("following") or [])[:_FOLLOWING_SHOWN])
        blocks.append(TextBlock("\n\n".join(lines)))
    return blocks


def newFilingSentencesBlock(data: dict | None) -> list:
    """calcNewFilingSentences 결과 -> 전년 사업보고서에 없던 문장 인용."""
    sentences = (data or {}).get("sentences") or []
    if not sentences:
        return []
    return [
        HeadingBlock(
            _meta("newFilingSentences").label,
            level=2,
            helper=(
                f"{data['previousPeriod'][:4]}년 보고서에 없던 문장 {data['newSentenceCount']:,}개 가운데 "
                "전망·위험·변화를 말한 문장"
            ),
        ),
        TextBlock("\n\n".join(_quote(item) for item in sentences[:_NEW_SENTENCE_SHOWN])),
    ]


__all__ = [
    "filingCoverageBlock",
    "filingAccountStoryBlock",
    "filingSegmentStoryBlock",
    "newFilingSentencesBlock",
]
