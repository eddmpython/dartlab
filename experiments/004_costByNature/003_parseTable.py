"""
실험 ID: 004-003
실험명: 비용의 성격별 분류 — 테이블 파싱

목적:
- "비용의 성격" 주석 영역에서 마크다운 테이블을 파싱하여 구조화된 데이터 추출
- 여러 종목에서 파싱 성공률 확인
- 기존 core.tableParser의 extractAccounts를 활용할 수 있는지 vs 별도 로직 필요한지 판단

가설:
1. segment 모듈과 동일한 패턴(번호 섹션 찾기 → 다음 번호까지 잘라내기)으로 영역 특정 가능
2. core.tableParser.extractAccounts로 파싱 가능 — 구조가 요약재무정보와 유사
3. 10개 종목 중 8개 이상에서 파싱 성공

방법:
1. 주석 섹션에서 "비용의 성격" 번호 섹션 추출 (segment extractor 패턴)
2. extractAccounts 적용 시도
3. 실패 시 직접 파싱 로직 구현
4. 10개 종목 × 최신 사업보고서 대상 테스트

결과 (실험 후 작성):

결론:

실험일: 2026-03-06
"""

import re
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dartlab.core.tableParser import extractAccounts, parseAmount
from dartlab.core.reportSelector import selectReport

DATA_DIR = Path("data/docsData")


def extractNotesContent(report: pl.DataFrame) -> list[str]:
    """보고서에서 주석 섹션 추출. 연결재무제표 주석 + 재무제표 주석 모두."""
    section = report.filter(
        pl.col("section_title").str.contains("주석")
    )
    if section.height == 0:
        return []
    return section["section_content"].to_list()


def findCostByNatureSection(contents: list[str]) -> str | None:
    """주석에서 '비용의 성격' 번호 섹션 추출.

    segment extractor와 동일 패턴:
    "N. 비용의 성격" 행 찾기 → 다음 번호 섹션까지 텍스트 반환.
    """
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
                if "비용의 성격" in title:
                    startIdx = i
                elif startIdx is not None and endIdx is None:
                    endIdx = i
                    break

        if startIdx is not None:
            if endIdx is None:
                endIdx = len(lines)
            return "\n".join(lines[startIdx:endIdx])
    return None


def parseCostByNature(sectionText: str) -> dict:
    """비용의 성격 섹션 텍스트에서 계정×금액 추출.

    Returns:
        {
            "accounts": {계정명: [당기, 전기, ...]},
            "order": [계정명 순서],
            "headers": [헤더],
            "unit": 단위,
        }
    """
    accounts, order = extractAccounts(sectionText)
    if accounts:
        return {"accounts": accounts, "order": order, "method": "extractAccounts"}

    return {"accounts": {}, "order": [], "method": "failed"}


if __name__ == "__main__":
    files = sorted(DATA_DIR.glob("*.parquet"))[:10]

    print(f"테스트 대상: {len(files)}개 종목")
    print("=" * 80)

    success = 0
    fail = 0

    for f in files:
        df = pl.read_parquet(str(f))
        corpName = df["corp_name"][0] if "corp_name" in df.columns else f.stem

        years = sorted(df["year"].unique().to_list(), reverse=True)
        latestYear = years[0] if years else None
        if not latestYear:
            continue

        report = selectReport(df, latestYear, reportKind="annual")
        if report is None:
            report = selectReport(df, years[1] if len(years) > 1 else latestYear, reportKind="annual")
        if report is None:
            print(f"\n{corpName}: 보고서 없음")
            fail += 1
            continue

        notes = extractNotesContent(report)
        if not notes:
            print(f"\n{corpName}: 주석 섹션 없음")
            fail += 1
            continue

        section = findCostByNatureSection(notes)
        if section is None:
            print(f"\n{corpName}: '비용의 성격' 섹션 없음")
            fail += 1
            continue

        result = parseCostByNature(section)

        if result["accounts"]:
            success += 1
            print(f"\n{corpName} ({f.stem}) — 파싱 성공 (method: {result['method']})")
            print(f"  계정 수: {len(result['order'])}개")
            for name in result["order"][:8]:
                vals = result["accounts"][name]
                vStr = ", ".join(
                    f"{v:,.0f}" if v is not None else "-" for v in vals[:2]
                )
                print(f"    {name}: [{vStr}]")
            if len(result["order"]) > 8:
                print(f"    ... +{len(result['order']) - 8}개")
        else:
            fail += 1
            print(f"\n{corpName} ({f.stem}) — 파싱 실패")
            print(f"  섹션 길이: {len(section)}자")
            print(f"  첫 500자:")
            print(section[:500])

    print()
    print("=" * 80)
    print(f"결과: 성공 {success}/{success + fail}, 실패 {fail}/{success + fail}")
    print(f"성공률: {success / (success + fail) * 100:.0f}%")
