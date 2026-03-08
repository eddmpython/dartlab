"""관계기업/공동기업 투자 파싱.

일반 테이블(2023↓, 2025) 및 XBRL 횡전개(2024) 포맷 지원.
"""

import re

from dartlab.engines.docsParser.finance.affiliate.types import AffiliateMovement, AffiliateProfile

# ── 금액 파싱 ──────────────────────────────────────────────────
# core.tableParser.parseAmount와 달리 "0"→0.0 반환, 횡전개 지분율(%) 처리.


def _parseAmount(text: str) -> float | None:
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


# ── 기업명 판별 상수 ──────────────────────────────────────────


_META_NAMES = {
    "구 분", "구분", "회사명", "기업명", "종 목", "기 업 명",
    "지분율(%)", "지분율", "소유지분율",
    "관계기업", "공동기업", "관계기업 및 공동기업",
    "소 계", "소계", "합 계", "합계", "계",
    "단위", "비 고", "비고",
    "기초", "기 초", "기말", "기 말", "취득", "취 득", "처분", "처 분",
    "배당", "배 당", "배당금", "손상", "손상차손",
    "기타", "기타변동", "기타증감액",
    "장부금액", "취득원가",
}


_MOVEMENT_ITEM_KEYWORDS = [
    "기초", "기말", "취득", "처분", "배당", "손상", "기타",
    "지분법", "이익 중", "자본변동", "연결범위",
    "환율변동", "대체", "원금회수",
]


def _isNameCell(text: str) -> bool:
    """셀이 기업명인지 판정."""
    s = text.strip()
    if not s:
        return False
    sClean = re.sub(r"\(\*?\d*\)", "", s).strip()
    if s in _META_NAMES or sClean in _META_NAMES:
        return False
    if any(sClean.startswith(kw) or sClean == kw for kw in _MOVEMENT_ITEM_KEYWORDS):
        return False
    if len(sClean) >= 20 and any(
        kw in sClean
        for kw in ["에 대한", "설명", "기술", "내역에 대한", "여부", "판단"]
    ):
        return False
    if _parseAmount(s) is not None and s != "0":
        cleaned = re.sub(r"[,.\-%()△\s]", "", s)
        if cleaned.isdigit() or not cleaned:
            return False
    alphaChars = sum(1 for c in s if c.isalpha())
    return alphaChars >= 2


# ── 투자현황 (프로필) ─────────────────────────────────────────


_PROFILE_NAME_KEYWORDS = [
    "회사명", "회 사 명", "기업명", "기 업 명", "종 목", "구 분",
]
_PROFILE_SUBHEADER_KEYWORDS = [
    "지분율", "소유지분율", "연결회사지분율",
    "장부금액", "취득원가", "순자산",
]


def _findHeaderColumns(
    headers: list[str], subHeaders: list[str] | None = None
) -> dict:
    """헤더(1~2행)에서 이름/지분율/장부금액/소재지 열 인덱스."""
    mapping: dict[str, int | None] = {
        "nameIdx": 0,
        "ownershipIdx": None,
        "bookValueIdx": None,
        "acquisitionIdx": None,
        "locationIdx": None,
        "activityIdx": None,
    }

    for j, h in enumerate(headers):
        hc = h.strip()
        if any(kw in hc for kw in ["지분율", "소유지분율"]):
            mapping["ownershipIdx"] = j
        elif any(kw in hc for kw in ["장부금액", "투자자산", "투자금액"]):
            mapping["bookValueIdx"] = j
        elif "취득원가" in hc:
            mapping["acquisitionIdx"] = j
        elif any(kw in hc for kw in ["소재지", "소재국가", "주사업장", "사업 소재지"]):
            mapping["locationIdx"] = j
        elif any(kw in hc for kw in [
            "주요 영업활동", "주요영업활동", "관계의 성격",
            "영업과 주요 활동",
        ]):
            mapping["activityIdx"] = j

    if subHeaders:
        for j, h in enumerate(subHeaders):
            hc = h.strip()
            if any(kw in hc for kw in ["지분율", "소유지분율"]):
                if mapping["ownershipIdx"] is None:
                    offset = len(headers) - len(subHeaders)
                    mapping["ownershipIdx"] = j + offset
            elif "장부금액" in hc:
                if mapping["bookValueIdx"] is None:
                    offset = len(headers) - len(subHeaders)
                    mapping["bookValueIdx"] = j + offset
            elif "취득원가" in hc:
                if mapping["acquisitionIdx"] is None:
                    offset = len(headers) - len(subHeaders)
                    mapping["acquisitionIdx"] = j + offset

    return mapping


