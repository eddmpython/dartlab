"""
실험 ID: 002
실험명: 노드/엣지 추출 + 법인명↔상장사 매칭

목적:
- 001에서 스캔한 전종목 investedCompany 데이터를 정제
- 출자회사(stockCode) → 피출자회사(inv_prm) 엣지 구축
- 피출자 법인명을 dartlab.listing() 상장사와 매칭
- 상장사 간 출자 네트워크 + 비상장 노드 식별

가설:
1. 법인명 정규화(㈜/(주)/주식회사 제거, strip)로 매칭률 50%+
2. 최신 연도 기준 경영참여 엣지만으로도 의미 있는 그래프 구축 가능
3. 상장사 간 엣지가 100개 이상 존재

방법:
1. listing()에서 회사명→종목코드 역매핑 dict 구축
2. inv_prm 법인명 정규화 (접두사/접미사 통일)
3. 노이즈 행 제거 (합계, -, null, 지분율 이상값)
4. 최신 연도 데이터 기준 엣지 추출
5. 상장사 매칭률 측정

결과 (실험 후 작성):
- 전체: 393,400 엣지, 883 출자회사, 55,774 피출자 법인명, 2015~2025
- 상장사 매칭: 1,093 법인명 (2.0%), 18,430 엣지 (4.7%)
  → 대부분 비상장 자회사/관계사이므로 비율 자체는 정상
- [2025년] 26,776 엣지, 823 출자회사, 14,559 피출자
- [2025년] 상장사→상장사: 1,929 엣지, 1,058 고유 쌍
- [2025년] 경영참여+상장사간: 492 엣지
- 투자목적: 경영참여 6,605 / 단순투자 12,540 / 기타 7,631
- 최다 출자: NH투자증권(456), 미래에셋증권(385), NAVER(259), 현대자동차(221)
- 최다 피출자: 건설공제조합(51개사), 한국경제신문(37), 전기공사공제조합(33)
- 중복: 같은 쌍이 분기별로 반복 → 그래프 구축 시 중복제거 필요
- 총 소요: 6.6초

결론:
- 가설 1 부분 채택: 정규화 매칭률 2%지만 대부분이 비상장이므로 자연스러움.
  상장사 간 엣지 1,058 고유 쌍 확보 — 충분히 의미 있는 규모.
- 가설 2 채택: 경영참여만으로도 492 엣지 (상장사간), 그래프 구축 가능
- 가설 3 채택: 상장사 간 고유 쌍 1,058개 (100개 목표 초과)
- 다음: 분기 중복 제거 + 그래프 분석 (연결 컴포넌트, 재벌 클러스터)

실험일: 2026-03-19
"""

import re
import time
from pathlib import Path

import polars as pl


def load_listing_map() -> tuple[dict[str, str], pl.DataFrame]:
    """상장사 회사명 → 종목코드 역매핑 dict.

    Returns:
        (name_to_code, listing_df)
    """
    import dartlab

    listing = dartlab.listing()
    name_to_code: dict[str, str] = {}
    for row in listing.iter_rows(named=True):
        name = row["회사명"]
        code = row["종목코드"]
        # 원본 이름
        name_to_code[name] = code
        # 정규화 이름도 등록
        norm = _normalize_company_name(name)
        if norm != name:
            name_to_code[norm] = code
        # 다양한 표기 변형 등록
        for prefix in ["㈜", "(주)", "주식회사 ", "주식회사"]:
            name_to_code[f"{prefix}{name}"] = code
        for suffix in [" ㈜", "㈜", " (주)", "(주)", " 주식회사", "주식회사"]:
            name_to_code[f"{name}{suffix}"] = code

    return name_to_code, listing


def _normalize_company_name(name: str) -> str:
    """법인명 정규화.

    - ㈜, (주), 주식회사 제거
    - 앞뒤 공백, 특수문자 정리
    - 영문 대소문자 통일
    """
    if not name:
        return name
    s = name.strip()
    # 법인 형태 접두사/접미사 제거
    for pat in [
        r"^\(주\)\s*",
        r"^㈜\s*",
        r"^주식회사\s*",
        r"\s*\(주\)$",
        r"\s*㈜$",
        r"\s*주식회사$",
        r"\s*\(유\)$",
        r"^유한회사\s*",
        r"\s*유한회사$",
        r"\s*㈜",       # 중간 위치
        r"\(주\)",      # 중간 위치
    ]:
        s = re.sub(pat, "", s)
    s = s.strip()
    return s


