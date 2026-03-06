"""관계기업 파서 v2.

v1 결과 분석으로 발견된 문제 수정:
1. 투자현황: 2행 헤더 병합 → 열 매핑 정확화
2. 변동내역: 기말 열 누락 대응, 삼성전자 3열 구조 지원
3. 2024 XBRL 횡전개 포맷: 지원하지 않음 (별도 처리 필요)

핵심 타깃:
- 2025 사업보고서 (XBRL 패딩 형식) → 모든 기업
- 2023 이전 (클린 마크다운) → 모든 기업
- 2024 (순수 XBRL 횡전개) → 일부만 가능
"""

import re
from pathlib import Path
from dataclasses import dataclass, field

import polars as pl

DATA_DIR = Path("data/docsData")
OUT = Path("experiments/003_subsidiaries/output")
OUT.mkdir(exist_ok=True)


@dataclass
class AffiliateProfile:
    """관계기업 투자현황."""
    name: str
    ownership: float | None = None  # 지분율 (%)
    bookValue: float | None = None  # 장부금액
    acquisitionCost: float | None = None  # 취득원가
    location: str | None = None  # 소재지
    activity: str | None = None  # 주요 영업활동
    category: str | None = None  # 관계기업/공동기업


@dataclass
class AffiliateMovement:
    """관계기업 변동내역."""
    name: str
    opening: float | None = None  # 기초
    closing: float | None = None  # 기말
    acquisition: float | None = None  # 취득
    disposal: float | None = None  # 처분
    equityIncome: float | None = None  # 지분법손익
    equityCapChange: float | None = None  # 지분법자본변동
    dividend: float | None = None  # 배당
    impairment: float | None = None  # 손상
    other: float | None = None  # 기타


@dataclass
class AffiliateResult:
    """연도별 관계기업 분석 결과."""
    profiles: list[AffiliateProfile] = field(default_factory=list)
    movements: list[AffiliateMovement] = field(default_factory=list)


def extractNotes(df: pl.DataFrame, year: str) -> list[str]:
    """사업보고서 연결재무제표 주석."""
    filtered = df.filter(
        (pl.col("year") == year)
        & pl.col("report_type").str.contains("사업보고서")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
        & pl.col("section_title").str.contains("연결재무제표")
        & pl.col("section_title").str.contains("주석")
    )
    if filtered.height == 0:
        filtered = df.filter(
            (pl.col("year") == year)
            & pl.col("section_title").str.contains("연결재무제표")
            & pl.col("section_title").str.contains("주석")
        )
    return filtered["section_content"].to_list()


def findSection(contents: list[str], keyword: str) -> str | None:
    """번호 매긴 섹션에서 keyword 포함 섹션 텍스트."""
    for content in contents:
        lines = content.split("\n")
        startIdx = None
        endIdx = None
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"):
                continue
            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m:
                title = m.group(2).strip()
                if keyword in title:
                    startIdx = i
                elif startIdx is not None and endIdx is None:
                    endIdx = i
                    break
        if startIdx is not None:
            if endIdx is None:
                endIdx = len(lines)
            return "\n".join(lines[startIdx:endIdx])
    return None


def parseTableRows(text: str) -> list[list[str]]:
    """마크다운 테이블 행 추출. XBRL 패딩 제거."""
    rows = []
    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        # 후행 빈 셀 제거 (XBRL 패딩)
        while cells and not cells[-1]:
            cells.pop()
        if not cells:
            continue
        if all(re.match(r"^-+$", c) for c in cells if c):
            continue
        if not any(c.strip() for c in cells):
            continue
        rows.append(cells)
    return rows


def parseAmount(text: str) -> float | None:
    """금액 문자열 → float."""
    s = text.strip().replace("\xa0", "").replace(" ", "")
    if not s or s == "-" or s == "−" or s == "0":
        return 0.0 if s == "0" else None
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    if s.startswith("△"):
        negative = True
        s = s[1:]
    s = s.replace(",", "")
    if s.endswith("%"):
        try:
            return float(s[:-1])
        except ValueError:
            return None
    try:
        val = float(s)
        return -val if negative else val
    except ValueError:
        return None


