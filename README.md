<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="180">

<h3>DartLab</h3>

<p><b>숫자만 읽는 시대는 끝났다</b> — DART 공시의 숫자와 텍스트를 모두 읽는다</p>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&color=c83232&labelColor=050811&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-94a3b8?style=for-the-badge&labelColor=050811" alt="License"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/"><img src="https://img.shields.io/badge/Docs-GitHub_Pages-fb923c?style=for-the-badge&labelColor=050811&logo=github&logoColor=white" alt="Docs"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-v1"><img src="https://img.shields.io/badge/Data-260%2B_Companies-f87171?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Data"></a>
<a href="https://buymeacoffee.com/eddmpython"><img src="https://img.shields.io/badge/Sponsor-☕_Buy_Me_a_Coffee-ffdd00?style=for-the-badge&labelColor=050811" alt="Sponsor"></a>
</p>

</div>

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

c = Company("005930")    # 종목코드
c = Company("삼성전자")   # 회사명도 가능
c.corpName               # "삼성전자"
```

객체를 만들면 사용 가이드가 출력된다. 상세 가이드는 `c.guide()`로 볼 수 있다.

데이터가 로컬에 없으면 GitHub Releases에서 자동 다운로드한다.

```python
from dartlab.core import downloadAll
downloadAll()  # 260+ 종목 일괄 다운로드
```

---

## 무엇을 할 수 있나

DartLab은 DART 전자공시 문서에서 **숫자(재무제표)**와 **텍스트(사업보고서)**를 모두 추출한다. 모든 데이터는 property로 바로 접근할 수 있다.

### 재무제표

```python
c.BS    # 재무상태표 DataFrame
c.IS    # 손익계산서 DataFrame
c.CF    # 현금흐름표 DataFrame
```

요약재무정보를 시계열로 추출하고, K-IFRS 개정으로 계정명이 바뀌어도 같은 계정을 자동 추적한다 (Bridge Matching).

```python
result = c.fsSummary()

