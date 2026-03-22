"""
실험 ID: 006
실험명: majorHolder 전종목 스캔 + 주주-회사 엣지 구축

목적:
- 978개 report parquet에서 majorHolder(최대주주현황)를 LazyFrame 스캔
- 주주가 법인인 경우 → 회사→회사 엣지 (investedCompany 보완, 역방향)
- 주주가 개인인 경우 → 사람→회사 엣지 (인적 네트워크)
- 같은 사람/법인이 여러 회사의 주주 → 그룹 추론 근거

가설:
1. majorHolder 데이터가 investedCompany보다 역방향 지분 관계 풍부
2. 특수관계인(개인) 공유로 재벌 그룹 추론 가능
3. 법인 주주 매칭으로 순환출자 경로 탐지 가능

방법:
1. 전종목 majorHolder LazyFrame 스캔 (nm, relate, trmend_posesn_stock_qota_rt)
2. 주주 유형 분류: 법인명 패턴(㈜/주식회사/법인) vs 개인명(2~4글자 한글)
3. 법인 주주 → listing 매칭 → 회사→회사 엣지
4. 개인 주주 → 사람 노드, 같은 사람이 여러 회사 주주인 패턴 분석

결과 (실험 후 작성):
- majorHolder 스캔: 348,175행, 1.7초 (978 parquet)
- 2026년 기준: 978종목
- 법인 주주 엣지: 3,950건, 상장사 매칭 932건 (24%), 고유 쌍 318개
- 개인 주주 엣지: 17,886건, 2개사+ 주주 852명
- 핵심 인물 (여러 회사 주주):
  - 이재용: 삼성화재, 삼성전자, 삼성E&A, 삼성에스디에스, 삼성생명, 플레이위드
  - 정의선: 현대자동차, 기아, 현대모비스, 현대글로비스, 현대위아, 현대오토에버
  - 조양래/조현준/조현상: 효성 그룹 전체 (6~7개사)
  - 국민연금공단: POSCO, 하나금융, 신한, KB, NAVER, 한솔 등 6개사
  - 삼성전자 (법인): 삼성바이오, 호텔신라, 삼성SDS, 삼성전기, 삼성중공업, 제일기획
- 분류 이슈: "현대자동차"/"삼성전자"/"국민연금공단" 등이 person으로 오분류
  → corp 분류에 listing 이름 직접 대조 필요
- relate 컬럼: 2026년은 전부 null (최신 분기 데이터 구조 문제)
  → 이전 연도에서 "최대주주 본인"/"특수관계인" 등 확인 가능

결론:
- 가설 1 채택: majorHolder로 318개 상장사→상장사 역방향 지분 쌍 추가 확보
- 가설 2 채택: 이재용→6개사, 정의선→6개사 등 인물 기반 그룹 추론 가능
- 가설 3 부분 채택: 법인 주주 매칭 24%, 순환출자 탐지는 007에서 통합 후 시도
- 개선 필요: corp/person 분류에 listing 회사명 직접 매칭 추가

실험일: 2026-03-19
"""

import re
import time
import polars as pl
from pathlib import Path
from collections import defaultdict


def scan_all_major_holders() -> pl.DataFrame:
    """전종목 majorHolder LazyFrame 스캔."""
    from dartlab.core.dataLoader import _dataDir

    report_dir = Path(_dataDir("report"))
    parquet_files = sorted(report_dir.glob("*.parquet"))

    keep_cols = [
        "stockCode", "year", "nm", "relate",
        "trmend_posesn_stock_co", "trmend_posesn_stock_qota_rt",
    ]

    t0 = time.perf_counter()
    frames: list[pl.LazyFrame] = []

    for pf in parquet_files:
        try:
            lf = pl.scan_parquet(str(pf))
            if "apiType" not in lf.collect_schema().names():
                continue
            lf = lf.filter(pl.col("apiType") == "majorHolder")
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

    df = pl.concat(unified).collect()
    elapsed = time.perf_counter() - t0
    print(f"majorHolder 스캔: {df.shape}, {elapsed:.1f}초")
    return df


