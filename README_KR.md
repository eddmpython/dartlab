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

## 문제

상장 기업은 매 분기 수백 페이지를 공시한다. 매출 추세, 리스크 경고, 경영 전략, 경쟁 포지션 — 기업이 직접 쓴, 기업에 대한 완전한 진실.

**아무도 읽지 않는다.**

읽고 싶지 않아서가 아니다. 같은 정보가 회사마다 다른 이름으로, 연도마다 다른 구조로, 규제기관용 포맷에 흩어져 있기 때문이다. 같은 "매출액"이 `ifrs-full_Revenue`, `dart_Revenue`, `SalesRevenue`로 표기된다. 같은 "사업의 내용"이 공시마다 다른 제목으로 올라온다.

DartLab은 하나의 전제 위에 서 있다: **모든 기간은 비교 가능해야 하고, 모든 회사는 비교 가능해야 한다.** 공시 섹션을 토픽-기간 그리드로 정규화하고(~95% 매핑율), XBRL 계정을 표준 이름으로 통일한다(~97% 매핑율) — 양식이 아니라 기업을 비교한다.

## 빠른 시작

```bash
uv add dartlab
```

```python
import dartlab

c = dartlab.Company("005930")       # 삼성전자

c.sections                          # 모든 topic, 모든 기간, 나란히
# shape: (41, 12) — 41개 토픽 × 12개 기간
#                     2025Q4  2024Q4  2024Q3  2023Q4  ...
# companyOverview       v       v       v       v
# businessOverview      v       v       v       v
# riskManagement        v       v       v       v

c.show("businessOverview")          # 이 회사가 실제로 뭘 하는지
c.diff("businessOverview")          # 작년 대비 뭐가 바뀌었는지
c.BS                                # 표준화된 재무상태표
c.ratios                            # 재무비율, 이미 계산됨

# 같은 인터페이스, 다른 나라
us = dartlab.Company("AAPL")
us.show("business")
us.ratios

# 자연어로 질문
dartlab.ask("삼성전자 재무건전성 분석해줘")
```

API 키 불필요. [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data)에서 자동 다운로드, 로컬 캐시로 즉시 로드.

## DartLab은 무엇인가

두 가지 엔진으로 원본 공시를 하나의 비교 가능한 맵으로 바꾼다:

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
| L4 | [UI](ops/ui.md) | Svelte SPA + VSCode 확장 | `dartlab share` |

### Company

> 설계: [ops/company.md](ops/company.md)

세 가지 데이터 소스 — docs(전문 공시), finance(XBRL 재무제표), report(DART API 정형 데이터) — 를 하나의 객체로 통합. [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data)에서 자동 다운로드, 설정 불필요.

```python
c = dartlab.Company("005930")

c.index                         # 뭐가 있는지 -- topic 목록 + 가용 기간
c.show("BS")                    # 데이터를 보려면 -- topic별 DataFrame
c.select("IS", ["매출액"])       # 데이터를 뽑으려면 -- finance든 docs든 같은 패턴
c.trace("BS")                   # 어디서 왔는지 -- source provenance
c.diff()                        # 뭐가 바뀌었는지 -- 기간 간 텍스트 변화
```

### Scan — 전 종목 횡단 비교

> 설계: [ops/scan.md](ops/scan.md)

2,700+ 종목 대상 13축 횡단 분석. 거버넌스, 인력, 주주환원, 부채, 현금흐름, 감사, 내부자, 이익의질, 유동성, 다이제스트, 네트워크, 계정, 비율.

```python
dartlab.scan("governance")            # 전종목 지배구조
dartlab.scan("ratio", "roe")          # 전종목 ROE
dartlab.scan("cashflow")              # OCF/ICF/FCF + 8유형 패턴 분류
```

### Gather — 외부 시장 데이터

> 설계: [ops/gather.md](ops/gather.md)

주가, 수급, 거시지표, 뉴스 — Polars DataFrame으로.

```python
dartlab.gather("price", "005930")             # KR OHLCV
dartlab.gather("price", "AAPL", market="US")  # US 주가
dartlab.gather("macro", "FEDFUNDS")           # 자동 US 감지
dartlab.gather("news", "삼성전자")             # Google News RSS
```

### Analysis — 14축 재무분석

> 설계: [ops/analysis.md](ops/analysis.md)

수익구조, 수익성, 성장성, 안정성, 현금흐름, 자본배분 — 14축이 원본 재무제표를 인과 서사로 가공한다.

```python
c.analysis("수익성")                   # 수익성 분석
c.analysis("현금흐름")                 # 현금흐름 분석
```

### Review — 분석을 보고서로

> 설계: [ops/review.md](ops/review.md)

analysis를 구조화 보고서로 조립. 4개 출력 형식: rich(터미널), html, markdown, json.

```python
c.review()              # 전체 보고서
c.reviewer()            # 보고서 + AI 종합의견
```

**샘플 보고서:** [삼성전자](docs/samples/005930.md) · [SK하이닉스](docs/samples/000660.md) · [기아](docs/samples/000270.md) · [한화오션](docs/samples/042660.md) · [SK텔레콤](docs/samples/017670.md) · [LG화학](docs/samples/051910.md) · [엔씨소프트](docs/samples/036570.md) · [아모레퍼시픽](docs/samples/090430.md)

### Search — 공시를 의미로 검색 *(alpha)*

> 설계: [ops/search.md](ops/search.md)

모델 없음, GPU 없음, cold start 없음. 400만 문서 95% 정밀도 — 임베딩보다 정확, 1/100 비용.

```python
dartlab.search("유상증자 결정")                     # 유상증자 공시 찾기
dartlab.search("대표이사 변경", corp="005930")       # 종목 필터
dartlab.search("회사가 돈을 빌렸다")                 # 자연어도 동작
```