_META_NAMES = {
    "구 분", "구분", "회사명", "기업명", "종 목", "기 업 명",
    "지분율(%)", "지분율", "소유지분율",
    "관계기업", "공동기업", "관계기업 및 공동기업",
    "소 계", "소계", "합 계", "합계", "계",
    "단위", "비 고", "비고",
    # 변동 항목명 (삼성전자 3열 테이블)
    "기초", "기 초", "기말", "기 말", "취득", "취 득", "처분", "처 분",
    "배당", "배 당", "배당금", "손상", "손상차손",
    "기타", "기타변동", "기타증감액",
}


_MOVEMENT_ITEM_KEYWORDS = [
    "기초", "기말", "취득", "처분", "배당", "손상", "기타",
    "지분법", "이익 중", "자본변동", "연결범위",
    "환율변동", "대체", "원금회수",
]


def _isNameCell(text: str) -> bool:
    """셀이 기업명인지 판정. 한글/영문이 포함되어야 함."""
    s = text.strip()
    if not s:
        return False
    # 주석 번호 제거한 원문
    sClean = re.sub(r"\(\*?\d*\)", "", s).strip()
    # 메타 키워드는 기업명이 아님
    if s in _META_NAMES or sClean in _META_NAMES:
        return False
    # 변동 항목명은 기업명이 아님 (삼성전자 3열 테이블의 행 이름)
    if any(sClean.startswith(kw) or sClean == kw for kw in _MOVEMENT_ITEM_KEYWORDS):
        return False
    # 순수 숫자/금액이면 이름 아님
    if parseAmount(s) is not None and s != "0":
        cleaned = re.sub(r"[,.\-%()△\s]", "", s)
        if cleaned.isdigit() or not cleaned:
            return False
    # 한글 또는 영문자가 2글자 이상 있어야 함
    alphaChars = sum(1 for c in s if c.isalpha())
    return alphaChars >= 2


# ── 투자현황 추출 ──

PROFILE_NAME_KEYWORDS = ["회사명", "기업명", "기 업 명", "종 목", "구 분"]
PROFILE_SUBHEADER_KEYWORDS = ["지분율", "소유지분율", "장부금액", "취득원가", "순자산"]


def _findHeaderColumns(headers: list[str], subHeaders: list[str] | None = None):
    """헤더(1~2행)에서 이름/지분율/장부금액/소재지 열 인덱스 탐색."""
    mapping = {
        "nameIdx": 0,
        "ownershipIdx": None,
        "bookValueIdx": None,
        "acquisitionIdx": None,
        "locationIdx": None,
        "activityIdx": None,
    }

    # 1행 헤더에서 직접 매핑
    for j, h in enumerate(headers):
        h_clean = h.strip()
        if any(kw in h_clean for kw in ["지분율", "소유지분율"]):
            mapping["ownershipIdx"] = j
        elif "장부금액" in h_clean:
            mapping["bookValueIdx"] = j
        elif "취득원가" in h_clean:
            mapping["acquisitionIdx"] = j
        elif "소재지" in h_clean or "소재국가" in h_clean or "주사업장" in h_clean:
            mapping["locationIdx"] = j
        elif any(kw in h_clean for kw in ["주요 영업활동", "주요영업활동", "관계의 성격"]):
            mapping["activityIdx"] = j

    # 2행 서브헤더에서 보완
    if subHeaders:
        for j, h in enumerate(subHeaders):
            h_clean = h.strip()
            if any(kw in h_clean for kw in ["지분율", "소유지분율"]):
                # 서브헤더의 지분율은 1행의 당기말 아래 첫 번째 서브컬럼
                # 카카오: 헤더=[회사명|소재지|당기말|||전기말], 서브=[지분율|취득원가|장부금액|장부금액]
                # → 지분율 = 서브헤더 idx 0 → 실제 데이터에서 idx 2 (당기말 아래 첫 번째)
                # 하지만 데이터행은 서브헤더와 동일한 길이
                # 보정: 데이터행 len == 서브헤더 len? 아니면 헤더 len?
                if mapping["ownershipIdx"] is None:
                    # 서브헤더 위치에서 offset 계산
                    offset = len(headers) - len(subHeaders)
                    mapping["ownershipIdx"] = j + offset
            elif "장부금액" in h_clean:
                if mapping["bookValueIdx"] is None:
                    offset = len(headers) - len(subHeaders)
                    mapping["bookValueIdx"] = j + offset
            elif "취득원가" in h_clean:
                if mapping["acquisitionIdx"] is None:
                    offset = len(headers) - len(subHeaders)
                    mapping["acquisitionIdx"] = j + offset

    return mapping


