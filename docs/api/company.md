---
title: Company
---

# Company

종목코드 하나로 기업의 모든 데이터에 접근한다.

## 생성

```python
import dartlab

c = dartlab.Company("005930")       # 종목코드
c = dartlab.Company("삼성전자")      # 회사명
us = dartlab.Company("AAPL")        # EDGAR (미국)
```

## 데이터 조회 — show / select

```python
# show: 특정 토픽의 전체 데이터
c.show("BS")                        # 재무상태표
c.show("사업의내용")                  # 사업보고서 텍스트
c.show("IS", period="2024")         # 기간 필터
c.show("IS", period=["2023", "2024"])  # 세로 비교

# select: 행/열 필터
c.select("IS", ["매출액", "영업이익"])           # 특정 계정만
c.select("IS", ["매출액"]).chart()               # 차트
c.select("IS", ["매출액", "영업이익"]).toDict()   # dict 변환
```

**성능**: show/select는 해당 토픽만 부분 빌드 — 0.01~0.65초.

## 재무제표 바로가기

```python
c.BS                    # 재무상태표
c.IS                    # 손익계산서
c.CF                    # 현금흐름표
c.CIS                   # 포괄손익계산서
c.ratios                # 47개 재무비율
c.ratioSeries           # 비율 시계열
c.timeseries            # 분기별 시계열
```

## 주석 (Notes) 접근

재무제표 주석은 BS/IS 총액 뒤의 **항목별 분해** 데이터다.

```python
c.notes.borrowings      # 차입금 상세 (이자율, 만기, 담보)
c.notes.inventory       # 재고자산 분해
c.notes.provisions      # 충당부채
c.notes.segments        # 부문별 매출/이익
c.notes.tangibleAsset   # 유형자산 변동
c.notes.lease           # 리스부채
c.notes.eps             # 주당이익 분해
c.notes.costByNature    # 비용 성격별 분류
```

## 4 Namespace

```python
c.docs      # 원문 (사업보고서 텍스트)
c.finance   # 숫자 (IS/BS/CF, ratios)
c.report    # 정형 공시 (DART 전용)
c.profile   # 통합 (위 3개 병합)
```

## 탐색/추적

```python
c.sections              # 전체 토픽 지도 (topic × period)
c.topics                # 토픽 목록
c.index                 # 인덱스
c.trace("BS")           # 출처 추적 (docs/finance/report 중 어디서)
c.diff()                # 기간간 텍스트 변화 감지
c.filings()             # 공시 목록
```

## 메타 정보

```python
c.corpName              # 회사명
c.stockCode             # 종목코드
c.market                # 시장 (KOSPI/KOSDAQ/NYSE 등)
c.currency              # 통화 (KRW/USD)
c.sector                # 업종 분류 (WICS)
c.rank                  # 시장 순위
```

## 분석 엔진 접근

```python
c.analysis("financial", "수익성")   # 14축 재무분석
c.credit()                         # dCR 신용평가
c.review("수익성")                  # 보고서
c.gather("price")                  # 주가
c.ask("이 회사 분석해줘")            # AI
```
