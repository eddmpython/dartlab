"""실험 ID: 096-002
실험명: 횡단면 회귀 실데이터 적합 + 예측 정확도 검증

목적:
- 실제 DART finance 데이터로 횡단면 회귀를 적합하고 예측력(R²) 확인
- 패널 회귀(기업 고정효과) 대비 개선 확인
- 메모리 안전 + 속도 확인

가설:
1. R² > 0.10이면 유의미 (매출 성장률은 잡음이 많으므로 높은 R² 기대 어려움)
2. PER/PBR/영업이익률/전년 성장률이 유의 변수
3. 패널 회귀(기업 고정효과)가 횡단면보다 R² 높음

방법:
1. 대형주 20개의 finance timeseries 로드
2. 연도별 매출 성장률 + 재무 변수 추출 → CompanyFeatures 생성
3. 횡단면 회귀 적합 → R², 계수, 유의성 확인
4. 패널 회귀 적합 → R², 기업별 절편 확인
5. 개별 기업 예측 vs 실제 비교

결과:
- 16개 기업(금융 4개 제외) × 578개 관측치 로드 (11.3초)
- 횡단면 회귀: R²=0.0000, adjR²=-0.030 (설명력 사실상 없음)
- 패널 회귀(FE): R²=0.0358, 16개 기업, 고정효과 범위 -136%~-122%
- 패널에서 유의 변수: lnMarketCap(+5.00), capexRatio(+0.35), revenueGrowthLag(-0.18)
- OLS 엔진 자체는 정상 작동 (14ms/5ms), 특이행렬 없이 수렴

결론:
- 가설1 기각: R²<0.10 — proxy 변수(IS 역산 PER/PBR/외국인비율)가 opMargin과 완전 상관
  → 실제 시장 데이터(Gather.price, Gather.flow)가 필수
- 가설2 부분 채택: revenueGrowthLag(-0.18)만 경제적 의미 있음 (평균회귀)
- 가설3 채택: 패널(R²=0.036) > 횡단면(R²=0.000) — 기업 고정효과 존재
- 핵심 교훈: crossRegression 엔진 코드는 정상이나, 프로덕션 투입 시
  반드시 Gather 실시간 데이터(PER/PBR/시가총액/외국인비율)를 피처로 써야 함
- 고정효과 값이 비현실적(-130%대) → lnMarketCap proxy(=ln매출)가 원인,
  실제 시가총액으로 대체 시 정상화 예상

실험일: 2026-03-25
"""

import math
import time

import dartlab
from dartlab.engines.analysis.analyst.crossRegression import (
    CompanyFeatures,
    fitCrossSection,
    fitPanel,
)
from dartlab.engines.common.finance.extract import getAnnualValues, getTTM

# 대형주 20개 (메모리 안전: 순차 로드 + 즉시 해제)
STOCKS = [
    ("005930", "삼성전자", "반도체"),
    ("000660", "SK하이닉스", "반도체"),
    ("005380", "현대차", "자동차"),
    ("000270", "기아", "자동차"),
    ("035420", "NAVER", "IT/소프트웨어"),
    ("035720", "카카오", "IT/소프트웨어"),
    ("051910", "LG화학", "화학"),
    ("006400", "삼성SDI", "전기전자"),
    ("003550", "LG", "지주"),
    ("105560", "KB금융", "금융/은행"),
    ("055550", "신한지주", "금융/은행"),
    ("012330", "현대모비스", "자동차"),
    ("028260", "삼성물산", "건설"),
    ("034730", "SK", "지주"),
    ("066570", "LG전자", "전기전자"),
    ("032830", "삼성생명", "금융/보험"),
    ("018260", "삼성에스디에스", "IT/소프트웨어"),
    ("010130", "고려아연", "비철금속"),
    ("011200", "HMM", "해운"),
    ("086790", "하나금융지주", "금융/은행"),
]


def extractFeatures(code: str, name: str, sector: str) -> list[CompanyFeatures]:
    """단일 기업에서 연도별 CompanyFeatures 추출."""
    try:
        c = dartlab.Company(code)
    except Exception as e:
        print(f"  ❌ {name}: Company 로드 실패 — {e}")
        return []

    tsRaw = c.finance.timeseries
    series = tsRaw[0] if isinstance(tsRaw, tuple) else tsRaw
    if not series or "IS" not in series:
        print(f"  ❌ {name}: timeseries 없음")
        return []

    # 연도별 매출 추출
    salesVals = getAnnualValues(series, "IS", "sales")
    if not salesVals:
        salesVals = getAnnualValues(series, "IS", "revenue")
    if not salesVals:
        print(f"  ❌ {name}: 매출 시계열 없음")
        return []

    opVals = getAnnualValues(series, "IS", "operating_profit")
    if not opVals:
        opVals = getAnnualValues(series, "IS", "operating_income")

    features: list[CompanyFeatures] = []

    # 연도별 매출 성장률 계산 (최소 2년 필요)
    for i in range(1, len(salesVals)):
        curSales = salesVals[i]
        prevSales = salesVals[i - 1]
        if curSales is None or prevSales is None or prevSales <= 0 or curSales <= 0:
            continue

        growth = (curSales / prevSales - 1) * 100

        # 전전년 성장률 (lag)
        lagGrowth = 0.0
        if i >= 2 and salesVals[i - 2] is not None and salesVals[i - 2] > 0:
            lagGrowth = (prevSales / salesVals[i - 2] - 1) * 100

        # 영업이익률
        opMargin = 0.0
        if opVals and i < len(opVals) and opVals[i] is not None and curSales > 0:
            opMargin = opVals[i] / curSales * 100

        # 시가총액: ln(매출) proxy, PER: 영업이익률 기반 proxy
        lnMktCap = math.log(curSales) if curSales > 0 else 20.0
        perProxy = curSales / opVals[i] if (opVals and i < len(opVals) and opVals[i] and opVals[i] > 0) else 15.0
        perProxy = min(max(perProxy, 3.0), 100.0)

        # PBR: 영업이익률 연동 proxy
        pbrProxy = 1.0 + opMargin / 20.0  # 마진 높을수록 PBR 높음

        # 부채비율: IS 구조 proxy (매출 대비 비용 비율)
        costRatio = 100.0 - opMargin  # 간접 proxy

        features.append(CompanyFeatures(
            stockCode=code,
            year=2020 + i,  # proxy 연도
            sector=sector,
            revenueGrowth=growth,
            per=perProxy,
            pbr=pbrProxy,
            lnMarketCap=lnMktCap,
            operatingMargin=opMargin,
            capexRatio=5.0 + opMargin * 0.1,  # 약간의 변동
            debtRatio=costRatio,
            foreignHoldingRatio=20.0 + opMargin * 0.5,  # 수익성 좋으면 외국인 비율 높음 proxy
            revenueGrowthLag=lagGrowth,
        ))

    print(f"  ✅ {name}: {len(features)}개 관측치")
    return features


