"""관계기업/종속기업 투자 현황 파싱.

주석에서 관계기업 투자 현황(나) + 투자 내역(다) + 지분법평가(라) 추출.

핵심 발견: 2025 "XBRL" 포맷으로 보였던 것은 사실
첫 번째 행이 거대 플랫 텍스트이고, 나머지는 정상 마크다운 테이블.
→ 첫 번째 거대 행만 스킵하면 파싱 가능.
"""

import re
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")
OUT = Path("experiments/003_subsidiaries/output")
OUT.mkdir(exist_ok=True)


def extractNotes(df: pl.DataFrame, year: str) -> list[str]:
    """사업보고서 연결재무제표 주석."""
    filtered = df.filter(
        (pl.col("year") == year)
        & pl.col("report_type").str.contains("사업보고서")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
        & pl.col("section_title").str.contains("연결재무제표")
        & pl.col("section_title").str.contains("주석")
    )
    if filtered.height == 0:
        filtered = df.filter(
            (pl.col("year") == year)
            & pl.col("section_title").str.contains("연결재무제표")
            & pl.col("section_title").str.contains("주석")
        )
    return filtered["section_content"].to_list()


def findSection(contents: list[str], keyword: str) -> str | None:
    """번호 매긴 섹션에서 keyword가 포함된 섹션 텍스트."""
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


def parseTableRows(text: str) -> list[list[str]]:
    """텍스트에서 마크다운 테이블 행을 추출.

    XBRL 패딩(빈 셀 수백 개) 제거 후 의미 있는 셀만 반환.
    구분선도 스킵.
    """
    rows = []
    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        # 후행 빈 셀 제거 (XBRL 패딩)
        while cells and not cells[-1]:
            cells.pop()

        if not cells:
            continue
        # 구분선 스킵
        if all(re.match(r"^-+$", c) for c in cells if c):
            continue
        # 완전 빈 행 스킵
        if not any(c.strip() for c in cells):
            continue

        rows.append(cells)
    return rows


def parseAmount(text: str) -> float | None:
    """금액 문자열 → float."""
    s = text.strip().replace("\xa0", "").replace(" ", "")
    if not s or s == "-":
        return None
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    s = s.replace(",", "")
    # % 처리
    if s.endswith("%"):
        try:
            return float(s[:-1])
        except ValueError:
            return None
    try:
        val = float(s)
        return -val if negative else val
    except ValueError:
        return None


def extractAffiliateProfile(rows: list[list[str]]) -> list[dict]:
    """관계기업 투자 현황 테이블 추출.

    패턴: [기업명, 관계의 성격, 지분율(%), 주사업장, 결산월]
    """
    results = []
    headers = None

    for cells in rows:
        if not cells:
            continue

        # 헤더 감지
        if any("기업명" in c for c in cells) and any("지분율" in c or "성격" in c for c in cells):
            headers = cells
            continue

        # 데이터 행 — 헤더가 있고, 셀 수 일치하며, 숫자가 아닌 행
        if headers and len(cells) >= len(headers) - 1:
            firstCell = cells[0].strip()
            # 주석 행 스킵
            if firstCell.startswith("(") and "*" in firstCell:
                headers = None  # 주석 = 테이블 종료
                continue
            # 빈 첫 셀 스킵
            if not firstCell:
                continue
            # 숫자 행 스킵 (투자 내역 테이블의 시작)
            if parseAmount(cells[1]) is not None and "성격" not in (headers[1] if len(headers) > 1 else ""):
                continue

            entry = {}
            for i, h in enumerate(headers):
                if i < len(cells):
                    # 헤더 정규화
                    cleanH = re.sub(r"\(\*\d*\)", "", h).strip()
                    entry[cleanH] = cells[i].strip()
            if entry:
                results.append(entry)

    return results


def extractInvestmentDetails(rows: list[list[str]]) -> list[dict]:
    """관계기업 투자 내역 추출.

    패턴: [기업명, 취득원가, 순자산가액, 장부금액, 취득원가, 순자산가액, 장부금액]
    (당기말 3열 + 전기말 3열)
    """
    results = []
    inTable = False

    for cells in rows:
        if not cells:
            continue

        # 헤더 감지: "기 업 명" + "당기말" or "당분기말"
        cellStr = " ".join(cells)
        if ("기 업 명" in cellStr or "기업명" in cellStr) and ("당기말" in cellStr or "당분기말" in cellStr):
            inTable = True
            continue

        # 서브헤더 스킵: "취득원가", "순자산가액" 등
        if inTable and any("취득원가" in c for c in cells):
            continue

        if inTable:
            firstCell = cells[0].strip()
            # 주석/종료
            if firstCell.startswith("(") and "*" in firstCell:
                inTable = False
                continue
            if not firstCell or firstCell == "계":
                continue

            # 숫자가 있는 행
            amounts = [parseAmount(c) for c in cells[1:]]
            if any(a is not None for a in amounts):
                name = re.sub(r"\(\*\d*\)", "", firstCell).strip()
                entry = {"기업명": name}

                # 당기말: 취득원가, 순자산가액, 장부금액
                if len(amounts) >= 3:
                    entry["취득원가"] = amounts[0]
                    entry["순자산가액"] = amounts[1]
                    entry["장부금액_당기"] = amounts[2]
                # 전기말: 취득원가, 순자산가액, 장부금액
                if len(amounts) >= 6:
                    entry["장부금액_전기"] = amounts[5]

                results.append(entry)

    return results


