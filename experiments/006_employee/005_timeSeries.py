"""
실험 ID: 005
실험명: 직원 현황 시계열 구축 + 검증

목적:
- 여러 해 사업보고서에서 직원 현황 시계열 구축
- 연도별 직원수/급여 추이 정합성 검증

가설:
1. 삼성전자 10년 이상 시계열 구축 가능
2. 연도별 직원수 변동 합리적 범위 (±30%)

방법:
1. 대표 종목 전체 사업보고서에서 직원 데이터 추출
2. 연도별 시계열 구성
3. 급격한 변동 이상치 검출

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

STOCKS = ["005930", "000660", "035420", "005380", "000270", "003550"]


def parseAmount(text: str) -> float | None:
    if not text or text.strip() in ("", "-", "\u3000", "\u2015", "\u2013"):
        return None
    cleaned = text.strip()
    isNegative = "\u25b3" in cleaned or "(" in cleaned
    cleaned = cleaned.replace("\u25b3", "").replace(",", "").replace(" ", "")
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


def parseTenure(text: str) -> float | None:
    if not text or text.strip() in ("", "-"):
        return None
    s = text.strip()
    m = re.match(r"(\d+)\s*년\s*(\d+)\s*개월", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 12
    m = re.match(r"(\d+)\s*년", s)
    if m:
        return float(m.group(1))
    m = re.match(r"(\d+)\s*개월", s)
    if m:
        return int(m.group(1)) / 12
    val = parseAmount(s)
    if val is not None and 0 < val < 100:
        return val
    return None


def _tryExtract(cells, empIdx, tenureIdx, salaryIdx, avgIdx):
    if empIdx >= len(cells):
        return None
    emp = parseAmount(cells[empIdx])
    if emp is None or emp < 1:
        return None
    result = {"totalEmployees": emp}
    if tenureIdx < len(cells):
        tenure = parseTenure(cells[tenureIdx])
        if tenure is not None:
            result["avgTenure"] = round(tenure, 1)
    if salaryIdx < len(cells):
        salary = parseAmount(cells[salaryIdx])
        if salary is not None and salary >= emp:
            result["totalSalary"] = salary
    if avgIdx < len(cells):
        avg = parseAmount(cells[avgIdx])
        if avg is not None:
            result["avgSalary"] = avg
    return result


def parseEmployeeTable(content: str) -> dict:
    lines = content.split("\n")

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        isTotal = cells[0] in ("합 계", "합계")
        if not isTotal:
            continue
        if len(cells) < 4:
            continue

        if len(cells) >= 10:
            r = _tryExtract(cells, 6, 7, 8, 9)
            if r and r.get("totalSalary"):
                return r

        if len(cells) >= 9:
            r = _tryExtract(cells, 5, 6, 7, 8)
            if r and r.get("totalSalary"):
                return r

        if len(cells) >= 10:
            r = _tryExtract(cells, 2, 7, 8, 9)
            if r and r.get("totalSalary"):
                return r

        if len(cells) >= 10:
            r = _tryExtract(cells, 6, 7, 8, 9)
            if r:
                return r

        if len(cells) >= 3:
            r = _tryExtract(
                cells,
                2,
                7 if len(cells) > 7 else 99,
                8 if len(cells) > 8 else 99,
                9 if len(cells) > 9 else 99,
            )
            if r:
                return r

    return {}


def extractReportYear(reportType: str) -> int | None:
    m = re.search(r"\((\d{4})\.\d{2}\)", reportType)
    if m:
        return int(m.group(1))
    return None


def buildTimeSeries(df: pl.DataFrame) -> list[dict]:
    years = sorted(df["year"].unique().to_list(), reverse=True)
    yearData = {}

    for year in years:
        rows = df.filter(
            (pl.col("year") == year)
            & (
                pl.col("section_title").str.contains("직원")
                | pl.col("section_title").str.contains("임원")
            )
            & pl.col("report_type").str.contains("사업보고서")
            & ~pl.col("report_type").str.contains("기재정정|첨부")
        )
        if rows.height == 0:
            rows = df.filter(
                (pl.col("year") == year)
                & (
                    pl.col("section_title").str.contains("직원")
                    | pl.col("section_title").str.contains("임원")
                )
                & pl.col("report_type").str.contains("사업보고서")
            )
        if rows.height == 0:
            continue

        content = rows["section_content"][0]
        reportYear = extractReportYear(rows["report_type"][0])
        if reportYear is None:
            continue

        parsed = parseEmployeeTable(content)
        if parsed.get("totalEmployees") is None:
            continue

        if reportYear not in yearData:
            yearData[reportYear] = parsed

    records = []
    for yr in sorted(yearData.keys()):
        d = yearData[yr]
        records.append(
            {
                "year": yr,
                "totalEmployees": d.get("totalEmployees"),
                "avgTenure": d.get("avgTenure"),
                "totalSalary": d.get("totalSalary"),
                "avgSalary": d.get("avgSalary"),
            }
        )
    return records


def main():
    print("=" * 100)
    print("직원 현황 시계열 구축 + 검증")
    print("=" * 100)

    for code in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            print(f"\n[{code}] 파일 없음")
            continue

        df = pl.read_parquet(str(path))
        corpName = (
            df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        )

        ts = buildTimeSeries(df)

        print(f"\n{'=' * 100}")
        print(f"[{code}] {corpName} ({len(ts)}년 시계열)")
        print(f"{'=' * 100}")

        if not ts:
            print("  데이터 없음")
            continue

        for row in ts:
            emp = row["totalEmployees"] or 0
            tenure = row.get("avgTenure", "N/A")
            avg = row.get("avgSalary", 0) or 0
            print(
                f"  {row['year']}: {emp:>8,.0f}명  근속 {tenure}년  1인평균 {avg:>8,.0f}"
            )

        # 이상치 검출: 전년대비 ±30% 이상 변동
        print(f"\n  --- 변동 분석 ---")
        anomalies = 0
        for i in range(1, len(ts)):
            prev = ts[i - 1]["totalEmployees"]
            curr = ts[i]["totalEmployees"]
            if prev and curr and prev > 0:
                change = (curr - prev) / prev * 100
                if abs(change) > 30:
                    print(
                        f"  ⚠ {ts[i-1]['year']}→{ts[i]['year']}: "
                        f"{prev:,.0f}→{curr:,.0f} ({change:+.1f}%)"
                    )
                    anomalies += 1
        if anomalies == 0:
            print(f"  변동 ±30% 이상: 없음 (안정적)")
        else:
            print(f"  변동 ±30% 이상: {anomalies}건")


if __name__ == "__main__":
    main()
