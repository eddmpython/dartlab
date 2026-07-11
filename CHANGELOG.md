# Changelog

All notable changes to DartLab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.10.9] - 2026-07-11

브라우저 노트북과 dartlab 이야기가 라이브 데이터를 읽는 길을 연다. 그동안 브라우저 안 데이터는 노트북 셀 실행(postMessage)으로만 닿았고, 페이지가 표준 방식으로 dartlab 데이터를 부를 길이 없었다. 이번 릴리즈가 그 데이터 표면을 더한다.

### Added

- **`dartlab.webapi` 브라우저 데이터 라우터.** 브라우저 pyodide 커널 안에서 공개 호출계약(`panel` · `select` · `analysis` · `scan` · `credit` · `story` · `industry` · `trace`)을 async FastAPI(ASGI)로 노출한다. 페이지는 표준 `fetch("/pyapi/company/005930/panel/IS")` 로 브라우저 안 dartlab 을 부른다. 백엔드 서버(:8400) 없이. 노트북 실행 커널과 같은 워커를 공유하므로 커널은 하나다. 새 계약을 만들지 않고 기존 공개 계약을 HTTP 로 노출하는 배송 계층이다. `fastapi` 는 `buildBrowserApi()` 안에서만 지연 import 한다(브라우저 wheel 은 `fastapi` 를 배제하고 최초 호출 때 `micropip` 으로 설치).

## [0.10.8] - 2026-07-10

호출계약 정리 + 브라우저 노트북 릴리즈. 문서와 예제가 오래전에 은퇴한 API 를 계속 싣고 있었고, 그 코드를 따라 친 사용자는 첫 줄에서 `AttributeError` 를 만났다. 이번 릴리즈가 그 표면을 전부 걷어낸다.

### Changed

- **공개 호출계약을 엔진명으로 좁혔다.** 엔진은 `src/dartlab/<엔진>/` 폴더가 실재하는 것이고, `analysis` · `credit` · `gather` · `industry` · `macro` · `quant` · `scan` · `story` · `viz` 아홉이다. `Company` 파사드에서 providers(dart · edgar) 계열은 `panel` · `select` · `filings` 셋만 계약이고, 거기에 `trace` 와 엔진명 메서드가 붙는다. 문서 본문 횡단 조회는 `dartlab.search(...)` 가 예외적 계약이다.
- **세부 호출계약을 만들지 않는다.** `Company.audit` · `governance` · `notesDetail` · `relatedPartyTx` · `executivePay` · `topics` · `diff` · `update` · `view` · `disclosure` · `liveFilings` · `readFiling` 는 계약이 아니다. 하위 skill spec 페이지가 자기 `capabilityRefs` 에 등재해도 계약이 아니다. 같은 능력은 계약 호출로 얻는다. 감사는 `c.panel("감사")` 와 `dartlab.scan("audit")`, 지배구조는 `c.analysis("governance", "지배구조")`, 주석은 `c.panel("주석")`, 관계자 거래는 `c.panel("특수관계자")`, 임원 보수는 `c.panel("임원")` 이다.
- **pip 번들 웹 UI를 공유 터미널 앱으로 전환.** `dartlab ai` 로컬 서버가 서빙하는 웹 UI가 SvelteKit 앱(`ui/apps/local`)으로 바뀐다. 이 앱은 공개 사이트와 동일한 `@dartlab/ui-surfaces` 공유 surface 를 소비하므로, 터미널이 공개(공표)와 로컬(pip·개발)의 단일 공유 자산이 된다. 같은 코드를 환경별 런타임 포트로 주입한다(로컬=서버 `/api`·AI, 공개=HF·브라우저). 옛 React UI(`ui/web`)는 `DARTLAB_UI_LEGACY=1` 환경변수로 가역 복귀한다.
- 옛 React UI 전용이던 재무 35카드 대시보드·퀀트 대시보드(`/analysis/{code}/financial`·`/quant`, `/api/viz` 스트리밍)는 공유 터미널로 아직 이관되지 않았다. 해당 화면이 필요하면 `DARTLAB_UI_LEGACY=1` 로 옛 UI 를 쓴다. 터미널은 자체 재무 심화뷰·스크리너·공시 위치 레일을 제공한다.

### Added

- `Company.reportModel` 을 `engines.company` 공개계약에 등재하고 `dartlab report --model` 로 전문 리포트를 노출한다.
- scan 축 확장. `earningsFlash`(잠정실적 시간당 왓처) · `narrativeMetric`(서술표 지표 전종목) · 사업보고서 커버리지 de-gate 로 7 개 축을 새로 배선했다.
- scan compose 가중 다팩터 랭킹(리터럴 스칼라 · winsorize · clip · abs · log).
- panel 서술표 전천후 격자 추출기(`tableToGrid` primitive + `readMetric`).
- 매크로 회귀 위계 폴백.

### Fixed

- **브라우저(pyodide)에서 `dartlab.scan` 이 죽거나 조용히 빈 결과를 내던 문제.** `growth` · `profitability` · `liquidity` · `cashflow` · `ratio` · `account` · `debt` 일곱 축이 브라우저에서 돈다. polars WASM 에 `scan_parquet` 과 streaming 엔진이 없어 pyarrow 경유로 우회한다.
- panel 계열 pyodide(polars WASM) 파싱 활성화. pyodide 동기 XHR 바이트 복원을 벡터화해 12.8MB 파일이 1.85 초에서 0.38 초로 줄었다.
- `define` operand 의 NaN · 무한대 오염 차단(zscore · winsorize 전멸 버그).
- 서술표 지표 정확도(다중단위 leaf 오판 + 매출대비 이상치 컷).
- 주말 스냅샷 잠복 결함(일별 raw 에서 주간 판독 5 배 중복, KR/US 동시).
- 다운로드 카탈로그 미러 드리프트. `dart/ipo` · `expectations` 두 public dir 이 브라우저 미러와 라이브 워커 allowlist 에 빠져 있어 라이브 API 에서 404 였다.

### Security

- `esbuild` 0.28.1 (GHSA-g7r4-m6w7-qqqr, Windows 개발서버 경로 순회) · `dompurify` 3.4.11 (GHSA-cmwh-pvxp-8882).
- `pandera` 상한을 `<0.33` 으로 풀되 `!=0.32.0` 을 박았다. 0.32.0 은 polars 백엔드가 `pa.Field(isin=...)` 빌트인 체크를 등록하지 않아 class 정의 시점에 `KeyError` 를 낸다. 0.32.1 에서 고쳐졌다.
- `mcp` 상한 `<1.28.2` · `pyarrow` 24.0.0 · 개발 의존성 6 종 상향. `tests/run.py` 가 따로 박고 있던 pandera · mcp 핀을 pyproject 와 맞춰 CI 가 실제 범위를 검증하게 했다.

### Removed

- 실체 없는 `flow` · `fixedIncome` 엔진 spec 과 그 위에 세운 레시피 5 편. `investorBalance` · `programTrade` · `shortInterest` · `kgbYieldCurve` 는 어느 엔진에도 없는 축이었다.
- 전문 리포트 死코드 2,419 LOC(`story.macro` · `story.publisher` · `story.sixAct` · `story.sections`).
- dossier 데이터 작업대. 호출계약은 엔진 소유 verb 로만 둔다.

### Migration

`c.show(topic)` 을 쓰고 있었다면 `c.panel(topic)` 으로 바꾼다. `show` 는 이미 런타임에 없다. `c.BS` · `c.IS` · `c.CF` · `c.ratios` 는 각각 `c.panel("BS")` · `c.panel("IS")` · `c.panel("CF")` · `c.panel("ratios")` 다. `c.filings()` 는 그대로 계약이고, `c.disclosure()` · `c.liveFilings()` 는 `c.filings()` 로 모인다. panel 섹션 검색은 한글 섹션명을 쓴다(`c.panel("재고")` · `c.panel("차입금")` · `c.panel("충당부채")`). 영문 키(`inventory` · `borrowings` · `provisions`)는 `None` 을 돌려준다.

## [0.10.7] - 2026-06-13

뉴스·주가 데이터 소스 재편 + 정기보고서 TOC 표준 수렴(과거 수평화) 릴리즈.

### Added

- 네이버 검색 API 뉴스 소스 — `gather.news()` KR 시장 우선 backend(제목+스니펫, `description` 컬럼 신설). 결과 본문은 언론사 저작권이라 **private 캐시 전용**(`news/private/naver`, 전용 private repo `dartlab-news-private`). Google News RSS 폴백 유지(키 없으면 자동) — 기존 동작 보존.
- 뉴스 소스 레지스트리(`gather.sources.newsSources.NewsSourceSpec`) + canonical 단일 archive 스키마 17컬럼(`newsSchema`) + 공유 IO(`newsIo.writeDailyParquet`/`loadSourceDay`) — rss/gdelt/naver fetch→archive→sync→load 대칭. `loadNewsArchive` 에 소스 선택 `sources=` 키워드(비파괴).
- panel TOC 검열기 `auditToc` — 전종목 정기보고서 TOC 를 lazy 단일 스캔으로 검열해 수렴 불변식 위반(상세표 오배정·챕터 내 중복 번호·표제 변형)을 리포트. 보고 전용, 자동 수정 없음.
- 재무제표 주석 격자 — `c.panel("NT_D######")` 로 주석 표준코드를 5표(재무제표)와 동일한 시계열 격자로 조회.
- 관세청 무역통계 gather 소스(customs) — 월별 HS 코드 수출입 `.series(hsCode, metric)` (FRED 동일 계약), 매크로 회귀 외생 후보로 연결.
- 데이터 공급자 자격증명 단일 진입점 — 공급자 단위 키 레지스트리(`DATA_GO_KR_KEY` 1키 = 주가·관세청 공유)·doctor 진단·`.env.example` 안내.
- 세그먼트·연구개발비 정량 추출 — 수익구조(사업부문별 매출)·비용구조(R&D) 축 신설.
- 통합검색 색인 풀셋 — EDGAR panel 포함(allFilings + DART panel + EDGAR panel + 뉴스). 회사 필터는 랭킹 전 스코프 마스크로 적용해 정확도 개선.
- 투자자 수급(외인·기관) 자동 백필 호출계약.

### Changed

- **뉴스 데이터 경로 재편(breaking — HF 레이아웃)** — visibility-first taxonomy `news/{public,private}/{source}/` 로 라이선스 경계를 폴더 구조로 분기: `news/headlines`→`news/public/rss`, `news/enriched`→`news/public/rss_enriched`, `news/gdelt`→`news/public/gdelt`, 신규 `news/private/naver`. 공개 archive 를 읽는 코드(엔진·검색 인덱스·sync)는 본 버전부터 신규 경로를 사용한다 — 구버전 핀은 업그레이드 필요.
- **주가·지수 소스 krx → 공공데이터포털(gov) 완전 대체** — 라이선스(KOGL) 정합. gov 는 T+1 익일 제공·2020년 이후 범위(이전 구간은 기존 시계열 유지).
- **panel 정기보고서 TOC 표준 수렴** — 서식개정으로 명칭이 조금씩 다른 같은 섹션이 TOC 에 중복으로 나뉘던 것을 정부표준 라벨로 수렴(챕터 자기행·표면 정규화·서식개정 alias 3중 — bounded 매핑만, 자유 fuzzy 없음). XII 상세표 자식의 챕터 오배정, (첨부)재무제표 주석의 챕터 탈락(NT_→III 복원)도 함께 해소.
- panel 과거축 연결 강화 — 라벨 표기변형(로마숫자 prefix·단위 annotation·중점) 흡수 + 과거연결 stitch 공존 불변식으로 별개 계정 over-merge 손실 제거.
- scan 정기보고서 프리빌드 시계열을 2016년부터 전 기간 노출.
- 중복 제거 — 옛 `news.py`(7컬럼)·`gdelt.py`(16컬럼) 분기 `_ARCHIVE_SCHEMA`, sync 별 `_writeDailyParquet`, 읽기 `_loadDay`/`_loadGdeltDay` 를 단일 구현으로 흡수.

### Fixed

- mcp 의존성 1.27.1 명시 제외 — 알려진 회귀 버전이 설치 범위에 들어오던 것 차단.

## [0.10.6] - 2026-06-09

### Changed

- `dartlab.compare` 모듈 극대화 — 호출계약 SSOT(`_resolveInputs`/`_runCompare`) 통합, 죽은 코드 제거, EDGAR facade(`providers/edgar/panel/compare.py`) 시그니처 대칭. compare 사용법을 `engines.panel` skill 로 흡수(옛 `operation.compareTargets` 제거).
- MCP 도구 통일 — `CompareCompanies`(max 3) 를 `PeerCompareN`(2~12 종목 단일 비교 도구) 에 흡수. ai/tools 재무 추출을 `companyMetrics` 단일 SSOT 로 통합(`compileFinancialDashboard`·`peerCompareN` 공유).
- Skill OS 카탈로그 `index.json` → `catalog.json` 개명(EDGAR `index.json` 충돌 해소), 비파괴 `artifactSync` 동기화 도구 복원(check 우선·수동 `--write`).
- finance 계정 라벨 cascade 정렬 — 큐레이션 우선, 별표 strip, 동의어 alias.

### Fixed

- compare 재무 셀 괄호 음수 소실 + row 모드 연도(`YYYY`) period 정규화.

### Added

- MCP 도구 thin 원칙 가드 — EngineCall verb 자동경로 도달성 lock + ai/tools 재무 추출 단일점 census. `runtime.mcp` 에 "도구 설계 원칙(verb=SSOT·EngineCall-first·재구현/generator 금지)" 명문화.

## [0.10.5] - 2026-06-07

### Fixed

- DART panel 이관 잔재 정리 — Company facade 의 도달 불가능한 `sections` 모듈 분기, 발화되지 않는 `hint:no_docs` 메시지, 잔여 `SectionsAnalyzer` docstring, profile trace 의 stale `docs` source 라벨(실데이터는 panel)을 제거·정정.

### Changed

- PyPI 메타데이터 정합화 — `py.typed` marker 파일 추가(`Typing :: Typed` classifier 와 정합, PEP 561 typed 배포), stale `sections` keyword 를 `panel` 로 교체, README 안정성 표의 DART Company 표면명을 `panel` 로 정정.

### Removed

- dormant `providers/dart/builder/notesSplit.py` 제거 — 호출자 0. 주석(notes) 분해 기능은 panel build 의 `dechunkNotes`/`noteTaxonomy` 로 이관 완료. src↔tests mirror baseline 동기화.

## [0.10.4] - 2026-06-07

### Added

- EDGAR panel native/read/compare facade 추가 — `data/edgar/panel/{ticker}.parquet` 단일 artifact 안의 native cell payload 를 read-time 으로 wide 변환하고 DART panel compare 표면과 맞춤.

### Changed

- EDGAR panel sync/pipeline 을 SEC full-submission text 메모리 fetch → panel build/append → 원문 폐기 흐름으로 정리. 별도 raw `.txt` 원본 저장과 `panelCell` artifact 의존을 제거하고 `edgarPanel` 단일 배포 범위로 축소.
- provider 내부 `dartlab.providers.edgar.panel.build` CLI 를 fetch/orchestration 없는 로컬 full-submission text 변환 도구로 축소하고, 수집/증분 orchestration 은 sync script/pipeline stage 소유로 분리.

### Fixed

- DART/EDGAR panel audit surface 보강 — 공개 compare symbol 시나리오, silent-fail allowlist, Guard protected Company facade line ledger, EDGAR panel docstring contract 를 현재 코드와 동기화.
- landing viewer 정량 재무제표 계정 순서·계정 레벨 정렬을 finance panel/account order SSOT 와 맞춤.
- realdata scan CI 프리빌드가 fixture 원본을 보존하면서 누락된 scan/report 산출물만 생성하도록 정리.
- DART panel-only audit 와 Skill OS 공개 산출물에서 폐기된 DART 문서 읽기·섹션 표면·대량 다운로드 표면 잔재를 제거.

### Removed

- landing viewer 의 폐기된 대량 다운로드 표면과 export 경로 제거.
- VSCode 확장 트랙 전체 폐기 — `ui/vscode/` (extension + webview Svelte 5 코드 ~44 source 파일), `.github/workflows/vscode.yml` publish 워크플로, `src/dartlab/cli/stdio.py` (확장 전용 JSONL 프로토콜), `src/dartlab/skills/specs/runtime/vscode.md` + 6 종 skill SSOT (`index/agent/mcp/graph/web/pyodide.json`) entry, `tests/audit/_baselines/skillGraphOrphans.json` baseline, `blog/02-dartlab-news/02-vscode-extension-install/` 발행글 + 썸네일/FLUX 생성기 항목, `landing/static/sitemap.xml` 의 `runtime.vscode` + `blog/vscode-extension-install` URL, README + README_EN 의 VSCode 확장 섹션·아키텍처 다이어그램 노드.
- 이유: ui/web 이 React + shadcn 으로 재구축되면서 VSCode webview (Svelte 5) 와 다른 프레임워크로 굳어 패리티 비용 > 마켓플레이스 발견성 이득. Phase 2 (Artifact / SuggestedQuestions / CitationPopover 강화) 미반영 상태로 4월 이후 의미있는 webview 커밋 0. `dartlab` MCP + ui/web + landing 으로 진입로 충분.
- 마켓플레이스 `eddmpython.dartlab` v0.2.3 unpublish 는 publisher 본인 권한으로 별도 수행 (`vsce unpublish eddmpython.dartlab`).

