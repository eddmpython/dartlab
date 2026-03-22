"""사업의 내용 섹션 추출 실험.

케이스별 추출:
1. 하위 섹션이 분리된 경우 (160종목 표준 패턴)
2. II. 사업의 내용 통합 텍스트에서 번호 패턴으로 분리
3. 금융업/복합업종 접두사 처리
"""

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

import polars as pl

from dartlab.core import loadData

SECTION_KEYS = {
    "overview": ["사업의 개요"],
    "products": ["주요 제품"],
    "materials": ["원재료", "생산 및 설비"],
    "sales": ["매출", "수주"],
    "risk": ["위험관리", "파생거래"],
    "rnd": ["주요계약", "연구개발", "경영상"],
    "etc": ["기타 참고"],
    "financial": ["재무건전성"],
}


def classifySection(title: str) -> str | None:
    for key, keywords in SECTION_KEYS.items():
        for kw in keywords:
            if kw in title:
                return key
    return None


def extractSections(stockCode: str) -> dict:
    df = loadData(stockCode)
    annual = df.filter(df["report_type"].str.contains("사업보고서"))
    if annual.height == 0:
        return {}

    latestYear = annual["year"].unique().sort().to_list()[-1]
    latest = annual.filter(annual["year"] == latestYear)

    result = {"year": latestYear, "sections": {}}

    subSections = latest.filter(
        latest["section_title"].str.contains("사업의 개요")
        | latest["section_title"].str.contains("주요 제품")
        | latest["section_title"].str.contains("원재료")
        | latest["section_title"].str.contains("생산 및 설비")
        | latest["section_title"].str.contains("매출")
        | latest["section_title"].str.contains("수주")
        | latest["section_title"].str.contains("위험관리")
        | latest["section_title"].str.contains("기타 참고")
        | latest["section_title"].str.contains("연구개발")
        | latest["section_title"].str.contains("주요계약")
        | latest["section_title"].str.contains("경영상")
        | latest["section_title"].str.contains("재무건전성")
    )

    if subSections.height > 0:
        for row in subSections.iter_rows(named=True):
            title = row["section_title"]
            key = classifySection(title)
            if key:
                content = row["section_content"]
                if key not in result["sections"]:
                    result["sections"][key] = {"title": title, "chars": len(content), "preview": content[:200]}
                else:
                    existing = result["sections"][key]
                    existing["title"] += f" + {title}"
                    existing["chars"] += len(content)
    else:
        mainSection = latest.filter(latest["section_title"].str.contains("사업의 내용"))
        if mainSection.height > 0:
            fullText = mainSection.row(0, named=True)["section_content"]
            result["sections"]["_full"] = {"title": "II. 사업의 내용 (통합)", "chars": len(fullText)}

            chunks = splitByNumber(fullText)
            for num, title, text in chunks:
                key = classifySection(title)
                if key:
                    result["sections"][key] = {"title": f"{num}. {title}", "chars": len(text), "preview": text[:200]}

    return result


def splitByNumber(text: str) -> list[tuple[str, str, str]]:
    pattern = re.compile(r"^(\d+)\.\s+(.+?)$", re.MULTILINE)
    allMatches = list(pattern.finditer(text))

    topMatches = []
    expectedNum = 1
    for m in allMatches:
        num = int(m.group(1))
        if num == expectedNum:
            topMatches.append(m)
            expectedNum = num + 1
        elif num == 1 and expectedNum > 2:
            break

    chunks = []
    for i, m in enumerate(topMatches):
        num = m.group(1)
        title = m.group(2).strip()
        start = m.end()
        end = topMatches[i + 1].start() if i + 1 < len(topMatches) else len(text)
        body = text[start:end].strip()
        chunks.append((num, title, body))

    return chunks


testCodes = [
    ("005930", "삼성전자 (표준 하위섹션)"),
    ("005380", "현대자동차 (금융+제조 복합)"),
    ("001200", "유진증권 (금융업)"),
    ("000660", "SK하이닉스 (표준)"),
    ("035720", "카카오페이/카카오 (복합)"),
]

for code, desc in testCodes:
    print(f"\n{'=' * 60}")
    print(f"{code} {desc}")
    print("=" * 60)

    try:
        result = extractSections(code)
        print(f"기준연도: {result.get('year')}")
        for key, info in result.get("sections", {}).items():
            print(f"  [{key}] {info['title']} ({info['chars']:,}자)")
            if "preview" in info:
                preview = info["preview"].replace("\n", " ")[:100]
                print(f"    → {preview}...")
    except Exception as e:
        print(f"  ERROR: {e}")


print(f"\n{'=' * 60}")
print("통합 텍스트 번호 패턴 분리 테스트")
print("=" * 60)

df = loadData("005930")
annual = df.filter(df["report_type"].str.contains("사업보고서"))

for testYear in ["2015", "2018", "2020"]:
    ydf = annual.filter(annual["year"] == testYear)
    main = ydf.filter(ydf["section_title"].str.contains("사업의 내용"))
    if main.height == 0:
        continue

    text = main.row(0, named=True)["section_content"]
    chunks = splitByNumber(text)
    print(f"\n{testYear} ({len(text):,}자) → {len(chunks)}개 섹션:")
    for num, title, body in chunks:
        key = classifySection(title) or "?"
        print(f"  {num}. {title} [{key}] ({len(body):,}자)")
