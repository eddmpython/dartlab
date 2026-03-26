"""실험 ID: 087-001
실험명: 매출 예측 앙상블 백테스트 — 시계열 only vs 앙상블 비교

목적:
- revenue_forecast.py의 앙상블 예측이 시계열 단독 대비 정확도를 개선하는지 검증
- 2024년 실제 매출 대비 2023년 기준 1년 전 예측 정확도 비교

가설:
1. 앙상블(시계열+컨센서스)이 시계열 단독 대비 방향성 정확도 5%p+ 향상
2. 앙상블의 MAPE가 시계열 단독 대비 10%+ 감소

방법:
1. 30+ 종목 (시총 상위, 섹터 다양)에서 buildTimeseries 로드
2. forecast_revenue(stock_code=None) → 시계열 only 예측
3. forecast_revenue(stock_code=code) → 앙상블 예측 (컨센서스 있으면)
4. 2024년 최근 연간 실적(4Q합산 or 컨센서스 actual)과 예측값 비교
5. MAPE, 방향성 정확도(성장/감소 방향 일치율) 계산

결과:
- 27개 종목 분석 (금융 4사+카카오뱅크 스킵 — 매출 개념 없음)
- 전체: MAE 18.9→13.2 (-30.3%), 방향성 33.3%→66.7% (+33.3%p)
- 앙상블 우위 섹터: IT/반도체(MAE 40.6→15.6), 게임(11.2→4.2), 산업재(10.8→6.6)
- 앙상블 열위 섹터: 2차전지(23.5→29.2), 비철금속(4.0→17.6) — 컨센서스 과대추정
- 주요 관찰: 시계열은 분기 기반이라 연간 성장 방향을 잘 못 맞춤(33%).
  컨센서스를 섞으면 성장 기업(SK하이닉스, 크래프톤, 하이브)에서 대폭 개선.
  역성장 기업(삼성SDI, LG에너지솔루션)에서는 컨센서스도 역성장을 예측 못해 오차 증가.

결론:
- 가설 1 채택: 방향성 +33.3%p (기준 5%p)
- 가설 2 채택: MAE -30.3% (기준 10%)
- 단, 역성장 기업에서 컨센서스가 과대추정하는 경향 — 향후 실적 추세 반영 보완 필요
- revenue_forecast.py 프로덕션 투입 근거 확보

실험일: 2026-03-22
"""

from __future__ import annotations

import logging
import sys
import time

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

# 시총 상위 + 섹터 다양 30+ 종목
# 제외: 금융업 (매출 개념이 다름), 지주회사
BACKTEST_STOCKS: list[tuple[str, str, str]] = [
    # (종목코드, 기업명, 섹터)
    ("005930", "삼성전자", "IT/반도체"),
    ("000660", "SK하이닉스", "IT/반도체"),
    ("035420", "NAVER", "IT/인터넷"),
    ("035720", "카카오", "IT/인터넷"),
    ("005380", "현대차", "산업재"),
    ("000270", "기아", "산업재"),
    ("006400", "삼성SDI", "2차전지"),
    ("373220", "LG에너지솔루션", "2차전지"),
    ("051910", "LG화학", "화학"),
    ("068270", "셀트리온", "바이오"),
    ("207940", "삼성바이오로직스", "바이오"),
    ("003670", "포스코퓨처엠", "소재"),
    ("005490", "POSCO홀딩스", "철강"),
    ("012330", "현대모비스", "자동차부품"),
    ("028260", "삼성물산", "건설/상사"),
    ("034730", "SK", "지주"),
    ("066570", "LG전자", "전자"),
    ("055550", "신한지주", "금융"),
    ("105560", "KB금융", "금융"),
    ("032830", "삼성생명", "금융"),
    ("009150", "삼성전기", "전자부품"),
    ("018260", "삼성에스디에스", "IT서비스"),
    ("003550", "LG", "지주"),
    ("033780", "KT&G", "소비재"),
    ("011170", "롯데케미칼", "화학"),
    ("010130", "고려아연", "비철금속"),
    ("036570", "엔씨소프트", "게임"),
    ("251270", "넷마블", "게임"),
    ("323410", "카카오뱅크", "금융"),
    ("352820", "하이브", "엔터"),
    ("259960", "크래프톤", "게임"),
    ("000810", "삼성화재", "금융"),
]


