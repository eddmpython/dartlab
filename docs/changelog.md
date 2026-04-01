---
title: Changelog
---

# Changelog

All notable changes to DartLab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.1] - 2026-04-01

### Changed

- 엔진 호출방식 2단계 통일 + accessor 패턴 추가
- 루트 축 함수 14개 + Company 편의 메서드 4개 제거
- 전체 문서/독스트링/AI 패턴/노트북 신 패턴 일괄 변환

## [0.8.0] - 2026-04-01

### Added

- **UI 엔진 승격 (L4)**: `src/dartlab/ui/` → 루트 `ui/`로 이동. L4 표현 계층으로 정식 승격
- **scan `extractAccount()` 공통 함수**: 4개 축의 중복 계정추출 로직 통합

### Changed

- **7개 엔진 코드 감사**: ~4,100줄 삭제. scan 이중호출 제거, analysis lazy 래퍼 통합, ai _validateCode 통합, review 블록 속성 추출, company 죽은코드 제거
- **스펙 문서 정리**: generateSpec 출력 7개 → 4개 축소
- **CI 안정화**: spec-sync non-blocking 전환
- **성숙도 classifier**: Production/Stable → Beta

### Removed

- vectorStore.py (697줄), _generatedCatalog.py, api-reference.json, generated-reference.md, STRUCTURE_MAP.md

### Fixed

- growthAnalysis.py `hist` 미정의 버그, Benchmark CI gh-pages 브랜치 생성

## [0.7.16] - 2026-03-31

### Added

- **시맨틱 검색 엔진(alpha)**: `dartlab.search("대표이사 변경")` — n-gram + vector hybrid 검색
- **AI 프롬프트 패턴 3종**: growth, quick_check, value_investor
- **review 6막 구조 확장**: builders/templates 대폭 강화
- **analysis predictionSignals 확장**: 12→15축
- **ops/ 운영문서 체계**: DEV.md → ops/ 통합
- **실험 105 시맨틱 맵**: 13개 실험 스크립트

### Changed

- **analysis 6축 계산 개선**, providers/dart 강화, ai/runtime 확장, core/search 이전

### Removed

- **DEV.md 28개 파일**, core/vectorStore.py (search로 이전)

## [0.7.15] - 2026-03-30

### Added

- **`c.topicSummaries()`**: 토픽별 200자 요약 dict 반환 — docs topics는 최신 사업보고서에서 자동 추출, finance topics는 고정 설명. AI가 어떤 토픽에 뭐가 있는지 코드로 조회해서 경로 탐색 라운드 절약
- **scan 3축 신규**: `scan("efficiency")` 효율성(자산/재고/매출채권 회전율+CCC), `scan("valuation")` 밸류에이션(PER/PBR/PSR+시가총액), `scan("dividendTrend")` 배당추이(DPS 3개년+패턴분류). 한국어 alias 포함
- **scan audit 품질 개선**: 감사의견 패턴 매칭 강화, 계속기업 의심/강조사항 분류 정밀화
- **scan profitability 개선**: 금융업(은행/보험/증권) 영업이익률 fallback 로직 추가
- **VSCode MessageBubble 마크다운 렌더링**: 테이블/코드블록/리스트 완전 렌더링, 코드 복사 버튼, 접이식 thinking 블록
- **VSCode ChatPanel stdio 통신**: SSE 프록시 제거 → stdio 직접 통신으로 전환. healthCheck/portManager/processManager 제거

### Changed

- **AI 엔진 대폭 경량화 (15,420줄 삭제)**: context/, conversation/(history 제외), eval/, skills/, tools/(coding+plugin 제외), spec.py, metadata.py, reviewer.py, agent.py, aiParser.py 전부 제거. 클로드 코드 모델 — 시스템 프롬프트 + 자유 코드 실행만 남김
- **AI coding.py 샌드박스 제거**: `_FORBIDDEN_IMPORTS`, `_FORBIDDEN_CALLS`, `_ALLOWED_IMPORTS`, `_SafetyVisitor` 전부 제거. 로컬 도구에 서버급 샌드박스는 과잉 — 타임아웃만 유지
- **Company 구조 정리**: deprecated `sce` property 제거(→ `c.SCE`), deprecated `getRatios()` 제거(→ `c.ratios`), finance 위임 보일러플레이트 `_financeProperty()` 헬퍼로 압축, re-export 주석 정리
- **서버/MCP stdio 통신 전환**: SSE bridge 제거, stdio proxy 도입. MCP `__init__.py` 경량화
- **테스트 import 경로 정규화**: `test_company.py`, `test_protocol.py`, `test_fixture_finance.py` — re-export 경유 → 원본 모듈 직접 import

### Removed

- **AI 레거시 모듈 60+ 파일**: context/, conversation/(templates 포함), eval/, skills/, tools/(discovery, registry, runtime, selector, superTools/, _helpers), spec.py, metadata.py, reviewer.py, agent.py, aiParser.py
- **AI 레거시 테스트 13파일**: test_ai_capabilities, test_ai_context_modules, test_ai_parser, test_benchmarks, test_context, test_context_coverage, test_dialogue, test_eval, test_eval_deterministic, test_metadata, test_prompts, test_spec_integrity, test_tools_registry
- **VSCode 레거시**: SettingsPanel.svelte, WelcomeView.svelte, chatViewProvider.ts, sseProxy.ts, healthCheck.ts, portManager.ts, processManager.ts
- **deprecated**: `c.sce` (→ `c.SCE`), `c.getRatios()` (→ `c.ratios`), `finance.sce` (→ `finance.SCE`)

## [0.7.14] - 2026-03-30

### Added

- **basePeriod 기준점 파라미터**: 모든 analysis calc 함수(124개, 18개 파일)에 `basePeriod: str | None = None` keyword-only 파라미터 추가. `analysis("financial", "수익구조", c, basePeriod="2022Q4")` 형태로 과거 특정 시점 기준 분석 가능
- **basePeriod 인프라 (`_helpers.py`)**: `PeriodRange` dataclass, `annualColsFromPeriods()`, `quarterlyColsFromPeriods()`, `resolveBasePeriod()` — 14개 파일에 중복되던 `_annualCols` 함수를 단일 통합 함수로 대체
- **`_acceptsBasePeriod()` 안전 전달**: `inspect.signature` 기반 체크 + 캐싱으로, 마이그레이션 완료된 함수에만 basePeriod 전달. 미마이그레이션 함수에는 기존 호출 유지
- **sections pipeline Phase 1 캐시**: `_PreparedRows` 캐시로 parquet 로드 + topic 매핑 결과 재사용. 동일 종목 반복 호출 시 I/O 제거 (최대 2종목 LRU)
- **테스트 fixture 인프라**: `tests/fixtureHelper.py` + `scripts/generateFixtures.py` — heavy 테스트(bsIdentity, mappingBenchmark, regressionFinance)를 fixture 기반으로 전환, 9종목 finance.parquet 사전 생성
- **basePeriod 단위 테스트 (`test_helpers_period.py`)**: annualColsFromPeriods 10개, quarterlyColsFromPeriods 4개, PeriodRange 1개 — 총 15개 테스트

### Changed

- **8기간 표준화**: 모든 analysis 테이블의 기본 기간 수를 5→8로 통일. `_MAX_YEARS`, `_MAX_RATIO_YEARS`, `maxYears`, `maxQuarters` 기본값 전부 8. review builders `_MAX_QUARTERS` 5→8. 연간 8개년, 분기 8분기 일관 출력
- **analysis 단일 진입점 통합**: `Analysis.__call__`에 `basePeriod` 파라미터 추가 → `_run()`에서 `_acceptsBasePeriod(fn)` 체크 후 전달. 기존 호출 100% 하위호환
- **review 소비 경로 관통**: `buildBlocks(company, keys, basePeriod=)` → `buildReview(company, basePeriod=)` → `Review.__call__(basePeriod=)` → `Company.review(basePeriod=)` → `buildReviewWithAI(basePeriod=)` 전 경로 basePeriod 관통
- **review registry calc 호출 80+곳**: `calcXxx(company)` → `calcXxx(company, basePeriod=basePeriod)` 일괄 변경
- **매출예측 엔진 v3→v4**: 실험 098 기반 — 매크로 GDP beta(기여도 0%), FX regex(29% 성공률), 주가내재 역산(순환논리), 횡단면 회귀(비활성), 공시 tone(미검증) 5개 소스 제거. 7-소스→4-소스 앙상블로 경량화
- **AI 시스템 프롬프트 대폭 간소화**: `_ANALYSIS_WORKFLOW_GUIDE` 90줄 → `_SYSTEM_PROMPT` 25줄. `_detectAvailableModules()`, `_detectSector()` 등 사전 감지 로직 제거. 도구 우선순위 명시 (1차: review/scan/gather → 2차: Company 직접)
- **ask() 호출 구조 정리**: `__init__.py` ask() 함수 — 중복 인자 나열 3곳 → `_call_kwargs` dict 1곳으로 통합

### Fixed

- **heavy 테스트 안정성**: bsIdentity, mappingBenchmark, regressionFinance — HF 다운로드 의존 → fixture parquet 기반으로 전환. CI 환경에서 네트워크 불안정으로 인한 실패 해소