if __name__ == "__main__":
    print("=" * 60)
    print("  횡단면/패널 회귀 실데이터 검증")
    print("=" * 60)

    allFeatures: list[CompanyFeatures] = []
    t0 = time.time()

    for code, name, sector in STOCKS:
        feats = extractFeatures(code, name, sector)
        allFeatures.extend(feats)
        # 메모리: Company 객체는 함수 리턴 시 자동 해제

    tLoad = time.time() - t0
    print(f"\n총 관측치: {len(allFeatures)}, 로드 시간: {tLoad:.1f}s")

    if len(allFeatures) < 30:
        print("관측치 부족 — 실험 중단")
    else:
        # 횡단면 회귀
        print(f"\n{'='*60}")
        print("  1. 횡단면 회귀 (Cross-Section)")
        print(f"{'='*60}")
        t1 = time.time()
        csModel = fitCrossSection(allFeatures, minObs=20)
        tFit = time.time() - t1
        if csModel:
            print(f"  R²: {csModel.rSquared:.4f}")
            print(f"  adj R²: {csModel.adjRSquared:.4f}")
            print(f"  관측치: {csModel.nObs}")
            print(f"  섹터 더미: {csModel.sectorNames}")
            print(f"  적합 시간: {tFit*1000:.0f}ms")

            # 계수 출력
            from dartlab.engines.analysis.analyst.crossRegression import FEATURES
            names = ["intercept"] + FEATURES + csModel.sectorNames
            for i, (name, coef) in enumerate(zip(names, csModel.coefficients)):
                print(f"    {name:30s}: {coef:+.4f}")

            if csModel.warnings:
                for w in csModel.warnings:
                    print(f"  ⚠️ {w}")

            # 개별 예측
            print(f"\n  [예측 샘플]")
            for feat in allFeatures[:5]:
                pred = csModel.predict(feat.toFeatureDict(), feat.sector)
                if pred is not None:
                    err = feat.revenueGrowth - pred
                    print(f"    {feat.stockCode} actual={feat.revenueGrowth:+.1f}% pred={pred:+.1f}% err={err:+.1f}%p")
        else:
            print("  ❌ 횡단면 회귀 적합 실패")

        # 패널 회귀
        print(f"\n{'='*60}")
        print("  2. 패널 회귀 (Fixed Effects)")
        print(f"{'='*60}")
        t2 = time.time()
        panelModel = fitPanel(allFeatures, minObs=20, minYears=2)
        tPanel = time.time() - t2
        if panelModel:
            print(f"  R²: {panelModel.rSquared:.4f}")
            print(f"  관측치: {panelModel.nObs}")
            print(f"  기업 수: {panelModel.nFirms}")
            print(f"  적합 시간: {tPanel*1000:.0f}ms")
            print(f"  전체 평균 성장률: {panelModel.grandMean:.1f}%")

            # 계수
            for i, (name, coef) in enumerate(zip(panelModel.featureNames, panelModel.coefficients)):
                print(f"    {name:30s}: {coef:+.4f}")

            # 기업별 고정효과 (상위 5개)
            print(f"\n  [기업 고정효과 — 상위 5개]")
            sorted_fi = sorted(panelModel.firmIntercepts.items(), key=lambda x: x[1], reverse=True)
            for code, alpha in sorted_fi[:5]:
                stockName = next((n for c, n, s in STOCKS if c == code), code)
                print(f"    {stockName:15s}: {alpha:+.1f}%")

            # 예측
            print(f"\n  [예측 샘플]")
            for feat in allFeatures[:5]:
                pred = panelModel.predict(feat.stockCode, feat.toFeatureDict())
                if pred is not None:
                    err = feat.revenueGrowth - pred
                    print(f"    {feat.stockCode} actual={feat.revenueGrowth:+.1f}% pred={pred:+.1f}% err={err:+.1f}%p")
        else:
            print("  ❌ 패널 회귀 적합 실패")

    print(f"\n실험 완료.")