def scan_all_invested() -> pl.DataFrame:
    """001과 동일 — 전종목 investedCompany 스캔."""
    from dartlab.core.dataLoader import _dataDir

    report_dir = Path(_dataDir("report"))
    parquet_files = sorted(report_dir.glob("*.parquet"))

    keep_cols = [
        "stockCode", "year", "inv_prm", "invstmnt_purps",
        "trmend_blce_qota_rt", "trmend_blce_acntbk_amount",
        "trmend_blce_qy",
    ]

    frames: list[pl.LazyFrame] = []
    for pf in parquet_files:
        try:
            lf = pl.scan_parquet(str(pf))
            if "apiType" not in lf.collect_schema().names():
                continue
            lf = lf.filter(pl.col("apiType") == "investedCompany")
            available = [c for c in keep_cols if c in lf.collect_schema().names()]
            lf = lf.select(available)
            frames.append(lf)
        except Exception:
            continue

    all_cols = set()
    for lf in frames:
        all_cols.update(lf.collect_schema().names())
    unified: list[pl.LazyFrame] = []
    for lf in frames:
        missing = all_cols - set(lf.collect_schema().names())
        if missing:
            lf = lf.with_columns([pl.lit(None).alias(c) for c in missing])
        unified.append(lf.select(sorted(all_cols)))

    return pl.concat(unified).collect()


def clean_and_build_edges(df: pl.DataFrame, name_to_code: dict[str, str]) -> pl.DataFrame:
    """데이터 정제 + 엣지 테이블 구축.

    Returns:
        edges: DataFrame[from_code, from_name, to_name, to_name_norm, to_code,
                         is_listed, ownership_pct, book_value, purpose, year]
    """
    # 1. 노이즈 행 제거
    noise_names = {"-", "합계", "소계", "", " "}
    df = df.filter(
        pl.col("inv_prm").is_not_null()
        & ~pl.col("inv_prm").is_in(list(noise_names))
    )

    # 2. 지분율 정제 — 문자열이면 숫자로
    if df["trmend_blce_qota_rt"].dtype == pl.Utf8:
        df = df.with_columns(
            pl.col("trmend_blce_qota_rt")
            .str.replace_all(",", "")
            .str.replace_all("-", "")
            .cast(pl.Float64, strict=False)
            .alias("ownership_pct")
        )
    else:
        df = df.with_columns(
            pl.col("trmend_blce_qota_rt").cast(pl.Float64, strict=False).alias("ownership_pct")
        )

    # 이상값 필터 (0~100% 범위만)
    df = df.with_columns(
        pl.when(pl.col("ownership_pct").is_between(0, 100))
        .then(pl.col("ownership_pct"))
        .otherwise(None)
        .alias("ownership_pct")
    )

    # 3. 장부가액 정제
    if df["trmend_blce_acntbk_amount"].dtype == pl.Utf8:
        df = df.with_columns(
            pl.col("trmend_blce_acntbk_amount")
            .str.replace_all(",", "")
            .str.replace_all("-", "")
            .cast(pl.Float64, strict=False)
            .alias("book_value")
        )
    else:
        df = df.with_columns(
            pl.col("trmend_blce_acntbk_amount").cast(pl.Float64, strict=False).alias("book_value")
        )

    # 4. 투자목적 정규화
    purpose_map = {
        "경영참여": "경영참여",
        "단순투자": "단순투자",
        "일반투자": "단순투자",
        "투자": "단순투자",
    }

    df = df.with_columns(
        pl.col("invstmnt_purps")
        .map_elements(lambda v: purpose_map.get(v, "기타") if v and v != "-" else "기타",
                      return_dtype=pl.Utf8)
        .alias("purpose")
    )

    # 5. 법인명 정규화 + 상장사 매칭
    def match_listing(name: str) -> tuple[str, str | None, bool]:
        """법인명 → (정규화명, 종목코드 or None, 상장여부)"""
        norm = _normalize_company_name(name)
        code = name_to_code.get(name) or name_to_code.get(norm)
        return norm, code, code is not None

    norms: list[str] = []
    codes: list[str | None] = []
    listed: list[bool] = []

    for name in df["inv_prm"].to_list():
        n, c, is_l = match_listing(name)
        norms.append(n)
        codes.append(c)
        listed.append(is_l)

    df = df.with_columns(
        pl.Series("to_name_norm", norms),
        pl.Series("to_code", codes),
        pl.Series("is_listed", listed),
    )

    # 6. from 회사명 추가 (listing에서 — 원본 이름 사용)
    code_to_name: dict[str, str] = {}
    import dartlab
    for row in dartlab.listing().iter_rows(named=True):
        code_to_name[row["종목코드"]] = row["회사명"]
    df = df.with_columns(
        pl.col("stockCode")
        .map_elements(lambda c: code_to_name.get(c, c), return_dtype=pl.Utf8)
        .alias("from_name")
    )

    # 최종 엣지 테이블
    edges = df.select([
        pl.col("stockCode").alias("from_code"),
        "from_name",
        pl.col("inv_prm").alias("to_name"),
        "to_name_norm",
        "to_code",
        "is_listed",
        "ownership_pct",
        "book_value",
        "purpose",
        "year",
    ])

    return edges