## [0.7.13] - 2026-03-29

### Added

- **review 매출전망 섹션 (6부)**: `c.review("매출전망")` — 7-소스 앙상블 매출 예측. revenueForecast, segmentForecast, proFormaHighlights, scenarioImpact, forecastMethodology, historicalRatios, forecastFlags 7개 블록. 업종별 시나리오 분화 지원
- **review 선택적 빌드**: `buildBlocks(company, keys=)` — section 지정 시 해당 블록만 빌드. 단일 섹션 0.5초 vs 전체 54초 (108x 속도 향상)
- **dartlab.askLog**: `dartlab.askLog = True`로 ask/chat 세션의 JSONL 이벤트 로그 토글
- **gather 확장**: sector, insider, ownership 수집 경로 추가
- **18축 분석 엔진 확장**: audit 모듈 + analysis 캐시 최적화

### Changed

- **AI 워크플로우 가이드 축소**: 90줄 절차 강제 → 25줄 원칙만. `capabilities(search=)` 자율 탐색 기반으로 전환. 주가 질문에 재무분석 강제하던 문제 해소
- **투하자본 계산 개선**: `calcEvaTimeline` — 부채총계 → 이자부차입금(단기+장기+사채) - 현금. ROIC와 동일 기준
- **AI 코드 실행기 개선**: Polars `set_fmt_float('full')` + `set_tbl_cols(20)` 자동 주입. 과학적 표기(e-01) 및 컬럼 잘림 해소
- **시스템 프롬프트**: "즉시 코드 실행" 원칙 3개 프롬프트(KR full/EN full/compact) 전부 반영

### Fixed

- **tabulate 의존성 에러**: AI가 `to_pandas().to_markdown()` 생성 → `print(df)` + Polars config으로 대체
- **getattr 보안 위반 오탐**: `c.gather()` 호출 시 AST 검증기가 차단 → FORBIDDEN_CALLS에서 제거
- **CF 계정명 fallback**: 투자자산 계정 변경 대응 + CF 패턴 미보고 처리
- **동의어 계정 중복 경고**: WACC/EVA 계산 + MetricBlock 수정
- **review trend 블록**: history 구조 불일치 수정 — 18축 전부 렌더링

## [0.7.12] - 2026-03-28

### Added

- **scan 3축 신규**: `cashflow` (OCF/ICF/FCF + 8유형 현금흐름 패턴 분류), `audit` (감사의견, 감사인변경, 종합 리스크 플래그), `insider` (최대주주 지분변동, 자기주식 현황, 경영권 안정성). 총 11축 시장 횡단분석
- **통합 scan 인터페이스**: `dartlab.scan("cashflow")`, `dartlab.scan.topics()` — 11축을 하나의 callable class로 통합. 한글 alias 지원
- **review narrative 자동생성**: 순환 서사 감지 + 섹션 간 스레드 연결
- **review 블록 60+개**: 이전 16개에서 확장 (수익성/성장성/안정성/효율성/이익품질/비용구조/자본배분/투자효율/재무정합성)
- **TUI 개선**: 커맨드 팔레트, 웰컴 스크린, 채팅 영역 고도화
- **AI 분석 품질 향상 로드맵**: `TODO_AI_ANALYSIS.md`

### Changed

- **scan debt risk 고도화**: 위험등급 판정 세분화, 만기 집중도 분석 강화
- **scan workforce growth 강화**: 성장률 계산 고도화
- **README 갱신**: Market Scan 섹션에 통합 scan 인터페이스 + 신규 3축 반영

### Fixed

- **CircuitBreaker flaky 테스트**: 타이밍 여유 확보 (Windows 간헐 실패 해결)

## [0.7.11] - 2026-03-28

### Added

- **AI 도구 카탈로그 자동 생성**: `generateSpec.py`가 registerTool() AST에서 전체 JSON Schema를 추출하여 `_generatedCatalog.py` 자동 생성. 수동 하드코딩 `_TOOL_CATALOG` 제거
- **CAPABILITIES.md 완전 명세**: AI Tools 섹션에 Super Tool 8개의 actions, parameters, questionTypes 완전 포함. Scan Axis 8축 + 질문유형별 도구 매핑 + 도구 연쇄 패턴 자동 생성
- **AI 품질 테스트 실험 103-002**: 토큰 효율 77% 절감 + 4/4 시나리오 PASS + 파라미터 정확도 95.8%

### Changed

- **시스템 프롬프트 토큰 77% 절감**: `_TOOL_CATALOG` 20,872자 → 4,697자. Super Tool 8개만 포함 (불필요한 defaults 99개 제거)
- **scan 구조 정리**: `scan/screen/` 디렉토리 삭제, `RankInfo`/`getRank` → `scan/rank.py`로 이동. `scan/signal`, `scan/peer`, `scan/network/health` 제거
- **analyze Super Tool 정리**: esg, peer, screen action 제거 (미구현 phantom action 정리). enum과 실제 handler 불일치 해소
- **market Super Tool 정리**: signal, benchmark, groupHealth, peer, screen action 제거. 실제 동작하는 13개 action만 유지
- **strategy 모듈 정리**: `analysis/strategy/esg/`, `analysis/strategy/supply/` 디렉토리 삭제 (미완성 모듈)

### Fixed

- **`_generatedCatalog.py` phantom action 문제**: LLM이 존재하지 않는 action을 호출하여 "[오류]" 응답을 받는 문제 해결. registerTool() schema enum과 정확히 일치하도록 자동 생성
- **테스트 import 정리**: `scan.screen` → `scan.rank` 이동에 따른 테스트 파일 import 수정. 삭제된 모듈 테스트 제거

## [0.7.10] - 2026-03-27

### Added

- **review 패키지**: 구조화된 기업 분석 보고서 시스템
  - `c.review("수익구조")` / `c.review("자금조달")` — 템플릿 기반 분석
  - `blocks(company)` — 16개 블록 사전, `Review([...])` 자유 조립
  - `c.reviewer()` — LLM 종합의견 + guide 파라미터
  - rich/html/markdown/json 4가지 렌더링
- **analysis/strategy calc-only 패턴**: 15개 calc 함수, import 방향 분리
- **README Review 섹션** (EN/KR)
- **sampleReview 노트북**, 블로그 124호

### Changed

- sections pipeline, DART/EDGAR Company review 메서드

## [0.7.9] - 2026-03-26

### Added

- **Gemini OAuth 2.0 브라우저 로그인**: API key 없이 Google 계정 로그인으로 Gemini 사용 가능
- **Gather 엔진 시계열 전면 개선**: `price()`, `flow()`, `macro()` Polars DataFrame 시계열 반환
- **네이버 차트 API 전환**: 모바일 API(1000일) → 차트 API(6000일, 수정주가, 1회 요청)
- **Gather 인프라 강화**: circuit breaker, stale-while-revalidate, Yahoo Direct consensus, FMP 확장
- **AI 도구 아키텍처 재설계**: 101개 → 8개 Super Tool 통합
- **Insight 10영역 확장**: predictability, uncertainty, coreEarnings 3영역 추가
- **`scanAccount()` / `scanRatio()`**: 전종목 재무 배치 스크리닝 (2,700+ DART / 500+ EDGAR)
- **sections Categorical 스키마**: RSS 427MB 절감 (83%)
- **ECOS gather 엔진**: 한국은행 경제통계 22개 지표 수집
- **Google Gemini provider**: `google-genai` SDK 기반
- **Ollama 속도 최적화**: GPU 자동 감지, flash_attn, 스마트 preload
- **HF Spaces Docker 웹 데모**: Gradio 기반 AI 분석 데모
- **글로벌 피어 매핑**: WICS→GICS 섹터 기반 자동 매핑

### Fixed

- Gather 코드 감사: 전체 에러 경로 `log.warning` 전환
- 차트/테이블 기간 컬럼 `2024Q1` 형식 지원
- EDGAR docs 수집 안정화: filing 파싱 실패 시 개별 스킵

### Changed

- `macro()` 시그니처: `macro(market="KR", indicator=None)` 직관적 호출
- DEV.md 전수 현행화 (analysis 10모듈, insight 10영역, gather 도메인 확장)
- README EN/KR 동기화: Market Data, scanAccount/scanRatio 섹션

## [0.7.8] - 2026-03-25

### Added

- **3-Layer Freshness 감지**: HF ETag(L1) → TTL 폴백(L2) → DART API `rcept_no` diff(L3) 3계층 모델로 로컬 데이터 최신 여부를 자동 판단
- **`freshness.py` 모듈 신규**: `checkFreshness(stockCode)` 종목 단위 감지, `scanMarketFreshness(days=7)` 시장 전체 스캔, `collectMissing(stockCode)` 누락 공시 증분 수집
- **`dartlab.checkFreshness()` 루트 함수**: `import dartlab` 하나로 freshness 체크 가능
- **`Company.update()` 메서드**: 누락된 최신 공시를 명시적 증분 수집 (`c.update()`, `c.update(categories=["finance"])`)
- **ETag 기반 HuggingFace freshness**: HTTP HEAD 요청(~0.5초)으로 원격 데이터 갱신 여부 판단. `.parquet.etag` 사이드카 파일로 ETag 비교
- **CLI `--check` / `--incremental` 옵션**: `dartlab collect --check 005930` (freshness 체크만), `dartlab collect --incremental` (누락 공시만 증분 수집)
- **guidance 메시지 5종**: `freshness:checking/fresh/stale/noKey/scanDone` + `hint:newFilingsAvailable` 구조화 메시지
- **README Data 섹션 전면 개편**: 3-Step Pipeline, Freshness 3-Layer 테이블, 감지/수집 예시 (Python + CLI), 배치 수집 (영문/한국어 동시)