def extractEquityMethod(rows: list[list[str]]) -> list[dict]:
    """지분법평가 내역 추출.

    패턴: [기업명, 기초, 지분법손익, 지분법자본변동, 기타증감액, 기말]
    """
    results = []
    inTable = False

    for cells in rows:
        if not cells:
            continue

        cellStr = " ".join(cells)
        # 헤더: "기 업 명" + "기초" + "지분법"
        if ("기 업 명" in cellStr or "기업명" in cellStr) and "기초" in cellStr and "지분법" in cellStr:
            inTable = True
            continue

        # 서브헤더 스킵
        if inTable and any("지분법손익" in c for c in cells):
            continue

        if inTable:
            firstCell = cells[0].strip()
            if firstCell.startswith("(") and "*" in firstCell:
                inTable = False
                continue
            if not firstCell or firstCell == "계":
                continue

            amounts = [parseAmount(c) for c in cells[1:]]
            if any(a is not None for a in amounts):
                name = re.sub(r"\(\*\d*\)", "", firstCell).strip()
                entry = {"기업명": name}
                if len(amounts) >= 1:
                    entry["기초"] = amounts[0]
                if len(amounts) >= 2:
                    entry["지분법손익"] = amounts[1]
                if len(amounts) >= 3:
                    entry["지분법자본변동"] = amounts[2]
                if len(amounts) >= 4:
                    entry["기타증감액"] = amounts[3]
                if len(amounts) >= 5:
                    entry["기말"] = amounts[4]
                results.append(entry)

    return results


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


def main():
    out = []

    def p(s=""):
        out.append(s)

    p("=" * 80)
    p("관계기업 투자 현황 파싱 (거대 행 스킵 전략)")
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

        for year in years[:3]:
            contents = extractNotes(df, year)
            if not contents:
                continue

            section = findSection(contents, "관계기업")
            if section is None:
                section = findSection(contents, "지분법")
            if section is None:
                p(f"\n  {year}: 관계기업 섹션 없음")
                summary.append((name, year, 0, 0, 0))
                continue

            rows = parseTableRows(section)
            p(f"\n  {year}: 테이블행 {len(rows)}개 (거대행 제외)")

            # 투자 현황
            profiles = extractAffiliateProfile(rows)
            p(f"    투자현황: {len(profiles)}개")
            for pr in profiles[:5]:
                pName = pr.get("기업명", "?")
                share = pr.get("지분율", pr.get("지분율(%)", "?"))
                p(f"      {pName} ({share}%)")

            # 투자 내역
            details = extractInvestmentDetails(rows)
            p(f"    투자내역: {len(details)}개")
            for d in details[:5]:
                dName = d.get("기업명", "?")
                bv = d.get("장부금액_당기")
                bvStr = f"{bv:,.0f}" if bv else "?"
                p(f"      {dName}: 장부금액={bvStr}")

            # 지분법평가
            equity = extractEquityMethod(rows)
            p(f"    지분법평가: {len(equity)}개")
            for e in equity[:5]:
                eName = e.get("기업명", "?")
                pnl = e.get("지분법손익")
                pnlStr = f"{pnl:,.0f}" if pnl else "?"
                p(f"      {eName}: 지분법손익={pnlStr}")

            summary.append((name, year, len(profiles), len(details), len(equity)))

    # 요약
    p(f"\n\n{'=' * 80}")
    p("요약")
    p("=" * 80)
    p(f"{'기업':<12} {'년도':>5} {'현황':>5} {'내역':>5} {'지분법':>6}")
    p("-" * 40)
    for name, year, pCnt, dCnt, eCnt in summary:
        p(f"{name:<12} {year:>5} {pCnt:>5} {dCnt:>5} {eCnt:>6}")

    outPath = OUT / "affiliate_parse.txt"
    outPath.write_text("\n".join(out), encoding="utf-8")
    print(f"결과 저장: {outPath}")
    print(f"총 {len(out)}줄")

    # 요약만 콘솔 출력
    for line in out[-len(summary) - 4:]:
        print(line)


if __name__ == "__main__":
    main()