def _cleanName(text: str) -> str:
    """기업명에서 주석번호 제거."""
    name = re.sub(r"\(\*?\d+\)", "", text).strip()
    name = re.sub(r"\(주\d+[,\d]*\)", "", name).strip()
    return name


def extractProfiles(rows: list[list[str]]) -> list[AffiliateProfile]:
    """투자현황 추출. 2행 헤더 지원."""
    results: list[AffiliateProfile] = []
    headers = None
    subHeaders = None
    headerIdx = None
    dataLen = None
    category = None

    for i, cells in enumerate(rows):
        cellStr = " ".join(cells)

        if len(cells) <= 2:
            for kw, cat in [("관계기업", "관계기업"), ("공동기업", "공동기업")]:
                if kw in cellStr:
                    category = cat

        if len(cells) > 30:
            continue

        hasName = any(kw in cellStr for kw in _PROFILE_NAME_KEYWORDS)
        hasDetail = any(
            kw in cellStr
            for kw in _PROFILE_SUBHEADER_KEYWORDS
            + ["소재지", "소재국가", "관계의 성격", "주요영업활동", "주요 영업활동", "결산월"]
        )
        # 헤더 감지:
        # 1) 이름키워드 + 세부키워드 (일반)
        # 2) 첫 셀 비어있고 세부키워드 2개+ (현대차/LG전자)
        # 3) 이름키워드 없지만 세부키워드 2개+ 3셀이상 (LG에너지 순자산|지분율|장부금액)
        firstEmpty = len(cells) >= 3 and not cells[0].strip()
        detailCount = sum(
            1 for kw in _PROFILE_SUBHEADER_KEYWORDS
            + ["소재지", "소재국가", "관계의 성격", "주요영업활동", "주요 영업활동"]
            if kw in cellStr
        )
        # 반복 패턴 체크: 고유 비어있지 않은 셀이 절반 이하면 횡전개 서브헤더
        uniqueNonEmpty = set(c.strip() for c in cells if c.strip())
        isRepeating = len(uniqueNonEmpty) * 2 < len([c for c in cells if c.strip()])
        if (
            not isRepeating
            and (
                (hasName and hasDetail)
                or (firstEmpty and detailCount >= 2 and len(cells) <= 12)
                or (not hasName and detailCount >= 2 and 3 <= len(cells) <= 12)
            )
        ):
            headers = cells
            headerIdx = i
            subHeaders = None
            dataLen = len(cells)
            continue

        # 서브헤더: 헤더 바로 다음 행이고 지분율/장부금액 키워드 포함
        if headers and headerIdx is not None and i == headerIdx + 1:
            if any(kw in cellStr for kw in _PROFILE_SUBHEADER_KEYWORDS):
                subHeaders = cells
                dataLen = max(len(headers), len(subHeaders))
                continue

        # "구 분 | 당기말" 같은 2셀 헤더 → 다음 행이 실제 컬럼 헤더
        if len(cells) == 2 and any(kw in cellStr for kw in ["구 분", "구분"]):
            if any(kw in cellStr for kw in ["당기", "전기"]):
                # 다음 행을 미리 확인해서 프로필 헤더인지 체크
                if i + 1 < len(rows):
                    nextStr = " ".join(rows[i + 1])
                    if any(kw in nextStr for kw in _PROFILE_SUBHEADER_KEYWORDS):
                        # 다음 행이 실제 헤더가 될 것이므로 skip
                        continue

        if headers is None:
            continue

        if len(cells) < 2:
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
        if firstCell in ("계", "합 계", "합계", "소 계", "소계"):
            continue
        if not firstCell:
            continue
        if re.match(r"^\(\*?\d", firstCell) or re.match(r"^\(주\d", firstCell):
            headers = None
            subHeaders = None
            continue
        # 기간 행 스킵 + 헤더 리셋
        if firstCell in ("당기", "전기", "당기말", "전기말"):
            headers = None
            subHeaders = None
            continue
        # "전체 관계기업 투자금액" 등 그룹 행은 카테고리만 추출
        if firstCell.startswith("전체 "):
            for kw, cat in [("관계기업", "관계기업"), ("공동기업", "공동기업")]:
                if kw in firstCell:
                    category = cat
            # 첫 행은 카테고리 + 기업명이 합쳐진 경우 (현대차)
            if len(cells) >= 3 and _isNameCell(cells[1].strip()):
                firstCell = cells[1].strip()
            else:
                continue

        if not _isNameCell(firstCell):
            continue

        mapping = _findHeaderColumns(headers, subHeaders)

        # offset: 헤더의 비어있지 않은 첫 셀 위치 vs 데이터의 두 번째 셀 위치
        # 헤더에 이름열이 명시적이면 직접 매핑, 아니면 fallback 사용
        headerHasName = any(
            kw in headers[0].strip() for kw in _PROFILE_NAME_KEYWORDS
        ) if headers[0].strip() else False

        name = _cleanName(firstCell)
        profile = AffiliateProfile(name=name, category=category)

        if headerHasName:
            # 직접 매핑: 헤더와 데이터의 셀 수 차이로 offset
            offset = len(headers) - len(cells)

            def _adj(idx: int | None) -> int | None:
                if idx is None:
                    return None
                adj = idx - offset
                return adj if 0 <= adj < len(cells) else None

            idx = _adj(mapping["ownershipIdx"])
            if idx is not None:
                val = cells[idx].strip().rstrip("%")
                amt = _parseAmount(val)
                if amt is not None and 0 < amt <= 100:
                    profile.ownership = amt

            idx = _adj(mapping["bookValueIdx"])
            if idx is not None:
                profile.bookValue = _parseAmount(cells[idx])

            idx = _adj(mapping["acquisitionIdx"])
            if idx is not None:
                profile.acquisitionCost = _parseAmount(cells[idx])

            idx = _adj(mapping["locationIdx"])
            if idx is not None:
                profile.location = cells[idx].strip() or None

            idx = _adj(mapping["activityIdx"])
            if idx is not None:
                profile.activity = cells[idx].strip() or None

        # fallback: 셀 탐색으로 지분율/장부금액/소재지 추출
        if profile.ownership is None:
            for c in cells[1:]:
                cs = c.strip()
                if cs.endswith("%"):
                    val = _parseAmount(cs.rstrip("%"))
                    if val is not None and 0 < val <= 100:
                        profile.ownership = val
                        break
                elif "." in cs and cs.replace(".", "").replace(",", "").isdigit():
                    val = _parseAmount(cs)
                    if val is not None and 0 < val <= 100:
                        profile.ownership = val
                        break

        if profile.bookValue is None:
            # 마지막 숫자 셀을 장부금액으로
            for j in range(len(cells) - 1, 0, -1):
                val = _parseAmount(cells[j])
                if val is not None:
                    profile.bookValue = val
                    break

        if profile.location is None:
            # 한글 2자+ 비숫자 셀 중 기업명이 아닌 것을 소재지로
            for c in cells[1:]:
                cs = c.strip()
                if cs and not _parseAmount(cs) and len(cs) <= 10:
                    if any(kw in cs for kw in [
                        "한국", "대한민국", "미국", "중국", "일본", "독일",
                        "프랑스", "싱가포르", "영국", "인도", "베트남",
                    ]):
                        profile.location = cs
                        break

        if profile.activity is None and not headerHasName:
            # 헤더 없는 경우: 기업명 바로 다음 텍스트 셀이 영업활동
            for c in cells[1:]:
                cs = c.strip()
                if cs and _parseAmount(cs) is None and not cs.endswith("%"):
                    if len(cs) >= 2 and cs != profile.location:
                        profile.activity = cs
                        break

        results.append(profile)

    return results


