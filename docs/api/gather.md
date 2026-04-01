---
title: Gather (시장 데이터)
---

# Gather — 외부 시장 데이터

공시 데이터와 시장 데이터를 연결한다.

## 사용법

```python
import dartlab

# 루트 함수
dartlab.gather("price", "005930")       # 주가 OHLCV
dartlab.gather("flow", "005930")        # 외국인/기관 수급
dartlab.gather("macro")                 # 거시지표
dartlab.gather("news", "삼성전자")       # 뉴스

# Company-bound
c = dartlab.Company("005930")
c.gather("price")                      # 종목코드 자동 바인딩
c.gather("flow")
```

## 4축

| 축 | 소스 | 데이터 |
|------|------|------|
| price | Naver/Yahoo | OHLCV 시계열 |
| flow | Naver/KRX | 외국인/기관 수급 |
| macro | FRED/ECOS | 거시지표 (금리, 환율, CPI) |
| news | Google News | 뉴스 검색 |

## 시장 지수

```python
dartlab.gather("price", "KOSPI")        # 코스피 지수
dartlab.gather("price", "코스닥")        # 코스닥 지수
dartlab.gather("price", "KPI200")       # 코스피200
```

## 웹/뉴스 검색

```python
from dartlab.gather.search import webSearch, newsSearch

webSearch("삼성전자 HBM 수요")           # 웹 검색
newsSearch("반도체 업황", days=7)         # 최근 7일 뉴스
```
