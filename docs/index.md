---
title: DartLab
---

# DartLab

DART 전자공시 문서에서 재무제표, 주석, 정기보고서, 텍스트를 파싱하고 시계열로 정렬하는 Python 라이브러리.

종목코드 하나면 된다. 40개 분석 모듈이 공시 원문에서 구조화된 데이터를 추출한다. yfinance처럼 property 한 줄로 DataFrame을 바로 받는다.

한국 상장사 2,700+개는 같은 경제적 개념에 대해 회사마다 다른 XBRL 계정ID와 계정명을 사용한다. DartLab은 7단계 매핑 파이프라인과 34,000+개의 학습된 동의어를 통해 자체 통합 계정 체계를 구축했다. 전체 1,585만 행 중 **98.7%**가 표준 계정으로 매핑되어, 어떤 두 기업이든 동일한 키로 직접 비교할 수 있다.

```python
import dartlab

c = dartlab.Company("005930")

c.index             # company structure index
c.show("BS")        # topic payload
c.trace("dividend") # source trace
c.BS                # 재무상태표 DataFrame
c.CIS               # 포괄손익계산서 DataFrame
c.SCE               # 자본변동표
c.dividend          # 배당 시계열 DataFrame
```

## 무엇을 할 수 있나

| 분류 | property | 설명 |
|------|----------|------|
| Company 탐색 | `c.index`, `c.show("...")`, `c.trace("...")` | 회사 구조를 먼저 보고, 필요한 topic을 열고, source를 추적 |
| 재무제표 | `c.BS`, `c.IS`, `c.CIS`, `c.CF`, `c.SCE` | 재무상태표, 손익계산서, 포괄손익계산서, 현금흐름표, 자본변동표 |
| K-IFRS 주석 | `c.notes.inventory`, `c.notes.borrowings` 등 12개 | 재고자산, 차입금, 리스, 충당부채 등 |
| 정기보고서 | `c.dividend`, `c.employee`, `c.majorHolder` 등 26개 | 배당, 직원, 최대주주, 감사, 임원 등 |
| 공시 텍스트 | `c.docs.sections`, `c.retrievalBlocks`, `c.contextSlices` | 수평화 source, 원문 markdown block, LLM slice |

전체 모듈 40개. 데이터가 로컬에 없으면 GitHub Releases에서 자동 다운로드한다.

## 핵심 기능

- **property 접근**: `c.dividend`로 바로 DataFrame. 2단계 접근 불필요
- **index/show/trace**: 회사 구조 확인 → topic 열기 → source 검증
- **Notes 통합**: `c.notes.inventory`로 K-IFRS 주석 12개 항목 통합 접근
- **일괄 조회**: `c.all()`로 전체 데이터를 한 번에 dict로
- **Bridge Matching**: 계정명 변경을 자동 추적해서 시계열 연속성 보장
- **계정 표준화**: 2,700+ 상장사 XBRL 계정을 통합 체계로 매핑 (98.7%, 1,585만 행)
- **기업 간 비교**: 동일 snakeId로 정규화된 분기별 시계열
- **인사이트 등급**: 7영역(실적·수익성·건전성·현금흐름·지배구조·리스크) A~F 등급
- **시장 순위**: 매출·자산·성장률 기준 전체 + 섹터 내 순위
- **lazy + cache**: 처음 접근할 때만 파싱하고 이후 캐싱
- **profile roadmap**: 향후 terminal/notebook 문서형 회사 보고서 뷰 예정

## 다음 단계

- [설치](getting-started/installation.md)
- [빠른 시작](getting-started/quickstart.md)
- [API Reference](api/overview.md)
- [계정 표준화와 시계열](api/timeseries.md)
- [섹터 분류](api/sector.md)
- [인사이트 등급](api/insight.md)
- [시장 순위](api/rank.md)
- [튜토리얼](tutorials/index.md)


