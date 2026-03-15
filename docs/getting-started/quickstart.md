---
title: 빠른 시작
---

# 빠른 시작

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb)

DartLab의 현재 시작 흐름은 간단하다.

1. `dartlab.Company("005930")` 로 회사를 만든다.
2. `c.index` 로 어떤 데이터가 있는지 본다.
3. `c.show("topic")` 으로 실제 내용을 연다.
4. `c.trace("topic")` 으로 source를 확인한다.

## 설치

```bash
uv add dartlab
```

> Python이 없어도 괜찮다. uv가 자동으로 설치하고 가상환경까지 만든다.

## Company 생성

```python
import dartlab

c = dartlab.Company("005930")
c.corpName
c.stockCode
```

회사명으로도 만들 수 있다.

```python
c = dartlab.Company("카카오")
```

미국 종목도 같은 facade로 생성한다. 티커 형식에 따라 DART/EDGAR가 자동 결정된다.

```python
c = dartlab.Company("AAPL")   # US stock — auto-detected
c.corpName  # "Apple Inc."
c.ticker    # "AAPL"
```

## 먼저 index를 본다

```python
c.index
```

`index`는 회사 전체 구조를 먼저 보여주는 DataFrame이다.

- 어떤 topic이 있는지
- 어떤 source를 쓰는지
- 시계열 범위가 어느 정도인지
- payload가 어떤 형태인지

를 한눈에 본다.

## topic을 연다

```python
c.show("BS")
c.show("audit")
c.show("companyOverview")
```

- 재무제표와 정형 공시는 DataFrame으로 바로 본다.
- 텍스트 topic은 `ShowResult(text, table)` 로 반환된다 — 텍스트와 테이블이 분리되어 있다.
- 원본에 가까운 형태가 필요하면 `raw=True`를 사용한다.

```python
result = c.show("companyOverview")
result.text    # 서술문 DataFrame
result.table   # 테이블 DataFrame
```

```python
c.show("companyOverview", raw=True)
```

## source를 추적한다

```python
c.trace("BS")
c.trace("dividend")
c.trace("companyOverview")
```

이 단계에서:

- `BS`는 대체로 `finance`
- `dividend`는 대체로 `report`
- `companyOverview`는 대체로 `docs`

가 선택된다는 것을 확인할 수 있다.

## docs가 없는 회사

사업보고서 docs가 아직 없는 회사도 있을 수 있다.

```python
c.index
c.show("docsStatus")
```

이 경우 `index`에는 `docsStatus` row가 추가되고, `show("docsStatus")` 는 `현재 사업보고서 부재` 안내를 반환한다.

## 재무제표 shortcut

기존 shortcut property도 그대로 쓸 수 있다.

```python
c.BS
c.IS
c.CIS
c.CF
c.SCE
```

## source namespace

원천 데이터 계층으로 직접 내려가고 싶다면 namespace를 쓴다.

```python
# DART Company (KR)
c.docs.sections      # 사업보고서 수평화
c.finance.BS         # XBRL 재무제표
c.report.dividend    # 정기보고서 정형 공시
```

EDGAR Company도 같은 namespace 구조를 따른다.

```python
# EDGAR Company (US)
us = dartlab.Company("AAPL")
us.docs.sections     # 10-K/10-Q sections
us.finance.BS        # SEC XBRL financials
```

## CLI

CLI도 같은 흐름이다.

```bash
uv run dartlab profile 005930
uv run dartlab profile 005930 --show BS
uv run dartlab profile 005930 --trace dividend
```

## 앞으로의 profile

`profile`은 지금 공개 메인 기능이 아니다. 앞으로는 다음 목표로 확장된다.

- terminal/notebook에서 문서처럼 읽는 company report
- 변하지 않는 텍스트 반복보다 변화 지점을 먼저 보여주는 뷰
- `index/show/trace` 위에 올라가는 상위 렌더 레이어

## 다음 단계

- [설치](./installation)
- [API Overview](../api/overview)
- [튜토리얼](../tutorials/index.md)