_CORP_PATTERNS = re.compile(
    r"㈜|주식회사|\(주\)|법인|조합|재단|기금|공사|은행|증권|보험|캐피탈|투자|펀드|"
    r"[A-Z]{2,}|Co\.|Corp|Ltd|Inc|LLC|PTE|Fund|Trust|Bank"
)

_NOISE_NAMES = {"합계", "-", "소계", "", "계", "기타"}


def classify_holder(name: str) -> str:
    """주주 유형 분류: 'corp' | 'person' | 'noise'."""
    if not name or name in _NOISE_NAMES:
        return "noise"
    if _CORP_PATTERNS.search(name):
        return "corp"
    # 한글 2~4글자는 개인일 가능성 높음
    hangul = re.sub(r"[^가-힣]", "", name)
    if 2 <= len(hangul) <= 4 and len(name) <= 6:
        return "person"
    # 긴 이름은 법인일 가능성
    if len(name) > 8:
        return "corp"
    # 애매한 경우 → person (보수적)
    return "person"


def build_holder_edges(
    df: pl.DataFrame,
    name_to_code: dict[str, str],
    code_to_name: dict[str, str],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """주주 엣지 구축.

    Returns:
        (corp_edges, person_edges)
    """
    # 노이즈 제거
    df = df.filter(
        pl.col("nm").is_not_null()
        & ~pl.col("nm").is_in(list(_NOISE_NAMES))
    )

    # 최신 연도만
    latest_year = df["year"].max()
    df = df.filter(pl.col("year") == latest_year)

    # 지분율 변환
    if df["trmend_posesn_stock_qota_rt"].dtype == pl.Utf8:
        df = df.with_columns(
            pl.col("trmend_posesn_stock_qota_rt")
            .str.replace_all(",", "").str.replace_all("-", "")
            .cast(pl.Float64, strict=False)
            .alias("ownership_pct")
        )
    else:
        df = df.with_columns(
            pl.col("trmend_posesn_stock_qota_rt").cast(pl.Float64, strict=False).alias("ownership_pct")
        )

    # 주주 유형 분류
    types: list[str] = []
    holder_codes: list[str | None] = []
    import importlib.util as _iu
    _sp = _iu.spec_from_file_location("_e2n", str(Path(__file__).resolve().parent / "002_buildEdges.py"))
    _md = _iu.module_from_spec(_sp); _sp.loader.exec_module(_md)
    _normalize = _md._normalize_company_name

    for row in df.iter_rows(named=True):
        nm = row["nm"]
        t = classify_holder(nm)
        types.append(t)

        # 법인이면 listing 매칭
        if t == "corp":
            norm = _normalize(nm)
            code = name_to_code.get(nm) or name_to_code.get(norm)
            holder_codes.append(code)
        else:
            holder_codes.append(None)

    df = df.with_columns(
        pl.Series("holder_type", types),
        pl.Series("holder_code", holder_codes),
    )

    # 법인 주주 엣지
    corp = df.filter(pl.col("holder_type") == "corp")
    corp_edges = corp.select([
        pl.col("holder_code").alias("from_code"),
        pl.col("nm").alias("from_name"),
        pl.col("stockCode").alias("to_code"),
        pl.col("relate"),
        pl.col("ownership_pct"),
        pl.col("year"),
    ])

    # 개인 주주 엣지
    person = df.filter(pl.col("holder_type") == "person")
    person_edges = person.select([
        pl.col("nm").alias("person_name"),
        pl.col("stockCode").alias("to_code"),
        pl.col("relate"),
        pl.col("ownership_pct"),
        pl.col("year"),
    ])

    return corp_edges, person_edges


def analyze_holder_data(
    df: pl.DataFrame,
    corp_edges: pl.DataFrame,
    person_edges: pl.DataFrame,
    code_to_name: dict[str, str],
) -> None:
    """주주 데이터 분석."""
    latest_year = df["year"].max()
    latest = df.filter(pl.col("year") == latest_year)

    print(f"\n{'=' * 70}")
    print(f"majorHolder 분석 ({latest_year}년)")
    print("=" * 70)
    print(f"  총 행: {len(latest):,}")
    print(f"  종목 수: {latest['stockCode'].n_unique()}")

    # 주주 유형별
    print(f"\n  주주 유형:")
    if "holder_type" not in latest.columns:
        # classify
        types = [classify_holder(nm) for nm in latest["nm"].to_list()]
        latest = latest.with_columns(pl.Series("holder_type", types))
    for t in ["corp", "person", "noise"]:
        cnt = latest.filter(pl.col("holder_type") == t).height
        print(f"    {t}: {cnt:,}")

    # 법인 주주 — 상장사 매칭률
    print(f"\n  법인 주주 엣지: {len(corp_edges):,}")
    matched = corp_edges.filter(pl.col("from_code").is_not_null())
    print(f"    상장사 매칭: {len(matched):,} / {len(corp_edges):,} ({len(matched)/max(len(corp_edges),1):.0%})")
    print(f"    매칭된 상장사→상장사 쌍: {matched.select(['from_code','to_code']).unique().height:,}")

    # 매칭된 법인 주주 TOP
    if len(matched) > 0:
        print(f"\n  매칭된 법인 주주 TOP 10:")
        top = matched.group_by("from_name").agg(
            pl.col("to_code").n_unique().alias("companies"),
            pl.col("ownership_pct").mean().alias("avg_pct"),
        ).sort("companies", descending=True).head(10)
        for row in top.iter_rows(named=True):
            avg = f"{row['avg_pct']:.1f}%" if row["avg_pct"] is not None else "N/A"
            print(f"      {row['from_name']}: {row['companies']}개사 주주 (평균 {avg})")

    # 개인 주주 — 여러 회사 주주인 사람
    print(f"\n  개인 주주 엣지: {len(person_edges):,}")
    multi_company = person_edges.group_by("person_name").agg(
        pl.col("to_code").n_unique().alias("companies"),
    ).filter(pl.col("companies") >= 2).sort("companies", descending=True)
    print(f"    2개사+ 주주인 사람: {len(multi_company):,}")

    if len(multi_company) > 0:
        print(f"\n  여러 회사 주주인 개인 TOP 20:")
        for row in multi_company.head(20).iter_rows(named=True):
            # 이 사람이 주주인 회사들
            companies = person_edges.filter(
                pl.col("person_name") == row["person_name"]
            )["to_code"].unique().to_list()
            comp_names = [code_to_name.get(c, c) for c in companies]
            print(f"      {row['person_name']}: {', '.join(comp_names[:6])}")

    # relate 분포
    print(f"\n  관계(relate) 분포:")
    if "relate" in latest.columns:
        for row in latest["relate"].value_counts().sort("count", descending=True).head(10).iter_rows(named=True):
            print(f"    {row['relate']}: {row['count']:,}")


if __name__ == "__main__":
    import importlib.util
    _parent = Path(__file__).resolve().parent
    _spec2 = importlib.util.spec_from_file_location("_e2", str(_parent / "002_buildEdges.py"))
    _m2 = importlib.util.module_from_spec(_spec2)
    _spec2.loader.exec_module(_m2)

    t0 = time.perf_counter()

    print("1. 상장사 목록 + majorHolder 스캔...")
    name_to_code, listing = _m2.load_listing_map()
    code_to_name = {row["종목코드"]: row["회사명"] for row in listing.iter_rows(named=True)}

    df = scan_all_major_holders()

    print("\n2. 주주 엣지 구축...")
    corp_edges, person_edges = build_holder_edges(df, name_to_code, code_to_name)

    analyze_holder_data(df, corp_edges, person_edges, code_to_name)

    elapsed = time.perf_counter() - t0
    print(f"\n총 소요: {elapsed:.1f}초")
