# 닫은 기획에서 옮긴 남은 일 (2026-11-27)

2026-11-27 기획 정리에서 mainPlan 폴더 17개를 지웠다. 그 가운데 코드, 공개 데이터, Skill OS에 실제로 남은 일만 여기로 옮긴다.
아직 코드가 없는 새 기능 설계는 옮기지 않았다. 지운 문서는 정리 직전 커밋 `5506222362107c72d1b423cfb8db5411f6f9712d`에 있다.
꺼내는 법: `git show 550622236:mainPlan/<폴더>/<파일>`. 아래에서 번호로만 적은 결함과 결정 대기 항목의 원문도 여기서 읽는다.

이 목록은 v1.0 점검(01 원장)의 남은 부채와 같은 차례로 처리한다. 운영자 결정이 필요한 항목은 그 이유를 적었다.
시뮬레이터 코드는 2026-08-04 결정대로 남겨 둔 `scenario-simulator` 기획 소속이라 여기로 옮기지 않았다.

## 공개 데이터와 저작권

1. **네이버 출처 밸류에이션의 공개 업로드** (옛 scan-screener-os P0).
   - `.github/workflows/valuationSnapshot.yml`이 매일(cron `0 23 * * *`) `.github/scripts/sync/prebuildValuation.py`를 돌려 공개 데이터셋 `eddmpython/dartlab-data`의 `dart/scan/valuation.parquet`를 덮어쓴다. 2026-11-24~26 예약 실행이 모두 성공했다.
   - 값의 출처는 `src/dartlab/scan/financial/valuation.py`의 `dartlab.gather.domains.naver.fetchPrice`이고 per, pbr, dividendYield를 그대로 싣는다.
   - 자력 조치: 세 지표를 자체 재무와 가격으로 다시 계산하거나 공개 업로드에서 빼고, 공개 경계 감사를 게이트에 건다.
   - 운영자 결정: 이미 공개 저장소에 올라간 과거 파일과 이력의 정리는 공개 데이터 삭제라 운영자가 정한다.

## 실험 코드와 죽은 경로

2. **dartlab-universe 실험의 잔여** (옛 dartlab-universe).
   - `landing/src/routes/universe/+page.svelte`가 `tests/_attempts/dartlabUniverse/gui/app.js`와 `universe.css`를 직접 import한다. `landing/src/routes/+layout.svelte`의 `isUniverseRoute` 분기와 `landing/vite.config.ts`의 `universeGuiDir`도 이 실험을 위한 것이다.
   - `tests/_attempts/dartlabUniverse/`에 git이 추적하는 파일 144개가 있다.
   - `pyproject.toml`의 코어 의존성 `msgspec`은 src 안에서 쓰는 곳이 없다.
   - 조치: 제품이 아니므로 공개 라우트와 분기, 코어 의존성을 걷어내고 실험 코드의 보존 여부를 정한다.
   - **처리함 (2026-11-27).** `landing/src/routes/universe/`, `tests/_attempts/dartlabUniverse/`, layout 분기, vite `universeGuiDir`, `msgspec` 의존성(uv.lock 포함)을 지웠다. 실험 코드는 git 기록에만 남긴다. 개발 서버에서 첫 화면 200, `/universe` 404, `svelte-check` 오류 0을 확인했다.
3. **리포트 엔진의 쓰이지 않는 자산** (옛 professional-report-engine).
   - `landing/static/charts/005930/hero/sixActRadar.json`과 `manifest.json`의 sixActRadar 항목, 이를 만드는 `landing/_scripts/buildCompanyCharts.py`의 분기.
   - `src/dartlab/analysis/financial/_segmentEconomics.py`의 `reconcileSegmentMargins`는 테스트(`tests/quant/test_segmentEconomics.py`)만 부른다.
   - 랜딩 리포트의 pro 블록(P3)은 지금은 착수하지 않아 기획을 닫았다. `Company.reportModel` 공개 계약은 Skill OS `engines/company`에 있다.
   - **처리함 (2026-11-27).** 레이더 생성 함수(`specSixActRadar`)는 2026-07-10 `c85c40147`에 이미 지워져 빌드 스크립트 분기가 ImportError로 죽는 상태였다. 분기, manifest 항목, json을 지웠고 이 함수를 쓰라고 적던 Skill OS `engines.viz.scenarioVisuals`도 고쳤다. `_segmentEconomics.py`와 그 테스트를 지웠다(되살릴 때 `d46f98e99`).
4. **깨진 블로그 스크립트** (옛 cards-knowledge-network).
   - `blog/_scripts/backfill_blog_insights.py`가 없는 모듈 `dartlab.ai.persistence.blog_insights`를 import한다.
   - **처리함 (2026-11-27).** 스크립트를 지우고 `blog/BLOG.md`, `blog/PIPELINE.md`, `blog/_scripts/README.md`의 안내 줄을 걷었다.
