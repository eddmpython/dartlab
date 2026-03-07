<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="120">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset=".github/assets/hero.svg">
  <source media="(prefers-color-scheme: light)" srcset=".github/assets/hero.svg">
  <img alt="DartLab Timeline" src=".github/assets/hero.svg" width="100%">
</picture>

<br>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=f59e0b&labelColor=0c0a09&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&labelColor=0c0a09&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-a8a29e?style=for-the-badge&labelColor=0c0a09" alt="License"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/"><img src="https://img.shields.io/badge/문서-GitHub_Pages-3b82f6?style=for-the-badge&labelColor=0c0a09&logo=github&logoColor=white" alt="Docs"></a>
</p>

<p>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-v1">데이터</a> ·
<a href="https://buymeacoffee.com/eddmpython">Sponsor</a>
</p>

</div>

---

DART 전자공시 문서를 완벽하게 분석하는 Python 라이브러리.

종목코드 하나면 재무제표, 배당, 주주, 자회사, 사업의 내용, 경영진단의견까지 — 숫자와 텍스트 모두 시계열로 추출한다.

## 설치

```bash
pip install dartlab
```

```bash
uv add dartlab
```

## 빠른 시작

```python
from dartlab import Company

samsung = Company("005930")    # 종목코드
samsung = Company("삼성전자")   # 회사명도 가능
samsung.corpName               # "삼성전자"
```

데이터가 로컬에 없으면 GitHub Releases에서 자동 다운로드한다. 수동으로 전체 데이터를 받으려면:

```python
from dartlab.core import downloadAll
downloadAll()  # 260+ 종목 일괄 다운로드
```

---

## 무엇을 할 수 있나

DartLab은 DART 전자공시 문서에서 **숫자(재무제표)**와 **텍스트(사업보고서)**를 모두 추출한다.

### 재무제표

요약재무정보를 시계열로 추출하고, K-IFRS 개정으로 계정명이 바뀌어도 같은 계정을 자동 추적한다 (Bridge Matching).

```python
result = samsung.analyze()

result.FS          # 전체 재무제표 시계열 (Polars DataFrame)
result.BS          # 재무상태표
result.IS          # 손익계산서
result.allRate     # 전체 매칭률 (예: 0.97)
result.breakpoints # 변경점 목록
```

재무상태표(BS), 손익계산서(IS), 현금흐름표(CF)를 분리해서 상세 항목까지 추출할 수도 있다.

```python
result = samsung.statements()

result.BS    # 재무상태표 상세 항목
result.IS    # 손익계산서 상세 항목
result.CF    # 현금흐름표
```

### 배당

DPS, 배당성향, 배당수익률 등 배당 관련 지표를 시계열로 추출한다.

```python
result = samsung.dividend()
result.timeSeries
# ┌──────┬───────────┬───────┬──────────────┬─────────────┬──────────────┬──────┐
# │ year ┆ netIncome ┆ eps   ┆ totalDividend┆ payoutRatio ┆ dividendYield┆ dps  │
# ├──────┼───────────┼───────┼──────────────┼─────────────┼──────────────┼──────┤
# │ 2024 ┆ ...       ┆ ...   ┆ ...          ┆ ...         ┆ ...          ┆ 1444 │
# │ 2023 ┆ ...       ┆ ...   ┆ ...          ┆ ...         ┆ ...          ┆ 1444 │
# └──────┴───────────┴───────┴──────────────┴─────────────┴──────────────┴──────┘
```

### 최대주주

최대주주와 특수관계인의 지분율 변화를 추적한다.

```python
result = samsung.majorHolder()
result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.totalRatio    # 특수관계인 포함 합계
result.holders       # 개별 주주 목록
result.timeSeries    # 지분율 시계열
```

5% 이상 주주, 소액주주, 의결권 현황도 별도로 제공한다.

```python
overview = samsung.holderOverview()
overview.bigHolders  # 5% 이상 주주 목록
overview.minority    # 소액주주 현황 (주주수, 주식수, 비율)
overview.voting      # 의결권 현황
```

### 직원 현황

총 직원수, 평균연봉, 근속연수를 시계열로 추출한다.

```python
result = samsung.employee()
result.timeSeries  # year, totalEmployees, avgSalary, avgTenure, ...
```

### 부문별 매출

사업부문, 제품, 지역별 매출 데이터를 추출한다.

```python
result = samsung.segments()
result.revenue  # 부문별 매출 시계열 DataFrame
result.tables   # {연도: [SegmentTable]} 상세 테이블
```

### 주식 현황

발행주식, 자기주식, 유통주식 수를 시계열로 추적한다.

```python
result = samsung.shareCapital()
result.outstandingShares  # 발행주식 총수
result.treasuryShares     # 자기주식수
result.floatingShares     # 유통주식수
result.treasuryRatio      # 자기주식 보유비율 (%)
```

