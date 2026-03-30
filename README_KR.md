<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="180">

<h3>DartLab</h3>

<p><b>종목코드 하나. 기업의 전체 이야기.</b></p>
<p>DART 전자공시와 EDGAR 공시, 한 줄의 Python으로 구조화하고 비교한다.</p>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&color=c83232&labelColor=050811&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-94a3b8?style=for-the-badge&labelColor=050811" alt="License"></a>
<a href="https://github.com/eddmpython/dartlab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/eddmpython/dartlab/ci.yml?branch=master&style=for-the-badge&labelColor=050811&logo=github&logoColor=white&label=CI" alt="CI"></a>
<a href="https://codecov.io/gh/eddmpython/dartlab"><img src="https://img.shields.io/codecov/c/github/eddmpython/dartlab?style=for-the-badge&labelColor=050811&logo=codecov&logoColor=white&label=Coverage" alt="Coverage"></a>
<a href="https://eddmpython.github.io/dartlab/"><img src="https://img.shields.io/badge/Docs-GitHub_Pages-38bdf8?style=for-the-badge&labelColor=050811&logo=github-pages&logoColor=white" alt="Docs"></a>
<a href="https://eddmpython.github.io/dartlab/blog/"><img src="https://img.shields.io/badge/Blog-120%2B_Articles-fbbf24?style=for-the-badge&labelColor=050811&logo=rss&logoColor=white" alt="Blog"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/">문서</a> · <a href="https://eddmpython.github.io/dartlab/blog/">블로그</a> · <a href="https://huggingface.co/spaces/eddmpython/dartlab">라이브 데모</a> · <a href="https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb">Colab에서 열기</a> · <a href="https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/01_company.py">Molab에서 열기</a> · <a href="README.md">English</a> · <a href="https://buymeacoffee.com/eddmpython">후원</a>
</p>

<p>
<a href="https://huggingface.co/datasets/eddmpython/dartlab-data"><img src="https://img.shields.io/badge/Data-HuggingFace-ffd21e?style=for-the-badge&labelColor=050811&logo=huggingface&logoColor=white" alt="HuggingFace Data"></a>
</p>

</div>

> **참고:** DartLab은 활발히 개발 중이다. 버전 간 API가 바뀔 수 있으며, 문서가 최신 코드를 따라가지 못하는 경우가 있다.

## 목차

