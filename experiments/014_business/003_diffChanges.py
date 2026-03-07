"""사업의 내용 연도별 변경 탐지 실험.

difflib로:
- 변경률 (SequenceMatcher ratio)
- 추가/삭제 줄 수
- 변경 시점 자동 탐지 (★ 마커)
- diff 원문 출력 (추가/삭제된 줄)
"""

import sys
import difflib
sys.stdout.reconfigure(encoding="utf-8")

from dartlab.core import loadData
import polars as pl


def getBusinessText(df: pl.DataFrame, year: str) -> str | None:
    annual = df.filter(
        (df["year"] == year) & df["report_type"].str.contains("사업보고서")
    )
    if annual.height == 0:
        return None

    overview = annual.filter(annual["section_title"].str.starts_with("1.") & annual["section_title"].str.contains("사업의 개요"))
    if overview.height > 0:
        return overview.row(0, named=True)["section_content"]

    main = annual.filter(annual["section_title"].str.contains("사업의 내용"))
    if main.height > 0:
        return main.row(0, named=True)["section_content"]

    return None


def analyzeChanges(stockCode: str):
    df = loadData(stockCode)
    name = df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else stockCode

    annual = df.filter(df["report_type"].str.contains("사업보고서"))
    years = sorted(annual["year"].unique().to_list())

    print(f"\n{'=' * 70}")
    print(f"{stockCode} {name} — 사업의 내용 연도별 변경 분석")
    print("=" * 70)

    prevText = None
    changes = []

    for y in years:
        text = getBusinessText(df, y)
        if text is None:
            continue

        if prevText is not None:
            ratio = difflib.SequenceMatcher(None, prevText, text).ratio()
            changedPct = round((1 - ratio) * 100, 1)

            diffLines = list(difflib.unified_diff(
                prevText.splitlines(), text.splitlines(),
                lineterm="", n=0
            ))
            added = sum(1 for l in diffLines if l.startswith("+") and not l.startswith("+++"))
            removed = sum(1 for l in diffLines if l.startswith("-") and not l.startswith("---"))

            marker = " ★★★" if changedPct > 30 else " ★" if changedPct > 10 else ""
            print(f"{y}: 변경률 {changedPct}% (추가 {added}줄, 삭제 {removed}줄, 총 {len(text):,}자){marker}")

            changes.append({
                "year": y,
                "changedPct": changedPct,
                "added": added,
                "removed": removed,
                "totalChars": len(text),
            })
        else:
            print(f"{y}: 기준 ({len(text):,}자)")

        prevText = text

    if changes:
        bigChanges = [c for c in changes if c["changedPct"] > 30]
        print(f"\n큰 변화 시점 (>30%): {len(bigChanges)}건")
        for c in bigChanges:
            print(f"  {c['year']}: {c['changedPct']}% (+{c['added']}/-{c['removed']})")

    return changes


def showDiff(stockCode: str, year1: str, year2: str, maxLines: int = 30):
    df = loadData(stockCode)
    text1 = getBusinessText(df, year1)
    text2 = getBusinessText(df, year2)

    if not text1 or not text2:
        print(f"텍스트 없음: {year1}={bool(text1)}, {year2}={bool(text2)}")
        return

    print(f"\n{'=' * 70}")
    print(f"{stockCode} diff: {year1} → {year2}")
    print("=" * 70)

    diffLines = list(difflib.unified_diff(
        text1.splitlines(), text2.splitlines(),
        fromfile=year1, tofile=year2,
        lineterm="", n=1
    ))

    shown = 0
    for line in diffLines:
        if shown >= maxLines:
            print(f"  ... ({len(diffLines) - shown}줄 더)")
            break
        if line.startswith("+") and not line.startswith("+++"):
            print(f"  + {line[1:][:120]}")
            shown += 1
        elif line.startswith("-") and not line.startswith("---"):
            print(f"  - {line[1:][:120]}")
            shown += 1


testCodes = ["005930", "000660", "003490", "005380", "000020"]

for code in testCodes:
    analyzeChanges(code)


print(f"\n{'=' * 70}")
print("삼성전자 2021→2022 diff 샘플 (섹션 분리 시점)")
print("=" * 70)
showDiff("005930", "2021", "2022", maxLines=40)

print(f"\n{'=' * 70}")
print("삼성전자 2023→2024 diff 샘플 (안정기)")
print("=" * 70)
showDiff("005930", "2023", "2024", maxLines=20)
