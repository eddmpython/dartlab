---
title: "9. US Stocks (EDGAR)"
---

# 9. US Stocks (EDGAR)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/09_edgar.ipynb)

DartLab은 한국 DART뿐 아니라 미국 SEC EDGAR도 같은 facade로 지원한다. 이 튜토리얼에서 다루는 내용은 다음과 같다.

- EDGAR Company 생성
- `index`로 사용 가능한 데이터 확인
- 재무제표 조회 (BS, IS, CF)
- 10-K 서술형 섹션 조회
- `docs.sections` — 10-K/10-Q 수평화
- 재무비율
- DART Company와의 비교

---

## EDGAR Company 생성

미국 종목은 티커로 생성한다. DartLab이 자동으로 EDGAR 엔진을 선택한다.

```python
import dartlab

c = dartlab.Company("AAPL")
c.corpName    # "Apple Inc."
c.ticker      # "AAPL"
c.market      # "US"
```

## index — 사용 가능한 데이터 확인

`c.index`는 DART Company와 동일한 8컬럼 구조를 반환한다.

```python
c.index
```

| 컬럼 | 설명 |
|------|------|
| `chapter` | 대분류 |
| `topic` | 데이터 항목 |
| `label` | 표시 이름 |
| `kind` | finance / docs |
| `source` | 데이터 원천 |
| `periods` | 시계열 범위 |
| `shape` | 데이터 크기 |
| `preview` | 미리보기 |

## 재무제표 조회

DART Company와 동일한 shortcut property로 접근한다.

```python
c.BS    # Balance Sheet
c.IS    # Income Statement
c.CF    # Cash Flow Statement
```

`show()`로도 동일하게 접근 가능하다.

```python
c.show("BS")
```

## 10-K 서술형 섹션

10-K, 10-Q 보고서의 서술형 섹션도 `show()`로 조회한다.

```python
result = c.show("riskFactors")
result.text    # 서술문 DataFrame
result.table   # 테이블 DataFrame (있는 경우)
```

`show()`는 공시 topic에 대해 `ShowResult(text, table)` 을 반환한다. 텍스트와 테이블이 분리되어 있어서 필요한 부분만 선택할 수 있다.

주요 topic:

| topic | 설명 |
|-------|------|
| `riskFactors` | 위험 요인 (Item 1A) |
| `mdna` | 경영진 토의 및 분석 (Item 7) |
| `financialStatements` | 재무제표 및 주석 (Item 8) |
| `controls` | 내부 통제 (Item 9A) |
| `legalProceedings` | 법적 절차 (Item 3) |

## docs.sections — 10-K/10-Q 수평화

`docs.sections`는 모든 10-K/10-Q 섹션을 기간별로 수평 정렬한 DataFrame이다.

```python
c.docs.sections
```

DART의 사업보고서 수평화와 동일한 개념이다. 컬럼이 기간(연도)이고, 행이 topic이다. `blockType` 컬럼으로 텍스트와 테이블을 구분한다.

## 재무비율

```python
c.ratios
```

DART Company와 동일한 비율 체계를 제공한다.

## source 추적

```python
c.trace("BS")
c.trace("riskFactors")
```

`trace()`는 해당 topic의 데이터가 어떤 source에서 왔는지 메타데이터를 반환한다.

## DART Company와의 비교

| 항목 | DART | EDGAR |
|------|------|-------|
| 생성 | `Company("005930")` | `Company("AAPL")` |
| index/show/trace | 동일 | 동일 |
| docs.sections | 사업보고서 수평화 | 10-K/10-Q 수평화 |
| finance.BS/IS/CF | XBRL 재무제표 | SEC XBRL 재무제표 |
| report namespace | 28개 API 체계 | 없음 |
| notes | K-IFRS 주석 12항목 | 없음 |
| ShowResult | text/table 분리 | text/table 분리 |

## 현재 제한사항

EDGAR Company는 현재 Beta (Tier 2) 단계다.

- `report` namespace 없음 — SEC에는 DART 정기보고서 API에 대응하는 구조가 없다
- `notes` namespace 없음
- docs 데이터 커버리지가 아직 전체 대비 제한적이다
- 재무 데이터는 연간(annual) 기준이다 (분기별 시계열은 DART만 해당)

---

## 다음 단계

- [1. Quickstart](./quickstart) — DART 기업 분석 시작
- [API Overview](../api/overview) — 전체 API 구조
