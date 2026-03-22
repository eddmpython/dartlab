"""
실험 ID: 004
실험명: MD&A 파서 전체 종목 테스트

목적:
- 전체 종목에서 MD&A 파싱 성공률 측정
- 실패 케이스 패턴 분석

가설:
1. 대부분 종목에서 MD&A 섹션 존재 및 파싱 가능

방법:
1. 전체 parquet 파일 대상 MD&A 추출
2. 성공/없음/실패 분류

결과:

결론:

실험일: 2026-03-07
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "docsData"


KOREAN_NUMS = {
    "가": 1, "나": 2, "다": 3, "라": 4, "마": 5,
    "바": 6, "사": 7, "아": 8, "자": 9, "차": 10,
}


def _isSectionHeader(line: str) -> tuple[int, str] | None:
    s = line.strip()

    m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
    if m:
        num = int(m.group(1))
        title = m.group(2).strip()
        if num <= 20 and len(title) >= 2:
            return (num, title)

    m = re.match(r"^([가-차])\.\s+(.+)", s)
    if m:
        char = m.group(1)
        title = m.group(2).strip()
        if char in KOREAN_NUMS and len(title) >= 2:
            return (KOREAN_NUMS[char], title)

    return None


def parseMdna(content: str) -> dict:
    lines = content.split("\n")
    sections = {}
    currentKey = None
    currentLines = []

    for line in lines:
        s = line.strip()

        if s.startswith("IV.") or s.startswith("V."):
            continue

        header = _isSectionHeader(s)
        if header:
            num, title = header
            if currentKey and currentLines:
                sections[currentKey] = "\n".join(currentLines)
            currentKey = f"{num}. {title}"
            currentLines = []
            continue

        if currentKey is not None:
            currentLines.append(line)

    if currentKey and currentLines:
        sections[currentKey] = "\n".join(currentLines)

    return sections


def main():
    print("=" * 100)
    print("MD&A 전체 종목 테스트")
    print("=" * 100)

    files = sorted(DATA_DIR.glob("*.parquet"))
    print(f"전체 종목: {len(files)}개")

    okCount = 0
    noSection = 0
    failCount = 0
    failList = []

    for path in files:
        code = path.stem
        df = pl.read_parquet(str(path))
        corpName = (
            df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        )
        years = sorted(df["year"].unique().to_list(), reverse=True)

        found = False
        for year in years[:3]:
            rows = df.filter(
                (pl.col("year") == year)
                & pl.col("section_title").str.contains("경영진단")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                continue

            content = rows["section_content"][0]
            sections = parseMdna(content)

            if sections:
                found = True
                okCount += 1
                break

        if not found:
            hasSection = False
            for year in years[:3]:
                rows = df.filter(
                    (pl.col("year") == year)
                    & pl.col("section_title").str.contains("경영진단")
                    & pl.col("report_type").str.contains("사업보고서")
                    & ~pl.col("report_type").str.contains("기재정정|첨부")
                )
                if rows.height > 0:
                    hasSection = True
                    content = rows["section_content"][0]
                    if "기재하지 않" in content or len(content.strip()) < 200:
                        noSection += 1
                    else:
                        failCount += 1
                        failList.append((code, corpName, "파싱실패"))
                    break

            if not hasSection:
                noSection += 1

    total = okCount + noSection + failCount
    print(f"\n성공: {okCount}/{total}")
    print(f"섹션 없음: {noSection}/{total}")
    print(f"파싱 실패: {failCount}/{total}")

    if failList:
        print(f"\n실패 목록:")
        for code, name, reason in failList:
            print(f"  [{code}] {name}: {reason}")

    successRate = okCount / (okCount + failCount) * 100 if (okCount + failCount) > 0 else 0
    print(f"\n성공률 (섹션 있는 종목 기준): {successRate:.1f}%")


if __name__ == "__main__":
    main()
