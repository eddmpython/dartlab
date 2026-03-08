---
title: DartLab
---

# DartLab

DART 전자공시 문서에서 재무제표, 주석, 정기보고서, 텍스트를 파싱하고 시계열로 정렬하는 Python 라이브러리.

종목코드 하나면 된다. 40개 분석 모듈이 공시 원문에서 구조화된 데이터를 추출한다. yfinance처럼 property 한 줄로 DataFrame을 바로 받는다.

```python
from dartlab import Company

c = Company("005930")

c.BS          # 재무상태표 DataFrame
c.IS          # 손익계산서 DataFrame
c.dividend    # 배당 시계열 DataFrame
c.employee    # 직원 현황 시계열 DataFrame
```

## 무엇을 할 수 있나

| 분류 | property | 설명 |
|------|----------|------|
| 재무제표 | `c.BS`, `c.IS`, `c.CF` | 재무상태표, 손익계산서, 현금흐름표 |
| K-IFRS 주석 | `c.notes.inventory`, `c.notes.borrowings` 등 12개 | 재고자산, 차입금, 리스, 충당부채 등 |
| 정기보고서 | `c.dividend`, `c.employee`, `c.majorHolder` 등 26개 | 배당, 직원, 최대주주, 감사, 임원 등 |
| 공시 텍스트 | `c.business`, `c.mdna`, `c.overview` | 사업의 내용, MD&A, 회사의 개요 |

전체 모듈 40개. 데이터가 로컬에 없으면 GitHub Releases에서 자동 다운로드한다.

## 핵심 기능

- **property 접근**: `c.dividend`로 바로 DataFrame. 2단계 접근 불필요
- **Notes 통합**: `c.notes.inventory`로 K-IFRS 주석 12개 항목 통합 접근
- **일괄 조회**: `c.all()`로 전체 데이터를 한 번에 dict로
- **Bridge Matching**: 계정명 변경을 자동 추적해서 시계열 연속성 보장
- **lazy + cache**: 처음 접근할 때만 파싱하고 이후 캐싱

## 다음 단계

- [설치](getting-started/installation.md)
- [빠른 시작](getting-started/quickstart.md)
- [API Reference](api/overview.md)
- [Bridge Matching](user-guide/bridge-matching.md)
- [튜토리얼](tutorials/index.md)
