"""다수 기업 관계기업/종속기업 구조 탐색.

주요 질문:
1. "일반적 사항" 종속기업 목록이 모든 기업에 존재하는가?
2. 관계기업 투자 현황 테이블 구조가 기업마다 다른가?
3. 어떤 데이터를 추출하면 가장 활용도가 높은가?
"""

import re
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")
OUT = Path("experiments/003_subsidiaries/output")
OUT.mkdir(exist_ok=True)

COMPANIES = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("005380", "현대차"),
    ("066570", "LG전자"),
    ("035420", "네이버"),
    ("035720", "카카오"),
    ("005490", "POSCO홀딩스"),
    ("006400", "삼성SDI"),
    ("373220", "LG에너지솔루션"),
]


def extractNotes(df: pl.DataFrame, year: str) -> list[str]:
    """사업보고서 연결재무제표 주석."""
    # report_type에서 사업보고서 우선
    filtered = df.filter(
        (pl.col("year") == year)
        & pl.col("section_title").str.contains("연결재무제표")
        & pl.col("section_title").str.contains("주석")
    )
    if filtered.height == 0:
        return []
    # 사업보고서 우선, 없으면 전체
    annual = filtered.filter(pl.col("report_type").str.contains("사업보고서"))
    if annual.height > 0:
        return annual["section_content"].to_list()
    return filtered["section_content"].to_list()


def findSection(contents: list[str], keyword: str) -> str | None:
    for content in contents:
        lines = content.split("\n")
        startIdx = None
        endIdx = None
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|"):
                continue
            m = re.match(r"^(\d{1,2})\.\s+(.+)", s)
            if m:
                title = m.group(2).strip()
                if keyword in title:
                    startIdx = i
                elif startIdx is not None and endIdx is None:
                    endIdx = i
                    break
        if startIdx is not None:
            if endIdx is None:
                endIdx = len(lines)
            return "\n".join(lines[startIdx:endIdx])
    return None


def analyzeFormat(text: str) -> str:
    """포맷 유형 분류: 'clean' (정상 마크다운) / 'flat' (단일셀 플랫) / 'xbrl' (초폭)."""
    lines = text.split("\n")
    tableLines = [l for l in lines if l.strip().startswith("|")]
    if not tableLines:
        return "no_table"

    cellCounts = []
    for l in tableLines:
        cells = [c.strip() for c in l.split("|") if c.strip()]
        cellCounts.append(len(cells))

    maxCells = max(cellCounts)
    singleRate = sum(1 for c in cellCounts if c <= 1) / len(cellCounts)

    if maxCells > 10:
        return "xbrl"
    if singleRate > 0.5:
        return "flat"
    return "clean"


def extractCleanTable(text: str, headerKeyword: str) -> list[dict]:
    """정상 마크다운 테이블에서 데이터 추출."""
    lines = text.split("\n")
    results = []
    headers = []
    inTable = False

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if inTable and results:
                inTable = False
            continue

        cells = [c.strip() for c in s.split("|")]
        cells = [c for c in cells if c != ""]

        if all(re.match(r"^-+$", c) for c in cells if c):
            continue

        if len(cells) <= 1:
            continue

        if any(headerKeyword in c for c in cells) and not any(c.replace(",", "").replace("(", "").replace(")", "").replace("-", "").replace(".", "").isdigit() for c in cells[1:] if c.strip()):
            headers = cells
            inTable = True
            results = []  # 새 테이블 시작 시 초기화
            continue

        if inTable and headers and len(cells) >= len(headers) - 1:
            entry = {}
            for i, h in enumerate(headers):
                if i < len(cells):
                    entry[h] = cells[i]
            # 숫자 데이터가 아닌 행만 (종속기업 목록 = 텍스트)
            if entry.get(headerKeyword, "").strip() and not entry.get(headerKeyword, "").replace(",", "").replace(".", "").isdigit():
                results.append(entry)

    return results


def main():
    out = []

    def p(s=""):
        out.append(s)

    p("=" * 80)
    p("다수 기업 관계기업/종속기업 탐색")
    p("=" * 80)

    summary = []

    for code, name in COMPANIES:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            continue

        df = pl.read_parquet(str(path))
        years = sorted(df["year"].unique().to_list(), reverse=True)

        p(f"\n{'=' * 60}")
        p(f"  {name} ({code})")
        p(f"{'=' * 60}")

        for year in years[:3]:  # 최근 3년
            contents = extractNotes(df, year)
            if not contents:
                continue

            p(f"\n  {year}:")

            # 일반적 사항
            general = findSection(contents, "일반적 사항")
            generalFmt = "-"
            subCount = 0
            if general:
                generalFmt = analyzeFormat(general)
                p(f"    일반적 사항: {generalFmt} ({len(general.split(chr(10)))}줄)")

                if generalFmt == "clean":
                    subs = extractCleanTable(general, "기업명")
                    if not subs:
                        subs = extractCleanTable(general, "회사명")
                    if not subs:
                        subs = extractCleanTable(general, "종속기업명")
                    subCount = len(subs)
                    if subs:
                        p(f"      종속기업 {len(subs)}개")
                        for s in subs[:3]:
                            # 기업명만 추출
                            entryName = s.get("기업명", s.get("회사명", s.get("종속기업명", "?")))
                            share = ""
                            for k, v in s.items():
                                if "지분" in k:
                                    share = v
                            p(f"        {entryName} ({share})")
                        if len(subs) > 3:
                            p(f"        ... ({len(subs) - 3}개 더)")

            # 관계기업 투자
            affiliate = findSection(contents, "관계기업")
            if not affiliate:
                affiliate = findSection(contents, "지분법")
            affFmt = "-"
            affCount = 0
            if affiliate:
                affFmt = analyzeFormat(affiliate)
                p(f"    관계기업: {affFmt} ({len(affiliate.split(chr(10)))}줄)")

                if affFmt == "clean":
                    affs = extractCleanTable(affiliate, "기업명")
                    affCount = len(affs)
                    if affs:
                        p(f"      관계기업 {len(affs)}개:")
                        for a in affs[:5]:
                            aName = a.get("기업명", "?")
                            share = ""
                            for k, v in a.items():
                                if "지분" in k:
                                    share = v
                            p(f"        {aName} ({share})")
                        if len(affs) > 5:
                            p(f"        ... ({len(affs) - 5}개 더)")

            summary.append((name, year, generalFmt, subCount, affFmt, affCount))

    # 요약
    p(f"\n\n{'=' * 80}")
    p("요약")
    p("=" * 80)
    p(f"{'기업':<12} {'년도':>5} {'일반(포맷)':>10} {'종속기업':>8} {'관계(포맷)':>10} {'관계기업':>8}")
    p("-" * 60)
    for name, year, gFmt, sCnt, aFmt, aCnt in summary:
        p(f"{name:<12} {year:>5} {gFmt:>10} {sCnt:>8} {aFmt:>10} {aCnt:>8}")

    outPath = OUT / "multi_company.txt"
    outPath.write_text("\n".join(out), encoding="utf-8")
    print(f"결과 저장: {outPath}")
    print(f"총 {len(out)}줄")


if __name__ == "__main__":
    main()