# ── 변동내역 ──────────────────────────────────────────────────


MOVEMENT_COL_MAP = {
    "기초": "opening", "기 초": "opening", "기초금액": "opening",
    "기말": "closing", "기 말": "closing", "기말금액": "closing",
    "취득": "acquisition", "취 득": "acquisition",
    "취득(처분)": "acquisition",
    "취득/처분": "acquisition",
    "취득/처분/출자금의환급": "acquisition",
    "취득/대체": "acquisition",
    "처분": "disposal", "처 분": "disposal",
    "지분법손익": "equityIncome", "지분법이익(손실)": "equityIncome",
    "지분법이익": "equityIncome", "지분법손실": "equityIncome",
    "이익중지분해당액": "equityIncome",
    "지분법자본변동": "equityCapChange", "지분법 자본변동": "equityCapChange",
    "(부의)지분법자본변동": "equityCapChange",
    "배당": "dividend", "배 당": "dividend", "배당금": "dividend",
    "배당및배분": "dividend", "배당 및 배분": "dividend",
    "손상": "impairment", "손상차손": "impairment",
    "기타": "other", "기타증감액": "other", "기타변동": "other",
    "연결범위변동": "other", "대 체": "other",
    "원금회수": "other",
}

_MOVEMENT_HEADER_KEYWORDS = ["기초", "기 초"]


