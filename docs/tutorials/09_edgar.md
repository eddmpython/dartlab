---
title: "9. US Stocks (EDGAR)"
---

# 9. US Stocks (EDGAR)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/09_edgar.ipynb)

DartLab은 한국 DART뿐 아니라 미국 SEC EDGAR도 같은 facade로 지원한다.

이 튜토리얼에서 다루는 내용:

- EDGAR `Company` 생성
- `sections`로 10-K / 10-Q 구조 보기
- `show()`로 재무 및 서술형 topic 열기
- `trace()`로 source 확인
- `OpenEdgar`로 raw public API 접근

---

## EDGAR Company 생성

```python
import dartlab

c = dartlab.Company("AAPL")
c.corpName
c.ticker
c.market
```

---

## 먼저 `sections`를 본다

```python
c.sections
c.docs.sections
```

EDGAR도 DART와 마찬가지로 `sections` 중심 흐름을 쓴다.

- `c.sections`: 공개 company board
- `c.docs.sections`: pure docs source

---

## 재무제표 조회

```python
c.show("BS")
c.show("IS")
c.show("CF")
```

EDGAR의 숫자 topic은 SEC XBRL 기반 `finance` layer가 담당한다.

---

## 10-K / 10-Q 서술형 섹션

```python
c.show("10-K::item1Business")
c.show("10-K::item1ARiskFactors")
c.show("10-K::item7MDandA")
```

EDGAR 서술형 topic은 docs 구조 위에서 연다. 텍스트와 테이블을 억지로 별도 public contract로 설명하기보다, topic payload를 그대로 연다고 이해하면 된다.

---

## source 추적

```python
c.trace("BS")
c.trace("10-K::item1ARiskFactors")
```

`trace()`는 해당 topic이 어떤 source에서 왔는지와 provenance를 보여준다.

---

## OpenEdgar

source-native public API wrapper가 필요하면 `OpenEdgar`를 쓴다.

```python
from dartlab import OpenEdgar

e = OpenEdgar()

e.company("AAPL")
e.filings("AAPL", forms=["10-K"])
e.companyFactsJson("AAPL")
```

이 계층은 SEC 공개 API surface를 최대한 그대로 유지한다.

---

## 현재 상태

EDGAR Company는 계속 개선 중이다.

- `sections -> show -> trace` 흐름은 이미 공유한다
- `report`는 DART처럼 풍부한 공식 API 계층이 아니라 제한적이다
- OpenAPI와 저장 parquet는 DartLab runtime과 호환되게 맞춘다

---

## 다음 단계

- [1. Quickstart](./quickstart)
- [API Overview](../api/overview)