def extractProfiles(rows: list[list[str]]) -> list[AffiliateProfile]:
    """투자현황 추출. 2행 헤더 지원."""
    results = []
    headers = None
    subHeaders = None
    headerIdx = None
    dataLen = None  # 데이터행의 예상 셀 수
    category = None  # 관계기업/공동기업

    for i, cells in enumerate(rows):
        cellStr = " ".join(cells)

        # 카테고리 감지 (<관계기업>, (1) 관계기업 투자 등)
        if len(cells) <= 2:
            for kw, cat in [("관계기업", "관계기업"), ("공동기업", "공동기업")]:
                if kw in cellStr:
                    category = cat

        # 헤더 감지: 이름 키워드 + 세부 키워드 (거대행 제외)
        if len(cells) > 30:
            continue
        hasName = any(kw in cellStr for kw in PROFILE_NAME_KEYWORDS)
        hasDetail = any(kw in cellStr for kw in PROFILE_SUBHEADER_KEYWORDS + ["소재지", "소재국가", "관계의 성격", "주요영업활동", "주요 영업활동", "결산월"])
        if hasName and hasDetail:
            headers = cells
            headerIdx = i
            subHeaders = None
            dataLen = len(cells)
            continue

        # 서브헤더: 헤더 바로 다음 행이고 지분율/장부금액 키워드 포함
        if headers and headerIdx is not None and i == headerIdx + 1:
            if any(kw in cellStr for kw in PROFILE_SUBHEADER_KEYWORDS):
                subHeaders = cells
                # 데이터행은 max(headers, subHeaders) 길이
                dataLen = max(len(headers), len(subHeaders))
                continue

        if headers is None:
            continue

        # 데이터행
        if len(cells) < 2:
            # 1셀 행: 주석 or 카테고리
            s = cells[0].strip() if cells else ""
            if s.startswith("(") and ("*" in s or "주" in s):
                headers = None
                subHeaders = None
            elif any(kw in s for kw in ["관계기업", "공동기업"]):
                for kw, cat in [("관계기업", "관계기업"), ("공동기업", "공동기업")]:
                    if kw in s:
                        category = cat
            continue

        firstCell = cells[0].strip()
        # 종료 조건
        if firstCell in ("계", "합 계", "합계", "소 계"):
            continue
        if not firstCell:
            continue
        if re.match(r"^\(\*?\d", firstCell) or re.match(r"^\(주\d", firstCell):
            headers = None
            subHeaders = None
            continue

        # 기업명인지 확인
        if not _isNameCell(firstCell):
            continue

        # 열 매핑
        mapping = _findHeaderColumns(headers, subHeaders)

        name = re.sub(r"\(\*?\d+\)", "", firstCell).strip()
        name = re.sub(r"\(주\d+[,\d]*\)", "", name).strip()

        profile = AffiliateProfile(name=name, category=category)

        # 지분율
        idx = mapping["ownershipIdx"]
        if idx is not None and idx < len(cells):
            val = cells[idx].strip().rstrip("%")
            amt = parseAmount(val)
            if amt is not None and 0 < amt <= 100:
                profile.ownership = amt

        # 장부금액
        idx = mapping["bookValueIdx"]
        if idx is not None and idx < len(cells):
            profile.bookValue = parseAmount(cells[idx])

        # 취득원가
        idx = mapping["acquisitionIdx"]
        if idx is not None and idx < len(cells):
            profile.acquisitionCost = parseAmount(cells[idx])

        # 소재지
        idx = mapping["locationIdx"]
        if idx is not None and idx < len(cells):
            profile.location = cells[idx].strip() or None

        # 주요 영업활동
        idx = mapping["activityIdx"]
        if idx is not None and idx < len(cells):
            profile.activity = cells[idx].strip() or None

        # 지분율이 없으면 셀을 탐색 (% 포함 or 0~100 사이 소수)
        if profile.ownership is None:
            for c in cells[1:]:
                s = c.strip()
                if s.endswith("%"):
                    val = parseAmount(s.rstrip("%"))
                    if val is not None and 0 < val <= 100:
                        profile.ownership = val
                        break
                elif "." in s:
                    val = parseAmount(s)
                    if val is not None and 0 < val <= 100:
                        profile.ownership = val
                        break

        results.append(profile)

    return results