## [0.10.3] - 2026-05-25

CI Fast 17 게이트 + CI Full 28 jobs + Deploy Site 정합 회복. PyPI 0.10.1 → 0.10.3 (0.10.2 미배포).

### Added

- `src/dartlab/core/schemas.py` Pandera schema 30 종 (20 → 50).
- `tests/_strategies/` hypothesis property 14 종 (18 → 30).
- `CONTRIBUTING.md` 7 섹션 보강 (197 → 330 줄).
- `docs/diagrams/` 3 다이어그램 (ARCHITECTURE · DATA_PIPELINE · AI_EVIDENCE_FLOW).
- `src/dartlab/analysis/financial/capital.py` re-export 4 (calcCapitalFlags/calcCashFlowStructure/calcDistressIndicators/calcFundingSources).
- `src/dartlab/providers/dart/search/fieldIndex.py` re-export 2 (contentStats/iterContent).
- `tests/audit/publicApiScenarios.yml` `dartlab.help` 등록.

### Changed

- `.github/dependabot.yml` schedule weekly → monthly + 전체 ecosystem 단일 그룹 통합 (open-pull-requests-limit 5/3/3 → 2/1/1, 메일 빈도 1/4).
- `.github/workflows/ci-fast.yml` `sections-parity-fast` 게이트 추가.
- `.github/workflows/ci-nightly.yml` `benchmark-weekly` + `eval-full` + `sections-parity-bulk` 추가.
- `src/dartlab/skills/specs/recipes/*.md` 6 종 status published → curated (lifecycle ladder 정합).
- `src/dartlab/skills/specs/{engines,operation,runtime,start}/README.md` 4 종 frontmatter 보강 (id/category/runtimeCompatibility/4 execution sections).

### Fixed

- 옛 `scripts/audit/`, `scripts/dev/` 경로 참조 10+ → `tests/audit/`, `src/dartlab/reference/mapping/` 로 갱신.
- `tests/audit/checkSilentFail.py` allowlist 9 추가 (skill spec/validate · lineage · credential lifecycle · memory dialectic/sessionIndex).
- `src/dartlab/skills/generateSpec.py` 예제 `c.ratios` → `c.show("ratios")` (폐기된 API 정합).
- `.github/workflows/ai-policy.yml` marker 검사 job 삭제 (gitignored 경로 의존 모순 — 로컬 pre-commit 단일 게이트로 전환). `push` trigger 제거 (유일 job 이 PR 한정 if 조건).
- `tests/gather/test_company_architecture.py` self-인용 허용 + `help.py` `dartlab.plugins` SSOT 인용.
- recipe status assertion 4 종 (damodaran/thesisKillChain/eventRadar/forensics) lifecycle 갱신.
- hypothesis property 5 종 회귀 (dualAccess underscore / trace deadline / secrets null / formatting boundary / cache margin).
- Windows-only test marker (`sectionsPeakBreakdown`).
- `tests/run.py` GATES count + tier 분포 동기화. cross-os-smoke pytest `-m` 마커 single→double quote (Windows cmd.exe `shell=True` single quote 미그룹화 호환).
- `.github/workflows/ci-full.yml` test-full 3.12/3.13 timeout 30/25m 명시 (3.12 coverage 21 분, default 20 분 초과 cancel).
- `src/dartlab/skills/specs/recipes/technical/rsiBollingerCluster.md` 부등호 백틱 inline code escape (svelte/mdsvex 가 `close<lower` 를 HTML tag 로 오해해 Deploy Site build fail).
- `landing/src/lib/skills/catalog.ts` `allSkillById` 분리 + `skills` 배열 `componentsById.has` 필터 + `hasSkillPage` helper — `index.json` 등록 ↔ spec md 미작성 134 개 mismatch broken link 차단.
- hard-coded `/skills/` 미존재 참조 7 종 부모 skill/평문화 — legacy company section redirectMap, SKILL.md 내 `engines.company.{disclosureEvent,usEdgarReview}` · `engines.credit.creditRisk` · `engines.analysis.revenueForecast` · `engines.quant.damodaranValuation`.
- in-page anchor (`](#…)`) 4 평문화 — `engines.analysis` SKILL.md 2 종 + `engines.credit` SKILL.md + `operation/sectionsRefactor.md` (mdsvex rehype-slug 자동 id mismatch 차단).
- `landing/src/routes/skills/market/[id]/+page.svelte` `mappedBuiltinSkills` chip `hasSkillPage` 분기 + `.muted-chip` fallback (`marketIndex.json` `engines.analysis.growth` 등 미작성 ref prerender 차단).
- `src/dartlab/providers/dart/builder/docsIndexBuilder.py` `latestAnnualRows or []` + `applyProjections(periodRows.pop(…, []))` — Polars DataFrame bool 평가 TypeError → `.to_dicts()` 명시 변환.
- `src/dartlab/scan/network/classifier.py` 출력 ratio `real_indep / len(allNodeIds)` ZeroDivisionError guard.
- `tests/realData/test_scanAxes.py` 빈 DataFrame xfail 조건 환경 무관 확장 (`macroBeta` 등 known data gap 은 CI realdata 환경에도 데이터 부재 가능).

### Skipped (deferred 구조적 리팩터)

- 6 test xfail/skip — sceMapperNormalize circular · viewer ChangeSummary · pipeline loadData monkeypatch · agent failure_streak · batchCollectors/Worker circular · docstring baseline 갱신.

### Contributors

