"""
실험 ID: 001
실험명: 전종목 investedCompany LazyFrame 스캔 + 컬럼 품질 탐색

목적:
- 978개 report parquet에서 investedCompany를 LazyFrame으로 일괄 스캔
- 컬럼 구조/품질/결측 현황 파악
- 노드-엣지 그래프 구축 가능성 판단

가설:
1. LazyFrame concat + predicate pushdown으로 전종목 스캔 10초 이내
2. inv_prm(법인명) 컬럼이 모든 종목에 존재하고 피출자회사 식별 가능
3. trmend_blce_qota_rt(지분율)이 80%+ 종목에서 non-null

방법:
1. 전종목 parquet을 pl.scan_parquet → apiType=="investedCompany" 필터
2. 핵심 컬럼만 projection → collect
3. 컬럼별 null률, 고유값 수, 분포 확인
4. inv_prm 값 패턴 분석 (합계, -, 빈값 등 노이즈)

결과 (실험 후 작성):
- 978개 parquet → 440,717행, 1.7초 (LazyFrame predicate pushdown)
- 969개 상장사, 12개 연도 (2015~2026), 2026년 966개사 보유
- 유효 법인명(inv_prm): 64,963개 고유값, 393,400행
- 노이즈: '-' 6,600 / '합계' 32,748 / null 7,967 / '소계' 2
- 투자목적: 단순투자 70,463 / 경영참여 63,935 / 투자 47,351 / '-' 45,707 / 일반투자 22,741
  → 2,321개 고유값 (자유텍스트 입력 → 정규화 필요)
- 지분율: 292,599건 non-null, median 24.9%
  → 이상값 존재 (max 640억% → 장부가액이 지분율 컬럼에 혼입)
  → 100% 이상 67,928건 (정제 필요)
  → 정상 범위 (0~100%): [0,5) 71K / [5,20) 65K / [20,50) 46K / [50,100) 42K
- 최다 출현 법인명: 건설공제조합(1,012), 정보통신공제조합(641), 전기공사공제조합(594)
  → 공제조합이 상위 차지 (다수 건설사가 투자)

결론:
- 가설 1 채택: 1.7초 (10초 이내 목표 초과 달성)
- 가설 2 채택: inv_prm 98.2% non-null, 노이즈 제거 후 유효
- 가설 3 수정: 지분율 non-null 66.4% (80% 미달), 이상값 정제 필수
- 노드-엣지 그래프 구축 가능. 다음 단계: 법인명 정규화 + 상장사 매칭 + 이상값 필터

실험일: 2026-03-19
"""

import time
from pathlib import Path

import polars as pl


def scan_all_invested() -> pl.DataFrame:
    """전종목 report parquet에서 investedCompany만 LazyFrame으로 추출."""
    from dartlab.core.dataLoader import _dataDir

    report_dir = Path(_dataDir("report"))
    parquet_files = sorted(report_dir.glob("*.parquet"))
    print(f"report parquet 파일 수: {len(parquet_files)}")

    # 핵심 컬럼만 선택 (projection pushdown)
    keep_cols = [
        "stockCode",
        "year",
        "inv_prm",           # 법인명 (피출자회사)
        "invstmnt_purps",    # 투자목적 (경영참여/단순투자)
        "trmend_blce_qota_rt",       # 기말 지분율(%)
        "trmend_blce_acntbk_amount", # 기말 장부가액
        "trmend_blce_qy",            # 기말 수량
        "frst_acqs_de",              # 최초취득일
        "recent_bsns_year_fnnr_sttus_tot_assets",  # 피출자 총자산
        "recent_bsns_year_fnnr_sttus_thstrm_ntpf", # 피출자 당기순이익
    ]

    t0 = time.perf_counter()
    frames: list[pl.LazyFrame] = []
    skipped = 0

    for pf in parquet_files:
        try:
            lf = pl.scan_parquet(str(pf))
            # apiType 컬럼이 없는 parquet은 스킵
            if "apiType" not in lf.collect_schema().names():
                skipped += 1
                continue

            # predicate pushdown: investedCompany만
            lf = lf.filter(pl.col("apiType") == "investedCompany")

            # 존재하는 컬럼만 select (종목마다 컬럼 다를 수 있음)
            available = [c for c in keep_cols if c in lf.collect_schema().names()]
            lf = lf.select(available)

            frames.append(lf)
        except Exception as e:
            print(f"  SKIP {pf.stem}: {e}")
            skipped += 1

    print(f"스캔 대상: {len(frames)}, 스킵: {skipped}")

    # 컬럼 통일 (일부 종목에 없는 컬럼 → null로 채움)
    all_cols = set()
    for lf in frames:
        all_cols.update(lf.collect_schema().names())

    unified: list[pl.LazyFrame] = []
    for lf in frames:
        schema = lf.collect_schema()
        missing = all_cols - set(schema.names())
        if missing:
            lf = lf.with_columns([pl.lit(None).alias(c) for c in missing])
        unified.append(lf.select(sorted(all_cols)))

    df = pl.concat(unified).collect()
    elapsed = time.perf_counter() - t0
    print(f"collect 완료: {df.shape}, {elapsed:.1f}초")
    return df


