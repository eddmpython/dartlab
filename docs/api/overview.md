---
title: API Overview
---

# API Overview

모든 분석 함수는 종목코드(6자리)를 받아서 Result 객체를 반환한다. 데이터가 부족하면 `None`을 반환한다.

## Company 클래스

통합 진입점. 종목코드로 초기화하면 모든 분석 메서드를 사용할 수 있다.

```python
from dartlab import Company

c = Company("005930")
c.corpName      # "삼성전자"
c.stockCode     # "005930"
```

### 정적 메서드

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `Company.status()` | `pl.DataFrame` | 로컬 보유 전체 종목 인덱스 |

### 인스턴스 메서드

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `.docs()` | `pl.DataFrame` | 공시 목록 + DART 뷰어 링크 |
| `.analyze(period="y")` | `AnalysisResult` | 요약재무정보 시계열 |
| `.statements(period="y")` | `StatementsResult` | 연결재무제표 BS/IS/CF |
| `.segments(period="y")` | `SegmentsResult` | 부문별 매출 |
| `.costByNature(period="y")` | `CostByNatureResult` | 비용의 성격별 분류 |
| `.majorHolder()` | `MajorHolderResult` | 최대주주 지분율 |
| `.holderOverview()` | `HolderOverview` | 5%이상 주주, 소액주주, 의결권 |
| `.shareCapital()` | `ShareCapitalResult` | 주식의 총수 |
| `.dividend()` | `DividendResult` | 배당 |
| `.employee()` | `EmployeeResult` | 직원 현황 |
| `.subsidiary()` | `SubsidiaryResult` | 타법인 출자 |
| `.affiliates(period="y")` | `AffiliatesResult` | 관계기업 투자 |
| `.bond()` | `BondResult` | 채무증권 발행실적 |
| `.rawMaterial()` | `RawMaterialResult` | 원재료/설비투자 |
| `.mdna()` | `MdnaResult` | 경영진단 및 분석의견 |

## 함수 직접 호출

```python
from dartlab.finance.summary import analyze
from dartlab.finance.statements import statements
from dartlab.finance.dividend import dividend
from dartlab.finance.employee import employee
from dartlab.finance.majorHolder import majorHolder, holderOverview
from dartlab.finance.shareCapital import shareCapital
from dartlab.finance.segment import segments
from dartlab.finance.affiliate import affiliates
from dartlab.finance.subsidiary import subsidiary
from dartlab.finance.bond import bond
from dartlab.finance.costByNature import costByNature
from dartlab.finance.rawMaterial import rawMaterial
from dartlab.finance.mdna import mdna
```

## 유틸리티

```python
from dartlab.core import loadData, buildIndex, downloadAll, extractCorpName

loadData("005930")       # Parquet 로드 (없으면 자동 다운로드)
buildIndex()             # 전체 종목 인덱스 생성
downloadAll()            # 전체 데이터 일괄 다운로드
```

## period 파라미터

`analyze`, `statements`, `segments`, `costByNature`, `affiliates`는 `period` 파라미터를 지원한다.

| 값 | 의미 | 포함 보고서 |
|-----|------|------------|
| `"y"` | 연간 (기본값) | 사업보고서 |
| `"q"` | 분기별 | 1분기 + 반기 + 3분기 + 사업 |
| `"h"` | 반기별 | 반기 + 사업 |