### 자회사 투자

타법인 출자 현황 — 자회사 포트폴리오 전체를 추출한다.

```python
result = samsung.subsidiary()
result.investments  # 투자 목록 (법인명, 지분율, 장부가 등)
result.timeSeries   # 연도별 총 투자건수, 장부가 시계열
```

### 관계기업

관계기업/공동기업 투자 데이터를 추출한다.

```python
result = samsung.affiliates()
result.profiles     # {연도: [기업 프로필]}
result.movementDf   # 기업별 변동 시계열
```

### 채무증권

회사채, 기업어음 등 채무증권 발행실적을 추출한다.

```python
result = samsung.bond()
result.issuances   # 채무증권 목록 (종류, 금액, 이자율, 만기일 등)
result.timeSeries  # 연도별 발행건수, 총액 시계열
```

### 비용 구조

비용의 성격별 분류 — 원재료비, 인건비, 감가상각비 등의 구성을 추출한다.

```python
result = samsung.costByNature()
result.timeSeries  # 비용 시계열
result.ratios      # 비용 구성비
```

### 회사 개요

설립일, 본사주소, 종속기업 수, 신용등급 등 기본 정보를 추출한다.

```python
result = samsung.overview()
result.founded          # "1969-01-13"
result.address          # "경기도 수원시 영통구 ..."
result.subsidiaryCount  # 종속기업 수
result.creditRatings    # [CreditRating(agency="Moody's", grade="Aa2"), ...]
result.isSME            # False
```

### 경영진단의견 (MD&A)

이사의 경영진단 및 분석의견 — 사업 전망, 실적 분석, 위험 요인 등을 섹션별로 분류한다.

```python
result = samsung.mdna()
result.overview    # 사업 개요 텍스트
result.sections    # 섹션별 분류 (overview, forecast, financials, ...)

for section in result.sections:
    print(f"[{section.category}] {section.title}")
    print(section.text[:200])
```

### 사업의 내용

사업보고서 "사업의 내용" 전체를 섹션별로 분류하고, 연도별 변경 시점을 탐지한다.

```python
result = samsung.business()
result.sections  # 하위 섹션 목록 (overview, products, risk, rnd, ...)
result.changes   # 연도별 변경 정보 (changedPct > 30이면 유의미한 변화)
```

### 원재료/설비투자

원재료 매입, 유형자산, 시설투자 현황을 추출한다.

```python
result = samsung.rawMaterial()
result.materials   # 원재료 매입 항목
result.equipment   # 유형자산 기말잔액
result.capexItems  # 시설투자 항목
```

---

## 종목 검색

```python
from dartlab import Company

# 회사명으로 검색
Company.search("삼성")
# ┌──────────────┬──────────┬────────────────┐
# │ 회사명       ┆ 종목코드 ┆ 업종           │
# ├──────────────┼──────────┼────────────────┤
# │ 삼성전자     ┆ 005930   ┆ 반도체         │
# │ 삼성SDI      ┆ 006400   ┆ 일차전지       │
# │ ...          ┆ ...      ┆ ...            │
# └──────────────┴──────────┴────────────────┘

# KRX 전체 상장법인 목록
Company.listing()

# 로컬 보유 종목 인덱스
Company.status()

# 공시 문서 목록 + DART 뷰어 링크
samsung.docs()
```

---

## 패키지 구조

DartLab은 데이터의 성격에 따라 두 패키지로 나뉜다.

### finance — 정량 재무 데이터 (11개 모듈)

숫자 테이블을 파싱해서 DataFrame으로 변환한다.

| 모듈 | 함수 | Company 메서드 | 설명 |
|------|------|------|------|
| `finance.summary` | `analyze(stockCode)` | `.analyze()` | 요약재무정보, Bridge Matching |
| `finance.statements` | `statements(stockCode)` | `.statements()` | 연결재무제표 BS, IS, CF |
| `finance.segment` | `segments(stockCode)` | `.segments()` | 부문별 매출 |
| `finance.costByNature` | `costByNature(stockCode)` | `.costByNature()` | 비용의 성격별 분류 |
| `finance.majorHolder` | `majorHolder(stockCode)` | `.majorHolder()` | 최대주주 지분율 |
| `finance.majorHolder` | `holderOverview(stockCode)` | `.holderOverview()` | 5% 주주, 소액주주, 의결권 |
| `finance.shareCapital` | `shareCapital(stockCode)` | `.shareCapital()` | 발행·자기·유통 주식 |
| `finance.dividend` | `dividend(stockCode)` | `.dividend()` | 배당 시계열 |
| `finance.employee` | `employee(stockCode)` | `.employee()` | 직원 현황 |
| `finance.subsidiary` | `subsidiary(stockCode)` | `.subsidiary()` | 타법인 출자 현황 |
| `finance.bond` | `bond(stockCode)` | `.bond()` | 채무증권 발행실적 |
| `finance.affiliate` | `affiliates(stockCode)` | `.affiliates()` | 관계기업 투자 |

