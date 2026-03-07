"""
실험 ID: 005
실험명: 배당 데이터 시계열 구성

목적:
- 여러 연도 사업보고서에서 배당지표를 추출하여 시계열 구성
- 당기/전기/전전기 → 실제 연도 매핑
- 중복 연도 데이터 일관성 검증

가설:
1. 제N기 연도 매핑으로 10년+ 시계열 구성 가능
2. 중복 구간 데이터 90% 이상 일치

방법:
1. 삼성전자 등 10종목 × 전체 사업보고서
2. 각 보고서에서 배당지표 파싱 + 연도 매핑
3. 보고서간 겹치는 연도 일치율 검증
4. 최종 시계열 DataFrame 구성

결과:

결론:

실험일: 2026-03-06
"""
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "docsData"

STOCKS = [
    "005930",
    "000660",
    "035420",
    "005380",
    "055550",
    "051910",
    "006400",
    "032830",
    "003550",
    "034020",
]


def parseAmount(text: str) -> float | None:
    if not text or text.strip() in ("", "-", "　", "―", "–"):
        return None
    cleaned = text.strip()
    isNegative = "△" in cleaned or "(" in cleaned
    cleaned = cleaned.replace("△", "").replace(",", "").replace(" ", "")
    cleaned = cleaned.replace("(", "").replace(")", "")
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned:
        return None
    if cleaned.count(".") > 1:
        return None
    cleaned = cleaned.strip(".")
    if not cleaned:
        return None
    val = float(cleaned)
    return -val if isNegative else val


def parseDividendTable(content: str) -> dict:
    lines = content.split("\n")
    tableRows = []
    inMainTable = False

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if not cells:
            continue
        if all(c.replace("-", "") == "" for c in cells):
            continue

        cellText = " ".join(cells)
        if "배당지표" in cellText or "단위" in cellText:
            inMainTable = True
            continue
        if "배당 이력" in cellText or "배당이력" in cellText:
            break
        if not inMainTable and "구" in cellText and "분" in cellText and "당기" in cellText:
            inMainTable = True
        if inMainTable or any(kw in cellText for kw in ["주당액면가액", "당기순이익", "현금배당금", "배당성향", "배당수익률"]):
            inMainTable = True
            tableRows.append(cells)

    result = {
        "netIncome": [],
        "eps": [],
        "totalDividend": [],
        "payoutRatio": [],
        "dividendYieldCommon": [],
        "dpsCommon": [],
        "dpsPreferred": [],
    }

    prevLabel = ""
    for row in tableRows:
        if len(row) < 3:
            continue

        label = row[0].strip()
        if not label:
            label = prevLabel

        stockType = ""
        values = row[1:]
        if len(row) >= 4:
            second = row[1].strip()
            if second in ("보통주", "우선주", "종류주", "1우선주(주1)", "1우선주"):
                stockType = "우선주" if "우선" in second else ("종류주" if "종류" in second else "보통주")
                values = row[2:]
            elif label in ("보통주", "우선주", "종류주", "1우선주(주1)", "1우선주"):
                stockType = "우선주" if "우선" in label else ("종류주" if "종류" in label else "보통주")
                label = prevLabel
                values = row[1:]

        amounts = [parseAmount(v) for v in values[:3]]
        while len(amounts) < 3:
            amounts.append(None)

        if "당기순이익" in label and "연결" in label:
            result["netIncome"] = amounts
        elif "당기순이익" in label and (not result["netIncome"] or all(a is None for a in result["netIncome"])):
            result["netIncome"] = amounts
        elif "주당순이익" in label:
            result["eps"] = amounts
        elif "현금배당금총액" in label:
            result["totalDividend"] = amounts
        elif "현금배당성향" in label:
            result["payoutRatio"] = amounts
        elif "현금배당수익률" in label:
            if stockType == "우선주" or label == "우선주":
                pass
            elif stockType == "종류주" and all(a is None for a in amounts):
                pass
            else:
                result["dividendYieldCommon"] = amounts
        elif "주당" in label and "현금배당금" in label:
            if stockType == "우선주" or label == "우선주":
                result["dpsPreferred"] = amounts
            elif stockType == "종류주" and all(a is None for a in amounts):
                pass
            else:
                result["dpsCommon"] = amounts

        if label and label not in ("보통주", "우선주", "종류주"):
            prevLabel = label

    return result


def extractReportYear(reportType: str) -> int | None:
    """사업보고서 (2024.12) → 2024"""
    m = re.search(r"\((\d{4})\.\d{2}\)", reportType)
    if m:
        return int(m.group(1))
    return None


