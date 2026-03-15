<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="180">

<h3>DartLab</h3>

<p><b>숫자만 읽는 시대는 끝났다</b> — DART 전자공시의 숫자와 텍스트를 모두 읽는다</p>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&color=c83232&labelColor=050811&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-94a3b8?style=for-the-badge&labelColor=050811" alt="License"></a>
<a href="https://github.com/eddmpython/dartlab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/eddmpython/dartlab/ci.yml?branch=master&style=for-the-badge&labelColor=050811&logo=github&logoColor=white&label=CI" alt="CI"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/">문서</a> · <a href="README.md">English</a> · <a href="https://buymeacoffee.com/eddmpython">후원</a>
</p>

<p>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-docs"><img src="https://img.shields.io/badge/Docs-260%2B_Companies-f87171?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Docs Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-finance-1"><img src="https://img.shields.io/badge/Finance-2,700%2B_Companies-818cf8?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Finance Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-report-1"><img src="https://img.shields.io/badge/Report-2,700%2B_Companies-34d399?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Report Data"></a>
</p>

</div>

## DartLab은 무엇인가

DartLab은 기업 공시를 파싱하고 분석하는 Python 패키지다. 안정화의 중심은 [DART 전자공시](https://dart.fss.or.kr/) (한국)이며, [SEC EDGAR](https://www.sec.gov/edgar) (미국)도 같은 `dartlab.Company(...)` facade로 지원한다.

공시에서 **숫자(재무제표)**와 **텍스트(사업보고서)**를 함께 추출하고, 비교 가능한 표와 회사 facade, CLI 워크플로우, AI 웹 인터페이스로 제공한다. 동일한 `index → show → trace` 흐름이 한국과 미국 종목 모두에서 동작한다.

## 계정 표준화

한국 상장사 2,700+개는 XBRL로 재무제표를 공시하지만, 같은 경제적 개념에 대해 **회사마다 다른 계정ID와 계정명**을 사용한다. "매출"이라는 하나의 개념이 수십 가지 변종으로 존재한다.

DartLab은 자체 **통합 계정 체계**를 구축했다. 7단계 매핑 파이프라인과 34,000개 이상의 학습된 동의어를 통해, 2,700+ 상장사 재무제표 행의 **98.7%** (1,585만 행)를 표준 계정으로 매핑한다. 삼성전자의 매출과 어떤 상장사의 매출이든 동일한 `revenue` 키로 직접 비교할 수 있다.

```
XBRL 원본 (회사마다 다름)              DartLab (표준화)
─────────────────────────────        ──────────────────────
ifrs-full_Revenue                 →  revenue
dart_OperatingIncomeLoss          →  operating_income
dart_ConstructionRevenue          →  revenue
ifrs_ProfitLoss                   →  net_income
매출액, 수익(매출액), 영업수익     →  revenue
```

## 40개 파싱 모듈

종목코드 하나면 된다. 40개 모듈이 공시 원문에서 재무제표, 주석, 배당, 임원, 지배구조, 리스크, 서술 텍스트를 구조화된 DataFrame으로 추출한다. yfinance처럼 property 한 줄로 바로 접근한다.

## 설치

> **[uv](https://docs.astral.sh/uv/)**가 필요하다 — Rust로 만든 Python 패키지 매니저. Python 버전 관리와 가상환경을 자동으로 처리한다.

```bash
# 1. uv 설치 (이미 있으면 건너뛴다)
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 프로젝트 생성
uv init my-analysis && cd my-analysis

# 3. DartLab 설치 — 필요한 옵션을 선택한다
uv add dartlab              # 기본 (재무제표 파싱)
uv add dartlab[ai]          # + AI 기업분석 웹 인터페이스 (dartlab ai)
uv add dartlab[llm]         # + OpenAI/Ollama LLM (CLI에서 분석)
uv add dartlab[charts]      # + Plotly 차트
uv add dartlab[all]         # 전부 포함

# 4. 설치 확인
uv run python -c "import dartlab; c = dartlab.Company('005930'); print(c.corpName)"
# → 삼성전자

# 5. AI 기업분석 실행 (dartlab[ai] 설치 시)
uv run dartlab ai
# → http://localhost:8400
```

## 빠른 시작

```python
import dartlab

# 한국 종목 (DART)
c = dartlab.Company("005930")    # 종목코드
c = dartlab.Company("삼성전자")   # 회사명도 가능
c.corpName               # "삼성전자"

# 미국 종목 (EDGAR) — 같은 facade, 같은 흐름
c = dartlab.Company("AAPL")
c.corpName               # "Apple Inc."
```

객체를 만들면 사용 가이드가 출력된다. 상세 가이드는 `c.guide()`로 볼 수 있다.

데이터가 로컬에 없으면 GitHub Releases에서 자동 다운로드한다.

```python
from dartlab.core.dataLoader import downloadAll

downloadAll("docs")                        # 260+ 종목 공시 문서 일괄 다운로드
downloadAll("finance")                     # 2,700+ 종목 재무 숫자 일괄 다운로드
downloadAll("report")                      # 2,700+ 종목 정기보고서 일괄 다운로드
downloadAll("finance", forceUpdate=True)   # 원격이 더 최신이면 재다운로드
```

## CLI

`dartlab` 명령은 웹 UI 실행용 보조 스크립트가 아니라 공개 인터페이스다.

```bash
uv run dartlab status
uv run dartlab setup codex
uv run dartlab ask 005930 "부채 리스크를 요약해줘"
uv run dartlab excel 005930
uv run dartlab ai
```

`dartlab ai`는 웹 인터페이스를 열고, `ask`, `status`, `setup`, `excel`은 현재 공개 CLI 명령으로 제공된다.

---

## 무엇을 할 수 있나

### Company — 통합 진입점

하나의 facade가 한국과 미국 시장을 모두 커버한다. 티커 형식이 데이터 소스를 자동 결정한다:

```python
import dartlab

# 한국 종목 → DART 엔진
kr = dartlab.Company("005930")
kr.corpName    # "삼성전자"

# 미국 종목 → EDGAR 엔진
us = dartlab.Company("AAPL")
us.corpName    # "Apple Inc."
```

둘 다 같은 `Company` 인터페이스를 반환하고, 같은 `index → show → trace` 흐름으로 동작한다.

### index / show / trace

현재 공개 사용 흐름은 단순하다.

- `index`로 회사 데이터 구조를 먼저 본다
- `show(topic)`으로 실제 내용을 연다
- `trace(topic)`으로 `docs / finance / report` 중 어떤 source가 채택됐는지 확인한다

```python
c = dartlab.Company("005930")
c.index              # 구조 index dataframe
c.show("BS")         # topic 하나 보기
c.trace("dividend")  # source 추적
c.docs.sections      # pure docs 수평화 source
c.finance.BS         # authoritative 재무제표
c.report.dividend    # authoritative 정형 공시

# EDGAR도 같은 흐름
us = dartlab.Company("AAPL")
us.index             # 같은 8컬럼 구조
us.show("BS")        # SEC XBRL 재무제표
us.show("riskFactors")  # 10-K 서술형 섹션
```

`show()`는 공시 topic에 대해 `ShowResult(text, table)` 을 반환한다 — 텍스트와 테이블이 분리된다:

```python
result = c.show("companyOverview")
result.text    # 서술문 DataFrame
result.table   # 테이블 DataFrame
```

### 재무제표

```python
c.BS    # 재무상태표 DataFrame
c.IS    # 손익계산서 DataFrame
c.CIS   # 포괄손익계산서 DataFrame
c.CF    # 현금흐름표 DataFrame
c.SCE   # 자본변동표 (DART만 해당)
```

### 기업 간 비교 가능한 시계열

통합 계정 체계(98.7% 매핑률)를 통해 모든 기업의 XBRL 데이터를 **개별 분기 시계열**로 변환한다. 반기/사업보고서의 누적 수치에서 개별 분기 실적을 역산한다.

```python
series, periods = c.timeseries
# periods = ["2016_Q1", "2016_Q2", ..., "2024_Q4"]
# series["IS"]["revenue"]            # 분기별 매출 시계열
# series["BS"]["total_assets"]       # 분기별 총자산
# series["CF"]["operating_cashflow"] # 분기별 영업현금흐름

r = c.ratios
r.roe               # 8.29 (%)
r.operatingMargin   # 9.51 (%)
r.debtRatio         # 27.4 (%)
r.fcf               # 잉여현금흐름 (원)
```

2,700+ 상장사가 동일한 snakeId 체계를 공유한다. 수동 매핑 없이 어떤 두 기업이든 직접 비교할 수 있다.

### 요약재무정보 + Bridge Matching

요약재무정보를 시계열로 추출하고, K-IFRS 개정으로 계정명이 바뀌어도 같은 계정을 자동 추적한다.

```python
result = c.fsSummary()

result.FS          # 전체 재무제표 시계열 (Polars DataFrame)
result.BS          # 재무상태표
result.IS          # 손익계산서
result.allRate     # 전체 매칭률 (예: 0.97)
result.breakpoints # 변경점 목록
```

### 주석 (K-IFRS)

주석 데이터는 deep access용이다. 회사 관점 기본 경로는 먼저 `c.show(...)`를 쓰고, 필요할 때만 notes로 내려간다.

```python
c.notes.inventory          # 재고자산 DataFrame
c.notes["재고자산"]         # 한글 키도 가능
c.notes.receivables        # 매출채권
c.show("tangibleAsset")    # 회사 관점 기본 payload
c.notes.tangibleAsset      # deep access legacy note parser
c.notes.intangibleAsset    # 무형자산
c.notes.investmentProperty # 투자부동산
c.notes.affiliates         # 관계기업
c.notes.borrowings         # 차입금
c.notes.provisions         # 충당부채
c.notes.eps                # 주당이익
c.notes.lease              # 리스
c.notes.segments           # 부문정보
c.show("costByNature")     # 회사 관점 기본 payload
c.notes.costByNature       # deep access legacy note parser
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

### 공시 수평화는 Company의 뼈대다

```python
c.sections          # 통합 topic x period company table
c.index             # same structure index dataframe
c.docs.sections     # pure docs horizontalization source
c.retrievalBlocks   # 원문 markdown block long table
c.contextSlices     # LLM 입력용 semantic/detail slice
```

수평화의 뼈대는 `sections`다. 컬럼은 시계열이고 row 구조는 공시 섹션에서 온다.
그 위에 `finance`가 `BS / IS / CIS / CF / SCE`를 채우고, `report`가 더 잘
정리된 정형 공시를 넣는다.

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

### 원본 데이터

```python
c.rawDocs        # 공시 문서 원본 parquet (가공 전)
c.rawFinance     # 재무제표 원본 parquet (가공 전)
c.rawReport      # 정기보고서 원본 parquet (가공 전)
```

---

## AI 기업분석 (dartlab ai)

DartLab의 구조화 데이터 위에서 LLM과 대화하며 기업을 분석할 수 있다 — `uv run dartlab ai`로 웹 UI가 `http://localhost:8400`에 열린다.

재무제표, 주석, 배당, 임원, 지배구조 등 DartLab이 추출한 모든 데이터를 컨텍스트로 제공하고, 자연어 질문에 대한 분석 답변을 스트리밍한다.

지원 provider는 Ollama, ChatGPT OAuth, OpenAI API, Anthropic API, Codex CLI, Claude Code를 포함한다. 웹 UI는 `dartlab ai`로 열고, 같은 런타임은 `dartlab ask`, `dartlab status`, `dartlab setup`, `dartlab excel` 같은 CLI 명령도 제공한다.

---

## 전체 추출

```python
d = c.all()    # 모든 모듈 데이터를 dict로 반환 (progress bar)
# {"BS": df, "IS": df, "CF": df, "dividend": df, "notes": {...},
#  "timeseries": (series, periods), "ratios": RatioResult, ...}
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
import dartlab

dartlab.Company.search("삼성")
# ┌──────────────┬──────────┬────────────────┐
# │ 회사명       ┆ 종목코드 ┆ 업종           │
# └──────────────┴──────────┴────────────────┘

dartlab.Company.listing()   # KRX 전체 상장법인 목록
dartlab.Company.status()    # 로컬 보유 종목 인덱스
c.filings()         # 공시 문서 목록 + DART 뷰어 링크
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

## 데이터

### 출처와 무결성

모든 데이터는 **[OpenDART](https://opendart.fss.or.kr/)**와 **[DART](https://dart.fss.or.kr/)** (금융감독원 전자공시시스템)에서 가져온 공시 데이터다. 개발자는 **단 하나의 숫자도 수정하지 않았으며**, 종목코드·사업연도·보고서유형 등 구조화를 위한 메타데이터 컬럼만 추가했다.

의심스러우면 패키지의 DART 뷰어 링크(`c.filings()`)를 통해 원본 공시와 직접 대조해볼 수 있다.

각 Parquet 파일에는 하나의 기업에 대한 모든 공시 문서가 들어있다.

- **메타데이터**: 종목코드, 회사명, 보고서 유형, 제출일, 사업연도
- **정량 데이터**: 요약재무정보, 재무제표 본문, 주석
- **텍스트 데이터**: 사업의 내용, 감사의견, 위험관리, 임원/주주 현황

### 데이터 릴리즈

| 카테고리 | 릴리즈 태그 | 설명 | 종목 수 |
|----------|------------|------|---------|
| 공시 문서 | [`data-docs`](https://github.com/eddmpython/dartlab/releases/tag/data-docs) | 사업보고서 파싱 데이터 | 260+ |
| 재무 숫자 | [`data-finance-1`](https://github.com/eddmpython/dartlab/releases/tag/data-finance-1) [`2`](https://github.com/eddmpython/dartlab/releases/tag/data-finance-2) [`3`](https://github.com/eddmpython/dartlab/releases/tag/data-finance-3) [`4`](https://github.com/eddmpython/dartlab/releases/tag/data-finance-4) | XBRL 재무제표 숫자 데이터 | 2,700+ |
| 정기보고서 | [`data-report-1`](https://github.com/eddmpython/dartlab/releases/tag/data-report-1) [`2`](https://github.com/eddmpython/dartlab/releases/tag/data-report-2) [`3`](https://github.com/eddmpython/dartlab/releases/tag/data-report-3) [`4`](https://github.com/eddmpython/dartlab/releases/tag/data-report-4) | 정기보고서 데이터 | 2,700+ |

finance와 report 데이터는 GitHub Release 1000 에셋 제한으로 종목코드 범위별 4개 태그로 분할되어 있다. `loadData()`, `downloadAll()`은 이를 자동으로 처리한다.

### 직접 수집한 데이터 사용

DartLab의 데이터 구조(Parquet 스키마)에 맞추면 직접 수집한 데이터로도 기존 기능을 모두 사용할 수 있다. `data/{카테고리}/{종목코드}.parquet` 형태로 파일을 배치하면 모든 property, 추출 모듈, 분석 도구가 정상 동작한다.

### 면책 조항

이 프로젝트는 MIT 라이선스다. 데이터는 OpenDART 공시를 그대로 반영하지만, **상업적 신뢰성을 보장하지 않는다**. 투자나 규제 준수 판단에는 반드시 공식 출처를 확인하라.

> **데이터 업데이트 주기**
>
> 비용이 발생하는 프록시를 사용하지 않고 직접 수집하고 있어서 데이터 업데이트가 매우 느리다. 새로운 종목 추가나 최신 공시 반영에 시간이 걸릴 수 있다.

---

## 왜 만들었나

DART 전자공시에는 재무제표 숫자뿐 아니라 사업의 내용, 위험 요인, 감사의견, 소송 현황, 지배구조 변동 같은 텍스트 정보가 함께 들어있다. 대부분의 도구는 숫자만 뽑아간다. 나머지는 버려진다.

DartLab은 숫자와 텍스트를 모두 추출한다. 분기/반기/사업보고서를 하나의 시간축 위에 정렬하고, 동일 기업 안에서 K-IFRS 개정이나 구조 변경으로 계정명이 바뀌어도 같은 계정을 자동으로 추적한다.

> **현재 범위**
>
> Bridge Matching은 **한 회사 내**에서 연도 간 계정명 변경을 추적하는 기능이다. 재무 엔진은 **회사 간 비교**가 가능하도록 XBRL 계정을 표준 snakeId로 매핑한다. 2,700+ 상장사의 재무제표를 동일 구조로 정규화하여 교차 비교할 수 있다.
>
> 인사이트 엔진은 7개 영역(실적, 수익성, 재무건전성, 현금흐름, 지배구조, 리스크)에 대해 등급을 부여하고, 이상치를 탐지한다. 랭크 엔진은 시장 전체 규모 순위를 산출한다.
>
> 텍스트 분석 영역은 **별도 프로젝트에서 추진 중인 전문 텍스트 분석 모듈**을 DartLab에 통합할 계획이다.
>
> 종목 하나가 아니라 시장 전체를 한 번에 분석할 수 있는 도구가 최종 목표다.

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
- [x] 계정 표준화 엔진 — 2,700+ 상장사 교차 비교
- [x] 분기별 시계열 + 재무비율 (c.timeseries, c.ratios)
- [x] 정기보고서 데이터 엔진 (배당, 직원, 최대주주, 감사, 임원)
- [x] 섹터 분류 (WICS 11섹터 — KSIC + 키워드 + 오버라이드)
- [x] 인사이트 등급 엔진 (7영역: 실적, 수익성, 건전성, 현금흐름, 지배구조, 리스크 + 종합)
- [x] 이상치 탐지 (Z-score + 도메인 규칙, 재무 지표 30개+)
- [x] 시장 규모 순위 (매출, 자산, 성장률 — 전체 + 섹터 내)
- [x] AI 기업분석 웹 인터페이스 (dartlab ai)
- [x] LLM provider 지원 (Ollama, OpenAI, Anthropic, ChatGPT OAuth, Codex CLI, Claude Code)
- [ ] Company `profile` 보고서 뷰 (변화 지점 중심, terminal/notebook 문서형)
- [ ] Compare UX 재정리 (`index/show/trace` 철학으로 개선 예정)
- [x] EDGAR Company UX를 DART Company 수준으로 정렬
- [x] EDGAR (US SEC) 재무 데이터 통합
- [ ] 텍스트 분석 모듈 통합 (별도 프로젝트에서 배치 예정)
- [ ] 정량 + 정성 교차 검증
- [ ] 시각화

## 기여

이슈와 PR을 환영합니다. 제출 전 확인사항:

- 새 기능은 `experiments/`에서 먼저 검증 — 확인 후 `src/`에 반영
- 데이터 매핑 개선(예: `accountMappings.json`)은 실험 결과와 함께 제출

### 개발 환경 설정

```bash
git clone https://github.com/eddmpython/dartlab.git
cd dartlab
uv sync --group dev
pre-commit install
pre-commit install --hook-type commit-msg
uv run pytest tests/ -v -m "not requires_data"
```

질문이나 아이디어가 있으면 [이슈](https://github.com/eddmpython/dartlab/issues)를 열어주세요. 한국어, 영어 모두 가능합니다.

## 후원

<a href="https://buymeacoffee.com/eddmpython">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180"/>
</a>

## 라이선스

MIT License

