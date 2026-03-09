"""
실험 ID: 045-004
실험명: 다종목 cross-validation

목적:
- 시계열 피벗 로직이 다양한 종목에서 정상 동작하는지 검증
- 에지 케이스 발견 (금융업, 소규모, 우선주 없는 종목 등)
- employee 집계행 패턴 확인 (종목별 차이)

가설:
1. 대부분 종목에서 dividend/employee/majorHolder 시계열 추출 가능
2. 금융업(은행)은 employee 패턴이 다를 수 있음
3. "계" 행이 없는 종목이 존재할 수 있음

방법:
1. 10개 종목으로 3개 시계열 함수 실행
2. 실패/에지 케이스 수집
3. employee의 합산행 탐지 로직 검증

결과 (실험 후 작성):

결론:

실험일: 2026-03-09
"""

import polars as pl
from pathlib import Path

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
    if common.is_empty():
        common = annual
    dps = common.filter(pl.col("se").str.contains("현금배당금"))
    if dps.is_empty():
        return {"years": [], "dps": [], "note": "no cash dividend rows"}

    years = sorted(dps["year"].unique().to_list())
    vals = {}
    for row in dps.iter_rows(named=True):
        vals[row["year"]] = row.get("thstrm")
    return {"years": years, "dps": [vals.get(y) for y in years]}


def employeeTimeseries(stockCode: str) -> dict | None:
    df = extract(stockCode, "employee")
    if df is None:
        return None
    df = tryNumeric(df, exclude={"rm"})
    annual = df.filter(pl.col("quarterNum") == 2)
    if annual.is_empty():
        annual = df.filter(pl.col("quarterNum") == 4)
    if annual.is_empty():
        return {"years": [], "totalEmployee": [], "note": "no annual data"}

    totals = annual.filter(
        (pl.col("sexdstn").is_null()) | (pl.col("sexdstn") == "계")
        | (pl.col("sexdstn") == "합계")
    )

    if totals.is_empty():
        totals = (
            annual
            .group_by(["year", "quarterNum"])
            .agg(pl.col("sm").sum().alias("sm"))
            .sort("year")
        )

    years = sorted(totals["year"].unique().to_list())
    totalEmp = []
    for y in years:
        row = totals.filter(pl.col("year") == y)
        if row.is_empty():
            totalEmp.append(None)
        else:
            totalEmp.append(row.row(0, named=True).get("sm"))

    return {"years": years, "totalEmployee": totalEmp}


def majorHolderTimeseries(stockCode: str) -> dict | None:
    df = extract(stockCode, "majorHolder")
    if df is None:
        return None
    df = tryNumeric(df, exclude={"stock_knd", "rm", "nm", "relate"})
    annual = df.filter(pl.col("quarterNum") == 2)
    common = annual.filter(pl.col("stock_knd") == "보통주")
    if common.is_empty():
        common = annual

    topRows = common.filter(pl.col("nm") == "계")
    if topRows.is_empty():
        topRows = common.filter(pl.col("rm") == "계")
    if topRows.is_empty():
        return {"years": [], "totalShareRatio": [], "note": "no subtotal row"}

    years = sorted(topRows["year"].unique().to_list())
    ratio = []
    for y in years:
        row = topRows.filter(pl.col("year") == y)
        if row.is_empty():
            ratio.append(None)
        else:
            ratio.append(row.row(0, named=True).get("trmend_posesn_stock_qota_rt"))

    return {"years": years, "totalShareRatio": ratio}


CODES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "네이버",
    "051910": "LG화학",
    "006400": "삼성SDI",
    "105560": "KB금융",
    "055550": "신한지주",
    "003550": "LG",
    "000270": "기아",
    "068270": "셀트리온",
}


if __name__ == "__main__":
    for code, name in CODES.items():
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        div = dividendTimeseries(code)
        if div:
            note = div.get("note", "")
            if note:
                print(f"  dividend: {note}")
            else:
                print(f"  dividend years: {div['years']}")
                print(f"  dps: {div['dps']}")

        emp = employeeTimeseries(code)
        if emp:
            note = emp.get("note", "")
            if note:
                print(f"  employee: {note}")
            else:
                print(f"  employee years: {emp['years']}")
                print(f"  totalEmp: {emp['totalEmployee']}")

        mh = majorHolderTimeseries(code)
        if mh:
            note = mh.get("note", "")
            if note:
                print(f"  majorHolder: {note}")
            else:
                print(f"  majorHolder years: {mh['years']}")
                print(f"  shareRatio: {mh['totalShareRatio']}")
