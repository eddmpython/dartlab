"""
실험 ID: 004-005
실험명: 비용의 성격별 분류 — 개선된 파싱 로직

목적:
- 004에서 파악한 실패 원인 해결
- 섹션 탐색 개선: "N." 뿐 아니라 "(N)" 형식, 테이블 내 키워드 매칭 추가
- 테이블 파싱 개선: 분리형(당기/전기 별도 블록) + 통합형(멀티컬럼) 모두 처리
- 10개 종목 성공률 80% 이상 목표

가설:
1. 섹션 탐색을 키워드 기반으로 바꾸면 "(5) 비용의 성격"도 잡힌다
2. 분리형 테이블은 "당기"/"전기" 구분자로 블록을 나눠 각각 파싱
3. 통합형 테이블은 합계 컬럼만 추출
4. 금융업(유진증권)은 최근 데이터에 비용의 성격이 없을 수 있어 제외

방법:
1. findCostByNatureSection 개선 — 번호 패턴 확장 + 키워드 폴백
2. parseSplitTable — "당기|전기" 구분자로 분리된 단일컬럼 테이블 파싱
3. parseMultiColTable — 합계 컬럼 추출
4. 10개 종목 테스트

결과 (실험 후 작성):

결론:

실험일: 2026-03-06
"""

import re
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import detectUnit, parseAmount

DATA_DIR = Path("data/docsData")


def extractNotesContent(report: pl.DataFrame) -> list[str]:
    """주석 섹션 추출. 연결 + 별도 모두."""
    section = report.filter(pl.col("section_title").str.contains("주석"))
    if section.height == 0:
        return []
    return section["section_content"].to_list()


def findCostByNatureSection(contents: list[str]) -> str | None:
    """주석에서 '비용의 성격' 영역 추출.

    탐색 순서:
    1. "N. 비용의 성격" 번호 섹션 (segment 패턴)
    2. "(N) 비용의 성격" 괄호 번호 섹션
    3. "비용의 성격" 키워드가 포함된 영역 (폴백)
    """
    for content in contents:
        lines = content.split("\n")

        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"):
                continue

            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m and "비용의 성격" in m.group(2):
                endIdx = _findNextSection(lines, i + 1, r"^(\d{1,2})\.\s+")
                return "\n".join(lines[i:endIdx])

            m2 = re.match(r"^\((\d{1,2})\)\s+(.+)", s)
            if m2 and "비용의 성격" in m2.group(2):
                endIdx = _findNextSection(lines, i + 1, r"^\(\d{1,2}\)\s+")
                return "\n".join(lines[i:endIdx])

    for content in contents:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "비용의 성격" in line:
                startIdx = max(0, i - 1)
                endIdx = _findTableEnd(lines, i + 1)
                return "\n".join(lines[startIdx:endIdx])

    return None


def _findNextSection(lines: list[str], fromIdx: int, pattern: str) -> int:
    """fromIdx부터 다음 번호 섹션을 찾아 인덱스 반환."""
    for i in range(fromIdx, len(lines)):
        s = lines[i].strip()
        if s.startswith("|"):
            continue
        if re.match(pattern, s):
            return i
    return len(lines)


def _findTableEnd(lines: list[str], fromIdx: int) -> int:
    """테이블 영역이 끝나는 지점. 빈 줄 2개 연속이면 끝."""
    emptyCount = 0
    lastTable = fromIdx
    for i in range(fromIdx, len(lines)):
        s = lines[i].strip()
        if s.startswith("|"):
            emptyCount = 0
            lastTable = i + 1
        elif not s:
            emptyCount += 1
            if emptyCount >= 2 and lastTable > fromIdx:
                return lastTable
        else:
            if "당기" in s or "전기" in s or re.match(r"^\d\)", s):
                emptyCount = 0
                continue
            if lastTable > fromIdx + 5:
                return lastTable
    return len(lines)


def parseCostByNature(sectionText: str) -> dict | None:
    """비용의 성격 섹션 파싱.

    Returns:
        {
            "당기": {계정명: 금액, ...},
            "전기": {계정명: 금액, ...},
            "order": [계정명 순서],
            "unit": "백만원" | "천원" | "원",
            "type": "split" | "multiCol",
        }
    """
    result = _tryParseInlineTable(sectionText)
    if result:
        return result

    result = _tryParseSplitTable(sectionText)
    if result:
        return result

    result = _tryParseMultiColTable(sectionText)
    if result:
        return result

    return None