# ── 변동내역 추출 ──

# 열 매핑 키워드
MOVEMENT_COL_MAP = {
    "기초": "opening", "기 초": "opening", "기초금액": "opening",
    "기말": "closing", "기 말": "closing", "기말금액": "closing",
    "취득": "acquisition", "취 득": "acquisition",
    "취득(처분)": "acquisition",  # 현대차: 취득과 처분이 합쳐진 열
    "취득/처분": "acquisition",  # 네이버: 취득/처분/출자금의 환급
    "취득/처분/출자금의환급": "acquisition",
    "취득/대체": "acquisition",
    "처분": "disposal", "처 분": "disposal",
    "지분법손익": "equityIncome", "지분법이익(손실)": "equityIncome",
    "지분법이익": "equityIncome", "지분법손실": "equityIncome",
    "이익중지분해당액": "equityIncome",  # 네이버: "이익 중지분해당액"
    "지분법자본변동": "equityCapChange", "지분법 자본변동": "equityCapChange",
    "(부의)지분법자본변동": "equityCapChange",
    "배당": "dividend", "배 당": "dividend", "배당금": "dividend",
    "배당및배분": "dividend", "배당 및 배분": "dividend",
    "손상": "impairment", "손상차손": "impairment",
    "기타": "other", "기타증감액": "other", "기타변동": "other",
    "연결범위변동": "other", "대 체": "other",
    "원금회수": "other",
}

MOVEMENT_HEADER_KEYWORDS = ["기초", "기 초"]  # 변동내역 헤더의 필수 키워드


def _normalizeColName(name: str) -> str:
    """열 이름 정규화: 주석번호 제거, 공백 제거."""
    # (*1), (*), (주1) 등 주석 제거
    s = re.sub(r"\(\*\d*\)", "", name)
    s = re.sub(r"\(주\d*\)", "", s)
    # 공백/특수 제거
    s = re.sub(r"[\s·ㆍ\u3000]", "", s)
    return s.strip()


def _mapMovementColumns(headers: list[str]) -> dict[int, str]:
    """헤더 열 → AffiliateMovement 필드 매핑."""
    colMap = {}
    for j, h in enumerate(headers):
        norm = _normalizeColName(h)
        if not norm:
            continue
        # 1단계: 정확히 일치하는 키워드 우선
        matched = False
        for kw, field in MOVEMENT_COL_MAP.items():
            kwNorm = re.sub(r"[\s·ㆍ\u3000]", "", kw)
            if norm == kwNorm:
                colMap[j] = field
                matched = True
                break
        if matched:
            continue
        # 2단계: 부분 매칭 (키워드가 norm에 포함되거나 vice versa)
        for kw, field in MOVEMENT_COL_MAP.items():
            kwNorm = re.sub(r"[\s·ㆍ\u3000]", "", kw)
            if kwNorm in norm or norm in kwNorm:
                colMap[j] = field
                break
    return colMap


