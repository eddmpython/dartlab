"""실험 ID: 098-018
실험명: 거시 시나리오 가상환경 프로토타입

목적:
- "환율 X%, 금리 Y%, 유가 Z% → 이 섹터/기업 매출 예측" 시나리오 엔진 검증
- simulation.py에 이미 있는 MacroScenario 프리셋 + SECTOR_ELASTICITY를 활용
- 015-017에서 확인한 거시 회귀의 한계를 인정하되, 방향성 시나리오 도구로서의 가치 검증
- 2020 코로나 / 2022 금리 인상 실제 데이터와 시나리오 예측을 비교

가설:
1. 시나리오 예측의 방향(+/-) 정확도 > 70% (8개 섹터 중 6개 이상)
2. 하드코딩 탄성도 기반 예측이 실증 회귀보다 robust (MAE 기준)
3. adverse 시나리오가 2020 실제와 가장 유사, rate_hike가 2022와 유사

방법:
1. simulation.py의 SECTOR_ELASTICITY(revenueToGdp, revenueToFx) 활용
2. 시나리오 정의: 2020형(코로나), 2022형(금리인상), 2024형(회복)
3. 각 시나리오에서 섹터별 매출 변동 예측 → 실제 데이터와 비교
4. 방향 정확도 + MAE로 시나리오 도구 유용성 평가

결과:
| 연도 | 상황 | 방향 정확 | MAE |
|------|------|----------|-----|
| 2020 | 코로나 | 50% (4/8) | 8.6%p |
| 2022 | 금리인상+원화약세 | 62% (5/8) | 9.5%p |
| 2024 | 완만한 회복 | 88% (7/8) | 6.2%p |
| **평균** | | **67%** | **8.1%p** |

- 2024(정상 경기) 방향 88% 우수, 2020(코로나) 50% = 랜덤
- 반도체 2020: 예측 -2.1%, 실제 +4.0% (코로나 비대칭 효과)
- 반도체 2022: 예측 +16.5%, 실제 -8.0% (재고 사이클 미반영)
- IT 2020: 예측 -0.9%, 실제 +21.3% (디지털 전환 수혜 포착 불가)
- 프리셋 매칭: adverse→2020(MAE 8.7), recovery→2022(MAE 7.9), baseline→2024(MAE 5.9)
  → 2022에 recovery가 매칭되는 역설 (탄성도가 방향만 맞추고 크기 엉뚱)

결론:
- **가설 1 부분 채택**: 평균 방향 67%>70% 미달. 2024(정상)만 88% 달성
- **가설 2 채택**: 하드코딩 탄성도 MAE 8.1%p — 015 실증 회귀 20.7%보다 robust
- **가설 3 기각**: adverse→2020은 맞지만 MAE 8.7%p. rateHike→2022는 오히려 recovery가 더 맞음
- **시나리오 도구 평가**:
  - 정상 경기(2024형)에서 방향성 참고용으로 유용 (88%)
  - 구조적 충격(2020 코로나, 2022 재고 사이클)에서는 실패 (50-62%)
  - MAE 8.1%p → 앙상블 MdAE 12.0%보다 낫지만, 섹터 수준이라 기업 수준과 직접 비교 불가
  - **결론: "방향성 참고 도구"로 유효. 점 추정 도구로는 부적합**

실험일: 2026-03-25
"""

import time

import numpy as np

# simulation.py의 SECTOR_ELASTICITY에서 가져온 값 (revenueToGdp, revenueToFx)
# 원본: src/dartlab/engines/analysis/analyst/simulation.py
SECTOR_ELASTICITY = {
    "반도체": {"gdp": 2.5, "fx": 0.8},    # 고 경기민감 + 수출
    "자동차": {"gdp": 1.5, "fx": 0.6},    # 중 경기민감 + 수출
    "화학": {"gdp": 1.8, "fx": 0.5},      # 중 경기민감 + 수출
    "철강": {"gdp": 2.0, "fx": 0.3},      # 고 경기민감
    "통신": {"gdp": 0.3, "fx": 0.0},      # 방어주
    "식품": {"gdp": 0.4, "fx": -0.1},     # 방어주 (원재료 수입 → 환율 역효과)
    "IT/소프트웨어": {"gdp": 1.2, "fx": 0.2}, # 중 성장
    "유통": {"gdp": 1.0, "fx": -0.2},     # 내수 (수입물가 역효과)
}