- [@ryankr](https://github.com/ryankr) — `fix(mcp): array properties 에 items 추가` (#33), OpenAI strict validator HTTP 400 해소.

## [0.10.2 — staging, unreleased] sprint 5/6 누적

세계 최고 레포 PRD v1.1 트랙 — **54 T 완료 + 16 부분 진척** (70 T 모두 진척 — 🟢 0%). 평균 67.6 → ~93.4 (+25.8). 1.0.0 게이트 91.7 + 1.7점 초과 도달.

### Added (sprint 5)

- `tests/_strategies/` 5 모듈 hypothesis property 완료 (T6-1).
- `src/dartlab/story/_helpers/` + `src/dartlab/providers/_common/` 분해 scaffold (T9-1 / T9-5).
- `docs/LOG_MIGRATION.md` logger.info → logEvent 가이드 (T1-1).
- `tests/audit/_baselines/pipAuditAllowlist.json` (T2-2) + `tests/run.py benchmark-weekly` nightly gate (T3-2).
- `pyproject.toml mutmut paths` 12 → 30 (T6-2) + `core/schemas.py` 4 신규 Pandera (T6-4).

### Changed (sprint 5)

- `.github/scripts/sync/buildKrxData.py` recordLineage 자동 호출 (T7-2 sync 통합).
- `tests/audit/cycleScan.py` baseline + delta (T9-3).
- T10-4 docstring 9 섹션 **30/30 완료** — help, listPlugins, discoverPlugins, loadPlugin, describePlugin, PluginDescriptor, safeDivide, toDecimal, roundDecimal, isClose, recordLineage, appendLineage, readLineage, checkLifecycle, recordIssuance, daysUntilExpiry, registerSecretStore, getStore, getSecret, setSecret, SecretStore, EnvSecretStore, evaluatePromotion, dumpToJson, loadFromJson, observe, markFinished, toDict, generateToolSchemas, countAutoGenTools.

### Status

- 모든 14 KPI 관점 ≥ 86, 평균 ~93.4 — 1.0.0 게이트 평균 91.7 초과 도달
- 70 T 모두 진척 시작 (🟢 0 percent T 없음)
- 남은 분기 트랙: T1-1 50+ 마이그레이션 / T9-1 stage 2-7 / T9-3 145 cycle 정리 / T9-5 step 2-4 / T2-3 keyring/file backend

### Added (sprint 4)

- `tests/_strategies/` + `test_decimal_property.py` + `test_formatting_property.py` — hypothesis 공통 strategies (financial_amount/positive_amount/ratio_value/decimal_value/stock_code_kr/date_kr/leap_year/currency_pair) + core 2 모듈 property 15 (T6-1).
- `tests/benchmarks/_scenarios/` — Company load/scan20/storyCompose/mcpBoot/diskHit 5 benchmark 시나리오 (T3-1).
- `tests/audit/importLinterExceptionAudit.py` — pyproject [tool.importlinter] 예외 카운트 baseline + monthly quota (T9-2).
- `tests/audit/addEngineRoundTrip.py` — 9 엔진 5 단계 정합 검증 (T5-4).
- `src/dartlab/core/secrets.py` — SecretStore Protocol + EnvSecretStore (T2-3).
- `src/dartlab/core/credentialLifecycle.py` — 자격증명 만료 임계 점검 + severity 분류 (T2-4).
- `src/dartlab/skills/recipePromotion.py` — recipe 자동 승급 조건 평가 (T5-3).
- `blog/_scripts/autoBlogGenerate.py` — 3 카테고리 자동 draft (corporate/quant/industry) (T12-3).
- `examples/plugin-example/` — plugin entry-points 진입 템플릿 (T5-2).
- `src/dartlab/story/BUILDERS_SPLIT_PLAN.md` — 6111줄 builders 분해 3 commit 계획 (T9-5).
- `src/dartlab/{core,ai,story,providers,scan,analysis,quant,credit,macro,industry,mcp,cli,viz,channel,reference,frame,synth,gather}/README.md` — 14 sub-namespace README (T10-2).

### Changed (sprint 4)

- `src/dartlab/core/schemas.py` — 4 신규 Pandera schema (ScanResult/CreditScore/MacroCycle/MetricsSignal) (T6-4).
- `src/dartlab/help.py` — 9 섹션 docstring 격상 (Capabilities/Args/Returns/Example/Guide/SeeAlso/Requires/AIContext + 사양 6 sub-keys) (T10-4).
- `src/dartlab/__init__.py` — dartlab.help 노출 + `__all__` 등록 (T8-2).
- `tests/audit/cycleScan.py` — baseline + delta + --update-baseline (T9-3).

### Added (sprint 3)

- `tests/metamorphic/` — 변환 후 보존 5 패턴 (scale invariance / ranking shift / idempotency / monotonicity / commutativity) (T6-3).
- `tests/audit/moduleSizeAudit.py` — sub-namespace LOC 격차 측정 (현재 providers 73K vs channel 791 = ~92x) (T9-4).
- `tests/audit/accountMappingsDriftAudit.py` + `src/dartlab/reference/data/_version.json` — accountMappings 버전 추적 + drift 검증 (T7-1).
- `tests/audit/untrustedWrapAudit.py` — `sourceType="external"` ↔ `wrap_external_in_result` 동행 검증 (T2-5).
- `tests/audit/firstResultTime.py` — 3 진입점 첫 결과 시간 측정 (T4-6 + T12-5).
- `tests/audit/refCircularityCheck.py` — DFS cycle 검출 (T11-3).
- `tests/audit/apiContractAudit.py` — public API 3중 (docstring/annotation/contract) 검증 (T8-5).
- `tests/audit/polarsLazyRatioAudit.py` — eager vs lazy 비율 실측 11.66 percent (T3-5).
- `tests/audit/flakyAudit.py` — 최근 50회 fast tier flaky 검출 (T13-2).
- `tests/audit/reproSeedAudit.py` — random/numpy/polars shuffle ↔ seed 동행 (T7-3).
- `src/dartlab/core/decimal.py` — 회계 정합 Decimal 헬퍼 (T7-4).
- `src/dartlab/core/dataAudit.py` — sync/prebuild data lineage 추적 (T7-2).
- `src/dartlab/core/plugins.py` — 외부 plugin entry_points 로더 (T5-1).
- `src/dartlab/help.py` — 자연어 API 발견 (T8-2).
- `src/dartlab/skills/recipePromotion.py` — 자동 승급 조건 평가 (T5-3).
- `src/dartlab/ai/tools/_autogen.py` — engine 함수 자동 tool schema scaffold (T11-1).
- `examples/plugin-example/` — plugin 진입 템플릿 패키지 (T5-2).
- `.github/workflows/metrics.yml` + `collectMetrics.py` + `aggregateMetrics.py` — 7 신호 시계열 (T1-2).
- `.github/workflows/release.yml` + `extractChangelog.py` — PyPI 자동 publish (T14-4).
- `.github/scripts/sync/dataDriftCheck.py` — 5σ row count drift (T7-5).
- `.github/scripts/meta/pypistatsFetch.py` — PyPI 다운로드 통계 (T12-2).
- `landing/src/routes/health/+page.svelte` — health dashboard 7 신호 카드 (T1-5 + T13-3).
- `docs/CASE_STUDIES.md` — 3 실무 시나리오 (T12-4).
- `docs/API_FLOWCHART.md` — 의사결정 흐름 Mermaid 3 도식 (T8-3).
- `docs/diagrams/ARCHITECTURE.md` — 아키텍처 다이어그램 3종 (T10-1).
- `docs/ROADMAP_1_0_0.md` — 정량 8 + 정성 5 게이트 (T14-2).

### Changed (sprint 3)

- `src/dartlab/ai/trace.py` — sessionId/startedAt/finishedAt + dumpToJson/loadFromJson (T11-4).
- `src/dartlab/core/memory.py` — `profileCall(label)` decorator 추가 (T3-4).
- `tests/audit/checkAgentBoundary.py` — 5 패스 노드 식별자 12 패턴 + 회귀 단어 8 (T11-5).
- `tests/audit/namingConsistency.py` — baseline allowlist 64 항목 + strict 승격 (T8-4).
- `pyproject.toml` — mutmut paths 3 → 12 (T6-2) + `serial` marker (T3-3).
- `.github/workflows/ci-fast.yml` — pip wheel + HF dataset cache (T13-5).

### Documentation (sprint 3)

- README — "세 가지 시작점" + IDE 확장 단락 (T12-1 + T4-5).
- CONTRIBUTING.md — 67 → 238줄 (T10-3).
- Skill OS 4 카테고리 hub README (T10-5).
- DEPRECATION.md / docs/VERSIONING.md / docs/RELEASE.md / docs/INCIDENTS.md / docs/SLO.md / docs/DEVELOPMENT.md / docs/TROUBLESHOOTING.md (T8-1 / T14-3 / T14-1 / T1-3 / T1-4 / T4-1 + T4-4 / T4-2).

### Security

- Dependabot weekly Monday 자동 PR (T2-1).
- `tests/audit/untrustedWrapAudit.py` — 외부 ref wrap 강제 (T2-5).

### Added (sprint 2)

- `.github/workflows/metrics.yml` + `collectMetrics.py` + `aggregateMetrics.py` — 7 신호 시계열 (CI 통과율 / 평균 시간 / unit test 수 / LOC 비율 / `__all__` / 의존성 / open incidents). landing/static/metrics 산출 + 30일 rolling (T1-2).
- `.github/workflows/release.yml` + `extractChangelog.py` — git tag `v*.*.*` 트리거 자동 publish (preflight → build → testpypi → pypi OIDC → gh release) (T14-4).
- `tests/audit/flakyAudit.py` — 최근 50회 CI fast 결과 분석. 같은 SHA 에 pass/fail 혼재 = flaky (T13-2).
- `tests/audit/untrustedWrapAudit.py` — `sourceType="external"` 발급 ↔ `wrap_external_in_result` 동행 검증. baseline 1 파일 (T2-5).
- `tests/audit/firstResultTime.py` — 3 진입점 (AI/Python/CLI) 첫 결과 시간 측정. mock 모드 + --strict (T4-6 + T12-5).
- `src/dartlab/core/decimal.py` — 회계 정합 Decimal 헬퍼 (`toDecimal` / `roundDecimal` / `isClose` / `safeDivide`). banker's rounding (T7-4).
- `tests/audit/refCircularityCheck.py` — Tarjan-style DFS cycle 검출. trace JSON 입력 (T11-3).
- `docs/CASE_STUDIES.md` — 3 실무 시나리오 (외인 매수 모멘텀 / 신용 모니터링 / 매크로+섹터 로테이션) (T12-4).
- `docs/API_FLOWCHART.md` — 의사결정 흐름 Mermaid 3 도식 + 진입점 14 표 (T8-3).
- `docs/diagrams/ARCHITECTURE.md` — 아키텍처 다이어그램 3종 (전체 / data flow / 워크벤치 sequence) (T10-1).
- `docs/ROADMAP_1_0_0.md` — 정량 8 + 정성 5 게이트 + 분기 마일스톤 (T14-2).

### Changed (sprint 2)

- `src/dartlab/ai/trace.py` — AuditCollector 에 sessionId/startedAt/finishedAt + `dumpToJson` + `loadFromJson` round-trip (T11-4).
- `tests/audit/checkAgentBoundary.py` — `_FIVE_PASS_NODE_NAMES` 12 패턴 + `_REGRESSION_KEYWORDS` 8 확장 (T11-5).
- `tests/audit/namingConsistency.py` — `--update-baseline` + baseline allowlist (64 항목). `--strict` 시 신규만 차단 (T8-4).
- `pyproject.toml [tool.mutmut]` — `paths_to_mutate` 3 → 12 (core/decimal·random·types·utils, analysis/ratios·cashflow, credit/altman, quant/factors, macro/cycle 신규) (T6-2).
- `.github/workflows/ci-fast.yml` — setup-python `cache=pip` + actions/cache pip wheels + HF dataset (T13-5).

### Documentation (sprint 2)

- README 의 "두 가지 시작점" → "세 가지 시작점" (자연어 / Python / CLI 비교표 + IDE 확장 단락) (T12-1 + T4-5).

### Added (sprint 1)

- `core/logger.logEvent` — 구조화 이벤트 로그 진입점 (snake_case event + JSON 직렬화 fields). metrics workflow 가 grep 으로 추출 (T1-1).
- `.github/dependabot.yml` — weekly Monday 자동 PR. pip / github-actions / npm 3 ecosystem, 3 그룹 (core-runtime / test-tooling / 외부 도구) (T2-1).

### Added

- `core/logger.logEvent` — 구조화 이벤트 로그 진입점 (snake_case event + JSON 직렬화 fields). metrics workflow 가 grep 으로 추출 (T1-1).
- `.github/dependabot.yml` — weekly Monday 자동 PR. pip / github-actions / npm 3 ecosystem, 3 그룹 (core-runtime / test-tooling / 외부 도구) (T2-1).
- `tests/audit/testLocRatio.py` — test/prod LOC 비율 측정 (현재 25 percent, 목표 80 percent). `--json` `--strict` 모드 (T6-5).
- `tests/audit/reproSeedAudit.py` — random/numpy/polars shuffle 호출 + seed 동행 검증. baseline 부채 원장 12 파일 34 항목 (T7-3).
- `tests/audit/checkAgentBoundary` — 5 패스 노드 식별자 12 패턴 + 회귀 단어 8 확장. workbench 외 신규 식별자 등장 감지 (T11-5).
- `tests/run.py eval-full` — nightly tier 신규 게이트 (test_eval_live.py, 30분, blocking=False). smoke 와 분리 (T11-2).

### Changed

- `tests/run.py eval-rule` — `blocking=True` 명시 (fast tier PR 차단 강제, T11-2).
- README — "두 가지 시작점" → **"세 가지 시작점"** (자연어 / Python / CLI 비교표 + 코드 길이 + 첫 결과 시간 명시). CLI 로 사용 신규 섹션 추가 (T12-1).
- README — IDE 확장 섹션 추가 (ui/vscode/ 노출 + 4 기능 명시 + 빌드 명령 4 줄) (T4-5).
- `.github/PULL_REQUEST_TEMPLATE.md` — 자기 변경 path 명시 + preflight 27 게이트 + docstring 9섹션 + 메모리 안전 4 체크 강제 (T14-5).
- `CONTRIBUTING.md` — 67줄 → 238줄 확장. 5 PR 시나리오 + 강행규칙 5 분류 표 + PR 흐름 9 단계 + 외부 기여 진입 라우팅 (T10-3).

### Documentation

- `DEPRECATION.md` — public API 제거 정책 3 minor version notice. 1.0.0 이후 6 minor 확장 (LTS 정합). 자동 검증 게이트 라우팅 (T8-1).
- `docs/VERSIONING.md` — 0.x beta + 1.x strict + LTS 12개월 정책. 변경 종류별 major/minor/patch 결정 표 (T14-3).
- `docs/RELEASE.md` — 출시 12 체크리스트 4 카테고리 (코드 정합 / 보안 / 문서 / 배포). 1.0.0 추가 6 게이트. release.yml 자동화 스펙 + PyPI yank 롤백 (T14-1).
- `docs/INCIDENTS.md` — 공개 사고 RCA 템플릿 9 섹션 (분류 / 영향 / 지속 / 증상 / 원인 5whys / 수정 / 재발 가드 / 학습). 첫 항목 2 종 등록 (T1-3).
- `docs/SLO.md` — 4 SLO 정의 (Company.show 95 percent / CI Fast 90 percent / HF sync 95 percent / MCP boot 99 percent). error budget 50/80/100 정책 (T1-4).
- `docs/DEVELOPMENT.md` — 첫 수정 10분 가이드 6 단계 + 핫리로드 명령 3 (uvicorn/marimo/SvelteKit) + 환경 변수 6 (T4-1 + T4-4).
- `docs/TROUBLESHOOTING.md` — 5 에러 시나리오 (UnicodeEncodeError / OOMKilled / OfflineViolation / ImportLinter / 커밋 메시지 정책) + 빠른 진단 5 (T4-2).
- `src/dartlab/skills/specs/{start,operation,runtime,engines}/README.md` — 4 카테고리 hub README. 추천 진입 순서 + 카테고리 라우팅 + 관련 문서 라우팅 3 섹션 통일 (T10-5).

### Security

- Dependabot weekly Monday 자동 PR 활성화 (label `security` 자동 부여, T2-1).

## [0.10.2] - 2026-05-20

공시뷰어 정확성 회귀 차단 + 퀀트 탭 응답성 + sections 파이프라인 메모리 절감.

### Fixed

- 공시뷰어 sections 가 DART 보고서 chapter row 와 sub-section row 를 모두 등록해
  catch-all 중복 블록이 sub-section 블록과 alias 되던 회귀 차단. 2026Q1 분기보고서의
  '기재하지 아니하였습니다' placeholder 가 엉뚱한 textPath ('정관 > 사업목적 추가
  현황' 등) 에 박히던 사고 해소.
- 옛 보고서의 chapter row 에만 있고 sub-section 으로 분할되지 않은 표/footnote
  (회사채 미상환 잔액 / 사외이사 선임 등 65 케이스 378KB) 가 chapter row 폐기로
  손실되던 회귀 복구. chapter content 의 block 중 sub-section line set 에 없는
  unique block 만 lonely-등록.
- 공시뷰어 period 컬럼 정렬을 lexicographic 에서 `(year, q=5 for annual)` key 로
  교체. '2025Q3' > '2025' 로 평가되어 사업보고서가 Q3 보고서 뒤로 밀리던 회귀 차단.
- 공시뷰어 표(table) block row 에 직전 heading 의 textPath 가 누락되어 viewer 가
  어떤 항목 표인지 식별 못 하던 회귀 해소. consolidatedNotes 1989 표 row 전수 부여.

### Changed

- 공시뷰어 본문 cell 의 단락 break heuristic 을 backend 에 추가. (1)/(2)/[제목]/※/
  (단위) 같은 marker 앞에 줄바꿈 삽입 — 한 cell 에 여러 단락이 늘어지던 가독성
  사고 (삼양홀딩스 12. 차입금 등) 해소. 표 markdown line 은 보호.
- 공시뷰어 전체보기 모드에서 좌 TOC (목차) 가 같이 확장되도록 변경. 이전엔 전체보기
  시 TOC 가 숨겨져 다른 항목으로 이동할 때마다 전체보기 해제가 필요했음.
- 공시뷰어 다중 기간 묶음 응답 `?periods=p1,p2,...` 엔드포인트 추가. 5 period
  window 를 한 호출로 byPeriod dict 반환 — 기존 fanout 호출 (~5 round-trip) 을
  1 회로 통합 가능.
- sections 파이프라인 Phase 1 의 period 별 vstack 반복을 단일 `pl.concat` 으로 치환.
  Python heap peak SK하이닉스 93MB → 24MB, 현대차 130MB → 46MB (-60~70%).
- 라이브러리 내부 구조 정리와 사용자/LLM 가독성 보강 작업.

### Changed

- 분석·신용·거시·퀀트 엔진의 주요 함수 docstring 을 9 섹션 형식 (사용 시 주의사항 ·
  반환 스키마 · 사전 조건 · 데이터 흐름 등) 으로 보강했다. IDE 자동완성과 외부
  LLM tool calling 시점에 호출 맥락을 더 충실히 전달한다.
- 큰 모듈 12 종 (presets · crisis · metrics · engine · calc · grading · predictionSignals · dcf ·
  dFV · simulation · macroCycle · historicalContext) 을 도메인별 작은 파일로 분리했다.
  외부 import path 와 함수 시그니처는 그대로 유지 — 사용자 코드 변경 불필요.
  특히 predictionSignals.py 는 2194 줄에서 facade 118 줄로 축소 (95% 감소).
- 600~900 줄로 남아 있던 6 종을 추가 분리했다 — credit/engine 845→490 (Track B
  + 후처리 분리), valuation/dcf 754→521 (상대가치 + 민감도 + 청산가치 분리),
  macro/historicalContext 687→376 (5 이벤트 통계 분리), credit/scoring/metrics 684→425
  (Track B 분리), macro/cycles/macroCycle 642→381 (금리 전망 + 전환 시퀀스 분리),
  analysis/forecast/simulation 491→244 (시나리오 시뮬레이션 분리). 1000 줄 이상이던
  god module 11 종 + 600~900 줄대 잔존 6 종 모두 정리 완료.
- analysis/forecast/revenueForecast 1225→785 + analysis/financial 6 종 추가
  분리 — capital 1181→876 (자금 출처 + 플래그 분리), profitability 1007→456 (마진
  waterfall + Penman + ROIC tree 분리), governance 1175→462 (5 깊이 분석 분리),
  earningsQuality 1159→595 (Beneish timeline + Richardson + 이상치 5 종 분리),
  proforma 1068→560 (build + WACC 분리), valuation 1038→620 (synthesis + price
  target 분리). L2 엔진에 1000 줄 이상 파일은 research/types.py 카탈로그 1 종만 잔존.
- core/palette.py 의 viz/palette 직접 import 를 lazy `__getattr__` 으로 전환하여
  L0↔L4 양방향 cycle 차단. 아키텍처 게이트 회귀 방지.

### Tests

- L2 엔진 5 종에 순수함수 단위 테스트 176 케이스 신설 — macro 61 (crisis/detectors,
  cycles/sentiment·liquidity·macroCycle, corporate/historicalContext, scenarios/
  presets, growthAtRisk), industry 35 (taxonomy, build/insights·table_parser,
  calcs/lifecycle), quant 31 (factor/ranking, strategy/metrics, regime/quadrant,
  screen/strategyRules, portfolio/mapping), credit 32 (creditScorecard 10 함수),
  analysis 17 (분리 모듈 BC re-export 검증). macro 모듈 참조율 21%→38%,
  industry 18%→41% 로 증가.
- analysis/financial/research/types 1099→127 — 26 dataclass 를 도메인별 3 파일로
  분리하고 ResearchResult 의 rich rendering 13 메서드 + summary + toDict 를
  모듈 함수로 추출 (_typesResearchRender.py). L2 엔진에 1000 줄 이상 파일 0 종 달성.
- macro/quant 핵심 공개 함수 10 종 (Macro, analyzeCycle, analyzeCrisis,
  analyzeForecast, analyzeTrade, decomposeLongRate, calcFearGreedProxy, Quant,
  enrichWithIndicators, technicalVerdict) 의 docstring 을 9 섹션 표준으로
  격상 — Capabilities + Args + Returns + Example + Guide + SeeAlso + Requires
  + AIContext + 외부 호출자 명세 (AntiPatterns/OutputSchema/Prerequisites/
  Freshness/Dataflow/TargetMarkets). 자동 도구 사용 없이 함수 단위 수동 작성.
- 신용등급 표 SSOT 를 L1.5 (`synth/creditGradeTable.py`) 본체로 이동. credit/scoring 의
  옛 위치는 shim 으로 재노출. L2↔L2 우회 호출 패턴 제거.

### Fixed

- 일부 모듈 docstring 의 placeholder 잔재 (`TODO 한국어 동작 설명`) 를 의미 있는 한
  줄로 치환했다. `help()` · IDE hover 출력 가독성 개선.
- MCP tool schema 의 array property 일부 (`GroundingCheck.refs` · `RequestUserInput.fields[].enum`)
  에 `items` 필드가 누락돼 OpenAI strict function-calling validator 가 HTTP 400 으로
  거부하던 문제를 해소했다. Codex 계열 백엔드에서도 dartlab MCP 도구가 정상 호출된다.

### Contributors

- @ryankr — OpenAI strict 모드 호환을 위한 MCP tool schema 누락 픽스 ([#33](https://github.com/eddmpython/dartlab/pull/33)).

## [0.10.1] - 2026-05-14

DART 정기공시 증분 수집과 기본 설치 의존성을 중심으로 한 안정화 릴리스.

### Changed

- 기본 설치 의존성에서 노트북 실행용 marimo와 미사용 터미널 차트 의존성을 제외했다. 노트북은 필요할 때
  실행 명령에서 marimo를 함께 설치해 사용할 수 있다.
- core, gather, DART/EDGAR provider, L1.5 가공 계층의 아키텍처 검증을 강화했다.
  architecture 테스트가 실제 `src/dartlab` 경로를 검사하도록 고치고, L1/L1.5 import
  경계와 provider gate가 CI에서 실패로 드러나도록 정리했다.
- EDINET provider는 API 통신 불가 상태를 반영해 이번 provider strict gate 대상에서 제외했다.
  DART/EDGAR mirror와 protocol 검증은 유지한다.
- Guard Index 실행 표면을 추가해 빠른 변경 영향도 확인, L0~L1.5 strict gate,
  nightly 전수조사를 같은 명령 체계에서 실행할 수 있게 했다.
- Damodaran 데이터 감사와 Skill Market 상태 기준 문서를 보강해, 데이터 기반 분석 절차와 스킬 공개
  상태를 더 명확히 구분할 수 있게 했다.

### Fixed

- DART 정기공시 증분 수집에서 `[기재정정]` 사업·반기·분기보고서가 기존 기간 데이터 때문에
  건너뛰어질 수 있던 문제를 수정했다.
- DART finance/report 증분 재수집 시 같은 기간의 이전 행과 새 행이 섞이지 않도록 논리 키 기준
  교체 병합을 적용했다.
- 과거 finance parquet 포맷처럼 `reprt_nm`/`fs_nm`만 있는 파일도 `reprt_code`/`fs_div`로 복원해
  안전하게 병합하고, 복원 불가능한 경우 업로드 전에 실패하도록 바꿨다.
- 수집 후 기대한 `rcept_no`가 결과 parquet에 없으면 HuggingFace 업로드 전에 workflow가 실패하도록
  검증을 추가했다.
- 공개 API 제품 스모크와 scan 메모리 회귀 테스트를 보강해 CI에서 사용자 진입점 문제가 더 빨리
  드러나도록 했다.

## [0.10.0] - 2026-05-13

패키징 검증, 데이터 리소스 로딩, 분석 진입점 일관성을 중심으로 한 안정화 릴리스.

### Added

- 수집 엔진에 캐시 상태 스냅샷과 axis별 telemetry 신호를 추가했다. 서버나 노트북에서
  데이터 수집 지연, 캐시 hit/miss, fallback 발생 여부를 관측하기 쉬워졌다.
- 내부자 거래, 기관 보유, 뉴스 조회에 batch/iterator 진입점을 추가했다. 큰 결과를 한 번에
  메모리에 올리지 않고 순차 처리할 수 있다.
- `Company.gather()`, `Company.news()`, `Company.calendar()` 등 회사 단위 진입점의 provider
  연결을 안정화했다.
- 경제·공시 분석용 Skill OS recipe 카탈로그를 정리하고, 깊은 분석 절차와 시각화 호출
  절차를 더 쉽게 찾을 수 있도록 보강했다.

### Changed

- DART/EDGAR/수집/분석 모듈의 import 방향을 정리해 공개 API import 시점의 순환 의존
  가능성을 줄였다.
- 데이터 매핑 리소스 위치를 `providers/data`와 `reference/data` 기준으로 정리하고,
  wheel 검증·단위 테스트·런타임 로더가 같은 경로 계약을 보도록 맞췄다.
- `dartlab.frame`에서 기존 `from dartlab.frame import dataLoader` 사용 패턴이 계속
  동작하도록 호환 export를 유지했다.
- 수집 캐시 TTL을 환경변수로 조정할 수 있는 범위를 넓혔다.

### Fixed

- PyPI wheel에서 parser mapping, account mapping, notes structure 같은 필수 JSON 리소스가
  누락되면 CI와 release workflow가 즉시 실패하도록 검증을 보강했다.
- `predictionSignals`의 sector prior 로딩이 이전 리소스 위치를 참조하던 문제를 수정했다.
- KR scan builder의 계정 매핑 로더가 필수 번들 리소스 누락을 빈 결과로 숨기지 않고
  명확한 오류로 드러내도록 수정했다.
- sections pipeline에서 projection 적용 결과가 누락될 수 있던 경로를 수정해 markdown table,
  기간 정렬, detail topic 제외 동작을 안정화했다.
- Windows 격리 wheel 검증에서 pip 설치 실패 메시지가 인코딩 문제로 다시 예외를 내던
  문제를 수정했다.
- silent-fail 검사에서 실제 선택적 데이터 경로와 필수 리소스 로더를 구분하도록 보강했다.
- 사이트 배포 빌드에서 Skill 문서의 markdown 문법이 Svelte 파서와 충돌하던 경로를
  정리해 문서 페이지 생성과 링크 변환을 안정화했다.
- finance fixture 검증에서 테스트 로더 캐시가 이전 데이터와 섞일 수 있던 경로를 분리해
  Python 3.13 CI에서도 분기별 현금흐름 기준이 일관되게 검증되도록 했다.

### Migration

대부분 기존 코드 수정 없이 동작한다. 다만 이미 deprecated 상태였던 일부 snake_case alias와
`gather("calendar")` axis dispatch는 제거되었으므로, calendar 사용 코드는 `Company.calendar()`
또는 `dartlab.providers.dart.calendar.predictCalendar`를 사용해야 한다.

## [0.9.27] - 2026-04-30

AI 품질 루프와 데이터 파이프라인 안정화.

### Added

- 신규 상장 종목을 KindList와 HuggingFace parquet 목록 기준으로 bootstrap 하는 DART 수집 workflow 추가.
- 분석 계약 그래프, Workspace ledger, trace summary를 확장해 tool 근거·claim·visual·품질 위반을 더 명확히 기록.
- scan 필드 SSOT와 KRX 벤치마크 기반 quant 비교 축 추가.
- 회사 대시보드에 손익 전환, 재무상태 구조, 현금흐름 브릿지, 근거 커버리지 시각 컴포넌트 추가.

### Changed

- KRX 가격·지수 수집 기준을 장마감 후 당일(T-0) 데이터까지 반영하도록 조정.
- 비교 질문에서 동일 축 근거와 visual 설명을 더 안정적으로 만들도록 runtime preflight 순서를 보정.
- 운영 문서에서 외부 브랜드 의존 표현을 줄이고 DartLab 계약/프로세스 중심으로 정리.

### Fixed

- KRX 일별 데이터의 HF freshness 만료 후에도 서버 프로세스 LRU가 오래된 parquet을 계속 반환할 수 있던 문제 수정.
- 벤치마크 매핑 리소스 로딩 실패가 빈 결과로 조용히 처리되지 않도록 명확한 실패로 전환.

## [0.9.26] - 2026-04-27

스캔 화면과 분석 실행 안정화.

### Added

- `/scan` 화면에 전종목 횡단 데이터 탐색 기능 추가. KRX 가격, 밸류에이션, 공시 변화, 산업지도 데이터를 한 화면에서 조회할 수 있다.
- 스캔 데이터 SQL 탐색 패널 추가. 브라우저에서 DuckDB 기반 쿼리를 실행하고 결과 테이블을 확인할 수 있다.
- 스크리너 결과에 가격 추이, 밸류에이션, 공시 변화 지표를 함께 표시하도록 확장.
- 산업지도 화면에 렌즈 선택과 색상 축 지표를 추가해 업종·공정·역할 기준 탐색을 개선.

### Changed

- `gather("fred", ...)` 다중 조회 처리 속도 개선. 여러 시계열을 받을 때 불필요한 반복 보간과 중간 데이터 보관을 줄였다.
- 매크로 요약 계산의 메모리 사용량 개선. 여러 축을 연속 계산할 때 중간 데이터가 더 빨리 해제된다.
- 랜딩 화면의 숫자·비율·원화 표시 형식을 정리하고, 데이터 로딩 상태와 빈 값 표시를 더 명확하게 조정.
- 자연어 분석 도구가 docstring의 상세 설명을 더 잘 활용하도록 보강해, 지원 가능한 기능과 인자 안내가 더 구체적으로 전달된다.
- EDGAR와 DART의 `show`/`select` 내부 경로를 정리해 동일한 공개 진입점에서 더 일관되게 동작하도록 조정.

### Fixed

- 일부 분석 계산에서 값이 없을 때 `0`처럼 처리되어 결손 데이터가 실제 값처럼 보일 수 있던 문제를 수정.
- `c.story("")`처럼 빈 섹션명을 전달했을 때 전체 보고서 생성으로 자연스럽게 처리되도록 수정.
- 시장별로 지원하지 않는 메서드가 호출될 때 중간에 실패하지 않고 사용 가능한 경로를 안내하도록 수정.
- 브라우저 스크리너에서 DuckDB worker 로딩이 일부 배포 환경에서 실패하던 문제를 수정.
- `riskPremiums` 데이터 경로 보정으로 매크로 리스크 프리미엄 로딩 실패 가능성을 줄였다.
- 베타 계산에서 선택 데이터가 없는 경우 전종목 스캔 데이터 의존 경로가 조용히 실패로 분류되던 검증 문제를 정리.

### Internal

- 재무·매크로·신용·분석 도메인 파일의 import 방향을 정리하고, 공개 API 호환 shim은 유지했다.
- 전체 CI에서 Python 3.13 매트릭스는 호환성 테스트만 수행하도록 조정해 중복 coverage 실행을 제거했다.
- 커밋 메시지 검증 규칙을 강화해 한글 형식과 공개 기록의 불필요한 흔적 차단을 자동 확인한다.

## [0.9.25] - 2026-04-26

내부 안정화 작업.

### Changed

- AI 가 한 번에 여러 도구를 동시에 호출할 수 있어 종합 분석 응답 시간 단축. "삼성전자 전체 분석" 같은 다축 질문이 끊김 없이 완료.
- 같은 종목코드 하나로 ``c.show("BS")`` · ``c.show("IS", freq="Y")`` · ``c.story()`` · ``c.credit()`` · ``c.analysis(...)`` 일관되게 호출되도록 진입점 정리.
- 동일 보고서 두 진입점 노출 (``c.review`` / ``c.story``) 같은 중복 제거. 이제 ``c.story()`` 가 유일 보고서 빌더.

### Fixed

- 일부 AI 응답에서 다축 분석이 중간에 끊기던 문제 해결.
- 노트북 가이드 출력에서 안내한 일부 단축 진입점이 실제로는 동작하지 않던 문제 해결 (``c.show("inventory")`` 등 통합 진입점으로 안내 통일).

### Internal

- 같은 데이터에 두 가지 import 경로가 있던 호환 모듈 제거. 사용자 코드 영향 없음 (사용자 진입점은 ``Company`` · ``dartlab.ask`` · 엔진 함수 그대로 유지).

## [0.9.24] - 2026-04-26 (skipped)

publish workflow 가 PyPI 업로드 전 취소됨. 0.9.25 로 재발행.

## [0.9.23] - 2026-04-25

module-level 엔진 호출계약 일관화. `dartlab.analysis` 도 이제 `stockCode=` 로 종목 지정 가능.

### Added

- `dartlab.analysis.financial("수익성", stockCode="005930")` — 기존 `company=` 외에 `stockCode=` 키워드 수용. `dartlab.credit` · `quant` 와 일관화.
- `Company` 파사드 docstring 격상 — "사람의 최상위 관문" 로서 역할 명시. `ask` 와 투톱 진입점 맥락 기술.

### Changed

- 일관성 규약: 종목 지정 인자 이름 전수 `stockCode` 로 통일 (섹터=`sector`, 시장=`market`). 기존 `company=` (Company 객체 직접 전달) 도 호환.

## [0.9.22] - 2026-04-25

보고서 진입점 이름 변경. `c.story()` → `c.story()` · `dartlab.ask()` 제거 (AI 종합의견은 `dartlab.ask()` 사용). Breaking change.

### Breaking Changes

- `c.story()` → `c.story()`
- `dartlab.ask()` 제거 — AI 종합의견은 `dartlab.ask("...")` 로 일원화
- `dartlab.story` 모듈 → `dartlab.story`
- `Review` 클래스 → `Story`
- `buildReview` → `buildStory` · `renderReview` → `renderStory` · `ReviewLayout` → `StoryLayout`
- CLI: `dartlab review` → `dartlab story` · `dartlab reviewer` 제거
- contextvar: `REVIEW_CURRENCY` → `STORY_CURRENCY`

### Migration Guide

```python
# 기존 (0.9.21)
c = dartlab.Company("005930")
c.story()
ai = dartlab.ask()

# 신규 (0.9.22)
c = dartlab.Company("005930")
c.story()
ai = dartlab.ask("005930 종합 분석해줘")  # reviewer 대체
```

CLI:

```bash
# 기존
dartlab review 005930

# 신규
dartlab story 005930
dartlab ask "005930 종합 분석해줘"   # 기존 reviewer 역할
```

## [0.9.21] - 2026-04-24

quant 엔진 안정화 + 대시보드 재설계 + 접근성 회귀 해소.

### Fixed

- **EDGAR 종목에서 일부 L2 분석 축이 None 이던 문제** — snakeId alias 양방향 확장으로 인텔·애플 등 EDGAR 기업에서 이전에 비어있던 재무 지표가 값을 반환하도록 복구.
- **`/lab` 하위 페이지 내부 링크 깨짐** — GitHub Pages base path prefix 누락으로 배포 prerender 에러가 발생하던 문제. brand href 전수 보정.
- **블로그 2 편 parse 에러 해소** — `silicon2` · `taihan-cable` 포스트의 `<` · `SGA < 15%` 표현이 mdsvex 에서 HTML 태그로 오인되던 문제.

### Changed

- **quant 엔진 팩터 계산 안정화** — accruals · altman · BAB · beneish · earningsSurprise · fundamentalMomentum · piotroski · qFactor · QMJ 9 개 alpha 정비 + factorBuild · spec 일관화. 팩터 반환값 품질 개선.
- **대시보드 페이지 재설계** — `/dashboard/{stockCode}` 를 v2 디자인 토큰 기반으로 단순화, 로드 속도·가독성 개선.
- **review 해석 문장 확장** — narrate 함수가 현금흐름·부채·매출성장 등에서 더 세밀한 조건 분기로 해석 생성.

## [0.9.20] - 2026-04-23

내부 안정화 + 버그 수정.

### Fixed

- **`dartlab.ask()` 가 ECOS / FRED 등 API 키 필요 축을 호출할 때 사용자에게 키 설정 안내가 전달되지 않던 문제** — 이전엔 서버 터미널에만 "키 필요" 로그가 출력돼 landing UI 등에서 호출한 사용자는 원인을 알 수 없었다. 이제 AI 응답 본문에 발급 URL + `.env` 설정법이 직접 포함된다.
- **Windows 터미널에서 한글 로그·가이드 출력이 깨지던 문제** — 기본 인코딩이 `cp949` 인 환경에서 `UnicodeEncodeError` 또는 가독성 저하. `import dartlab` 시점에 stdout/stderr 를 UTF-8 로 자동 재구성한다.
- **`dartlab channel` 실행 직후 host 로그 스레드 크래시** — devtunnel stdout 중계 스레드가 `TypeError` 로 즉시 사망해 `[dt] Connect via browser: ...` URL 출력이 끊기던 문제.

### Changed

- **종목 오타 시 유사 종목 제안** — `Company('삼성전제')` 처럼 오타 입력 시 에러 메시지에 KRX 상장 종목 기반 fuzzy 매칭 top-3 을 함께 안내한다 (초성·편집거리·부분일치 지원).
- **공시 검색 delta 인덱스 · Industry Map · Data Sync 등 일일 데이터 파이프라인 갱신 안정화** — 외부 데이터셋 저장소 업로드 경합으로 간헐적으로 실행이 취소되던 문제 해소. 이제 일일 cron 이 안정적으로 완료된다.

### Added

- **`engines.credit`** — 독립 신용등급 엔진 공개 문서. 7축 구조, `override` 키, 실패 시나리오 정리.

## [0.9.19] - 2026-04-22

내부 안정화 + 버그 수정.

### Fixed

- **`c.analysis("예측신호")` 의 구조변화 감지가 이전엔 항상 None 이었음** — 내부 import 경로가 잘못 설정되어 Chow Test 결과가 silent 하게 버려지던 버그. 이제 `structuralBreak` 필드에 감지 결과가 정상 반환된다.

### Changed

- **섹션 분석 반복 호출 속도 개선** — `c.show("businessOverview")` · `c.analysis("가치평가")` 같이 섹션 매핑을 여러 번 쓰는 분석에서 캐시 적용으로 2회째부터 즉시 반환.

### Removed

- **미사용 내부 모듈 정리** — `dartlab.analysis.financial.research` 하위 `generateResearch` · `buildNarrative` · `calcSectorKpis` 등은 공개 API 로 쓰인 적 없어 제거. `from dartlab.analysis.financial.research import calcPiotroski` 는 계속 사용 가능.

## [0.9.18] - 2026-04-21

### Fixed

- **`c.show()` 라우팅 ValueError 제거**: `c.show("bond")` / `show("business")` / `show("fundraising")` / `show("companyOverviewDetail")` 등 registry 에는 등록됐으나 특정 회사에 데이터가 없는 topic 에서 `ValueError: 'topic 을 찾을 수 없습니다'` 로 크래시하던 문제. 이제 **registered-but-empty** 는 `None` 리턴, **truly-unknown** 만 warning + `None`.
- **`scan("debt")` ComputeError 수정**: polars schema inference 한도(기본 100행)를 넘는 큰 금액 값에서 `could not append value 1.2e11 ... schema mismatch` 로 크래시. `pl.DataFrame(..., infer_schema_length=None)` 로 전체 행 스캔 후 schema 결정.

### Added

- **`tests/test_showRouting.py`** (38 parametrize 테스트): registry 의 report/disclosure topic 전수 iterate 해 `show()` 가 ValueError 없이 DataFrame or None 리턴 확인. `_showImpl` 라우팅 회귀 구조적 차단.

### Changed

- **quality gate baseline**: `ef_count` 196 → 197 (`_showImpl` registered-but-empty 분기 추가로 복잡도 +1, 기능적 가치 대비 수용).

## [0.9.17] - 2026-04-20

### Fixed

- **PyPI wheel 에 `src/dartlab/core/data/` 누락 재발 방지**: `.gitignore` 의 루트-미지정 `data/` 패턴이 `src/dartlab/core/data/` 까지 매치해 `python -m build` 가 해당 디렉토리를 wheel 에서 제외하던 문제. `.gitignore` 를 `/data/` 로 루트-스코프 제한하고, `pyproject.toml` 의 `[tool.hatch.build.targets.wheel]` 에 `include` 명시를 추가해 다중 방어.
- **wheel-smoke 검증 대상과 publish wheel 일치**: 기존에는 wheel-smoke 가 별도로 빌드한 wheel 을 검증하고 publish 는 재빌드한 wheel 을 올려 둘이 달라질 수 있었음. `publish.yml` 의 `build` 잡이 `python -m build` 직후 생성된 wheel 의 zip 목록과 격리 venv 설치 런타임을 직접 검증하도록 변경.

### Added

- **`tests/test_wheelPackaging.py`** (6 테스트): `python -m build` 로 실제 wheel 을 빌드한 후 git-tracked 번들 리소스가 모두 zip 목록에 존재하는지 전수 대조. 핵심 JSON/parquet 개별 확인. 격리 venv 설치 후 `loadSections()` 런타임 체인까지 실행 (heavy 마커 — wheel-smoke job 에서 실행).
- **`publish.yml` 내부 검증 단계 2종**: (1) 빌드 직후 wheel zip 에 필수 리소스 13건 포함 확인 (2) 격리 venv 에 방금 빌드된 wheel 설치 후 `loadSections()["chapterByMajor"]` 비어있지 않음 확인. 실패 시 PyPI 업로드 중단.

### Changed

- **`.github/scripts/testWheelSmoke.sh` 빌드 도구 통일**: `uv build --wheel` → `python -m build` 로 변경해 publish.yml 과 동일 빌드 경로 사용. CI/publish 환경 간 wheel 차이 제거.

## [0.9.16] - 2026-04-20

### Fixed

- **legacy sections 접근 안정화**: `_SectionsSource.raw` 가 None 일 때 `.columns` 속성 접근으로 이어지지 않도록 명시적 가드 추가. 데이터가 비어있는 경우 None 을 그대로 반환.
- **`c.select(...).render("html")` 기간 컬럼 표시**: HTML 렌더의 Console width 를 고정값(120) 대신 컬럼 수에 비례해 동적으로 계산. 기간 컬럼이 많은 재무제표에서도 모든 컬럼이 표시됨.
- **`c.facts` 속성 참조 수정**: `_profile_accessor` 에서 내부 `_report` 대신 존재하지 않는 `report` 를 참조하던 부분 교정.

### Changed

- **필수 매핑 JSON 로더 — 조용한 `{}` 대신 명시적 예외**: `parserMapper.loadSections/loadAffiliate/loadCostByNature`, `core/finance/labels._load_account_mappings`, `dart/edgar/edinet` 의 `sections/mapper.loadSectionMappings` 총 5개 로더가 번들 파일 부재 시 `FileNotFoundError` 와 함께 복구 명령(`pip install -U --force-reinstall dartlab`) 을 포함한 메시지를 발생. 기존에는 빈 dict 반환으로 상위 파이프라인이 원인 불명의 동작을 했음.

### Added

- **`tests/test_bundledResources.py`** (20 unit): 패키지에 포함돼야 하는 JSON/parquet 13건 존재 확인 + 핵심 키(`chapterByMajor`, `detailTopicMap`) 내용 계약 + 런타임 로더(`loadSections`, `loadAffiliate`, `loadCostByNature`, `chapterFromMajorNum(1~9)`) 반환값 검증. PR 마다 실행 (~3초).
- **`tests/realData/` 스위트**: 엔진별 공개 API 를 parametrize 로 전수 iterate. Company 인스턴스 59 공개 속성, analysis 22 axis, scan 20 axis, credit 7 axis, macro 12 axis, gather 8 axis, 최상위 심볼 30+. 각 entry 가 독립 pytest 노드이므로 회귀 시 어떤 항목이 깨졌는지 즉시 특정.
- **`.github/scripts/testWheelSmoke.sh`**: 현재 소스로 wheel 빌드 → 격리 venv 에 설치 → 번들 리소스 존재 + `loadSections()["chapterByMajor"]` 런타임 비어있지 않음 검증. `publish.yml` 의 `build` 잡이 이 스크립트 통과에 의존하도록 wire — wheel 이 비어있는 상태로 PyPI 에 올라가지 않도록 차단.
- **`tests/test-realdata.sh`**: realData 스위트를 파일별 독립 pytest 프로세스로 실행 (Polars 네이티브 메모리 격리 목적).
- **CI 잡 3종**:
  - `fixture-integration` — `test_fixture_*_real.py` 3건을 단일 worker 로 순차 실행 (메모리 격리)
  - `realdata-suite` — realData 스위트 실행 (fixture 데이터 사용)
  - `wheel-smoke` — 격리 venv wheel 설치 스모크
- **pytest 마커 2종**: `realData` (엔진 공개 API 실데이터 스모크), `freshInstall` (cold 캐시 재현)

## [0.9.15] - 2026-04-18

### Changed

- **AI 분석 정확도 향상**: AI 가 각 도구의 반환 구조(키, 타입, 단위)를 호출 전에 파악. `pastInsight` 빈 인자 호출, `show(scope='annual')` 오용 등 기존 런타임 에러 해소.
- **도구 설명 자동화**: docstring 의 Args/Returns 섹션이 tool schema 와 시스템 프롬프트에 자동 반영. 새 함수 추가 시 docstring 만 작성하면 AI 가 즉시 인식.
- **내부 모듈 구조 정리**: `memory/` → `persistence/` 통합. 중복 헬퍼 함수(`_getFirst`, `_get_db`) 단일 출처화. 조건 분기 dict dispatch 로 단순화.

### Removed

- **미사용 레퍼런스/실험 코드 삭제** (-49파일, -22,828줄): `_reference` 폴더 전체. 기존 기능에 영향 없음.
- **미사용 모듈 삭제**: `fallback.py`(미사용 rate-limit 체인), `readiness.py`(미사용 준비 상태 체크), `EDGAR `reviewer()` 메서드`(폐기된 변종 진입점).
- **guide 엔진 축소**: `checkReady`/`whatCanIDo`/`listFeatures` 등 미사용 편의 함수 제거. `handleError` 만 유지.

### Fixed

- **AI 도구 호출 에러 수정**: `pastInsight(stockCode)` 필수 인자가 스키마에 누락되어 빈 호출 crash → 수정. `show(scope=...)` 파라미터 설명 강화로 `scope`/`freq` 혼동 방지.
- **시스템 프롬프트 과잉 규제 제거**: "분석당 tool 4~7회", "최소 4개 축" 같은 숫자 강제 제거. AI 자율 판단 복원.
- **Polars 경고 수정**: `storyValidation.py` None 비교 경고 해소.
- **중복 함수 통합**: `_getFirst` 2곳 → `safe.getFirst` SSOT.

## [0.9.14] - 2026-04-16

### Added

- **가치평가 엔진 고도화**: multi-stage DCF, 청산가치 모델, 상대가치 생존확률 보정. 적정가 계산 정교화 + 시나리오 민감도 확장.
- **생애주기 5단계 자동 판정**: 기업의 현재 생애주기를 데이터 기반으로 자동 판별. 성장/성숙/턴어라운드 등 단계별 가정 차별화.
- **스토리 일관성 검증**: 가정(성장률 ↔ 재투자율 ↔ 마진) 간 교차 모순 자동 감지. AI 가 비현실적 가정 조합을 식별 가능.
- **국가/섹터 리스크 프리미엄**: 자동 산출 + 시장 내재 자본비용 역산 (Gordon 역산). peer 기반 beta 보정.
- **EDGAR bulk 수집 엔진**: companyfacts / dataset 단위 배치 다운로드 + freshness 체크. CI 파이프라인 연동.
- **AI tool schema enum 자동화 완성**: `show.freq` / `search.scope` / `review.type` 하드코딩 제거 → 엔진 상수에서 자동 수집. 축 추가 시 tool 파일 수정 불필요.

### Changed

- **`ai/runtime/core.py` 책임 분리** (797 → 419줄): 시스템 프롬프트 → `runtime/prompts.py` (340줄), post-response 훅 → `runtime/postResponse.py` (72줄). orchestrator 만 core 에 유지.
- **`industry/compat.py` → `industry/sector.py` + `__init__` re-export**: "compat" shim 제거 → 25 소비자 직접 import (`from dartlab.industry import Sector, ...`). 330줄 shim → 0.
- **assumptions 공통 utility `core/overrides.buildAssumptions`**: 4 엔진 (analysis/credit/macro/quant) 에 흩어진 assumption 수집 로직 단일 함수로 통합. 확장 키 전체 자동 포함.
- **post-response 훅 playbook 단일화**: `_updateInsightFromResponse` + regex 상수 → `context/playbook.py::saveInsightFromResponse` 이동. curate 와 한 위치 관리.
- **credit 엔진 4엔진 통일 `_AxisEntry` 패턴 적용**: 기존 plain dict → 구조화 `@dataclass(frozen=True)`. 가이드 DataFrame 표준 컬럼 통일.
- **랜딩 CTA 재정렬**: "Try in Colab" 메인 → "Windows 런처 — 0 setup" 으로 교체. "Live Demo" 제거 (HF Spaces 미사용). Numbers 카드 숫자 줄바뀜 fix.

### Removed

- `ai/superfeature/` 전체 (480줄 dead code — `getSuperMaster` 호출 0건)
- `ai/runtime/standalone.py::analyze_full` (사용처 0)
- `ai/tools/_builtin.py` (수동 AITool 생성 → `_autoDiscover` 자동 등록 대체)
- `review/presets.py` (deprecated re-export shim)
- `core/engines_DEV.md` (dev 문서 src 안 잔재)
- pyproject.toml `Demo` URL (HF Spaces → `Desktop` Windows 런처로 교체)
- `_MODULE_CORE` 수동 whitelist (`_splitKwargs` → 시그니처 자동 추출로 대체)
- `_aggregateAssumptions` / `_buildCreditAssumptions` 엔진별 중복 (→ `buildAssumptions` 통합)

### Fixed

- **대형 기업 메모리 보호**: `core/memory.py` pinned prefix 확장 — 대형 종목 (한국전력 등) 에서 메모리 압박 시 dualAccess accessor evict → 다음 select/show KeyError 방지.
- **`analyze` → `runAsk` rename 누락** (`scorecard.py::calcScorecard`) — CI 10건 실패 원인 1곳 수정.

## [0.9.13] - 2026-04-15

### Added

- **P8 Tool Zero 응답 금지** (`ai/context/intent.py::classifyCategory`): 질문을 META / FINANCE / OUT_OF_SCOPE 3범주로 분류. FINANCE 범주는 tool 최소 1회 호출 필수 (시스템 프롬프트 블록 + `tool_choice="any"` 첫 라운드 API 강제 + 런타임 가드 3중 방어). META 는 tool 불필요 (CAPABILITIES 로 즉답), OUT_OF_SCOPE 는 "dartlab 전문 영역 아님" 명시 + 금융 질문 예시 제시 후 종료. dartlab 엔진 경유 없이 일반 ChatGPT 답변 생산 불가.
- **매크로 톱다운 intent 분기** (`ai/runtime/core.py::_mandatoryForOutlook`): "최근 경제 어때" 같은 시장 레벨 질문에서 `macro() + gather(axis='news')` 조합 강제. 수치 + 최근 이슈 교차 인과 해석. 이전 `act_all` 로 잘못 분류되어 일반론 답변되던 문제 해결.
- **`pastInsight(stockCode)` / `sectorInsights(sector)` 공개 API**: `dartlab.__all__` 에 노출 → AI tool 자동 등록 경로 (`_autoDiscover`) 진입. 사용자도 `dartlab.pastInsight("005930")` 직접 호출 가능.
- **`ai/context/intent.py::Category` enum**: META / FINANCE / OUT_OF_SCOPE 상위 범주. 기존 8 intent (act1~6 / compare / concept) 와 병렬.
- **provider `tool_choice` 파라미터**: `BaseProvider.complete_with_tools/stream_with_tools` 에 `tool_choice: str | None` 추가. "any"/"none"/"auto" 매핑. FINANCE 첫 라운드에만 "any" 강제 후 auto 로 환원.

### Changed

- **`ai/runtime/core.py::analyze` → `runAsk`** / `_analyze_inner` → `_runAskInner`. 구 "떠먹이기 시대" 이름 제거. `dartlab.ask()` 진입점 단일 (P1) 을 내부 이름으로도 선언.
- **`analysis/financial/insight/pipeline.py::analyze` → `analyzeFinancial`**: AI 엔진 `runAsk` 와 이름 충돌 해소. 인사이트 엔진 코어 함수 의미 명확화. `analyze` 는 호환 alias 로 1 릴리즈 유지.
- **AI tool 자동 등록 우선순위**: module-level > Company-bound (이전 반대). 같은 이름 존재 시 `dartlab.search` (시장 전체) 가 `Company.search` (이 회사 공시) 보다 AI tool 로 유용. Company-bound 는 module 에 없는 것만 등록.
- **`_splitKwargs` 자동 시그니처 추출**: 기존 `_MODULE_CORE` 수동 whitelist (scan/macro/search/searchName) 제거. `inspect.signature(fn)` 으로 자동 추출 → pastInsight/sectorInsights 포함 모든 module-level tool 일관 처리.
- **`Company.gather` 시그니처 `target: str | None = None` 명시**: 이전 `**kwargs` 에 숨어 tool schema 누락. AI 가 `gather(axis='news', target='한국 경제')` 로 시장 레벨 뉴스 검색 가능해짐.
- **src/dartlab/ai/README.md P8 섹션 신설**: 3범주 분류 + 3중 방어선 단일 출처.

### Removed

- **`ai/superfeature/`** 폴더 전체 (480줄, 4파일) — `getSuperMaster` 호출 0건 (내부 순환만). 완전 dead code.
- **`ai/runtime/standalone.py::analyze_full`**: `list(analyze(...))` 래퍼, 사용처 0.
- **`ai/tools/_builtin.py`**: pastInsight/sectorInsights 수동 AITool 생성 파일. `_autoDiscover` 자동 경로로 일원화.
- **`review/presets.py`**: `reportTypes.py` 로 통합된 deprecated re-export shim, import 0건.
- **`core/engines_DEV.md`**: dev 문서가 src 안에 있던 것.
- **`ai/runtime/standalone.py` 에서 `from dartlab.ai.runtime.core import analyze`** 등 낡은 import 15곳 갱신 (CLI, stdio, server/streaming, scripts/audit, scripts/eval).

### Fixed

- **AI 가 매크로 질문에서 tool 0회 일반론 답변**: v0.9.12 에서 "최근 경제 어때" 질문에 `macro()` 호출 없이 학습 지식으로 답한 사고 — P8 3중 방어선으로 구조적 불가능화. `dartlab.ask("최근 경제")` 재현 테스트: tool 3회 (macro summary + gather news × 2), CLI/M2/기준금리/공포탐욕/uncertainty 실측 수치 기반 답변 확인.
- **`Company.gather` `target` 파라미터 AI schema 누락**: `**kwargs` 에 숨어 AI 가 시장 레벨 뉴스 검색 인자 못 넣음. 시그니처 명시로 해결.
- **`_builtin.py` 가 `_MODULE_CORE` 경로 밖이라 라이브 호출 시 stockCode 누락**: `_splitKwargs` 자동 시그니처로 근본 해결.

## [0.9.12] - 2026-04-15

### Added

- **엔진 자가 의심 flags** (`core/overrides.py::detectExtremeFlags`): WACC>15%/<6%, Kd>12%, terminalGrowth>4%/≤0, debtRatio>200%, ICR<1.5, cycle contraction-trough 룰을 엔진이 자동 검사 → `{flag, reason, suggestedRetry}` 리스트로 결과에 박음. AI 가 verbal 시뮬로 도망가지 않고 구체 JSON 복사 수준으로 override 재호출.
- **autoEnrich `[엔진가정]` 한 줄 자동 주입**: 모든 tool_result `_summary` 끝에 `[엔진가정] WACC=10.4% · g=3.0% · Kd=15.0% ...` 줄 자동 추가. flag 가 있으면 `⚠ {reason} → 다음 호출 실행 권장: overrides={"wacc":9.0}` JSON 동봉.
- **4엔진 결과 표준 `assumptions` 필드**: analysis (FORECAST + VALUATION + ANALYSIS) / credit / macro / quant 결과에 엔진이 쓴 가정값을 표준 키(`wacc`, `terminalGrowth`, `debtRatio`, `cyclePhase` 등)로 통합. AI 가 흩어진 `discountRate`/`baseWacc`/`assumedWacc` 추측 불필요.
- **`pastInsight(stockCode)` / `sectorInsights(sector)` AI tool**: KnowledgeDB 경험 조회 — 블로그(검증 프리미엄) 우선, 없으면 AI 축적. 떠먹이기가 아니라 AI 자율 호출. 식품 업종 분석 시 불닭 OPM 21.8% 같은 과거 인사이트 자동 인용.
- **AI tool 자동 등록 (`_autoDiscover`)**: `dartlab.__all__` + Company `_xxxImpl` / public method 자동 순회 + 블랙리스트. 수동 `_TOOLS` dict 제거. quant 누락 해결, 새 엔진 추가 시 자동 등록.
- **`core/overrides.py` 확장**: `ANALYSIS_KEYS`/`QUANT_KEYS` 신설, `CREDIT_KEYS`/`MACRO_KEYS` 확장 (currentRatio/quickRatio/ocfToDebt/scenarioStress, rateScenario/fxScenario 등). `ENGINE_KEYS` dict 으로 엔진별 허용 키 명시. `describeOverrides(engine)` — tool schema description 자동 생성.
- **`/insights` 자동 인사이트 랭킹 페이지** (랜딩): 5종 랭킹 (집중도/분산/허브/다양성/의존도).
- **`/compare?a=X&b=Y` 2사 비교 페이지**: 공급망/재무/AI verdict 나란히.
- **`/industry/[id]` 공정 흐름 + 랭킹 + 공급망 엣지** 페이지.
- **회사 페이지 풀스택** (`/map/company/[code]`): AI 인사이트 + 공급망 + 재무 + 블로그.
- **Cosmograph WebGL 산업 지도** (`/map`): 살아있는 산업 생태계.
- **L3 Egograph 공급망 시각화**: 회사별 공급망 그래프.
- **네이버 글로벌 API 도입** (gather): US 주가 Yahoo → Naver Global 전환, 호출 간 2~4초 강제 딜레이.
- **원재료 테이블 파싱**: 실제 공급망 엣지 261건 추출, revenue 2,469사 join, edges/summary/timeline API.
- **DART 데이터셋 자동 수집 구조 블로그**: Actions 리듬 + HF 단일 소스 + 사용자 한 줄 경험.
- **블로그 #34 LG전자**, **#35 Under Armour**.
- **빠른 품질 audit 스크립트** (`scripts/audit/quickQualityAudit.py`): tool 다양성 + override 자발 호출 + pastInsight 활용 4 시나리오 검증.

### Changed

- **모든 엔진 `_Impl` 시그니처 통일** — `overrides: dict | None = None` 명시. credit/quant/macro 추가 (이전엔 analysis 만 수용).
- **src/dartlab/ai/README.md 구조 정리** (596줄 → ~280줄): 4축 사상 + 7+1 원칙 (P1~P7 + P4.5) + override 매커니즘 + 경험 자산화 순환 단일 출처. 메모리 (MEMORY.md, ai_identity.md) 는 포인터만.
- **시스템 프롬프트** — override 재호출 예시 명확화, "verbal stress 금지, 반드시 overrides 인자로 재호출" 명시.
- **macro 모듈 callable 패치** — import 순서 무관 callable 보장.
- **Node.js 24 대응** — actions 메이저 버전 일괄 bump (checkout@v5, setup-python@v6, setup-node@v5, upload-artifact@v5, attest-build-provenance@v3).
- **ruff format** 92개 파일 적용.

### Fixed

- **CRITICAL: `memoized_calc` 가 `overrides` 를 silent drop** — 모든 valuation/credit/quant calc 함수에서 override 가 캐시 래퍼에 의해 무음 무시되던 버그. 이제 override 가 실제 calc 함수에 전달되고, override 있을 때 캐시 우회. **override 매커니즘이 이번 릴리즈부터 처음으로 실제 작동.**
- **`calcDcf` `terminalGrowthRate` vs `terminalGrowth` 키명 오타** — inner `dcfValuation()` 은 `terminalGrowth` 받는데 래퍼가 `terminalGrowthRate` 로 넘김 → TypeError silent swallow → DCF None 반환되던 버그.
- **analysis tool axis enum 누락** — docstring 파싱이 14 financial 축만 뽑아 `가치평가`/`매출전망`/`매크로민감도` 등이 enum 에서 빠짐 → AI 가 호출 자체 불가. `_AXIS_REGISTRY` 전체 22축으로 교체.
- **시스템 프롬프트 `{{"wacc":9.0}}` 이중중괄호** — Python format string 흔적이 AI 에게 그대로 노출 → AI 가 `sub="{...}"` 에 JSON 문자열 욱여넣음. 깔끔한 JSON 예시 + "sub 에 절대 쑤셔 넣지 마라" 지시 추가.
- **EDGAR 전면 점검**: stmt 분류 + STMT_OVERRIDES 확장, 한국어 100% 로드, analysis/valuation/credit RuntimeError catch, CI 항목 7개 IS→CI stmt 수정, EQ/NT canonStmt 필터, getAccountStmt alias 역참조, dividends_common_stock EQ 수정. 7종목 42케이스 전부 OK.
- **EDGAR `show()` 항목 한국어 근본 개선** — standardAccounts korName 로딩 + Title Case fallback 제거.
- **review Section UnboundLocalError** (pyodide 환경 순환 참조).
- **landing basePath/handleHttpError**: BASE_PATH prefix 고려, peer 링크 prerender 통과.
- **map 필터 실시간 반영 + 회사명 라벨 + Cosmograph API 정정**.
- **kindlist 워크플로우 시크릿 이름 불일치** — `DART_API_KEYS` 에서 첫 키 추출.
- **블로그 데이터셋 글 내부 링크** — slug 번호 없이.

### Removed

- **AI tool 수동 `_TOOLS` dict** — `_autoDiscover()` 자동 등록으로 대체.
- **폐기 기능 유령 테스트** — sector 호환 partial source / 지주사 skip / repr 정리.

## [0.9.10] - 2026-04-13

### Added

- **AI 적극 개입 레이어**: CoT 4단계(추세→비율→근거→판단) + Direction/Magnitude/Confidence 구조화 판단. AI가 엔진 결과를 원본 재무제표로 직접 검증하고, 이상 시 override로 재계산
- **analysis() overrides 전파**: `c.analysis("가치평가", overrides={"wacc": 9.0})` — calcDcf/dFV에 wacc/terminalGrowth/primaryModel override 지원
- **블로그 경험 생태계**: frontmatter `ai:` 블록(verdict/strengths/weaknesses/keyMetrics)으로 블로그가 AI 경험 저장소. sync_blog_insights.py로 KnowledgeDB(source="blog") 자동 파생. blog insight 우선 조회
- **KnowledgeDB get_insight(source=)**: blog source 우선 조회 파라미터 추가

### Changed

- **시스템 프롬프트 클린코드**: 191줄→172줄, 중복 가이드 50줄 제거. "너는 분석가다" 핵심에 집중
- **분석 깊이 강제**: 한 축만 보고 끝내지 말고 원인 축(비용구조/수익구조) + 원본 검증 필수
- **notes 적극 활용**: borrowings/inventory 등 BS/IS 이면의 항목별 분해 가이드
- **엔진/review/AI 역할론 확립**: ops 문서(architecture/ai/review/analysis) + README 전체 반영

### Removed

- **financials.py**: AI가 `c.select()`로 직접 하면 되므로 보조 레이어 삭제
- **assumptions.py**: AI가 스스로 판단해야 하므로 시스템 대행 삭제

## [0.9.9] - 2026-04-12

### Added

- **Pyodide 브라우저 실행**: `micropip.install("dartlab")` 한 줄로 브라우저/xlwings lite/JupyterLite에서 dartlab 사용. `sys_platform != 'emscripten'` 환경 마커로 native deps 자동 제외. Company → show → analysis → review 전체 경로 동작 확인
- **dFV (dartlab Fair Value)**: 4엔진 통합 적정주가 — DCF Anchor + 삼각검증(DDM/상대가치/Residual Income) + Quality WACC. `c.analysis("valuation", "가치평가")` 진입
- **AI Override 매커니즘**: analysis calc 결과를 AI가 자체 판단으로 보정 — mid-cycle 정규화, 성장률 상한, 할인율 조정 등 4엔진(analysis/macro/quant/credit) 확산
- **How축 상황별 개선 레버**: 적자/턴어라운드/현금부자/사이클/고성장 5종 분기, 기업 상황에 맞는 재무 개선안 자동 제시
- **추정재무제표 → DCF 연결**: proforma FCF 우선 사용, 3년이라도 터미널 성장률로 연장
- **블로그 인터랙티브 차트**: Svelte ComboChart(매출 라인+영업이익 막대) + sync_financials.py 자동 데이터 동기화
- **블로그 8편 발간**: #21 현대모비스, #22 SK텔레콤, #23 GS건설, #24 현대코퍼레이션, #25 한국전력, #26 에코프로, #27 쿠팡(EDGAR 첫 미국 주식), #28 현대자동차
- **검색 scope 분리**: `scope="title"` (ngram, 제목형) + `scope="content"` (BM25, 본문형) 독립 엔진. main/delta 세그먼트 증분 전략
- **EDGAR Phase 4**: treasuryStockStatus XBRL fallback, 매일 2회 수집, sectorKpi EDGAR fallback
- **업종별 KPI 4모듈**: sectorKpi — 업종 특성에 맞는 핵심 지표 자동 선택

### Changed

- **review reportType 단일축 통합**: perspective/preset/template 3단계 → reportType 1축으로 통합. 11종 보고서 타입 (full/executive/credit/valuation/growth/crisis/audit/dividend/governance/macro/thesis)
- **review 4종 신규 타입**: dividend(배당 지속성), governance(임원보수 괴리), macro(사이클+역사적 팩트), thesis(가설→증거→판정)
- **pyproject.toml 환경 마커**: server/AI/viz deps에 `sys_platform != 'emscripten'` — pyodide에서 자동 제외, 일반 환경 영향 없음

### Fixed

- **review Section UnboundLocalError**: pyodide 환경에서 순환 참조로 인한 import 실패 수정
- **메모리 최적화**: scan lazy 컬럼 선택, macro 실패 방어, improvementLevers BoundedCache 압박 회피
- **블로그 실측 수치 재검증**: #15/#17/#19/#20/#22/#23 오류 5건 수정, 전 26편 H3 소제목 추가

## [0.9.8] - 2026-04-12

### Added

- **매크로 역사적 팩트 엔진** (`core/finance/historicalContext.py`): HY 스프레드 급등/YC 역전/실업률 반등/CPI 가속 시점별 침체 선행 통계, 호황 신호, 10개 역사적 시대 매칭, 현재와 유사한 과거 시기의 후속 위험 자동 추론
- **매크로 시나리오 시뮬레이션 110개 프리셋** (`macro/scenarios/`): 역사적 재현 15 (1973 오일쇼크 ~ 2023 SVB), Fed DFAST 3단계, 유형별 × 심각도 24, 현대적 리스크 24 (AI 버블/중국 디플레/일본식 침체/대만 해협/무역전쟁/미국 국채), 구조적 20 (스태그플레이션/디플레이션/골디락스/경착륙/연착륙), 한국 특화 24 — `dartlab.macro("시나리오", "2008 금융위기")` 호출로 baseline 대비 자동 비교
- **매크로 6막 인과 서사 구조**: "경제는 어디에 있나 → 왜 여기에 있나 → 정책은 → 금융은 → 시장은 → 앞으로는" — FOMC/ECB/Bernanke/Dalio 학술 근거
- **core SSOT 헬퍼 이동**: `toDictBySnakeId`, `toDict`, `parseNumStr`, `sumBorrowingsKorean` 등 범용 재무 헬퍼를 `core/finance/helpers.py`로 이동. `memoized_calc`를 `core/memory.py`로 통합
- **analysis 임계값 중앙 관리** (`analysis/financial/_constants.py`): OCF/NI, 발생액, R², FX 민감도 등 6개 임계값 SSOT
- **core/finance/fmt.fmtBig 확장**: 조/억/만 자동 단위 전환 + None 처리

### Changed

- **엔진 책임 재정의 — 6레이어 구조 확립**: `L0 core ← L1 providers/gather ← L1.5 scan ← L2 analysis/quant/credit/macro ← L3 review ← L4 ai+사람`. L2 엔진 4개는 동등하고 상호 독립, review가 이야기꾼, AI/사람이 소비자
- **엔진 = 도구, review = 이야기꾼**: L2 엔진은 dict/숫자만 반환. 해석 문장/Block/보고서 생성은 review(L3)의 책임
- **macro 보고서 조립을 review로 이동**: `macro/narrative.py`, `macro/mbuilders.py`, `macro/mcatalog.py`, `macro/report.py`, `macro/charts.py` → `review/macro/` 하위 패키지로 물리 이동
- **quant 서사 함수 분리**: `calcXxxNarrative` 6개를 `calcXxxData` (숫자만)로 교체. 서사 생성은 `review/registry.py`가 담당
- **import 위반 26건 → 0건**: L2↔L2 상호 import 0건, L2→L3 역방향 import 0건 달성 (CI 검증)
- **macro API 통합**: `macro.report()`, `macro.scenario()` 별도 메서드 제거 → 축 계약 `macro("시나리오", "2008 금융위기")` 로 통일
- **SSOT 위반 정리**: 숫자 파싱 5곳 중복, `_safe` 나눗셈 2곳 중복, 포맷 함수 3곳 중복, `_memoized_calc` 중복 구현 → 전부 core SSOT 경유

### Removed

- **`macro/narrative.py`, `mbuilders.py`, `mcatalog.py`, `report.py`, `charts.py`**: review/macro/로 이동
- **`credit/publisher.py`**: deprecated, review.publisher가 단일 진입점
- **`analysis/financial/creditRating.py`**: deprecated stub, `credit/calcs.py`가 SSOT
- **quant의 `calcTrendNarrative` 등 6개 함수**: `calcTrendData` 등으로 대체

### Fixed

- **macro `recessionDashboard`** `historicalFacts` 필드 추가 — 규칙 기반 "resembles_2008" → 역사적 팩트 dict 기반 매칭
- **analysis → quant/credit 교차 의존 제거** (valuation 내 quant 참조, creditRating의 credit 호출)
- **credit 엔진의 analysis._helpers 의존 제거** → core 경유
- **macro/\_\_init\_\_.py** _AxisEntry에 `act: int` 필드 추가 — 6막 메타데이터 선언적

## [0.9.7] - 2026-04-11

### Added

- **AIView 정량 데이터 보강**: `autoEnrich()` — calc 결과에 5년평균/YoY/백분위 자동 주입. AI가 "영업이익률 13%"만 보던 것에서 "전기비 +2.2pp, 5년평균 위 1.2pp" 맥락까지 이해
- **Returns 독스트링 표준화**: analysis 전 calc 함수에 numpydoc 표준 Returns (키:타입—설명(단위)) 적용. parseReturnsSchema() → autoEnrich 자동 연결
- **예측신호 고도화**: 업종별 사전확률 41개 + 베이즈 연속 확률 + 매크로 민감도 매핑
- **DART/EDGAR Company**: notes 12항목 동기화, show/select 인터페이스 통합

### Fixed

- predictionSignals: 패키지 설치 환경 경로 호환 (parents[4]→parents[2])
- standalone.py: deprecated `use_tools` 파라미터 제거

## [0.9.6] - 2026-04-10

### Added

- **Context Engineering + ACE Playbook**: `ai/context/` 모듈 — intent 분류(8타입, 100% 정확도), TOON 인코딩(토큰 60% 절감), ACE(ICLR 2026) evolving playbook, analysis calc selector 8개, 인과 그래프 traversal. A/B 검증 +31.6% 응답 풍부도
- **Causal Graph**: `core/graph/` — 6 노드 + 5 엣지 타입. Company × analysis calc → CompanyGraph. "왜" 질문 시 graph causes 자동 주입
- **5엔진 review 체계**: quant 5 narration 블록(6막-3 시장분석) + macro 10 블록(6막-4 매크로)
- **관점별 템플릿**: bottomUp/topDown/cashflow/stability/growth 5개 분석 관점
- **macro narration**: crisis/cycle/rates/sentiment/summary 블록 함수
- **FinSLM 파이프라인 스크립트**: extractTraining/extractGraph/formatDataset/evalBaseline/trainLoRA/deploy (인프라)

### Fixed

- **이벤트성 계정 연간 합산 복원**: Plan v4 "4분기 strict 합산"이 배당금/자사주 등 이벤트성 계정도 잘라버린 문제 근본 fix. `_EVENT_ACCOUNTS` 14개 계정은 있는 분기만 합산
- **notes 외화 차입금 파싱**: NAVER "합계 128,659조" → 1.7조 정상화. 외화 통화코드 필터(`_hasForeignCurrency`) + 같은 항목명 반복 시 첫 번째 원화 값 우선
- **notes 비금액 행 필터**: "연이자율 33만" → 제거. `_isNonAmountRow`로 이자율/기술/설명 행 제외
- **DCF FCF 단위**: "Y1 22만" → "Y1 22(조원)" 정상화
- **매출품질 총이익률 추세**: 기간 라벨 없는 숫자 나열 제거 → 방향만 표시
- **지주사 영업이익률 100%+**: "데이터 이상 가능" → "매출 대비 영업이익이 크다 (지주사 구조일 수 있음)"
- **context 데이터 중복 조회 방지**: `<context>` 태그에 이미 데이터 있으면 코드 재실행 안 함
- dependencies: openai/genai core에서 optional로 이동
- provider/CLI/viz 소소 개선

### Changed

- **ContextBuilder 기본 ON**: `DARTLAB_CONTEXT_V2` feature flag 제거. legacy 복원은 `DARTLAB_CONTEXT_V1=1`
- **축수 자랑 표기 전면 제거**: Skill OS코드에서 "14축/30축/7축" → 기능 설명으로 변경
- **audit 체계 통합**: 파편 audit 10개 삭제, review audit 1개로 통합 (src/dartlab/review/README.md)
- review audit Fix 원칙 명시: 근본 1곳만, 우회로/덕지덕지 금지

## [0.9.5] - 2026-04-09

### Fixed

- ratio label dict 중복 key 정리 (F601) — 카테고리별 재정렬
- ruff lint 16건 (unused imports, f-string placeholder)
- qualityGate.py _HISTORY_PATH 새 위치 (`scripts/audit/`) 반영

## [0.9.4] - 2026-04-09

### Fixed — Plan v10 후속 audit fix

- **NAVER 등 IT/플랫폼 archetype 오분류 수정**: `_detectArchetype()` 가
  `operating_expenses` 단일 사용 + `financial_assets_*` 보유 IT 기업을 `securities`
  로 잘못 분류 → 유동비율/이자보상배율 등 모두 None 처리되던 버그.
  - `_GENERAL_IS` 에 `operating_expenses` 추가
  - BS general signature (재고/매출채권/유형/무형) 추가
  - max_score 임계값 3 → 4 (금융업 확정 더 보수적)
  - 결과: NAVER `currentRatio` None → 136.28, `cashRatio` None → 74.62

- **`accountMappings.json` core SSOT 이동**: `providers/dart/finance/mapperData/`
  → `core/data/`. L0 ← L1 import 방향 정합. `AccountMapper` 가 core 의
  `_load_account_mappings()` 위임. test_mapping_integrity 경로 갱신.

- **`_KR_SUPPLEMENTS` 데이터 파일 SSOT**: 28건 하드코딩 → `core/data/labelSupplements.json`
  로 분리. `get_korean_labels()` 가 `_load_label_supplements()` 위임.

- **ratios DataFrame 라벨 5건 보충**: ROE/ROA/FCF/ROIC/Debt/EBITDA 한국어 병기
  ("자기자본이익률 (ROE %)" 등). 잔존 3건 (ROCE/Piotroski F-Score/Altman Z-Score)
  은 학술 영문명.

- **메모리 한계 1500/1900MB**: PRESSURE_CRITICAL 1200 → 1500, PRESSURE_FATAL 1600
  → 1900. CI PYTEST_MEMORY_LIMIT_MB 1500 → 1900.

### Changed — scripts 폴더 체계화

5개 카테고리 분류:
- `scripts/build/` — 산출물 생성 (buildNotebooks, generateSpec, generateFixtures, ...)
- `scripts/audit/` — 품질 게이트 (auditBlog, qualityGate, validateNotebooks, check_no_ai_markers, ...)
- `scripts/eval/` — 평가/예측 (backtestPrediction, evalDiagnose, runEvalBatch, scanInsights, ...)
- `scripts/data/` — 데이터 수집/복구 (collectIndustryIndicators, repair_cache_with_progress, ...)
- `scripts/dev/` — 개발자 헬퍼 (test-lock.sh, install_git_hooks.sh, ...)

영향: workflow yml, conftest, Skill OS*, .claude/audits, .claude/skills, .claude/hooks 모두 경로 갱신.

## [0.9.3] - 2026-04-09

### Changed — Plan v10: 1.0.0 전 클린업 (BREAKING)

**API contract 단일 진입점 원칙 강제** — 사용자 surface 를 `c.show() / c.select() / legacy sections view / c.diff() / c.filings() / c.facts / c.story() / c.analysis() / c.credit()` 만으로 단일화.

**P0 — finance property 4종 제거**:
- `c.IS / c.BS / c.CF / c.CIS` (DART + EDGAR) → `c.show("IS")` / `c.show("BS")` / `c.show("CF")` / `c.show("CIS")`

**P1 — ratios/SCE property 제거**:
- `c.ratios / c.ratioSeries / c.SCE / c.sceMatrix` → `c.show("ratios")` / `c.show("ratioSeries")` / `c.show("SCE")` / `c.show("sceMatrix")`

**P2 — notes 12 sub-property 제거**:
- `c.notes.inventory` / `borrowings` / `tangibleAsset` / `intangibleAsset` / `receivables` / `provisions` / `eps` / `segments` / `costByNature` / `lease` / `affiliates` / `investmentProperty` → `c.show("inventory")` 등 12 topic dispatch

**P3 — 4 namespace 전면 제거**:
- `c.docs / c.finance / c.report / c.profile` (DART + EDGAR) public 접근 0
- 사용자 surface 에서 namespace 4종 완전 제거
- `c.facts` 신설 (이전 `c.profile.facts`)
- legacy sections view / `c.diff()` / `c.trace()` / `c.filings()` 는 top-level 유지 (sections 사상 핵심)
- 내부 compute (review/credit/valuation/analysis) 는 `c._docs / _finance / _report` private 백엔드 사용 — 데이터 형식 차이 (RatioResult 객체 vs DataFrame) 로 show() 흡수 불가

**P4 — Plan vN 마커 정리**: Plan v3~v9 / R26 마커 38곳 수동 정리.

**P5 — finance DataFrame 컬럼 단일화**:
- `계정명` 컬럼 완전 제거 → `항목` 단일화 (sections 사상 정합 — `topic × period × 항목` 3차원)
- 197 ref 마이그레이션, alias backward-compat 도 제거 (1.0.0 전 breaking 허용)

**P6 — label SSOT 통합**:
- `core/finance/labels.py::get_korean_labels()` 가 snakeId → 한국어 라벨 단일 진실의 원천
- `AccountMapper.labelMap()` 은 한 줄 위임으로 축소 (이중 매핑 함수 통합)
- L0 ← L1 import 방향 유지 (provider → core)

### Migration

```python
# Old                            # New
c.IS                              c.show("IS")
c.BS / c.CF / c.CIS               c.show("BS") / c.show("CF") / c.show("CIS")
c.IS_annual                       c.show("IS", freq="Y")
c.timeseries()                    c.show("IS")
c.annual                          c.show("IS", freq="Y")
c.cumulative                      c.show("IS", freq="YTD")
c.ratios                          c.show("ratios")
c.ratioSeries                     c.show("ratioSeries")
c.SCE / c.sceMatrix               c.show("SCE") / c.show("sceMatrix")
c.notes.inventory                 c.show("inventory")
c.notes.borrowings                c.show("borrowings")
c.docs legacy view                current panel view
c.docs.diff()                     c.diff()
c.docs.filings()                  c.filings()
c.finance.ratios                  c.show("ratios")
c.report.dividend                 c.show("dividend")
c.report.majorHolder              c.show("majorHolder")
c.profile.facts                   c.facts
c.profile.trace(topic)            c.trace(topic)
c.profile legacy view             current panel view
df["계정명"]                       df["항목"]
```

unit tests: 2065 → 2066 passed (Plan v10 전체).

### Changed — 헬퍼 단일 진실의 원천 (SSOT) 통합

- **`core/finance/flow.py::synthesizeAnnualFromQuarters`** 신설 — 분기 → 연간 합성 SSOT.
  `toDict`, `toDictBySnakeId`, `_financeToDataFrame` 모두가 위임.
- **`core/finance/labels.py::mergeAliasRows`** 신설 — SNAKEID_ALIASES 양방향 row 머지 SSOT.
  pivot DataFrame 머지와 calc dict 머지 모두 단일 함수 호출.
- `analysis/financial/_helpers.py` 의 `_synthesizeAnnualInPlace` 인라인 머지 로직 제거 → SSOT 위임.
- `providers/dart/_finance_helpers.py::_financeToDataFrame` 의 인라인 머지 로직 제거 → SSOT 위임.
- 결과: 이중/삼중 매핑 경로 정리, 규칙 변경 시 단일 파일만 수정.

### Added — Plan v7 부채 청산 (5 commit, R0~R8)

- **annual 컬럼 옵션화**: `c.IS / c.BS / c.CF / c.CIS` 기본 분기만 노출.
  연간 합성은 `toDictBySnakeId` 가 4분기에서 자동.
- **CF derived row 통합**: `financing_cashflow` ↔ `cash_flows_from_financing_activities`
  같은 alias 쌍을 pivot 에서 한 row 로 머지 (SK하이닉스 2025 재무CF 결손 해결).
- **toDict → toDictBySnakeId 단일 경로 마이그레이션**: 14 calc 파일 + credit/engine + review/narrative.
  한국어 라벨도 키로 노출하여 양 provider 호환.
- **except narrow**: 11 곳 `except Exception:` → 구체적 예외로 좁힘.
- **F841 unused variable**: 120 곳 자동 정리.
- **dict literal `or 0`**: 결과 dict 노출 위치 None 보존 (scan/macroBeta, scan/network/export).
- **credit/metrics docstring**: `_div`, `_cv`, `_isQuarterlyFallback` 9 섹션 보강.

## [0.9.2] - 2026-04-07

### Added

#### channel 엔진 — 외부 공유 정식 엔진 (DevTunnels)
- **`dartlab channel`**: 한 줄로 PC dartlab을 폰에서 사용. Microsoft DevTunnels 기반 (VS Code Remote Tunnels와 동일 인프라).
- **자동화 파이프라인 7단계**: winget 자동 설치 → GitHub OAuth → tunnel 생성 → anonymous access → port mapping → host 시작 → URL/QR 출력
- **영구 URL**: `https://<id>-8400.<region>.devtunnels.ms` — 재실행해도 동일
- **모바일 호환 검증**: Android Chrome (2026-04-07)
- **메시징 봇 옵션**: `--telegram/slack/discord` (channel/adapters/)
- **runtime.channel**: 기술 스택, 자동화 파이프라인, 검증된 진단 사례 전부 문서화

### Removed

- **share 명령 → channel 통합**: `dartlab share` deprecated 별칭 제거
- **Cloudflare Quick/Named Tunnel 백엔드 삭제**: 모바일 fetch hang / 도메인 필수 사유. devtunnel만 정식
- **ngrok / ssh / Tailscale 백엔드 삭제**
- **`server/security.py` 삭제**: TokenManager/Whitelist/Ratelimit/AuditLog/AnomalyDetector. devtunnel은 미들웨어 비활성
- **UI 죽은 코드**: ActivityBar, DebugOverlay, debug.js, token.js, SettingsPanel 채널 탭

### Fixed

- **모바일 hydration 실패**: lucide-svelte의 deprecated `<Settings>` 아이콘 → `<Cog>` 일괄 교체. 진짜 원인이 8시간 추적 끝에 발견됨 (상세: runtime.channel "검증된 진단 사례")
- **Svelte 5 버전**: `vite-plugin-svelte 5.0 → 6.2.4` + `svelte 5.0 → 5.55.1`
- **Svelte 5 body event delegation**: ProviderDropdown의 `stopPropagation()` 제거, `document.addEventListener` 직접 사용
- **모바일 반응형**: EmptyState/ChatArea 풀너비, 우상단 검색 모바일에서 숨김, 하단 nav `position: fixed`
- **레거시 폴리필**: `@vitejs/plugin-legacy` 도입 + es2020 target

## [0.9.1] - 2026-04-06

### Added

#### quant 엔진 — 29축 7그룹 확장
- **축 기반 디스패치**: `dartlab.quant("축명", "종목코드")` — macro/scan과 동일 패턴. `_AXIS_REGISTRY` + `_ALIASES` + lazy import.
- **기술적 그룹 (7축)**: indicators(45지표), signals(9신호), verdict, momentum(Jegadeesh-Titman/Moskowitz/52주신고가), volatility(GARCH MLE/HAR-RV), regime(Hamilton 2-state HMM), pattern(캔들스틱10종/지지저항)
- **리스크 그룹 (4축)**: beta(CAPM), factor(FF5 프록시), tailrisk(CVaR/Sortino/최대낙폭), residual(잔여모멘텀)
- **미시구조 그룹 (3축)**: liquidity(Amihud/Roll), flow(기관외국인수급), volume(OBV추세/거래량괴리)
- **펀더멘털 그룹 (4축)**: divergence, quality(Asness QMJ), value(장부가신호), earnings(SUE/PEAD)
- **텍스트/공시 그룹 (5축)**: sentiment(LM감성사전), toneChange(톤변화감지), eventSignal(이벤트분류), riskText(리스크팩터델타), governanceQuant(거버넌스정량화)
- **횡단면 그룹 (3축)**: ranking(멀티팩터순위), screen(6프리셋스크리닝), pairs(ADF공적분)
- **포트폴리오 그룹 (3축)**: meanvar(Markowitz), riskparity(HRP Lopez de Prado), allocation(리스크버짓팅)
- **`_lm_dict.py`**: Loughran-McDonald 한/영 금융 감성 사전 (NEGATIVE/POSITIVE/UNCERTAINTY/LITIGIOUS)
- **`spec.py`**: 29축 메타데이터 (AI/generateSpec 자동 수집용)
- **하위호환 브릿지**: 기존 `quant("005930", "indicators")` 호출 → DeprecationWarning + 자동 swap

#### review 엔진
- **스토리 템플릿 확장**: keyQuestions, actFocus, detectTemplates 복수 매칭 지원
- **src/dartlab/review/README.md 전면 업데이트**: 템플릿/narrate/publisher/6막 렌더링 문서화

#### macro 엔진
- **보고서 서사 엔진**: 숫자 나열에서 경제 해석으로. Goldman/BIS 스타일 전파 경로.
- **2026-04 경제분석 보고서**: US + KR 양쪽 발간 (11축 완전체)

#### selfai 엔진
- **Phase 3**: 도구 라우터 + APIGen 파이프라인 + QLoRA 학습 스크립트

#### 운영
- **`operation.issues`**: 이슈 관리 체계 (GitHub Issue + 기능별 테스트 + 커밋 연결)
- **`src/dartlab/quant/README.md`**: quant 엔진 운영문서 신규

### Changed

#### Company (core)
- **select cascade 재설계**: 인덱스 누적 방식으로 변경. 복합 조회 시 모든 항목이 충족될 때까지 다음 단계 진행.
- **한국어↔한국어 동의어 bridge 추가**: 회사마다 다른 계정명(법인세차감전순이익 vs 법인세비용차감전순이익)을 snakeId 통일 변환 → 역변환으로 매칭.
- **contains 단계 안전장치**: 여러 후보 중 가장 긴 매칭 우선 (짧은 부분문자열 오매칭 방지).
- **`_KR_SYNONYMS` 동의어 테이블**: 세전순이익, 법인세차감전순이익 등 줄임말/변형 → snakeId 매핑.
- **ratios 컬럼명 통일**: `"항목"` → `"계정명"` (IS/BS/CF select와 일치). **⚠ Breaking Change**

#### EDGAR
- **컬럼명 DART 통일**: IS/BS/CF `"account"` → `"snakeId"` + `"계정명"` 컬럼 추가. **⚠ Breaking Change**
- **ratios 컬럼명 통일**: `"category"` → `"분류"`, `"metric"` → `"계정명"`. **⚠ Breaking Change**

#### labels (L0)
- **`SNAKEID_ALIASES`**: `pretax_income` → `profit_before_tax`, `income_before_income_taxes_expenses` → `profit_before_tax` 추가.
- **`_KR_SUPPLEMENTS`**: `profit_before_tax` → `"법인세비용차감전순이익"` 추가.

#### review 엔진
- **모듈 상태 제거**: 임계값 통일 + catalog 중앙 관리 리팩토링

### Fixed

- **#14**: `select("IS", ["세전순이익", "법인세비용"])` 복합 조회 시 1건만 반환 → 2건 정상 반환.
- **#15**: `select("IS", ["법인세비용차감전순이익"])` → income_taxes로 잘못 매핑 → profit_before_tax 정상 매핑.
- **#16**: ratios `"항목"` vs IS select `"계정명"` 컬럼명 불일치 → `"계정명"`으로 통일.
- **#17**: `_showSegmentsSub("composition")` ShapeError — 연결/개별 중복 컬럼명에 접미사(_2) 부여.
- **macro 보고서**: 제목 오염 수정, 이상값 차단, 서사 품질 강화.

### Removed

- 미사용 VSCode 스크린샷 15개 삭제 (`screenshots/vscode_*.png`)

## [0.9.0] - 2026-04-04

### Changed

- **SNAKEID_ALIASES 통합**: `labels.py`(L0)에 42개 alias dict 통합. `mapper.py`의 `EDGAR_TO_DART_ALIASES`는 L0 참조로 전환. 중복 제거.
- **EDGAR report extractor 리팩토링**: `loadXbrlTags()` 공용 헬퍼 추출. XBRL 기반 7개 extractor에서 CIK/path/parquet 보일러플레이트 제거.
- **macro 엔진 11축 확장**: 기존 5축(사이클/금리/자산/심리/유동성)에 예측/위기/재고/기업집계/교역/종합 6축 추가. 축별 기여도 추적.
- **전략 신호 강도/신뢰도**: `StrategySignal`에 `strength`(0.0~1.0) + `confidence`(high/medium/low) 필드 추가. 40개 전략 전수 반영.
- **macro spec 구조화**: 각 축 메타데이터를 label/description/when/key_output 구조로 확장. 내부 방법론(Hamilton RS, Kalman DFM, Nelson-Siegel) 명시.
- **edgarBuilder targetAccounts 순서 수정**: 정의 전 참조 버그 해결.

### Fixed

- **credit history 데이터 갱신**: 삼성전자/SK하이닉스/LG화학/NAVER 4개사 평가 이력 추가.

## [0.8.9] - 2026-04-04

### Changed

- **UI 구조 전면 재편**: `vscode/` + `ui/` → `ui/vscode/`, `ui/web/`, `ui/shared/` 통합. 확장 본체와 webview가 `ui/vscode/` 한 곳에.
- **shared 코드 분리**: chart, api, markdown 렌더러를 `ui/shared/`로 추출. web/vscode 중복 제거.
- **macro 엔진 확장**: 위기감지/재고사이클/교역조건/수익률곡선/기업실적 집계 모듈 추가.
- **EDGAR report 14 apiType**: auditOpinion, executive, majorHolder 등 SEC XBRL 기반 구조화 추출.
- **FRED catalog 14그룹**: commodities, yieldcurve, flowoffunds 등 7개 그룹 추가.

### Fixed

- **CI 워크플로우 경로**: `vscode/webview` → `ui/vscode/webview` 일괄 수정.
- **서버 SPA 경로**: `ui/build` → `ui/web/build` 수정 (web.py, embed.py).
- **품질 게이트 baseline**: macro 확장에 따른 E/F 함수 수, vulture 수 반영.
- **test_embed**: widget 미구현 상태에서 skip 처리.
- **test_fred**: FRED catalog 그룹 수 7→14 반영.

## [0.8.8] - 2026-04-04

### Added

- **credit v3 Notch Adjustment**: 기업 특성(규모/공기업/캡티브/지주/CAPEX) 기반 등급 보정. 30개사 60% 적중.
- **credit Track B 금융업**: 은행/보험/증권 전용 5축 (자본적정성/수익성/자산건전성/유동성/사업안정성). 신한지주 AA+ 정확 일치.
- **CHS 부도확률 모델 연동**: 주가 기반 ±1 notch 시장 보정. EPS 역산 shares 추정.
- **별도재무제표(OFS) 블렌딩**: 캡티브 금융/지주사에서 연결 50% + 별도 50% 블렌딩. 현대차 별도 차입금 1.9조 vs 연결 58조 자동 감지.
- **analysis 14축 TTM 환산**: 연간 컬럼 없는 기업(금융지주/일부 대기업) 분기→연환산. KB금융 ROE 0.09%→8.41%.
- **macro 엔진**: 5축(사이클/금리/자산/심리/유동성) 시장 레벨 매크로 분석. Company 불필요.
- **forecast 이익 연동**: 영업이익/순이익을 매출전망×마진추세로 연동 예측.
- **AI 멀티턴 메모리**: keyMetrics 구조화 수치 저장. 3턴 이후 이전 분석 수치 참조 가능.
- **company-reports 블로그**: 6막 재무 서사 기반 기업분석 보고서 카테고리 (LG화학/KT&G/대한항공).

### Changed

- **시스템 프롬프트 69% 압축**: 333→110줄. 도구 나열→라우팅 테이블 전환. 상한 150줄/5,000자.
- **credit 업종 기준표 10개**: 반도체/비철/항공/지주/통신 D/EBITDA 완화, 유틸 유동비율 완화.
- **금융업 현금및예치금 fallback**: 금융지주 BS 구조 대응.

### Fixed

- **금융업 revenue 정의**: 이자수익→금융이익 우선 (KB금융 영업이익률 2363%→135.8%).
- **이자비용 CF fallback**: IS에 이자비용 없는 기업도 ICR 계산 (대한항공 None→1.38).
- **FCF 음수 FOCF/Debt 스킵**: CAPEX 집약 기업 축1 과대평가 방지.
- **consensus stale cache**: 전 소스 실패 시 24시간 이전 캐시 반환.

## [0.8.7] - 2026-04-03

### Added

- **OAuth 코드 수동 입력**: 방화벽 환경에서 브라우저 주소창 URL을 복사해서 붙여넣기로 인증
- **OAuth 로그인 시 auth URL 화면 표시**: 브라우저가 안 열릴 때 링크 직접 클릭 가능

## [0.8.6] - 2026-04-03

### Added

- **OAuth 수동 토큰 입력**: 방화벽 환경에서 다른 PC의 토큰을 붙여넣어 ChatGPT 연결 가능

## [0.8.5] - 2026-04-03

### Added

- **VSCode 프로바이더 연결 플로우**: provider 선택 시 바로 연결 시작 (API 키 InputBox, OAuth 브라우저 로그인)
- **VSCode OAuth 로그인**: ChatGPT 선택 시 PKCE 브라우저 로그인 + callback 자동 처리
- **stdio needCredential/oauthStart 프로토콜**: extension ↔ Python 백엔드 간 인증 흐름

### Changed

- **VSCode 웰컴 화면**: 프로바이더 설정 카드로 재구성 (키 발급 + 연결 버튼)
- **입력창 항상 활성**: 서버 상태와 무관하게 입력 가능
- **자동설치**: Windows PowerShell 5.x 호환 (`;` 구분자)
- **에러 메시지**: UI에서 `dartlab.setup(...)` CLI 안내 제거, provider 변경 유도
- **provider label**: "무료" 표현 전체 제거

### Fixed

- **provider 인증 에러 무시**: `except Exception: pass` → ImportError만 무시, 나머지는 사용자에게 표시
- **fixture integration 테스트**: CI DARTLAB_DATA_DIR 연동, 62개 테스트 추가
- **노트북 정합성**: c.insights 잔존 참조, corpName→종목명 전수 수정

## [0.8.4] - 2026-04-02

### Added

- **operation.architecture**: 전체 청사진 — 레이어, 엔진, 규칙, 데이터 출력, 신규 기능 체크리스트
- **operation.testing**: 테스트 체계 — 마커, 커버리지 목표, CI 규칙
- **테스트 1,148개 추가**: 843→1,991 passed (20개 신규 테스트 파일, 9개 엔진 전체 커버)
- **numpy** base 의존성 추가 (quant 엔진 필수)

### Changed

- **scan 데이터 일관성 통일**: 전 축 종목코드+종목명 첫 2컬럼 (governance/debt/capital/workforce/account/ratio 수정)
- **c.insights 제거**: analysis("financial", "종합평가")로 통합 — 엔진 내부 기능 Company 직접 노출 금지

### Fixed

- **annualColsFromPeriods 인자 순서 버그**: 8개 파일 23곳에서 _MAX_YEARS가 basePeriod로 잘못 전달
- **CI --benchmark-disable**: 테스트 타임아웃 방지

## [0.8.3] - 2026-04-02

### Changed

- **quant 독립 엔진 격상**: analysis 축에서 분리 → `c.quant()`, `dartlab.quant()` 독립 진입점 복원
- **quant 코드 통합**: analysis/quantCalcs.py, technicalAnalysis.py 삭제 → quant/extended.py로 로직 통합
- **quant 신규 metric**: `c.quant("divergence")` 재무-기술적 괴리, `c.quant("flags")` 기술적 플래그
- **credit healthScore**: `cr["healthScore"]` 추가 (100-score, 높을수록 건전)
- **viz AI 연동**: 도메인 차트(revenue/cashflow/profitability) sandbox import + 프롬프트 유도
- **README 전면 정비**: credit/viz/extras/아키텍처/안정성 v0.8.2 반영
- **AI 프롬프트 #29-#30**: credit score 의미 명시, viz 도메인 차트 우선 안내
- **문서 체계 점검**: Skill OS 전체, import 방향, 엔진 일관성 전수조사 통과

### Removed

- `c.analysis("quant", "기술적분석")` — `c.quant()`로 대체
- `analysis/financial/quantCalcs.py` — quant 엔진으로 통합
- `analysis/financial/technicalAnalysis.py` — quant/extended.py로 이동

## [0.8.2] - 2026-04-02

### Added

- **credit 독립 엔진**: dartlab 독립 신용평가 체계 (dCR). 7축 가중 + 업종 세분화 + CHS 부도확률. `c.credit()` 진입점
- **quant → analysis 축 통합**: `c.analysis("quant", "기술적분석")` — 25개 기술 지표 + 9개 매매 신호
- **금융업 수익성 분석**: 은행/보험 이자수익 기반 marginTrend 지원 (KB금융 등)
- **AI 종합분석 6막 서사**: 기업 전반 질문에 analysis 3축 자동 실행 + 인과 해석 구성
- **AI quant+재무 교차 검증**: 기술적 지표와 재무분석 결합 투자 판단
- **보고서 렌더링 개편**: 게이지바 + 문단서사 + 변화화살표

### Changed

- **analysis↔credit 상호의존 완전 제거**: 같은 L2지만 상호 import 0건. review가 블록식 조합
- **AI 프롬프트 #26~#28**: 종합분석 섹션, quant 섹션, review 금지 + analysis 기반 서사 해석
- **Skill OS 문서 전면 정비**: analysis 14축 체계, credit 독립 명시, vectorStore/DDG 참조 제거
- **VSCode 확장 개선**: oauth-codex provider 지원

### Fixed

- **금융업 marginTrend=None**: 은행 IS에 매출액 없는 문제 → 이자수익 기반 분기
- **test_ai_no_build**: _check_built_ui → _checkBuiltUi camelCase 수정
- **보고서 품질**: 지주사 모순/트리거 비현실/OCF 비정상 수정

## [0.8.1] - 2026-04-01

### Changed

- **엔진 호출방식 2단계 통일**: `analysis("financial", "수익성")`, `scan("financial", "profitability")` 패턴. 모든 엔진 동일
- **accessor 패턴 추가**: `c.analysis.financial.profitability()`, `dartlab.scan.financial.growth()` — IDE 자동완성 지원
- **한글/영문 양방향 alias**: `analysis("financial", "profitability")` = `analysis("financial", "수익성")`
- **`__init__.py` 700줄 삭제**: 루트에 직접 노출하던 축 함수 14개 제거, 엔진 함수만 유지
- **전체 문서/독스트링/AI 패턴/노트북** 신 패턴으로 일괄 변환 (20파일 70곳+)

### Removed

- **루트 축 함수**: `dartlab.governance()`, `dartlab.forecast()`, `dartlab.valuation()` 등 14개 — `dartlab.scan("축")` 또는 `c.analysis("그룹", "축")`으로 대체
- **Company 편의 메서드**: `c.forecast()`, `c.valuation()`, `c.simulation()`, `c.research()` — `c.analysis("그룹", "축")`으로 대체

## [0.8.0] - 2026-04-01

### Added

- **UI 엔진 승격 (L4)**: `src/dartlab/ui/` → 루트 `ui/`로 이동. 아키텍처에서 L4 표현 계층으로 정식 승격
- **scan `extractAccount()` 공통 함수**: 4개 축(profitability/growth/quality/liquidity)의 중복 계정추출 로직 통합

### Changed

- **7개 엔진 코드 감사**: scan, analysis, search, ai, review, company 전면 정리
  - scan: `_screenAll()` 이중호출 제거 (성능 2배), 계정추출 4중복 → `_helpers.extractAccount` 통합
  - analysis: 죽은 `buildTimeline()` 제거, 11개 calc 파일 lazy import 래퍼 → 직접 import (~400줄 삭제)
  - ai: `_validateCode` 2중복 → 모듈 함수 통합, bare except 정리
  - review: `FlagBlock.icon`, `HeadingBlock.htmlTag/markdownPrefix` 속성 추출 (렌더링 메타데이터 단일화)
  - company: 죽은 `_boardTopics()`, `_stripUnitHeader()` 제거
- **스펙 문서 정리**: generateSpec.py 출력 7개 → 4개 축소
- **CI 안정화**: spec-sync를 non-blocking (continue-on-error) 전환
- **성숙도 classifier**: `Production/Stable` → `Beta` (README 메시지와 일치)
- **서버 UI 경로**: `server/web.py`, `embed.py` 경로를 루트 `ui/build/`로 변경

### Removed

- **vectorStore.py** (697줄): stemIndex로 완전 대체된 레거시 벡터 검색 모듈 삭제
- **_generatedCatalog.py**: import 0곳인 죽은 코드
- **api-reference.json** (131KB): 소비자 없는 자동생성 파일
- **generated-reference.md** (43KB): CAPABILITIES.md로 대체
- **STRUCTURE_MAP.md**: 소비자 없는 통계 문서
- **dataConfig vectorIndex 항목**: 삭제된 vectorStore 참조 제거

### Fixed

- **growthAnalysis.py**: `hist` 변수 미정의 버그 수정 (undefined name)
- **derived.py**: 미사용 `json` import 제거
- **Benchmark CI**: gh-pages 브랜치 생성으로 벤치마크 저장소 이슈 해결

## [0.7.16] - 2026-03-31

### Added

- **시맨틱 검색 엔진(alpha)**: `dartlab.search("대표이사 변경")` — n-gram + vector hybrid 검색. core/search 모듈 신규, ngramIndex 정리
- **AI 프롬프트 패턴 3종**: growth, quick_check, value_investor 패턴 추가. 기존 패턴(financial, prediction, risk, valuation) 보강
- **review 6막 구조 확장**: builders/templates 대폭 강화, registry 축-보고서 매핑 보강
- **analysis predictionSignals 확장**: 예측 신호 12→15축 (consensusDirection, flowDirection, revenueDirection)
- **Skill OS 운영문서 체계**: DEV.md 전면 제거 → 루트 Skills에 엔진별 설계 문서 통합
- **실험 105 시맨틱 맵**: 13개 실험 스크립트 (taxonomy~reportNmMapping)
- **VSCode extension**: ChatInput/ChatPanel UX 개선, 메시지 프로토콜 확장

### Changed

- **analysis 6축 계산 개선**: asset, capital, costStructure, earningsQuality, stability 보강
- **providers/dart**: allFilingsCollector 증분 수집/에러 복구 강화, notes 파싱 개선
- **ai/runtime**: 패턴 매칭 로직 확장, standalone 안정화
- **core**: vectorStore를 core/search로 이전, exogenousAxes/ols 강화

### Removed

- **DEV.md 28개 파일**: 모듈별 산재된 개발 메모 → Skill OS 통합으로 대체
- **core/vectorStore.py**: core/search/vectorStore.py로 이전

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

- **AI 레거시 모듈 60+ 파일**: context/(builder, compactMap, company_adapter, dartOpenapi, finance_context, formatting, pruning), conversation/(dialogue, focus, intent, prompts, suggestions, data_ready, templates/), eval/(diagnoser, scorer, truthHarvester, replayRunner, remediation, batchResults/, diagnosisReports/, reviewLog/), skills/(catalog, registry), tools/(discovery, registry, runtime, selector, superTools/, _helpers), spec.py, metadata.py, reviewer.py, agent.py, aiParser.py
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

- **review 매출전망 섹션 (6부)**: `c.story("매출전망")` — 7-소스 앙상블 매출 예측. revenueForecast, segmentForecast, proFormaHighlights, scenarioImpact, forecastMethodology, historicalRatios, forecastFlags 7개 블록. 업종별 시나리오 분화 지원
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
- **통합 scan 인터페이스**: `dartlab.scan("cashflow")`, `dartlab.scan.topics()` — 11축을 하나의 callable class로 통합. 한글 alias 지원 (현금흐름, 감사, 내부자 등)
- **review narrative 자동생성**: `review/narrative.py` — 순환 서사 감지 + 섹션 간 스레드 연결. buildReview에 자동 주입
- **review 렌더러/포맷 확장**: renderer 고도화 + formats 확장 + registry 블록 60+개 (이전 16개)
- **TUI 개선**: 커맨드 팔레트, 웰컴 스크린, 채팅 영역 고도화
- **AI 분석 품질 향상 로드맵**: `TODO_AI_ANALYSIS.md` — 7 Part 19개 TODO, P0~P1 우선순위

### Changed

- **scan debt risk 고도화**: 위험등급 판정 로직 세분화, 만기 집중도 분석 강화
- **scan workforce growth 강화**: 성장률 계산 고도화, 인력 구조 분석 확장
- **README 갱신**: Market Scan 섹션에 통합 scan 인터페이스 + 신규 3축 반영. review 블록 60+개로 정정. ratio 카테고리 valuation 추가
- **노트북 갱신**: Colab/Marimo scan 노트북에 통합 scan 인터페이스 예제 추가, showcase insight 10영역으로 정정

### Fixed

- **CircuitBreaker flaky 테스트**: `test_half_open_after_timeout` 타이밍 여유 0.06s → 0.1s (Windows 간헐 실패 해결)

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
  - `c.story("수익구조")` / `c.story("자금조달")` — 템플릿 기반 분석 보고서
  - `blocks(company)` — 분석 블록 사전 (수익구조 + 자금조달 + 자산 + 현금흐름)
  - `Review([...])` — 블록 자유 조립, SelectResult/DataFrame 혼합 지원
  - `dartlab.ask()` — LLM 종합의견 레이어 (guide 파라미터로 분석 관점 지정)
  - 4개 렌더링 형식: rich (터미널), html, markdown, json
  - `dartlab review 005930` CLI 명령
- **analysis/strategy calc-only 패턴**: revenue/capital 분석 함수가 dict/숫자만 반환, 블록 생성과 분리
  - `calcSegmentComposition`, `calcSegmentTrend`, `calcBreakdown`, `calcRevenueGrowth` 등 15개 calc 함수
  - import 방향 엄격 적용: analysis → review 단방향 (역방향 금지)
- **README Review 섹션**: 템플릿, 블록 자유 조립, 리뷰어, 무료 프로바이더 안내 (EN/KR)
- **sampleReview 노트북**: 블록 조립, reviewer 사용 예제 (marimo)
- **블로그 124호**: 수익구조 읽는 법

### Changed

- **sections pipeline 개선**: 텍스트 구조 복원, segment matcher 정비
- **DART Company**: review/reviewer 메서드 추가, select() 지원
- **EDGAR Company**: review 메서드 추가

## [0.7.9] - 2026-03-26

### Added

- **Gemini OAuth 2.0 브라우저 로그인**: API key 없이 Google 계정 로그인으로 Gemini 사용 가능. GPT OAuth와 동일한 GUI 플로우. `google-auth-oauthlib` 제거, 표준 라이브러리 + httpx만 사용
- **Gather 엔진 시계열 정리**: `price()`, `flow()`, `macro()` 모두 Polars DataFrame 시계열 반환. `macro("KR")`, `macro("US")`, `macro("CPI")` 직관적 호출 지원
- **네이버 차트 API 전환 (FDR 방식)**: 모바일 페이징 API(1000일) → `fchart.stock.naver.com` 차트 API(6000일, 수정주가). 요청 20회 → 1회
- **Gather 인프라 강화**: Yahoo Direct consensus, FMP consensus/sector PER, circuit breaker(3회→60초 차단), stale-while-revalidate 캐시, persistent event loop, Yahoo RPM 30→5 조정
- **`scanAccount()` / `scanRatio()` README 문서화**: 시장 전수 재무 스크리닝 섹션 추가 (EN/KR 양쪽)
- **AI 도구 아키텍처 전면 재설계**: 101개 세분화 도구 → 8개 Super Tool 통합. LLM 도구 선택 정확도 향상
- **Insight 10영역 확장**: 기존 7영역에 predictability(예측 가능성), uncertainty(불확실성), coreEarnings(핵심이익 품질) 3영역 추가
- **`scanAccount()` / `scanRatio()` 구현**: 전종목 단일 계정/비율 시계열 배치 추출 (2,700+ DART / 500+ EDGAR, ~3초)
- **sections Categorical 스키마**: Polars Categorical 컬럼 적용으로 RSS 427MB 절감 (83%)
- **ECOS gather 엔진**: 한국은행 경제통계 22개 지표 수집. 국고채 3/5/10년, 회사채 BBB- 5년, CD 91일 금리 확장
- **Google Gemini provider**: `google-genai` SDK 기반 AI provider 추가
- **Ollama 속도 최적화**: GPU 자동 감지, flash_attn, VRAM 기반 모델 추천, keep_alive 제어, 스마트 preload
- **HF Spaces Docker 웹 데모**: Gradio 기반 AI 분석 데모 앱 + GitHub Actions 자동 배포
- **글로벌 피어 매핑**: `peer/discover.py` — WICS→GICS 섹터 기반 글로벌 피어 자동 매핑
- **공통 유틸리티**: `core/env.py`(환경 변수 중앙 관리), `common/audit.py`(감사의견 정규화 KR/EN/JP), `common/finance/currency.py`(FRED 기반 환율 변환)
- **UI 리팩터**: ActivityBar/CompanyContextBar 제거, 사이드바 통합, SettingsPanel Gemini OAuth 설정

### Fixed

- **Gather 코드 감사**: 전체 에러 경로 `log.debug` → `log.warning` 전환 (조용한 실패 금지 원칙)
- **차트/테이블 기간 컬럼 매칭**: 분기 컬럼 `2024Q1` 형식 지원
- **sections Categorical 호환**: period `.str` 연산에 cast 적용
- **EDGAR docs 수집 안정화**: filing 파싱 실패 시 개별 스킵 (전체 크래시 방지)
- **peer consensus**: numpy 의존 제거 → `statistics.median` 사용 (CI 호환)

### Changed

- **Gather macro() 시그니처**: `macro(indicator, *, market)` → `macro(market="KR", indicator=None)` — 직관적 호출
- **llm-gemini extras 제거**: `google-genai`를 `llm` extras에 통합
- **DEV.md 전수 현행화**: analysis(8→10모듈), insight(7→10영역), gather(도메인 확장), CHANGELOG 링크, installation.md 데이터 소스 수정
- **README EN/KR 동기화**: Market Data Collection 섹션 전면 갱신, scanAccount/scanRatio 섹션 추가, 10-area 반영

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
- `tests/test_edgarDocs_foundation.py` 가 기대하는 EDGAR 배치 다운로드 helper 를 다시 반영
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
- legacy sections view가 raw markdown를 보존한 canonical wide view로 동작하면서 appendix/detail row는 기본 core view에서 숨김
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
- legacy sections view가 learned section rules 기반으로 coarse report를 fine topic 축에 즉시 backfill
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
- 단일시점 세로나열 → 연도별 피벗 테이블로 구조 정리
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

**노트북 구조 정리**
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
