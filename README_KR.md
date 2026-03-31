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
  - [데이터 -- 모든 게 준비되어 있다](#데이터--모든-게-준비되어-있다)
  - [Company -- 두 가지 문제](#company--두-가지-문제)
  - [Scan -- 시장 전체를 한 번에](#scan--시장-전체를-한-번에)
  - [Gather -- 외부 시장 데이터](#gather--외부-시장-데이터)
  - [Analysis -- 숫자에서 스토리로](#analysis--숫자에서-스토리로)
  - [Review -- analysis를 보고서로](#review--analysis를-보고서로)
  - [AI -- 적극적 분석가](#ai--적극적-분석가)
- [EDGAR (미국)](#edgar-미국)
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
# 코어 -- 재무제표, sections, Company
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

---

**설정 불필요.** `Company`를 생성하면 필요한 데이터를 [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data)에서 자동으로 다운로드한다. EDGAR 데이터는 SEC API에서 가져온다. 두 번째 실행부터는 로컬 캐시로 즉시 로드된다.

## 빠른 시작

```python
import dartlab

# 삼성전자 -- 원본 공시에서 구조화된 데이터로
c = dartlab.Company("005930")
c.sections                      # 모든 topic, 모든 기간, 나란히
c.show("businessOverview")      # 이 회사가 실제로 뭘 하는지
c.diff("businessOverview")      # 작년 대비 뭐가 바뀌었는지
c.BS                            # 표준화된 재무상태표
c.ratios                        # 재무비율, 이미 계산됨

# Apple -- 같은 인터페이스, 다른 나라
us = dartlab.Company("AAPL")
us.show("business")
us.ratios

# 코드 없이 자연어로 질문
dartlab.ask("삼성전자 재무건전성 분석해줘")
```

## DartLab은 무엇인가

상장 기업은 매 분기 수백 페이지를 공시한다. 그 안에 모든 것이 있다 -- 매출 추세, 리스크 경고, 경영 전략, 경쟁 포지션. 기업이 직접 쓴, 기업에 대한 완전한 진실.

아무도 읽지 않는다.

읽고 싶지 않아서가 아니다. 같은 정보가 회사마다 다른 이름으로, 연도마다 다른 구조로, 규제기관용 포맷에 흩어져 있기 때문이다. 같은 "매출액"이 `ifrs-full_Revenue`, `dart_Revenue`, `SalesRevenue`로 표기된다.

DartLab은 하나의 전제 위에 서 있다: **모든 기간은 비교 가능해야 하고, 모든 회사는 비교 가능해야 한다.** 이것 없이는 분석이 불가능하다 -- 양식을 비교하는 것이지 기업을 비교하는 게 아니다. DartLab의 모든 기능은 이 전제를 현실로 만들기 위해 존재한다.

두 가지 엔진으로 원본 공시를 하나의 비교 가능한 맵으로 바꾼다.

| 레이어 | 엔진 | 하는 일 | 진입점 |
|--------|------|---------|--------|
| Data | [Data](ops/data.md) | HuggingFace 사전 구축 데이터, 자동 다운로드 | `Company("005930")` |
| L0/L1 | [Company](ops/company.md) | 섹션 수평화 + 계정 표준화 | `c.show()`, `c.select()` |
| L1 | [Scan](ops/scan.md) | 전 종목 횡단 비교, 13축 | `dartlab.scan()` |
| L1 | [Gather](ops/gather.md) | 외부 시장 데이터 (주가, 수급, 매크로, 뉴스) | `dartlab.gather()` |
| L2 | [Analysis](ops/analysis.md) | 14축 스토리텔링 분석 (6막 구조) | `c.analysis()` |
| L2 | [Review](ops/review.md) | 분석을 서사 보고서로 | `c.review()` |
| L0 | [Search](ops/search.md) | 공시 시맨틱 검색 *(alpha)* | `dartlab.search()` |
| L3 | [AI](ops/ai.md) | 적극적 분석가 — 코드 실행 + 해석 | `dartlab.ask()` |

### 데이터 -- 모든 게 준비되어 있다

> 설계: [ops/data.md](ops/data.md)

모든 데이터는 [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data)에 사전 구축되어 있다. `pip install dartlab`하고 `Company("005930")` -- 그게 끝이다. API 키 없음, 수동 다운로드 없음, 데이터 파이프라인 설정 없음.

왜 HuggingFace인가? DART 원본 공시는 수천 개의 ZIP 파일과 XML 조각에 흩어져 있다. 이걸 파싱하고 정규화하고 구조화하려면 기업 하나당 수 시간이 걸린다. DartLab이 이 전체 파이프라인을 사전 구축하고 결과를 배포해서, 사용자는 이 과정을 겪을 필요가 없다.

| 데이터셋 | 범위 | 크기 |
|----------|------|------|
| DART docs | 2,500+ 기업 | ~8 GB |
| DART finance | 2,700+ 기업 | ~600 MB |
| DART report | 2,700+ 기업 | ~320 MB |
| DART scan | 전종목 사전 계산 | ~271 MB |
| EDGAR | 온디맨드 | SEC API (자동 수집) |

데이터 파이프라인은 3단계다: 로컬 캐시 (즉시) -> HuggingFace (자동 다운로드, 키 불필요) -> DART API (직접 수집, 키 필요). 대부분의 사용자는 처음 두 단계를 벗어나지 않는다.

### Company -- 두 가지 문제

> 설계: [ops/company.md](ops/company.md)

모든 기간과 모든 회사가 비교 가능하려면, 두 가지 장벽을 넘어야 한다:

**1. 같은 기업이 매년 다르게 말한다.**

섹션 수평화는 모든 공시 섹션을 **topic x period** 격자로 정규화한다. 회사/연도/업종별로 다른 제목이 모두 같은 canonical topic으로 수렴한다:

```
                    2025Q4    2024Q4    2024Q3    2023Q4    ...
companyOverview       v         v         v         v
businessOverview      v         v         v         v
productService        v         v         v         v
employee              v         v         v         v
dividend              v         v         v         v
```

```
Before (원본 섹션 제목):                     After (canonical topic):
삼성전자    "II. 사업의 내용"                -> businessOverview
현대차      "II. 사업의 내용 [자동차부문]"    -> businessOverview
카카오      "2. 사업의 내용"                 -> businessOverview
```

전체 상장사 ~95%+ 매핑률. 각 셀에는 heading/body로 분리된 원문, 테이블, 증거가 보존된다.

**2. 모든 기업이 같은 숫자를 다르게 부른다.**

계정 표준화는 모든 XBRL 계정을 하나의 canonical 이름으로 정규화한다:

```
Before (원본 XBRL):                        After (표준화):
회사        account_id          account_nm   ->  snakeId    label
삼성전자    ifrs-full_Revenue   수익(매출액)  ->  revenue    매출액
SK하이닉스  dart_Revenue        매출액       ->  revenue    매출액
LG에너지    Revenue             매출         ->  revenue    매출액
```

~97% 매핑률. 회사 간 비교가 수작업 없이 가능하다.

`Company`는 세 가지 데이터 소스 -- docs (전문 공시), finance (XBRL 재무제표), report (DART API 정형 데이터) -- 를 하나의 객체로 통합한다:

```python
c = dartlab.Company("005930")

c.index                         # 뭐가 있는지 -- topic 목록 + 가용 기간
c.show("BS")                    # 데이터를 보려면 -- topic별 DataFrame
c.select("IS", ["매출액"])       # 데이터를 뽑으려면 -- finance든 docs든 같은 패턴
c.trace("BS")                   # 어디서 왔는지 -- source provenance
c.diff()                        # 뭐가 바뀌었는지 -- 기간 간 텍스트 변화

c.analysis("수익성")             # 분석하려면 -- 재무분석
c.review()                      # 보고서 보려면 -- 구조화된 전체 보고서
```

`select()`는 어떤 topic이든 동작한다 -- `"IS"`, `"BS"`, `"CF"`는 재무제표, `"productService"`, `"salesOrder"` 같은 docs topic은 사업보고서 테이블. 같은 패턴, 단일 진입점.

### Scan -- 시장 전체를 한 번에

> 설계: [ops/scan.md](ops/scan.md)

모든 회사가 비교 가능하다면, 다음 질문은 자연스럽다: 비교하라.

Company는 한 기업을 깊이 본다. Scan은 전 기업을 가로로 본다. "ROE가 가장 높은 기업은?", "올해 감사인을 바꾼 기업은?" 같은 질문은 시장 전체를 횡단하는 분석이 필요하다.

`scan()` 하나로 전부 접근한다.

```python
dartlab.scan()                        # 가이드: 축 목록 + 사용법
dartlab.scan("governance")            # 전종목 지배구조
dartlab.scan("governance", "005930")  # 삼성전자만 필터
dartlab.scan("ratio", "roe")          # 전종목 ROE
dartlab.scan("account", "매출액")     # 전종목 매출액 시계열
dartlab.scan("cashflow")              # OCF/ICF/FCF + 8유형 패턴 분류
```

| 축 | 라벨 | 설명 |
|----|------|------|
| governance | 거버넌스 | 지분율, 사외이사, 보수비율, 감사의견 |
| workforce | 인력/급여 | 직원수, 평균급여, 인건비율, 1인당부가가치 |
| capital | 주주환원 | 배당, 자사주(취득/처분/소각), 증자/감자 |
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

### Gather -- 외부 시장 데이터

> 설계: [ops/gather.md](ops/gather.md)

Company와 Scan은 공시 데이터 -- 기업이 제출한 것 -- 를 다룬다. 하지만 투자자는 시장 데이터도 필요하다: 주가, 기관/외국인 수급, 거시지표, 뉴스. Gather가 공시와 시장 사이의 간극을 메운다.

`gather()` 하나로 외부 시장 데이터를 수집한다 -- 전부 **Polars DataFrame**.

```python
dartlab.gather()                              # 가이드 -- 4축
dartlab.gather("price", "005930")             # KR OHLCV 시계열 (기본 1년)
dartlab.gather("price", "AAPL", market="US")  # US 주가
dartlab.gather("flow", "005930")              # 외국인/기관 수급 (KR)
dartlab.gather("macro")                       # KR 거시지표
dartlab.gather("macro", "FEDFUNDS")           # 단일 지표 (자동 US 감지)
dartlab.gather("news", "삼성전자")             # Google News RSS
```

Company 바인딩: `c.gather("price")` -- 종목코드 다시 안 넘겨도 된다.

### Analysis -- 숫자에서 스토리로

> 설계: [ops/analysis.md](ops/analysis.md)

모든 회사에는 스토리가 있다. 수익구조가 무엇을 하는지 말하고, 수익성이 얼마나 잘하는지 보여주고, 현금흐름이 이익이 진짜인지 확인하고, 안정성이 살아남을 수 있는지 말하고, 자본배분이 번 돈을 어디에 쓰는지 보여주고, 전망이 과거와 미래를 연결한다. 이 6막은 인과 사슬이다 -- 각 막이 다음 막을 설명한다.

원본 재무제표는 숫자다. 매출이 302조원이라는 사실만으로는 이 기업이 건강한지, 성장 중인지, 위험한지 알 수 없다. Analysis가 이 간극을 메운다 -- 단절된 비율의 대시보드가 아니라, 각 숫자가 스토리 속에서 자기 자리를 갖는 서사로.

`analysis()`는 재무제표를 구조화된 스토리 데이터로 가공하는 중간 계층이다. Review(보고서), AI(해석), 사람(직접 해석) 세 소비자 모두를 위한 분석의 중간재 -- analysis 품질이 올라가면 셋 다 좋아진다.

```
Company 전체 데이터 (finance + docs + report)
    |  Company.select()  <- 모든 데이터의 단일 접근 경로
analysis()  ->  14축 구조화 데이터 (금액 + 비율 + YoY + 플래그)
    |              |              |
 review()       AI(ask)        사람
 보고서화        해석           해석
```

scan과 동일한 3단계 호출 패턴.

```python
dartlab.analysis()                    # 가이드: 전체 축 목록
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

### Review -- analysis를 보고서로

> 설계: [ops/review.md](ops/review.md)

Analysis는 구조화된 데이터를 만든다. Review는 이걸 6막 서사를 따르는 사람이 읽을 수 있는 보고서로 조립한다 -- "이 회사는 뭘 하는가"에서 "얼마의 가치가 있는가"까지. 각 analysis 축이 테이블, 플래그, 서사와 함께 보고서의 한 섹션이 되고, 막 사이에는 인과 전환 문장이 연결된다.

```python
c.review()              # 전체 보고서
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
| [LG화학](docs/samples/051910.md) | 화학/배터리 | EBITDA 음수 EV/Sales fallback, 사업부 괴리 |
| [SK](docs/samples/034730.md) | 지주사 | 지주사 할인, NAV/SOTP 괴리 |
| [엔씨소프트](docs/samples/036570.md) | 게임 | 파이프라인 의존, R&D 기반 밸류에이션 |
| [아모레퍼시픽](docs/samples/090430.md) | 소비재 | 브랜드 가치, 채널 전환(면세점→이커머스) |
| [현대제철](docs/samples/004020.md) | 철강/사이클 | Mid-cycle 정규화, 중국 과잉 공급 |

각 보고서 하단에 **분석 한계** 섹션으로 모델 제약을 기록한다.

**Reviewer**는 review 위에 AI 종합의견을 올린다:

```python
c.reviewer()                                    # 전체 + AI
c.reviewer(guide="반도체 사이클 관점에서 평가해줘")  # 도메인 특화
```

### Search -- 공시를 의미로 검색 *(alpha)*

> 설계: [ops/search.md](ops/search.md)

상장사는 수천 건의 공시를 제출한다 — 유상증자, 소송, 대표이사 변경, 합병. DartLab은 제목이 아니라 **내용의 의미로 검색**한다.

```python
import dartlab

dartlab.search("유상증자 결정")                     # 유상증자 공시 찾기
dartlab.search("대표이사 변경", corp="005930")       # 종목 필터
dartlab.search("전환사채 발행", start="20240101")    # 기간 필터
dartlab.search("회사가 돈을 빌렸다")                 # 자연어도 동작
```

**모델 없음, GPU 없음, cold start 없음.** 400만 문서 실측:

| | Ngram+Synonym (DartLab) | 임베딩 (ko-sroberta) |
|---|:---:|:---:|
| **정밀도(Precision@5)** | **95%** | 83% |
| **검색 속도** | **138ms** | 58ms |
| **Cold start** | **0ms** | 12,700ms |
| **의존성** | **없음 (numpy만)** | PyTorch 2GB + GPU |

**왜 임베딩 없이 되는가:** DART 공시는 정형화된 어휘를 사용한다 — "유상증자결정", "대표이사변경", "정기주주총회결과"가 `report_nm`과 `section_title`에 그대로 나타난다. stem ID 역인덱스(bigram/trigram → 정수 ID → CSR posting list)가 이 구조를 직접 포착한다. 동의어 확장이 자연어("돈을 빌렸다")를 공시 용어("사채", "차입")로 변환한다. 결과: 신경망 임베딩보다 높은 정밀도, 1/100 비용.

사전 빌드된 인덱스를 HuggingFace에서 다운로드하면 즉시 검색:

```python
from dartlab.core.search import pullIndex
pullIndex()                            # ~320MB 다운로드, 이후 즉시 검색
```

> **상태:** alpha — 데이터 범위 확장 중. 2,500+ 종목 사업보고서 + 일자별 공시 포함.

### AI -- 적극적 분석가

> 설계: [ops/ai.md](ops/ai.md)

DartLab의 AI는 수동적 해설자가 아니다. dartlab을 도구로 삼아 함수를 호출하고, 코드를 작성하고, 분석을 실행하고, 질문에 맞는 워크플로우를 스스로 설계하는 **적극적 분석가**다.

질문하면 AI가 dartlab의 전체 API를 사용해 Python 코드를 작성하고 실행한다. 사용자는 AI가 실행하는 모든 코드와 결과를 볼 수 있다. 단순히 답을 얻는 게 아니라, 기업을 분석하는 방법 자체를 배울 수 있다. AI는 `analysis()`, `scan()`, `gather()`, `review()`, `show()`, `notes` 등 어떤 함수든 조합해서 질문이 요구하는 흐름을 스스로 만든다.

**AI 분석 능력:**
- 질문에 맞는 축을 정확히 선택 (60+ 질문 검증, 1회 성공률 95%+)
- 재무 데이터 + 실시간 뉴스 교차 검증 (newsSearch 자발 사용)
- K-IFRS 주석 상세 활용 (재고자산/차입금/유형자산 항목별 분해)
- 실행 결과를 마크다운 테이블로 깔끔하게 표시
- analysis 캐시 공유로 빠른 응답 (가치평가 97% 속도 개선)

```python
import dartlab

answer = dartlab.ask("삼성전자 재무건전성 분석해줘")

# provider + model 지정
answer = dartlab.ask("삼성전자 분석", provider="openai", model="gpt-4o")

# 에이전트 모드 -- LLM이 도구를 선택하여 심화 분석
answer = dartlab.chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")
```

### Provider

**무료 API 키 provider** -- 가입하고 키만 넣으면 바로 분석:

| Provider | 무료 한도 | 모델 |
|----------|-----------|------|
| `gemini` | Gemini 2.5 Pro/Flash 무료 | Gemini 2.5 |
| `groq` | 6K-30K TPM 무료 | LLaMA 3.3 70B |
| `cerebras` | 1M tokens/day 영구 무료 | LLaMA 3.3 70B |
| `mistral` | 1B tokens/month 무료 | Mistral Small |

**기타 provider:**

| Provider | 인증 | 비용 | Tool Calling |
|----------|------|------|:---:|
| `oauth-codex` | ChatGPT 구독 (Plus/Team/Enterprise) | 구독에 포함 | Yes |
| `openai` | API 키 (`OPENAI_API_KEY`) | 토큰당 과금 | Yes |
| `ollama` | 로컬 설치, 계정 불필요 | 무료 | 모델에 따라 다름 |
| `codex` | Codex CLI 로컬 설치 | 무료 (Codex 세션 사용) | Yes |
| `custom` | OpenAI 호환 엔드포인트 | 다양 | 다양 |

**자동 전환:** 여러 무료 API 키를 등록하면 하나가 한도를 초과할 때 자동으로 다음 provider로 전환한다. `provider="free"`로 fallback 체인 활성화.

**Claude provider가 없는 이유:** Anthropic은 OAuth 기반 접근을 제공하지 않는다. OAuth 없이는 사용자가 기존 구독으로 인증할 방법이 없다. Anthropic이 향후 OAuth를 지원하면 Claude provider를 추가할 예정이다. 현재 Claude는 **MCP**로 사용 가능.

**`oauth-codex`**가 권장 provider다 -- ChatGPT 구독이 있으면 API 키 없이 바로 작동한다.

### 프로젝트 설정 (`.dartlab.yml`)

```yaml
company: 005930         # 기본 종목
provider: openai        # 기본 LLM provider
model: gpt-4o           # 기본 모델
verbose: false
```

### 5계층 관계

```
gather()     외부 시장 데이터 (4축)     -- 주가, 수급, 거시, 뉴스
scan()       시장 전체 횡단 (13축)     -- 종목 간 비교/스크리닝
analysis()   단일 종목 심층 (14축)     -- 재무제표 완전 분석
c.review()   analysis -> 구조화 보고서  -- 블록-템플릿 파이프라인
c.reviewer() review + AI 해석          -- 섹션별 종합의견
```

### 아키텍처 -- 책임 기반 레이어

```
L0  core/        프로토콜, 재무 유틸, docs 유틸, 레지스트리
L1  providers/   국가별 데이터 (DART, EDGAR, EDINET)
    gather/      외부 시장 데이터 (Naver, Yahoo, FRED)
    scan/        시장 횡단분석 (13축)
L2  analysis/    재무 분석 + 전망 + 밸류에이션
    review/      블록-템플릿 보고서 조립
L3  ai/          적극적 분석가 — 전체 API 접근 가능한 LLM (5개 provider)
```

import 방향은 CI에서 강제한다 -- 역방향 의존 불허.

### 확장성 -- Core 수정 0줄

새 국가를 추가할 때 core 코드를 수정할 필요가 없다:

1. `providers/` 아래에 provider 패키지 생성
2. `canHandle(code) -> bool`과 `priority() -> int` 구현
3. `pyproject.toml`의 `entry_points`에 등록

```python
dartlab.Company("005930")  # -> DART provider (priority 10)
dartlab.Company("AAPL")    # -> EDGAR provider (priority 20)
```

facade가 priority 순으로 provider를 순회하여 첫 번째 매칭을 사용한다.

## EDGAR (미국)

동일한 `Company` 인터페이스, 동일한 계정 표준화 파이프라인, 다른 데이터 소스. EDGAR 데이터는 SEC API에서 자동 수집된다 -- 사전 다운로드 불필요:

```python
us = dartlab.Company("AAPL")

us.sections                         # 10-K/10-Q sections (heading/body 분리)
us.show("business")                 # 사업 설명
us.show("10-K::item1ARiskFactors")  # 리스크 요인
us.BS                               # SEC XBRL 재무상태표
us.ratios                           # 동일한 비율
us.diff("10-K::item7Mdna")          # MD&A 텍스트 변화
```

인터페이스가 동일하다 -- 같은 메서드, 같은 구조:

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
| `docs`        | v              | v              |
| `finance`     | v              | v              |
| `report`      | v (28개 API 타입) | x (해당 없음) |
| `profile`     | v              | v              |

DART는 정형 공시 API가 있는 `report` 네임스페이스가 있다 (배당, 지배구조, 임원 보상 등). SEC는 공시 구조가 다르므로 EDGAR에는 해당 없음.

**EDGAR topic 네이밍**: `{formType}::{itemId}` 형식. 단축 별칭도 사용 가능:

```python
us.show("10-K::item1Business")     # 전체 형식
us.show("business")                # 단축 별칭
us.show("risk")                    # -> 10-K::item1ARiskFactors
us.show("mdna")                    # -> 10-K::item7Mdna
```

## MCP -- AI 어시스턴트 연동

DartLab은 [MCP](https://modelcontextprotocol.io/) 서버를 내장하고 있다. Claude Desktop, Claude Code, Cursor 등 MCP 호환 클라이언트에서 사용할 수 있다.

### 빠른 설정 -- 복사 + 붙여넣기

**Claude Code:**

```bash
pip install "dartlab[mcp]" && claude mcp add dartlab -- uv run dartlab mcp
```

**OpenAI Codex CLI:**

```bash
pip install "dartlab[mcp]" && codex mcp add dartlab -- uv run dartlab mcp
```

한 줄이면 설치 + 등록 끝.

**Claude Desktop** -- `claude_desktop_config.json`에 추가:

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

**Cursor** -- `.cursor/mcp.json`에 위와 동일한 형식으로 추가.

설정 파일 위치를 모르겠다면 자동 생성:

```bash
dartlab mcp --config claude-desktop
dartlab mcp --config claude-code
dartlab mcp --config cursor
```

### 사용 가능한 기능

연결하면 AI 어시스턴트가 다음을 수행할 수 있다:

- **검색** -- 이름이나 코드로 기업 찾기 (`searchCompany`)
- **프로필** -- 기업 개요, 지배구조, 업종 (`companyProfile`, `companyGovernance`)
- **재무** -- BS, IS, CF, 재무비율 (`companyFinancials`, `companyRatios`)
- **분석** -- 인사이트, 밸류에이션, 전망 (`companyInsights`, `companyValuation`, `companyForecast`)
- **공시** -- 임의 topic 조회, 기간간 비교 (`companyShow`, `companyTopics`, `companyDiff`)
- **리뷰** -- 전체 분석 보고서 (`companyReview`, `companyAudit`)
- **시장** -- 섹터 스크리닝, 피어 비교 (`marketScan`)

## OpenAPI -- 원본 공공 API

원본 공시 API를 직접 다루고 싶을 때 source-native wrapper를 쓴다.

### OpenDart (한국)

> **참고:** `Company`는 API 키가 **필요 없다** -- 사전 구축 데이터셋으로 동작한다.
> `OpenDart`는 DART 원본 API를 직접 사용하므로 [opendart.fss.or.kr](https://opendart.fss.or.kr) 에서 API 키가 필요하다 (무료).

```python
from dartlab import OpenDart

d = OpenDart()
d.search("카카오", listed=True)
d.filings("삼성전자", "2024")
d.finstate("삼성전자", 2024)
d.report("삼성전자", "배당", 2024)
```

### OpenEdgar (미국)

> **API 키 불필요.** SEC EDGAR는 공공 API다 -- 등록 없이 사용 가능.

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
| EDGAR | 주문형 | -- | SEC API (자동 수집) |

### 3단계 데이터 파이프라인

```
dartlab.Company("005930")
  |
  +- 1. 로컬 캐시 ------ 이미 있으면 즉시 반환 (instant)
  |
  +- 2. HuggingFace ---- 자동 다운로드 (수 초, 키 불필요)
  |
  +- 3. DART API -------- API 키로 직접 수집 (키 필요)
```

HuggingFace에 없는 기업은 DART에서 직접 수집한다 -- API 키가 필요하다:

```bash
dartlab setup dart-key
```

### Freshness -- 자동 업데이트 감지

3-Layer freshness 시스템으로 로컬 데이터를 최신 상태로 유지한다:

| Layer | 방식 | 비용 |
|-------|------|------|
| L1 | HTTP HEAD -> HuggingFace ETag 비교 | ~0.5초, 수백 바이트 |
| L2 | 로컬 파일 나이 (90일 TTL 폴백) | 즉시 (로컬) |
| L3 | DART API -> `rcept_no` diff (API 키 필요) | API 1회, ~1초 |

`Company`를 열면 새 공시가 있는지 자동으로 확인한다:

```python
c = dartlab.Company("005930")
# [dartlab] 005930 -- 새 공시 발견 (사업보고서 (2024.12))

c.update()  # 누락된 공시만 증분 수집
```

## 바로 시작하기

### 라이브 데모

**[라이브 데모 열기](https://huggingface.co/spaces/eddmpython/dartlab)** -- 설치 없이 브라우저에서 바로

### 노트북

| 기능 | 설명 | Colab | Molab |
|------|------|-------|-------|
| **Company** | `Company("005930")` -- index, show, select, trace, diff + 재무 바로가기 | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/01_company.py) |
| **Scan** | `scan()` -- 전종목 횡단 스캔, 2,700+ 기업 | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/02_scan.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/02_scan.py) |
| **Review** | `c.review()` -- 구조화 보고서 + `c.reviewer()` AI 해석 | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/03_review.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/03_review.py) |
| **Gather** | `gather()` -- 주가, 수급, 거시, 뉴스를 한 번에 | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/04_gather.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/04_gather.py) |
| **Analysis** | `c.analysis()` -- 14축 분석, 인사이트, 전망, 밸류에이션 | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/05_analysis.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/05_analysis.py) |
| **Ask (AI)** | `ask("...")` -- 자연어로 LLM 분석 | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/06_ask.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/06_ask.py) |

<details>
<summary>로컬에서 Marimo로 실행</summary>

```bash
uv add dartlab marimo
marimo edit notebooks/marimo/01_company.py
marimo edit notebooks/marimo/02_scan.py
marimo edit notebooks/marimo/03_review.py
marimo edit notebooks/marimo/04_gather.py
marimo edit notebooks/marimo/05_analysis.py
marimo edit notebooks/marimo/06_ask.py
```

</details>

## 문서

- 문서: https://eddmpython.github.io/dartlab/
- Sections 가이드: https://eddmpython.github.io/dartlab/docs/getting-started/sections
- 빠른 시작: https://eddmpython.github.io/dartlab/docs/getting-started/quickstart
- API 개요: https://eddmpython.github.io/dartlab/docs/api/overview
- 초보자 가이드: https://eddmpython.github.io/dartlab/blog/dartlab-easy-start/

### 블로그

[DartLab 블로그](https://eddmpython.github.io/dartlab/blog/)는 실전 공시 분석 주제를 다룬다 -- 재무제표 읽는 법, 공시 패턴 해석, 리스크 신호 포착 등. 120편 이상, 3개 카테고리:

- **공시 제도** -- DART/EDGAR 공시의 구조와 작동 원리
- **보고서 읽기** -- 감사보고서, 잠정실적, 재작성 등 실전 가이드
- **재무 해석** -- 재무제표, 비율, 공시 신호 해석

## 안정성

| Tier | 범위 |
|------|------|
| **Stable** | DART Company (sections, show, trace, diff, BS/IS/CF, CIS, index, filings, profile), EDGAR Company core, valuation, forecast, simulation |
| **Beta** | EDGAR 파워유저 (SCE, notes, freq, coverage), insights, distress, ratios, timeseries, network, governance, workforce, capital, debt, chart/table/text 도구, ask/chat, OpenDart, OpenEdgar, Server API, MCP |
| **Experimental** | AI 도구 호출, export |

자세한 기준은 [docs/stability.md](docs/stability.md)를 본다.

## 기여

**기여자를 대환영합니다.** 버그 리포트, 새 분석 축, 매핑 수정, 문서 개선 -- 어떤 기여든 dartlab을 더 좋게 만듭니다.

규칙 하나: **실험 먼저, 엔진은 그 다음.** 아이디어는 `experiments/`에서 검증한 뒤 엔진에 반영한다. 이렇게 하면 코어는 안정적으로 유지하면서 대담한 시도를 할 수 있다.

- **실험 폴더**: `experiments/XXX_camelCaseName/` -- 각 파일은 독립 실행 가능해야 하고, docstring에 실제 결과가 포함되어야 한다
- **데이터 기여** (`accountMappings.json`, `sectionMappings.json` 등): 실험 증거가 있을 때 수용
- 한국어/영어 이슈와 PR 모두 환영
- 어디서 시작할지 모르겠다면 이슈를 열어주세요 -- 함께 찾아드립니다

## 라이선스

MIT