def _tryParseSplitTable(text: str) -> dict | None:
    """분리형 테이블: 당기/전기가 별도 블록으로 나뉜 구조.

    | 당기 | (단위: 백만원) |
    |  | 공시금액 |
    | 계정 | 금액 |
    ...
    | 전기 | (단위: 백만원) |
    |  | 공시금액 |
    | 계정 | 금액 |
    """
    lines = text.split("\n")

    blocks: list[tuple[str, list[str]]] = []
    currentPeriod = None
    currentLines: list[str] = []

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if re.match(r"^\d\)\s*(당기|전기)", s):
                if currentPeriod and currentLines:
                    blocks.append((currentPeriod, currentLines))
                currentPeriod = "당기" if "당기" in s else "전기"
                currentLines = []
            continue

        cells = [c.strip() for c in s.split("|") if c.strip()]
        if not cells:
            continue

        if len(cells) <= 2 and any(p in cells[0] for p in ("당기", "전기")):
            if currentPeriod and currentLines:
                blocks.append((currentPeriod, currentLines))
            currentPeriod = "당기" if "당기" in cells[0] else "전기"
            currentLines = []
            continue

        if currentPeriod:
            currentLines.append(s)

    if currentPeriod and currentLines:
        blocks.append((currentPeriod, currentLines))

    if len(blocks) < 2:
        return None

    unit = detectUnit(text)
    periodData: dict[str, dict[str, float | None]] = {}
    allAccounts: list[str] = []

    for period, tableLines in blocks:
        accounts = _parseSimpleRows(tableLines, unit)
        if not accounts:
            continue
        periodData[period] = accounts
        for name in accounts:
            if name not in allAccounts:
                allAccounts.append(name)

    if not periodData or not allAccounts:
        return None

    return {
        "당기": periodData.get("당기", {}),
        "전기": periodData.get("전기", {}),
        "order": allAccounts,
        "type": "split",
    }


def _parseSimpleRows(
    tableLines: list[str], unit: float
) -> dict[str, float | None]:
    """단일컬럼 테이블 행 파싱. | 계정명 | 금액 | 형식."""
    accounts: dict[str, float | None] = {}

    for line in tableLines:
        if "---" in line:
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 2:
            continue

        name = cells[0]
        if _isSkipRow(name):
            continue

        valCell = cells[-1]
        val = parseAmount(valCell)
        if val is not None and unit != 1.0:
            val = val * unit

        name = _cleanAccountName(name)
        if name:
            accounts[name] = val

    return accounts


def _tryParseMultiColTable(text: str) -> dict | None:
    """통합형 테이블: | 계정 | 판관비 | 원가 | 합계 | 형식.

    "1) 당기" / "2) 전기" 구분자로 블록 분리,
    마지막 컬럼(합계)을 사용.
    """
    lines = text.split("\n")
    unit = detectUnit(text)

    blocks: list[tuple[str, list[str]]] = []
    currentPeriod = None
    currentLines: list[str] = []

    for line in lines:
        s = line.strip()
        m = re.match(r"^\d\)\s*(당기|전기)", s)
        if m:
            if currentPeriod and currentLines:
                blocks.append((currentPeriod, currentLines))
            currentPeriod = m.group(1)
            currentLines = []
            continue

        if s.startswith("|"):
            if currentPeriod:
                currentLines.append(s)

    if currentPeriod and currentLines:
        blocks.append((currentPeriod, currentLines))

    if len(blocks) < 2:
        return None

    periodData: dict[str, dict[str, float | None]] = {}
    allAccounts: list[str] = []

    for period, tableLines in blocks:
        accounts = _parseMultiColRows(tableLines, unit)
        if not accounts:
            continue
        periodData[period] = accounts
        for name in accounts:
            if name not in allAccounts:
                allAccounts.append(name)

    if not periodData or not allAccounts:
        return None

    return {
        "당기": periodData.get("당기", {}),
        "전기": periodData.get("전기", {}),
        "order": allAccounts,
        "type": "multiCol",
    }


def _parseMultiColRows(
    tableLines: list[str], unit: float
) -> dict[str, float | None]:
    """멀티컬럼 행에서 합계(마지막 숫자 컬럼) 추출."""
    accounts: dict[str, float | None] = {}
    headerPassed = False

    for line in tableLines:
        if "---" in line:
            headerPassed = True
            continue
        if not headerPassed:
            continue

        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 3:
            continue

        name = cells[0]
        if _isSkipRow(name):
            continue
        if "단위" in name:
            continue

        val = parseAmount(cells[-1])
        if val is not None and unit != 1.0:
            val = val * unit

        name = _cleanAccountName(name)
        if name:
            accounts[name] = val

    return accounts


