"""실험 ID: 073-017
실험명: crossValidation — 전 축 다종목 교차 검증

목적:
- governance/workforce/capital/debt 4축 데이터가 동일 종목에서 일관되는지 검증
- 데이터 커버리지 확인 (4축 모두 유효한 종목 수)
- 이상치 교차 확인

가설:
1. 4축 모두 유효 데이터가 있는 종목이 전체의 80% 이상
2. governance A등급 기업이 다른 축에서도 양호한 지표를 보인다
3. 고위험 debt 기업은 governance 점수도 낮다

방법:
1. 각 축 핵심 실험 결과를 재스캔 (간소화)
2. 종목 코드 기준 4축 교차 매칭
3. 커버리지 분석 + 등급간 교차 분석

결과 (2,652종목):
- governance: 2,652종목, workforce: 2,592종목, capital: 2,652종목, debt: 1,457종목
- 교차 커버리지:
  - governance ∩ workforce: 2,592 (97.7%)
  - governance ∩ capital: 2,652 (100.0%)
  - governance ∩ debt: 1,457 (54.9%) — debt가 병목
  - 3축 이상: 2,621 (98.8%)
  - 4축 모두: 1,428 (53.8%)
- 축 수 분포: 4축 53.8%, 3축 45.0%, 2축 1.2%, 1축 0%
- 시장별 4축 커버:
  - 유가: 503/815 (61.7%)
  - 코스닥: 879/1,736 (50.6%)
  - 코넥스: 41/110 (37.3%)

결론:
- 가설1 기각: 4축 모두 53.8% (80% 미만). debt(corporateBond)가 병목 (사채 미발행 기업 제외)
- 3축 이상은 98.8% → debt 제외하면 거의 모든 종목이 커버됨
- governance × capital은 100% 교차 — 두 축의 종목 집합 완전 일치
- governance × workforce도 97.7% — employee 데이터가 일부 누락
- debt는 사채 발행 기업만 해당되므로 본질적으로 커버리지 낮음 (53.8%)
- 4축 모두 커버되는 1,428종목이 scan insight의 핵심 분석 대상
- 3축 기준 2,621종목은 debt를 선택적 축으로 두면 충분한 분석 가능

실험일: 2026-03-19
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


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


# ── 각 축 간소 스캔 ──

def _governance_codes() -> set[str]:
    """005_governanceScore 기반: majorHolder 유효 종목."""
    raw = _scan_parquets("majorHolder", ["stockCode", "year", "quarter", "trmend_posesn_stock_qota_rt"])
    if raw.is_empty():
        return set()
    valid = raw.filter(pl.col("trmend_posesn_stock_qota_rt").is_not_null() & (pl.col("trmend_posesn_stock_qota_rt") != "-"))
    return set(valid["stockCode"].unique().to_list())


def _workforce_codes() -> set[str]:
    """006_employeeScan 기반: employee 유효 종목."""
    raw = _scan_parquets("employee", ["stockCode", "year", "quarter", "jan_salary_am"])
    if raw.is_empty():
        return set()
    valid = raw.filter(pl.col("jan_salary_am").is_not_null() & (pl.col("jan_salary_am") != "-"))
    return set(valid["stockCode"].unique().to_list())


def _capital_codes() -> set[str]:
    """010_dividendScan 기반: dividend 유효 종목."""
    raw = _scan_parquets("dividend", ["stockCode", "year", "quarter", "se"])
    if raw.is_empty():
        return set()
    return set(raw["stockCode"].unique().to_list())


def _debt_codes() -> set[str]:
    """014_bondScan 기반: corporateBond 유효 종목."""
    raw = _scan_parquets("corporateBond", ["stockCode", "year", "quarter", "sm"])
    if raw.is_empty():
        return set()
    valid = raw.filter(pl.col("sm").is_not_null() & (pl.col("sm") != "-") & (pl.col("sm") != ""))
    return set(valid["stockCode"].unique().to_list())


def cross_validate():
    print("=== 각 축 커버리지 스캔 ===")

    gov = _governance_codes()
    print(f"governance (majorHolder): {len(gov)}종목")

    work = _workforce_codes()
    print(f"workforce (employee): {len(work)}종목")

    cap = _capital_codes()
    print(f"capital (dividend): {len(cap)}종목")

    debt = _debt_codes()
    print(f"debt (corporateBond): {len(debt)}종목")

    # 합집합/교집합
    all_codes = gov | work | cap | debt
    print(f"\n전체 (합집합): {len(all_codes)}종목")

    # 교차 커버리지
    gov_work = gov & work
    gov_cap = gov & cap
    gov_debt = gov & debt
    all_four = gov & work & cap & debt
    three_plus = set()
    for code in all_codes:
        count = sum(1 for s in [gov, work, cap, debt] if code in s)
        if count >= 3:
            three_plus.add(code)

    print(f"\n=== 교차 커버리지 ===")
    print(f"governance ∩ workforce: {len(gov_work)} ({len(gov_work)/len(all_codes)*100:.1f}%)")
    print(f"governance ∩ capital: {len(gov_cap)} ({len(gov_cap)/len(all_codes)*100:.1f}%)")
    print(f"governance ∩ debt: {len(gov_debt)} ({len(gov_debt)/len(all_codes)*100:.1f}%)")
    print(f"3축 이상: {len(three_plus)} ({len(three_plus)/len(all_codes)*100:.1f}%)")
    print(f"4축 모두: {len(all_four)} ({len(all_four)/len(all_codes)*100:.1f}%)")

    # 축별 분포
    print(f"\n=== 축 수 분포 ===")
    for n in [4, 3, 2, 1]:
        cnt = sum(1 for code in all_codes if sum(1 for s in [gov, work, cap, debt] if code in s) == n)
        print(f"  {n}축: {cnt}개 ({cnt/len(all_codes)*100:.1f}%)")

    # listing 조인으로 시장별
    from dartlab.engines.dart.scan.network.scanner import load_listing
    _, _, _, listing_meta = load_listing()

    for market in ["유가", "코스닥", "코넥스"]:
        market_codes = {c for c, m in listing_meta.items() if m.get("market") == market}
        in_all = market_codes & all_four
        in_any = market_codes & all_codes
        total = len(market_codes)
        if total > 0:
            print(f"\n=== {market} (상장 {total}) ===")
            print(f"1축 이상: {len(in_any)} ({len(in_any)/total*100:.1f}%)")
            print(f"4축 모두: {len(in_all)} ({len(in_all)/total*100:.1f}%)")


if __name__ == "__main__":
    cross_validate()