### disclosure — 공시 서술형 섹션 (4개 모듈)

텍스트에서 정보를 추출하고 섹션별로 분류한다.

| 모듈 | 함수 | Company 메서드 | 설명 |
|------|------|------|------|
| `disclosure.business` | `business(stockCode)` | `.business()` | 사업의 내용 + 변경 탐지 |
| `disclosure.companyOverview` | `companyOverview(stockCode)` | `.overview()` | 회사의 개요 (설립일, 주소, 신용등급) |
| `disclosure.mdna` | `mdna(stockCode)` | `.mdna()` | 경영진단의견 (MD&A) |
| `disclosure.rawMaterial` | `rawMaterial(stockCode)` | `.rawMaterial()` | 원재료, 유형자산, 설비투자 |

### 함수 직접 호출

Company를 거치지 않고 모듈 함수를 직접 호출할 수도 있다.

```python
from dartlab.finance.summary import analyze
from dartlab.finance.statements import statements
from dartlab.finance.dividend import dividend
from dartlab.disclosure.business import business
from dartlab.disclosure.mdna import mdna

result = analyze("005930")
result = statements("005930")
result = dividend("005930")
result = business("005930")
result = mdna("005930")
```

### 유틸리티

| 함수 | 설명 |
|------|------|
| `Company.listing()` | KRX 전체 상장법인 목록 |
| `Company.search(keyword)` | 회사명 부분 검색 |
| `Company.status()` | 로컬 보유 전체 종목 인덱스 |
| `company.docs()` | 해당 종목의 공시 목록 + DART 뷰어 링크 |
| `core.loadData(stockCode)` | Parquet 로드 (없으면 자동 다운로드) |
| `core.downloadAll()` | 전체 데이터 일괄 다운로드 |

모든 분석 함수는 종목코드(6자리)를 받아서 Result 객체를 반환한다. 데이터가 부족하면 `None`을 반환한다. 연간/분기/반기 분석은 `period` 파라미터로 제어한다 (`"y"`, `"q"`, `"h"`).

---

## 핵심 기술

### 공시 수평 정렬

DART 전자공시는 보고서마다 담고 있는 기간이 다르다.

```
                           1분기      2분기      3분기      4분기
                          ┌──────┐
 1분기 보고서              │  Q1  │
                          └──────┘
                          ┌──────────────┐
 반기 보고서               │   Q1 + Q2    │
                          └──────────────┘
                          ┌─────────────────────┐
 3분기 보고서              │    Q1 + Q2 + Q3     │
                          └─────────────────────┘
                          ┌──────────────────────────────┐
 사업 보고서               │       Q1 + Q2 + Q3 + Q4      │
                          └──────────────────────────────┘
```

1분기 보고서에는 Q1만, 반기에는 Q1+Q2 누적, 사업보고서에는 1년 전체가 들어있다. 이 누적 구조에서 개별 분기 실적을 역산하고, 보고서 간 계정명이 바뀌어도 같은 계정을 추적하는 것이 DartLab의 핵심이다.

### Bridge Matching

K-IFRS 개정이나 내부 구조 변경으로 **동일 기업 안에서** 계정명이 바뀌는 경우가 빈번하다. Bridge Matching은 인접 연도의 재무제표에서 금액과 명칭 유사도를 조합해 동일 계정을 자동으로 연결한다.

```
             2022년            2023년            2024년
             ──────            ──────            ──────
 매출액 ────────────── 매출액 ────────────── 수익(매출액)
                              ↑ 명칭 변경                ↑ 명칭 변경
 영업이익 ──────────── 영업이익 ──────────── 영업이익
 당기순이익 ────────── 당기순이익 ────────── 당기순이익(손실)
```

4단계 매칭으로 구성된다:

1. **정확 매칭** — 금액이 완전히 동일한 계정 연결
2. **재작성 매칭** — 소수점 오차(0.5 이내) 허용
3. **명칭 변경 매칭** — 금액 오차 5% 이내 + 명칭 유사도 60% 이상
4. **특수 항목 매칭** — 주당이익(EPS) 등 소수점 단위 항목

매칭률이 85% 이하로 떨어지면 변경점(breakpoint)으로 판정하고 구간을 분리한다.

---

## 데이터

DartLab이 제공하는 데이터는 DART 전자공시 원문을 eddmpython의 노하우로 상세하게 파싱하여 만든 구조화 데이터다. 단순 API 호출 결과가 아니라 문서 구조를 분석하고 항목별로 분류·정제한 결과물이다.

각 Parquet 파일에는 하나의 기업에 대한 모든 공시 문서가 들어있다:

