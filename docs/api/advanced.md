---
title: 고급 기능
---

# 고급 기능

Insight 등급, 시장 순위, 섹터 분류, 기술적 분석.

## Insight 등급

7개 영역을 A~F로 평가한다.

```python
c = dartlab.Company("005930")
c.insights                              # 7영역 등급 카드

# 영역: 실적, 수익성, 재무건전성, 현금흐름, 지배구조, 예측가능성, 핵심이익
```

## 시장 순위

```python
c.rank                                  # 시장 내 순위
# RankInfo: 매출 2/3000위, 섹터 1/45위, sizeClass="large"
```

## 섹터 분류

WICS 11개 대분류 + 30개 중분류로 자동 분류.

```python
c.sector
# SectorInfo(IT/반도체와반도체장비, conf=1.00)

c.sectorParams
# SectorParams(discountRate=0.10, perMultiple=18.5, ...)
```

## 기술적 분석 (Quant)

```python
c = dartlab.Company("005930")
q = c.quant()                           # 25개 지표, 9개 신호

# 또는 루트 함수
dartlab.quant("005930")
```

25개 기술 지표 (RSI, MACD, 볼린저밴드 등) + 9개 매매 신호 + 종합 판단.

## OpenAPI

DART/EDGAR 원시 API 직접 접근.

```python
# OpenDART
od = dartlab.OpenDart()
od.company("005930")                   # 기업 기본정보
od.disclosure(corpCode="00126380")     # 공시 목록

# FRED
fred = dartlab.Fred()
fred.series("DGS10")                   # 미국 10년 국채수익률
```