### Fixed

- **배치 수집 v1 스키마 크래시**: 구형 HuggingFace parquet에 `reprt_code`/`apiType` 컬럼이 없을 때 `SchemaError` 대신 빈 set 반환 (미수집 취급 → 재수집)
- **`dataLoader.py` 중복 분기**: `"error:download_failed" if category == "docs" else "error:download_failed"` 양쪽 동일한 삼항연산 정리
- **docs 데이터 출처 표기**: installation.md "GitHub Releases" → "HuggingFace Datasets"로 현행화, quickstart.md 자동 다운로드 메시지 동기화

## [0.7.7] - 2026-03-24

### Fixed

- **stale TTM 차단**: `getTTM()`에 trailing `None` 최신성 가드를 추가하여 오래된 분기 값만 남은 시계열을 최신 TTM으로 잘못 해석하지 않도록 수정
- **`finance.ratios` 최신성 검증 강화**: `calcRatios()`가 분기 TTM 계산 시 stale CF/IS 항목을 최신값처럼 섞지 않도록 변경
- **IS-CF 순이익 교차검증 오탐 수정**: SK하이닉스처럼 CF `net_profit`이 2018년 값에서 끊긴 경우 최신 IS TTM과 비교해 경고를 띄우던 버그 해결
- **회귀 테스트 2건 추가**: stale TTM utility 케이스와 stale CF 순이익 cross-check 오탐 케이스를 unit test로 고정

## [0.7.6] - 2026-03-23

### Added

- **`dartlab.simulation()` 루트 함수**: 경제 시나리오 시뮬레이션. Company 메서드 `c.simulation()` 동시 추가
- **`__all__` 보완**: `governance`, `workforce`, `capital`, `debt`, `simulation` 5개 함수 추가
- **EDGAR Company Tier 1 승격**: EDGAR core (sections, show, trace, diff, BS/IS/CF, ratios, profile) Stable로 격상
- **EDGAR Company.valuation() / forecast()**: 2-Tier 원칙에 따라 EDGAR Company 메서드 추가
- **analyst 모듈 USD 자동 감지**: `dartlab.valuation()`, `dartlab.forecast()`, `dartlab.simulation()` 루트 함수가 `company.currency` 기반 KRW/USD 자동 포맷
- **US 매크로 시나리오**: `PRESET_SCENARIOS_US` (baseline, adverse, rate_hike, rate_cut, tech_downturn) + US 섹터 탄력성 12개
- **`fmt.py` 통화 포맷 헬퍼**: `fmtBig()` (억/M), `fmtPrice()` (원/$), `fmtUnit()` — analyst 모듈 공통 사용
- **AI 비서 도구 2개**: `checkDataReady` (종목별 데이터 준비 상태 확인), `estimateTime` (작업 예상 시간 안내)
- **AI 시스템 프롬프트 데이터 관리 원칙**: 분석 전 데이터 확인, 시간 안내, 단계별 가이드 규칙 추가
- **AI 분석 데이터 신선도 헤더**: meta 이벤트에 `dataDate` 필드 자동 삽입 (Company filings 최신일 기반)
- **AI 도구 자동 탐색 모듈**: `tools/discovery.py` — 도구 카탈로그 동적 생성
- **AI 도구 선택기**: `tools/selector.py` — 질문 유형별 도구 우선순위 선택
- **AI 7개 도메인 도구 확장**: company/finance/analysis/scan/system/openapi/ui 도구 세트 강화
- **AI skeleton 가이드 기반 분석**: 구조화된 분석 흐름 + 동적 턴 확장
- **capabilities 런타임 선언**: `core/capabilities.py` 도구 기능 메타데이터 모듈
- **USD 테스트 7개**: DCF/valuation/forecast/simulation USD repr + fmt helper 테스트
- **README AI 비서 권장 Tip**: AI Analysis 섹션에 `dartlab.ask()` 적극 권장 문구 (영문/한국어)
- **README Market Scan 확장**: `screen()`, `benchmark()`, `signal()` 함수 문서화

### Fixed

- **IS 계정 정렬**: `selling_and_administrative_expenses` sortOrder 1050→1300 수정. 판관비가 매출원가 위에 표시되던 문제 해결. `loss_before_tax` sortOrder 1350→1905로 위치 교정
- **CFS/OFS 시트 단위 분리**: `_applyCfsPriority()` 행 단위 혼합 → 시트(연도×분기×재무제표) 단위 선택으로 변경. 동일 시트에 연결/별도 숫자가 섞이던 문제 해결. CFS 존재 시 CFS만, 없으면 OFS 전체 폴백
- **`forecast()`/`valuation()` timeseries None 가드**: `c.finance.timeseries`가 None일 때 크래시 대신 None 반환
- **`hasattr` 이중 체크 제거**: `getattr(c, "sectorKey", None) if hasattr(...)` → `getattr(c, "sectorKey", None)` 단순화
- **`revenueForecast.py` 도달불가 조건**: `len(recent) > 8` → `len(valid) > 8` (recent = valid\[-4:\]이므로 항상 False였음)
- **`revenueForecast.py` dict key 통일**: `reinvestment_rate` → `reinvestmentRate`, `delta_nwc` → `deltaNwc`, `invested_capital` → `investedCapital`, `fundamental_growth` → `fundamentalGrowth`, `sign_changes` → `signChanges`, `data_points` → `dataPoints` — 프로젝트 네이밍 규칙과 불일치하던 6개 키 수정
- **timeseries 튜플 언래핑**: `finance.timeseries`가 `(dict, list)` 튜플 반환 시 `dict`만 추출 — DART/EDGAR 양쪽 analyst 함수 에러 수정
- **`revenueForecast.py` 속성명 버그**: `tsResult.r_squared` → `tsResult.rSquared` — 실제 속성명과 불일치하여 AttributeError 발생하던 3곳 수정

### Changed

- **stability.md Tier 재편**: EDGAR core Tier 2 → Tier 1, valuation/forecast/simulation Tier 3 → Tier 1
- **README 양쪽 Stability 테이블 갱신**: EDGAR core Stable, analyst 함수 Stable 반영
- **AI runtime agent 경량화**: 292줄 → 구조화된 모듈로 분리

## [0.7.5] - 2026-03-22

### Added

- **`_reference/` 공개**: DART/EDGAR finance 계정학습 메커니즘 및 매핑 도구를 git 추적 대상으로 전환. wheel 배포에서는 제외
- **stability.md 확장**: `index`, `filings()`, `profile`, `CIS`, `SCE`, `timeseries`, `ratios`, 도구 모듈 등 누락 API의 안정성 등급 명시
- **EDGAR topic naming convention 문서화**: `{formType}::{itemId}` 형식 및 짧은 alias 설명
- **DART/EDGAR namespace 차이 문서화**: docs/report namespace 비대칭 설명 추가

### Changed

- **`sce` deprecation**: `finance.sce` / `c.sce`에 DeprecationWarning 추가 → v0.8.0에서 제거 예정. `SCE`(대문자)가 공식 경로
- **`filings()` type hint 통일**: DART `filings()` 반환 타입을 `DataFrame` → `DataFrame | None`으로 Protocol과 일치 (실제 동작 변경 없음)
- **CLAUDE.md `_reference/` 정책 갱신**: 계정학습 메커니즘 공개, git 추적 대상으로 재정의

## [0.7.4] - 2026-03-22

### Added

- **`dartlab collect` CLI 명령**: DART 공시문서 HTML → parquet 수집
- **`dartlab report` CLI 명령**: 기업 분석 보고서 Markdown 자동 생성
- **AI 분석 validation 모듈**: `runtime/validation.py` — LLM 응답 품질 검증 로직 분리
- **테스트 8개 신규**: `test_api_common`(17), `test_company_validation`(12), `test_resolve_messages`(6), `test_screen_presets`(5), `test_models_validation`(15), `test_context_coverage`(8), `test_mapping_integrity`, `test_ratios_golden` — 서버 보안/입력 검증/비즈니스 로직 커버리지 확대
- **`.env.example`**: 15개 환경변수 문서화 (DARTLAB_DATA_DIR, DART_API_KEY, OPENAI_API_KEY 등)
- **보안 pre-commit 훅**: `detect-private-key`, `bandit` 추가
- **CI security job**: `pip-audit --strict` 의존성 취약점 검사
- **서버 입력 검증 강화**: Pydantic Field 제약 (question max_length=5000, company max_length=100 등), 종목코드 path traversal 방어 regex (`^[A-Za-z0-9가-힣]{1,20}$`)
- **에러 메시지 credential 마스킹**: api_key, token, secret, password, bearer 패턴 자동 `***` 치환