def analyze_edges(edges: pl.DataFrame) -> None:
    """엣지 테이블 분석."""
    print("=" * 60)
    print("엣지 테이블 통계")
    print("=" * 60)
    print(f"  총 엣지: {len(edges):,}")
    print(f"  출자회사(from) 수: {edges['from_code'].n_unique():,}")
    print(f"  피출자회사(to) 수: {edges['to_name_norm'].n_unique():,}")
    print(f"  연도 범위: {edges['year'].min()} ~ {edges['year'].max()}")

    # 상장사 매칭률
    listed = edges.filter(pl.col("is_listed"))
    unlisted = edges.filter(~pl.col("is_listed"))
    total_unique_targets = edges["to_name_norm"].n_unique()
    listed_unique_targets = listed["to_name_norm"].n_unique()

    print(f"\n  피출자 상장사 매칭:")
    print(f"    매칭된 법인명: {listed_unique_targets:,} / {total_unique_targets:,} ({listed_unique_targets/total_unique_targets:.1%})")
    print(f"    매칭된 엣지: {len(listed):,} / {len(edges):,} ({len(listed)/len(edges):.1%})")

    # 최신 연도만
    latest_year = edges["year"].max()
    latest = edges.filter(pl.col("year") == latest_year)
    print(f"\n  [{latest_year}년] 엣지: {len(latest):,}")
    print(f"    출자회사: {latest['from_code'].n_unique():,}")
    print(f"    피출자회사: {latest['to_name_norm'].n_unique():,}")

    latest_listed = latest.filter(pl.col("is_listed"))
    print(f"    상장사→상장사 엣지: {len(latest_listed):,}")
    print(f"    고유 상장사→상장사 쌍: {latest_listed.select(['from_code','to_code']).unique().height:,}")

    # 투자목적별
    print(f"\n  [{latest_year}년] 투자목적별:")
    for purpose in ["경영참여", "단순투자", "기타"]:
        p = latest.filter(pl.col("purpose") == purpose)
        print(f"    {purpose}: {len(p):,}")

    # 경영참여만 — 상장사 간
    mgmt = latest_listed.filter(pl.col("purpose") == "경영참여")
    print(f"\n  [{latest_year}년] 경영참여 + 상장사간: {len(mgmt):,}")
    if len(mgmt) > 0:
        print(f"  상위 20개 엣지 (경영참여, 상장사간):")
        top = mgmt.sort("ownership_pct", descending=True, nulls_last=True).head(20)
        for row in top.iter_rows(named=True):
            pct = f"{row['ownership_pct']:.1f}%" if row["ownership_pct"] is not None else "N/A"
            bv = f"{row['book_value']/1e8:.0f}억" if row["book_value"] is not None else "N/A"
            print(f"    {row['from_name']} → {row['to_name']} ({pct}, {bv})")

    # 허브 분석 — 가장 많이 출자하는 회사
    print(f"\n  [{latest_year}년] 최다 출자 회사 (from) TOP 15:")
    from_counts = latest.group_by("from_name").agg(
        pl.col("to_name_norm").n_unique().alias("targets"),
        pl.col("is_listed").sum().alias("listed_targets"),
    ).sort("targets", descending=True).head(15)
    for row in from_counts.iter_rows(named=True):
        print(f"    {row['from_name']}: {row['targets']}개 출자 (상장사 {row['listed_targets']}개)")

    # 허브 분석 — 가장 많이 출자 받는 회사
    print(f"\n  [{latest_year}년] 최다 피출자 법인 (to) TOP 15:")
    to_counts = latest.group_by("to_name_norm").agg(
        pl.col("from_code").n_unique().alias("investors"),
    ).sort("investors", descending=True).head(15)
    for row in to_counts.iter_rows(named=True):
        print(f"    {row['to_name_norm']}: {row['investors']}개사가 출자")


if __name__ == "__main__":
    t0 = time.perf_counter()

    print("1. 상장사 목록 로드...")
    name_to_code, listing = load_listing_map()
    print(f"   상장사 {listing.height}개, 매핑 {len(name_to_code)}개")

    print("\n2. 전종목 investedCompany 스캔...")
    raw = scan_all_invested()
    print(f"   raw: {raw.shape}")

    print("\n3. 정제 + 엣지 구축...")
    edges = clean_and_build_edges(raw, name_to_code)
    print(f"   edges: {edges.shape}")

    print()
    analyze_edges(edges)

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
