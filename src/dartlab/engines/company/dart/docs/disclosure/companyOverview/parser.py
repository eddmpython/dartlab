"""회사의 개요 정량 필드 파싱."""

from __future__ import annotations

import re

from dartlab.engines.company.dart.docs.disclosure.companyOverview.types import CreditRating

# ── 필드 존재 여부 판별 키워드 ──

_SECTION_KEYWORDS: dict[str, list[str]] = {
    "founded": ["설립일", "설립 일"],
    "address": ["주소", "소재지", "본사의 주소"],
    "homepage": ["홈페이지"],
    "subsidiaryCount": ["종속", "연결대상"],
    "isSME": ["중소기업"],
    "isVenture": ["벤처기업"],
    "creditRatings": ["신용평가"],
    "listedDate": ["상장", "기업공개"],
}


def parseOverview(text: str) -> dict:
    """회사의 개요 텍스트에서 정량 필드를 추출한다.

    Returns:
        dict with keys:
        - 추출된 필드 값 (founded, address, homepage, ...)
        - missing: list[str] — 원문에 해당 항목 자체가 없는 필드
        - failed: list[str] — 항목은 있지만 파싱 실패한 필드
    """
    result: dict = {}
    missing: list[str] = []
    failed: list[str] = []

    # ── founded ──
    _parseFounded(text, result, missing, failed)

    # ── address ──
    _parseAddress(text, result, missing, failed)

    # ── homepage ──
    _parseHomepage(text, result, missing, failed)

    # ── subsidiaryCount ──
    _parseSubsidiaryCount(text, result, missing, failed)

    # ── isSME ──
    _parseSME(text, result, missing, failed)

    # ── isVenture ──
    _parseVenture(text, result, missing, failed)

    # ── creditRatings ──
    _parseCreditRatings(text, result, missing, failed)

    # ── listedDate ──
    _parseListedDate(text, result, missing, failed)

    result["missing"] = missing
    result["failed"] = failed
    return result


def _hasSection(text: str, field: str) -> bool:
    """원문에 해당 필드 관련 키워드가 있는지 확인."""
    return any(kw in text for kw in _SECTION_KEYWORDS[field])


# ── 개별 필드 파서 ──


