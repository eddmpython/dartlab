"""
실험 ID: 003
실험명: 배당 데이터 파서 개발 + 10종목 테스트

목적:
- "주요 배당지표" 테이블에서 핵심 항목 추출하는 파서 개발
- 보통주/우선주 분리 처리
- 시계열 구성 (당기/전기/전전기 → 연도 매핑)

가설:
1. 단일 파서로 2010~2025 모든 포맷 처리 가능
2. 10개 종목 모두 핵심 지표 추출 성공

방법:
1. 테이블 행을 파싱하여 계정명-값 매핑
2. 보통주/우선주 분리 행 처리
3. 당기/전기/전전기를 연도로 변환
4. 10개 종목 × 최신 3년 검증

결과:

결론:

실험일: 2026-03-06
"""
import io
import re
import sys
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


def extractPeriodYears(rows: list[list[str]]) -> list[str]:
    """제N기 행에서 연도 추출. "제56기" → 실제 연도는 알 수 없으므로 상대값 반환."""
    for row in rows:
        periodNums = []
        for cell in row:
            m = re.search(r"제\s*(\d+)\s*기", cell)
            if m:
                periodNums.append(m.group(0).strip())
        if len(periodNums) >= 2:
            return periodNums
    return []


def parseDividendTable(content: str) -> dict:
    """배당 섹션에서 주요 배당지표 테이블 파싱."""
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

    if not tableRows:
        for line in lines:
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.split("|")]
            if cells and cells[0] == "":
                cells = cells[1:]
            if cells and cells[-1] == "":
                cells = cells[:-1]
            if not cells or all(c.replace("-", "") == "" for c in cells):
                continue
            cellText = " ".join(cells)
            if any(kw in cellText for kw in ["주당액면가액", "당기순이익", "현금배당", "배당성향", "배당수익률", "주당순이익"]):
                tableRows.append(cells)

    result = {
        "netIncome": [],
        "netIncomeStandalone": [],
        "eps": [],
        "totalDividend": [],
        "payoutRatio": [],
        "dividendYieldCommon": [],
        "dividendYieldPreferred": [],
        "dpsCommon": [],
        "dpsPreferred": [],
        "faceValue": [],
        "periods": [],
    }

    periodYears = extractPeriodYears(tableRows)
    if periodYears:
        result["periods"] = periodYears

    prevLabel = ""
    for row in tableRows:
        if len(row) < 3:
            continue

        label = row[0].strip()
        if not label:
            label = prevLabel

        values = row[1:] if len(row) >= 3 else []

        hasStockType = False
        stockType = ""
        if len(row) >= 4:
            secondCell = row[1].strip()
            if secondCell in ("보통주", "우선주", "종류주", "1우선주(주1)", "1우선주"):
                hasStockType = True
                stockType = "우선주" if "우선" in secondCell else ("종류주" if "종류" in secondCell else "보통주")
                values = row[2:]
            elif label in ("보통주", "우선주", "종류주", "1우선주(주1)", "1우선주"):
                hasStockType = True
                stockType = "우선주" if "우선" in label else ("종류주" if "종류" in label else "보통주")
                label = prevLabel
                values = row[1:]

        amounts = [parseAmount(v) for v in values[:3]]
        while len(amounts) < 3:
            amounts.append(None)

        if "당기순이익" in label and "연결" in label:
            result["netIncome"] = amounts
        elif "당기순이익" in label and ("별도" in label or "개별" in label):
            result["netIncomeStandalone"] = amounts
        elif "당기순이익" in label and not result["netIncome"]:
            result["netIncome"] = amounts
        elif "주당순이익" in label:
            result["eps"] = amounts
        elif "현금배당금총액" in label:
            result["totalDividend"] = amounts
        elif "현금배당성향" in label:
            result["payoutRatio"] = amounts
        elif "현금배당수익률" in label:
            if stockType == "우선주" or label == "우선주":
                result["dividendYieldPreferred"] = amounts
            elif stockType in ("종류주",) and all(a is None for a in amounts):
                pass
            else:
                result["dividendYieldCommon"] = amounts
        elif "주당" in label and "현금배당금" in label:
            if stockType == "우선주" or label == "우선주":
                result["dpsPreferred"] = amounts
            elif stockType in ("종류주",) and all(a is None for a in amounts):
                pass
            else:
                result["dpsCommon"] = amounts
        elif "주당액면가액" in label:
            result["faceValue"] = amounts

        if label and label not in ("보통주", "우선주", "종류주"):
            prevLabel = label

    return result


def getDividendSection(df: pl.DataFrame, year: str) -> str | None:
    rows = df.filter(
        (pl.col("year") == year)
        & pl.col("section_title").str.contains("배당")
        & pl.col("report_type").str.contains("사업보고서")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
    )
    if rows.height == 0:
        rows = df.filter(
            (pl.col("year") == year)
            & pl.col("section_title").str.contains("배당")
            & pl.col("report_type").str.contains("사업보고서")
        )
    if rows.height == 0:
        return None
    return rows["section_content"][0]


def main():
    print("=" * 100)
    print("배당 파서 10종목 테스트")
    print("=" * 100)

    totalTests = 0
    successTests = 0

    for code in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            print(f"\n[{code}] 파일 없음")
            continue

        df = pl.read_parquet(str(path))
        corpName = df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        years = sorted(df["year"].unique().to_list(), reverse=True)

        print(f"\n{'=' * 100}")
        print(f"[{code}] {corpName}")
        print(f"{'=' * 100}")

        for year in years[:5]:
            content = getDividendSection(df, year)
            if content is None:
                continue

            totalTests += 1
            parsed = parseDividendTable(content)

            hasDps = any(v is not None for v in parsed["dpsCommon"])
            hasYield = any(v is not None for v in parsed["dividendYieldCommon"])
            hasPayout = any(v is not None for v in parsed["payoutRatio"])
            hasIncome = any(v is not None for v in parsed["netIncome"])
            hasTotalDiv = any(v is not None for v in parsed["totalDividend"])

            isNoDividend = hasIncome and not hasDps and not hasYield and not hasTotalDiv
            status = "OK" if (hasDps or hasYield or isNoDividend) else "FAIL"
            if status == "OK":
                successTests += 1
            if isNoDividend:
                status = "OK (무배당)"

            print(f"\n  {year} [{status}]")
            if parsed["periods"]:
                print(f"    기수: {parsed['periods']}")
            if parsed["netIncome"]:
                print(f"    (연결)당기순이익: {parsed['netIncome']}")
            if parsed["eps"]:
                print(f"    주당순이익: {parsed['eps']}")
            if parsed["totalDividend"]:
                print(f"    현금배당금총액: {parsed['totalDividend']}")
            if parsed["payoutRatio"]:
                print(f"    배당성향: {parsed['payoutRatio']}")
            if parsed["dividendYieldCommon"]:
                print(f"    배당수익률(보통주): {parsed['dividendYieldCommon']}")
            if parsed["dividendYieldPreferred"]:
                print(f"    배당수익률(우선주): {parsed['dividendYieldPreferred']}")
            if parsed["dpsCommon"]:
                print(f"    DPS(보통주): {parsed['dpsCommon']}")
            if parsed["dpsPreferred"]:
                print(f"    DPS(우선주): {parsed['dpsPreferred']}")

    print(f"\n{'=' * 100}")
    print(f"결과: {successTests}/{totalTests} 성공 ({successTests/totalTests*100:.1f}%)")
    print(f"{'=' * 100}")


if __name__ == "__main__":
    main()