def _mergeSubHeader(headers: list[str], subHeaders: list[str]) -> list[str]:
    """메인헤더의 빈 셀에 서브헤더 값을 채워 병합.

    패턴: 메인헤더에 '그룹제목 | (빈) | (빈) | ... | 다음열' 형태가 있을 때
    서브헤더가 그룹제목+빈 셀들을 구체적 열 이름으로 대체.

    예: 메인=[...|지분법평가| | | | |기말금액], 서브=[이익|자본변동|배당|손상|기타]
    → 병합: [...|이익|자본변동|배당|손상|기타|기말금액]
    """
    merged = list(headers)
    # 메인헤더에서 빈 셀이 연속되는 첫 그룹 찾기
    emptyStart = None
    emptyEnd = None
    for j, h in enumerate(merged):
        if not h.strip():
            if emptyStart is None:
                emptyStart = j
            emptyEnd = j
        else:
            if emptyStart is not None:
                break
    if emptyStart is None:
        return merged

    # 빈 셀 바로 앞(그룹 제목)도 서브헤더 첫 값으로 대체할지 결정
    # 빈 셀 수 vs 서브헤더 수:
    # - 빈 셀 수 == 서브헤더 수: 빈 셀만 채우기
    # - 빈 셀 수 + 1 == 서브헤더 수: 빈 셀 앞의 그룹제목도 교체
    # - 빈 셀 수 < 서브헤더 수: 그룹제목부터 교체
    nEmpty = emptyEnd - emptyStart + 1

    if nEmpty >= len(subHeaders):
        # 빈 셀이 서브헤더보다 많거나 같음 → 빈 셀에만 채움
        for k, sh in enumerate(subHeaders):
            merged[emptyStart + k] = sh.strip()
    elif nEmpty + 1 >= len(subHeaders):
        # 빈 셀 + 그룹제목 = 서브헤더 수 → 그룹제목부터 교체
        startIdx = emptyStart - 1
        for k, sh in enumerate(subHeaders):
            idx = startIdx + k
            if 0 <= idx < len(merged):
                merged[idx] = sh.strip()
    else:
        # 그 외: 가능한 만큼 채움
        startIdx = max(0, emptyStart - 1)
        for k, sh in enumerate(subHeaders):
            idx = startIdx + k
            if idx < len(merged):
                merged[idx] = sh.strip()

    return merged


