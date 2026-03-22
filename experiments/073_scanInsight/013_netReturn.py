"""실험 ID: 073-013
실험명: netReturn — 순주주환원 종합 (배당 + 자사주 - 증자)

목적:
- 배당(010), 자사주(011), 증자/감자(012) 데이터를 종합
- 순주주환원 방향 분류: 환원형 / 중립 / 희석형
- 시장별 환원 패턴 비교

가설:
1. 배당+자사주 환원형 기업이 전체의 50% 이상
2. 배당은 하면서 증자도 하는 "모순형" 기업이 10% 이상
3. 유가증권이 코스닥보다 환원형 비율이 높다

방법:
1. 010 배당 스캔 → 배당여부, 배당총액
2. 011 자사주 스캔 → 보유여부, 당기취득
3. 012 증자 스캔 → 최근3년 증자 활동
4. 3개 결합하여 순환원 방향 분류
5. listing 조인으로 시장별 분석

결과 (2,655종목):
- 배당: 2,652종목 (2024 기준), 자사주: 2,652종목, 증자: 2,380종목
- 순주주환원 분류:
  - 환원형: 1,092개 (41.1%)
  - 중립: 756개 (28.5%)
  - 희석형: 807개 (30.4%)
- 모순형 (배당+최근증자): 285개 (10.7%)
- 상세 패턴:
  - 배당O+자사주X+증자X: 688 (25.9%) ← 순수 배당형
  - 배당X+자사주X+증자O: 807 (30.4%) ← 순수 희석형
  - 배당X+자사주X+증자X: 430 (16.2%) ← 완전 무활동
  - 배당O+자사주O+증자X: 231 (8.7%) ← 최강 환원형
- 시장별:
  - 유가: 환원형 64.6%, 중립 24.2%, 희석형 11.2%
  - 코스닥: 환원형 33.0%, 중립 30.0%, 희석형 37.1%
  - 코넥스: 환원형 5.5%, 중립 40.9%, 희석형 53.6%

결론:
- 가설1 기각: 환원형 41.1% (50% 미만). 희석형 30.4%가 시장의 큰 축
- 가설2 채택: 모순형(배당+최근증자) 10.7% (10% 이상). CB/BW로 자금 조달하면서 배당하는 기업 존재
- 가설3 채택: 유가 64.6% vs 코스닥 33.0% (유가가 2배 환원적)
- 코스닥은 희석형(37.1%)이 환원형(33.0%)보다 많음 — 성장 자금 조달 활발
- 코넥스는 절반 이상이 희석형 — 초기 기업은 주주환원 여력 없음
- 순수 배당형(25.9%)이 가장 큰 환원 패턴. 자사주+배당 병행은 8.7%로 소수
- capital축 4개 실험 완료. 종합 인사이트: 한국 시장 주주환원은 유가 중심, 코스닥은 성장/희석 우세

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


def _parse_date_year(s) -> int | None:
    if s is None:
        return None
    s = str(s).strip()
    if s in ("", "-"):
        return None
    for sep in (".", "-"):
        if sep in s:
            parts = s.split(sep)
            if parts:
                try:
                    y = int(parts[0])
                    if 1990 <= y <= 2030:
                        return y
                except ValueError:
                    pass
    return None


# ── 010 배당 스캔 (간소화) ──

DPS_KEYS = {"주당 현금배당금(원)", "주당현금배당금(원)", "주당현금배당금", "현금배당금(원)"}
TOTAL_KEYS = {"현금배당금총액(백만원)", "현금배당금총액"}


def _scan_dividend() -> dict[str, dict]:
    raw = _scan_parquets(
        "dividend",
        ["stockCode", "year", "quarter", "se", "thstrm"],
    )
    if raw.is_empty():
        return {}

    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        q4 = sub.filter(pl.col("quarter") == "4분기")
        target = q4 if not q4.is_empty() else sub
        # DPS 행 기준으로 유효 체크 (thstrm이 숫자인 DPS 행이 100개 이상)
        dps_ok = target.filter(
            pl.col("se").is_in(list(DPS_KEYS))
            & pl.col("thstrm").is_not_null()
            & (pl.col("thstrm") != "-")
            & (pl.col("thstrm") != "")
        ).shape[0]
        if dps_ok >= 100:
            latest_year = y
            break
    if latest_year is None:
        return {}

    latest = raw.filter(pl.col("year") == latest_year)
    q4 = latest.filter(pl.col("quarter") == "4분기")
    if not q4.is_empty():
        latest = q4

    result = {}
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        dps = None
        total_div = None
        for row in group.iter_rows(named=True):
            se = row.get("se", "")
            if not se:
                continue
            val = _parse_num(row.get("thstrm"))
            if se in DPS_KEYS and val and val > 0:
                if dps is None or val > dps:
                    dps = val
            elif se in TOTAL_KEYS and val and val > 0:
                total_div = val
        result[code_val] = {
            "배당여부": dps is not None and dps > 0,
            "배당총액_백만": total_div or 0,
        }
    return result


# ── 011 자사주 스캔 (간소화) ──

def _scan_treasury() -> dict[str, dict]:
    raw = _scan_parquets(
        "treasuryStock",
        ["stockCode", "year", "quarter", "trmend_qy", "change_qy_acqs"],
    )
    if raw.is_empty():
        return {}

    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col("trmend_qy").is_not_null() & (pl.col("trmend_qy") != "-")).shape[0]
        if ok >= 300:
            latest_year = y
            break
    if latest_year is None:
        return {}

    latest = raw.filter(pl.col("year") == latest_year)
    result = {}
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        total_held = 0
        total_acqs = 0
        for row in group.iter_rows(named=True):
            held = _parse_num(row.get("trmend_qy"))
            acqs = _parse_num(row.get("change_qy_acqs"))
            if held and held > 0:
                total_held += int(held)
            if acqs and acqs > 0:
                total_acqs += int(acqs)
        result[code_val] = {
            "자사주보유": total_held > 0,
            "당기취득": total_acqs > 0,
        }
    return result


# ── 012 증자 스캔 (간소화 — 최근 3년) ──

INCREASE_TYPES = {
    "유상증자(주주배정)", "유상증자(제3자배정)", "유상증자(일반공모)",
    "전환권행사", "신주인수권행사", "주식매수선택권행사", "무상증자",
}


def _scan_capital_change() -> dict[str, dict]:
    raw = _scan_parquets(
        "capitalChange",
        ["stockCode", "year", "quarter", "isu_dcrs_stle", "isu_dcrs_de"],
    )
    if raw.is_empty():
        return {}

    valid = raw.filter(
        pl.col("isu_dcrs_stle").is_not_null()
        & (pl.col("isu_dcrs_stle") != "-")
        & (pl.col("isu_dcrs_stle") != "")
    )

    result = {}
    for code, group in valid.group_by("stockCode"):
        code_val = code[0]
        recent_increase = False
        for row in group.iter_rows(named=True):
            stle = row.get("isu_dcrs_stle", "")
            event_year = _parse_date_year(row.get("isu_dcrs_de"))
            if stle in INCREASE_TYPES and event_year and event_year >= 2023:
                recent_increase = True
                break
        result[code_val] = {"최근증자": recent_increase}
    return result


# ── 종합 ──

def compute_net_return() -> pl.DataFrame:
    print("배당 스캔...")
    div_map = _scan_dividend()
    print(f"  배당: {len(div_map)}종목")

    print("자사주 스캔...")
    treasury_map = _scan_treasury()
    print(f"  자사주: {len(treasury_map)}종목")

    print("증자 스캔...")
    cap_map = _scan_capital_change()
    print(f"  증자: {len(cap_map)}종목")

    # 전체 종목 합집합
    all_codes = set(div_map.keys()) | set(treasury_map.keys()) | set(cap_map.keys())
    print(f"\n전체 종목: {len(all_codes)}")

    results = []
    for code in all_codes:
        d = div_map.get(code, {})
        t = treasury_map.get(code, {})
        c = cap_map.get(code, {})

        has_dividend = d.get("배당여부", False)
        has_buyback = t.get("당기취득", False)
        has_treasury = t.get("자사주보유", False)
        recent_increase = c.get("최근증자", False)

        # 환원 점수: 배당(+1), 자사주 취득(+1), 최근 증자(-1)
        return_score = 0
        if has_dividend:
            return_score += 1
        if has_buyback:
            return_score += 1
        if recent_increase:
            return_score -= 1

        # 분류
        if return_score >= 1:
            category = "환원형"
        elif return_score == 0:
            category = "중립"
        else:
            category = "희석형"

        # 모순형: 배당하면서 최근 증자
        contradiction = has_dividend and recent_increase

        results.append({
            "종목코드": code,
            "배당": has_dividend,
            "자사주취득": has_buyback,
            "자사주보유": has_treasury,
            "최근증자": recent_increase,
            "환원점수": return_score,
            "분류": category,
            "모순형": contradiction,
        })

    df = pl.DataFrame(results)
    total = df.shape[0]

    # 분류별 분포
    print(f"\n=== 순주주환원 분류 ({total}종목) ===")
    for cat in ["환원형", "중립", "희석형"]:
        cnt = df.filter(pl.col("분류") == cat).shape[0]
        print(f"{cat}: {cnt}개 ({cnt/total*100:.1f}%)")

    # 모순형
    contra = df.filter(pl.col("모순형") == True).shape[0]
    print(f"\n모순형 (배당+최근증자): {contra}개 ({contra/total*100:.1f}%)")

    # 조합 패턴
    print(f"\n=== 상세 패턴 ===")
    patterns = {
        "배당O + 자사주O + 증자X": (True, True, False),
        "배당O + 자사주X + 증자X": (True, False, False),
        "배당O + 자사주O + 증자O": (True, True, True),
        "배당O + 자사주X + 증자O": (True, False, True),
        "배당X + 자사주O + 증자X": (False, True, False),
        "배당X + 자사주X + 증자X": (False, False, False),
        "배당X + 자사주O + 증자O": (False, True, True),
        "배당X + 자사주X + 증자O": (False, False, True),
    }
    for label, (d, b, i) in patterns.items():
        cnt = df.filter(
            (pl.col("배당") == d) & (pl.col("자사주취득") == b) & (pl.col("최근증자") == i)
        ).shape[0]
        if cnt > 0:
            print(f"  {label}: {cnt}개 ({cnt/total*100:.1f}%)")

    return df


def analyze_by_market(df: pl.DataFrame) -> None:
    from dartlab.engines.dart.scan.network.scanner import load_listing
    _, _, _, listing_meta = load_listing()

    rows = []
    for row in df.iter_rows(named=True):
        meta = listing_meta.get(row["종목코드"], {})
        if meta:
            rows.append({**row, "시장": meta.get("market", "")})

    if not rows:
        return
    merged = pl.DataFrame(rows)

    for market in ["유가", "코스닥", "코넥스"]:
        sub = merged.filter(pl.col("시장") == market)
        if sub.is_empty():
            continue
        total = sub.shape[0]
        returning = sub.filter(pl.col("분류") == "환원형").shape[0]
        neutral = sub.filter(pl.col("분류") == "중립").shape[0]
        diluting = sub.filter(pl.col("분류") == "희석형").shape[0]
        contra = sub.filter(pl.col("모순형") == True).shape[0]
        print(f"\n=== {market} ({total}종목) ===")
        print(f"환원형: {returning}개 ({returning/total*100:.1f}%)")
        print(f"중립: {neutral}개 ({neutral/total*100:.1f}%)")
        print(f"희석형: {diluting}개 ({diluting/total*100:.1f}%)")
        print(f"모순형: {contra}개 ({contra/total*100:.1f}%)")


if __name__ == "__main__":
    df = compute_net_return()
    if not df.is_empty():
        analyze_by_market(df)
