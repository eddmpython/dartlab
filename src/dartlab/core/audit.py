"""감사의견 다국가 정규화 — 적정/Unqualified/適正 → 통일 코드."""

from __future__ import annotations

# 한국어 / 영어 / 일본어 → canonical code
_OPINION_MAP: dict[str, str] = {
    # unqualified (적정)
    "적정": "unqualified",
    "unqualified": "unqualified",
    "unqualified opinion": "unqualified",
    "適正": "unqualified",
    "無限定適正意見": "unqualified",
    # qualified (한정)
    "한정": "qualified",
    "qualified": "qualified",
    "qualified opinion": "qualified",
    "限定付適正": "qualified",
    "限定付適正意見": "qualified",
    # adverse (부적정)
    "부적정": "adverse",
    "adverse": "adverse",
    "adverse opinion": "adverse",
    "不適正": "adverse",
    "不適正意見": "adverse",
    # disclaimer (의견거절)
    "의견거절": "disclaimer",
    "의견불표명": "disclaimer",
    "disclaimer": "disclaimer",
    "disclaimer of opinion": "disclaimer",
    "意見不表明": "disclaimer",
    # emphasis (강조사항 포함 적정)
    "적정(강조사항)": "unqualified_emphasis",
    "적정(특기사항)": "unqualified_emphasis",
    "unqualified with emphasis": "unqualified_emphasis",
    "emphasis of matter": "unqualified_emphasis",
}

# canonical → 한국어 라벨
_LABEL_KR: dict[str, str] = {
    "unqualified": "적정",
    "qualified": "한정",
    "adverse": "부적정",
    "disclaimer": "의견거절",
    "unqualified_emphasis": "적정(강조사항)",
}

# canonical → 영어 라벨
_LABEL_EN: dict[str, str] = {
    "unqualified": "Unqualified",
    "qualified": "Qualified",
    "adverse": "Adverse",
    "disclaimer": "Disclaimer",
    "unqualified_emphasis": "Unqualified (Emphasis)",
}


def normalizeAuditOpinion(opinion: str) -> str | None:
    """감사의견을 canonical 코드로 정규화."""
    if not opinion:
        return None
    key = opinion.strip().lower()
    return _OPINION_MAP.get(key, _OPINION_MAP.get(opinion.strip()))


def auditOpinionLabel(canonical: str, lang: str = "kr") -> str:
    """canonical 코드 → 표시 라벨."""
    labels = _LABEL_KR if lang == "kr" else _LABEL_EN
    return labels.get(canonical, canonical)
