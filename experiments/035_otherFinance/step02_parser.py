"""
실험 035 · step02 — 기타 재무에 관한 사항 파서

목적:
- 대손충당금 설정내역 파싱 (계정과목, 채권금액, 대손충당금, 설정률)
- 재고자산 현황 파싱 (품목, 금액)
- 267개 배치 테스트

가설:
1. 대손충당금은 5컬럼 (구분|계정과목|채권금액|대손충당금|설정률) 구조
2. 200/267 (75%) 이상에서 하나 이상 파싱 성공

실험일: 2026-03-08
"""

import os
import re
import sys

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"
sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport


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


def parseAmount(text: str) -> int | None:
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    if text in ("-", "−", "–", ""):
        return None
    negative = False
    if text.startswith("△") or text.startswith("(") or text.startswith("−"):
        negative = True
        text = text.lstrip("△(−").rstrip(")")
    text = text.replace(",", "").replace(" ", "")
    text = re.sub(r"[^\d.]", "", text)
    if not text:
        return None
    try:
        val = int(float(text))
        return -val if negative else val
    except (ValueError, OverflowError):
        return None


def parseBadDebtProvision(content: str) -> list[dict]:
    """대손충당금 설정내역 파싱."""
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False
    currentPeriod = ""

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            continue

        cells = splitCells(stripped)
        if len(cells) < 3:
            continue

        # 단위 행 스킵
        if any("단위" in c for c in cells) and len(cells) <= 2:
            continue

        # 헤더 감지
        if any("계정과목" in c for c in cells) and any("대손충당금" in c or "충당금" in c for c in cells):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 변동현황 테이블 시작시 중단
        if any("기초" in c and "잔액" in c for c in cells):
            break
        if any("변동" in c for c in cells) and any("현황" in c for c in cells):
            break

        # 기수 감지 (제96기, 제95기 등)
        periodMatch = re.search(r"제\d+기", cells[0])
        if periodMatch:
            currentPeriod = periodMatch.group()

        # 숫자가 있는 셀 찾기
        nums = [parseAmount(c) for c in cells]
        validNums = [n for n in nums if n is not None]

        if not validNums:
            continue

        # 계정과목 찾기
        account = ""
        for c in cells:
            if parseAmount(c) is None and c.strip() and c.strip() not in ("-", "−", "–"):
                cleaned = re.sub(r"제\d+기", "", c).strip()
                if cleaned and len(cleaned) >= 2:
                    account = cleaned
                    break

        if not account:
            continue

        entry: dict = {"account": account}
        if currentPeriod:
            entry["period"] = currentPeriod
        if len(validNums) >= 1:
            entry["totalDebt"] = validNums[0]
        if len(validNums) >= 2:
            entry["provision"] = validNums[1]

        results.append(entry)

    return results


def parseInventory(content: str) -> list[dict]:
    """재고자산 현황 파싱."""
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False
    inSection = False

    for line in lines:
        stripped = line.strip()

        if not inSection:
            if "재고자산" in stripped and ("현황" in stripped or "내역" in stripped):
                inSection = True
            continue

        if "|" not in stripped or isSeparatorRow(stripped):
            if headerFound and results:
                break
            continue

        cells = splitCells(stripped)
        if len(cells) < 2:
            continue

        if any("단위" in c for c in cells) and len(cells) <= 2:
            continue

        if any("구 분" in c or "구분" in c or "계정과목" in c for c in cells) and any(
            "금액" in c or "당기" in c or "기말" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 숫자 찾기
        nums = [parseAmount(c) for c in cells]
        validNums = [n for n in nums if n is not None]
        if not validNums:
            continue

        label = ""
        for c in cells:
            if parseAmount(c) is None and c.strip() and c.strip() not in ("-", "−", "–"):
                if len(c.strip()) >= 2:
                    label = c.strip()
                    break

        if not label:
            continue

        entry = {"item": label, "values": validNums}
        results.append(entry)

    return results


def pipeline(stockCode: str):
    try:
        df = loadData(stockCode)
    except FileNotFoundError:
        return None

    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years[:2]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        for row in report.iter_rows(named=True):
            title = row.get("section_title", "") or ""
            if "기타 재무" in title or ("기타" in title and "재무" in title):
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                badDebt = parseBadDebtProvision(content)
                inventory = parseInventory(content)

                if not badDebt and not inventory:
                    if "해당사항" in content[:500] or "없습니다" in content[:500] or "참조" in content[:300]:
                        return {
                            "corpName": corpName,
                            "year": year,
                            "badDebt": [],
                            "inventory": [],
                            "noData": True,
                        }
                    continue

                return {
                    "corpName": corpName,
                    "year": year,
                    "badDebt": badDebt,
                    "inventory": inventory,
                    "noData": False,
                }
    return None


if __name__ == "__main__":
    files = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])

    ok = 0
    fail = 0
    totalBadDebt = 0
    totalInventory = 0
    errors = []

    for code in files:
        try:
            r = pipeline(code)
            if r is None:
                fail += 1
            else:
                ok += 1
                totalBadDebt += len(r["badDebt"])
                totalInventory += len(r["inventory"])
        except Exception as e:
            fail += 1
            errors.append((code, str(e)))

    total = len(files)
    print(f"\n=== 035 기타 재무에 관한 사항 배치 결과 ===")
    print(f"성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}/{total}")
    print(f"대손충당금: {totalBadDebt}건")
    print(f"재고자산: {totalInventory}건")
    if errors:
        print(f"\n에러 ({len(errors)}건):")
        for code, err in errors[:5]:
            print(f"  {code}: {err}")
