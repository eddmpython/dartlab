"""유형자산 주석 섹션 추출 + 포맷 분류 실험."""

import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import detectUnit, extractTables, parseAmount

TARGETS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
    ("055550", "신한지주"),
    ("006400", "삼성SDI"),
    ("051910", "LG화학"),
    ("005380", "현대자동차"),
    ("000270", "기아"),
    ("035720", "카카오"),
    ("105560", "KB금융"),
    ("068270", "셀트리온"),
    ("028260", "삼성물산"),
    ("003550", "LG"),
    ("207940", "삼성바이오로직스"),
    ("012330", "현대모비스"),
    ("066570", "LG전자"),
    ("096770", "SK이노베이션"),
    ("034730", "SK"),
    ("316140", "우리금융지주"),
    ("003490", "대한항공"),
]


def extractTangibleSection(stockCode: str):
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years[:2]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        notes = extractNotesContent(report)
        if not notes:
            continue

        section = findNumberedSection(notes, "유형자산")
        if section:
            return corpName, year, section

    return corpName, None, None


def classifyFormat(section: str) -> str:
    tables = extractTables(section)
    if not tables:
        return "NO_TABLE"

    allHeaders = []
    for t in tables:
        allHeaders.extend(t["headers"])

    headerText = " ".join(allHeaders)

    hasMovement = any(
        kw in headerText
        for kw in ["기초", "기말", "취득", "감가상각", "처분"]
    )
    hasGrossAccum = any(
        kw in headerText
        for kw in ["취득원가", "감가상각누계액"]
    )
    hasAssetCols = any(
        kw in headerText
        for kw in ["토지", "건물", "기계장치", "구축물", "차량운반구"]
    )
    hasGovSub = "정부보조금" in headerText
    hasROU = any(
        kw in section[:500]
        for kw in ["사용권자산", "리스"]
    )

    if hasMovement and hasAssetCols:
        return "MOVEMENT_FULL"
    if hasMovement and not hasAssetCols:
        return "MOVEMENT_SIMPLE"
    if hasGrossAccum:
        return "GROSS_ACCUM"
    return "OTHER"


def analyzeSection(section: str):
    tables = extractTables(section)
    unit = detectUnit(section)
    lines = section.split("\n")
    nonTableLines = [l for l in lines if not l.strip().startswith("|") and l.strip()]

    info = {
        "length": len(section),
        "tableCount": len(tables),
        "unit": unit,
        "format": classifyFormat(section),
        "nonTableLines": len(nonTableLines),
    }

    for idx, t in enumerate(tables[:5]):
        info[f"table{idx}_headers"] = t["headers"]
        info[f"table{idx}_rows"] = len(t["rows"])
        if t["rows"]:
            info[f"table{idx}_firstRow"] = t["rows"][0]

    return info


if __name__ == "__main__":
    print("=" * 80)
    print("유형자산 주석 섹션 추출 + 포맷 분류")
    print("=" * 80)

    formatCount = {}

    for code, name in TARGETS:
        print(f"\n{'─' * 60}")
        corpName, year, section = extractTangibleSection(code)
        print(f"[{code}] {corpName}")

        if section is None:
            print("  → 유형자산 주석 없음")
            continue

        print(f"  → {year}년 보고서, 섹션 길이: {len(section):,}자")

        info = analyzeSection(section)
        fmt = info["format"]
        formatCount[fmt] = formatCount.get(fmt, 0) + 1

        print(f"  → 포맷: {fmt}")
        print(f"  → 테이블 {info['tableCount']}개, 단위: {info['unit']}")

        for idx in range(min(3, info["tableCount"])):
            hKey = f"table{idx}_headers"
            rKey = f"table{idx}_rows"
            fKey = f"table{idx}_firstRow"
            if hKey in info:
                print(f"  → T{idx} headers: {info[hKey]}")
                print(f"     rows: {info[rKey]}")
                if fKey in info:
                    print(f"     first: {info[fKey][:5]}...")

    print(f"\n{'=' * 80}")
    print("포맷 분포")
    for fmt, cnt in sorted(formatCount.items(), key=lambda x: -x[1]):
        print(f"  {fmt}: {cnt}개")
    print(f"  합계: {sum(formatCount.values())}개")
