"""
실험 ID: 022-01
실험명: 이사회 섹션 구조 탐색

목적:
- "VI. 이사회 등 회사의 기관에 관한 사항" 및 하위 섹션 구조 파악
- 이사회 개최횟수, 참석률, 위원회 구성 테이블 존재 여부 확인
- 파싱 가능한 정량 데이터 식별

가설:
1. "1. 이사회에 관한 사항" 하위에 이사회 운영 테이블이 존재
2. 개최횟수, 참석률 등 정량 데이터를 시계열로 추출 가능
3. 223/267 기업에서 데이터 존재

방법:
1. 267개 기업에서 이사회 관련 섹션 탐색
2. 테이블 블록 분류 및 정량 데이터 식별
3. 대표 기업 샘플로 파싱 가능성 평가

결과 (실험 후 작성):

결론:

실험일: 2026-03-08
"""
import collections
import os
import re
import sys

import polars as pl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

BOARD_SECTION_PATTERNS = [
    r"이사회에\s*관한\s*사항",
]

BOARD_PARENT_PATTERNS = [
    r"이사회\s*등\s*회사의\s*기관",
]


def findBoardSection(df: pl.DataFrame, year: str) -> str | None:
    """이사회 섹션 content 반환."""
    report = selectReport(df, year, reportKind="annual")
    if report is None:
        return None

    # 소분류 우선
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in BOARD_SECTION_PATTERNS):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content

    # 대분류 fallback
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in BOARD_PARENT_PATTERNS):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content

    return None


def extractTableBlocks(content: str) -> list[list[str]]:
    """파이프라인 테이블 블록 추출."""
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


def blockSummary(block: list[str]) -> str:
    """블록 처음 4줄 요약."""
    lines = []
    for line in block[:4]:
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if not all(re.match(r"^-+$", c) or c == "" for c in cells):
            lines.append(" | ".join(cells))
    return " // ".join(lines)


if __name__ == "__main__":
    # 1) 샘플 기업으로 구조 탐색
    targets = [
        ("005930", "삼성전자"),
        ("005380", "현대자동차"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
    ]

    for code, name in targets:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        df = loadData(code)
        years = sorted(df["year"].unique().to_list(), reverse=True)

        content = findBoardSection(df, years[0])
        if content is None:
            print("  섹션 없음")
            continue

        print(f"  content 길이: {len(content)}")

        # 테이블 블록 분석
        blocks = extractTableBlocks(content)
        print(f"  테이블 블록 수: {len(blocks)}")

        for i, block in enumerate(blocks):
            summary = blockSummary(block)
            print(f"  [{i}] ({len(block)}줄) {summary[:120]}")

        # 키워드 탐색
        keywords = ["개최", "참석", "출석", "안건", "부의", "위원회", "사외이사", "이사회 운영"]
        found = []
        for kw in keywords:
            if kw in content:
                found.append(kw)
        print(f"  키워드: {found}")

    # 2) 267개 대량 탐색
    print(f"\n\n{'='*60}")
    print("267개 대량 탐색")
    print(f"{'='*60}")

    codes = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])

    hasSection = 0
    hasTable = 0
    hasAttendance = 0
    hasCommittee = 0
    noData = 0
    blockCountDist = collections.Counter()

    for code in codes:
        try:
            df = loadData(code)
            years = sorted(df["year"].unique().to_list(), reverse=True)
            content = findBoardSection(df, years[0])

            if content is None:
                noData += 1
                continue

            hasSection += 1
            blocks = extractTableBlocks(content)
            blockCountDist[len(blocks)] += 1

            if blocks:
                hasTable += 1

            if re.search(r"참석|출석|개최", content):
                hasAttendance += 1

            if re.search(r"위원회", content):
                hasCommittee += 1

        except Exception as e:
            pass

    total = len(codes)
    print(f"  섹션 보유: {hasSection}/{total}")
    print(f"  테이블 있음: {hasTable}/{total}")
    print(f"  참석/출석 키워드: {hasAttendance}/{total}")
    print(f"  위원회 키워드: {hasCommittee}/{total}")
    print(f"  NoData: {noData}")
    print(f"  블록수 분포: {dict(sorted(blockCountDist.items()))}")