def _parseFounded(text: str, result: dict, missing: list[str], failed: list[str]) -> None:
    if not _hasSection(text, "founded"):
        missing.append("founded")
        return

    m = re.search(
        r"설립\s*일\s*자?\s*\n?(.*?\d{4}년\s*\d{1,2}월\s*\d{1,2}일)",
        text,
        re.DOTALL,
    )
    if m:
        dm = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", m.group(1))
        if dm:
            result["founded"] = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}"
            return

    m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일[에\s]*설립", text)
    if m:
        result["founded"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return

    failed.append("founded")


def _parseAddress(text: str, result: dict, missing: list[str], failed: list[str]) -> None:
    if not _hasSection(text, "address"):
        missing.append("address")
        return

    patterns = [
        r"\|\s*(?:주\s*소|본사\s*주소)\s*\|\s*:?\s*\|?\s*(?:\(본사\)\s*)?(.+?)\s*\|",
        r"본점소재지\s*[:：]\s*(.+)",
        r"(?:○\s*)?주\s+소\s*[:：]\s*(.+)",
        r"주소\s*[:：]\s*(.+)",
        r"\(주\s*소\)\s*(.+)",
        r"주소지는\s*'([^']+)'",
        r"본사의\s*주소[^\n]*\n[-\s]*([가-힣].{10,})",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            addr = m.group(1).strip().rstrip("|").strip()
            if len(addr) > 5 and not addr.startswith("http"):
                result["address"] = addr
                return

    failed.append("address")


def _parseHomepage(text: str, result: dict, missing: list[str], failed: list[str]) -> None:
    if not _hasSection(text, "homepage"):
        missing.append("homepage")
        return

    patterns = [
        r"홈페이지\s*[:：]?\s*(https?://\S+)",
        r"\|\s*홈페이지\s*(?:주소)?\s*\|\s*:?\s*\|?\s*(https?://\S+?)[\s|]",
        r"홈페이지[^\n]*?(https?://\S+)",
        r"\(홈페이지\)\s*(https?://\S+)",
        r"홈페이지[^\n]*?'(www\.\S+?)'",
        r"홈페이지[^\n]*?(www\.\S+?)[\s'\")]",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            hp = m.group(1).strip().rstrip("|").strip()
            if not hp.startswith("http"):
                hp = "http://" + hp
            result["homepage"] = hp
            return

    failed.append("homepage")


def _parseSubsidiaryCount(text: str, result: dict, missing: list[str], failed: list[str]) -> None:
    if not _hasSection(text, "subsidiaryCount"):
        missing.append("subsidiaryCount")
        return

    tableMatch = re.search(
        r"\|\s*합계\s*\|[\s\-]*(\d+)\s*\|[\s\-]*(?:\d+|-)\s*\|[\s\-]*(?:\d+|-)\s*\|[\s\-]*(\d+)\s*\|",
        text,
    )
    if tableMatch:
        result["subsidiaryCount"] = int(tableMatch.group(2))
        return

    # 합계 행이 전부 - 인 경우 (종속기업 0개)
    allDashMatch = re.search(r"\|\s*합계\s*\|\s*-\s*\|\s*-\s*\|\s*-\s*\|\s*-\s*\|", text)
    if allDashMatch:
        result["subsidiaryCount"] = 0
        return

    m = re.search(r"(\d+)개의?\s*종속(?:기업|회사)", text)
    if not m:
        m = re.search(r"종속기업은.*?(\d+)개사", text)
    if not m:
        m = re.search(r"(\d+)개사", text)
    if m:
        result["subsidiaryCount"] = int(m.group(1))
        return

    failed.append("subsidiaryCount")


def _parseSME(text: str, result: dict, missing: list[str], failed: list[str]) -> None:
    if not _hasSection(text, "isSME"):
        missing.append("isSME")
        return

    m = re.search(r"중소기업\s*해당\s*여부\s*(?:\|\s*)*\s*(미해당|해당)", text)
    if not m:
        m = re.search(r"중소기업에\s*(해당되지\s*않|해당)", text)
    if m:
        result["isSME"] = "해당되지" not in m.group(1) and "미해당" not in m.group(1)
        return

    failed.append("isSME")


def _parseVenture(text: str, result: dict, missing: list[str], failed: list[str]) -> None:
    if not _hasSection(text, "isVenture"):
        missing.append("isVenture")
        return

    m = re.search(r"벤처기업\s*해당\s*여부\s*\|?\s*(미해당|해당)", text)
    if m:
        result["isVenture"] = "미해당" not in m.group(1)
        return

    failed.append("isVenture")


_GRADE_RE = (
    r"Aaa|Aa[123]|A[123]|Baa[123]|Ba[123]|B[123]|Caa|Ca"
    r"|AAA|AA[+\-]|AA|A[+\-]|A[12][+\-]?|A"
    r"|BBB[+\-]|BBB|BB[+\-]|BB|B[+\-]"
    r"|CCC[+\-]|CCC|CC|D"
)
_AGENCY_RE = (
    r"Moody'?s|S&P|한국신용평가|한국기업평가|NICE신용평가|Nice신용평가"
    r"|나이스신용평가|나이스디앤비|서울신용평가|한국평가데이터|한국기업데이터"
)
_AGENCY_FULL_RE = _AGENCY_RE + r"|Fitch|한기평|한신평|NICE신평"


def _parseCreditRatings(text: str, result: dict, missing: list[str], failed: list[str]) -> None:
    if not _hasSection(text, "creditRatings"):
        missing.append("creditRatings")
        return

    creditSection = text.split("신용평가에 관한 사항")[-1]

    # 다음 섹션 경계 컷오프
    sectionCutoff = None
    for boundary in [
        "주권상장",
        "회사의 연혁",
        "주주에 관한",
        "자본금 변동",
    ]:
        pos = creditSection.find(boundary)
        if pos != -1 and (sectionCutoff is None or pos < sectionCutoff):
            sectionCutoff = pos
    if sectionCutoff is not None:
        creditSection = creditSection[:sectionCutoff]

    # "해당사항 없음" 감지 → missing 처리
    head = creditSection[:300]
    if re.search(r"해당\s*사항\s*(?:이\s*)?없|해당\s*없음", head):
        missing.append("creditRatings")
        return

    # 등급 설명표 컷오프
    descCutoff = None
    for keyword in [
        "등급별 내용",
        "정 의",
        "등 급 | 정 의",
        "투자적격등급",
        "투기등급",
        "등급의 정의",
        "등 급 정 의",
        "신용등급체계",
        "국내 신용등급 체계",
        "신용등급 체계",
    ]:
        pos = creditSection.find(keyword)
        if pos != -1 and (descCutoff is None or pos < descCutoff):
            descCutoff = pos
    if descCutoff is not None:
        creditSection = creditSection[:descCutoff]

    # 등급 범위 표기 제거
    creditSection = re.sub(r"\([A-Za-z0-9+\-]+\s*~\s*[A-Za-z0-9+\-]+\)", "", creditSection)
    creditSection = re.sub(r"[A-Za-z0-9+]+\s+~\s+[A-Za-z0-9+]+", "", creditSection)

    # 등급 뒤 (Stable), (안정적), /부정적 등 제거
    creditSection = re.sub(
        r"((?:AAA|AA[+\-]?|A[+\-]?|A[12][+\-]?|A[123]"
        r"|BBB[+\-]?|BB[+\-]?|B[+\-]?"
        r"|Aaa|Aa[123]|Baa[123]|Ba[123]|B[123]|Caa|Ca))"
        r"\s*(?:\([^)]*\)|/[가-힣]+)",
        r"\1",
        creditSection,
    )

    # "신용평가를 받은 사실이 없습니다" → missing 처리
    if re.search(r"신용평가를\s*받은\s*사실이\s*없", creditSection[:300]):
        missing.append("creditRatings")
        return

    # 날짜 정규화: 한국식 → YYYY.MM.DD
    # 'YY. MM. DD → 20YY.MM.DD
    creditSection = re.sub(
        r"'(\d{2})\.\s*(\d{1,2})\.\s*(\d{1,2})",
        lambda m: f"20{m.group(1)}.{int(m.group(2)):02d}.{int(m.group(3)):02d}",
        creditSection,
    )
    # YYYY년MM월 DD일 or YYYY년 MM월 DD일 → YYYY.MM.DD
    creditSection = re.sub(
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
        lambda m: f"{m.group(1)}.{int(m.group(2)):02d}.{int(m.group(3)):02d}",
        creditSection,
    )
    # YYYY. MM. DD → YYYY.MM.DD (공백 포함 전체)
    creditSection = re.sub(
        r"(\d{4})\.\s+(\d{1,2})\.\s+(\d{1,2})",
        lambda m: f"{m.group(1)}.{int(m.group(2)):02d}.{int(m.group(3)):02d}",
        creditSection,
    )
    # YYYY. M → YYYY.0M (단일 컴포넌트)
    creditSection = re.sub(
        r"(\d{4})\.\s+(\d{1,2})\b",
        lambda m: f"{m.group(1)}.{int(m.group(2)):02d}",
        creditSection,
    )
    # - 구분자 → .
    creditSection = re.sub(
        r"(\d{4})-(\d{2})-(\d{2})",
        r"\1.\2.\3",
        creditSection,
    )

    ratings: list[CreditRating] = []

    # 1) 서술문: "평가등급은 Aa2"
    for m in re.finditer(
        rf"({_AGENCY_RE})\S*\s+(?:의\s+)?(?:당사\s+)?평가등급은\s+({_GRADE_RE})",
        creditSection,
    ):
        ratings.append(CreditRating(agency=m.group(1), grade=m.group(2)))

    # 1b) 현등급 요약표: | 평가기관 | 현등급 | 날짜 |
    if not ratings:
        for m in re.finditer(
            rf"\|\s*({_AGENCY_FULL_RE})\s*\|\s*({_GRADE_RE})\s*\|"
            rf"\s*\d{{4}}\.\d{{2}}\.\d{{2}}\s*\|",
            creditSection,
        ):
            ratings.append(CreditRating(agency=m.group(1), grade=m.group(2)))

    # 2) 표에서 최신 행 (날짜가 첫 열)
    if not ratings:
        seen: set[tuple[str, str]] = set()
        cleanSection = re.sub(r"\([A-Za-z0-9+\-]+~[A-Za-z0-9+\-]+\)", "", creditSection)
        dateRows = list(
            re.finditer(
                r"\|\s*(\d{4}\.\d{2}(?:\.\d{2})?)\s*\|([^\n]+)",
                cleanSection,
            )
        )
        if dateRows:
            uniqueDates = list(dict.fromkeys(dr.group(1) for dr in reversed(dateRows)))
            latestYM = uniqueDates[0][:7]
            recentDates = {d for d in uniqueDates if d[:7] == latestYM}
            recentRows = [dr for dr in dateRows if dr.group(1) in recentDates]
            for dr in recentRows:
                rowText = dr.group(2)
                agencies = [am.group(1) for am in re.finditer(rf"({_AGENCY_FULL_RE})", rowText)]
                grades = [gm.group(1) for gm in re.finditer(rf"({_GRADE_RE})", rowText)]
                if len(grades) == 1 and agencies:
                    for agency in agencies:
                        key = (agency, grades[0])
                        if key not in seen:
                            seen.add(key)
                            ratings.append(CreditRating(agency=agency, grade=grades[0]))
                elif len(agencies) == 1 and grades:
                    for grade in grades:
                        key = (agencies[0], grade)
                        if key not in seen:
                            seen.add(key)
                            ratings.append(CreditRating(agency=agencies[0], grade=grade))

    if ratings:
        result["creditRatings"] = ratings
    else:
        failed.append("creditRatings")


def _parseListedDate(text: str, result: dict, missing: list[str], failed: list[str]) -> None:
    if not _hasSection(text, "listedDate"):
        missing.append("listedDate")
        return

    patterns = [
        r"(?:상장|기업공개).*?(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
        r"(?:유가증권|코스닥|코넥스|코스피).*?상장\s*\|\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            result["listedDate"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
            return

    failed.append("listedDate")