result.FS          # 전체 재무제표 시계열 (Polars DataFrame)
result.BS          # 재무상태표
result.IS          # 손익계산서
result.allRate     # 전체 매칭률 (예: 0.97)
result.breakpoints # 변경점 목록
```

### 주석 (K-IFRS)

주석 데이터를 영문 속성 또는 한글 키로 바로 접근할 수 있다.

```python
c.notes.inventory          # 재고자산 DataFrame
c.notes["재고자산"]         # 한글 키도 가능
c.notes.receivables        # 매출채권
c.notes.tangibleAsset      # 유형자산
c.notes.intangibleAsset    # 무형자산
c.notes.investmentProperty # 투자부동산
c.notes.affiliates         # 관계기업
c.notes.borrowings         # 차입금
c.notes.provisions         # 충당부채
c.notes.eps                # 주당이익
c.notes.lease              # 리스
c.notes.segments           # 부문정보
c.notes.costByNature       # 비용의성격별분류
```

### 배당

```python
c.dividend
# ┌──────┬───────────┬───────┬──────────────┬─────────────┬──────────────┬──────┐
# │ year ┆ netIncome ┆ eps   ┆ totalDividend┆ payoutRatio ┆ dividendYield┆ dps  │
# └──────┴───────────┴───────┴──────────────┴─────────────┴──────────────┴──────┘
```

### 최대주주

```python
c.majorHolder    # 최대주주 + 특수관계인 지분율 시계열 DataFrame
```

전체 Result 객체가 필요하면 `c.get("majorHolder")`로 접근한다.

```python
result = c.get("majorHolder")
result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.timeSeries    # 지분율 시계열
```

### 직원 현황

```python
c.employee    # year, totalEmployees, avgSalary, avgTenure, ...
```

### 감사의견

```python
c.audit    # year, auditor, opinion, keyAuditMatters
```

### 임원 현황

```python
c.executive      # year, totalRegistered, insideDirectors, outsideDirectors, ...
c.executivePay   # year, category, headcount, totalPay, avgPay
```

### 주식 / 자본

```python
c.shareCapital     # 발행·자기·유통 주식 DataFrame
c.capitalChange    # 자본금 변동 DataFrame
c.fundraising      # 증자/감자 DataFrame
```

### 자회사 / 관계기업

```python
c.subsidiary           # 타법인 출자 현황 DataFrame
c.affiliateGroup       # 계열회사 현황 DataFrame
c.investmentInOther    # 투자법인, 지분율, 장부가 DataFrame
```

### 이사회 / 지배구조

```python
c.boardOfDirectors     # 이사회 구성, 출석률 DataFrame
c.shareholderMeeting   # 주주총회 안건, 결의 DataFrame
c.auditSystem          # 감사위원, 감사활동 DataFrame
c.internalControl      # 내부통제 평가 DataFrame
```

### 리스크 / 법률

```python
c.contingentLiability  # 우발부채, 채무보증, 소송 DataFrame
c.relatedPartyTx       # 관계자거래 DataFrame
c.sanction             # 제재·처벌 DataFrame
c.riskDerivative       # 환율 민감도, 파생상품 DataFrame
```

### 기타 재무

```python
c.bond                 # 채무증권 DataFrame
c.rnd                  # 연구개발비 DataFrame
c.otherFinance         # 대손충당금 등 DataFrame
c.productService       # 주요 제품/서비스 DataFrame
c.salesOrder           # 매출실적, 수주잔고 DataFrame
c.articlesOfIncorporation  # 정관 변경 이력 DataFrame
```

### 회사 정보

```python
c.companyHistory         # 연혁 DataFrame
c.companyOverviewDetail  # 설립일, 상장일, 대표이사, 소재지 dict
```

### 공시 서술

```python
c.business       # 사업의 내용 (sections + 변경 탐지)
c.overview       # 회사의 개요 (설립일, 주소, 신용등급)
c.mdna           # 경영진단의견 MD&A
c.rawMaterial    # 원재료, 유형자산, 설비투자
```

---

## 전체 추출

```python
d = c.all()    # 모든 모듈 데이터를 dict로 반환 (progress bar)
# {"BS": df, "IS": df, "CF": df, "dividend": df, "notes": {...}, ...}
```

```python
import dartlab
dartlab.verbose = False    # 진행 표시 끄기

d = c.all()    # 조용히 추출
```

---

## Result 객체

property는 대표 DataFrame을 반환한다. 모듈의 전체 Result 객체가 필요하면 `c.get()`을 사용한다.

```python
# property — DataFrame 바로 반환
c.audit          # opinionDf (감사의견 DataFrame)

# get() — 전체 Result 객체
result = c.get("audit")
result.opinionDf   # 감사의견
result.feeDf       # 감사보수
```

---

## 종목 검색

```python
from dartlab import Company

Company.search("삼성")
# ┌──────────────┬──────────┬────────────────┐
# │ 회사명       ┆ 종목코드 ┆ 업종           │
# └──────────────┴──────────┴────────────────┘