def _normalizeColName(name: str) -> str:
    """열 이름 정규화: 주석번호·공백 제거."""
    s = re.sub(r"\(\*\d*\)", "", name)
    s = re.sub(r"\(주\d*\)", "", s)
    s = re.sub(r"[\s·ㆍ\u3000]", "", s)
    return s.strip()


def _mapMovementColumns(headers: list[str]) -> dict[int, str]:
    """헤더 열 → AffiliateMovement 필드 매핑."""
    colMap: dict[int, str] = {}
    for j, h in enumerate(headers):
        norm = _normalizeColName(h)
        if not norm:
            continue
        matched = False
        for kw, field in MOVEMENT_COL_MAP.items():
            kwNorm = re.sub(r"[\s·ㆍ\u3000]", "", kw)
            if norm == kwNorm:
                colMap[j] = field
                matched = True
                break
        if matched:
            continue
        for kw, field in MOVEMENT_COL_MAP.items():
            kwNorm = re.sub(r"[\s·ㆍ\u3000]", "", kw)
            if kwNorm in norm or norm in kwNorm:
                colMap[j] = field
                break
    return colMap


def _mergeSubHeader(headers: list[str], subHeaders: list[str]) -> list[str]:
    """메인헤더의 빈 셀에 서브헤더 값을 채워 병합."""
    merged = list(headers)
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

    nEmpty = emptyEnd - emptyStart + 1

    if nEmpty >= len(subHeaders):
        for k, sh in enumerate(subHeaders):
            merged[emptyStart + k] = sh.strip()
    elif nEmpty + 1 >= len(subHeaders):
        startIdx = emptyStart - 1
        for k, sh in enumerate(subHeaders):
            idx = startIdx + k
            if 0 <= idx < len(merged):
                merged[idx] = sh.strip()
    else:
        startIdx = max(0, emptyStart - 1)
        for k, sh in enumerate(subHeaders):
            idx = startIdx + k
            if idx < len(merged):
                merged[idx] = sh.strip()

    return merged