def buildTimeSeries(df: pl.DataFrame) -> pl.DataFrame:
    """전체 사업보고서에서 배당 시계열 구성."""
    rows = df.filter(
        pl.col("section_title").str.contains("배당")
        & pl.col("report_type").str.contains("사업보고서")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
    ).sort("year", descending=True)

    if rows.height == 0:
        rows = df.filter(
            pl.col("section_title").str.contains("배당")
            & pl.col("report_type").str.contains("사업보고서")
        ).sort("year", descending=True)

    yearData: dict[int, dict] = {}

    for i in range(rows.height):
        reportType = rows["report_type"][i]
        content = rows["section_content"][i]
        reportYear = extractReportYear(reportType)
        if reportYear is None:
            continue

        parsed = parseDividendTable(content)
        # 당기 = reportYear, 전기 = reportYear-1, 전전기 = reportYear-2
        offsets = [0, -1, -2]

        for field in ["netIncome", "eps", "totalDividend", "payoutRatio", "dividendYieldCommon", "dpsCommon", "dpsPreferred"]:
            vals = parsed.get(field, [])
            for j, offset in enumerate(offsets):
                if j < len(vals) and vals[j] is not None:
                    yr = reportYear + offset
                    if yr not in yearData:
                        yearData[yr] = {}
                    # 최신 보고서 우선 (이미 있으면 덮어쓰지 않음)
                    if field not in yearData[yr]:
                        yearData[yr][field] = vals[j]

    if not yearData:
        return pl.DataFrame()

    records = []
    for yr in sorted(yearData.keys()):
        d = yearData[yr]
        records.append({
            "year": yr,
            "netIncome": d.get("netIncome"),
            "eps": d.get("eps"),
            "totalDividend": d.get("totalDividend"),
            "payoutRatio": d.get("payoutRatio"),
            "dividendYield": d.get("dividendYieldCommon"),
            "dps": d.get("dpsCommon"),
            "dpsPreferred": d.get("dpsPreferred"),
        })

    return pl.DataFrame(records)


def checkOverlap(df: pl.DataFrame) -> tuple[int, int]:
    """보고서간 중복 연도 데이터 일관성 검증."""
    rows = df.filter(
        pl.col("section_title").str.contains("배당")
        & pl.col("report_type").str.contains("사업보고서")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
    ).sort("year", descending=True)

    if rows.height == 0:
        rows = df.filter(
            pl.col("section_title").str.contains("배당")
            & pl.col("report_type").str.contains("사업보고서")
        ).sort("year", descending=True)

    allData: list[tuple[int, str, float]] = []
    for i in range(rows.height):
        reportType = rows["report_type"][i]
        content = rows["section_content"][i]
        reportYear = extractReportYear(reportType)
        if reportYear is None:
            continue

        parsed = parseDividendTable(content)
        for field in ["dpsCommon", "netIncome", "dividendYieldCommon"]:
            vals = parsed.get(field, [])
            for j, offset in enumerate([0, -1, -2]):
                if j < len(vals) and vals[j] is not None:
                    allData.append((reportYear + offset, field, vals[j]))

    # 같은 (year, field) 조합의 값들 비교
    from collections import defaultdict
    groups: dict[tuple, list] = defaultdict(list)
    for yr, field, val in allData:
        groups[(yr, field)].append(val)

    matchCount = 0
    mismatchCount = 0
    for key, vals in groups.items():
        if len(vals) <= 1:
            continue
        ref = vals[0]
        for v in vals[1:]:
            if abs(ref - v) < 0.01 * max(abs(ref), 1):
                matchCount += 1
            else:
                mismatchCount += 1

    return matchCount, mismatchCount


def main():
    print("=" * 100)
    print("배당 시계열 구성 실험")
    print("=" * 100)

    for code in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            print(f"\n[{code}] 파일 없음")
            continue

        df = pl.read_parquet(str(path))
        corpName = df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code

        print(f"\n{'=' * 100}")
        print(f"[{code}] {corpName}")
        print(f"{'=' * 100}")

        # 사업보고서 수
        bizReports = df.filter(
            pl.col("section_title").str.contains("배당")
            & pl.col("report_type").str.contains("사업보고서")
        )
        print(f"  사업보고서 배당 섹션: {bizReports.height}개")

        # 중복 검증
        matchCount, mismatchCount = checkOverlap(df)
        total = matchCount + mismatchCount
        if total > 0:
            rate = matchCount / total * 100
            print(f"  중복 구간 일치율: {matchCount}/{total} ({rate:.1f}%)")
            if mismatchCount > 0:
                print(f"    ⚠ 불일치 {mismatchCount}건")

        # 시계열 구성
        ts = buildTimeSeries(df)
        if ts.height == 0:
            print("  시계열 구성 실패")
            continue

        yearRange = f"{ts['year'].min()}~{ts['year'].max()}"
        print(f"  시계열 범위: {yearRange} ({ts.height}년)")

        # DPS 시계열 출력
        dpsCol = ts.select(["year", "dps"]).filter(pl.col("dps").is_not_null())
        if dpsCol.height > 0:
            print(f"  DPS 데이터: {dpsCol.height}년")
            for row in dpsCol.iter_rows():
                print(f"    {row[0]}: {row[1]:,.0f}원")

        # 배당수익률 시계열
        yieldCol = ts.select(["year", "dividendYield"]).filter(pl.col("dividendYield").is_not_null())
        if yieldCol.height > 0:
            print(f"  배당수익률 데이터: {yieldCol.height}년")
            for row in yieldCol.iter_rows():
                print(f"    {row[0]}: {row[1]:.2f}%")


if __name__ == "__main__":
    main()
