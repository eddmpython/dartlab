---
id: runtime.notebooks
title: Colab · Molab · 로컬 marimo 노트북
kind: curated
scope: builtin
status: observed
category: runtime
purpose: 같은 dartlab 코드를 Colab (Google) · Molab (marimo cloud) · 로컬 marimo 세 경로로 실행하는 노트북 카탈로그와 작성·운영 규칙이다.
whenToUse:
  - dartlab 을 설치 없이 브라우저에서 시도
  - Molab 무료 클라우드에서 실행
  - 로컬 marimo 로 영구 노트북 작성
  - colab/marimo 1:1 대응 코드 위치 찾기
  - 노트북 새로 만들거나 기존 노트북 수정
inputs:
  - 노트북 환경 선택 (Colab · Molab · 로컬)
  - 분석 대상 (Company · Scan · Story · Gather · Analysis · Ask)
outputs:
  - 실행 가능한 노트북 링크
  - 로컬 실행 명령
  - 노트북 작성 규칙
capabilityRefs: []
toolRefs:
  - colab
  - marimo
knowledgeRefs:
  - start.dartlabSkillOs
  - start.installUv
  - start.quickStart
sourceRefs:
  - dartlab://skills/runtime.notebooks
  - https://github.com/eddmpython/dartlab/tree/master/notebooks
procedure:
  - 환경을 고른다 (브라우저 즉시 → Colab/Molab, 로컬 영구 → marimo).
  - 노트북 카탈로그에서 분석 대상에 맞는 항목을 연다.
  - 첫 셀에서 의존성 추가 (`!pip install dartlab` 또는 `uv add dartlab`).
  - 코드 실행 — 데이터는 자동 다운로드.
  - 새 노트북 작성 시 작성 규칙 (Colab 마크다운 / marimo 주석) 을 따른다.
requiredEvidence:
  - execution
  - executionRef
  - sourceRef
expectedOutputs:
  - 노트북 진입 링크
  - 실행 환경별 의존성 설치 결과
  - 작성 규칙 충족 여부
runtimeCompatibility:
  server:
    status: limited
  localPython:
    status: supported
    notes:
      - "uv run --with marimo marimo edit notebooks/marimo/{name}.py 로 실행."
  mcp:
    status: limited
  webAi:
    status: supported
    notes:
      - Colab / Molab 둘 다 브라우저에서 즉시.
  pyodide:
    status: limited
    notes:
      - marimo wasm 빌드는 별도 — 본 카탈로그 외 항목.
failureModes:
  - Colab 노트북을 로컬 jupyter 와 혼동
  - marimo 의 reactive 모델을 jupyter 의 셀 순서 모델로 오해
  - 노트북에서 큰 데이터 셋을 메모리 폭주시킴
  - 셀 순서에 의존하는 비결정 코드 작성 (marimo reactive 모델 위반)
  - colab (.ipynb) 과 marimo (.py) 의 1:1 대응을 깨고 한쪽만 갱신
forbidden:
  - 셀 순서에 의존하는 비결정 코드 작성
  - colab/marimo 한쪽만 갱신한 채 변경 완료 처리
examples:
  - dartlab Colab 으로 시도
  - 로컬 marimo 에서 Company 분석
  - Molab 으로 무료 실행
  - 새 노트북 작성 규칙 확인
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-05-06"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 노트북 카탈로그

Colab 은 브라우저에서 바로 실행 (Google 계정). Molab 은 marimo 클라우드 (무료).

노트북 파일명은 `notebooks/colab/{name}.ipynb` 와 `notebooks/marimo/{name}.py` 가 1:1 로 같다.
축 개수는 각 엔진 카탈로그(인자 없이 호출) 실측값이다.