def _tryParseInlineTable(text: str) -> dict | None:
    """인라인 테이블: | 구분 | 당기 | 전기 | 형식 (KR모터스 등)."""
    lines = text.split("\n")
    unit = detectUnit(text)

    tableLines = [l for l in lines if l.strip().startswith("|") and "---" not in l]
    if len(tableLines) < 3:
        return None

    headerLine = None
    dataLines = []
    for line in tableLines:
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if not cells:
            continue
        if "단위" in " ".join(cells):
            continue
        cellText = "".join(cells).replace(" ", "")
        if headerLine is None and ("당기" in cellText or "전기" in cellText) and len(cells) >= 2:
            headerLine = cells
            continue
        if headerLine and len(cells) >= 2:
            dataLines.append(cells)

    if not headerLine or not dataLines:
        return None

    danggiIdx = None
    jeongiIdx = None
    for j, h in enumerate(headerLine):
        hClean = h.replace(" ", "")
        if "당기" in hClean and danggiIdx is None:
            danggiIdx = j
        if "전기" in hClean and jeongiIdx is None:
            jeongiIdx = j

    if danggiIdx is None and jeongiIdx is None:
        return None

    danggiData: dict[str, float | None] = {}
    jeongiData: dict[str, float | None] = {}
    order: list[str] = []

    for cells in dataLines:
        name = cells[0]
        if _isSkipRow(name):
            continue
        name = _cleanAccountName(name)
        if not name:
            continue

        if danggiIdx is not None and danggiIdx < len(cells):
            val = parseAmount(cells[danggiIdx])
            if val is not None and unit != 1.0:
                val = val * unit
            danggiData[name] = val

        if jeongiIdx is not None and jeongiIdx < len(cells):
            val = parseAmount(cells[jeongiIdx])
            if val is not None and unit != 1.0:
                val = val * unit
            jeongiData[name] = val

        if name not in order:
            order.append(name)

    if not order:
        return None

    return {
        "당기": danggiData,
        "전기": jeongiData,
        "order": order,
        "type": "inline",
    }


_SKIP_KEYWORDS = [
    "구분", "구 분", "계정과목", "공시금액",
    "단위", "합 계", "합계", "성격별 비용 합계",
    "성격별비용합계", "성격별 비용",
]


def _isSkipRow(name: str) -> bool:
    cleaned = name.strip()
    if not cleaned:
        return True
    for kw in _SKIP_KEYWORDS:
        if cleaned == kw:
            return True
    return False


def _cleanAccountName(name: str) -> str:
    name = name.strip()
    name = re.sub(r"^\d+[\.\)]\s*", "", name)
    name = re.sub(r"\s+", "", name)
    return name


if __name__ == "__main__":
    files = sorted(DATA_DIR.glob("*.parquet"))[:10]

    print(f"테스트 대상: {len(files)}개 종목")
    print("=" * 80)

    success = 0
    fail = 0
    skipped = 0

    for f in files:
        df = pl.read_parquet(str(f))
        corpName = df["corp_name"][0] if "corp_name" in df.columns else f.stem

        years = sorted(df["year"].unique().to_list(), reverse=True)
        report = None
        for y in years:
            report = selectReport(df, y, reportKind="annual")
            if report is not None:
                break

        if report is None:
            print(f"\n{corpName}: 보고서 없음 (SKIP)")
            skipped += 1
            continue

        notes = extractNotesContent(report)
        if not notes:
            print(f"\n{corpName}: 주석 섹션 없음 (SKIP)")
            skipped += 1
            continue

        section = findCostByNatureSection(notes)
        if section is None:
            print(f"\n{corpName} ({f.stem}): '비용의 성격' 영역 없음 (FAIL)")
            fail += 1
            continue

        result = parseCostByNature(section)
        if result is None:
            print(f"\n{corpName} ({f.stem}): 파싱 실패 (FAIL)")
            print(f"  섹션 첫 300자: {section[:300]}")
            fail += 1
            continue

        success += 1
        danggi = result["당기"]
        jeongi = result["전기"]
        order = result["order"]

        print(f"\n{corpName} ({f.stem}) — 성공 (type: {result['type']})")
        print(f"  계정 수: {len(order)}개")

        for name in order[:8]:
            dVal = danggi.get(name)
            jVal = jeongi.get(name)
            dStr = f"{dVal:>14,.0f}" if dVal is not None else f"{'-':>14}"
            jStr = f"{jVal:>14,.0f}" if jVal is not None else f"{'-':>14}"
            print(f"    {name:<30} 당기:{dStr}  전기:{jStr}")
        if len(order) > 8:
            print(f"    ... +{len(order) - 8}개")

    total = success + fail
    print()
    print("=" * 80)
    print(f"결과: 성공 {success}/{total} (skip {skipped})")
    if total > 0:
        print(f"성공률: {success / total * 100:.0f}%")
