"""
실험 ID: 045-003
실험명: Report 시계열 피벗 — dividend, employee, majorHolder

목적:
- report 데이터에서 시계열 형태로 피벗하는 로직 검증
- dividend: 연도별 DPS/배당수익률/배당성향 시계열
- employee: 연도별 총직원수, 평균연봉 시계열
- majorHolder: 연도별 최대주주 지분율 시계열
- 빈 행(미래 분기) 제거 로직 확인

가설:
1. year+quarter 기준으로 시계열 정렬 가능
2. 연도 사보고서(4분기) 기준으로 연간 스냅샷 추출 가능
3. 다중 행(employee 성별, majorHolder 개인별)은 집계 필요

방법:
1. extract → tryNumeric → 빈행 제거 → 연도별 피벗
2. 삼성전자(005930) 기준 시계열 출력
3. docsParser 결과와 비교 가능한 형태로 정리

결과 (실험 후 작성):

결론:

실험일: 2026-03-09
"""

from pathlib import Path

import polars as pl

REPORT_DIR = Path(r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\report")
META_COLS = {"rcept_no", "corp_cls", "corp_code", "corp_name", "corpCode", "fsDiv", "collectStatus", "apiName"}
KEEP_META = {"stockCode", "year", "quarter", "apiType", "stlm_dt"}
Q_MAP = {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}


def extract(stockCode: str, apiType: str) -> pl.DataFrame | None:
    path = REPORT_DIR / f"{stockCode}.parquet"
    if not path.exists():
        return None

    df = pl.read_parquet(path)
    sub = df.filter(pl.col("apiType") == apiType)
    if sub.is_empty():
        return None

    dropCols = []
    for c in sub.columns:
        if c in META_COLS:
            dropCols.append(c)
            continue
        if c in KEEP_META:
            continue
        if sub[c].null_count() == sub.height:
            dropCols.append(c)

    sub = sub.drop(dropCols)
    sub = sub.with_columns(pl.col("year").cast(pl.Int32))
    sub = sub.with_columns(
        pl.col("quarter").replace(Q_MAP).cast(pl.Int32).alias("quarterNum")
    )

    sub = sub.filter(pl.col("stlm_dt").is_not_null())
    sub = sub.sort(["year", "quarterNum"])
    return sub


def tryNumeric(df: pl.DataFrame, exclude: set[str] | None = None) -> pl.DataFrame:
    if exclude is None:
        exclude = set()
    skip = KEEP_META | {"quarterNum"} | exclude

    for c in df.columns:
        if c in skip:
            continue
        if df[c].dtype != pl.Utf8:
            continue

        col = df[c]
        stripped = col.str.strip_chars().str.replace_all(",", "")
        cleanedSeries = stripped.to_frame("_v").select(
            pl.when((pl.col("_v") == "-") | (pl.col("_v") == ""))
            .then(pl.lit(None))
            .otherwise(pl.col("_v"))
            .alias("_v")
        ).to_series()

        numSeries = cleanedSeries.cast(pl.Float64, strict=False)
        nonNullOriginal = cleanedSeries.drop_nulls().len()
        nonNullConverted = numSeries.drop_nulls().len()

        if nonNullOriginal > 0 and nonNullConverted / nonNullOriginal >= 0.7:
            df = df.with_columns(numSeries.alias(c))

    return df


def dividendTimeseries(stockCode: str) -> dict | None:
    df = extract(stockCode, "dividend")
    if df is None:
        return None
    df = tryNumeric(df, exclude={"se", "stock_knd"})

    annual = df.filter(pl.col("quarterNum") == 2)
    common = annual.filter(pl.col("stock_knd") == "보통주")

    years = sorted(common["year"].unique().to_list())
    result = {"years": years, "items": {}}

    seValues = common["se"].unique().drop_nulls().to_list()
    for se in sorted(seValues):
        rows = common.filter(pl.col("se") == se).sort("year")
        vals = {}
        for row in rows.iter_rows(named=True):
            vals[row["year"]] = row["thstrm"]

        result["items"][se] = [vals.get(y) for y in years]

    return result


def employeeTimeseries(stockCode: str) -> dict | None:
    df = extract(stockCode, "employee")
    if df is None:
        return None
    df = tryNumeric(df, exclude={"rm"})

    annual = df.filter(pl.col("quarterNum") == 2)

    totals = annual.filter(
        (pl.col("sexdstn").is_null()) | (pl.col("sexdstn") == "계")
        | (pl.col("sexdstn") == "합계")
    )

    if totals.is_empty():
        totals = (
            annual
            .group_by(["year", "quarterNum"])
            .agg([
                pl.col("sm").sum().alias("sm"),
                pl.col("fyer_salary_totamt").sum().alias("fyer_salary_totamt"),
                pl.col("jan_salary_am").mean().alias("jan_salary_am"),
            ])
            .sort("year")
        )

    years = sorted(totals["year"].unique().to_list())
    totalEmp = []
    avgSalary = []
    for y in years:
        row = totals.filter(pl.col("year") == y)
        if row.is_empty():
            totalEmp.append(None)
            avgSalary.append(None)
        else:
            r = row.row(0, named=True)
            totalEmp.append(r.get("sm"))
            avgSalary.append(r.get("jan_salary_am"))

    return {
        "years": years,
        "totalEmployee": totalEmp,
        "avgMonthlySalary": avgSalary,
    }


def majorHolderTimeseries(stockCode: str) -> dict | None:
    df = extract(stockCode, "majorHolder")
    if df is None:
        return None
    df = tryNumeric(df, exclude={"stock_knd", "rm", "nm", "relate"})

    annual = df.filter(pl.col("quarterNum") == 2)
    common = annual.filter(pl.col("stock_knd") == "보통주")

    topRows = common.filter(pl.col("nm") == "계")
    if topRows.is_empty():
        topRows = common.filter(pl.col("rm") == "계")

    years = sorted(topRows["year"].unique().to_list())
    shareRatio = []
    for y in years:
        row = topRows.filter(pl.col("year") == y)
        if row.is_empty():
            shareRatio.append(None)
        else:
            shareRatio.append(row.row(0, named=True).get("trmend_posesn_stock_qota_rt"))

    topHolder = common.filter(
        (pl.col("nm") != "계") & pl.col("nm").is_not_null()
    )
    names = topHolder.filter(pl.col("year") == years[-1]).sort("trmend_posesn_stock_qota_rt", descending=True)
    latestHolders = []
    for row in names.head(5).iter_rows(named=True):
        latestHolders.append({
            "name": row["nm"],
            "relate": row.get("relate"),
            "ratio": row.get("trmend_posesn_stock_qota_rt"),
        })

    return {
        "years": years,
        "totalShareRatio": shareRatio,
        "latestTopHolders": latestHolders,
    }


if __name__ == "__main__":
    code = "005930"

    print("=" * 60)
    print("1. Dividend Timeseries")
    print("=" * 60)
    div = dividendTimeseries(code)
    if div:
        print(f"  years: {div['years']}")
        for se, vals in div["items"].items():
            print(f"  {se}: {vals}")

    print()
    print("=" * 60)
    print("2. Employee Timeseries")
    print("=" * 60)
    emp = employeeTimeseries(code)
    if emp:
        print(f"  years: {emp['years']}")
        print(f"  totalEmployee: {emp['totalEmployee']}")
        print(f"  avgMonthlySalary: {emp['avgMonthlySalary']}")

    print()
    print("=" * 60)
    print("3. MajorHolder Timeseries")
    print("=" * 60)
    mh = majorHolderTimeseries(code)
    if mh:
        print(f"  years: {mh['years']}")
        print(f"  totalShareRatio: {mh['totalShareRatio']}")
        print(f"  latestTopHolders:")
        for h in mh["latestTopHolders"]:
            print(f"    {h['name']} ({h['relate']}): {h['ratio']}%")
