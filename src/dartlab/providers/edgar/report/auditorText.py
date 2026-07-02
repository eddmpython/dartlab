"""10-K 텍스트 감사인 추출. canonical 법인명 + 재임시작연도(auditor since). panel contentRaw 소비.

US 감사인은 companyfacts XBRL 에 없고(dei:AuditorName 은 문서 인라인 전용) 10-K 감사보고서 텍스트에만
있다. PCAOB 표준문장 "We have served as the Company's auditor since YYYY"(주어는 회사별 변형: the Firm·
Corporation 등)와 법인명(스타일드 small-caps 공백 "D ELOITTE" 포함)을 정규화 + canonical 리스트로 뽑는다.

실측(tests/_attempts/proxyGovernance/auditorProbe): 대형 10사 중 firm 10/10 · since 9/10, 전부 공지
실제값 일치(KO EY 1921·CAT PwC 1925·JPM PwC 1965). ``employeeBuild`` 와 같은 panel 텍스트 트랙.
"""

from __future__ import annotations

import re

# canonical 감사법인 (검출 패턴 → 표준명). US 상장사 감사시장 상위 + mid tier. 정규화 후 매칭.
CANONICAL_FIRMS: list[tuple[str, str]] = [
    (r"ernst\s*&\s*young", "Ernst & Young LLP"),
    (r"pricewaterhousecoopers", "PricewaterhouseCoopers LLP"),
    (r"deloitte", "Deloitte & Touche LLP"),
    (r"kpmg", "KPMG LLP"),
    (r"grant\s*thornton", "Grant Thornton LLP"),
    (r"bdo\s*usa", "BDO USA"),
    (r"rsm\s*us", "RSM US LLP"),
    (r"marcum", "Marcum LLP"),
    (r"crowe", "Crowe LLP"),
    (r"moss\s*adams", "Moss Adams LLP"),
    (r"baker\s*tilly", "Baker Tilly"),
    (r"cohnreznick", "CohnReznick LLP"),
    (r"withum", "WithumSmith+Brown"),
    (r"forvis", "Forvis Mazars"),
    (r"cherry\s*bekaert", "Cherry Bekaert"),
    (r"malone\s*bailey", "MaloneBailey LLP"),
    (r"mnp\b", "MNP LLP"),
]
_SINCE = re.compile(r"(?i)auditor\s+since\s+(?:at\s+least\s+)?(\d{4})")  # 주어 변형(the Firm 등) 허용


def _normalize(t: str) -> str:
    """스타일드 small-caps 공백 제거('D ELOITTE' → 'DELOITTE') 후 소문자."""
    return re.sub(r"\b([A-Z])\s+(?=[A-Z]{2,})", r"\1", t).lower()


def extractAuditorFromText(text: str) -> tuple[str | None, int | None]:
    """10-K 감사 관련 텍스트에서 (canonical 법인명, 재임시작연도)를 뽑는다.

    Args:
        text: 최신기 10-K 의 감사 관련 블록 연결 텍스트(panel contentRaw).

    Returns:
        tuple[str | None, int | None]: (법인명, since 연도). 미검출은 각각 None.

    Raises:
        없음.

    Example:
        >>> extractAuditorFromText("We have served as the Company's auditor since 2009. Ernst & Young LLP")
        ('Ernst & Young LLP', 2009)
    """
    m = _SINCE.search(text)
    since = int(m.group(1)) if m and 1900 <= int(m.group(1)) <= 2035 else None
    norm = _normalize(text)
    firm = next((name for pat, name in CANONICAL_FIRMS if re.search(pat, norm)), None)
    return firm, since


__all__ = ["CANONICAL_FIRMS", "extractAuditorFromText"]