### Changed

- **AI context builder 리팩토링**: 컨텍스트 조립 로직 구조화 (builder.py 113줄 변경)
- **AI 런타임 파이프라인 리팩토링**: core.py, pipeline.py — 분석 흐름을 validation/events/core로 모듈 분리
- **CI test 마커 필터 보강**: `-m "not requires_data"` → `-m "not requires_data and not heavy"` (CI에서 heavy 테스트 제외)
- **pre-commit ruff 버전 동기화**: v0.9.0 → v0.11.4 (CI ruff 버전과 일치시켜 format 불일치 해소)
- **ruff exclude에 `_reference/` 추가**: 참조 파일 lint 제외
- **의존성 상한 추가**: `polars<2`, `requests<3`, `rich<14`, `beautifulsoup4<5` 등 주요 의존성에 major version 상한 설정
- **rank 엔진 print → logger**: `rank.py`, `screen.py`의 print문을 `logging.getLogger(__name__)` 전환
- **서버 bare except 구체화**: `streaming.py`의 `except Exception` → OSError, RuntimeError 등 7개 구체 예외 타입
- **publish.yml 버전 검증 추가**: git tag와 pyproject.toml 버전 불일치 시 빌드 자동 실패
- **test_cli_e2e 안정화**: CLI subcommand 목록 하드코딩 → 핵심 명령 개별 존재 체크 (새 명령 추가 시 테스트 안 깨짐)
- **test_server LRU 안정화**: 메모리 압박 환경에서 `_max_size` 동적 축소로 인한 테스트 실패 → 메모리 체크 모킹

### Fixed

- **CI lint 10연패 해결**: `_reference/` 폴더의 참조 코드(F601 중복키, E722 bare except, F403 star import) 44개 에러 → ruff exclude 설정으로 근본 해소
- **CI format 실패**: pre-commit ruff v0.9.0과 CI ruff v0.11.4 버전 차이로 42개 파일 포맷 불일치 → 버전 동기화
- **CI test_cli 실패**: `dartlab.core.ai.detect` 모듈이 git에 미커밋 상태에서 테스트가 import 시도 → 누락 파일 추가
- **CompanyCache LRU 테스트**: 메모리 1.5GB 초과 시 캐시 크기가 5→1로 축소되어 `assert len(cache) == 5` 실패 → `_check_memory_pressure` 모킹

## [0.7.3] - 2026-03-21

### Added

- **도구 모듈 루트 접근**: `dartlab.chart`, `dartlab.table`, `dartlab.text`로 직접 사용 가능 — `_Module.__getattr__` lazy import, 기존 `from dartlab.tools import chart` 경로도 유지
- **CLI OAuth 브라우저 로그인**: `dartlab setup oauth-codex` 실행 시 브라우저 자동 열림 + PKCE 콜백 서버 대기 (120초 타임아웃)
- **CLI 스트리밍 기본값**: `dartlab ask`가 기본 스트리밍 출력 (`--no-stream`으로 비활성화)
- **CLI provider 전체 안내**: `dartlab setup`에 5개 provider (oauth-codex, codex, ollama, openai, custom) 설치/설정 가이드 추가
- **CLI 상태 테이블**: `dartlab status`가 전체 provider를 테이블 형식으로 요약
- **AI Marimo 노트북**: `startMarimo/aiAnalysis.py` — `dartlab.ask()` 사용 예시 (기본, provider 지정, 스트리밍, include/exclude)
- **README AI 분석 섹션**: `dartlab.ask()` + CLI 사용법 + OpenDART API 키 안내

### Changed

- **차트 메서드명 단순화**: `revenue_trend` → `revenue`, `cashflow_pattern` → `cashflow`, `dividend_analysis` → `dividend`, `balance_sheet_composition` → `balance_sheet`, `profitability_ratios` → `profitability` (기존 이름은 alias로 유지)
- **README/README_KR 차트 예시**: `from dartlab.tools import chart` → `dartlab.chart.*` 단축 경로로 변경
- **메모리 최적화 — OOM 크래시 해결**: 32GB 시스템에서 Python 37GB+31GB 소비 → 크래시 발생. 8개 기법 적용:
  - LRU 캐시 maxsize 85% 축소 (textStructure.py 6개, 실측 working set 기준)
  - CompanyCache 20→5, TTL 30분→10분
  - MCP 캐시에 LRU 퇴출 정책 적용 (기존 무제한 dict)
  - Polars Categorical 자동 전환 (sj_div, topic, account_id 등 반복 문자열)
  - Int64→Int32 다운캐스트 (year, section_order 등)
  - `loadData()` columns 파라미터 추가 — Company 초기화 시 corpName만 경량 읽기
  - sections() 파이프라인 중간 dict 조기 해제 + `gc.collect()`
- **채팅 UI rAF 스크롤**: 스트리밍 흔들림 해소
- **contentSplitter monotonic 보장**: committed 영역이 줄어들지 않는 증분 마크다운 렌더러
- **채팅 입력 provider/model chip**: 현재 설정 표시
- **사이드바 대화 미리보기**: 마지막 메시지 50자 미리보기

### Fixed

- **docs/api/finance-summary.md**: 존재하지 않는 `c.fsSummary()` 참조를 공개 API (`c.BS`, `c.IS`, `c.CF`)로 수정
- **docs/tutorials/04_ratios.md**: 내부 모듈 경로 (`engines.dart.finance.pivot`)를 공개 API (`c.finance.ratioSeries`)로 수정
- **CLI 스트리밍 출력 누락**: `dartlab ask` 스트리밍 제너레이터 미소비 버그 수정
- **startMarimo/aiAnalysis.py**: 깊은 import 경로를 `dartlab.ask()` 루트 진입점으로 수정

## [0.7.2] - 2026-03-20

### Added

- **복합 재무비율 11개**: ROIC, DuPont 3분해(마진·회전율·레버리지), CCC(현금전환주기), Altman Z-Score, Piotroski F-Score, EV/EBITDA, 이자보상배율, 배당성향, 배당수익률
- **AI 대화 품질 Phase 1**: CoT 구조화 프레임워크(4단계 분석), Tool Routing(질문 유형별 도구 서브셋), Self-Critique/Reflection(답변 자체 검증), 정보 배치 최적화(Lost-in-the-Middle 대응)
- **MCP 39개 도구 노출**: OpenAI function calling 스키마 → MCP Tool 자동 변환, stock_code 자동 주입
- **증분 마크다운 렌더러**: `createIncrementalRenderer()` — 스트리밍 중 완결 블록 캐시 + 꼬리만 재파싱

### Changed

- **UI 성능 최적화**: `content-visibility: auto`(뷰포트 밖 스킵), SSE chunk rAF 배칭(스트리밍 끊김 방지), IntersectionObserver 점진 렌더(초기 10개), `contain: layout style paint`(테이블 격리)
- **Tool Description 정밀화**: 15개 핵심 도구에 "사용 시점 / 사용하지 말 것" 가이드 추가
- **Parallel Tool Calling**: OpenAI provider `parallel_tool_calls=True` 활성화
- **히스토리 압축 개선**: 구조화된 메타 추출(관심 기업, 분석 주제, Q&A 쌍)
- **`dartlab ui` alias 제거**: deprecated CLI alias 완전 제거, 테스트 정리

### Fixed

- **보안 감사 수정**: XSS 이스케이프, path traversal 차단, bare except 구체화, CORS 강화, MD5 usedforsecurity, subprocess 보안, SSL fallback
- **CAPEX 부호 버그**: 음수 처리 수정 + ZeroDivision 방어
- **글로벌 캐시 스레드 안전**: 5곳에 threading.Lock double-check 패턴 적용

## [0.7.1] - 2026-03-20

### Added

- **시장 전수 스캔 4축**: `governance`, `workforce`, `capital`, `debt` 엔진 추가
- **공개 API 확장**: `Company.governance/workforce/capital/debt()`와 모듈 레벨 `dartlab.governance/workforce/capital/debt()` 추가
- **scan 개발 문서**: `src/dartlab/engines/dart/scan/DEV.md`, `src/dartlab/engines/dart/scan/network/DEV.md`, `src/dartlab/tools/DEV.md`
- **공시뷰어 근본 재설계**: entries 기반 인터리브 렌더링 — 텍스트/테이블 원본 순서 복원
- **heading level 전달**: sections `textLevel` → viewer → 프론트엔드까지 레벨 메타데이터 전파
- **AI 순수 대화 감지**: `_is_pure_conversation()` — "잘되나", "대화 계속 안되나" 등 일상 대화 패턴 자동 감지
- **서버 응답 최적화**: GZip 압축 + Cache-Control + asyncio.gather 병렬화

### Changed

- **관계 네트워크 경로 정리**: 내부 import 경로를 `affiliate`에서 `scan.network`로 통일
- **TopicRenderer 단일 루프**: nonTextBlocks 이중 루프 → docEntries 단일 루프로 교체
- **뷰어 UI 개선**: nav 접기 토글, 테이블 sticky 첫 컬럼, 숫자 정렬
- **AI 프롬프트 강화**: 내부 구현 노출 금지 규칙 + 순수 대화 시 viewContext 무시
- **oauthCodex timeout**: 300초 → 90초로 단축
- README / README_KR에 관계 네트워크와 시장 스캔 사용 예시 반영

