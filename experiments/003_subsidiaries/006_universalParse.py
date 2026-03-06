"""관계기업/종속기업 범용 파서.

기업마다 테이블 헤더가 다른 문제를 해결.
전략: 각 행의 의미를 키워드로 분류 → 테이블 경계 자동 감지 → 범용 추출.

추출 대상:
1. 투자현황 — 회사명, 지분율, 장부금액, 소재지, 주요영업활동
2. 변동내역 — 기초, 취득, 처분, 지분법손익, 배당, 기말
3. 요약재무 — 유동/비유동자산, 유동/비유동부채, 매출, 당기순손익
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
    """번호 매긴 섹션에서 keyword 포함 섹션 텍스트."""
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
    """마크다운 테이블 행 추출. XBRL 패딩 제거."""
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
    if not s or s == "-" or s == "−":
        return None
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    if s.startswith("△"):
        negative = True
        s = s[1:]
    s = s.replace(",", "")
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


# ── 테이블 분류 키워드 ──

# 투자현황 헤더 키워드: 회사명/기업명 + 지분율 + (장부금액 or 소재지)
PROFILE_HEADER_KEYWORDS = ["회사명", "기업명", "기 업 명", "종 목"]
PROFILE_DETAIL_KEYWORDS = ["지분율", "소유지분율", "장부금액", "소재지", "소재국가",
                           "주요영업활동", "주요 영업활동", "관계의 성격",
                           "결산월", "주사업장"]

# 변동내역 헤더 키워드
MOVEMENT_KEYWORDS = ["기초", "기 초", "취득", "취 득", "처분", "지분법손익", "지분법이익",
                     "배당", "배 당", "기말", "기 말", "원금회수", "손상차손", "대 체"]

# 요약재무 키워드
SUMMARY_FIN_KEYWORDS = ["유동자산", "비유동자산", "유동부채", "비유동부채",
                        "매출", "매출액", "당기순손익", "계속영업손익",
                        "총포괄손익", "순자산"]


def classifyRow(cells: list[str], prevClassification: str | None = None) -> str:
    """행의 유형 분류: profile_header, profile_data, movement_header,
    movement_data, summary_header, summary_data, meta, unknown"""
    if not cells:
        return "unknown"

    cellStr = " ".join(cells)

    # 단위 표시
    if "단위" in cellStr and ("백만원" in cellStr or "천원" in cellStr or "원)" in cellStr):
        return "meta_unit"

    # 투자현황 헤더 감지
    if any(kw in cellStr for kw in PROFILE_HEADER_KEYWORDS):
        if any(kw in cellStr for kw in PROFILE_DETAIL_KEYWORDS):
            return "profile_header"

    # 변동내역 헤더 감지 (기초 + 기말 or 지분법 키워드 동시)
    movementCount = sum(1 for kw in MOVEMENT_KEYWORDS if kw in cellStr)
    if movementCount >= 3:
        return "movement_header"

    # 요약재무 키워드
    summaryCount = sum(1 for kw in SUMMARY_FIN_KEYWORDS if kw in cellStr)
    if summaryCount >= 2:
        return "summary_data"
    if summaryCount == 1 and len(cells) >= 2:
        # 요약재무 데이터행 (유동자산 | 123,456 | ...)
        if any(kw in cells[0] for kw in SUMMARY_FIN_KEYWORDS):
            return "summary_data"

    return "unknown"


def extractProfiles(rows: list[list[str]]) -> list[dict]:
    """투자현황(프로필) 추출. 범용 헤더 매칭."""
    results = []
    headers = None
    headerIdx = None

    for i, cells in enumerate(rows):
        cellStr = " ".join(cells)

        # 헤더 감지: 회사명/기업명 + 지분율 관련 키워드
        if any(kw in cellStr for kw in PROFILE_HEADER_KEYWORDS):
            if any(kw in cellStr for kw in PROFILE_DETAIL_KEYWORDS):
                headers = cells
                headerIdx = i
                continue

        # 서브헤더 감지 (지분율|순자산|장부금액 행 — 헤더 바로 다음)
        if headers and i == headerIdx + 1:
            if any("지분율" in c or "장부금액" in c for c in cells):
                # 멀티행 헤더 → 병합
                mergedHeaders = []
                for j in range(max(len(headers), len(cells))):
                    h1 = headers[j].strip() if j < len(headers) else ""
                    h2 = cells[j].strip() if j < len(cells) else ""
                    if h1 and h2:
                        mergedHeaders.append(f"{h1}_{h2}")
                    else:
                        mergedHeaders.append(h1 or h2)
                headers = mergedHeaders
                headerIdx = i
                continue

        if headers is None:
            continue

        # 데이터행 판정
        if len(cells) < 2:
            # 주석행 or 종료
            if cells and cells[0].startswith("("):
                headers = None
            continue

        firstCell = cells[0].strip()
        # 합계/계 행 스킵
        if firstCell in ("계", "합 계", "합계", "소 계"):
            continue
        # 빈 첫 셀 스킵
        if not firstCell:
            continue
        # 주석행((*1) 등)
        if re.match(r"^\(\*?\d", firstCell):
            headers = None
            continue

        # 숫자만 있는 행이면 이 테이블이 아닌 다른 테이블일 수 있음
        # → 첫 셀이 순수 숫자면 스킵
        if parseAmount(firstCell) is not None and not any(c.isalpha() or c in "㈜()（）" for c in firstCell):
            continue

        entry = {}
        for j, h in enumerate(headers):
            if j < len(cells):
                cleanH = re.sub(r"\(\*?\d*\)", "", h).strip()
                if cleanH:
                    entry[cleanH] = cells[j].strip()
        if entry:
            # 최소한 이름 + 하나 이상의 데이터가 있어야 함
            nonEmpty = sum(1 for v in entry.values() if v and v != "-")
            if nonEmpty >= 2:
                results.append(entry)

    return results


def extractMovements(rows: list[list[str]]) -> list[dict]:
    """변동내역 추출. 범용 헤더 매칭."""
    results = []
    headers = None
    inTable = False

    for i, cells in enumerate(rows):
        cellStr = " ".join(cells)

        # 헤더 감지: 기초/기말 + 지분법 관련 키워드
        movementCount = sum(1 for kw in MOVEMENT_KEYWORDS if kw in cellStr)
        if movementCount >= 3 and len(cells) >= 3:
            headers = cells
            inTable = True
            continue

        # 서브헤더 (지분법손익|지분법자본변동 등)
        if inTable and headers and not results:
            subKwCount = sum(1 for kw in ["지분법손익", "지분법자본변동", "기타증감"] if kw in cellStr)
            if subKwCount >= 1 and len(cells) >= 2:
                # 병합 헤더
                if len(cells) <= len(headers):
                    continue  # 서브헤더 스킵
                headers = cells
                continue

        if not inTable:
            continue

        if len(cells) < 2:
            if cells and cells[0].startswith("("):
                inTable = False
                headers = None
            continue

        firstCell = cells[0].strip()
        if firstCell in ("계", "합 계", "합계", "소 계"):
            continue
        if not firstCell:
            continue
        if re.match(r"^\(\*?\d", firstCell):
            inTable = False
            headers = None
            continue

        # 숫자 데이터가 있어야 함
        amounts = [parseAmount(c) for c in cells[1:]]
        if not any(a is not None for a in amounts):
            continue

        name = re.sub(r"\(\*?\d*\)", "", firstCell).strip()
        entry = {"기업명": name}

        if headers:
            for j, h in enumerate(headers):
                if j < len(cells):
                    cleanH = re.sub(r"\(\*?\d*\)", "", h).strip()
                    cleanH = re.sub(r"[\s·ㆍ\u3000]", "", cleanH)
                    if cleanH and j > 0:
                        entry[cleanH] = parseAmount(cells[j])
        else:
            # 헤더 없이 순서 기반
            for j, a in enumerate(amounts):
                entry[f"col{j}"] = a

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
    p("관계기업 범용 파서 테스트")
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
                section = findSection(contents, "공동기업")
            if section is None:
                p(f"\n  {year}: 관계기업 섹션 없음")
                summary.append((name, year, 0, 0))
                continue

            rows = parseTableRows(section)
            p(f"\n  {year}: 테이블행 {len(rows)}개")

            # 투자현황
            profiles = extractProfiles(rows)
            p(f"    투자현황: {len(profiles)}개")
            for pr in profiles[:5]:
                # 이름 추출: 여러 가능한 키
                pName = "?"
                for key in ["기업명", "회사명", "회사명(주1)", "종 목", "기 업 명"]:
                    if key in pr:
                        pName = pr[key]
                        break
                if pName == "?":
                    # 첫 번째 비-숫자 값
                    for v in pr.values():
                        if v and not v.replace(",", "").replace(".", "").replace("%", "").replace("-", "").isdigit():
                            pName = v
                            break

                # 지분율 추출
                share = "?"
                for key in pr:
                    if "지분율" in key or "소유지분" in key:
                        share = pr[key]
                        break

                # 장부금액 추출
                bv = "?"
                for key in pr:
                    if "장부금액" in key:
                        bv = pr[key]
                        break

                p(f"      {pName} | 지분율={share} | 장부={bv}")

            # 변동내역
            movements = extractMovements(rows)
            p(f"    변동내역: {len(movements)}개")
            for mv in movements[:5]:
                mvName = mv.get("기업명", "?")
                # 기초/기말 금액
                start = None
                end = None
                for key, val in mv.items():
                    k = re.sub(r"[\s·ㆍ\u3000]", "", key)
                    if k in ("기초", "기초금액"):
                        start = val
                    if k in ("기말", "기말금액"):
                        end = val
                p(f"      {mvName}: 기초={start} → 기말={end}")

            summary.append((name, year, len(profiles), len(movements)))

    # 요약
    p(f"\n\n{'=' * 80}")
    p("요약")
    p("=" * 80)
    p(f"{'기업':<16} {'년도':>5} {'현황':>5} {'변동':>5}")
    p("-" * 40)
    for name, year, pCnt, mCnt in summary:
        p(f"{name:<16} {year:>5} {pCnt:>5} {mCnt:>5}")

    outPath = OUT / "universal_parse.txt"
    outPath.write_text("\n".join(out), encoding="utf-8")
    print(f"결과 저장: {outPath}")
    print(f"총 {len(out)}줄")

    # 요약만 콘솔
    for line in out[-len(summary) - 4:]:
        print(line)


if __name__ == "__main__":
    main()
