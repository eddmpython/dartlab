# Phase 4 완전 설계: 퍼블릭 scan뷰가 screens/*.json 을 SSOT 로 렌더

> 상태: **설계 확정, 착수 대기(운영자 명시 UI 트리거 "지어" 전 미착수)**. 부모 PRD [[00-prd]].
> 근거: 프론트 표면 전수 read-only 조사(2026-07-06, 파일:라인 그라운딩). 백엔드 Phase 1~3 완성.
> 규율: 화면/배선 작업 = 눈검수 필수 + auto-push 금지 (CLAUDE.md + [[feedback_ui_rules]]).

## 배경 / 정공법 한 줄

백엔드 `src/dartlab/scan/screens/*.json` 은 선언형 스크린 SSOT 로 완성됐으나 프론트가 전혀 소비하지 않는다(grep 0). 퍼블릭 `/scan` Scan Studio 는 스크리너를 **TS/DuckDB-SQL 로 3~4중 재구현**한 별세계다. Phase 4 = 그 재구현들을 **screens/*.json 을 해석하는 단일 프론트 엔진으로 붕괴**시켜, python·왓처·프론트 3자가 같은 JSON 을 소비하게 한다. 새 bake 최소화(런타임-SSOT), 정적 프론트라 서버 executor 호출은 불가. 시맨틱을 프론트로 포팅하되 spec 은 JSON 이 소유.

## 조사 실측 (아키텍처 제약, 파일:라인)

- 퍼블릭 scan 화면 = `landing/src/routes/scan/+page.svelte` (~1280줄), `+page.ts:3-5` `prerender=true; ssr=false` = **정적, 서버 없음**. 데이터 = 클라 DuckDB-WASM 이 HF parquet 직독(`ui/packages/surfaces/src/scan/duckSql.ts:57,237,311,669`) + `scanRuntime.worker.ts` 가 `map/*.json` static→HF fetch.
- scan UI 공유 컴포넌트 = `ui/packages/surfaces/src/scan/*` (Grid·ScreenBuilder·PresetModal·metrics·presets 등 40여 파일).
- **3~4중 재구현 실증**: `scan/presets.ts:33-169`(7 프리셋) · `ScreenBuilder.svelte:95-132`(setPreset 5) · `evalCond` x2(`ScreenBuilder.svelte:177-197`·`scan/+page.svelte:257-287`) · `metrics.ts:54-608`(~50 지표) · `financeLiteRuntime.ts:273-300`(JS 비율) · `duckSql.ts:308-374`(SQL 비율).
- 데이터 코어 SSOT = `ui/packages/runtime/src/data/fetch/request.ts:82 createDataCore` + `origins/registry.ts:90-143 ORIGINS`. scan 은 이 코어를 우회해 HF 직독(레지스트리 밖 `dartlabData.loadJson`/`HF_RESOLVE`).
- **HTTP executor 엔드포인트 없음**: `infra/workers/*` scan grep 0. 로컬 `scanSource.ts:11-13` = `notWiredYet`(throw). 백엔드 executeScreenSpec 은 Python 전용, 정적 프론트가 못 부름.
- **JSON→프론트 선례 = 빌드타임 코드젠**: `landing/_scripts/buildFinanceAccountOrder.py` 가 accountMappings.json → `viewer/lib/finance/accountOrder.ts` 코드젠 + `--check` 드리프트 가드. 백엔드도 screens/json 을 "accountMappings 급"(`scan/screen/__init__.py:36`)으로 규정.
- **스키마 격차**: 프론트 `{metric:"roe", op, value, value2}` (로컬 지표명) vs json `{field:"finance.ratio.roe", op, value}` + `@define`(min/cagr/mean/percentile years·by) + `@ref` + `percentile by industry`. 프론트 조건 모델엔 define·@ref·업종백분위 개념이 전혀 없음.

## 1. 목표 / 범위 (2 서브페이즈)

- **Phase 4a (엔진 붕괴 + JSON SSOT 유입, 비주얼 무변경)**: (1) `screens/*.json` → TS 코드젠(`landing/_scripts/buildScreens.py`, accountOrder 선례·`--check` 드리프트 가드) 로 `ui/packages/surfaces/src/scan/screensCatalog.ts` 생성. (2) 프론트 조건 모델을 json spec shape 로 정규화(`{field, op, value}` + `define` + `@ref`). (3) `evalCond` x2 + `presets.ts` + `ScreenBuilder.setPreset` 을 **단일 `specEngine.ts`** 로 통합(json spec 해석기, define 산술·시계열·상대 포팅). (4) 필드 네이밍 브리지(`roe`↔`finance.ratio.roe`) = `metrics.ts` 에 canonical key 매핑 추가. **UI 레이아웃·색·그리드 불변**, 내부 엔진만 교체.
- **Phase 4b (screens 노출 + 신 능력 UI)**: 저장 스크린(financialStabilityDrawdown·resilientCompounders) 을 프리셋 목록에 노출 + define/시계열/상대 조건을 ScreenBuilder UI 에서 작성 가능하게(percentile by industry·cagr years 등 입력 위젯). 왓처 `notify:true` 구독 배지.

## 2. 영향 파일 / 함수

- 신규 `landing/_scripts/buildScreens.py`: screens/*.json → `screensCatalog.ts` 코드젠 + `--check`. `noScriptsDir` 회피(도메인 폴더 `landing/_scripts/`).
- 신규 `ui/packages/surfaces/src/scan/specEngine.ts`: `evalSpec(nodes, spec)` = where/any/select/sort + `computeDefine`(add/sub/mul/div·min/max/mean/yoy/cagr/slope·percentile/zscore by industry). DuckDB 우선(집계·percentile 은 SQL), 스칼라 술어는 JS. executeScreenSpec 의 프론트 미러(파서 재구현 아님, 시맨틱 1:1, 테스트로 parity 강제).
- 개조 `ui/packages/surfaces/src/scan/presets.ts`: 하드코딩 7 프리셋 제거 → `screensCatalog.ts` re-export. `SSOT` 주석(:11) 실현.
- 개조 `ui/packages/surfaces/src/scan/ScreenBuilder.svelte`: `setPreset`(:95-132)·`evalCond`(:177-197) 제거 → `specEngine` 위임. define/상대 입력 위젯 추가(4b).
- 개조 `landing/src/routes/scan/+page.svelte`: 인라인 `evalCond`(:257-287)·`applyPreset`(:365-374) 제거 → `specEngine` 위임.
- 개조 `metrics.ts`: `METRICS_DEF` 에 `canonicalField`(`finance.ratio.roe`) 매핑 컬럼 추가(격차 브리지).
- 테스트 신규 `ui/packages/surfaces/src/scan/specEngine.test.ts`(vitest): 백엔드 `test_screen_define.py` 케이스 미러(산술·시계열·상대·회귀) + **parity 골든**(동일 spec → 백엔드 executeScreenSpec 결과 vs 프론트 specEngine 결과 종목셋 일치, 실 HF finance-lite 소표본).
- 드리프트 가드: `buildScreens.py --check` 를 CI 린트 게이트 등재(`tests/audit/` 또는 landing lint).

## 3. 아키텍처 결정 (핵심 3)

- **JSON 유입 = 빌드타임 코드젠**(accountOrder 선례). 런타임 HF fetch 대신 코드젠 채택 이유: screens 는 accountMappings 급 저빈도 config(운영자 수동 저작), 정적 프리렌더라 번들 인라인이 자연스럽고 `--check` 로 드리프트 봉쇄. 새 HF 산출물 bake 0(런타임-SSOT 위반 아님, TS 는 소스 코드젠).
- **executor 시맨틱은 프론트 포팅이 불가피**(정적 프론트 + Python executor = 서버 호출 불가). 재구현 아니라 **1:1 미러 + parity 테스트 강제**로 조용한 오답 차단. percentile/집계/시계열은 DuckDB-SQL(이미 duckSql.ts 패턴), 스칼라 술어는 JS.
- **네이밍 정규화 = json field key 가 정본**. 프론트 `roe` 는 `finance.ratio.roe` 의 별칭으로 강등(metrics.ts 매핑). 프리셋 ID 도 백엔드(value/quality 등) 로 통일하되 기존 URL 딥링크 호환 alias 유지.

## 4. 테스트 / 게이트 (눈검수 필수)

- vitest specEngine 유닛 + **parity 골든**(프론트=백엔드 종목셋 일치, 신규 능력의 조용한 발산 차단).
- `buildScreens.py --check` CI 드리프트 게이트.
- landing `npm run build` + 실 서빙 경로(:8400/프리뷰) 렌더 확인([[feedback_local_app_served_by_backend_build]]).
- **★푸시 전 스크린샷 전수 눈검수**: `/scan` 그리드·프리셋·디테일·필터빌더 시각 회귀 정성 검수(정량 PASS 가 디자인 못 봄, [[feedback_ui_rules]]). Playwright 정량 + 눈검수 병행.
- **auto-push 금지**: 운영자 "올려/발간해" 후에만 push.

## 5. 롤백 / 리스크 + 이중평가

- 롤백: specEngine 도입은 additive(기존 evalCond 병존 후 스위치), 프리셋 코드젠은 re-export 라 revert = 파일 삭제 + 원본 복원. 비주얼 무변경(4a)이라 시각 회귀면 즉시 되돌림.
- 리스크: (a) 프론트 DuckDB 가 percentile-by-industry 를 SQL window 로 정확 재현해야(백엔드 polars over(grp) 미러) → parity 골든이 잡음. (b) finance-lite parquet 이 백엔드 finance.parquet 의 부분집합이라 종목셋 차이 가능 → 유니버스 명시 + 커버리지 배지. (c) 코드젠 드리프트 → `--check` 게이트. (d) UI 조건빌더 복잡도 증가(define·상대) → 4b 로 분리, 4a 는 노출만.
- 개발자 평가: 재구현 붕괴 = 순부채 감소(3~4→1), parity 테스트로 정합 강제, 코드젠은 검증된 accountOrder 패턴. additive 스위치라 회귀 0 경로 존재.
- PM 평가: "퍼블릭 scan뷰도 맞춘다" 비전 종결. screens/*.json 3자 소비 실현 = 시그니처 완성. 단 화면 회귀 위험 실재 → 눈검수 게이트 + 단계 분리(4a 무비주얼 우선)로 통제. **운영자 명시 트리거 + 눈검수 없이는 미착수.**

## 착수 조건 (게이트)

운영자 명시 UI 트리거("지어"·"만들어"·"scan뷰 붙여") 수신 시 4a 부터 무중단 구현. 그 전까지 본 문서는 설계 대기 상태이며 프론트 코드 0 변경.