### Fixed

- 관계 네트워크 회귀 테스트 import 경로를 새 패키지 구조에 맞게 수정
- `test_scan_axes.py`로 새 scan 축 import/분류 기본 검증 추가
- `view=\"market\"` 요약에서 빈 시장 라벨을 `미분류`로 정리

## [0.7.0] - 2026-03-19

### Added

- **AI 공시 탐색 도구**: `show_topic`, `list_topics`, `trace_topic`, `diff_topic` — LLM이 Company의 핵심 API를 직접 호출
- **AI 동적 컨텍스트**: Company의 실제 topics/insights를 자동으로 LLM 컨텍스트에 포함
- **ChartSpec JSON 프로토콜**: `chart.spec_*()` → JSON dict → `chart.chart_from_spec()` 경로 추가 (combo, radar, waterfall, sparkline, heatmap, pie)
- **UI 뷰어 대폭 개선**: DisclosureViewer, TopicRenderer, ViewerNav, TableRenderer 리뉴얼
- **docs quickstart**: "바로 실행해보기" 섹션 추가 (startMarimo + Colab 링크)

### Changed

- **README/README_KR 개선**: 자동 다운로드 설명, Try It Now 섹션, 데이터 섹션 보강, Docs/Blog 뱃지
- **서버 TOC 챕터 정렬**: 로마 숫자 순서(I~XII) 정렬 적용
- **sections pipeline**: cadence 메타 계산 성능 개선 (불필요한 리스트 컴프리헨션 제거)
- **AI agent 분석 절차**: sections 중심으로 재정렬 (`list_topics` → `show_topic` → `get_data` 순서)

### Fixed

- **CLI e2e 테스트**: Windows cp949 인코딩 오류 수정 (UTF-8 명시)

## [0.6.0] - 2026-03-19

### Added

- **세로 뷰**: `show(topic, period=["2024Q4", "2023Q4"])` — 특정 기간을 세로(기간 × 항목)로 비교
- **topics DataFrame**: `c.topics`가 리스트 대신 DataFrame 반환 (topic, source, blocks, periods 컬럼)
- **ratios 시계열**: `c.ratios`가 단일 시점 대신 시계열 DataFrame 반환 (항목 × period, 최신 먼저)
- **RatioResult `__repr__`**: 6개 카테고리별 한국어 라벨 + 억 단위 포맷 가독성 개선
- **report 분기 데이터**: DART report가 Q4(연간)만 아닌 Q1~Q4 전 분기 표시
- **EDGAR `_transposeToVertical`**: EDGAR에도 세로 뷰 지원 추가
- **서버 viewer 기능 확장**: TOC, topic summary SSE, diff 엔드포인트 추가

### Changed

- **finance/report 기간 정렬**: 모든 재무/report DataFrame 컬럼이 최신 먼저 역순 정렬
- **2015년 데이터 제외**: finance pivot에서 2015년 필터링 (Q4만 있어 standalone 변환 불가)
- **openai_compat provider**: `OpenAIError`를 catch 목록에 추가 (서버 status 500 수정)
- README/README_KR에 topics, ratios 시계열, 세로 뷰 반영
- docs quickstart/overview/ratios 튜토리얼 현행화
- 노트북 `c.name` → `c.corpName` 수정, topics DataFrame 반영
- startMarimo 두 파일에 세로 뷰 데모 셀 추가
- 랜딩 CodeDemo에서 `ratios` 설명 업데이트

### Fixed

- EDGAR `index` 프로퍼티가 topics DataFrame을 순회할 때 컬럼명이 아닌 topic 리스트로 순회하도록 수정
- 테스트 코드에서 topics를 리스트로 가정하던 부분을 DataFrame 호환으로 수정

[Unreleased]: https://github.com/eddmpython/dartlab/compare/v0.7.9...HEAD
[0.7.9]: https://github.com/eddmpython/dartlab/compare/v0.7.8...v0.7.9
[0.7.8]: https://github.com/eddmpython/dartlab/compare/v0.7.7...v0.7.8
[0.7.7]: https://github.com/eddmpython/dartlab/compare/v0.7.6...v0.7.7
[0.7.6]: https://github.com/eddmpython/dartlab/compare/v0.7.5...v0.7.6
[0.7.5]: https://github.com/eddmpython/dartlab/compare/v0.7.4...v0.7.5
[0.7.4]: https://github.com/eddmpython/dartlab/compare/v0.7.3...v0.7.4
[0.7.3]: https://github.com/eddmpython/dartlab/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/eddmpython/dartlab/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/eddmpython/dartlab/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/eddmpython/dartlab/compare/v0.6.1...v0.7.0
[0.6.1]: https://github.com/eddmpython/dartlab/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/eddmpython/dartlab/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/eddmpython/dartlab/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/eddmpython/dartlab/compare/v0.4.5...v0.5.0

## [0.5.1] - 2026-03-19

### Added

- EDGAR sections 텍스트 구조 메타데이터 추가 (`textNodeType`, `textLevel`, `textPath` — heading/body 분리)
- EDGAR sections 연간 보고서 Q4 라벨 통일 (`2024` → `2024Q4`)
- quickstart 문서에 insights 섹션 추가
- pyproject.toml keywords에 `edgar`, `sec`, `sections` 추가

### Changed

**공개 문서 전면 현행화**
- README / README_KR를 `sections` 중심 회사 맵 서사로 재작성 (ratios, insights, diff, text structure, EDGAR 반영)
- docs 전체 흐름을 `sections → show → trace` 기준으로 통일
- `finance-others.md`의 `c.get()` 패턴을 `c.report.extract()` / `c.docs.notes` 경로로 전환
- `stability.md`에서 profile CLI 제거, profile 설명 현행화
- `sections.md`에 텍스트 구조 컬럼(textNodeType/textLevel/textPath) 반영, Q4 기간 표기 통일
- `overview.md`에 텍스트 구조 컬럼 추가
- pyproject.toml description에 EDGAR 반영
- llms.txt description을 DART+EDGAR 통합으로 갱신
- EDGAR `DEV.md` 현행화 (sections 형태, show 계약, profile 제거)

### Removed

- 중복 DEV 문서 2건 삭제 (`dart/dev/company.md`, `dart/docs/dev/learning.md`)

## [0.5.0] - 2026-03-15

### Added

**EDGAR Company DART급 완성**
- EDGAR Company가 DART Company와 동일한 `sections / show / trace` 메인 흐름에 합류
- EDGAR sections 매퍼 100% (182개 매핑, 442,025행), 974종목 에러 0 전수조사 통과
- EDGAR profile namespace 구현 — docs + finance merged view
- EDGAR sections blockType 분리 (text/table)
- 10-K/10-Q 의미적 대응 6쌍 매핑 (riskFactors, mdna, financialStatements, controls, legalProceedings, exhibits)

**OpenDART API 직접 클라이언트**
- `engines/dart/openapi` 모듈 추가 — OpenDART REST API 직접 호출 지원

**sections / show() 품질 강화**
- `sections` blockType 분리: text/table 별도 행, blockOrder로 원본 순서 보존
- `c.table()` — subtopic wide 셀의 markdown table 구조화 파싱
- table-heavy docs topic 자동 subtopic wide 수평화 + topic 한글화

**문서 대규모 개선**
- README/README_KR: 공개 흐름을 `sections/show/trace` 기준으로 재구성, EDGAR 통합 강조
- docs/tutorials/edgar: EDGAR 통합 가이드 신규 추가 (7개 섹션 + DART 비교표)
- docs/stability: EDGAR → Tier 2 (Beta) 승격
- docs/quickstart, api/overview: EDGAR 예시 추가
- notebooks/tutorials/09_edgar.ipynb: EDGAR Colab 노트북 신규
- navigation.ts: EDGAR 튜토리얼 항목 추가

**랜딩 사이트 리디자인**
- shadcn 스타일 전면 리디자인 — UI 컴포넌트 + 레이아웃 + 랜딩 전체
- 블로그 카드 프리뷰 — 아바타 대신 콘텐츠 SVG 자동 매칭
- WebP 변환 — avatar 12개 PNG→WebP (85% 용량 절감) + picture 패턴 전면 적용
- SEO Phase 1/2 — 중복 meta 제거, 한국어화, lazy loading, fetchpriority

### Changed

- `show()` 재무제표 후처리: all-null 행 제거, 중복 계정명 병합, CF 잘못된 당기순이익 제거
- `show()` subtopic 내부 topic명 한글화 + 기간 없는 DF None 반환
- sections table subtopic→항목 통일
- Roadmap 업데이트: EDGAR Company UX alignment / EDGAR financial data integration 완료 체크

### Fixed

- `_reportFrame` RuntimeError 방어 — report 미보유 종목 다운로드 실패 시 None 반환
- 272개 전수조사 — report 방어 로직 + 재무제표 중복행 병합
- sections 파싱 실패 fallback 경로 누락 수정
- 테스트 수정 — sections blockType 컬럼 추가에 맞춰 period 필터 갱신