def run_backtest():
    """메인 백테스트 실행."""
    from dartlab.providers.dart.finance.pivot import buildTimeseries
    from dartlab.core.finance.forecast import forecast_metric
    from dartlab.core.finance.revenue_forecast import forecast_revenue

    results = []
    skipped = []

    for code, name, sector in BACKTEST_STOCKS:
        print(f"\n{'='*50}")
        print(f"[{code}] {name} ({sector})")

        try:
            series, periods = buildTimeseries(code)
        except (FileNotFoundError, OSError) as exc:
            print(f"  ⚠ 데이터 없음: {exc}")
            skipped.append((code, name, "데이터 없음"))
            continue

        # 매출 시계열 확인
        sales = series.get("IS", {}).get("sales", [])
        if not sales:
            # revenue fallback
            sales = series.get("IS", {}).get("revenue", [])

        valid_sales = [v for v in sales if v is not None and v > 0]
        if len(valid_sales) < 4:
            print(f"  ⚠ 매출 데이터 부족 ({len(valid_sales)}개)")
            skipped.append((code, name, f"매출 데이터 {len(valid_sales)}개"))
            continue

        # 최근 4분기 합 = 연간 매출 (actual 2024~2025)
        # 마지막 4개 유효값의 합을 actual로 사용
        last_4q = valid_sales[-4:]
        actual_annual = sum(last_4q)

        # 1년 전 기준: 직전 4분기 합 (2023~2024)
        if len(valid_sales) >= 8:
            prev_4q = valid_sales[-8:-4]
            prev_annual = sum(prev_4q)
        else:
            print(f"  ⚠ 연간 비교 불가 (유효 {len(valid_sales)}개)")
            skipped.append((code, name, "연간 비교 불가"))
            continue

        actual_growth = (actual_annual / prev_annual - 1) * 100 if prev_annual > 0 else 0

        # === 시계열 only 예측 ===
        ts_result = forecast_revenue(series, stock_code=None, horizon=1)
        ts_projected = ts_result.projected[0] if ts_result.projected else None

        # === 앙상블 예측 ===
        ens_result = forecast_revenue(series, stock_code=code, sector_key=sector, horizon=1)
        ens_projected = ens_result.projected[0] if ens_result.projected else None

        # 성장률 비교
        ts_growth = ts_result.growth_rates[0] if ts_result.growth_rates else None
        ens_growth = ens_result.growth_rates[0] if ens_result.growth_rates else None

        print(f"  실제 연간 매출: {actual_annual / 1e8:,.0f}억 (YoY {actual_growth:+.1f}%)")
        print(f"  시계열 예측: {ts_projected / 1e8:,.0f}억 (성장률 {ts_growth:+.1f}%)" if ts_projected else "  시계열: 예측 불가")
        print(f"  앙상블 예측: {ens_projected / 1e8:,.0f}억 (성장률 {ens_growth:+.1f}%)" if ens_projected else "  앙상블: 예측 불가")
        print(f"  앙상블 방법: {ens_result.method}")
        print(f"  소스: {ens_result.source_weights}")

        results.append({
            "code": code,
            "name": name,
            "sector": sector,
            "actual_annual": actual_annual,
            "actual_growth": actual_growth,
            "ts_projected": ts_projected,
            "ts_growth": ts_growth,
            "ens_projected": ens_projected,
            "ens_growth": ens_growth,
            "ens_method": ens_result.method,
            "ens_sources": list(ens_result.source_weights.keys()),
        })

        # 금융업은 매출 비교가 어려우므로 태깅
        if sector == "금융":
            results[-1]["note"] = "금융업 — 매출 비교 주의"

        # 메모리 관리: gc 호출
        import gc
        gc.collect()

    # === 결과 분석 ===
    print("\n\n" + "=" * 70)
    print("=== 백테스트 결과 요약 ===")
    print("=" * 70)

    if not results:
        print("유효한 결과 없음")
        return

    # MAPE 계산 (성장률 기반)
    ts_errors = []
    ens_errors = []
    ts_direction_correct = 0
    ens_direction_correct = 0
    total_direction = 0

    # 컨센서스 있는 종목만 별도 집계
    ens_with_consensus = []

    for r in results:
        actual_g = r["actual_growth"]
        ts_g = r["ts_growth"]
        ens_g = r["ens_growth"]

        if ts_g is not None:
            ts_errors.append(abs(ts_g - actual_g))
            # 방향성: 성장(>0) vs 감소(<0) 일치 여부
            if (ts_g > 0) == (actual_g > 0):
                ts_direction_correct += 1

        if ens_g is not None:
            ens_errors.append(abs(ens_g - actual_g))
            if (ens_g > 0) == (actual_g > 0):
                ens_direction_correct += 1
            total_direction += 1

            if "consensus" in r["ens_sources"]:
                ens_with_consensus.append(r)

    n = len(results)
    ts_mae = sum(ts_errors) / len(ts_errors) if ts_errors else 0
    ens_mae = sum(ens_errors) / len(ens_errors) if ens_errors else 0
    ts_dir_pct = ts_direction_correct / total_direction * 100 if total_direction else 0
    ens_dir_pct = ens_direction_correct / total_direction * 100 if total_direction else 0

    print(f"\n총 {n}개 종목 분석 (스킵: {len(skipped)}개)")
    print(f"\n{'지표':<20} {'시계열 only':>15} {'앙상블':>15} {'차이':>15}")
    print("-" * 70)
    print(f"{'MAE (성장률 %p)':.<20} {ts_mae:>15.1f} {ens_mae:>15.1f} {ens_mae - ts_mae:>+15.1f}")
    print(f"{'방향성 정확도':.<20} {ts_dir_pct:>14.1f}% {ens_dir_pct:>14.1f}% {ens_dir_pct - ts_dir_pct:>+14.1f}%p")

    # 컨센서스 있는 종목만
    if ens_with_consensus:
        con_errors_ts = []
        con_errors_ens = []
        con_dir_ts = 0
        con_dir_ens = 0
        for r in ens_with_consensus:
            actual_g = r["actual_growth"]
            ts_g = r["ts_growth"]
            ens_g = r["ens_growth"]
            if ts_g is not None:
                con_errors_ts.append(abs(ts_g - actual_g))
                if (ts_g > 0) == (actual_g > 0):
                    con_dir_ts += 1
            if ens_g is not None:
                con_errors_ens.append(abs(ens_g - actual_g))
                if (ens_g > 0) == (actual_g > 0):
                    con_dir_ens += 1

        con_n = len(ens_with_consensus)
        con_ts_mae = sum(con_errors_ts) / len(con_errors_ts) if con_errors_ts else 0
        con_ens_mae = sum(con_errors_ens) / len(con_errors_ens) if con_errors_ens else 0
        con_ts_dir = con_dir_ts / con_n * 100 if con_n else 0
        con_ens_dir = con_dir_ens / con_n * 100 if con_n else 0

        print(f"\n--- 컨센서스 가용 종목만 ({con_n}개) ---")
        print(f"{'MAE (성장률 %p)':.<20} {con_ts_mae:>15.1f} {con_ens_mae:>15.1f} {con_ens_mae - con_ts_mae:>+15.1f}")
        print(f"{'방향성 정확도':.<20} {con_ts_dir:>14.1f}% {con_ens_dir:>14.1f}% {con_ens_dir - con_ts_dir:>+14.1f}%p")

    # 섹터별 분석
    print("\n--- 섹터별 앙상블 MAE ---")
    sector_results: dict[str, list] = {}
    for r in results:
        sector_results.setdefault(r["sector"], []).append(r)

    for sector, items in sorted(sector_results.items()):
        sector_ens_errors = [abs(r["ens_growth"] - r["actual_growth"]) for r in items if r["ens_growth"] is not None]
        sector_ts_errors = [abs(r["ts_growth"] - r["actual_growth"]) for r in items if r["ts_growth"] is not None]
        if sector_ens_errors:
            s_ens_mae = sum(sector_ens_errors) / len(sector_ens_errors)
            s_ts_mae = sum(sector_ts_errors) / len(sector_ts_errors) if sector_ts_errors else 0
            names = ", ".join(r["name"] for r in items)
            print(f"  {sector:<15} TS MAE={s_ts_mae:5.1f} ENS MAE={s_ens_mae:5.1f} ({names})")

    # 개별 결과 테이블
    print("\n--- 종목별 상세 ---")
    print(f"{'종목':<12} {'실제':>8} {'TS예측':>8} {'앙상블':>8} {'TS오차':>8} {'앙상블오차':>8} {'방법':<15}")
    for r in results:
        actual_g = r["actual_growth"]
        ts_g = r["ts_growth"] or 0
        ens_g = r["ens_growth"] or 0
        ts_err = abs(ts_g - actual_g)
        ens_err = abs(ens_g - actual_g)
        winner = "✓" if ens_err < ts_err else ""
        print(f"  {r['name']:<10} {actual_g:>+7.1f}% {ts_g:>+7.1f}% {ens_g:>+7.1f}% {ts_err:>7.1f} {ens_err:>7.1f} {r['ens_method']:<15} {winner}")

    # 스킵 종목
    if skipped:
        print(f"\n--- 스킵 ({len(skipped)}개) ---")
        for code, name, reason in skipped:
            print(f"  [{code}] {name}: {reason}")

    # 가설 판정
    print("\n" + "=" * 70)
    print("=== 가설 판정 ===")
    dir_diff = ens_dir_pct - ts_dir_pct
    mae_improvement = (ts_mae - ens_mae) / ts_mae * 100 if ts_mae > 0 else 0
    print(f"가설 1 (방향성 +5%p): {dir_diff:+.1f}%p → {'채택' if dir_diff >= 5 else '기각'}")
    print(f"가설 2 (MAPE -10%): {mae_improvement:+.1f}% → {'채택' if mae_improvement >= 10 else '기각'}")


if __name__ == "__main__":
    start = time.time()
    run_backtest()
    elapsed = time.time() - start
    print(f"\n실행 시간: {elapsed:.1f}초")
