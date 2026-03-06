"""관계기업/종속기업 파싱 실험.

주요 목표:
1. "일반적 사항" → 종속기업 목록 추출
2. "관계기업 및 공동기업 투자" → 투자 현황 + 투자 내역 추출
3. 연도별 포맷 차이 파악

삼성전자 기준으로 사업보고서(연간)만 탐색.
"""

import re
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")
OUT = Path("experiments/003_subsidiaries/output")
OUT.mkdir(exist_ok=True)


def extractNotes(df: pl.DataFrame, year: str) -> list[str]:
    """해당 연도 사업보고서 연결재무제표 주석 content 목록."""
    # 사업보고서만 (분기 제외)
    filtered = df.filter(
        (pl.col("year") == year)
        & pl.col("report_type").str.contains("사업보고서")
        & pl.col("section_title").str.contains("연결재무제표")
        & pl.col("section_title").str.contains("주석")
    )
    if filtered.height == 0:
        # fallback: year만으로 시도
        filtered = df.filter(
            (pl.col("year") == year)
            & pl.col("section_title").str.contains("연결재무제표")
            & pl.col("section_title").str.contains("주석")
        )
    return filtered["section_content"].to_list()


def findSection(contents: list[str], keyword: str) -> str | None:
    """번호 매긴 섹션에서 keyword가 포함된 섹션 텍스트 추출."""
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


def analyzeTableFormat(text: str) -> dict:
    """텍스트 내 테이블 포맷 분석."""
    lines = text.split("\n")
    tableLines = [l for l in lines if l.strip().startswith("|")]
    nonTableLines = [l for l in lines if l.strip() and not l.strip().startswith("|")]

    # 테이블 행 중 셀 개수 분포
    cellCounts = []
    for l in tableLines:
        cells = [c.strip() for c in l.split("|") if c.strip()]
        cellCounts.append(len(cells))

    # 단일셀 테이블 비율 (XBRL 플랫 포맷 감지)
    singleCell = sum(1 for c in cellCounts if c == 1)
    singleCellRate = singleCell / len(cellCounts) if cellCounts else 0

    return {
        "totalLines": len(lines),
        "tableLines": len(tableLines),
        "nonTableLines": len(nonTableLines),
        "cellCountRange": (min(cellCounts), max(cellCounts)) if cellCounts else (0, 0),
        "singleCellRate": singleCellRate,
    }


def extractSubsidiaryList(text: str) -> list[dict]:
    """'일반적 사항'에서 종속기업 목록 추출 시도.

    마크다운 테이블 포맷:
    | 기업명 | 소재지 | 업종 | 결산월 | 지분율(%) |
    """
    lines = text.split("\n")
    results = []
    inTable = False
    headers = []

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if inTable and results:
                break
            inTable = False
            continue

        cells = [c.strip() for c in s.split("|")]
        cells = [c for c in cells if c != ""]

        # 구분선 스킵
        if all(re.match(r"^-+$", c) for c in cells if c):
            continue

        # 단일셀: 플랫 포맷 → 스킵
        if len(cells) <= 1:
            continue

        # 헤더 감지: "기업명" 또는 "종속기업명" 포함
        if any("기업명" in c or "회사명" in c for c in cells):
            headers = cells
            inTable = True
            continue

        if inTable and len(cells) >= 3:
            entry = {}
            for i, h in enumerate(headers):
                if i < len(cells):
                    entry[h] = cells[i]
            if entry:
                results.append(entry)

    return results


def extractAffiliateSummary(text: str) -> list[dict]:
    """'관계기업 및 공동기업 투자'에서 투자 현황 추출.

    마크다운 테이블:
    | 기업명 | 관계의 성격 | 지분율(%) | 주사업장 | 결산월 |
    """
    lines = text.split("\n")
    results = []
    inTable = False
    headers = []

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if inTable and results:
                # 다음 비테이블 영역 → 현재 테이블 종료
                inTable = False
            continue

        cells = [c.strip() for c in s.split("|")]
        cells = [c for c in cells if c != ""]

        if all(re.match(r"^-+$", c) for c in cells if c):
            continue

        if len(cells) <= 1:
            # 단일셀에 전체 데이터가 합쳐진 경우 (2025 포맷)
            content = cells[0] if cells else ""
            if "기업명" in content and "지분율" in content:
                # 플랫 포맷에서 관계기업 테이블 감지
                return _parseFlatAffiliateTable(content)
            continue

        # 헤더 감지
        if any("기업명" in c for c in cells) and any("지분율" in c or "성격" in c for c in cells):
            headers = cells
            inTable = True
            continue

        if inTable and headers and len(cells) >= 3:
            entry = {}
            for i, h in enumerate(headers):
                if i < len(cells):
                    entry[h] = cells[i]
            if entry:
                results.append(entry)

    return results


def _parseFlatAffiliateTable(text: str) -> list[dict]:
    """단일셀에 합쳐진 플랫 포맷에서 관계기업 데이터 추출.

    패턴: 기업명 + 관계의성격 + 지분율 + 주사업장 + 결산월 이 반복.
    """
    results = []
    # 기업명 패턴: ㈜, (주), (유) 등 법인 표시가 있는 이름
    parts = re.split(r"(?=[\w㈜]+(?:㈜|\(주\)|\(유\)))", text)
    # 간단한 추출은 어려움 → 빈 리스트 반환
    return results


def main():
    path = DATA_DIR / "005930.parquet"
    df = pl.read_parquet(str(path))
    years = sorted(df["year"].unique().to_list(), reverse=True)

    out = []

    def p(s=""):
        out.append(s)

    p("=" * 80)
    p("삼성전자 관계기업/종속기업 파싱 실험")
    p("=" * 80)

    for year in years[:5]:
        contents = extractNotes(df, year)
        if not contents:
            continue

        p(f"\n{'=' * 60}")
        p(f"  {year}")
        p(f"{'=' * 60}")

        # 1. 일반적 사항 — 종속기업 목록
        general = findSection(contents, "일반적 사항")
        if general:
            fmt = analyzeTableFormat(general)
            p(f"\n  [일반적 사항]")
            p(f"    포맷: {fmt}")

            subs = extractSubsidiaryList(general)
            if subs:
                p(f"    종속기업 {len(subs)}개:")
                for s in subs[:5]:
                    p(f"      {s}")
                if len(subs) > 5:
                    p(f"      ... ({len(subs) - 5}개 더)")
            else:
                p(f"    종속기업 추출 실패 (포맷 확인 필요)")
                # 첫 500자 프리뷰
                preview = general[:500]
                for line in preview.split("\n")[:15]:
                    p(f"      {line}")

        # 2. 관계기업 및 공동기업 투자
        affiliate = findSection(contents, "관계기업")
        if affiliate:
            fmt = analyzeTableFormat(affiliate)
            p(f"\n  [관계기업 및 공동기업 투자]")
            p(f"    포맷: {fmt}")

            affiliates = extractAffiliateSummary(affiliate)
            if affiliates:
                p(f"    관계기업 {len(affiliates)}개:")
                for a in affiliates:
                    p(f"      {a}")
            else:
                p(f"    관계기업 추출 실패 (포맷 확인 필요)")
                # 첫 500자
                preview = affiliate[:500]
                for line in preview.split("\n")[:15]:
                    p(f"      {line}")

    outPath = OUT / "parse_explore_samsung.txt"
    outPath.write_text("\n".join(out), encoding="utf-8")
    print(f"결과 저장: {outPath}")
    print(f"총 {len(out)}줄")


if __name__ == "__main__":
    main()