Company.listing()   # KRX 전체 상장법인 목록
Company.status()    # 로컬 보유 종목 인덱스
c.docs()            # 공시 문서 목록 + DART 뷰어 링크
```

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

4단계 매칭으로 구성된다.

1. **정확 매칭** — 금액이 완전히 동일한 계정 연결
2. **재작성 매칭** — 소수점 오차(0.5 이내) 허용
3. **명칭 변경 매칭** — 금액 오차 5% 이내 + 명칭 유사도 60% 이상
4. **특수 항목 매칭** — 주당이익(EPS) 등 소수점 단위 항목

매칭률이 85% 이하로 떨어지면 변경점(breakpoint)으로 판정하고 구간을 분리한다.

---

## 패키지 구조

### finance — 정량 재무 데이터 (36개 모듈)

| property | 설명 |
|----------|------|
| `c.BS` / `c.IS` / `c.CF` | 재무상태표, 손익계산서, 현금흐름표 |
| `c.fsSummary()` | 요약재무정보 + Bridge Matching |
| `c.dividend` | 배당 시계열 |
| `c.majorHolder` | 최대주주 지분율 |
| `c.holderOverview` | 5% 주주, 소액주주, 의결권 |
| `c.employee` | 직원 현황 |
| `c.shareCapital` | 발행·자기·유통 주식 |
| `c.subsidiary` | 타법인 출자 현황 |
| `c.bond` | 채무증권 발행실적 |
| `c.audit` | 감사의견 + 감사보수 |
| `c.executive` | 임원 현황 |
| `c.executivePay` | 임원 보수 |
| `c.boardOfDirectors` | 이사회 구성·출석률 |
| `c.capitalChange` | 자본금 변동 |
| `c.contingentLiability` | 우발부채·소송 |
| `c.relatedPartyTx` | 관계자 거래 |
| `c.sanction` | 제재·처벌 |
| `c.rnd` | 연구개발비 |
| `c.internalControl` | 내부통제 평가 |
| `c.affiliateGroup` | 계열회사 현황 |
| `c.fundraising` | 증자/감자 |
| `c.salesOrder` | 매출실적·수주상황 |
| `c.productService` | 주요 제품/서비스 |
| `c.riskDerivative` | 위험관리·파생거래 |
| `c.articlesOfIncorporation` | 정관 변경 이력 |
| `c.otherFinance` | 대손충당금 등 |
| `c.companyHistory` | 연혁 |
| `c.shareholderMeeting` | 주주총회 |
| `c.auditSystem` | 감사제도 |
| `c.investmentInOther` | 타법인출자 |
| `c.companyOverviewDetail` | 회사개요 상세 |

### K-IFRS 주석 (12개 항목)

| property | 설명 |
|----------|------|
| `c.notes.receivables` | 매출채권 |
| `c.notes.inventory` | 재고자산 |
| `c.notes.tangibleAsset` | 유형자산 |
| `c.notes.intangibleAsset` | 무형자산 |
| `c.notes.investmentProperty` | 투자부동산 |
| `c.notes.affiliates` | 관계기업 |
| `c.notes.borrowings` | 차입금 |
| `c.notes.provisions` | 충당부채 |
| `c.notes.eps` | 주당이익 |
| `c.notes.lease` | 리스 |
| `c.notes.segments` | 부문정보 |
| `c.notes.costByNature` | 비용의성격별분류 |

한글 키도 지원: `c.notes["재고자산"]`

### disclosure — 공시 서술형 섹션 (4개 모듈)

| property | 설명 |
|----------|------|
| `c.business` | 사업의 내용 + 변경 탐지 |
| `c.overview` | 회사의 개요 (설립일, 주소, 신용등급) |
| `c.mdna` | 경영진단의견 (MD&A) |
| `c.rawMaterial` | 원재료, 유형자산, 설비투자 |

---

## 데이터

DartLab이 제공하는 데이터는 DART 전자공시 원문을 eddmpython의 노하우로 상세하게 파싱하여 만든 구조화 데이터다. 단순 API 호출 결과가 아니라 문서 구조를 분석하고 항목별로 분류·정제한 결과물이다.

각 Parquet 파일에는 하나의 기업에 대한 모든 공시 문서가 들어있다.

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
- 36개 분석 모듈로 단일 기업의 재무제표, 주석, 텍스트를 시계열로 추출
- Bridge Matching으로 동일 기업 내 계정명 변경 자동 추적
- 260+ 상장사 데이터 제공
- property 기반 접근 — `c.BS`, `c.dividend`, `c.notes.inventory`

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
- [x] 감사의견, 임원 현황, 임원 보수
- [x] 유형자산 변동표, 주석 세부항목 (23개 키워드)
- [x] 이사회, 자본금 변동, 우발부채, 대주주 거래, 제재, 연구개발, 내부통제
- [x] 계열회사, 증자/감자, 매출·수주, 주요 제품, 위험관리·파생거래
- [x] 경영진단의견, 사업의 내용, 회사의 개요
- [x] Company property 기반 접근 + Notes 통합 + all()
- [x] rich 기반 터미널 출력 (아바타 + 사용 가이드)
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