def extractMovements(rows: list[list[str]]) -> list[AffiliateMovement]:
    """변동내역 추출. 범용 헤더 매칭."""
    results = []
    headers = None
    colMap = None
    inTable = False
    tableRows = 0  # 현재 테이블에서 데이터행 수
    headerIdx = None  # 헤더 행 인덱스

    for i, cells in enumerate(rows):
        cellStr = " ".join(cells)

        # 변동내역 헤더 감지: '기초' 또는 '기 초' 포함 + 3~30열 (거대행 제외)
        hasOpening = any(kw in cellStr for kw in MOVEMENT_HEADER_KEYWORDS)
        if hasOpening and 3 <= len(cells) <= 30:
            # 변동 관련 키워드 수 체크
            movKws = sum(1 for kw in MOVEMENT_COL_MAP if kw in cellStr)
            if movKws >= 2:
                headers = cells
                colMap = _mapMovementColumns(headers)
                inTable = True
                tableRows = 0
                headerIdx = i
                continue

        # 삼성전자 특수 케이스: 구 분|당기|전기 (3열, 변동내역)
        if not inTable and len(cells) == 3:
            c0, c1, c2 = cells[0].strip(), cells[1].strip(), cells[2].strip()
            if ("구 분" in c0 or "구분" in c0) and "당기" in c1 and "전기" in c2:
                headers = cells
                colMap = {1: "current", 2: "prior"}
                inTable = True
                tableRows = 0
                headerIdx = i
                continue

        if not inTable:
            continue

        # 서브헤더 감지: 헤더 바로 다음 행, 기업명 아닌 행, 변동 키워드 포함
        if tableRows == 0 and headerIdx is not None and i == headerIdx + 1:
            subKws = sum(1 for kw in MOVEMENT_COL_MAP if kw in cellStr)
            if subKws >= 2 and len(cells) < len(headers):
                # 서브헤더를 메인헤더에 병합
                headers = _mergeSubHeader(headers, cells)
                colMap = _mapMovementColumns(headers)
                continue

        if len(cells) < 2:
            s = cells[0].strip() if cells else ""
            if s.startswith("(") and ("*" in s or "주" in s):
                inTable = False
                headers = None
            continue

        firstCell = cells[0].strip()
        if firstCell in ("계", "합 계", "합계", "소 계", "소계"):
            continue
        if not firstCell:
            continue
        if re.match(r"^\(\*?\d", firstCell) or re.match(r"^\(주\d", firstCell):
            inTable = False
            headers = None
            continue

        # 기업명이어야 함 (또는 카테고리+기업명 행)
        isCategory = firstCell in ("관계기업", "공동기업")
        if not _isNameCell(firstCell) and not isCategory:
            # 아직 데이터행이 없는데 서브헤더 키워드가 있으면 스킵
            if tableRows == 0:
                subKws = sum(1 for kw in MOVEMENT_COL_MAP if kw in cellStr)
                if subKws >= 2:
                    # 서브헤더 병합 시도 (헤더 바로 다음이 아닌 경우)
                    if len(cells) < len(headers or []):
                        headers = _mergeSubHeader(headers, cells)
                        colMap = _mapMovementColumns(headers)
                    continue
            continue

        # 카테고리 행 감지 (관계기업/공동기업이 첫 셀이고 두 번째가 기업명)
        if firstCell in ("관계기업", "공동기업") and len(cells) > 2:
            # 이 행에서 첫 셀은 카테고리, 두 번째가 실제 기업명
            firstCell = cells[1].strip() if len(cells) > 1 else firstCell
            if not _isNameCell(firstCell):
                continue

        name = re.sub(r"\(\*?\d+\)", "", firstCell).strip()
        name = re.sub(r"\(주\d+[,\d]*\)", "", name).strip()

        mv = AffiliateMovement(name=name)

        if colMap:
            # offset 계산:
            # - 헤더 > 데이터: 양수 offset (네이버: 헤더에 구분+종목 2열, 데이터에 1열)
            # - 헤더 < 데이터: 음수 offset (LG에너지: 헤더에 이름열 없음, 데이터에 이름+값)
            # - 헤더 첫 셀이 변동 키워드면 → 헤더에 이름열 없음, offset = -1
            if headers:
                firstH = _normalizeColName(headers[0])
                headerHasName = not any(
                    re.sub(r"[\s·ㆍ\u3000]", "", kw) in firstH or firstH in re.sub(r"[\s·ㆍ\u3000]", "", kw)
                    for kw in MOVEMENT_COL_MAP
                )
                if headerHasName:
                    # 헤더에 이름 열이 있음 → 일반 offset
                    offset = len(headers) - len(cells)
                else:
                    # 헤더에 이름 열 없음 → 데이터의 col 0은 이름, col 1부터 값
                    offset = -(len(cells) - len(headers))
            else:
                offset = 0

            for j, fieldName in colMap.items():
                dataIdx = j - offset
                if 0 <= dataIdx < len(cells):
                    val = parseAmount(cells[dataIdx])
                    # 특수 케이스: 구 분|당기|전기 (삼성전자)
                    if fieldName == "current":
                        pass
                    elif fieldName == "prior":
                        pass
                    else:
                        setattr(mv, fieldName, val)

        # 기말이 없으면 마지막 숫자 열 사용
        if mv.closing is None and "closing" not in (colMap or {}).values():
            # 마지막 셀부터 역순 탐색
            for j in range(len(cells) - 1, 0, -1):
                val = parseAmount(cells[j])
                if val is not None:
                    mv.closing = val
                    break

        tableRows += 1
        results.append(mv)

    return results


# ── 3열 변동표 (삼성전자 형태) ──

def extractSimpleMovement(rows: list[list[str]]) -> list[dict]:
    """구 분|당기|전기 형태의 간단한 변동표."""
    results = []
    inTable = False

    for cells in rows:
        if len(cells) != 3:
            if inTable and len(cells) < 3:
                inTable = False
            continue

        c0, c1, c2 = cells[0].strip(), cells[1].strip(), cells[2].strip()

        if ("구 분" in c0 or "구분" in c0) and ("당기" in c1 or "당분기" in c1):
            inTable = True
            continue

        if not inTable:
            continue

        if not c0 or c0.startswith("("):
            if c0.startswith("(") and ("*" in c0 or "주" in c0):
                inTable = False
            continue

        curAmt = parseAmount(c1)
        prevAmt = parseAmount(c2)

        if curAmt is not None or prevAmt is not None:
            results.append({
                "항목": c0,
                "당기": curAmt,
                "전기": prevAmt,
            })

    return results