def analyze_quality(df: pl.DataFrame) -> None:
    """컬럼별 품질 분석."""
    print("\n" + "=" * 60)
    print("컬럼별 품질 분석")
    print("=" * 60)

    total = len(df)
    for col in sorted(df.columns):
        non_null = df[col].drop_nulls().len()
        null_rate = 1 - non_null / total if total > 0 else 0
        n_unique = df[col].n_unique()
        print(f"  {col:50s}  non_null={non_null:>7,}  null={null_rate:5.1%}  unique={n_unique:>6,}")

    # inv_prm 노이즈 분석
    print("\n" + "=" * 60)
    print("inv_prm (법인명) 노이즈 패턴")
    print("=" * 60)
    if "inv_prm" in df.columns:
        inv = df["inv_prm"]
        noise_vals = ["-", "합계", "", None, "소계"]
        for v in noise_vals:
            if v is None:
                cnt = inv.null_count()
            else:
                cnt = (inv == v).sum()
            print(f"  '{v}': {cnt:,}")

        # 유효 법인명 수
        valid = inv.filter(
            inv.is_not_null()
            & (inv != "-")
            & (inv != "합계")
            & (inv != "소계")
            & (inv != "")
        )
        print(f"\n  유효 법인명 수: {valid.n_unique():,} (총 {valid.len():,}행)")
        print(f"  상위 20개 법인명:")
        top = valid.value_counts().sort("count", descending=True).head(20)
        print(top)

    # 투자목적 분포
    print("\n" + "=" * 60)
    print("투자목적 분포")
    print("=" * 60)
    if "invstmnt_purps" in df.columns:
        print(df["invstmnt_purps"].value_counts().sort("count", descending=True))

    # 지분율 분포
    print("\n" + "=" * 60)
    print("지분율 분포 (trmend_blce_qota_rt)")
    print("=" * 60)
    if "trmend_blce_qota_rt" in df.columns:
        raw = df["trmend_blce_qota_rt"]
        # 문자열이면 숫자로 변환
        if raw.dtype == pl.Utf8:
            rate = raw.str.replace_all(",", "").str.replace_all("-", "").cast(pl.Float64, strict=False).drop_nulls()
        else:
            rate = raw.cast(pl.Float64, strict=False).drop_nulls()
        if len(rate) > 0:
            mean_v = rate.mean()
            med_v = rate.median()
            min_v = rate.min()
            max_v = rate.max()
            print(f"  count: {len(rate):,}")
            print(f"  mean:  {mean_v:.2f}%" if mean_v is not None else "  mean: N/A")
            print(f"  median: {med_v:.2f}%" if med_v is not None else "  median: N/A")
            print(f"  min:   {min_v:.2f}%" if min_v is not None else "  min: N/A")
            print(f"  max:   {max_v:.2f}%" if max_v is not None else "  max: N/A")
            # 구간별
            for lo, hi in [(0, 5), (5, 20), (20, 50), (50, 100), (100, 101)]:
                cnt = rate.filter((rate >= lo) & (rate < hi)).len()
                print(f"  [{lo:3d}%, {hi:3d}%): {cnt:>6,}")

    # 종목 수
    print("\n" + "=" * 60)
    print("종목 분포")
    print("=" * 60)
    if "stockCode" in df.columns:
        print(f"  종목 수: {df['stockCode'].n_unique()}")
        print(f"  연도 수: {df['year'].n_unique()}")
        years = df["year"].drop_nulls().unique().sort()
        print(f"  연도 범위: {years[0]} ~ {years[-1]}")
        # 최신 연도 종목 수
        latest_year = years[-1]
        latest = df.filter(pl.col("year") == latest_year)
        print(f"  {latest_year}년 데이터 보유 종목: {latest['stockCode'].n_unique()}")


if __name__ == "__main__":
    df = scan_all_invested()
    analyze_quality(df)