# 실제 거시 변동 (전년 대비)
ACTUAL_MACRO = {
    2020: {"gdp": -0.7, "fx": -0.4, "label": "코로나"},
    2022: {"gdp": 2.6, "fx": 12.5, "label": "금리인상+원화약세"},
    2024: {"gdp": 2.0, "fx": 7.0, "label": "완만한 회복"},
}

# 시나리오 프리셋 (simulation.py MacroScenario 스타일)
SCENARIOS = {
    "adverse": {"gdp": -2.0, "fx": 10.0, "desc": "경기침체+원화약세"},
    "rateHike": {"gdp": 1.5, "fx": 8.0, "desc": "금리인상+원화약세"},
    "baseline": {"gdp": 2.5, "fx": 0.0, "desc": "정상 성장"},
    "recovery": {"gdp": 3.5, "fx": -3.0, "desc": "강한 회복+원화강세"},
    "semDown": {"gdp": 1.0, "fx": 5.0, "desc": "반도체 하강 사이클"},
}

# 실제 섹터별 매출 성장률 (%)
ACTUAL_REVENUE = {
    2020: {
        "반도체": 4.0, "자동차": -9.8, "화학": -10.4, "철강": -7.8,
        "통신": 3.0, "식품": 5.5, "IT/소프트웨어": 21.3, "유통": -8.5,
    },
    2022: {
        "반도체": -8.0, "자동차": 18.6, "화학": 6.3, "철강": -3.5,
        "통신": 3.2, "식품": 12.1, "IT/소프트웨어": 9.5, "유통": 8.5,
    },
    2024: {
        "반도체": 35.2, "자동차": 3.1, "화학": -2.1, "철강": 0.5,
        "통신": 0.9, "식품": 1.0, "IT/소프트웨어": 8.0, "유통": 1.5,
    },
}


def predictFromScenario(gdp, fx):
    """탄성도 기반 섹터별 매출 변동 예측."""
    predictions = {}
    for sector, elast in SECTOR_ELASTICITY.items():
        predicted = elast["gdp"] * gdp + elast["fx"] * fx
        predictions[sector] = round(predicted, 2)
    return predictions


def evaluateScenario(predicted, actual):
    """예측 vs 실제 비교: 방향 정확도 + MAE."""
    dirCorrect = 0
    errors = []
    details = {}

    for sector in predicted:
        p = predicted[sector]
        a = actual[sector]
        err = abs(p - a)
        errors.append(err)

        dirMatch = (p > 0 and a > 0) or (p < 0 and a < 0) or (p == 0 and a == 0)
        if dirMatch:
            dirCorrect += 1

        details[sector] = {
            "predicted": p,
            "actual": a,
            "error": round(err, 1),
            "direction": "✓" if dirMatch else "✗",
        }

    dirAccuracy = dirCorrect / len(predicted) * 100
    mae = np.mean(errors)
    return round(dirAccuracy, 1), round(mae, 1), details


