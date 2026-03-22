"""내부통제 파서."""

import re


def extractTableBlocks(content: str) -> list[list[str]]:
    """content에서 |(pipe) 구분 테이블 블록들 추출."""
    lines = content.split("\n")
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if "|" in stripped:
            current.append(stripped)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


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


def parseInternalControlTable(block: list[str]) -> list[dict]:
    """내부회계관리제도 테이블 파싱.

    구조:
    | 사업연도 | 구분 | 운영실태 보고일 | 평가 결론 | 중요한취약점 | 시정조치 |
    | 제56기 | 내부회계관리제도 | 2025.01.24 | 효과적... | 해당사항없음 | ... |

    또는 감사인 검토 테이블:
    | 사업연도 | 감사인 | 검토(감사)의견 | 지적사항 |

    Returns:
        [{period, opinion, auditor, hasWeakness}, ...]
    """
    dataRows = [line for line in block if not isSeparatorRow(line)]
    if len(dataRows) < 3:
        return []

    blockText = " ".join(dataRows)

    # 감사인 검토 테이블인지 확인
    isAuditReview = "감사인" in blockText and ("검토" in blockText or "감사의견" in blockText)

    # 경영진 평가 테이블인지 확인
    isManagementEval = "평가" in blockText and ("결론" in blockText or "효과" in blockText)

    if not isAuditReview and not isManagementEval:
        return []

    results = []

    for row in dataRows:
        cells = splitCells(row)
        if len(cells) < 3:
            continue
        # 단위행/헤더 건너뛰기
        if any(c.strip() in ("---", "사업연도", "구 분", "구분") for c in cells[:2]):
            continue
        if any("단위" in c for c in cells):
            continue

        rowText = " ".join(cells)

        # 기 정보 추출 (제56기, 제55기 등)
        period = None
        for cell in cells:
            m = re.search(r"제?\d+기", cell)
            if m:
                period = m.group()
                break

        if period is None:
            continue

        entry: dict = {"period": period}

        if isAuditReview:
            # 감사인 추출
            for cell in cells:
                c = cell.strip()
                if c and "회계법인" in c or "감사법인" in c:
                    entry["auditor"] = c
                    break
                # 일반 감사인명 (삼일, 삼정, 안진, 한영 등)
                if c and re.match(r"(삼일|삼정|안진|한영|대주|성현|신한|이촌|다산)", c):
                    entry["auditor"] = c
                    break

            # 의견 추출
            for cell in cells:
                c = cell.strip()
                if "적정" in c or "유효" in c or "효과" in c:
                    entry["opinion"] = c
                    break
                if "비적정" in c or "부적정" in c:
                    entry["opinion"] = c
                    break

        elif isManagementEval:
            # 평가 결론 추출
            for cell in cells:
                c = cell.strip()
                if "효과" in c or "적정" in c:
                    entry["opinion"] = c[:100]
                    break

            # 중요한 취약점 여부
            for cell in cells:
                c = cell.strip()
                if "해당사항" in c or "해당없음" in c or "없음" in c:
                    entry["hasWeakness"] = False
                    break
                if "취약점" in c and ("있" in c or "발견" in c):
                    entry["hasWeakness"] = True
                    break

        if entry.get("opinion") or entry.get("auditor"):
            results.append(entry)

    return results