| 노트북 | 기능 | 설명 |
|---|---|---|
| `01_company` | **Company** | `Company("005930")` 로 회사를 잡고 `c.panel` · `c.select` · `c.trace` |
| `02_gather` | **Gather** | `gather()` 16 축. 주가 · 수급 · 거시 · 뉴스 (네트워크 필요, 로컬 전용) |
| `03_scan` | **Scan** | `scan()` 27 축 전 종목 횡단 스캔 |
| `04_quant` | **Quant** | `c.quant()` 48 축. 기술적 지표 · 신호 · 백테스트 |
| `05_analysis` | **Analysis** | `c.analysis()` 22 축. 수익성 · 성장성 · 안정성 · 밸류에이션 |
| `06_macro` | **Macro** | `macro()` 15 축. 사이클 · 금리 · 시나리오 |
| `07_credit` | **Credit** | `c.credit()` dCR 등급 + 7 축 위험 |
| `08_story` | **Story** | `c.story()` 구조화 보고서 |
| `09_ai` | **Ask (AI)** | `ask("...")` 자연어 LLM 분석 |
| `10_search` | **Search** | `search()` 공시 제목 · 본문 검색 |
| `11_listing` | **Listing** | `listing()` 상장사 · 공시 · 토픽 목록 |

- Colab: `https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/{name}.ipynb`
- Molab: `https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/{name}.py`

## 브라우저 노트북 (설치 0, 단계별 커리큘럼)

`landing` 의 `/notebooks` 는 pyodide 로 브라우저 안에서 도는 별도 표면이다. Colab/Molab 과 달리
계정도 설치도 필요 없고, 코드와 결과가 바깥으로 나가지 않는다.

- 레슨 SSOT: `landing/src/lib/notebook/lessons/content/{track}/{NN}-{slug}.yaml` (한 편 = 한 파일).
  같은 파일을 브라우저 레지스트리와 파이썬 게이트가 함께 읽는다. 파생 산출물을 굽지 않는다.
- 트랙: 시작 · 회사 재무 · 판독 엔진 · 시장 횡단. 트랙 순서가 곧 학습 경로다.
- 레슨을 열면 `lesson:<레슨 id>` 안정 키로 IndexedDB 에 저장되어 하던 곳에서 이어진다.
- 새 레슨 추가 절차와 스키마: `landing/src/lib/notebook/lessons/README.md`.
- 기계 가드: `tests/audit/lessonSchema.py` (스키마 · prereq 사이클 · 브라우저 경계 정합 · 규모),
  `tests/audit/notebookContract.py` (공개 호출 계약). CI fast `notebooks` 게이트가 둘 다 돌린다.

브라우저에서 되는 것과 안 되는 것은 `runtime.pyodide` 가 정본이다.

## 로컬 marimo 실행

```bash
uv run --with marimo marimo edit notebooks/marimo/01_company.py
```

같은 코드 (`notebooks/marimo/{name}.py`) 가 Molab 클라우드에서도 동작한다.

Colab (`.ipynb`) 과 marimo (`.py`) 는 **1:1 대응** — 같은 분석을 두 노트북 형식으로 유지한다. 한쪽만 갱신 금지.

## 노트북 작성 규칙

### Colab — 마크다운 허용

- 학습·공유용 독자가 맥락을 빠르게 잡게 마크다운 셀로 섹션 설명.
- **3~4 코드 셀마다 1 마크다운**. 너무 잦으면 흐름 끊고, 너무 드물면 맥락 사라진다.
- 노트북 최상단 1 장: 제목 + 한 줄 요약 + "이 노트북에서 다루는 것" 2~3 줄.
- 주요 섹션 전환점에만 1 장씩.

### marimo — 코드 + 짧은 주석

- 실습·실행용. 설명은 코드 옆 짧은 주석으로.
- 첫 줄 한글 주석으로 셀 의도 표시.
- 마크다운 셀 자제 — reactive 모델은 코드 흐름이 본체다.

### 공통 규칙

- 같은 분석은 같은 코드·같은 순서로 두 노트북에 동기화.
- 셀 순서에 의존하는 비결정 코드 금지 (marimo 가 reactive 라 의도와 다른 결과 낳는다).
- 큰 데이터 셋 (Company 3 개 이상 동시 로드) 금지 — OOM 위험.

## 다음 단계

- [start.installUv](/skills/start.installUv) — 로컬 dartlab 설치.
- [start.quickStart](/skills/start.quickStart) — 8 단계 walkthrough.
- [engines.company](/skills/engines.company) — Company 엔진 메서드 카탈로그.
