"""
실험 ID: 004
실험명: scan 4축 시장 내 위치 맵

목적:
- 전체 상장사 분포 위에 개별 기업의 scan 4축 percentile을 산출하여
  "이 회사가 시장에서 어디쯤인가"를 직관적으로 보여줄 수 있는지 검증
- 4축 percentile 레이더 ChartSpec + 분포 히스토그램 호환 여부 확인

가설:
1. 4축 중 3축 이상에서 percentile 산출 가능 (10사 기준)
2. 분포가 의미 있는 형태 (정규/편향 — 극단 편향이면 percentile 무의미)
3. 전체 scan 로딩 10초 이내 (UI 실시간 사용 가능)

방법:
1. c.governance("all") 등 전체 DataFrame 로드 (4축)
2. 각 축의 대표 지표에서 percentile rank 산출
3. 10개사에 대해 4축 percentile 레이더 ChartSpec dict 생성
4. 분포 통계 (평균, 중앙값, std, skewness) 산출
5. 로딩 시간 측정

결과:
- 전체 scan 로딩: 266초 (4축 × 전종목 parquet 스캔)
- 분포: governance 정규(skew=-0.37), workforce 극우편향(skew=0.33, mean=14 vs median=1.6)
        capital 이산(환원점수 -1/0/1), debt 극우편향(ICR mean=97 vs median=0.84)
- 10사 모두 3축+ percentile 산출 (3/4축 2사=금융, 4/4축 8사)
- 삼성전자: governance=7%, workforce=86%, capital=100%, debt=68%
- 현대차: governance=7%, workforce=86%, capital=100%, debt=88%
- 카카오: governance=78%, workforce=82%, capital=59%, debt=50%

결론:
- 가설 1 채택: 10사 모두 3축+ percentile 산출 (금융업만 workforce 결측)
- 가설 2 부분채택: governance는 정규 분포로 percentile 의미 있음.
  workforce/debt는 극우편향으로 median 근처 밀집 → percentile 해석 주의.
  capital은 이산변수(-1/0/1)라 percentile보다 분류 자체가 의미 있음.
- 가설 3 기각: 로딩 266초 → UI 실시간 불가. 캐시 필수.
  → 서버에서 전체 scan 결과를 사전 캐시하고 percentile만 즉시 반환하는 구조 필요
- 레이더 ChartSpec은 정상 생성되지만 4축 중 capital(이산)은 레이더에 부적합
  → governance/workforce/debt 3축 레이더 + capital은 분류 뱃지로 분리 권장
- 흡수: scan 결과 캐시 + percentile 함수 → engines/dart/scan/position.py

실험일: 2026-03-20
"""

import math
import time

import polars as pl

import dartlab

# 각 축의 대표 지표 (percentile 산출용)
AXIS_METRICS = {
    "governance": "총점",
    "workforce": "직원당매출_억",
    "capital": "환원점수",
    "debt": "ICR",
}


def load_all_scans(company):
    """4축 전체 DataFrame 로드 + 시간 측정."""
    results = {}
    t0 = time.time()
    for axis in AXIS_METRICS:
        try:
            df = getattr(company, axis)("all")
            results[axis] = df
        except Exception as e:
            print(f"  {axis} all 로드 실패: {e}")
            results[axis] = None
    elapsed = time.time() - t0
    return results, elapsed


def compute_percentile(all_df: pl.DataFrame, metric: str, company_code: str) -> dict | None:
    """전체 DataFrame에서 해당 회사의 percentile + 분포 통계 (polars only)."""
    if all_df is None or metric not in all_df.columns:
        return None

    col = all_df[metric].drop_nulls().cast(pl.Float64)
    n = col.len()
    if n < 10:
        return None

    code_col = "종목코드" if "종목코드" in all_df.columns else None
    if code_col is None:
        return None

    company_row = all_df.filter(pl.col(code_col) == company_code)
    if len(company_row) == 0:
        return None

    company_val = company_row[metric][0]
    if company_val is None:
        return None

    company_val = float(company_val)

    # percentile rank: count of values <= company_val / total
    leq_count = col.filter(col <= company_val).len()
    pct = float(leq_count) / float(n) * 100

    mean_val = col.mean()
    median_val = col.median()
    std_val = col.std()

    return {
        "value": company_val,
        "percentile": round(pct, 1),
        "total": int(n),
        "mean": round(mean_val, 2),
        "median": round(median_val, 2),
        "std": round(std_val, 2),
        "min": round(col.min(), 2),
        "max": round(col.max(), 2),
        "q25": round(col.quantile(0.25), 2),
        "q75": round(col.quantile(0.75), 2),
    }


def build_radar_spec(positions: dict, company_name: str) -> dict:
    """4축 percentile → RadarChart ChartSpec 호환 dict."""
    labels = []
    values = []
    for axis, pos in positions.items():
        if pos is not None:
            labels.append(axis)
            values.append(pos["percentile"])

    return {
        "chartType": "radar",
        "title": f"{company_name} 시장 내 위치",
        "labels": labels,
        "datasets": [
            {
                "label": company_name,
                "data": values,
            }
        ],
        "meta": {
            "maxValue": 100,
            "unit": "percentile",
        },
    }