## [0.4.7] - 2026-03-14

### Added

**Profile Pipeline 구축 (Phase 1~4)**
- `c.diff()` 3-mode API: 전체 요약 / topic 이력(delta, deltaRate) / 줄 단위 인터리빙 diff
- `sections/diff.py` 모듈: hash 기반 기간간 텍스트 변화 감지
- `common/finance/inflection.py` 모듈: 재무 시계열 변곡점 탐지
- report `toWide()`: 5개 pivot Result에 metric × year wide DataFrame 반환
- `sections/_common.py`: `sortPeriods()` 기간 정렬 유틸리티

### Changed

**데이터 품질 전수조사 및 안정화**
- `show()` 3-layer 디스패치: finance stmt → report toWide → docs 세로 unpivot
- `_applyPeriodFilter()` 수정: period 필터 시 `분류`/`항목`/`metric` 등 label 컬럼 보존
- `_reportFrame()` 메타 컬럼 6개(`stlm_dt`, `apiType`, `stockCode`, `year`, `quarter`, `quarterNum`) 자동 제거
- `index` lazy 구축: 30초 → 1.77초, I~XII장 문서 순서 정렬
- sections pipeline 장 제목 중복 제거 (71 → 54 topic)
- 기간 정렬 오름차순 통일 (과거 → 최신)
- `sectionMappings.json` 30건 추가 (커버리지 94.6% → 98.9%)
- SCE 계정명 한글화 (CAUSE_LABELS / DETAIL_LABELS)
- 6종목 485 show() 전수검증 에러 0, BS 항등식 6종목 OK

**EDGAR 엔진 확장**
- EDGAR CIS/SCE 실험 (059), standardAccounts 확장
- EDGAR Company lazy profile 최적화 (060)

### Fixed

- `_applyPeriodFilter` period 필터 시 non-period label 컬럼 누락 버그
- `index` period range 표시 역순(`2025..1999Q2`) → 오름차순(`1999Q2..2025`)
- `test_regression_fixture` threshold 조정 (fixture parquet 3년 데이터 대응)
- `test_sections_pipeline`, `test_sections_runtime` 오름차순 정렬 반영

## [0.4.6] - 2026-03-13

### Fixed

**EDGAR docs foundation release test 정합성 복구**
- `tests/test_edgarDocs_foundation.py` 가 기대하는 EDGAR 배치 다운로드 helper를 `experiments/057_edgarSectionMap/002_downloadFirst2000.py` 에 다시 반영
- `v0.4.5` publish workflow 를 막던 release test mismatch를 해소

## [0.4.5] - 2026-03-13

### Changed

**Company public surface 정리**
- 공개 진입 예제를 `import dartlab; c = dartlab.Company("005930")` 로 통일
- `Company.index`, `Company.show(topic)`, `Company.trace(topic)` 를 현재 메인 흐름으로 문서/예제/CLI에 반영
- `Company.profile` 은 향후 terminal/notebook 문서형 보고서 뷰 로드맵으로만 명시

**문서 / notebook / marimo 동기화**
- README, GitHub Pages 문서, startMarimo, 연계 notebook 예제를 현재 API 기준으로 정리
- docs 없는 회사에서 `현재 사업보고서 부재` 안내가 나온다는 점을 예제와 설명에 추가
- compare 개선 예정, EDGAR Company UX 정렬 예정 메시지를 문서에 명시

**CLI / server / UI surface 정리**
- `dartlab profile` 기본 출력을 `company.index` 로 변경
- `dartlab profile --show TOPIC`, `--trace TOPIC` 지원 추가
- AI UI용 `/api/company/{code}/index`, `/show/{topic}`, `/trace/{topic}` endpoint와 client helper 추가

### Fixed

**생성 문서와 버전 메타데이터 갱신**
- `scripts/generateSpec.py` 를 현재 Company surface 기준으로 갱신
- `API_SPEC.md`, `llms.txt`, skill reference 생성물 재생성
- 패키지/landing 버전을 `0.4.5` 로 갱신

## [0.4.4] - 2026-03-12

### Changed

**docs/sections production 마감**
- `Company.sections` 가 raw markdown를 보존한 canonical wide view로 동작하면서 appendix/detail row는 기본 core view에서 숨김
- `Company.retrievalBlocks`, `Company.contextSlices` 가 `sourceTopic`, `cellKey`, `semanticTopic`, `detailTopic` 을 함께 반환해 원문 block을 역추적 가능하게 정리
- appendix/detail 명세서(`재고자산명세서`, `감가상각비등명세서`, `제조원가명세서`, `법인세등명세서`, 감사 보수 등)를 detail semantic layer로 분리
- broad raw residual 일부를 exact mapping으로 흡수해 package 기본 수평화 품질을 마감
- 금융업/지적재산권/수주/계약 상세표를 detail taxonomy로 흡수해 추가 docs 종목군에서도 core raw residual이 사라지도록 보강

**Company 레이어 정상화**
- `engines.dart.company`, `engines.edgar.company` 에 시장별 Company 본체를 배치하고 루트 `dartlab.company` 는 facade만 담당하도록 재구성
- `engines.dart.compare`, `engines.edgar.compare` 도 루트 compare 의존 없이 독립 import 가능하도록 정리
- `engines` 하위에서 루트 `dartlab.company`, `dartlab.compare`, `dartlab.usCompany` 를 직접 import 하지 않도록 레이어 방향을 바로잡음

### Fixed

**패키지 메타데이터와 문서 정리**
- README에 `sections/retrievalBlocks/contextSlices` 사용 흐름과 런타임 무저장 원칙을 명시
- `pyproject.toml` classifier 를 `Production/Stable` 로 상향

**CLI 상용화 준비**
- 단일 `cli.py` 를 `dartlab/cli/` 패키지로 분리하고 명령/서비스/파서 계층을 고정
- `dartlab` 엔트리포인트를 `dartlab.cli.main:main` 으로 전환
- CLI 종료 코드, 공통 예외 처리, deprecated alias 정책, `--version` 지원을 표준화
- subprocess 기반 CLI E2E smoke test와 packaging contract test를 추가

## [0.4.3] - 2026-03-12

### Fixed

**EDGAR sections 패키지 아티팩트 포함**
- `canonicalRows.parquet`, `formTopicDrafts.json`, `mappingCoverage.latest.json` 를 패키지 리소스로 포함
- EDGAR sections artifact loader가 실험 폴더가 아닌 설치 패키지에서도 정상 동작하도록 수정

## [0.4.2] - 2026-03-12

### Fixed

**서버 테스트 런타임 의존성 보강**
- `dartlab[ai]` 에 `httpx` 추가
- `starlette.testclient` 가 `httpx` 미설치로 실패하던 문제 해결

## [0.4.1] - 2026-03-12

### Fixed

**릴리즈/CI 테스트 의존성 정리**
- `Publish to PyPI`와 `CI` workflow가 서버 테스트에 필요한 `ai` optional dependency를 설치하도록 수정
- `tests/test_server.py` 수집 단계에서 `starlette` 미설치로 실패하던 문제 해결
- 실험용 `experiments/**/*.parquet` 및 `experiments/**/output/` 산출물이 Git에 섞이지 않도록 제외 규칙 보강

## [0.4.0] - 2026-03-11

### Added

**docs/sections 학습형 수평화 runtime**
- `Company.sections`가 learned section rules 기반으로 coarse report를 fine topic 축에 즉시 backfill
- `projectionRules.chapterII.json` 패키지 포함
- `sectionProfileTable.parquet` 패키지 포함 + runtime artifact loader 추가

### Changed

**Company 데이터 소스 계층 개선 (Breaking Change)**
- `c.BS`, `c.IS`, `c.CF` — docs HTML 파싱 → **finance XBRL 정규화** 기반으로 변경
  - snakeId 통일로 회사간 비교 가능, 단위: 원 (기존 docs는 백만원)
  - finance 데이터 없으면 docs fallback 유지
- `c.IS` — docs가 반환하던 CIS(포괄손익계산서)에서 **finance IS(손익계산서)**로 변경
  - 매출액, 영업이익 등 핵심 계정이 누락되던 문제 해결
- `c.dividend`, `c.employee`, `c.majorHolder`, `c.executive`, `c.audit` — docs → **report API** 우선으로 변경
  - DART API 정형 데이터 사용 (HTML 파싱보다 정확), report 없으면 docs fallback
- `sections` pipeline — 단순 leaf title 병합에서 learned-rule 기반 horizontalization으로 변경
  - 번호/기호 prefix 제거 강화
  - legacy section title exact mapping 흡수
  - chapter II coarse topic(`매출에관한사항`, `연구개발활동`, `경영상의주요계약등`, `파생상품등에관한사항`)을 canonical fine topic으로 projection

**registry BS/IS/CF 메타데이터 업데이트**
- `requires`: "docs" → "finance"
- `unit`: "원" 추가
- `description`: finance XBRL 정규화 기반 명시

### Added

**report 엔진 5개→22개 apiType 확장**
- `_ReportAccessor`에 `__getattr__` 추가 — 17개 비피벗 apiType 자동 접근
  - `c.report.treasuryStock`, `c.report.capitalChange`, `c.report.minorityHolder` 등
