---
title: 재무 데이터
---

# 재무 데이터

재무제표(BS/IS/CF) + 47개 비율 + 시계열 + 계정 표준화.

## 재무제표

```python
c = dartlab.Company("005930")

c.BS                    # 재무상태표 (자산/부채/자본)
c.IS                    # 손익계산서 (매출/영업이익/순이익)
c.CF                    # 현금흐름표 (영업/투자/재무)
c.CIS                   # 포괄손익계산서
c.SCE                   # 자본변동표
```

## 특정 계정 추출 — select

```python
# 특정 계정만 추출
c.select("IS", ["매출액", "영업이익", "당기순이익"])

# 기간 필터
c.select("BS", ["자산총계"], period=["2023", "2024"])

# 차트 시각화
c.select("IS", ["매출액"]).chart()

# dict 변환
c.select("IS", ["매출액", "영업이익"]).toDict()
```

## 재무비율 — ratios

47개 비율을 한 번에 산출한다.

```python
r = c.ratios

# 수익성
r.roe                   # ROE (%)
r.roa                   # ROA (%)
r.operatingMargin       # 영업이익률 (%)
r.netMargin             # 순이익률 (%)
r.ebitdaMargin          # EBITDA 마진 (%)

# 안정성
r.debtRatio             # 부채비율 (%)
r.currentRatio          # 유동비율 (%)
r.interestCoverage      # 이자보상배율 (배)
r.netDebtRatio          # 순차입금비율 (%)

# 성장성
r.revenueGrowth         # 매출 성장률 (%)
r.operatingProfitGrowth # 영업이익 성장률 (%)

# 효율성
r.totalAssetTurnover    # 총자산회전율
r.inventoryTurnover     # 재고자산회전율
r.ccc                   # Cash Conversion Cycle (일)

# 현금흐름
r.fcf                   # Free Cash Flow
r.operatingCfMargin     # 영업CF 마진 (%)

# 부실 예측
r.altmanZScore          # Altman Z-Score
r.ohlsonProbability     # Ohlson 부도확률 (%)
r.beneishMScore         # Beneish M-Score (이익 조작)
r.piotroskiFScore       # Piotroski F-Score (0-9)

# 주당/밸류에이션
r.eps                   # EPS
r.bps                   # BPS
r.per                   # PER
r.pbr                   # PBR
```

## 비율 시계열

```python
series, periods = c.ratioSeries
# series: {비율명: {기간: 값}} dict
# periods: ["2024", "2023", "2022", ...] 기간 목록

# 예: ROE 5개년 추이
for p in periods[:5]:
    print(f"{p}: ROE {series['roe'].get(p)}%")
```

## 계정 표준화

2,700+ 상장사의 재무제표는 같은 개념이라도 다른 계정명을 사용한다.

```
ifrs-full_Revenue          → 삼성전자
dart_OperatingIncomeLoss   → LG화학
dart_ConstructionRevenue   → 현대건설
```

dartlab은 7단계 매핑 파이프라인으로 이를 **하나의 `매출액`**으로 통일한다.
15,850,000행 중 **98.7%**가 표준 계정에 매핑된다.

## EDGAR 호환

```python
us = dartlab.Company("AAPL")

us.BS                       # US-GAAP Balance Sheet
us.select("IS", ["매출액"])   # 한국어로 질의 → 자동 번역
us.select("IS", ["revenue"]) # 영문으로도 가능
```