- [설치](#설치)
- [빠른 시작](#빠른-시작)
- [DartLab은 무엇인가](#dartlab은-무엇인가)
  - [Company -- 기억할 것 7개](#company--기억할-것-7개)
  - [Scan -- 시장 전체를 한 번에](#scan--시장-전체를-한-번에)
  - [Analysis -- 재무제표 완전 분석](#analysis--재무제표-완전-분석)
  - [Review -- analysis를 보고서로](#review--analysis를-보고서로)
  - [Gather -- 외부 시장 데이터 수집](#gather--외부-시장-데이터-수집)
- [EDGAR (미국)](#edgar-미국)
- [AI 분석](#ai-분석)
- [MCP -- AI 어시스턴트 연동](#mcp--ai-어시스턴트-연동)
- [OpenAPI -- 원본 공공 API](#openapi--원본-공공-api)
- [데이터](#데이터)
- [바로 시작하기](#바로-시작하기)
- [문서](#문서)
- [안정성](#안정성)
- [기여](#기여)

## 설치

**Python 3.12+** 필요.

```bash
# 코어 — 재무제표, sections, Company
uv add dartlab

# pip으로 설치
pip install dartlab
```

### 선택적 확장

핵심 분석, AI, 차트, LLM은 기본 설치에 모두 포함된다. 선택적 확장은 통합 기능을 추가한다:

```bash
uv add "dartlab[mcp]"             # Claude Desktop / Code / Cursor용 MCP 서버
```

### 소스에서 설치

```bash
git clone https://github.com/eddmpython/dartlab.git
cd dartlab && uv pip install -e ".[all]"

# pip으로 설치
pip install -e ".[all]"
```

PyPI 배포는 코어가 안정적일 때만 한다. 최신 기능(감사, 예측, 밸류에이션 등 실험적 기능 포함)을 바로 쓰고 싶다면 git clone을 권장하지만, 간헐적 breaking change에 주의해야 한다.

### 데스크톱 앱 (Alpha)

설치 과정 없이 바로 실행할 수 있는 Windows 런처:

- **[DartLab.exe 다운로드](https://github.com/eddmpython/dartlab-desktop/releases/latest/download/DartLab.exe)** — [dartlab-desktop](https://github.com/eddmpython/dartlab-desktop) 릴리즈
- [DartLab 랜딩 페이지](https://eddmpython.github.io/dartlab/)에서도 다운로드 가능

원클릭 실행 — Python, 터미널, 패키지 관리자 모두 불필요. 웹 UI와 내장 Python 런타임이 번들되어 있다.

> **Alpha** — 동작하지만 불완전. Windows 전용 `.exe` 런처. macOS/Linux는 아직 미지원.

---

**설정 불필요.** `Company`를 생성하면 필요한 데이터를 [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data)에서 자동으로 다운로드한다. EDGAR 데이터는 SEC API에서 가져온다. 두 번째 실행부터는 로컬 캐시로 즉시 로드된다.

## 빠른 시작

### 터미널 — `dartlab` 한 줄이면 시작

```bash
dartlab                          # AI 분석 REPL 시작
dartlab chat 005930              # 삼성전자 바로 분석
```

REPL 안에서 자연어 질문 또는 스킬 명령어 사용:

```
삼성전자 > 수익성 추세와 이익의 질 분석해줘

삼성전자 > /comprehensive        # 종합 투자 분석
삼성전자 > /health               # 재무건전성 체크
삼성전자 > /company SK하이닉스    # 기업 전환
```

### Python — 종목코드 하나면 전체 그림

```python
import dartlab

# 삼성전자 — 원본 공시에서 구조화된 데이터로
c = dartlab.Company("005930")
c.sections                      # 모든 topic, 모든 기간, 나란히
c.show("businessOverview")      # 이 회사가 실제로 뭘 하는지
c.diff("businessOverview")      # 작년 대비 뭐가 바뀌었는지
c.BS                            # 표준화된 재무상태표
c.ratios                        # 47개 재무비율, 이미 계산됨

# Apple — 같은 인터페이스, 다른 나라
us = dartlab.Company("AAPL")
us.show("business")
us.ratios

# 코드 없이 자연어로 질문
dartlab.ask("삼성전자 재무건전성 분석해줘")
```

## DartLab은 무엇인가

상장 기업은 매 분기 수백 페이지를 공시한다. 그 안에 모든 것이 있다 — 매출 추세, 리스크 경고, 경영 전략, 경쟁 포지션. 기업이 직접 쓴, 기업에 대한 완전한 진실.

아무도 읽지 않는다.

읽고 싶지 않아서가 아니다. 같은 정보가 회사마다 다른 이름으로, 연도마다 다른 구조로, 규제기관용 포맷에 흩어져 있기 때문이다. 같은 "매출액"이 `ifrs-full_Revenue`, `dart_Revenue`, `SalesRevenue`로 표기된다.

DartLab은 이 정보에 접근할 수 있는 사람을 바꾼다. 두 가지 엔진으로 원본 공시를 하나의 비교 가능한 맵으로 바꾼다:

### DartLab이 해결하는 두 가지 문제

**1. 같은 기업이 매년 다르게 말한다.**

섹션 수평화는 모든 공시 섹션을 **topic × period** 격자로 정규화한다. 회사·연도·업종별로 다른 제목이 모두 같은 canonical topic으로 수렴한다:

```
                    2025Q4    2024Q4    2024Q3    2023Q4    …
companyOverview       ✓         ✓         ✓         ✓
businessOverview      ✓         ✓         ✓         ✓
productService        ✓         ✓         ✓         ✓
salesOrder            ✓         ✓         —         ✓
employee              ✓         ✓         ✓         ✓
dividend              ✓         ✓         ✓         ✓
audit                 ✓         ✓         ✓         ✓
…                    (98개 canonical topics)
```

```
Before (원본 섹션 제목):                     After (canonical topic):
삼성전자    "II. 사업의 내용"                → businessOverview
현대차      "II. 사업의 내용 [자동차부문]"    → businessOverview
카카오      "2. 사업의 내용"                 → businessOverview
```

전체 상장사 ~95%+ 매핑률. 각 셀에는 heading/body로 분리된 원문, 테이블, 증거가 보존된다. "작년 대비 올해 리스크 기술이 어떻게 바뀌었는지"를 `diff()` 한 줄로 비교할 수 있다.

**2. 모든 기업이 같은 숫자를 다르게 부른다.**

계정 표준화는 모든 XBRL 계정을 하나의 canonical 이름으로 정규화한다:

```
Before (원본 XBRL):                        After (표준화):
회사        account_id          account_nm   →  snakeId    label
삼성전자    ifrs-full_Revenue   수익(매출액)  →  revenue    매출액
SK하이닉스  dart_Revenue        매출액       →  revenue    매출액
LG에너지    Revenue             매출         →  revenue    매출액
```

~97% 매핑률. 회사 간 비교가 수작업 없이 가능하다. `scan("account", ...)` / `scan("ratio", ...)`와 결합하면 **2,700+ 기업**의 동일 지표를 한 번에 비교할 수 있다.

### 원칙 — 접근성과 신뢰성

이 두 원칙이 모든 공개 API를 지배한다:

**접근성** — 종목코드 하나면 끝. `import dartlab` 하나로 모든 기능 접근. 내부 DTO도 추가 import도 데이터 설정도 필요 없다. `Company("005930")` 하나면 [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data)에서 자동 다운로드.

**신뢰성** — 숫자는 DART/EDGAR 원본 그대로. 데이터가 없으면 추정하지 않고 `None`을 반환한다. `trace(topic)`으로 어떤 소스가 왜 채택됐는지 항상 확인 가능. 에러를 삼키지 않는다.

### 데이터 — 모든 게 준비되어 있다

모든 데이터는 [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data)에 사전 구축되어 있다. `Company`를 만들면 필요한 데이터를 자동 다운로드한다 — **설정 없음, API 키 없음, 수동 다운로드 없음.**

| 데이터셋 | 범위 | 크기 |
|----------|------|------|
| DART docs | 2,500+ 기업 | ~8 GB |
| DART finance | 2,700+ 기업 | ~600 MB |
| DART report | 2,700+ 기업 | ~320 MB |
| DART scan | 전종목 사전 계산 | ~271 MB |
| EDGAR | 온디맨드 | SEC API (자동 수집) |

원본에서 직접 수집하고 싶다면 [OpenAPI](#openapi--원본-공공-api)를 참조. 전체 파이프라인(캐시, 최신화, 일괄 수집)은 [데이터](#데이터) 참조.

### Company — 기억할 것 7개

`Company`는 docs/finance/report 3개 소스를 통합한 회사 객체다. 사용자가 알아야 할 메서드는 7개뿐이다.

```python
c = dartlab.Company("005930")

c.index                         # 뭐가 있는지 -- topic 목록 + 가용 기간
c.show("BS")                    # 데이터를 보려면 -- topic별 DataFrame
c.select("IS", ["매출액"])       # 데이터를 뽑으려면 -- finance든 docs든 같은 패턴
c.trace("BS")                   # 어디서 왔는지 -- source provenance
c.diff()                        # 뭐가 바뀌었는지 -- 기간 간 텍스트 변화

c.analysis("수익성")             # 분석하려면 -- 14축 재무분석
c.review()                      # 보고서 보려면 -- 구조화된 전체 보고서
```

`select()`는 어떤 topic이든 동작한다 — `"IS"`, `"BS"`, `"CF"`는 재무제표, `"productService"`, `"salesOrder"` 같은 docs topic은 사업보고서 테이블. 같은 패턴, 단일 진입점.

BS/IS/CF/ratios 등은 `show`의 편의 바로가기로 존재한다. 3개 namespace(`c.docs`, `c.finance`, `c.report`)는 source별 직접 접근이 필요할 때만 사용한다.

### Scan — 시장 전체를 한 번에

`scan()` 하나로 모든 시장 횡단분석에 접근한다. 기억할 것은 `scan` 하나뿐이다.

```python
dartlab.scan()                        # 가이드: 축 목록 + 사용법
dartlab.scan("governance")            # 전종목 지배구조
dartlab.scan("governance", "005930")  # 삼성전자만 필터
dartlab.scan("ratio")                 # 가용 비율 목록
dartlab.scan("ratio", "roe")          # 전종목 ROE
dartlab.scan("account", "매출액")     # 전종목 매출액 시계열
dartlab.scan("cashflow")              # OCF/ICF/FCF + 8유형 패턴 분류
```

| 축 | 라벨 | 설명 |
|----|------|------|
| governance | 거버넌스 | 지분율, 사외이사, 보수비율, 감사의견, 소액주주 분산 |
| workforce | 인력/급여 | 직원수, 평균급여, 인건비율, 1인당부가가치, 성장률, 고액보수 |
| capital | 주주환원 | 배당, 자사주(취득/처분/소각), 증자/감자, 환원 분류 |
| debt | 부채구조 | 사채만기, CP/단기사채, 부채비율, ICR, 위험등급 |
| cashflow | 현금흐름 | OCF/ICF/FCF + 8종 라이프사이클 패턴 |
| audit | 감사리스크 | 감사의견, 감사인변경, 특기사항, 감사독립성비율 |
| insider | 내부자지분 | 최대주주 지분변동, 자기주식, 경영권 안정성 |
| quality | 이익의 질 | Accrual Ratio + CF/NI -- 이익이 현금 뒷받침되는지 |
| liquidity | 유동성 | 유동비율 + 당좌비율 -- 단기 지급능력 |
| digest | 다이제스트 | 시장 전체 공시 변화 다이제스트 |
| network | 네트워크 | 상장사 관계 네트워크 (출자/지분/계열) |
| account | 계정 | 전종목 단일 계정 시계열 (target 필수) |
| ratio | 비율 | 전종목 단일 재무비율 시계열 (target 필수) |

새 축 추가 = 모듈 1개. 다른 코드 수정 불필요.

### Analysis — 재무제표 완전 분석

`analysis()`는 원본 재무제표를 **스토리가 가능한 구조화 데이터**로 가공하는 중간 계층이다. Review(보고서), AI(해석), 사람(직접 해석) 세 소비자 모두를 위한 분석의 중간재 -- analysis 품질이 올라가면 셋 다 좋아진다.

```
Company 전체 데이터 (finance + docs + report)
    ↓  Company.select()  ← 모든 데이터의 단일 접근 경로
analysis()  →  14축 구조화 데이터 (금액 + 비율 + YoY + 플래그)
    ↓              ↓              ↓
 review()       AI(ask)        사람
 보고서화        해석           해석
```

scan과 동일한 3단계 호출 패턴.

```python
dartlab.analysis()                    # 14축 가이드
dartlab.analysis("수익구조")           # 수익구조 축의 분석 항목 목록
dartlab.analysis("수익구조", c)        # 삼성전자 수익구조 분석 실행 -> dict

c.analysis()                          # 가이드
c.analysis("수익성")                   # 수익성 분석
```

| Part | 축 | 설명 | 항목 |
|------|-----|------|------|
| 1-1 | 수익구조 | 이 회사는 무엇으로 돈을 버는가 | 8 |
| 1-2 | 자금조달 | 돈을 어디서 조달하는가 | 9 |
| 1-3 | 자산구조 | 조달한 돈으로 뭘 준비했는가 | 4 |
| 1-4 | 현금흐름 | 실제로 현금은 어떻게 흘렀는가 | 3 |
| 2-1 | 수익성 | 이 회사는 얼마나 잘 벌고 있는가 | 4 |
| 2-2 | 성장성 | 이 회사는 얼마나 빨리 성장하는가 | 3 |
| 2-3 | 안정성 | 이 회사는 망하지 않는가 | 4 |
| 2-4 | 효율성 | 이 회사는 자산을 잘 굴리는가 | 3 |
| 2-5 | 종합평가 | 재무 상태를 한마디로 | 3 |
| 3-1 | 이익품질 | 이익이 진짜인가 | 4 |
| 3-2 | 비용구조 | 비용이 어떻게 움직이는가 | 4 |
| 3-3 | 자본배분 | 번 돈을 어디에 쓰는가 | 5 |
| 3-4 | 투자효율 | 투자가 가치를 만드는가 | 4 |
| 3-5 | 재무정합성 | 재무제표가 서로 맞는가 | 5 |

### Review — analysis를 보고서로

```python
c.review()              # 14개 섹션 전체 보고서
c.review("수익구조")     # 단일 섹션
```

4개 출력 형식: `rich`(터미널), `html`, `markdown`, `json`.

**샘플 보고서** (`c.review().toMarkdown()` 출력):

| 기업 | 업종 | 특징 |
|------|------|------|
| [삼성전자](docs/samples/005930.md) | 반도체 | Mid-cycle FCF 정규화, 사이클 조정 DCF |
| [SK하이닉스](docs/samples/000660.md) | 반도체 | HBM 구조적 성장 vs DRAM/NAND 사이클 |
| [기아](docs/samples/000270.md) | 자동차 | EV 전환 투자 영향, 배당 정책 |
| [한화오션](docs/samples/042660.md) | 조선 | 적자 턴어라운드, 수주잔고 기반 밸류에이션 괴리 |
| [SK텔레콤](docs/samples/017670.md) | 통신 | 안정 배당주, 지주사 성격 자회사 구조 |

각 보고서 하단에 **분석 한계** 섹션으로 모델 제약을 기록합니다.

### Reviewer — review + AI 해석

review 위에 AI 종합의견을 올린다:

```python
c.reviewer()                                    # 전체 + AI
c.reviewer(guide="반도체 사이클 관점에서 평가해줘")  # 도메인 특화
```

### Gather — 외부 시장 데이터 수집

`gather()` 하나로 주가, 수급, 거시지표, 뉴스를 수집한다 — 전부 **Polars DataFrame**.

```python
dartlab.gather()                              # 가이드 -- 4축
dartlab.gather("price", "005930")             # KR OHLCV 시계열 (기본 1년)
dartlab.gather("price", "AAPL", market="US")  # US 주가
dartlab.gather("flow", "005930")              # 외국인/기관 수급 (KR)
dartlab.gather("macro")                       # KR 12개 거시지표
dartlab.gather("macro", "FEDFUNDS")           # 단일 지표 (자동 US 감지)
dartlab.gather("news", "삼성전자")             # Google News RSS
```

Company 바인딩: `c.gather("price")` — 종목코드 다시 안 넘겨도 된다.

### 5계층 관계

```
gather()     외부 시장 데이터 (4축)     -- 주가, 수급, 거시, 뉴스
scan()       시장 전체 횡단 (13축)     -- 종목 간 비교/스크리닝
analysis()   단일 종목 심층 (14축)     -- 재무제표 완전 분석
c.review()   analysis -> 구조화 보고서  -- 블록-템플릿 파이프라인
c.reviewer() review + AI 해석          -- 섹션별 종합의견
```

### 아키텍처 — 책임 기반 레이어

```
L0  core/        프로토콜, 재무 유틸, docs 유틸, 레지스트리
L1  providers/   국가별 데이터 (DART, EDGAR, EDINET)
    gather/      외부 시장 데이터 (Naver, Yahoo, FRED)
    scan/        시장 횡단분석 (13축)
L2  analysis/    8대 분석 영역 (strategy → macro)
    review/      블록-템플릿 보고서 조립
L3  ai/          LLM 기반 분석 (5개 provider)
```

import 방향은 CI에서 강제한다 — 역방향 의존 불허. 4개 축이 자연스럽게 합성된다: **Company**(한 기업, 깊이) → **Analysis**(판단) → **Review**(표현) → **Scan**(전 기업, 폭).

### 확장성 — Core 수정 0줄

새 국가를 추가할 때 core 코드를 수정할 필요가 없다:

1. `providers/` 아래에 provider 패키지 생성
2. `canHandle(code) -> bool`과 `priority() -> int` 구현
3. `pyproject.toml`의 `entry_points`에 등록

```python
dartlab.Company("005930")  # → DART provider (priority 10)
dartlab.Company("AAPL")    # → EDGAR provider (priority 20)
```

facade가 priority 순으로 provider를 순회하여 첫 번째 매칭을 사용한다.

## EDGAR (미국)

동일한 `Company` 인터페이스, 동일한 계정 표준화 파이프라인, 다른 데이터 소스. EDGAR 데이터는 SEC API에서 자동 수집된다 — 사전 다운로드 불필요:

```python
us = dartlab.Company("AAPL")

us.sections                         # 10-K/10-Q sections (heading/body 분리)
us.show("business")                 # 사업 설명
us.show("10-K::item1ARiskFactors")  # 리스크 요인
us.BS                               # SEC XBRL 재무상태표
us.ratios                           # 동일한 47개 비율
us.diff("10-K::item7Mdna")          # MD&A 텍스트 변화
```

인터페이스가 동일하다 — 같은 메서드, 같은 구조:

```python
# Korea (DART)                          # US (EDGAR)
c = dartlab.Company("005930")           c = dartlab.Company("AAPL")
c.sections                              c.sections
c.show("businessOverview")              c.show("business")
c.BS                                    c.BS
c.ratios                                c.ratios
c.diff("businessOverview")              c.diff("10-K::item7Mdna")
```

### DART vs EDGAR 네임스페이스 차이

|               | DART           | EDGAR          |
|---------------|:--------------:|:--------------:|
| `docs`        | ✓              | ✓              |
| `finance`     | ✓              | ✓              |
| `report`      | ✓ (28개 API 타입) | ✗ (해당 없음) |
| `profile`     | ✓              | ✓              |

DART는 28개 정형 공시 API가 있는 `report` 네임스페이스가 있다 (배당, 지배구조, 임원 보상 등). SEC는 공시 구조가 다르므로 EDGAR에는 해당 없음.

**EDGAR topic 네이밍**: `{formType}::{itemId}` 형식. 단축 별칭도 사용 가능:

```python
us.show("10-K::item1Business")     # 전체 형식
us.show("business")                # 단축 별칭
us.show("risk")                    # → 10-K::item1ARiskFactors
us.show("mdna")                    # → 10-K::item7Mdna
```

## AI 분석

> **실험적** — AI 분석 레이어와 `analysis/` 엔진은 활발히 개발 중이다. API, 출력 형식, 사용 가능한 도구가 버전 간 변경될 수 있다.

> **Tip:** 코드를 모르거나 자연어를 선호한다면 `dartlab.ask()`를 사용하세요. AI 비서가 데이터 다운로드부터 분석까지 모든 것을 처리합니다.

DartLab의 AI는 엔진이 이미 계산한 전기간 비교가능/기업간 비교가능 데이터 위에서 동작한다 — LLM은 *왜*를 설명하지, 숫자를 만들어내지 않는다. **코드 없이** 자연어로 질문하면 DartLab이 모든 것을 처리한다: 데이터 선택, 컨텍스트 조립, 답변 스트리밍.

```bash
# 터미널 한 줄 — Python 코드 필요 없음
dartlab ask "삼성전자 재무건전성 분석해줘"
```

DartLab이 데이터를 구조화하고, 관련 컨텍스트(재무제표, 인사이트, 섹터 벤치마크)를 선택해서 LLM에 전달한다:

```
$ dartlab ask "삼성전자 재무건전성 분석해줘"

삼성전자의 재무건전성은 A등급입니다.

▸ 부채비율 31.8% — 업종 평균(45.2%) 대비 양호
▸ 유동비율 258.6% — 200% 안전 기준 상회
▸ 이자보상배수 22.1배 — 이자 부담 매우 낮음
▸ ROE 회복세: 1.6% → 10.2% (4분기 연속 개선)

[데이터 출처: 2024Q4 사업보고서, dartlab insights 엔진]
```

`최근 7일 수주공시 알려줘` 같은 실시간 공시목록 질문은 `OpenDART API 키`를 사용한다. 프로젝트 `.env`에 저장하거나 UI Settings에서 관리할 수 있다.

2-Tier 아키텍처로 기본 분석은 어떤 provider에서든 동작하고, tool-calling provider(OpenAI, Claude)는 대화 중 추가 데이터를 요청해 더 깊이 분석할 수 있다.

### Python API

```python
import dartlab

# 스트리밍 출력 + 전체 텍스트 반환
answer = dartlab.ask("삼성전자 재무건전성 분석해줘")

# provider + model 지정
answer = dartlab.ask("삼성전자 분석", provider="openai", model="gpt-4o")

# 데이터 필터링
answer = dartlab.ask("삼성전자 핵심 포인트", include=["BS", "IS"])

# 분석 패턴
answer = dartlab.ask("삼성전자 분석", pattern="financial")

# 에이전트 모드 — LLM이 도구를 선택하여 심화 분석
answer = dartlab.chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")
```

### CLI

```bash
# provider 설정 — 무료 provider 우선
dartlab setup              # 전체 provider 목록
dartlab setup gemini       # Google Gemini (무료)
dartlab setup groq         # Groq (무료)

# 상태 확인
dartlab status             # 전체 provider (테이블 뷰)
dartlab status --cost      # 누적 토큰/비용 통계

# 질문 (스트리밍 기본값)
dartlab ask "삼성전자 재무건전성 분석해줘"
dartlab ask "AAPL risk analysis" -p ollama
dartlab ask --continue "배당 추세는?"

# 보고서 자동 생성
dartlab report "삼성전자" -o report.md

dartlab --help             # 전체 명령어 확인
```

<details>
<summary>전체 CLI 명령어 (15개)</summary>

| 분류 | 명령어 | 설명 |
|------|--------|------|
| 데이터 | `show` | topic 열기 |
| 데이터 | `search` | 종목 검색 |
| 데이터 | `statement` | BS / IS / CF / SCE 출력 |
| 데이터 | `sections` | 원본 docs sections |
| 데이터 | `profile` | 회사 인덱스, facts |
| 데이터 | `modules` | 사용 가능 모듈 목록 |
| AI | `ask` | 자연어 질문 |
| AI | `report` | 분석 보고서 자동 생성 |
| 내보내기 | `excel` | Excel 내보내기 (experimental) |
| 수집 | `collect` | 데이터 다운로드 / 갱신 / 배치 수집 |
| 수집 | `collect --check` | 새 공시 감지 (freshness 체크) |
| 수집 | `collect --incremental` | 누락 공시만 증분 수집 |
| 서버 | `ai` | AI 분석 서버 |
| 서버 | `status` | Provider 연결 상태 |
| 서버 | `setup` | Provider 설정 마법사 |
| MCP | `mcp` | MCP stdio 서버 실행 |
| 플러그인 | `plugin` | 플러그인 생성 / 관리 |

</details>

### Provider

**무료 API 키 provider** — 가입하고 키만 넣으면 바로 분석:

| Provider | 무료 한도 | 모델 | 설정 |
|----------|-----------|------|------|
| `gemini` | Gemini 2.5 Pro/Flash 무료 | Gemini 2.5 | `dartlab setup gemini` |
| `groq` | 6K–30K TPM 무료 | LLaMA 3.3 70B | `dartlab setup groq` |
| `cerebras` | 1M tokens/day 영구 무료 | LLaMA 3.3 70B | `dartlab setup cerebras` |
| `mistral` | 1B tokens/month 무료 | Mistral Small | `dartlab setup mistral` |

**기타 provider:**

| Provider | 인증 | 비용 | Tool Calling |
|----------|------|------|:---:|
| `oauth-codex` | ChatGPT 구독 (Plus/Team/Enterprise) | 구독에 포함 | Yes |
| `openai` | API 키 (`OPENAI_API_KEY`) | 토큰당 과금 | Yes |
| `ollama` | 로컬 설치, 계정 불필요 | 무료 | 모델에 따라 다름 |
| `codex` | Codex CLI 로컬 설치 | 무료 (Codex 세션 사용) | Yes |
| `custom` | OpenAI 호환 엔드포인트 | 다양 | 다양 |

**자동 전환:** 여러 무료 API 키를 등록하면 하나가 한도를 초과할 때 자동으로 다음 provider로 전환한다. `provider="free"`로 fallback 체인 활성화:

```python
dartlab.ask("삼성전자 분석", provider="free")
```

**Claude provider가 없는 이유:** Anthropic은 OAuth 기반 접근을 제공하지 않는다. OAuth 없이는 사용자가 기존 구독으로 인증할 방법이 없어서 API 키를 직접 입력하게 해야 하는데, 이는 DartLab의 마찰 없는 설계에 맞지 않는다. Anthropic이 향후 OAuth를 지원하면 Claude provider를 추가할 예정이다. 현재 Claude는 **MCP**로 사용 가능 — Claude Desktop, Claude Code, Cursor에서 DartLab의 60개 도구를 직접 호출할 수 있다.

**`oauth-codex`**가 권장 provider다 — ChatGPT 구독이 있으면 API 키 없이 바로 작동한다. `dartlab setup oauth-codex`로 인증.

### 프로젝트 설정 (`.dartlab.yml`)

```yaml
company: 005930         # 기본 종목
provider: openai        # 기본 LLM provider
model: gpt-4o           # 기본 모델
verbose: false
```

## MCP — AI 어시스턴트 연동

DartLab은 [MCP](https://modelcontextprotocol.io/) 서버를 내장하고 있다. 60개 도구 (글로벌 16 + 기업별 44)를 Claude Desktop, Claude Code, Cursor 등 MCP 호환 클라이언트에 노출한다.

```bash
uv add "dartlab[mcp]"
```

### Claude Desktop

`claude_desktop_config.json`에 추가:

```json
{
  "mcpServers": {
    "dartlab": {
      "command": "uv",
      "args": ["run", "dartlab", "mcp"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add dartlab -- uv run dartlab mcp
```

또는 `~/.claude/settings.json`에 추가:

```json
{
  "mcpServers": {
    "dartlab": {
      "command": "uv",
      "args": ["run", "dartlab", "mcp"]
    }
  }
}
```

### Cursor

`.cursor/mcp.json`에 Claude Desktop과 동일한 형식으로 추가.

### 사용 가능한 기능

연결하면 AI 어시스턴트가 다음을 수행할 수 있다:

- **검색** — 이름이나 코드로 기업 찾기 (`search_company`)
- **공시 조회** — 임의 topic의 공시 데이터 열기 (`show_topic`, `list_topics`, `diff_topic`)
- **재무** — BS, IS, CF, 재무비율 (`get_financial_statements`, `get_ratios`)
- **분석** — 인사이트, 섹터 순위, 밸류에이션 (`get_insight`, `get_ranking`)
- **EDGAR** — 미국 기업도 동일한 도구로 지원 (`stock_code: "AAPL"`)

플랫폼별 설정 자동 생성:

```bash
dartlab mcp --config claude-desktop
dartlab mcp --config claude-code
dartlab mcp --config cursor
```

## OpenAPI — 원본 공공 API

원본 공시 API를 직접 다루고 싶을 때 source-native wrapper를 쓴다.

### OpenDart (한국)

> **참고:** `Company`는 API 키가 **필요 없다** — 사전 구축 데이터셋으로 동작한다.
> `OpenDart`는 DART 원본 API를 직접 사용하므로 [opendart.fss.or.kr](https://opendart.fss.or.kr) 에서 API 키가 필요하다 (무료).
> 전체 시장 최근 공시목록을 AI가 직접 찾는 기능도 이 키를 사용하며, UI Settings에서 `OpenDART API 키`를 관리할 수 있다.

```python
from dartlab import OpenDart

d = OpenDart()
d.search("카카오", listed=True)
d.filings("삼성전자", "2024")
d.finstate("삼성전자", 2024)
d.report("삼성전자", "배당", 2024)
```

### OpenEdgar (미국)

> **API 키 불필요.** SEC EDGAR는 공공 API다 — 등록 없이 사용 가능.

```python
from dartlab import OpenEdgar

e = OpenEdgar()
e.search("Apple")
e.filings("AAPL", forms=["10-K", "10-Q"])
e.companyFactsJson("AAPL")
```

## 데이터

**설정 불필요.** `Company`를 생성하면 해당 종목의 데이터를 자동으로 다운로드한다.

| 데이터셋 | 규모 | 용량 | 출처 |
|----------|------|------|------|
| DART docs | 2,500+ 기업 | ~8 GB | [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/docs) |
| DART finance | 2,700+ 기업 | ~600 MB | [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/finance) |
| DART report | 2,700+ 기업 | ~320 MB | [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/report) |
| DART scan | 전종목 횡단분석 프리빌드 | ~271 MB | [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/scan) |
| EDGAR | 주문형 | — | SEC API (자동 수집) |

### 3단계 데이터 파이프라인

```
dartlab.Company("005930")
  │
  ├─ 1. 로컬 캐시 ────── 이미 있으면 즉시 반환 (instant)
  │
  ├─ 2. HuggingFace ──── 자동 다운로드 (수 초, 키 불필요)
  │
  └─ 3. DART API ──────── API 키로 직접 수집 (키 필요)
```

HuggingFace에 없는 기업은 DART에서 직접 수집한다 — API 키가 필요하다:

```bash
dartlab setup dart-key
```

### Freshness — 자동 업데이트 감지

3-Layer freshness 시스템으로 로컬 데이터를 최신 상태로 유지한다:

| Layer | 방식 | 비용 |
|-------|------|------|
| L1 | HTTP HEAD → HuggingFace ETag 비교 | ~0.5초, 수백 바이트 |
| L2 | 로컬 파일 나이 (90일 TTL 폴백) | 즉시 (로컬) |
| L3 | DART API → `rcept_no` diff (API 키 필요) | API 1회, ~1초 |

`Company`를 열면 새 공시가 있는지 자동으로 확인한다:

```python
c = dartlab.Company("005930")
# [dartlab] ⚠ 005930 — 새 공시 2건 발견 (사업보고서 (2024.12))
#   • 증분 수집: dartlab collect --incremental 005930
#   • 또는 Python: c.update()

c.update()  # 누락된 공시만 증분 수집
```

```bash
# CLI freshness 체크
dartlab collect --check 005930         # 단일 종목
dartlab collect --check                # 전체 로컬 종목 스캔 (7일)

# 증분 수집 — 누락된 공시만
dartlab collect --incremental 005930   # 단일 종목
dartlab collect --incremental          # 새 공시 있는 전체 종목
```

### 배치 수집 (DART API)

```bash
dartlab collect --batch                    # 전체 상장, 미수집만
dartlab collect --batch -c finance 005930  # 특정 카테고리 + 종목
dartlab collect --batch --mode all         # 전체 재수집
```

## 바로 시작하기

### 라이브 데모

**[라이브 데모 열기](https://huggingface.co/spaces/eddmpython/dartlab)** -- 설치 없이 브라우저에서 바로

### 노트북

| 기능 | 설명 | Colab | Molab |
|------|------|-------|-------|
| **Company** | `Company("005930")` -- index, show, select, trace, diff + 재무 바로가기 | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/01_company.py) |
| **Scan** | `scan()` -- 13축 전종목 횡단 스캔, 2,700+ 기업 | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/02_scan.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/02_scan.py) |
| **Review** | `c.review()` -- 14개 섹션 구조화 보고서 + `c.reviewer()` AI 해석 | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/03_review.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/03_review.py) |
| **Gather** | `gather()` -- 주가, 수급, 거시, 뉴스를 한 번에 | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/04_gather.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/04_gather.py) |

<details>
<summary>로컬에서 Marimo로 실행</summary>

```bash
uv add dartlab marimo
marimo edit notebooks/marimo/01_company.py
marimo edit notebooks/marimo/02_scan.py
marimo edit notebooks/marimo/03_review.py
marimo edit notebooks/marimo/04_gather.py
```

</details>

## 문서

- 문서: https://eddmpython.github.io/dartlab/
- Sections 가이드: https://eddmpython.github.io/dartlab/docs/getting-started/sections
- 빠른 시작: https://eddmpython.github.io/dartlab/docs/getting-started/quickstart
- API 개요: https://eddmpython.github.io/dartlab/docs/api/overview
- 초보자 가이드: https://eddmpython.github.io/dartlab/blog/dartlab-easy-start/

### 블로그

[DartLab 블로그](https://eddmpython.github.io/dartlab/blog/)는 실전 공시 분석 주제를 다룬다 — 재무제표 읽는 법, 공시 패턴 해석, 리스크 신호 포착 등. 3개 카테고리 120편 이상:

- **공시 제도** — DART/EDGAR 공시의 구조와 작동 원리
- **보고서 읽기** — 감사보고서, 잠정실적, 재작성 등 실전 가이드
- **재무 해석** — 재무제표, 비율, 공시 신호 해석

## 안정성

| Tier | 범위 |
|------|------|
| **Stable** | DART Company (sections, show, trace, diff, BS/IS/CF, CIS, index, filings, profile), EDGAR Company core, valuation, forecast, simulation |
| **Beta** | EDGAR 파워유저 (SCE, notes, freq, coverage), insights, distress, ratios, timeseries, network, governance, workforce, capital, debt, chart/table/text 도구, ask/chat, OpenDart, OpenEdgar, Server API, MCP, CLI 서브커맨드 |
| **Experimental** | AI 도구 호출, export |
| **Alpha** | Desktop App (Windows .exe) — 동작하지만 불완전, Sections Viewer — 수평화된 공시 뷰어, 아직 체계 미완성 |

자세한 기준은 [docs/stability.md](docs/stability.md)를 본다.

## 기여

이 프로젝트는 **엔진 변경 전에 실험으로 먼저 검증**하는 방식을 선호한다.

- **실험 폴더**: `experiments/XXX_camelCaseName/` — 각 파일은 독립 실행 가능해야 하고, docstring에 실제 결과가 포함되어야 한다
- **데이터 기여** (`accountMappings.json`, `sectionMappings.json` 등): 실험 증거가 있을 때만 수용 — 수작업 일괄 수정 불가
- 한국어/영어 이슈와 PR 모두 환영

## 라이선스

MIT
