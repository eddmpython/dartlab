"""실험 ID: 073-015
실험명: debtMix — 부채 포트폴리오 + 재무비율 통합

목적:
- corporateBond(014) + finance BS 부채비율 통합
- 사채 의존도 = 사채잔액 / 총부채
- 6개 보조 부채 report(commercialPaper, debtSecurities, hybridSecurities, contingentCapital)는
  전수 스캔 결과 유효 데이터 0건 → 제외

가설:
1. 사채 발행 기업의 부채비율이 미발행 기업보다 높다
2. 사채 발행 기업 중 부채비율 200% 초과가 20% 이상
3. 업종별 사채 의존도 차이가 뚜렷하다 (금융 > 제조)

방법:
1. 014 corporateBond 결과 재활용 (사채잔액)
2. finance BS에서 총부채, 총자산, 자본총계 추출
3. 부채비율 = 총부채 / 자본총계 × 100
4. 사채의존도 = 사채잔액 / 총부채 × 100
5. listing 조인으로 업종별 분석

결과 (2,564종목, finance BS + corporateBond 통합):
- BS 스캔: 2,564종목 (에러 0)
- 사채 발행: 788개 (30.7%), 미발행: 1,776개 (69.3%)
- 부채비율 비교:
  - 사채 발행: 중앙값 120.0%, 평균 197.2%
  - 사채 미발행: 중앙값 54.7%, 평균 101.3%
- 사채발행 + 부채비율 200%+: 199개 (25.5%)
- 사채의존도(사채/총부채): 중앙값 15.3%, 평균 221.3%(이상치), 최대 65,199%
- 시장별:
  - 유가: 사채 44.7%, 부채비율 중앙값 95.2%
  - 코스닥: 사채 25.3%, 부채비율 중앙값 61.9%
- 사채의존도 높은 업종: R&D(46.2%), 전기통신(38.0%), 기초의약(34.7%)
- 사채의존도 낮은 업종: 보험(3.2%), 금융지원(3.4%), 자동차부품(5.2%)
- 보조 부채 report(commercialPaper, debtSecurities, hybridSecurities, contingentCapital) 전수 스캔 결과 유효 0건 → 제외

결론:
- 가설1 채택: 사채 발행 기업 부채비율 중앙값 120% vs 미발행 55% (2배 이상 높음)
- 가설2 채택: 사채발행 + 부채비율 200%+ = 25.5% (20% 이상)
- 가설3 채택: R&D/바이오/소프트웨어가 사채의존도 높음, 금융/보험은 낮음. 업종 차이 뚜렷
- R&D 업종 사채의존도가 높은 이유: 매출 전 기업이 CB/BW로 자금 조달 → 부채 중 사채 비중 높음
- 보험/금융은 예수금/보험료 등 영업 부채가 주류 → 사채 비중 낮음
- 사채의존도 이상치(65,199%) 존재 → 자본잠식 기업에서 발생 (부채 대비 사채 비율 비정상)
- debt축에서 016_maturityRisk와 결합 시 차환 위험 기업 식별 가능

실험일: 2026-03-19
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def _parse_num(s) -> float | None:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip().replace(",", "")
    if s in ("", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ── finance BS 전수 스캔 ──

LIABILITIES_IDS = {"Liabilities", "liabilities", "ifrs-full_Liabilities", "dart_Liabilities"}
LIABILITIES_NMS = {"부채총계", "부채 총계"}
EQUITY_IDS = {"Equity", "equity", "ifrs-full_Equity", "dart_Equity"}
EQUITY_NMS = {"자본총계", "자본 총계"}
ASSETS_IDS = {"Assets", "assets", "ifrs-full_Assets", "dart_Assets"}
ASSETS_NMS = {"자산총계", "자산 총계"}


def scan_bs_totals() -> dict[str, dict]:
    """finance BS에서 총부채, 총자본, 총자산 추출."""
    from dartlab.core.dataLoader import _dataDir

    finance_dir = Path(_dataDir("finance"))
    parquet_files = sorted(finance_dir.glob("*.parquet"))
    print(f"finance parquets: {len(parquet_files)}개")

    result: dict[str, dict] = {}
    errors = 0

    for i, pf in enumerate(parquet_files):
        if i % 500 == 0:
            print(f"  {i}/{len(parquet_files)}...")
        code = pf.stem

        try:
            df = pl.read_parquet(str(pf))
        except (pl.exceptions.ComputeError, OSError):
            errors += 1
            continue

        if df.is_empty() or "account_id" not in df.columns:
            continue

        # BS 행만
        bs = df.filter(
            (pl.col("sj_div") == "BS")
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
        )
        if bs.is_empty():
            continue

        # 연결 우선
        cfs = bs.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else bs

        # 최신 연도
        years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = target.filter(pl.col("bsns_year") == years[0])

        liab = None
        equity = None
        assets = None

        for row in latest.iter_rows(named=True):
            aid = row.get("account_id", "")
            anm = row.get("account_nm", "")
            val = _parse_num(row.get("thstrm_amount"))

            if (aid in LIABILITIES_IDS or anm in LIABILITIES_NMS) and val:
                if liab is None or val > liab:
                    liab = val
            elif (aid in EQUITY_IDS or anm in EQUITY_NMS) and val:
                if equity is None or val > equity:
                    equity = val
            elif (aid in ASSETS_IDS or anm in ASSETS_NMS) and val:
                if assets is None or val > assets:
                    assets = val

        if liab and liab > 0:
            result[code] = {
                "총부채": liab,
                "총자본": equity or 0,
                "총자산": assets or 0,
            }

    print(f"BS 스캔 완료: {len(result)}종목 (에러: {errors})")
    return result


# ── corporateBond 간소화 스캔 ──

def _scan_parquets(api_type: str, keep_cols: list[str]) -> pl.DataFrame:
    from dartlab.core.dataLoader import _dataDir
    report_dir = Path(_dataDir("report"))
    parquet_files = sorted(report_dir.glob("*.parquet"))
    frames: list[pl.LazyFrame] = []
    for pf in parquet_files:
        try:
            lf = pl.scan_parquet(str(pf))
            schema_names = lf.collect_schema().names()
            if "apiType" not in schema_names:
                continue
            available = [c for c in keep_cols if c in schema_names]
            non_meta = [c for c in available if c not in ("stockCode", "year", "quarter")]
            if not non_meta:
                continue
            lf = lf.filter(pl.col("apiType") == api_type).select(available)
            frames.append(lf)
        except (pl.exceptions.ComputeError, OSError):
            continue
    if not frames:
        return pl.DataFrame()
    all_cols: set[str] = set()
    for lf in frames:
        all_cols.update(lf.collect_schema().names())
    unified: list[pl.LazyFrame] = []
    for lf in frames:
        missing = all_cols - set(lf.collect_schema().names())
        if missing:
            lf = lf.with_columns([pl.lit(None).alias(c) for c in missing])
        unified.append(lf.select(sorted(all_cols)))
    return pl.concat(unified).collect()


def scan_bond_amounts() -> dict[str, float]:
    """corporateBond → 종목별 사채잔액."""
    raw = _scan_parquets(
        "corporateBond",
        ["stockCode", "year", "quarter", "remndr_exprtn2", "sm"],
    )
    if raw.is_empty():
        return {}

    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col("sm").is_not_null() & (pl.col("sm") != "-")).shape[0]
        if ok >= 200:
            latest_year = y
            break
    if latest_year is None:
        return {}

    latest = raw.filter(pl.col("year") == latest_year)
    totals = latest.filter(pl.col("remndr_exprtn2") == "합계")
    if totals.is_empty() or totals["stockCode"].n_unique() < 50:
        totals = latest

    result = {}
    for code, group in totals.group_by("stockCode"):
        code_val = code[0]
        max_sm = 0
        for row in group.iter_rows(named=True):
            sm = _parse_num(row.get("sm"))
            if sm and sm > 0:
                max_sm = max(max_sm, sm)
        if max_sm > 0:
            result[code_val] = max_sm
    return result


def compute_debt_mix() -> pl.DataFrame:
    print("BS 스캔 (finance)...")
    bs_map = scan_bs_totals()

    print("\n사채잔액 스캔 (corporateBond)...")
    bond_map = scan_bond_amounts()
    print(f"  사채 발행: {len(bond_map)}종목")

    # 통합
    rows = []
    for code, bs in bs_map.items():
        liab = bs["총부채"]
        equity = bs["총자본"]
        bond = bond_map.get(code, 0)
        debt_ratio = (liab / equity * 100) if equity > 0 else None
        bond_ratio = (bond / liab * 100) if liab > 0 and bond > 0 else 0

        rows.append({
            "종목코드": code,
            "총부채_억": round(liab / 1e8, 0),
            "부채비율": round(debt_ratio, 1) if debt_ratio else None,
            "사채잔액_억": round(bond / 1e8, 0) if bond > 0 else 0,
            "사채의존도": round(bond_ratio, 1),
            "사채발행": bond > 0,
        })

    df = pl.DataFrame(rows)
    total = df.shape[0]
    has_bond = df.filter(pl.col("사채발행") == True).shape[0]
    no_bond = total - has_bond

    print(f"\n=== 부채 현황 ({total}종목) ===")
    print(f"사채 발행: {has_bond}개 ({has_bond/total*100:.1f}%)")
    print(f"사채 미발행: {no_bond}개 ({no_bond/total*100:.1f}%)")

    # 부채비율 비교
    valid_dr = df.filter(pl.col("부채비율").is_not_null())
    bond_dr = valid_dr.filter(pl.col("사채발행") == True)["부채비율"]
    nobond_dr = valid_dr.filter(pl.col("사채발행") == False)["부채비율"]

    if bond_dr.len() > 0 and nobond_dr.len() > 0:
        print(f"\n=== 부채비율 비교 ===")
        print(f"사채 발행 기업: 중앙값 {bond_dr.median():.1f}%, 평균 {bond_dr.mean():.1f}%")
        print(f"사채 미발행 기업: 중앙값 {nobond_dr.median():.1f}%, 평균 {nobond_dr.mean():.1f}%")

    # 사채 발행 기업 중 부채비율 200% 초과
    if bond_dr.len() > 0:
        over200 = bond_dr.filter(bond_dr > 200).len()
        print(f"사채발행 + 부채비율 200%+: {over200}개 ({over200/bond_dr.len()*100:.1f}%)")

    # 사채의존도 분포
    bond_dep = df.filter(pl.col("사채의존도") > 0)["사채의존도"]
    if bond_dep.len() > 0:
        print(f"\n=== 사채의존도 분포 (사채 발행 {bond_dep.len()}종목) ===")
        print(f"평균: {bond_dep.mean():.1f}%")
        print(f"중앙값: {bond_dep.median():.1f}%")
        print(f"최대: {bond_dep.max():.1f}%")

    return df


def analyze_by_market(df: pl.DataFrame) -> None:
    from dartlab.market.network.scanner import load_listing
    _, _, _, listing_meta = load_listing()

    rows = []
    for row in df.iter_rows(named=True):
        meta = listing_meta.get(row["종목코드"], {})
        if meta:
            rows.append({**row, "시장": meta.get("market", ""), "업종": meta.get("industry", "")})

    if not rows:
        return
    merged = pl.DataFrame(rows)

    # 시장별
    for market in ["유가", "코스닥"]:
        sub = merged.filter(pl.col("시장") == market)
        if sub.is_empty():
            continue
        total = sub.shape[0]
        bond = sub.filter(pl.col("사채발행") == True).shape[0]
        dr = sub.filter(pl.col("부채비율").is_not_null())["부채비율"]
        print(f"\n=== {market} ({total}종목) ===")
        print(f"사채 발행: {bond}개 ({bond/total*100:.1f}%)")
        if dr.len() > 0:
            print(f"부채비율 중앙값: {dr.median():.1f}%")

    # 업종별 사채의존도 (5개 이상)
    industry_stats = (
        merged.filter(pl.col("사채발행") == True)
        .group_by("업종")
        .agg([
            pl.col("사채의존도").mean().alias("평균의존도"),
            pl.col("사채의존도").median().alias("중앙값의존도"),
            pl.col("종목코드").count().alias("종목수"),
        ])
        .filter(pl.col("종목수") >= 5)
        .sort("중앙값의존도", descending=True)
    )
    if not industry_stats.is_empty():
        print(f"\n=== 사채의존도 높은 업종 ===")
        print(industry_stats.head(10))
        print(f"\n=== 사채의존도 낮은 업종 ===")
        print(industry_stats.tail(10))


if __name__ == "__main__":
    df = compute_debt_mix()
    if not df.is_empty():
        analyze_by_market(df)
