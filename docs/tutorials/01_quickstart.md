---
title: "1. Quickstart"
---

# 1. Quickstart

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/01_quickstart.ipynb)

지금 DartLab의 첫 분석 흐름은 `sections -> show -> trace`다.

이 튜토리얼에서 다루는 내용:

- `Company` 생성
- `sections`로 회사 맵 보기
- `show("topic")`으로 payload 열기
- `trace("topic")`으로 source 확인
- source namespace 직접 접근

---

## Company 생성

```python
import dartlab

c = dartlab.Company("005930")
c.corpName
c.stockCode
```

회사명으로도 가능하다.

```python
c = dartlab.Company("카카오")
```

---

## 먼저 `sections`를 본다

```python
c.sections
```

`sections`는 회사의 canonical board다. 컬럼은 기간이고, row는 공시에서 정렬된 topic 구조다.

pure docs source가 필요하면:

```python
c.docs.sections
```

---

## topic을 연다

```python
c.show("BS")
c.show("companyOverview")
c.show("audit")
```

자주 쓰는 해석:

- `BS`, `IS`, `CF` 같은 숫자 topic은 `finance`
- `audit`, `dividend` 같은 정형 공시는 `report`
- `companyOverview`, `business` 같은 서술/섹션 topic은 `docs`

---

## source를 추적한다

```python
c.trace("BS")
c.trace("companyOverview")
c.trace("audit")
```

`trace(...)`는 그 topic이 실제로 어느 source에서 왔는지 설명한다.

---

## 공시 목록

```python
c.filings()
```

회사에 연결된 공시 목록과 기본 메타데이터를 확인할 수 있다.

---

## source namespace

필요하면 source를 직접 내려간다.

```python
c.docs.sections
c.docs.retrievalBlocks
c.docs.contextSlices

c.finance.BS
c.report.audit
```

하지만 공개 기본 흐름은 여전히 `sections -> show -> trace`다.

---

## 상태와 검색

```python
dartlab.Company.status()
dartlab.Company.search("반도체")
dartlab.Company.listing()
```

---

## 진행 표시 끄기

```python
import dartlab

dartlab.verbose = False
c = dartlab.Company("005930")
```

---

## 다음 단계

- [2. 재무제표 조회](./financial-statements)
- [API Overview](../api/overview)