- `c.report.apiTypes` — 사용 가능한 22개 apiType 목록
- `c.report.labels` — apiType → 한글명 매핑

**Company property 추가**
- `c.tangibleAsset` — 유형자산 변동표 DataFrame (docs)
- `c.costByNature` — 비용 성격별 분류 시계열 DataFrame (docs)

**엔진별 SPEC.md 문서**
- `engines/dart/finance/SPEC.md` — 매핑 파이프라인, 5개 피벗 함수, snakeId 테이블, AccountMapper 상세
- `engines/dart/report/SPEC.md` — 22개 apiType 컬럼 명세, 4단계 추출 파이프라인, 6개 Result 타입
- `engines/dart/docs/SPEC.md` — 40개 모듈(finance 36 + disclosure 4) 전체 함수 시그니처, Result 패턴

**Company 소스 역할 배정 문서**
- `engines/dart/ROLE_ASSIGNMENT.md` — property별 데이터 소스 우선순위, 구현 계획

**테스트 추가**
- `test_bsIdentity.py` — BS 항등식 검증 (자산=부채+자본)
- `test_mappingBenchmark.py` — 매핑률 벤치마크 (97%+ 기준)
- `test_regressionFinance.py` — finance 출력 회귀 테스트
- `test_server.py` — 서버 smoke test

**CI/인프라**
- pytest-cov 설정 추가 (coverage run/report)
- API 안정성 Tier 문서 (`docs/stability.md`)

**블로그**
- 007: EDGAR 통합 플레이북
- 008: 사업의 내용으로 기업 판단하기
- 블로그별 SVG 다이어그램 추가

[0.4.4]: https://github.com/eddmpython/dartlab/compare/v0.4.3...v0.4.4
[0.4.5]: https://github.com/eddmpython/dartlab/compare/v0.4.4...v0.4.5
[0.4.3]: https://github.com/eddmpython/dartlab/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/eddmpython/dartlab/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/eddmpython/dartlab/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/eddmpython/dartlab/compare/v0.3.2...v0.4.0

## [0.3.2] - 2026-03-11

### Added

**Data Explorer 전면 리디자인**
- 모달 → 전체화면 레이아웃으로 변경 (fixed inset-0)
- 한글/영문 계정명 토글 — L1 labelMap()의 5,790개 한글 라벨 활용
- 계정 계층 구조 인덴트 (대/중/소 분류, levelMap() 기반)
- 재무 시계열 테이블: 첫 번째 열 고정(sticky), 가로 스크롤
- 원 단위 자동 포맷 (조/억/만), 음수 빨간색 표시
- 회사 아바타 (첫 글자) + 단위 배지 표시

**서버 재무 메타데이터 API**
- `_build_finance_meta()` — finance 시계열 모듈의 한글 라벨, 정렬 순서, 레벨 정보를 preview API에 포함
- preview 응답에 `unit` 필드 추가 (DataEntry.unit 기반)

**6개 LLM Provider 지원**
- ChatGPT (OAuth), Ollama (로컬), OpenAI API, Anthropic API, Codex CLI, Claude Code CLI

**README Architecture 섹션**
- 3계층 엔진 아키텍처(L1/L2/L3) 시각화
- 기여자를 위한 프로젝트 구조 설명

### Changed

**README 전면 보강**
- AI Analysis 섹션: Ollama 전용 → 6개 provider 테이블로 확장
- Roadmap: Cloud LLM, Data Explorer, Excel export 완료 표시, EDGAR 추가

[0.3.2]: https://github.com/eddmpython/dartlab/compare/v0.3.1...v0.3.2

## [0.3.1] - 2026-03-10

### Added

**재무비율 시계열 피벗 (engines/common/finance)**
- `toSeriesDict()` — 연도별 재무비율 시계열을 IS/BS/CF와 동일한 dict 구조로 변환
- `RATIO_CATEGORIES` — 6카테고리(수익성, 안정성, 성장성, 효율성, 현금흐름, 절대값) 그룹핑 상수
- `calcRatioSeries`, `toSeriesDict` re-export 추가 (dart/finance, common/finance)

**Company.ratioSeries property**
- `c.ratioSeries` — 연도별 재무비율 시계열 (`{"RATIO": {snakeId: [v1, v2, ...]}}`, years) 반환
- IS/BS/CF/SCE와 동일한 패턴으로 재무비율 접근 가능

**Excel 재무비율 시트 개선**
- 단일시점 세로나열 → 연도별 피벗 테이블로 전면 재작성
- 카테고리별 섹션 헤더 (수익성, 안정성, 성장성, 효율성, 현금흐름, 절대값) + 색상 구분
- 35개 비율 한글 라벨 매핑 (`_RATIO_LABELS`)
- freeze panes (좌측 지표명 고정)

**SCE(자본변동표) spec.py 반영**
- `dart/finance/spec.py` statements 목록에 SCE 추가
- normalization 설명에 SCE 매트릭스 피벗 방식 명시

### Fixed

**서버 Company.search 버그 수정**
- `Company`는 팩토리 함수이므로 `.search()` staticmethod가 존재하지 않던 문제
- `server/resolve.py`, `server/__init__.py`에서 DART engine company search 경로로 수정
- `Company()` 팩토리 함수 반환 타입 힌트를 facade 구조 기준으로 정리

[0.3.1]: https://github.com/eddmpython/dartlab/compare/v0.3.0...v0.3.1

## [0.3.0] - 2026-03-09

### Changed

**엔진 레이어 아키텍처 리팩토링 (Breaking Change)**
- `engines/` 디렉토리를 L1(데이터소스)/L2(분석)/L3(AI) 3계층으로 재편
- `engines/docsParser/` → `engines/dart/docs/`
- `engines/financeEngine/` → `engines/dart/finance/`
- `engines/reportEngine/` → `engines/dart/report/`
- `engines/sectorEngine/` → `engines/sector/`
- `engines/insightEngine/` → `engines/insight/` (rank 분리)
- `engines/llmAnalyzer/` → `engines/ai/`
- 모든 import 경로가 변경됨 (하위 호환 alias 미제공)

### Added

**섹터 분류 엔진 (engines/sector)**
- WICS 11섹터 분류 (수동 오버라이드 → 키워드 → KSIC 3단계)
- 섹터별 밸류에이션 파라미터 (할인율, PER/PBR/EV-EBITDA 멀티플)

**인사이트 등급 확장 (engines/insight)**
- 섹터 감지 (금융/비금융 자동 판별) + 섹터 벤치마크 기반 상대평가
- 7영역 등급에 섹터 상대 등급 반영

**시장 규모 순위 (engines/rank)**
- 매출/자산/성장률 3축 전체 순위 + 섹터 내 순위
- JSON 캐시 기반 조회 (빌드 ~2분, 이후 즉시)

**문서 전면 업데이트**
- API_SPEC.md에 report/sector/insight/rank 스펙 추가
- README Roadmap에 새 엔진 반영
- GitHub Pages docs 핵심 기능 목록 갱신

## [0.2.5] - 2026-03-09

### Changed

**`dartlab[ui]` → `dartlab[ai]` 리네이밍**
- AI 기업분석 optional dependency를 `[ai]`로 변경 (`dartlab ai` CLI 명령과 일치)
- `dartlab[ui]`는 하위호환 alias로 유지 (내부적으로 `[ai]` 참조)
- `dartlab ui` CLI 실행 시 `dartlab ai`로 변경 안내

**uv 통일**
- 전체 문서(README, README_KR, docs, landing)에서 pip 참조 제거, uv 설치 방법으로 통일
- 모든 provider ImportError 메시지를 `uv add dartlab[...]` 형태로 변경

### Added

**insightEngine — 종합 인사이트 분석 엔진**
- 7영역(실적, 수익성, 재무건전성, 현금흐름, 성장성, 지배구조, 밸류에이션) 등급 분석
- 이상치 탐지 (z-score 기반) + 요약 텍스트 자동 생성
- Company 클래스에 `insights` property 통합

**AI 웹 인터페이스 UX 개선**
- 로딩 단계 표시 (생각 중 → 데이터 로딩 → 분석 → 응답 생성)
- 응답 완료 후 경과시간 배지 표시
- 대화 삭제 확인 팝업
- context 모달 헤더 2행 구조로 개선 (탭 버튼 세로 텍스트 버그 수정)

**Ollama 최적화**
- 서버 시작 시 모델 preload (cold start 제거)
- 모델 추천 가이드 API (`/api/models/ollama` 응답에 recommendations 포함)
- 질문 유형 기반 컨텍스트 필터링 (건전성/수익성/성장성/배당/현금 별 관련 계정만 전송)
- Guided Generation JSON 스키마 (Ollama 구조화 출력용)

## [0.2.4] - 2026-03-09

### Added

**LLM 분석 품질 개선**
- Compact 프롬프트에 Few-Shot 예시 5종, 교차검증 규칙, 토픽 가이드 추가
- compact 모드 컨텍스트 압축 (연도 4년 제한, 비율 핵심 7개, 리포트 축약) — 전체 52.9% 압축
- 복합 질문 다중 분류 (`_classify_question_multi`) — "수익성과 배당" 같은 질문 지원
- Self-Critique 인프라 (2-pass 검증 구조, UI 옵션 연동 예정)
- 응답 메타데이터 추출 (등급, 시그널, 테이블 수) → SSE done 이벤트 포함