def extractMovements(rows: list[list[str]]) -> list[AffiliateMovement]:
    """변동내역 추출. 범용 헤더 매칭."""
    results: list[AffiliateMovement] = []
    headers = None
    colMap: dict[int, str] | None = None
    inTable = False
    tableRows = 0
    headerIdx = None

    for i, cells in enumerate(rows):
        cellStr = " ".join(cells)

        hasOpening = any(kw in cellStr for kw in _MOVEMENT_HEADER_KEYWORDS)
        if hasOpening and 3 <= len(cells) <= 30:
            movKws = sum(1 for kw in MOVEMENT_COL_MAP if kw in cellStr)
            if movKws >= 2:
                headers = cells
                colMap = _mapMovementColumns(headers)
                inTable = True
                tableRows = 0
                headerIdx = i
                continue

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

        if tableRows == 0 and headerIdx is not None and i == headerIdx + 1:
            subKws = sum(1 for kw in MOVEMENT_COL_MAP if kw in cellStr)
            if subKws >= 2 and len(cells) < len(headers):
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

        isCategory = firstCell in ("관계기업", "공동기업")
        if not _isNameCell(firstCell) and not isCategory:
            if tableRows == 0:
                subKws = sum(1 for kw in MOVEMENT_COL_MAP if kw in cellStr)
                if subKws >= 2:
                    if len(cells) < len(headers or []):
                        headers = _mergeSubHeader(headers, cells)
                        colMap = _mapMovementColumns(headers)
                    continue
            continue

        if firstCell in ("관계기업", "공동기업") and len(cells) > 2:
            firstCell = cells[1].strip() if len(cells) > 1 else firstCell
            if not _isNameCell(firstCell):
                continue

        name = _cleanName(firstCell)
        mv = AffiliateMovement(name=name)

        if colMap:
            if headers:
                firstH = _normalizeColName(headers[0])
                headerHasName = not any(
                    re.sub(r"[\s·ㆍ\u3000]", "", kw) in firstH
                    or firstH in re.sub(r"[\s·ㆍ\u3000]", "", kw)
                    for kw in MOVEMENT_COL_MAP
                )
                if headerHasName:
                    offset = len(headers) - len(cells)
                else:
                    offset = -(len(cells) - len(headers))
            else:
                offset = 0

            for j, fieldName in colMap.items():
                dataIdx = j - offset
                if 0 <= dataIdx < len(cells):
                    val = _parseAmount(cells[dataIdx])
                    if fieldName in ("current", "prior"):
                        pass
                    else:
                        setattr(mv, fieldName, val)

        if mv.closing is None and "closing" not in (colMap or {}).values():
            for j in range(len(cells) - 1, 0, -1):
                val = _parseAmount(cells[j])
                if val is not None:
                    mv.closing = val
                    break

        tableRows += 1
        results.append(mv)

    return results


# ── 3열 변동표 (삼성전자 형태) ────────────────────────────────


def extractSimpleMovement(rows: list[list[str]]) -> list[dict]:
    """구 분|당기|전기 형태의 간단한 변동표."""
    results: list[dict] = []
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

        curAmt = _parseAmount(c1)
        prevAmt = _parseAmount(c2)

        if curAmt is not None or prevAmt is not None:
            results.append({
                "항목": c0,
                "당기": curAmt,
                "전기": prevAmt,
            })

    return results


# ── 횡전개(기업명=열) 파서 ────────────────────────────────────


_TRANSPOSED_PROFILE_MAP = {
    "지분율": "ownership",
    "소유지분율": "ownership",
    "장부금액": "bookValue",
    "지분법적용 투자지분": "bookValue",
    "지분법적용투자지분": "bookValue",
    "관계기업투자 장부금액": "bookValue",
    "관계기업투자장부금액": "bookValue",
    "순자산 지분금액": "bookValue",
    "순자산지분금액": "bookValue",
    "취득원가": "acquisitionCost",
    "소재지": "location",
    "소재국가": "location",
    "주요 사업 소재지": "location",
    "주요사업소재지": "location",
    "관계기업의 주요 사업 소재지": "location",
    "공동기업의 주요 사업 소재지": "location",
    "주된 사업장": "location",
    "주요 영업활동": "activity",
    "주요영업활동": "activity",
}

_TRANSPOSED_MOVEMENT_MAP = {
    "기초": "opening", "기초금액": "opening",
    "기말": "closing", "기말금액": "closing",
    "취득": "acquisition",
    "취득/처분": "acquisition",
    "취득/처분/출자금의 환급": "acquisition",
    "취득/처분/출자금의환급": "acquisition",
    "처분": "disposal",
    "지분법손익": "equityIncome",
    "지분법이익(손실)": "equityIncome",
    "이익 중 지분해당액": "equityIncome",
    "이익중지분해당액": "equityIncome",
    "지분법 자본변동": "equityCapChange",
    "지분법자본변동": "equityCapChange",
    "배당": "dividend", "배당금수령": "dividend",
    "배당금": "dividend", "배당 및 배분": "dividend",
    "손상": "impairment", "손상차손": "impairment",
    "기타": "other", "기타증감액": "other", "기타변동": "other",
    "원금회수": "other",
    # 현대차 2024 횡전개
    "지분법적용 투자지분, 기초": "opening",
    "지분법적용 투자지분, 기말": "closing",
    "취득(처분), 공동기업 및 관계기업": "acquisition",
    "배당금수취": "dividend",
    "기타증감, 공동기업 및 관계기업": "other",
    # 삼성전자 2024 횡전개
    "관계기업 및 공동기업의 기타포괄손익에 대한 지분": "equityCapChange",
}

