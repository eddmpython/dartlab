"""
실험 ID: 045-002
실험명: apiType별 extract + 정제 로직

목적:
- apiType으로 필터 → null 컬럼 제거 → 숫자 파싱하는 범용 extract 함수 검증
- 각 apiType별 실제 데이터 샘플 확인 (오탐 수정)
- stlm_dt(결산일), year, quarter를 period로 변환하는 로직 확인

가설:
1. null 컬럼 drop + 숫자 파싱으로 깔끔한 DataFrame 생성 가능
2. 모든 apiType에 stlm_dt + year + quarter가 존재하여 시계열 정렬 가능
3. "-" 또는 빈 문자열은 null로 처리 가능

방법:
1. 범용 extract 함수 구현
2. 주요 apiType 5개로 결과 확인 (dividend, employee, majorHolder, auditOpinion, executive)
3. 실제 데이터 샘플 출력하여 정제 품질 검증

결과 (실험 후 작성):

결론:

실험일: 2026-03-09
"""

import polars as pl
from pathlib import Path

REPORT_DIR = Path(r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\report")
META_COLS = {"rcept_no", "corp_cls", "corp_code", "corp_name", "corpCode", "fsDiv", "collectStatus", "apiName"}
KEEP_META = {"stockCode", "year", "quarter", "apiType", "stlm_dt"}


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

    sub = sub.with_columns(
        pl.col("year").cast(pl.Int32),
    )

    qMap = {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}
    sub = sub.with_columns(
        pl.col("quarter").replace(qMap).cast(pl.Int32).alias("quarterNum")
    )

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


STR_OVERRIDES = {
    "auditContract": {"adtor", "cn"},
    "auditOpinion": {"adtor", "adt_reprt_spcmnt_matter"},
    "capitalChange": {"isu_dcrs_de", "isu_dcrs_stle", "isu_dcrs_stock_knd"},
    "nonAuditContract": {"bsns_year", "cntrct_cncls_de", "servc_cn", "servc_exc_pd"},
    "investedCompany": {"frst_acqs_de", "invstmnt_purps"},
    "majorHolderChange": {"change_on", "mxmm_shrholdr_nm", "change_cause"},
    "employee": {"rm"},
    "executivePayAllTotal": {"rm"},
    "unregisteredExecutivePay": {"rm"},
    "treasuryStock": {"stock_knd", "acqs_mth1", "acqs_mth2", "acqs_mth3", "rm"},
    "outsideDirector": {"apnt", "rlsofc", "mdstrm_resig"},
    "privateOfferingUsage": {"se_nm", "pay_de", "real_cptal_use_sttus", "real_cptal_use_dtls_cn", "dffrnc_occrrnc_resn", "cptal_use_plan", "mtrpt_cptal_use_plan_useprps"},
    "publicOfferingUsage": {"se_nm", "pay_de", "on_dclrt_cptal_use_plan", "real_cptal_use_sttus", "rs_cptal_use_plan_useprps", "real_cptal_use_dtls_cn", "dffrnc_occrrnc_resn"},
    "stockTotal": {"se"},
    "minorityHolder": {"se"},
    "executive": {"mxmm_shrholdr_relate"},
    "dividend": {"se", "stock_knd"},
}


if __name__ == "__main__":
    code = "005930"
    testTypes = ["dividend", "employee", "majorHolder", "auditOpinion", "executive"]

    for apiType in testTypes:
        print(f"\n{'='*60}")
        print(f"{apiType}")
        print(f"{'='*60}")

        df = extract(code, apiType)
        if df is None:
            print("  No data")
            continue

        overrides = STR_OVERRIDES.get(apiType, set())
        df = tryNumeric(df, exclude=overrides)

        print(f"  shape: {df.shape}")
        print(f"  columns: {df.columns}")
        print(f"  dtypes:")
        for c in df.columns:
            print(f"    {c}: {df[c].dtype}")

        print(f"\n  sample (latest 3 rows):")
        latest = df.tail(3)
        for row in latest.iter_rows(named=True):
            print(f"    {row}")
