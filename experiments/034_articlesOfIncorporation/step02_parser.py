"""
실험 034 · step02 — 정관에 관한 사항 파서

목적:
- 정관 변경 이력 테이블 파싱 (변경일, 주총명, 변경사항, 변경이유)
- 사업목적 현황 테이블 파싱 (구분, 사업목적, 영위 여부)
- 267개 배치 테스트

가설:
1. 정관 변경 이력은 4컬럼 (정관변경일|해당주총명|주요변경사항|변경이유) 구조
2. 사업목적 현황은 3컬럼 (구분|사업목적|사업영위 여부) 구조
3. 200/267 (75%) 이상에서 하나 이상 파싱 성공

실험일: 2026-03-08
"""

import os
import re
import sys

import polars as pl

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


def parseArticlesChanges(content: str) -> list[dict]:
    """정관 변경 이력 파싱."""
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            if headerFound and results:
                # 사업목적 테이블 시작시 중단
                pass
            continue

        cells = splitCells(stripped)
        if len(cells) < 3:
            continue

        # 헤더 감지
        if any("변경일" in c or "정관변경" in c for c in cells) and any(
            "주총" in c or "변경사항" in c or "변경이유" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 사업목적 테이블 시작시 중단
        if any("사업목적" in c for c in cells) and any("영위" in c for c in cells):
            break

        # 데이터 행
        date = cells[0].strip()
        if not date or len(date) < 4:
            continue

        # 날짜가 아닌 행 스킵 (숫자 시작이 아님)
        if not re.search(r"\d{4}", date):
            continue

        entry: dict = {"date": date}
        if len(cells) >= 2:
            entry["meetingName"] = cells[1].strip()
        if len(cells) >= 3:
            entry["changes"] = cells[2].strip()
        if len(cells) >= 4:
            entry["reason"] = cells[3].strip()

        results.append(entry)

    return results


def parseBusinessPurpose(content: str) -> list[dict]:
    """사업목적 현황 파싱."""
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            if headerFound and results:
                # 다른 섹션 시작시 중단 가능
                pass
            continue

        cells = splitCells(stripped)
        if len(cells) < 2:
            continue

        # 헤더 감지
        if any("사업목적" in c for c in cells) and any("영위" in c or "구 분" in c or "구분" in c for c in cells):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 정관 변경 이력 테이블 만나면 중단 (순서가 바뀐 경우)
        if any("변경일" in c or "정관변경" in c for c in cells):
            break

        # 데이터 행
        purpose = ""
        status = ""

        # 첫 번째 셀이 숫자면 구분 번호
        if len(cells) >= 3:
            purpose = cells[1].strip()
            status = cells[2].strip()
        elif len(cells) == 2:
            purpose = cells[0].strip()
            status = cells[1].strip()

        if not purpose or len(purpose) < 2:
            continue

        # "※" 주석행 스킵
        if purpose.startswith("※") or purpose.startswith("*"):
            continue

        entry: dict = {"purpose": purpose}
        if status:
            entry["active"] = "영위" in status
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
            if "정관" in title:
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                changes = parseArticlesChanges(content)
                purposes = parseBusinessPurpose(content)

                if not changes and not purposes:
                    # 해당사항 없음 체크
                    if "없습니다" in content[:500] or "해당사항" in content[:500]:
                        return {
                            "corpName": corpName,
                            "year": year,
                            "changes": [],
                            "purposes": [],
                            "noData": True,
                        }
                    continue

                return {
                    "corpName": corpName,
                    "year": year,
                    "changes": changes,
                    "purposes": purposes,
                    "noData": False,
                }
    return None


if __name__ == "__main__":
    files = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])

    ok = 0
    fail = 0
    totalChanges = 0
    totalPurposes = 0
    errors = []

    for code in files:
        try:
            r = pipeline(code)
            if r is None:
                fail += 1
            else:
                ok += 1
                totalChanges += len(r["changes"])
                totalPurposes += len(r["purposes"])
        except Exception as e:
            fail += 1
            errors.append((code, str(e)))

    total = len(files)
    print(f"\n=== 034 정관에 관한 사항 배치 결과 ===")
    print(f"성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}/{total}")
    print(f"정관 변경 이력: {totalChanges}건")
    print(f"사업목적 현황: {totalPurposes}건")
    if errors:
        print(f"\n에러 ({len(errors)}건):")
        for code, err in errors[:5]:
            print(f"  {code}: {err}")