5. **지운 기획 문서를 가리키는 코드 주석**.
   - `src/dartlab/analysis/forecast/forwardTest.py`, `src/dartlab/synth/expectationSpec.py`, `tests/synth/test_calibrationMetrics.py`가 `expectation-grid` 문서 절을, `src/dartlab/simulate/profile.py`가 `panel-extraction-workbench-ssot`를, `tests/audit/workspaceHygiene.py`가 `search-productization`을 이름으로 가리킨다.
   - 조치: 가리키는 내용이 Skill OS로 옮겨지면 주석을 Skill OS id로 바꾼다.
   - **처리함 (2026-11-27).** 지운 기획 문서의 이름과 절 번호를 주석 6곳(`tests/audit/checkUiDataWiring.mjs` 포함 5개 파일)에서 걷어내고 기능 이름(기대 격자, 공시 검색)으로 바꿨다. `expectationSpec.py`의 "Expectation Grid"는 기능 이름이라 그대로 둔다.

## 운영 중인 기능의 Skill OS 반영 부족

6. **추출 카탈로그와 인벤토리** (옛 panel-extraction-workbench-ssot).
   - `src/dartlab/core/extractionCatalog/`, `src/dartlab/frame/inventory.py`의 `reportInventory`, `src/dartlab/frame/narrative.py`가 Skill OS 어디에도 없다.
   - `tests/audit/extractionCoverageCensus.py`와 `inventoryUniverseCensus.py`는 `tests/run.py`와 워크플로에 등록되지 않아 손으로만 돈다.
   - `src/dartlab/providers/dart/sectionTopic.py`의 정규식 덧대기(옛 기획의 P2 제거 목표)는 끝나지 않았다.
7. **기대 격자 원장** (옛 expectation-grid).
   - 월간 예약 실행이 2026-07-05~11-06 다섯 번 모두 성공했고, 11-06 실행은 `cycle=monthly issued=12 scored=6 errorRows=0 unscored=102`로 실데이터 채점을 했다.
   - quarterly cycle은 수동 실행 전용이고 성공 기록이 없다(수동 실행은 07-03 한 번, 실패).
   - Skill OS `engines/simulate/SKILL.md`에 한 줄뿐이고, `src/dartlab/analysis/forecast/scenarioSim.py`의 `quarterlyValues`, `seasonalSharesFromYearQuarters`는 스펙에 없다.
   - 옛 원장(04)이 적은 결함 D3, D4, D6이 남았다. 01 원장이 이 4모듈을 "expectation-grid 소속 운영 표면"으로 적은 것은 이제 v1.0 점검 소속이다.
8. **미국 종목 터미널** (옛 edgar-terminal-reach).
   - 가격 일일 수집, 재무, 검색 색인, 런타임 배선은 코드로 있고 `edgarPricesDaily.yml`이 돈다. `edgarPricesBackfill.yml`의 마지막 성공은 2026-06-30 수동 실행이다.
   - `src/dartlab/pipeline/stages/edgarPrices.py`의 `marketCap`은 `None`(TODO, 주식 수 결합 미구현)이다.
   - Skill OS `operation/terminal.md`에 미국 종목 지원이 적혀 있지 않다.
9. **공시 검색** (옛 search-productization).
   - 옛 기획이 스스로 운영 정본이라 적은 운영 런북(11번, 839줄)과 파이프라인 연결표(12번, 606줄)는 Skill OS에 없다. 둘 다 2026-06-19에 `searchIndexBuild.yml`로 합쳐진 옛 워크플로(`Search Index Delta/Main`) 기준이라 그대로 옮기지 않고, 지금 워크플로 기준으로 Skill OS `engines/search`의 운영 절에 다시 적는다.
   - Skill OS `engines/search/SKILL.md`도 지금은 없는 `searchIndexMain`을 인덱스 빌드로 적는다.
   - 출시 판정은 사람이 검토한 실제 질의 300행이 필요한데 `tests/fixtures/search/queryLogGold.real.jsonl`은 106행에서 멈췄다. 사람 검토가 필요한 항목이다.

## 옮길 것이 없었던 폴더

- 코드와 Skill OS가 이미 끝난 것: brokerage-research-index(`gather("research")`, `brokerageSync.yml`), unified-data-workbench(`dartlab.dataHub`, Skill OS `engines/dataHub`).
- 코드 없이 설계만 있던 것: ai-workbench-connector, first-party-ai, local-agent-workbench, tutorial-guide, financial-statement-lab(첫 단계 화면만 있음), innovation-stack-research(조사 노트).
- 콘텐츠 편성: dartlab-story-curriculum(블로그 연재 13편 발행 뒤 새 편 없음). 다시 쓸 때 위 커밋에서 편성 지도를 꺼낸다.