**reportEngine — 정기보고서 정규화 엔진**
- 배당, 임원, 직원, 감사, 자기주식 데이터 추출·피벗
- Company 클래스에 `report` property 통합
- agent tools_registry에 report 관련 도구 함수 추가
- `dartlab.dataDir` property 추가 (데이터 디렉토리 설정)

[0.2.5]: https://github.com/eddmpython/dartlab/compare/v0.2.4...v0.2.5
[0.2.4]: https://github.com/eddmpython/dartlab/compare/v0.2.0...v0.2.4

## [0.2.0] - 2026-03-08

엔진 분류 리팩토링 — `finance/`와 `disclosure/`를 `engines/docsParser/` 아래로 이동. 향후 정량 데이터 엔진, 전체 종목 비교 엔진 등 다른 엔진을 추가할 수 있는 구조로 전환.

### Changed

**엔진 구조 리팩토링**
- `finance/`(36개 모듈)과 `disclosure/`(4개 모듈)를 `engines/docsParser/` 아래로 이동
- `notes.py`도 `engines/docsParser/notes.py`로 이동 (docsParser 엔진의 래퍼)
- 모든 import 경로를 `dartlab.engines.docsParser.{finance,disclosure}.XXX`로 변경
- `company.py` `_MODULE_REGISTRY` 경로 문자열 일괄 변경
- 사용자 API(`Company.BS`, `Company.dividend` 등)는 변경 없음

**GitHub Pages 레이아웃**
- 블로그 컨텐츠 중앙 배치 (max-width 720px), ToC 우측 유지 (모바일 숨김)
- 독스/블로그 섹션 간 간격 확대 (h2 margin-top 3.5rem, h3 2.5rem)
- 독스/블로그 하단에 랜딩 Footer 추가 (Buy Me a Coffee 포함)
- 데이터 릴리즈 태그 `data-v1` → `data-docs` 변경 반영

**노트북 전면 재작성**
- `print(df)` 제거, Jupyter/Colab rich 렌더링 활용 (셀 마지막 줄에 변수만 배치)
- 한 셀에 하나의 DataFrame만 표시
- pip install 셀에 Colab 의존성 경고 안내 추가

### Added

- OG 이미지 적용 (`og-image.png`, `summary_large_image`)
- `getting-started/quickstart.ipynb` 노트북 생성
- 블로그 섹션 + 첫 번째 포스트 "DART의 모든 것"
- `CHANGELOG.md` 추가

[0.2.0]: https://github.com/eddmpython/dartlab/compare/v0.1.12...v0.2.0

## [0.1.12] - 2026-03-08

파싱 품질 점검 릴리즈.

### Fixed

- 파싱 모듈 5건 수정 — 출력 품질 점검 결과 반영

[0.1.12]: https://github.com/eddmpython/dartlab/compare/v0.1.11...v0.1.12

## [0.1.11] - 2026-03-08

Company 클래스 전면 재설계 — yfinance 스타일 property 접근, Notes 통합, rich 터미널 출력.

### Changed

**Company 재설계**
- 40개 모듈을 property로 직접 접근 (`c.BS`, `c.dividend`, `c.audit`)
- `_MODULE_REGISTRY` 기반 lazy loading + caching
- `get(name)` 메서드로 전체 Result 객체 반환 (복수 DataFrame 접근)
- `all()` 메서드로 전체 데이터 dict + alive_bar progress bar
- `guide()` 메서드로 사용 가능한 property 목록 rich 출력
- verbose 모드 기본 활성화

**Notes 통합**
- `c.notes.inventory` / `c.notes["재고자산"]` 이중 접근
- K-IFRS 주석 12개 항목 통합 래퍼

**브랜딩**
- red/coral 색상 전환 (#ea4647)
- 아바타 마스코트 적용 (6종 변형)
- `analyze` → `fsSummary` 리네이밍

### Added

- 전체 문서를 property API 기준으로 전면 갱신 (quickstart, API overview, tutorials)

[0.1.11]: https://github.com/eddmpython/dartlab/compare/v0.1.10...v0.1.11

## [0.1.10] - 2026-03-08

finance 모듈 대량 추가 + 랜딩 페이지 확장.

### Added

**finance 모듈 8개 추가**
- `articlesOfIncorporation`, `auditSystem`, `companyHistory`, `companyOverviewDetail`
- `investmentInOther`, `otherFinance`, `shareholderMeeting`

**랜딩 페이지**
- 랜딩 전체 영어화
- Workflow, ModuleCatalog, UseCases 섹션 신규 추가
- 튜토리얼 4종 + Colab 노트북 추가

[0.1.10]: https://github.com/eddmpython/dartlab/compare/v0.1.9...v0.1.10

## [0.1.9] - 2026-03-08

finance 모듈 대량 추가 릴리즈 (15개 모듈 추가).

### Added

**finance 모듈 15개 추가**
- v0.1.8: `audit`, `boardOfDirectors`, `bond`, `capitalChange`, `contingentLiability`, `costByNature`, `internalControl`, `relatedPartyTx`, `sanction`, `shareCapital`
- v0.1.9: `affiliateGroup`, `fundraising`, `salesOrder`, `productService`, `riskDerivative`

### Fixed

- mdsvex 빌드 오류 수정 (중괄호 표현식을 백틱으로 감싸기)

[0.1.9]: https://github.com/eddmpython/dartlab/compare/v0.1.6...v0.1.9

## [0.1.6] - 2026-03-07

notesDetail 확장 릴리즈.

### Changed

- `notesDetail` 키워드 23개로 확장
- `parseNotesTable` Pattern D 추가 (4-패턴 파서)
- `tableDf` 시계열 정규화

[0.1.6]: https://github.com/eddmpython/dartlab/compare/v0.1.5...v0.1.6

## [0.1.5] - 2026-03-07

K-IFRS 주석 파싱 모듈 추가.

### Added

- `notesDetail` 모듈 — K-IFRS 주석 상세 파싱
- `parseNotesTable` 범용 파서
- 테스트 48개

[0.1.5]: https://github.com/eddmpython/dartlab/compare/v0.1.4...v0.1.5

## [0.1.4] - 2026-03-07

재무제표 fallback + 자동화.

### Changed

- `statements` 연결/별도 재무제표 자동 fallback

### Added

- `tangibleAsset` 모듈 추가
- KindList auto-update GitHub Actions workflow (daily cron)

[0.1.4]: https://github.com/eddmpython/dartlab/compare/v0.1.3...v0.1.4

## [0.1.3] - 2026-03-07

패키지 구조 정립 + 랜딩 페이지 구축.

### Changed

- `finance/` / `disclosure/` 패키지 분리 (기존 단일 모듈에서 분리)

### Added

- KRX KIND 상장기업 목록 매퍼 (`getKindList`, `codeToName`, `nameToCode`, `searchName`)
- Company 이름 검색 기능
- `companyOverview` 공시 서술형 모듈
- `business` 공시 서술형 모듈
- SvelteKit 랜딩 페이지 구축 (shadcn-svelte)
- SEO 최적화

[0.1.3]: https://github.com/eddmpython/dartlab/compare/v0.1.2...v0.1.3

## [0.1.2] - 2026-03-07

문서 시스템 구축.

### Added

- SvelteKit docs 통합 (mdsvex + Shiki)
- 브랜딩 에셋 (아바타, favicon)

[0.1.2]: https://github.com/eddmpython/dartlab/compare/v0.1.1...v0.1.2

## [0.1.1] - 2026-03-07

초기 모듈 확장.

### Added

- `affiliate` 모듈 추가
- stockCode API 전환
- 랜딩 페이지, docs 기본 구축, quarterly 지원

[0.1.1]: https://github.com/eddmpython/dartlab/compare/v0.1.0...v0.1.1

## [0.1.0] - 2026-03-06

DartLab 최초 공개 릴리즈 — DART 전자공시 문서를 파싱하는 Python 라이브러리.

### Added

**핵심 기능**
- `Company` 클래스 — 종목코드 기반 데이터 접근
- `loadData()` — GitHub Releases에서 Parquet 자동 다운로드
- `selectReport()` — 보고서 선택 (사업보고서 우선)
- `extractTables()` — HTML 테이블 파싱 + Polars DataFrame 변환

**finance 모듈 (초기 5개)**
- `summary` — 요약재무정보
- `statements` — 재무제표 본문 (연결/별도)
- `segment` — 사업부문별 실적
- `dividend` — 배당 데이터
- `employee` — 직원 현황

**disclosure 모듈 (초기 2개)**
- `mdna` — 경영진의 분석 및 논의
- `rawMaterial` — 원재료 현황

**인프라**
- Polars 기반 DataFrame 처리
- GitHub Actions CI + PyPI trusted publishing
- 260+ 상장사 Parquet 데이터 (GitHub Releases)
- uv 패키지 매니저 지원

[0.1.0]: https://github.com/eddmpython/dartlab/releases/tag/v0.1.0