### AI — 적극적 분석가

> 설계: [ops/ai.md](ops/ai.md)

AI가 dartlab의 전체 API로 Python 코드를 작성하고 실행한다. 모든 코드와 결과를 볼 수 있다. 60+ 질문 검증, 1회 성공률 95%+.

```python
dartlab.ask("삼성전자 재무건전성 분석해줘")
dartlab.ask("삼성전자 분석", provider="gemini")  # 무료 provider 사용 가능
```

Provider: `gemini`(무료), `groq`(무료), `oauth-codex`(ChatGPT 구독), `openai`, `ollama`(로컬) 등. rate limit 시 자동 전환.

### 아키텍처

```
L0  core/        프로토콜, 재무 유틸, docs 유틸, 레지스트리
L1  providers/   국가별 데이터 (DART, EDGAR, EDINET)
    gather/      외부 시장 데이터 (Naver, Yahoo, FRED)
    scan/        시장 횡단분석 (13축)
L2  analysis/    재무 분석 + 전망 + 밸류에이션
    review/      블록-템플릿 보고서 조립
L3  ai/          적극적 분석가 — 전체 API 접근 가능한 LLM
L4  ui/          Svelte SPA (웹) + VSCode 확장
```

import 방향은 CI 강제. 새 국가 추가 = provider 패키지 하나, core 수정 0줄.

## EDGAR (미국)

같은 인터페이스, 다른 데이터 소스. SEC API에서 자동 수집, 사전 다운로드 불필요.

```python
# Korea (DART)                          # US (EDGAR)
c = dartlab.Company("005930")           c = dartlab.Company("AAPL")
c.sections                              c.sections
c.show("businessOverview")              c.show("business")
c.BS                                    c.BS
c.ratios                                c.ratios
c.diff("businessOverview")              c.diff("10-K::item7Mdna")
```

## MCP — AI 어시스턴트 연동

[MCP](https://modelcontextprotocol.io/) 서버 내장. Claude Desktop, Claude Code, Cursor에서 사용 가능.

```bash
# Claude Code — 한 줄 설정
claude mcp add dartlab -- uv run dartlab mcp

# Codex CLI
codex mcp add dartlab -- uv run dartlab mcp
```

<details>
<summary>Claude Desktop / Cursor 설정</summary>

`claude_desktop_config.json` 또는 `.cursor/mcp.json`에 추가:

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

자동 생성: `dartlab mcp --config claude-desktop`

</details>

## OpenAPI — 원본 공공 API

```python
from dartlab import OpenDart, OpenEdgar

# 한국 (opendart.fss.or.kr 무료 API 키 필요)
d = OpenDart()
d.filings("삼성전자", "2024")
d.finstate("삼성전자", 2024)

# 미국 (API 키 불필요)
e = OpenEdgar()
e.filings("AAPL", forms=["10-K", "10-Q"])
```

## 데이터

모든 데이터는 [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data)에 사전 구축 — 자동 다운로드. EDGAR는 SEC API 직접 수집.

| 데이터셋 | 규모 | 용량 |
|----------|------|------|
| DART docs | 2,500+ 기업 | ~8 GB |
| DART finance | 2,700+ 기업 | ~600 MB |
| DART report | 2,700+ 기업 | ~320 MB |
| EDGAR | 주문형 | SEC API |

파이프라인: 로컬 캐시(즉시) → HuggingFace(자동 다운로드) → DART API(키 필요). 대부분 처음 두 단계로 충분.

## 바로 시작하기

**[라이브 데모](https://huggingface.co/spaces/eddmpython/dartlab)** — 설치 없이 브라우저에서 바로

**노트북:** [Company](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb) · [Scan](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/02_scan.ipynb) · [Review](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/03_review.ipynb) · [Gather](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/04_gather.ipynb) · [Analysis](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/05_analysis.ipynb) · [Ask (AI)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/06_ask.ipynb)

## 문서

[문서](https://eddmpython.github.io/dartlab/) · [빠른 시작](https://eddmpython.github.io/dartlab/docs/getting-started/quickstart) · [API 개요](https://eddmpython.github.io/dartlab/docs/api/overview) · [블로그 (120+ 글)](https://eddmpython.github.io/dartlab/blog/)

## 안정성

| Tier | 범위 |
|------|------|
| **Stable** | DART Company (sections, show, trace, diff, BS/IS/CF, CIS, index, filings, profile), EDGAR Company core, valuation, forecast, simulation |
| **Beta** | EDGAR 파워유저 (SCE, notes, freq, coverage), insights, distress, ratios, timeseries, network, governance, workforce, capital, debt, chart/table/text 도구, ask/chat, OpenDart, OpenEdgar, Server API, MCP |
| **Experimental** | AI 도구 호출, export |

자세한 기준은 [docs/stability.md](docs/stability.md)를 본다.

## 기여

**기여자를 대환영합니다.** 버그 리포트, 새 분석 축, 매핑 수정, 문서 개선 — 어떤 기여든 dartlab을 더 좋게 만듭니다.

규칙 하나: **실험 먼저, 엔진은 그 다음.** 아이디어는 `experiments/`에서 검증한 뒤 엔진에 반영한다.

- **실험 폴더**: `experiments/XXX_camelCaseName/` — 각 파일은 독립 실행 가능, docstring에 실제 결과 포함
- **데이터 기여** (`accountMappings.json`, `sectionMappings.json` 등): 실험 증거가 있을 때 수용
- 한국어/영어 이슈와 PR 모두 환영
- 어디서 시작할지 모르겠다면 이슈를 열어주세요

## 라이선스

MIT
