---
id: engines.data
title: Data (수집·프리빌드 파이프라인)
kind: curated
scope: builtin
status: observed
category: engines
purpose: Data 는 dartlab 의 데이터 파이프라인 운영 SSOT — DART 12h 수집, EDGAR 일배치, scan 프리빌드, HF 직렬 업로드를 하나의 워크플로우 그래프로 묶는다. 사용자 호출 capability 가 아니라 *운영자 절차* + python 진입점 (gather/Company/scan) 안내. 트리거 — '데이터 수집', 'data 명세', '프리빌드', 'HF 업로드'.
whenToUse:
  - data
  - 데이터 수집
  - 데이터 다운로드
  - 데이터 프리빌드
  - HF 업로드
  - dataSync
  - dataPrebuild
  - edgarSync
  - 12h 주기
  - workflow_run
inputs:
  - 종목코드 또는 universe
  - 수집 카테고리 (finance · panel · report)
  - 빌드 주기 (12h · 일 · 수동)
outputs:
  - parquet snapshot (HF dataset)
  - scan 프리빌드 결과
  - latestAsOf metadata
capabilityRefs:
  - Company
  - gather
  - scan
  - collect
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.company
  - engines.gather
  - engines.scan
sourceRefs:
  - dartlab://skills/engines.data
requiredEvidence:
  - provider
  - dataset
  - latestAsOf
  - source
  - executionRef
  - sourceRef
expectedOutputs:
  - 종목/유니버스 데이터 freshness
  - 수집 결과 종목별 카테고리별 건수
  - 빌드 산출물 위치
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
failureModes:
  - 분석 답변에 latestAsOf 없이 *최신 데이터* 라고 단정
  - HF 업로드 동시 실행 (concurrency.group 미설정 → sliding-window 429)
  - workflow_run 체인 끊김 (dataSync 완료 후 dataPrebuild 트리거 미동작)
  - Company.panel 의 topic 을 추측 (정식 topic 은 BS/IS/CF/CIS/SCE/ratios. 주석은 섹션명 검색)
forbidden:
  - latestAsOf · provider · source 없이 데이터 신선도를 *최신* 으로 단정 금지.
  - Company.panel topic 을 추측 금지 (정식 topic 은 BS/IS/CF/CIS/SCE/ratios. 주석은 c.panel("재고") 처럼 섹션명으로).
  - HF 업로드 직렬화 우회 금지 (`concurrency.group: hf-dataset-push` 강제).
examples:
  - 005930 finance freshness 확인
  - 전종목 prebuild freshness 확인
  - 신규 종목 KindList bootstrap
  - dataSync workflow_dispatch mode=full
  - scan 프리빌드 트리거
procedure:
  - python 사용자 진입점은 `dartlab.checkFreshness("005930")` (개별) · `dartlab.collect(...)` · `dartlab.Company(code).panel(topic)`.
  - 단일 종목 데이터는 `dartlab.Company(code).panel(topic)`. topic 은 BS/IS/CF/CIS/SCE/ratios.
  - 전종목 횡단은 `dartlab.scan(axis)` — prebuilt parquet 또는 provider scan 함수 자동 라우팅.
  - 운영자 워크플로우는 `.github/workflows/dataSync.yml` (12h) · `dataPrebuild.yml` (workflow_run) · `edgarSync.yml` (일).
  - 수동 backup 은 `dataSync.yml workflow_dispatch mode=full` — 88 분기 차집합.
linkedSkills:
  - engines.company
  - engines.gather
  - engines.scan
  - engines.data.foundation
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-05-08'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 엔진 역할

`data` 는 dartlab 의 *데이터 파이프라인 SSOT*. python 호출 capability 가 아니라 — 운영자 절차 + 사용자가 데이터에 접근하는 진입점 (`Company`, `gather`, `scan`, `checkFreshness`, `collect`) 의 통합 안내.

데이터 흐름:

```
DART API ──12h─→ dataSync.yml ──workflow_run─→ dataPrebuild.yml
                      │                                │
                      ↓                                ↓
                HF dataset                    scan 프리빌드 parquet
                (finance·panel·report)           (governance·workforce·etc)
                      │                                │
                      └────────────┬───────────────────┘
                                   ↓
                           Company / gather / scan
                                (사용자 진입점)

EDGAR ──일배치─→ edgarSync.yml (end-to-end, HF 업로드 포함)

KindList 신규 종목 ──bootstrap─→ 별도 워크플로우
```

## 공개 호출 방식

```python
import dartlab

# 1. 데이터 freshness 확인 (DART API 직접 조회)
c = dartlab.Company("005930")   # 신선도는 panel 결과의 dataAsOf / latestPeriod 로 본다
# → FreshnessResult: isFresh · missingCount · lastLocalDate · lastRemoteDate

# 2. 단일/다종목 직접 수집 (DART_API_KEY 필요)
dartlab.collect("005930", "000660", categories=["finance"])
# → dict: {종목: {카테고리: 수집 건수}}

# 3. 단일 종목 데이터 조회 (topic 은 BS/IS/CF/CIS/SCE/ratios)
c = dartlab.Company("005930")
print(c.panel.shape)             # 항목 x 기간 격자 크기
bs = c.panel("BS", freq="Q")      # 분기 재무상태표
ratios = c.panel("ratios")

# 4. 횡단 데이터 (전종목 비율·계정)
roe_all = dartlab.scan("ratio", "roe")
revenue_all = dartlab.scan("account", "매출액")
```