def main():
    startTime = time.time()

    print("=" * 70)
    print("  098-018: 거시 시나리오 가상환경 프로토타입")
    print("=" * 70)

    # 1. 실제 거시 조건으로 시나리오 예측 → 실제와 비교
    print("\n" + "=" * 70)
    print("  실제 거시 조건 → 탄성도 기반 예측 vs 실제 매출")
    print("=" * 70)

    yearSummary = {}

    for year, macro in ACTUAL_MACRO.items():
        predicted = predictFromScenario(macro["gdp"], macro["fx"])
        actual = ACTUAL_REVENUE[year]
        dirAcc, mae, details = evaluateScenario(predicted, actual)
        yearSummary[year] = {"dirAcc": dirAcc, "mae": mae, "label": macro["label"]}

        print(f"\n  [{year}] {macro['label']} (GDP={macro['gdp']:+.1f}%, FX={macro['fx']:+.1f}%)")
        print(f"  {'섹터':<14} {'예측':>8} {'실제':>8} {'오차':>8} {'방향':>4}")
        print(f"  {'─' * 44}")
        for sector in SECTOR_ELASTICITY:
            d = details[sector]
            print(f"  {sector:<14} {d['predicted']:>+8.1f} {d['actual']:>+8.1f} {d['error']:>8.1f} {d['direction']:>4}")
        print(f"  {'─' * 44}")
        print(f"  방향 정확: {dirAcc:.0f}% ({int(dirAcc * 8 / 100)}/8) | MAE: {mae:.1f}%p")

    # 2. 연도별 요약
    print(f"\n" + "=" * 70)
    print(f"  연도별 시나리오 성능 요약")
    print("=" * 70)
    print(f"\n  {'연도':<6} {'상황':<18} {'방향 정확':>10} {'MAE':>8}")
    print(f"  {'─' * 44}")
    avgDir = 0
    avgMae = 0
    for year, s in yearSummary.items():
        print(f"  {year:<6} {s['label']:<18} {s['dirAcc']:>9.0f}% {s['mae']:>7.1f}%p")
        avgDir += s["dirAcc"]
        avgMae += s["mae"]
    avgDir /= len(yearSummary)
    avgMae /= len(yearSummary)
    print(f"  {'─' * 44}")
    print(f"  {'평균':<6} {'':18} {avgDir:>9.0f}% {avgMae:>7.1f}%p")

    # 3. 프리셋 시나리오 → 예측 결과 미리보기
    print(f"\n" + "=" * 70)
    print(f"  프리셋 시나리오별 예측 매출 변동 (% 포인트)")
    print("=" * 70)

    sectors = list(SECTOR_ELASTICITY.keys())
    header = f"  {'시나리오':<12}" + "".join(f"{s:>10}" for s in sectors)
    print(f"\n{header}")
    print(f"  {'─' * (12 + 10 * len(sectors))}")

    for scenName, scenData in SCENARIOS.items():
        pred = predictFromScenario(scenData["gdp"], scenData["fx"])
        row = f"  {scenName:<12}"
        for s in sectors:
            row += f"{pred[s]:>+10.1f}"
        print(row)

    # 4. 가장 잘 맞는 시나리오 프리셋 찾기
    print(f"\n" + "=" * 70)
    print(f"  각 연도에 가장 잘 맞는 프리셋 시나리오")
    print("=" * 70)

    for year, actual in ACTUAL_REVENUE.items():
        bestScen = None
        bestMae = 999

        for scenName, scenData in SCENARIOS.items():
            pred = predictFromScenario(scenData["gdp"], scenData["fx"])
            _, mae, _ = evaluateScenario(pred, actual)
            if mae < bestMae:
                bestMae = mae
                bestScen = scenName

        macro = ACTUAL_MACRO[year]
        print(f"\n  {year} ({macro['label']})")
        print(f"  → 최적 프리셋: {bestScen} (MAE={bestMae:.1f}%p)")

        # 실제 거시 vs 프리셋 거시 비교
        scenData = SCENARIOS[bestScen]
        print(f"    프리셋: GDP={scenData['gdp']:+.1f}%, FX={scenData['fx']:+.1f}%")
        print(f"    실제:   GDP={macro['gdp']:+.1f}%, FX={macro['fx']:+.1f}%")

    # 5. 시나리오 도구의 한계와 가치 평가
    print(f"\n" + "=" * 70)
    print(f"  시나리오 도구 평가")
    print("=" * 70)

    print(f"""
  방향 정확도: {avgDir:.0f}% (3개년 평균)
  MAE: {avgMae:.1f}%p (3개년 평균)

  강점:
  - 사전 정의된 탄성도로 즉시 예측 (API 불필요)
  - 시나리오 비교가 직관적 (adverse vs baseline)
  - 경기민감주 방향 포착에 유용 (반도체/자동차/화학)

  한계:
  - 구조적 충격 포착 불가 (2020 코로나: IT +21.3% 예측 불가)
  - MAE {avgMae:.1f}%p → 점 추정 아닌 방향성 참고만 가능
  - 방어주(통신/식품) 탄성도 작아서 예측값 ≈ 0 (정보량 없음)
  - 섹터→기업 개별 변환 미지원 (015의 커버리지 12/168 문제 동일)
  """)

    elapsed = time.time() - startTime
    print(f"  소요시간: {elapsed:.1f}s")
    print("\n실험 완료.")


if __name__ == "__main__":
    main()