COMPANIES = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("005380", "현대차"),
    ("066570", "LG전자"),
    ("035420", "네이버"),
    ("035720", "카카오"),
    ("005490", "POSCO홀딩스"),
    ("006400", "삼성SDI"),
    ("373220", "LG에너지솔루션"),
]


def main():
    out = []

    def p(s=""):
        out.append(s)

    p("=" * 80)
    p("관계기업 파서 v2")
    p("=" * 80)

    summary = []

    for code, name in COMPANIES:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            continue

        df = pl.read_parquet(str(path))
        years = sorted(df["year"].unique().to_list(), reverse=True)

        p(f"\n{'=' * 60}")
        p(f"  {name} ({code})")
        p(f"{'=' * 60}")

        for year in years[:3]:
            contents = extractNotes(df, year)
            if not contents:
                continue

            section = findSection(contents, "관계기업")
            if section is None:
                section = findSection(contents, "지분법")
            if section is None:
                section = findSection(contents, "공동기업")
            if section is None:
                p(f"\n  {year}: 관계기업 섹션 없음")
                summary.append((name, year, 0, 0, 0))
                continue

            rows = parseTableRows(section)
            p(f"\n  {year}: 테이블행 {len(rows)}개")

            # 투자현황
            profiles = extractProfiles(rows)
            p(f"    투자현황: {len(profiles)}개")
            for pr in profiles[:5]:
                ownStr = f"{pr.ownership:.1f}%" if pr.ownership else "?"
                bvStr = f"{pr.bookValue:,.0f}" if pr.bookValue else "?"
                locStr = pr.location or ""
                p(f"      {pr.name} | {ownStr} | 장부={bvStr} | {locStr}")

            # 변동내역
            movements = extractMovements(rows)
            p(f"    변동내역: {len(movements)}개")
            for mv in movements[:5]:
                openStr = f"{mv.opening:,.0f}" if mv.opening is not None else "?"
                closeStr = f"{mv.closing:,.0f}" if mv.closing is not None else "?"
                eqStr = f"{mv.equityIncome:,.0f}" if mv.equityIncome is not None else "?"
                p(f"      {mv.name}: 기초={openStr} → 기말={closeStr} | 지분법={eqStr}")

            # 간단 변동표 (삼성전자 등)
            simpleMovs = extractSimpleMovement(rows)
            if simpleMovs and not movements:
                p(f"    간단변동표: {len(simpleMovs)}개")
                for sm in simpleMovs[:5]:
                    curStr = f"{sm['당기']:,.0f}" if sm['당기'] is not None else "?"
                    prevStr = f"{sm['전기']:,.0f}" if sm['전기'] is not None else "?"
                    p(f"      {sm['항목']}: 당기={curStr} | 전기={prevStr}")

            nSimple = len(simpleMovs) if not movements else 0
            summary.append((name, year, len(profiles), len(movements), nSimple))

    # 요약
    p(f"\n\n{'=' * 80}")
    p("요약")
    p("=" * 80)
    p(f"{'기업':<16} {'년도':>5} {'현황':>5} {'변동':>5} {'간단':>5}")
    p("-" * 45)
    for name, year, pCnt, mCnt, sCnt in summary:
        p(f"{name:<16} {year:>5} {pCnt:>5} {mCnt:>5} {sCnt:>5}")

    outPath = OUT / "v2_parse.txt"
    outPath.write_text("\n".join(out), encoding="utf-8")
    print(f"결과 저장: {outPath}")
    print(f"총 {len(out)}줄")

    for line in out[-len(summary) - 4:]:
        print(line)


if __name__ == "__main__":
    main()
