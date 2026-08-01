---
id: operation.stability
title: API 안정성 정책 (tier · deprecation · semver)
kind: curated
scope: builtin
status: observed
category: operation
purpose: dartlab 공개 API 의 stability tier 4 단계 (Stable · Beta · Experimental · Alpha) 와 변경·삭제 정책을 정의한다. DART core 는 stable, EDGAR 와 일부 AI 는 더 빨리 변할 수 있다.
whenToUse:
  - 공개 API 변경 또는 삭제 검토
  - 외부 사용자가 호환성 약속 확인
  - 새 메서드 추가 시 어느 tier 로 둘지 결정
  - deprecation 안내 형식 확인
  - CLI / EDGAR / DART 의 안정성 차이 이해
inputs:
  - 변경하려는 API 식별자
  - 변경 종류 (추가 · 폐기 · 시그니처 변경)
outputs:
  - 적용할 tier
  - deprecation 안내 문구
  - CHANGELOG 항목
  - 관련 skill 갱신 항목
toolRefs:
  - CHANGELOG.md
  - operation.code
  - operation.apiContract
sourceRefs:
  - dartlab://skills/operation.stability
  - https://github.com/eddmpython/dartlab/blob/master/CHANGELOG.md
requiredEvidence:
  - tier 분류 결정 근거
  - 영향받는 호출처 목록
  - CHANGELOG 항목
  - executionRef
  - sourceRef
expectedOutputs:
  - 변경 tier 와 적용 정책
  - deprecation 메시지 또는 즉시 제거 결정
  - skill 동기화 결과
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: supported
procedure:
  - 변경하려는 API 가 어느 tier 인지 식별 (Tier 1 ~ 4).
  - tier 별 deprecation 정책 적용 (Tier 1 = 2 minor 사전 안내, Tier 2 = 1 minor, Tier 3 = 즉시).
  - DeprecationWarning 또는 CHANGELOG 항목으로 외부 사용자에게 알림.
  - 관련 skill (engines.* 또는 operation.*) 본문 동시 갱신.
  - semver 규칙 준수 (major = breaking, minor = feature, patch = bugfix).
failureModes:
  - tier 분류 없이 API 즉시 삭제
  - deprecation 안내 없이 시그니처 변경
  - CLI exit code 변경
  - 관련 skill 갱신 누락
forbidden:
  - Tier 1 API 를 deprecation 안내 없이 변경하지 않는다.
  - CLI exit code 0/1/2/130 의 의미를 변경하지 않는다.
  - skill 갱신 없이 API 변경을 완료 처리하지 않는다.
examples:
  - 새 메서드 어느 tier 에 둘까
  - Tier 1 API 폐기 안내
  - EDGAR 추가 메서드의 tier 결정
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-08-01"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

dartlab 은 현재 **DART core 가 stable**. 본 문서는 변경 시 적용할 tier 와 호환성 정책이다.

## Tier 분류

### Tier 1: Stable

변경 시 deprecation 기간 + 마이그레이션 가이드 동반.

| API | 설명 |
|---|---|
| `dartlab.Company(code)` | Company 객체 생성 facade |
| `Company.panel(topic)` | topic payload 조회 (source-aware) |
| `Company.trace()` | source provenance 조회 |
| `Company.diff()` | 기간 간 텍스트 변화 감지 |
| `Company.topics` | 사용 가능 topic 리스트 |
| `dartlab.listing()` | 전체 상장사 디렉터리 |
| `Company.panel("BS"|"IS"|"CF"|"CIS")` | 재무제표 조회 |
| `Company.panel("ratios")` | 재무비율 조회 |
| `Company.select(topic, accounts)` | topic 의 행/열 선택 |
| `Company.index` | topic × 기간 정형 보드 DataFrame |
| `Company.filings()` | 공시 문서 리스트 |
| `dartlab` CLI 진입점 | 공개 CLI 명령 진입점 |
| `dartlab.Company("AAPL")` | EDGAR Company facade (US 종목) |
| `engines.edgar.docs` | EDGAR 10-K/10-Q/20-F 섹션 가로화 |
| `engines.edgar.docs.retrievalBlocks` | EDGAR 블록 단위 LLM 검색 |
| `engines.edgar.docs.contextSlices` | EDGAR LLM context window 슬라이싱 |
| `engines.edgar.finance` | SEC XBRL 재무제표 (BS/IS/CF) |
| `engines.edgar.profile` | EDGAR docs + finance 병합 레이어 |
| `c.analysis("valuation", "가치평가")` | 다중 가치평가 (DCF · DDM · 상대) — KRW/USD 자동 감지 |
| `c.analysis("forecast", "매출전망")` | 매출 전망 (시계열 · 컨센서스 · 매크로 · ROIC) |

### Tier 2: Beta

경고 후 변경 가능. CHANGELOG 기록.