_TRANSPOSED_NON_NAME_KEYWORDS = [
    "장부금액", "취득원가", "순자산", "순자산지분금액", "순자산(부채)", "내부거래",
    "보유주식수", "유동자산", "비유동자산", "자산", "부채", "자본",
    "매출액", "당기순이익", "당기순손실", "당기손익",
    "지분법적용", "지분법 적용", "투자지분",
    "주요 사업 소재지", "주요사업소재지", "주된 사업장",
    "주요 영업활동", "주요영업활동", "결산월",
    "지분율", "소유지분율",
    "관계의 성격", "기업의 영업", "의결권", "영향력",
    "종속기업 명칭", "담보", "보증",
]


def _isTransposedNameCell(text: str) -> bool:
    """횡전개용 기업명 판정. _isNameCell보다 엄격."""
    if not _isNameCell(text):
        return False
    s = text.strip()
    sClean = re.sub(r"\(\*?\d*\)", "", s).strip()
    for kw in _TRANSPOSED_NON_NAME_KEYWORDS:
        if kw in sClean:
            return False
    return True


def _findTransposedBlocks(rows: list[list[str]]) -> list[dict]:
    """횡전개 블록 탐색.

    블록: 기업명 행(첫 셀 비어있고 나머지에 기업명 다수) + 항목 행들.
    """
    blocks: list[dict] = []
    currentPeriod = None

    i = 0
    while i < len(rows):
        cells = rows[i]

        if len(cells) <= 2:
            c0 = cells[0].strip()
            if c0 == "당기":
                currentPeriod = "당기"
            elif c0 == "전기":
                currentPeriod = "전기"
            i += 1
            continue

        if len(cells) >= 8:
            first = cells[0].strip()
            isFirstEmpty = not first or first in (
                "전체 관계기업 투자금액", "전체 관계기업 및 공동기업",
                "관계기업", "공동기업", "전체 공동기업",
            )
            if isFirstEmpty:
                nameCount = sum(1 for c in cells[1:] if _isTransposedNameCell(c))
                if nameCount >= 3 and nameCount >= len(cells) * 0.3:
                    names: list[str | None] = []
                    for c in cells[1:]:
                        n = c.strip()
                        if _isTransposedNameCell(n):
                            n = re.sub(r"\(\*?\d+[,\d]*\)", "", n).strip()
                            n = re.sub(r"\(주\d+[,\d]*\)", "", n).strip()
                            names.append(n)
                        else:
                            names.append(None)

                    items: dict[str, list[str]] = {}
                    j = i + 1
                    while j < len(rows):
                        jcells = rows[j]
                        if len(jcells) < 3:
                            break
                        jfirst = jcells[0].strip()
                        jnameCount = sum(
                            1 for c in jcells[1:] if _isTransposedNameCell(c)
                        )
                        if not jfirst and jnameCount >= 3:
                            break
                        if len(jcells) <= 2 and jcells[0].strip() in ("당기", "전기"):
                            break

                        itemName = jfirst
                        if not itemName:
                            j += 1
                            continue

                        vals = [
                            jcells[k].strip() if k < len(jcells) else ""
                            for k in range(1, len(jcells))
                        ]
                        items[itemName] = vals
                        j += 1

                    # 블록 타입 판별
                    hasOpening = False
                    hasClosing = False
                    movCount = 0
                    profCount = 0
                    for itemName in items:
                        normItem = re.sub(r"[\s·ㆍ\u3000]", "", itemName)
                        for mk, field in _TRANSPOSED_MOVEMENT_MAP.items():
                            mkNorm = re.sub(r"[\s·ㆍ\u3000]", "", mk)
                            if mkNorm in normItem or normItem in mkNorm:
                                movCount += 1
                                if field == "opening":
                                    hasOpening = True
                                elif field == "closing":
                                    hasClosing = True
                                break
                        for pk in _TRANSPOSED_PROFILE_MAP:
                            pkNorm = re.sub(r"[\s·ㆍ\u3000]", "", pk)
                            if pkNorm in normItem or normItem in pkNorm:
                                profCount += 1
                                break

                    if hasOpening and hasClosing and movCount >= 2:
                        blockType = "movement"
                    elif profCount >= 1:
                        blockType = "profile"
                    else:
                        blockType = None

                    if items and blockType:
                        blocks.append({
                            "period": currentPeriod or "당기",
                            "names": names,
                            "items": items,
                            "blockType": blockType,
                            "startRow": i,
                        })

                    i = j
                    continue

        i += 1

    return blocks


