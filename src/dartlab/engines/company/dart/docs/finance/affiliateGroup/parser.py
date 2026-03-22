"""계열회사 현황 파서."""

import re


def splitCells(line: str) -> list[str]:
    cells = [c.strip() for c in line.split("|")]
    while cells and cells[0] == "":
        cells.pop(0)
    while cells and cells[-1] == "":
        cells.pop()
    return cells


def isSeparatorRow(line: str) -> bool:
    cells = splitCells(line)
    return all(re.match(r"^-+$", c.strip()) for c in cells if c.strip())


def parseGroupSummary(content: str) -> dict | None:
    """요약 테이블에서 그룹명, 상장수, 비상장수 추출."""
    lines = content.split("\n")

    skipNames = {"상장", "비상장", "계", "상장여부", "기업집단의 명칭", "---"}

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped:
            continue
        cells = splitCells(stripped)

        if len(cells) >= 4:
            name = cells[0].strip()
            nums = []
            for c in cells[1:]:
                c = c.strip().replace(",", "")
                if re.match(r"^\d+$", c):
                    nums.append(int(c))

            if len(nums) >= 3 and not re.match(r"^\d+$", name) and name not in skipNames:
                return {
                    "groupName": name,
                    "listedCount": nums[0],
                    "unlistedCount": nums[1],
                    "totalCount": nums[2],
                }

    return None


def _isCompanyName(text: str) -> bool:
    """텍스트가 기업명인지 판별."""
    if not text or len(text) < 2:
        return False
    if re.match(r"^[\d\-−–]+$", text):
        return False
    if re.match(r"^\d{10,}$", text.replace("-", "")):
        return False
    if text in ("-", "−", "–", "없음", "해당없음"):
        return False
    if text.startswith("※") or "참조" in text or "본문 위치" in text:
        return False
    return True


def parseAffiliateList(content: str) -> list[dict]:
    """상세표에서 국내 계열사 목록 추출."""
    # 해외 섹션 이전까지만 사용
    cutoff = len(content)
    for marker in ["해외계열회사", "해외 계열회사", "나. 해외", "2) 해외법인", "2) 해외"]:
        idx = content.find(marker)
        if idx > 0:
            cutoff = min(cutoff, idx)

    lines = content[:cutoff].split("\n")
    results: list[dict] = []
    currentStatus = None

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            continue

        cells = splitCells(stripped)
        if len(cells) < 2:
            continue

        if any(c in ("상장여부", "기업명", "회사수") for c in cells):
            continue
        if any("본문 위치" in c or "기준일" in c or "단위" in c for c in cells):
            continue

        first = cells[0].strip()

        if first in ("상장", "비상장"):
            currentStatus = first
            for c in cells[1:]:
                c = c.strip()
                if re.match(r"^\d+$", c):
                    continue
                if _isCompanyName(c):
                    results.append({"name": c, "listed": currentStatus == "상장"})
            continue

        if currentStatus is not None:
            if _isCompanyName(first):
                results.append({"name": first, "listed": currentStatus == "상장"})

    return results