- **메타데이터**: 종목코드, 회사명, 보고서 유형, 제출일, 사업연도
- **정량 데이터**: 요약재무정보, 재무제표 본문, 주석
- **텍스트 데이터**: 사업의 내용, 감사의견, 위험관리, 임원/주주 현황

[GitHub Releases](https://github.com/eddmpython/dartlab/releases/tag/data-v1)에 260개 이상의 상장 기업 데이터가 있다. `loadData()`는 로컬에 파일이 없으면 자동으로 다운로드한다.

> **데이터 업데이트 주기**
>
> 비용이 발생하는 프록시를 사용하지 않고 직접 수집하고 있어서 데이터 업데이트가 매우 느리다. 새로운 종목 추가나 최신 공시 반영에 시간이 걸릴 수 있다.

---

## 왜 만들었나

DART 전자공시에는 재무제표 숫자뿐 아니라 사업의 내용, 위험 요인, 감사의견, 소송 현황, 지배구조 변동 같은 텍스트 정보가 함께 들어있다. 대부분의 도구는 숫자만 뽑아간다. 나머지는 버려진다.

DartLab은 숫자와 텍스트를 모두 추출한다. 분기/반기/사업보고서를 하나의 시간축 위에 정렬하고, 동일 기업 안에서 K-IFRS 개정이나 구조 변경으로 계정명이 바뀌어도 같은 계정을 자동으로 추적한다.

> **현재 범위와 향후 계획**
>
> Bridge Matching은 **한 회사 내**에서 연도 간 계정명 변경을 추적하는 기능이다. 서로 다른 회사 간 계정을 직접 비교하는 기능은 아직 제공하지 않는다.
>
> 다만, eddmpython이 다른 프로젝트에서 축적해 온 계정 표준화 노하우가 있다. 이를 바탕으로 **전체 상장사 재무제표의 95% 이상을 커버하는 교차 비교 기능**을 배치 적용할 예정이다. 또한 텍스트 분석 영역은 **별도 프로젝트에서 추진 중인 전문 텍스트 분석 모듈**을 DartLab에 통합할 계획이다.
>
> 종목 하나가 아니라 시장 전체를 한 번에 분석할 수 있는 도구가 최종 목표다.

## 비전

DartLab의 최종 목표는 **전자공시 데이터의 완전한 활용**이다.

**현재 (v0.1.x)** — 문서 파싱 도구
- 15개 분석 모듈로 단일 기업의 재무제표, 주석, 텍스트를 시계열로 추출
- Bridge Matching으로 동일 기업 내 계정명 변경 자동 추적
- 260+ 상장사 데이터 제공
- DART 전자공시 문서를 구조화된 데이터로 파싱하는 도구를 만드는 단계

**다음 단계** — 기업 간 비교
- 계정 표준화 엔진 도입 (eddmpython 타 프로젝트의 계정 매핑 노하우 활용)
- 전체 상장사 재무제표의 95% 이상 교차 비교 커버리지 목표
- 업종별, 규모별 그룹 비교 및 시장 전체 스크리닝

**텍스트 분석 고도화** — AI + 별도 프로젝트 연계
- 현재 별도 프로젝트에서 전문 텍스트 이해 패키지를 개발 중
- 공시 문서 텍스트의 시계열 비교, 섹션별 변경 추적, 의미 분석 등
- 추후 AI와 eddmpython의 텍스트 이해 패키지를 결합하여, 공시 문서의 모든 경우에 대응되는 범용 헬퍼로 DartLab에 투입할 예정
- 현재 DartLab이 파싱한 구조화 데이터 위에서 동작하는 지능형 분석 레이어가 최종 형태

**최종 목표** — 정량·정성 교차 검증
- 정량 변동과 정성 변화의 연결 (실적 악화 ↔ 위험 요인 텍스트 변화)
- 감사의견, 지배구조 변동 등 리스크 시그널 자동 탐지
- 종목 하나가 아니라 시장 전체를 한 번에 분석

## 로드맵

- [x] 요약재무정보 시계열 (Bridge Matching)
- [x] 연결재무제표 BS, IS, CF
- [x] 부문별 매출, 관계기업, 배당, 직원, 주주, 자회사
- [x] 채무증권, 비용 성격별 분류, 원재료/설비투자
- [x] 경영진단의견, 사업의 내용, 회사의 개요
- [x] Company 통합 인터페이스
- [x] finance/disclosure 패키지 분리
- [ ] 계정 표준화 및 기업 간 교차 비교
- [ ] 텍스트 분석 모듈 통합 (별도 프로젝트에서 배치 예정)
- [ ] 정량 + 정성 교차 검증
- [ ] 시각화

## Sponsor

<a href="https://buymeacoffee.com/eddmpython">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180"/>
</a>

## 라이선스

MIT License