def extractTransposedProfiles(rows: list[list[str]]) -> list[AffiliateProfile]:
    """횡전개 포맷에서 투자현황 추출."""
    blocks = _findTransposedBlocks(rows)
    results: list[AffiliateProfile] = []
    seen: set[tuple[str, str]] = set()

    for block in blocks:
        if block["blockType"] != "profile":
            continue

        names = block["names"]
        items = block["items"]

        fieldMap: dict[str, str] = {}
        for itemName in items:
            normItem = re.sub(r"[\s·ㆍ\u3000]", "", itemName)
            for pk, field in _TRANSPOSED_PROFILE_MAP.items():
                pkNorm = re.sub(r"[\s·ㆍ\u3000]", "", pk)
                if pkNorm in normItem or normItem in pkNorm:
                    fieldMap[itemName] = field
                    break

        if not fieldMap:
            continue

        for idx, name in enumerate(names):
            if name is None:
                continue
            if (name, block["period"]) in seen:
                continue
            seen.add((name, block["period"]))

            profile = AffiliateProfile(name=name)

            for itemName, field in fieldMap.items():
                vals = items[itemName]
                if idx >= len(vals):
                    continue
                valStr = vals[idx].strip()
                if not valStr:
                    continue

                if field == "ownership":
                    v = valStr.rstrip("%")
                    amt = _parseAmount(v)
                    if amt is not None:
                        if 0 < amt < 1:
                            amt *= 100
                        if 0 < amt <= 100:
                            profile.ownership = amt
                elif field == "bookValue":
                    profile.bookValue = _parseAmount(valStr)
                elif field == "acquisitionCost":
                    profile.acquisitionCost = _parseAmount(valStr)
                elif field == "location":
                    profile.location = valStr or None
                elif field == "activity":
                    profile.activity = valStr or None

            results.append(profile)

    return results


def extractTransposedMovements(rows: list[list[str]]) -> list[AffiliateMovement]:
    """횡전개 포맷에서 변동내역 추출."""
    blocks = _findTransposedBlocks(rows)
    results: list[AffiliateMovement] = []
    seen: set[tuple[str, str]] = set()

    for block in blocks:
        if block["blockType"] != "movement":
            continue

        names = block["names"]
        items = block["items"]

        fieldMap: dict[str, str] = {}
        for itemName in items:
            normItem = re.sub(r"[\s·ㆍ\u3000]", "", itemName)
            for mk, field in _TRANSPOSED_MOVEMENT_MAP.items():
                mkNorm = re.sub(r"[\s·ㆍ\u3000]", "", mk)
                if mkNorm in normItem or normItem in mkNorm:
                    fieldMap[itemName] = field
                    break

        if not fieldMap:
            continue

        for idx, name in enumerate(names):
            if name is None:
                continue
            key = (name, block["period"])
            if key in seen:
                continue
            seen.add(key)

            mv = AffiliateMovement(name=name)

            for itemName, field in fieldMap.items():
                vals = items[itemName]
                if idx >= len(vals):
                    continue
                valStr = vals[idx].strip()
                if not valStr:
                    continue

                val = _parseAmount(valStr)
                if val is not None:
                    setattr(mv, field, val)

            results.append(mv)

    return results
