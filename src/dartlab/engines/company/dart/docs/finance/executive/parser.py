"""임원 현황 테이블 파서."""

import re

# ──────────────────────────────────────────────
# 유틸리티
# ──────────────────────────────────────────────


def _cellsFromLine(line: str) -> list[str]:
    """파이프 라인에서 셀 추출."""
    return [c.strip() for c in line.split("|")[1:-1]]


def _isSeparator(cells: list[str]) -> bool:
    """--- 구분선 여부."""
    return all(re.match(r"^-+$", c.strip()) or c.strip() == "" for c in cells)


def _flatText(cells: list[str]) -> str:
    """셀 합쳐서 하나의 텍스트."""
    return " ".join(c for c in cells if c.strip())


def _parseFloat(text: str) -> float | None:
    """실수 파싱."""
    if not text or text.strip() in ("-", "", "—", "해당없음"):
        return None
    text = text.replace(",", "").replace(" ", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


# ──────────────────────────────────────────────
# 테이블 블록 추출 + 분류
# ──────────────────────────────────────────────


def extractTableBlocks(content: str) -> list[list[str]]:
    """content에서 연속된 파이프라인 블록 추출."""
    lines = content.split("\n")
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip().startswith("|"):
            current.append(line)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


def classifyBlock(block: list[str]) -> str:
    """테이블 블록 분류.

    Returns: "executive" | "unregisteredPay" | "other"
    """
    allText = ""
    for line in block[:8]:
        cells = _cellsFromLine(line)
        if not _isSeparator(cells):
            allText += " " + _flatText(cells)

    # 등기임원 테이블: "성명" + "등기임원" + ("상근" 또는 "출생")
    if re.search(r"성명", allText) and re.search(r"등기임원", allText):
        if re.search(r"상근|출생|직위", allText):
            return "executive"

    # 미등기임원 보수: "미등기" + "인원" + "급여"
    if re.search(r"미등기", allText) and re.search(r"인원|급여|보수", allText):
        return "unregisteredPay"

    return "other"


# ──────────────────────────────────────────────
# 등기임원 테이블 파서
# ──────────────────────────────────────────────


def parseExecutiveBlock(block: list[str]) -> list[dict]:
    """등기임원 테이블에서 임원 리스트 추출.

    Returns: [{name, gender, position, registrationType, fullTime}]
    """
    rows = []
    for line in block:
        cells = _cellsFromLine(line)
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 3:
        return []

    # 헤더 찾기: "성명" 포함 행
    headerIdx = None
    for i, row in enumerate(rows):
        if any("성명" in c for c in row):
            headerIdx = i
            break

    if headerIdx is None:
        return []

    # 서브헤더 확인 (의결권있는 주식 | 의결권없는 주식)
    subHeaderIdx = None
    if headerIdx + 1 < len(rows):
        nextRow = rows[headerIdx + 1]
        if any("의결권" in c for c in nextRow):
            subHeaderIdx = headerIdx + 1

    dataStart = (subHeaderIdx or headerIdx) + 1

    header = rows[headerIdx]
    nCols = len(header)

    colMap: dict[str, int] = {}
    for i, h in enumerate(header):
        h = h.strip()
        if "성명" in h:
            colMap["name"] = i
        elif "성별" in h:
            colMap["gender"] = i
        elif "직위" in h and "담당" not in h:
            colMap["position"] = i
        elif "등기" in h:
            colMap["registrationType"] = i
        elif "상근" in h:
            colMap["fullTime"] = i

    result = []
    for row in rows[dataStart:]:
        if len(row) < 4:
            continue
        filled = [c for c in row if c.strip() and c.strip() != "-"]
        if len(filled) < 2:
            continue

        while len(row) < nCols:
            row.append("")

        entry = {
            "name": row[colMap["name"]].strip() if "name" in colMap else "",
            "gender": row[colMap["gender"]].strip() if "gender" in colMap else "",
            "position": row[colMap["position"]].strip() if "position" in colMap else "",
            "registrationType": row[colMap["registrationType"]].strip() if "registrationType" in colMap else "",
            "fullTime": row[colMap["fullTime"]].strip() if "fullTime" in colMap else "",
        }

        if not entry["name"]:
            continue

        result.append(entry)

    return result


def aggregateExecutives(executives: list[dict]) -> dict:
    """임원 리스트에서 집계 통계 생성."""
    total = len(executives)
    inside = sum(1 for e in executives if "사내" in e.get("registrationType", ""))
    outside = sum(1 for e in executives if "사외" in e.get("registrationType", ""))
    otherNonexec = sum(1 for e in executives if "기타" in e.get("registrationType", ""))
    fullTime = sum(1 for e in executives if e.get("fullTime", "") == "상근")
    partTime = sum(1 for e in executives if e.get("fullTime", "") == "비상근")
    male = sum(1 for e in executives if e.get("gender", "") == "남")
    female = sum(1 for e in executives if e.get("gender", "") == "여")

    return {
        "totalRegistered": total,
        "insideDirectors": inside,
        "outsideDirectors": outside,
        "otherNonexec": otherNonexec,
        "fullTimeCount": fullTime,
        "partTimeCount": partTime,
        "maleCount": male,
        "femaleCount": female,
    }


# ──────────────────────────────────────────────
# 미등기임원 보수 테이블 파서
# ──────────────────────────────────────────────


def parseUnregisteredPayBlock(block: list[str]) -> dict | None:
    """미등기임원 보수 테이블 파싱.

    Returns:
        {
            "headcount": int,
            "totalSalary": float,      # 백만원
            "avgSalary": float,        # 백만원
        }
    """
    rows = []
    for line in block:
        cells = _cellsFromLine(line)
        if _isSeparator(cells):
            continue
        rows.append(cells)

    if len(rows) < 3:
        return None

    for row in rows:
        if any("미등기" in c for c in row):
            nums = []
            for cell in row:
                n = _parseFloat(cell)
                if n is not None:
                    nums.append(n)
            if len(nums) >= 3:
                return {
                    "headcount": int(nums[0]),
                    "totalSalary": nums[1],
                    "avgSalary": nums[2],
                }
            elif len(nums) == 2:
                return {
                    "headcount": int(nums[0]),
                    "totalSalary": nums[1],
                    "avgSalary": None,
                }
    return None