```bash
# 운영자 절차 — 워크플로우 수동 트리거
gh workflow run dataSync.yml -f mode=full          # 88 분기 차집합 backup
gh workflow run dataPrebuild.yml                   # scan 프리빌드 강제 재빌드
gh workflow run edgarSync.yml                       # EDGAR 전체 동기
```

## 강행 호출 룰 (agent 답변 품질 회귀 차단)

data 는 *운영자 절차* SKILL — ask LLM 의 EngineCall 대상이 아님. 사용자 질문 ("데이터 freshness", "프리빌드 언제 됐어") 시 다음 4 룰 강행:

1. **EngineCall(apiRef="data") 같은 호출 금지** — 데이터 freshness 는 `checkFreshness(stockCode)` 또는 `Company.panel` 결과 dict 의 `dataAsOf`/`latestPeriod` 필드 인용.
2. **`dataAsOf` / `latestPeriod` / `freshness` 값을 답변 첫 줄 명시** — stale 데이터 환각 차단. `[dateRef:date:...:asOf]` inline.
3. **scan 프리빌드 결과는 prebuild asOf 명시** — `dataAsOf` 가 며칠 전이면 그 시점 데이터임을 명시.
4. **데이터 수집·파이프라인 운영 질문 ("HF 업로드", "재수집") 은 운영자 절차 안내 + GitHub Actions workflow 링크** — agent 가 직접 수집 시도 금지.

## 호출 동작

`checkFreshness(stockCode)` — DART API 의 최신 공시 vs 로컬 parquet 비교 → `isFresh` (bool), `missingCount`, `lastLocalDate`, `lastRemoteDate`. 캐시 가능.

`collect(*codes, categories=)` — 종목별 DART OpenAPI 직접 호출. multi-key 병렬 (DART_API_KEYS 쉼표 구분). 증분 수집 default.

`Company(code).panel(topic)` — finance topic (BS/IS/CF/CIS/SCE/ratios) 은 `freq="Q"|"Y"|"YTD"` + `scope="consolidated"|"separate"` 토글. 비finance topic (dividend·employee 등) 은 토픽별 자체 구조. `c.topics` 가 가용 topic SSOT.

## 워크플로우 단일 책임

| workflow | 책임 | 주기 |
| --- | --- | --- |
| `dataSync.yml` | DART OpenAPI 수집 (finance·panel·report) | 12h cron |
| `dataPrebuild.yml` | scan 프리빌드 parquet 빌드 | dataSync `workflow_run` |
| `edgarSync.yml` | EDGAR 수집 + 가공 + HF 업로드 (end-to-end) | 일 cron |
| `dataAudit.yml` | 데이터 무결성 감사 (gap · 누락 · stale) | 주간 |

**HF 업로드 직렬화** — 모든 워크플로우의 HF 업로드 step 은 `concurrency.group: hf-dataset-push` 로 묶여 순차 처리. 동시 push 시 sliding-window 429 회피.

**workflow_run 체인** — dataSync 완료 → dataPrebuild 자동 트리거. EDGAR 는 단일 워크플로우 내부 end-to-end (분리 안 함).

**KindList bootstrap** — 신규 상장 종목은 dataSync 의 종목 목록 외라 별도 bootstrap workflow 가 KindList 변동 감지 후 첫 수집.

## 대표 반환 형태

```text
dartlab.checkFreshness("005930")
→ FreshnessResult
   isFresh : bool
   missingCount : int
   lastLocalDate : str         # 로컬 parquet 의 마지막 공시 접수일
   lastRemoteDate : str        # DART API 의 최신 공시 접수일
```

```text
dartlab.collect("005930", categories=["finance"])
→ dict
   "005930" : {"finance": <수집 건수>}
```

```text
Company.panel("BS")
→ pl.DataFrame
   snakeId · 항목 · 2025Q4 · 2025Q3 · ...   # 분기별 컬럼
```

## evidence 기준

데이터 답변은 `provider` (DART · EDGAR · HF) · `dataset` · `latestAsOf` · `entity/universe` 를 남긴다. `isFresh=False` 면 missingCount 함께 답변에 명시.

## 기본 실행 순서

1. 데이터 신선도 확인이면 `checkFreshness(code)` 또는 scan 프리빌드 metadata.
2. 사용자 분석 진입은 `Company` · `gather` · `scan` 셋 중 하나 — data skill 자체가 호출 대상 아님.
3. 운영자 데이터 갱신은 위 워크플로우 수동 트리거 또는 cron 대기.

## 기본 검증

데이터 SSOT 가 바뀌면 본 skill + [engines.data.foundation](/skills/engines.data.foundation) 응용 skill 갱신. 워크플로우 정의 (`.github/workflows/data*.yml`) 가 변경되면 본 skill 의 워크플로우 표를 같은 commit 에 갱신.
