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

DART 공시 문서의 재무제표, 주석, 텍스트를 파싱하고 시계열로 정렬하는 Python 라이브러리.

종목코드 하나로 요약재무정보, 연결재무제표, 배당, 직원, 주주, 부문별 매출, 관계기업, 채무증권, 경영진단의견까지 14개 분석 모듈을 제공한다. 데이터가 로컬에 없으면 GitHub Releases에서 자동으로 다운로드한다.

## 왜 만들었나

DART 공시에는 재무제표 숫자뿐 아니라 사업의 내용, 위험 요인, 감사의견, 소송 현황, 지배구조 변동 같은 텍스트 정보가 함께 들어있다. 대부분의 도구는 숫자만 뽑아간다. 나머지는 버려진다.

DartLab은 숫자와 텍스트를 모두 추출한다. 분기/반기/사업보고서를 하나의 시간축 위에 정렬하고, **동일 기업 안에서** K-IFRS 개정이나 구조 변경으로 계정명이 바뀌어도 같은 계정을 자동으로 추적한다 (Bridge Matching).

> **현재 범위와 향후 계획**
>
> Bridge Matching은 **한 회사 내**에서 연도 간 계정명 변경을 추적하는 기능이다. 서로 다른 회사 간 계정을 직접 비교하는 기능은 아직 제공하지 않는다.
>
> 다만, eddmpython이 다른 프로젝트에서 축적해 온 계정 표준화 노하우가 있다. 이를 바탕으로 **전체 상장사 재무제표의 95% 이상을 커버하는 교차 비교 기능**을 배치 적용할 예정이다. 또한 텍스트 분석 영역은 **별도 프로젝트에서 추진 중인 전문 텍스트 분석 모듈**을 DartLab에 통합할 계획이다.
>
> 종목 하나가 아니라 시장 전체를 한 번에 분석할 수 있는 도구가 최종 목표다.

## 공시 수평 정렬

DART 공시는 보고서마다 담고 있는 기간이 다르다.

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

Bridge Matching은 인접 연도의 재무제표에서 금액과 명칭 유사도를 조합해 동일 계정을 자동으로 연결한다.

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

## 설치

```bash
pip install dartlab
```

```bash
uv add dartlab
```

## 빠른 시작

### Company 클래스

모든 분석의 진입점. 종목코드를 넣으면 데이터를 자동으로 로드한다 (로컬에 없으면 GitHub Releases에서 다운로드).

```python
from dartlab import Company

samsung = Company("005930")
samsung.corpName  # "삼성전자"
```

### 요약 재무정보

요약재무정보를 시계열로 추출한다. Bridge Matching으로 계정명 변경을 자동 추적한다.

```python
result = samsung.analyze()

result.FS          # 전체 재무제표 시계열 (Polars DataFrame)
result.BS          # 재무상태표
result.IS          # 손익계산서
result.nYears      # 분석 연도 수
result.allRate     # 전체 매칭률 (예: 0.97)
result.breakpoints # 변경점 목록
```

### 연결 재무제표

재무상태표(BS), 손익계산서(IS), 현금흐름표(CF)를 분리해서 시계열로 추출한다.

```python
result = samsung.statements()

result.BS    # 재무상태표 상세 항목
result.IS    # 손익계산서 상세 항목
result.CF    # 현금흐름표
```

### 배당

DPS, 배당성향, 배당수익률 등 배당 관련 지표 시계열.

```python
result = samsung.dividend()
result.timeSeries  # year, dps, payoutRatio, dividendYield, ...
```

### 직원 현황

총 직원수, 평균연봉, 근속연수 시계열.

```python
result = samsung.employee()
result.timeSeries  # year, totalEmployees, avgSalary, avgTenure, ...
```

### 최대주주

최대주주와 특수관계인의 지분율.

```python
result = samsung.majorHolder()
result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.totalRatio    # 특수관계인 포함 합계
result.holders       # list[Holder] - 개별 주주 목록
result.timeSeries    # 지분율 시계열
```

### 경영진단의견 (MD&A)

이사의 경영진단 및 분석의견. 사업 전망, 실적 분석, 위험 요인 등 경영진이 직접 작성한 텍스트를 섹션별로 분류한다.

```python
result = samsung.mdna()
result.sections    # list[MdnaSection]
result.overview    # 사업 개요 텍스트

for section in result.sections:
    print(f"[{section.category}] {section.title}")
    print(section.text[:200])
```

### 함수 직접 호출

Company를 거치지 않고 모듈 함수를 직접 호출할 수도 있다.

