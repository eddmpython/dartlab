---
title: API Overview
---

# API Overview

DartLab의 현재 공개 Company 흐름은 `index -> show(topic) -> trace(topic)` 이다.  
먼저 회사 구조를 보고, 필요한 topic을 열고, 마지막에 그 값이 `docs`, `finance`, `report` 중 어디에서 왔는지 확인한다.

## Company 생성

```python
import dartlab

c = dartlab.Company("005930")
c = dartlab.Company("삼성전자")

c.corpName
c.stockCode
```

데이터가 로컬에 없으면 GitHub Releases에서 자동 다운로드한다.

## 현재 공개 surface

```python
c.index
c.show("BS")
c.trace("dividend")
```

- `c.index`: 회사 구조 인덱스 DataFrame
- `c.show(topic)`: topic payload 반환
- `c.trace(topic)`: source provenance 반환

`profile`은 이번 기준에서 공개 기능이 아니다. 향후에는 terminal/notebook에서 문서처럼 읽고, 변화 지점을 먼저 파악할 수 있는 회사 보고서 뷰로 확장될 예정이다.

## index

`c.index`는 회사에 어떤 데이터가 있는지 먼저 보여주는 인덱스다.

대표 컬럼:

- `chapter`
- `topic`
- `label`
- `kind`
- `source`
- `periods`
- `shape`
- `preview`

```python
c.index
```

이 표를 통해:

- 어떤 topic이 있는지
- 어떤 source가 현재 authoritative 인지
- payload가 DataFrame인지 notice인지
- 시계열 범위가 어느 정도인지

를 먼저 파악한다.

`docs`가 없는 회사는 `docsStatus` row가 추가되고 `현재 사업보고서 부재` preview가 나타난다.

## show(topic)

`c.show(topic)`는 topic의 실제 payload를 연다.

```python
c.show("BS")
c.show("audit")
c.show("companyOverview")
```

- 재무/정형 공시 topic은 DataFrame이 바로 반환된다.
- 텍스트 topic은 읽기 쉬운 형태로 정리된 DataFrame이 반환된다.
- `raw=True`를 주면 원본 wide view에 더 가까운 payload를 볼 수 있다.

```python
c.show("companyOverview", raw=True)
```

## trace(topic)

`c.trace(topic)`는 같은 topic에서 어떤 source가 최종적으로 선택됐는지 설명한다.

```python
c.trace("BS")
c.trace("dividend")
c.trace("companyOverview")
```

예상 흐름:

- `BS` -> `finance`
- `dividend` -> `report`
- `companyOverview` -> `docs`

## source namespace

공개 메인 플로우는 `index/show/trace`지만, 필요하면 source namespace로 직접 내려갈 수 있다.

```python
c.docs.sections
c.finance.BS
c.report.dividend
```

- `docs`: 공시 텍스트 원천
- `finance`: authoritative 재무제표/시계열
- `report`: authoritative 정형 공시

## 정적 메서드

```python
dartlab.Company.search("삼성")
dartlab.Company.listing()
dartlab.Company.status()
```

- `search(query)`: 종목 검색
- `listing()`: 전체 상장기업 목록
- `status()`: 로컬 데이터 보유 현황

## CLI 대응

현재 CLI에서도 같은 철학을 사용한다.

```bash
uv run dartlab profile 005930
uv run dartlab profile 005930 --show BS
uv run dartlab profile 005930 --trace dividend
```

- 기본: `index`
- `--show`: topic payload
- `--trace`: source trace

## Roadmap

- `profile`: 변화 지점 중심의 company report view로 확장 예정
- `Compare`: 같은 철학으로 UX 개선 예정
- `EDGAR Company`: DART Company와 같은 수준의 Company-style surface로 정렬 예정


