"""
실험 ID: 003
실험명: MD&A 파서 개발 + 10종목 검증

목적:
- MD&A 섹션에서 서브섹션별 텍스트 추출
- 개요/재무상태/유동성 등 핵심 섹션 분리

가설:
1. 번호 체계 (1. 2. 3. ...) 기반으로 섹션 분리 가능
2. 개요 섹션은 경영 전반 서술, 재무상태는 테이블 포함

방법:
1. 번호 패턴으로 섹션 경계 탐지 (1~2자리만, 연도 오탐 방지)
2. 각 섹션의 텍스트/테이블 분리
3. 10종목 검증

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

STOCKS = [
    "005930", "000660", "035420", "005380", "055550",
    "003550", "034020", "006400", "001200", "000720",
]


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


SECTION_ALIASES = {
    "overview": ["개요", "영업상황"],
    "forecast": ["예측정보"],
    "financials": ["재무상태", "영업실적"],
    "liquidity": ["유동성", "자금조달"],
    "offBalance": ["부외거래", "부외 거래"],
    "other": ["그 밖에", "그 밖의", "투자의사결정", "투자결정"],
    "accounting": ["회계정책", "회계추정"],
    "regulation": ["법규상", "규제"],
    "derivative": ["파생상품", "위험관리"],
    "strategy": ["추진 전략", "사업전망"],
}


def classifySection(title: str) -> str:
    for key, keywords in SECTION_ALIASES.items():
        for kw in keywords:
            if kw in title:
                return key
    return "unknown"


def extractOverview(sections: dict) -> str | None:
    for key, content in sections.items():
        if classifySection(key) == "overview":
            textLines = [l for l in content.split("\n") if l.strip() and not l.strip().startswith("|")]
            return "\n".join(textLines).strip() or None
    return None


def main():
    print("=" * 100)
    print("MD&A 파서 10종목 검증")
    print("=" * 100)

    okCount = 0
    noData = 0

    for code in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            continue

        df = pl.read_parquet(str(path))
        corpName = (
            df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        )
        years = sorted(df["year"].unique().to_list(), reverse=True)

        found = False
        for year in years[:2]:
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
                overview = extractOverview(sections)

                print(f"\n[{code}] {corpName} ({year}): {len(sections)}개 섹션")
                for key in sections:
                    cls = classifySection(key)
                    textLen = len([l for l in sections[key].split("\n") if l.strip() and not l.strip().startswith("|")])
                    tableLen = len([l for l in sections[key].split("\n") if l.strip().startswith("|")])
                    print(f"  [{cls:12s}] {key[:60]} (텍스트 {textLen}줄, 테이블 {tableLen}줄)")

                if overview:
                    preview = overview[:200].replace("\n", " ")
                    print(f"  개요 미리보기: {preview}...")
                break

        if not found:
            noData += 1
            print(f"\n[{code}] {corpName}: MD&A 없음")

    print(f"\n{'=' * 100}")
    print(f"성공: {okCount}/{len(STOCKS)}, 없음: {noData}/{len(STOCKS)}")


if __name__ == "__main__":
    main()
