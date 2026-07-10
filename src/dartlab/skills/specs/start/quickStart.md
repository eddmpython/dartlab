---
id: start.quickStart
title: DartLab 8 단계 빠른 시작
kind: curated
scope: builtin
status: observed
category: start
purpose: 설치 직후 Company · topics/panel · diff · EDGAR · scan · ask 까지 핵심 기능을 한 번에 통과하는 walkthrough 절차다.
whenToUse:
  - DartLab 설치 직후 첫 분석
  - 핵심 기능 빠르게 훑기
  - 데모용 코드 흐름이 필요할 때
  - Company / Scan / Ask 셋의 관계를 파악할 때
inputs:
  - 설치된 dartlab 환경
  - 임의의 한국 종목코드 또는 미국 ticker
outputs:
  - 회사 객체와 topic 별 DataFrame
  - 시장 횡단 scan 결과
  - AI 분석 결과 (옵션)
toolRefs:
  - dartlab.Company
  - dartlab.scan
  - dartlab.ask
  - dartlab.search
sourceRefs:
  - dartlab://skills/start.quickStart
  - dartlab://skills/engines.company
requiredEvidence:
  - execution
  - executionRef
  - sourceRef
expectedOutputs:
  - 회사 단위 결과
  - 시장 단위 결과
  - 다음에 깊이 볼 skill 후보
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
    notes:
      - scan 과 ask 는 데이터·모델 의존성에 따라 제한될 수 있다.
procedure:
  - dartlab.Company(code) 로 회사 객체를 만든다.
  - c.panel 로 항목 x 기간 wide 격자를 통째로 본다.
  - c.panel(topic) 으로 개별 topic 을 연다 (IS · BS · CF · CIS · SCE · ratios).
  - c.trace(항목) 으로 그 값이 어느 공시에서 왔는지 되짚는다.
  - 미국 종목은 같은 API 로 동작한다 (Company("AAPL")).
  - dartlab.scan(group, axis) 로 시장 전체 횡단.
  - dartlab.search(name) 으로 회사 식별.
  - dartlab.ask(question) 으로 자연어 분석 (LLM provider 필요).
failureModes:
  - 종목코드 / ticker 혼동 (한국 6 자리 vs 미국 알파벳)
  - panel 의 topic 이름 오타 (companyOverview vs company-overview)
  - ask 호출 전 dartlab[llm] 미설치
forbidden:
  - 검증 없이 코드 결과를 결론으로 단정
  - panel 결과의 누락 (null) 을 0 으로 대체
examples:
  - 처음 dartlab 깔고 뭘 해봐야 하나
  - 8 분 안에 회사·시장·AI 까지 한 번 훑기
  - 미국 종목도 같은 코드로 분석
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-05-06"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

DartLab 은 세 가지를 한다 — **Company** (한 회사 깊게), **Scan** (시장 횡단), **Ask** (AI 분석).

## 0. 설치

```bash
uv add dartlab
```

## 1. Company — 아무 회사나 읽기

```python
import dartlab

c = dartlab.Company("005930")  # 삼성전자
```

데이터는 첫 호출 시 자동 다운로드. 별도 셋업 없음.

### 신선도

- **첫 사용**: HuggingFace 에서 자동 다운로드 (종목당 수 MB).
- **이후**: 24 시간마다 HF 갱신 자동 확인 (HTTP HEAD, 비용 거의 0).
- **오프라인**: `dartlab.loadData("005930", refresh="local_only")` — 네트워크 체크 생략.

## 2. 회사 전체 보기

```python
c.panel          # 항목 x 기간 wide 격자 그 자체 (pl.DataFrame)
c.panel.shape    # (항목 수, 기간 열 수)
```

## 3. 개별 topic 열기

정식 topic 은 `IS` · `BS` · `CF` · `CIS` · `SCE` · `ratios` 다. 주석 본문은 섹션명으로 검색한다.

```python
c.panel("재고")     # 섹션명·canonicalKey 행 검색 (주석 본문)
```

## 4. 재무제표

```python
c.panel("IS")       # 손익계산서
c.panel("BS")       # 재무상태표
c.panel("CF")       # 현금흐름표
c.panel("ratios")   # 47 개 재무비율
```

## 5. 값의 출처 되짚기

```python
c.trace("IS")   # 손익 데이터가 어느 출처(panel/finance/report)에서 왔나
```

## 6. 미국 종목 — 같은 API

```python
apple = dartlab.Company("AAPL")
apple.panel("IS")
apple.panel("10-K::item1ARiskFactors")
```

## 7. 시장 횡단 (Scan)

```python
dartlab.search("삼성전자")              # 회사 검색
dartlab.scan("ratio", "roe")           # 전 상장 ROE
dartlab.scan("account", "매출액")       # 전 상장 매출
```

## 8. AI 분석 (Ask)

```bash
uv add "dartlab[llm]"
```

```python
dartlab.ask("삼성전자 재무 건강도 분석")
```

provider (OpenAI · Ollama · ChatGPT OAuth) 가 필요하다. `dartlab setup` 으로 옵션 확인.

## 실습 노트북

같은 코드를 Colab · Molab · 로컬 marimo 세 경로로 돌려볼 수 있다 → [runtime.notebooks](/skills/runtime.notebooks).

## 다음 단계

- [start.dartlabSkillOs](/skills/start.dartlabSkillOs) — Skill OS 카탈로그 첫 진입.
- [engines.company](/skills/engines.company) — Company 엔진 전체 메서드.
- [engines.scan](/skills/engines.scan) — 시장 횡단 19 축.
- [engines.story](/skills/engines.story) — 구조화 보고서 생성.