def build_histogram_data(all_df: pl.DataFrame, metric: str, bins: int = 20) -> dict | None:
    """분포 히스토그램 데이터 (polars only)."""
    if all_df is None or metric not in all_df.columns:
        return None

    col = all_df[metric].drop_nulls().cast(pl.Float64)
    n = col.len()
    if n < 10:
        return None

    # outlier 제거 (1~99 percentile)
    p1 = col.quantile(0.01)
    p99 = col.quantile(0.99)
    trimmed = col.filter((col >= p1) & (col <= p99))

    # 수동 히스토그램
    lo = trimmed.min()
    hi = trimmed.max()
    if hi == lo:
        return None
    step = (hi - lo) / bins
    labels = []
    counts = []
    for i in range(bins):
        edge_lo = lo + step * i
        edge_hi = lo + step * (i + 1)
        if i < bins - 1:
            cnt = trimmed.filter((trimmed >= edge_lo) & (trimmed < edge_hi)).len()
        else:
            cnt = trimmed.filter((trimmed >= edge_lo) & (trimmed <= edge_hi)).len()
        labels.append(f"{edge_lo:.1f}~{edge_hi:.1f}")
        counts.append(int(cnt))

    return {
        "labels": labels,
        "counts": counts,
        "total": int(n),
        "trimmed": int(trimmed.len()),
    }


if __name__ == "__main__":
    test_codes = [
        ("005930", "삼성전자"),
        ("005380", "현대차"),
        ("035720", "카카오"),
        ("000660", "SK하이닉스"),
        ("051910", "LG화학"),
        ("006400", "삼성SDI"),
        ("003550", "LG"),
        ("105560", "KB금융"),
        ("055550", "신한지주"),
        ("068270", "셀트리온"),
    ]

    # 첫 번째 회사로 전체 scan 로드 (캐시 위해)
    print("전체 scan 로드 중...")
    c0 = dartlab.Company(test_codes[0][0])
    all_scans, load_time = load_all_scans(c0)
    print(f"전체 scan 로딩 시간: {load_time:.1f}초")

    for axis, df in all_scans.items():
        if df is not None:
            metric = AXIS_METRICS[axis]
            valid = df[metric].drop_nulls().len() if metric in df.columns else 0
            print(f"  {axis}: {len(df)}행, {metric} 유효 {valid}개")
        else:
            print(f"  {axis}: null")

    # 분포 통계
    print(f"\n{'='*60}")
    print("분포 통계")
    print(f"{'='*60}")
    for axis, metric in AXIS_METRICS.items():
        df = all_scans.get(axis)
        if df is not None and metric in df.columns:
            col = df[metric].drop_nulls().cast(pl.Float64)
            n = col.len()
            mean = col.mean()
            median = col.median()
            std = col.std()
            # skewness 근사: (mean - median) / std * 3 (Pearson's)
            skew = (mean - median) / (std + 1e-9) * 3 if std else 0
            print(f"  {axis} ({metric}):")
            print(f"    N={n}, mean={mean:.2f}, median={median:.2f}")
            print(f"    std={std:.2f}, skew≈{skew:.2f}")
            print(f"    Q25={col.quantile(0.25):.2f}, Q75={col.quantile(0.75):.2f}")

    # 10사 percentile 산출
    print(f"\n{'='*60}")
    print("10사 시장 내 위치 (percentile)")
    print(f"{'='*60}")

    all_results = {}
    for code, name in test_codes:
        positions = {}
        for axis, metric in AXIS_METRICS.items():
            df = all_scans.get(axis)
            pos = compute_percentile(df, metric, code)
            positions[axis] = pos

        valid_axes = sum(1 for v in positions.values() if v is not None)
        pct_str = ", ".join(
            f"{a}={p['percentile']:.0f}%"
            for a, p in positions.items()
            if p is not None
        )
        print(f"  {name}: {valid_axes}/4축 — {pct_str}")

        # 레이더 ChartSpec
        radar = build_radar_spec(positions, name)
        all_results[name] = {
            "positions": positions,
            "radar": radar,
            "valid_axes": valid_axes,
        }

    # 종합
    print(f"\n{'='*60}")
    print("종합")
    print(f"{'='*60}")
    valid_3plus = sum(1 for r in all_results.values() if r["valid_axes"] >= 3)
    print(f"  3축 이상 유효: {valid_3plus}/{len(all_results)}")
    print(f"  로딩 시간: {load_time:.1f}초")

    # 히스토그램 샘플 (governance 총점)
    hist = build_histogram_data(all_scans.get("governance"), "총점")
    if hist:
        print(f"\n  governance 총점 히스토그램 ({hist['total']}개 → {hist['trimmed']}개 trimmed):")
        for label, count in zip(hist["labels"], hist["counts"]):
            bar = "#" * (count // 5)
            print(f"    {label:>12}: {count:>4} {bar}")