```python
from dartlab.finance.summary import analyze
from dartlab.finance.statements import statements
from dartlab.finance.dividend import dividend

result = analyze("005930")
result = statements("005930")
result = dividend("005930")
```

## 전체 API

### 재무제표

| 모듈 | 함수 | Company 메서드 | 설명 |
|------|------|------|------|
| `finance.summary` | `analyze(stockCode)` | `.analyze()` | 요약재무정보 시계열, Bridge Matching |
| `finance.statements` | `statements(stockCode)` | `.statements()` | 연결재무제표 BS, IS, CF |
| `finance.segment` | `segments(stockCode)` | `.segments()` | 부문별 매출 (사업부문, 제품, 지역) |
| `finance.costByNature` | `costByNature(stockCode)` | `.costByNature()` | 비용의 성격별 분류 (원재료비, 인건비, 감가상각비 등) |

### 주주/자본

| 모듈 | 함수 | Company 메서드 | 설명 |
|------|------|------|------|
| `finance.majorHolder` | `majorHolder(stockCode)` | `.majorHolder()` | 최대주주 지분율, 특수관계인 |
| `finance.majorHolder` | `holderOverview(stockCode)` | `.holderOverview()` | 5% 이상 주주, 소액주주, 의결권 |
| `finance.shareCapital` | `shareCapital(stockCode)` | `.shareCapital()` | 발행주식, 자기주식, 유통주식 |

### 사업 현황

| 모듈 | 함수 | Company 메서드 | 설명 |
|------|------|------|------|
| `finance.dividend` | `dividend(stockCode)` | `.dividend()` | DPS, 배당성향, 배당수익률 시계열 |
| `finance.employee` | `employee(stockCode)` | `.employee()` | 직원수, 평균연봉, 근속연수 시계열 |
| `finance.subsidiary` | `subsidiary(stockCode)` | `.subsidiary()` | 타법인 출자 현황 |
| `finance.affiliate` | `affiliates(stockCode)` | `.affiliates()` | 관계기업/공동기업 투자, 지분율, 장부가 |
| `finance.bond` | `bond(stockCode)` | `.bond()` | 채무증권 발행실적 (회사채, 기업어음) |
| `finance.rawMaterial` | `rawMaterial(stockCode)` | `.rawMaterial()` | 원재료 매입, 유형자산, 설비투자 현황 |

### 텍스트

| 모듈 | 함수 | Company 메서드 | 설명 |
|------|------|------|------|
| `finance.mdna` | `mdna(stockCode)` | `.mdna()` | 경영진단의견 (사업 전망, 실적 분석, 위험 요인) |

### 유틸리티

| 함수 | 설명 |
|------|------|
| `Company.status()` | 로컬에 보유한 전체 종목 인덱스 |
| `company.docs()` | 해당 종목의 공시 목록 + DART 뷰어 링크 |
| `core.loadData(stockCode)` | Parquet 로드 (없으면 자동 다운로드) |
| `core.downloadAll()` | 전체 데이터 일괄 다운로드 (260+ 종목) |

모든 분석 함수는 종목코드(6자리)를 받아서 Result 객체를 반환한다. 데이터가 부족하면 `None`을 반환한다. 연간/분기/반기 분석은 `period` 파라미터로 제어한다 (`"y"`, `"q"`, `"h"`).

## 데이터

각 Parquet 파일에는 하나의 기업에 대한 모든 공시 문서가 들어있다:

- **메타데이터**: 종목코드, 회사명, 보고서 유형, 제출일, 사업연도
- **정량 데이터**: 요약재무정보, 재무제표 본문, 주석
- **텍스트 데이터**: 사업의 내용, 감사의견, 위험관리, 임원/주주 현황

[GitHub Releases](https://github.com/eddmpython/dartlab/releases/tag/data-v1)에 260개 이상의 상장 기업 데이터가 있다. `loadData()`는 로컬에 파일이 없으면 자동으로 다운로드한다.

```python
from dartlab.core import downloadAll

downloadAll()  # 전체 데이터 일괄 다운로드
```

## 비전

DartLab의 최종 목표는 **공시 데이터의 완전한 활용**이다.

**현재 (v0.1.x)** — 문서 파싱 도구
- 14개 분석 모듈로 단일 기업의 재무제표, 주석, 텍스트를 시계열로 추출
- Bridge Matching으로 동일 기업 내 계정명 변경 자동 추적
- 260+ 상장사 데이터 제공
- DART 공시 문서를 구조화된 데이터로 파싱하는 도구를 만드는 단계

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
- [x] 채무증권, 경영진단의견, 비용 성격별 분류, 원재료/설비투자
- [x] Company 통합 인터페이스
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