| API | 설명 |
|---|---|
| `dartlab.search()` | DART 공시 ngram/BM25 검색 — 인덱스 신선도 제한 (일별 delta 자동화 보류). 단일 종목 공시는 `Company.filings` / `liveFilings` 권장. |
| `engines.edgar.finance.SCE` | 자본변동표 (BS delta + CF) |
| `engines.edgar.finance.explore()` | XBRL Fact Explorer (tag 단위 history) |
| `engines.edgar.finance.listTags()` | XBRL tag 인벤토리 |
| `engines.edgar.docs.notes()` | XBRL TextBlock 주석 추출 |
| `engines.edgar.docs.freq()` | topic × 기간 분포 매트릭스 |
| `engines.edgar.docs.coverage()` | topic 커버리지 요약 |
| `Company.insights` | 인사이트 등급 (7 영역) |
| `Company.insights.distress` | 부실 예측 스코어카드 (4 축, 신용 등급, 현금 런웨이) |
| `Company.rank` | 시장 규모 랭킹 |
| `Company.ask()` | LLM 기반 분석 |
| `dartlab` 서브커맨드 | `ask`, `status`, `setup`, `ai`, `excel` UX |
| Server API `/api/*` | 웹 서버 엔드포인트 |
| `engines.ai.*` | AI/LLM 엔진 |
| `Company.panel("SCE")` | 자본변동표 (DART) |
| `Company.panel("ratioSeries")` | 비율 시계열 |
| `Company.network()` | 계열사 네트워크 그래프 |
| `Company.governance()` | 지배구조 데이터 |
| `Company.workforce()` | 인력 데이터 |
| `Company.capital()` | 자본 구조 |
| `Company.debt()` | 부채 상세 |
| `Company.table()` | 인라인 표 추출 |
| `dartlab.chart` | chart 도구 모듈 |
| `dartlab.ai.tools.table` | table 도구 모듈 |
| `dartlab.text` | text 도구 모듈 |
| MCP server | MCP protocol 서버 (60 tools, stdio) |
| `dartlab mcp` | MCP CLI 명령 |

### Tier 3: Experimental

Breaking 변경 허용. 프로덕션 비권장.

| API | 설명 |
|---|---|
| `export.*` | Excel export |
| `engines.ai.tools.*` | LLM tool calling |
| `Company.causalWeights()` / `valuationImpact()` / `storyTree()` / `narrativeDiff()` | Phase 10 실험의 Python 하위호환 표면. capability/EngineCall에는 노출하지 않으며 새 코드는 `Company.story`·`Company.reportModel`·`Company.simulate`의 안정 계약을 사용 |

### Tier 4: Alpha

초기 단계. 동작은 하지만 미완성.

| 기능 | 설명 |
|---|---|
| Desktop App (Windows .exe) | 독립 데스크탑 앱 — 동작 가능, 미완성 |
| Sections Viewer | 가로화 공시 뷰어 — 핵심 컨셉 동작, 구조 미정 |

## Deprecation 정책

| Tier | 안내 | 제거 |
|---|---|---|
| Tier 1 | 2 minor 사전 | DeprecationWarning → 다음 minor 에서 제거 |
| Tier 2 | 1 minor 사전 | CHANGELOG 후 변경 |
| Tier 3 | 즉시 | CHANGELOG 만 |
| Tier 4 | 없음 | 통보 없이 변경/소멸 가능 |

DeprecationWarning 예시:

```python
import warnings
warnings.warn(
    "Company.oldMethod() will be removed in v0.5.0. "
    "Use Company.newMethod() instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

## Stability 기준

DART core stable 기준:

- CI 테스트 커버리지 80%+ (core 엔진).
- API Tier 1 테스트 100% 통과.
- sections raw residual 0 유지 (대표 종목 셋).
- BS identity check 95%+ 통과.
- Tier 1 breaking change 3 개월 부재.
- PyPI 다운로드 안정 추세.
- 외부 사용자 피드백 수렴 (2 건+).

## 버전 정책

- **semver 준수**: major = breaking, minor = feature, patch = bugfix.
- DART core stable 범위는 minor 안에서 호환성 우선.
- EDGAR 와 일부 AI 기능은 tier 정책에 따라 더 빨리 변할 수 있다.
- 내부 profile merge 레이어는 docs spine 위. 공식 사용 경로는 `c.topics` 로 topic catalog 확인 후 `c.panel(topic)` 호출.

## CLI 호환성 규칙

- 최상위 `dartlab` 진입점은 Tier 1.
- 공개 서브커맨드와 주요 옵션 변경은 1 minor 이상 deprecation 사전 안내.
- exit code 는 계약: `0` 성공, `1` 런타임 에러, `2` 사용 에러, `130` 사용자 인터럽트.
- deprecated 별칭은 help 에서 숨겨도 제거 전까지는 실행 가능 유지.

## EDGAR Topic Naming

EDGAR topic 은 `{formType}::{itemId}` 형식.

- `10-K::item1Business` — 사업 설명.
- `10-K::item1ARiskFactors` — 위험 요인.
- `10-K::item7Mdna` — 경영진 토의.

짧은 별칭도 동작: `business`, `risk`, `mdna`, `governance`.

## DART · EDGAR Namespace 차이

- EDGAR 는 accessor 분리 (_DocsAccessor, _FinanceAccessor, _ProfileAccessor) + retrievalBlocks + contextSlices + 서버 API 지원 — DART 아키텍처와 같은 핵심.
- DART `docs` namespace 는 추가 sections 분석 (coverage, freq, semanticRegistry, structureRegistry) — EDGAR 미지원, Tier 2.
- DART `report` namespace (28 종 정형 공시 API) 는 EDGAR 에 없다 — DART 와 SEC 의 구조적 차이.

## 다음 단계

- [operation.code](/skills/operation.code) — 코드 품질 · 독스트링 · 릴리즈.
- [operation.apiContract](/skills/operation.apiContract) — 새 함수 추가 시 API 계약.
- [operation.cliMaintenance](/skills/operation.cliMaintenance) — CLI 유지보수 규칙.
