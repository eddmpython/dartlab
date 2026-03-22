import re

import polars as pl

from dartlab.core.constants import ASSET_TOTAL_KEYWORDS


def _normalizeSpaces(text: str) -> str:
    """공백/특수문자 제거 (자 산 총 계 → 자산총계)."""
    return re.sub(r"[\s·ㆍ\u3000]", "", text)


def _hasAssetTotal(text: str) -> bool:
    """텍스트에 자산총계/자산합계/자산총액이 포함되어 있는지 (공백 무시)."""
    norm = _normalizeSpaces(text)
    return any(kw in norm for kw in ASSET_TOTAL_KEYWORDS)


def _findAssetTotalLine(lines: list[str]) -> int:
    """자산총계/자산합계가 포함된 첫 번째 테이블 행 인덱스."""
    for i, line in enumerate(lines):
        if "|" not in line:
            continue
        if _hasAssetTotal(line):
            return i
    return -1


def extractSummaryContent(report: pl.DataFrame) -> str | None:
    """요약재무정보 섹션 내용 추출. 연결재무 우선, 없으면 별도/개별."""
    content = None
    summary = report.filter(pl.col("section_title").str.contains("요약재무정보"))
    if summary.height > 0:
        content = summary["section_content"][0]
    else:
        finance = report.filter(pl.col("section_title").str.contains("재무에 관한 사항"))
        if finance.height > 0:
            content = finance["section_content"][0]

    if content is None:
        return None

    lines = content.split("\n")

    summaryHeaders = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if len(stripped) >= 80 or stripped.startswith("|"):
            continue
        if "요약" in stripped and ("재무" in stripped or "연결" in stripped):
            isConsolidated = "연결" in stripped
            summaryHeaders.append((i, stripped, isConsolidated))

    if not summaryHeaders:
        return _extractFirstAssetTable(lines)

    target = None
    for idx, title, isCons in summaryHeaders:
        if isCons:
            target = (idx, title)
            break
    if target is None:
        target = (summaryHeaders[0][0], summaryHeaders[0][1])

    startIdx = target[0]

    endIdx = len(lines)
    inTable = False
    for i in range(startIdx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("|"):
            inTable = True
        elif inTable and stripped:
            if re.match(r"^\d+\.", stripped) or re.match(r"^[가-힣][.．]", stripped):
                endIdx = i
                break

    region = "\n".join(lines[startIdx:endIdx])
    if not _hasAssetTotal(region):
        return _extractFirstAssetTable(lines)

    return region


def _extractFirstAssetTable(lines: list[str]) -> str | None:
    """자산총계/자산합계가 포함된 첫 번째 테이블 영역을 추출."""
    assetIdx = _findAssetTotalLine(lines)
    if assetIdx < 0:
        return None

    startIdx = 0
    for j in range(assetIdx - 1, -1, -1):
        stripped = lines[j].strip()
        if not stripped.startswith("|") and not stripped == "":
            startIdx = j
            break

    endIdx = len(lines)
    inTable = False
    for j in range(assetIdx, len(lines)):
        stripped = lines[j].strip()
        if stripped.startswith("|"):
            inTable = True
        elif inTable and stripped and not stripped.startswith("|"):
            endIdx = j
            break

    region = "\n".join(lines[startIdx:endIdx])
    if _hasAssetTotal(region):
        return region
    return None
