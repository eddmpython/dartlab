---
title: Scan (횡단분석)
---

# Scan — 전종목 횡단분석

`scan()` 하나로 시장 전체를 한 번에 비교한다.

## 사용법

```python
import dartlab

# 루트 함수
dartlab.scan("governance")              # 전종목 지배구조
dartlab.scan("governance", "all")       # 전체 상장사

# Company-bound
c = dartlab.Company("005930")
c.governance()                          # 이 회사 1행
c.governance("all")                     # 전체 비교
c.debt()                                # 부채 구조
c.workforce()                           # 인력 분석
c.capital()                             # 주주환원
```

## 주요 축

| 축 | 설명 | 핵심 지표 |
|------|------|---------|
| governance | 지배구조 5축 100점 | 대주주 지분, 사외이사, 경영진 보상, 감사의견 |
| workforce | 인력/급여 | 종업원수, 1인당부가가치, 급여매출괴리 |
| capital | 주주환원 | 배당, 자사주, 환원형/중립/희석형 분류 |
| debt | 부채 구조 | 사채잔액, ICR, 위험등급 |
| network | 관계 네트워크 | 계열사, 주요 거래처 |
| signal | 키워드 트렌드 | 공시 키워드 연도별 추세 |
| disclosureRisk | 공시 리스크 | 우발부채, 리스크 키워드, 감사변경 |

## 계정/비율 횡단 조회

```python
# 특정 계정 전종목 조회
dartlab.scan("account", "영업이익")     # 전종목 영업이익 비교

# 특정 비율 전종목 조회
dartlab.scan("ratio", "roe")            # 전종목 ROE 비교
```

## 시장 지수

```python
dartlab.gather("price", "KOSPI")        # 코스피 지수
dartlab.gather("price", "KOSDAQ")       # 코스닥 지수
```
