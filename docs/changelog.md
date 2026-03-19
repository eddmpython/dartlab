---
title: Changelog
---

# Changelog

All notable changes to DartLab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.0] - 2026-03-19

### Added

- **AI 공시 탐색 도구**: `show_topic`, `list_topics`, `trace_topic`, `diff_topic` — LLM이 Company 핵심 API 직접 호출
- **ChartSpec JSON 프로토콜**: combo, radar, waterfall 등 6가지 차트 타입 지원
- **UI 뷰어 리뉴얼**: DisclosureViewer, TopicRenderer 등 전면 개선

### Changed

- README/README_KR 자동 다운로드 설명 + Try It Now 섹션 추가
- 서버 TOC 로마 숫자 순서 정렬
- sections pipeline cadence 성능 개선

### Fixed

- CLI e2e 테스트 Windows 인코딩 수정

## [0.6.0] - 2026-03-19

### Added

- **세로 뷰**: `show(topic, period=["2024Q4", "2023Q4"])` — 특정 기간을 세로로 비교
- **topics DataFrame**: `c.topics` → DataFrame (topic, source, blocks, periods)
- **ratios 시계열**: `c.ratios` → 시계열 DataFrame (항목 × period, 최신 먼저)
- **RatioResult `__repr__`**: 6개 카테고리별 한국어 라벨 + 억 단위 포맷
- **report 분기 데이터**: Q1~Q4 전 분기 표시

### Changed

- finance/report 기간 정렬 최신 먼저 역순 통일
- 2015년 데이터 제외 (standalone 변환 불가)
- openai_compat provider `OpenAIError` catch 추가

### Fixed

- EDGAR index topics DataFrame 순회 수정
- 테스트 topics 호환성 수정

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

## [0.4.4] - 2026-03-12

### Changed

**docs/sections production 마감**
- `Company.sections` 가 raw markdown를 보존한 canonical wide view로 동작하면서 appendix/detail row는 기본 core view에서 숨김
- `Company.retrievalBlocks`, `Company.contextSlices` 가 `sourceTopic`, `cellKey`, `semanticTopic`, `detailTopic` 을 함께 반환해 원문 block을 역추적 가능하게 정리
- appendix/detail 명세서를 detail semantic layer로 분리해 core 비교축과 분리
- broad raw residual 일부를 exact mapping으로 흡수해 package 기본 수평화 품질을 마감
- 금융업/지적재산권/수주/계약 상세표를 detail taxonomy로 흡수해 추가 docs 종목군에서도 core raw residual이 사라지도록 보강

### Fixed

**패키지 메타데이터와 문서 정리**
- README에 `sections/retrievalBlocks/contextSlices` 사용 흐름과 런타임 무저장 원칙을 명시
- `pyproject.toml` classifier 를 `Production/Stable` 로 상향

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
- `c.IS` — docs CIS(포괄손익계산서) → **finance IS(손익계산서)**로 변경
  - 매출액, 영업이익 등 핵심 계정 누락 문제 해결
- `c.dividend`, `c.employee`, `c.majorHolder`, `c.executive`, `c.audit` — report API 우선으로 변경
- `sections` pipeline — 단순 leaf title 병합에서 learned-rule 기반 horizontalization으로 변경
  - 번호/기호 prefix 제거 강화
  - legacy section title exact mapping 흡수
  - chapter II coarse topic을 canonical fine topic으로 projection

### Added

**report 엔진 5개→22개 apiType 확장**
- `c.report.treasuryStock`, `c.report.capitalChange` 등 17개 비피벗 apiType 자동 접근
- `c.report.apiTypes`, `c.report.labels` 속성 추가

**Company property 추가**
- `c.tangibleAsset` — 유형자산 변동표
- `c.costByNature` — 비용 성격별 분류 시계열

**엔진별 SPEC.md 문서** — finance, report, docs 각 엔진 상세 API 스펙

**테스트 추가** — BS 항등식, 매핑 벤치마크, 재무 회귀, 서버 smoke test

**블로그** — 007 EDGAR 통합 플레이북, 008 사업의 내용으로 기업 판단하기

## [0.3.2] - 2026-03-11

### Added

**Data Explorer 전면 리디자인**
- 모달 → 전체화면 레이아웃, 한글/영문 토글, 계정 계층 인덴트
- 재무 시계열 테이블: 첫 열 고정, 원 단위 자동 포맷, 음수 빨간색

**6개 LLM Provider 지원**
- ChatGPT (OAuth), Ollama, OpenAI API, Anthropic API, Codex CLI, Claude Code CLI

## [0.3.1] - 2026-03-10

### Added

**재무비율 시계열 피벗 (engines/common/finance)**
- `toSeriesDict()` — 연도별 재무비율 시계열을 IS/BS/CF와 동일한 dict 구조로 변환
- `RATIO_CATEGORIES` — 6카테고리(수익성, 안정성, 성장성, 효율성, 현금흐름, 절대값) 그룹핑 상수

**Company.ratioSeries property**
- `c.ratioSeries` — 연도별 재무비율 시계열 접근 (`{"RATIO": {snakeId: [v1, v2, ...]}}`, years)

**Excel 재무비율 시트 개선**
- 단일시점 세로나열 → 연도별 피벗 테이블 + 카테고리 섹션 헤더 + 색상 구분

**SCE(자본변동표) spec.py 반영**
- AI Tier 2에서 자본변동표 데이터 존재를 인지할 수 있도록 spec 추가

### Fixed

**서버 Company.search 버그 수정**
- `dartlab.Company.search()` → DART engine company search 경로로 변경 (팩토리 함수에 staticmethod 부재 문제)
- `dartlab.Company()` 반환 타입 힌트 수정

## [0.3.0] - 2026-03-09

### Changed

**엔진 레이어 아키텍처 리팩토링 (Breaking Change)**
- `engines/` 디렉토리를 L1(데이터소스)/L2(분석)/L3(AI) 3계층으로 재편
- 모든 import 경로 변경 (docsParser→dart/docs, financeEngine→dart/finance, reportEngine→dart/report, sectorEngine→sector, insightEngine→insight, llmAnalyzer→ai)

### Added

**섹터 분류 (engines/sector)** — WICS 11섹터, 3단계 분류 + 밸류에이션 파라미터
**인사이트 확장 (engines/insight)** — 섹터 벤치마크 상대평가, 금융/비금융 자동 판별
**시장 순위 (engines/rank)** — 매출/자산/성장률 전체+섹터 내 순위
**문서 갱신** — API_SPEC, README, docs 전면 업데이트

## [0.2.5] - 2026-03-09

### Changed

**`dartlab[ui]` → `dartlab[ai]` 리네이밍**
- AI 기업분석 optional dependency를 `[ai]`로 변경 (`dartlab ai` CLI 명령과 일치)
- `dartlab[ui]`는 하위호환 alias로 유지
- `dartlab ui` CLI 실행 시 `dartlab ai`로 변경 안내

**uv 통일**
- 전체 문서에서 pip 참조 제거, uv 설치 방법으로 통일

### Added

**insightEngine — 종합 인사이트 분석 엔진**
- 7영역(실적, 수익성, 재무건전성, 현금흐름, 성장성, 지배구조, 밸류에이션) 등급 분석
- 이상치 탐지 + 요약 텍스트 자동 생성
- Company 클래스에 `insights` property 통합

**AI 웹 인터페이스 UX 개선**
- 로딩 단계 표시, 응답 경과시간 배지, 대화 삭제 확인 팝업
- context 모달 헤더 레이아웃 수정

**Ollama 최적화**
- 서버 시작 시 모델 preload (cold start 제거)
- 모델 추천 가이드 API
- 질문 유형 기반 컨텍스트 필터링

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
- 블로그 컨텐츠 중앙 배치, ToC 우측 유지 (모바일 숨김)
- 독스/블로그 섹션 간 간격 확대
- 독스/블로그 하단에 랜딩 Footer 추가 (Buy Me a Coffee 포함)

**노트북 전면 재작성**
- `print(df)` 제거, Jupyter/Colab rich 렌더링 활용
- 한 셀에 하나의 DataFrame만 표시

### Added

- OG 이미지 적용 (링크 공유 시 미리보기)
- 블로그 섹션 + 첫 번째 포스트
- `CHANGELOG.md` 추가

## [0.1.12] - 2026-03-08

### Fixed

- 파싱 모듈 5건 수정 — 출력 품질 점검 결과 반영

## [0.1.11] - 2026-03-08

Company 클래스 전면 재설계 — yfinance 스타일 property 접근, Notes 통합, rich 터미널 출력.

### Changed

**Company 재설계**
- 40개 모듈을 property로 직접 접근 (`c.BS`, `c.dividend`, `c.audit`)
- `_MODULE_REGISTRY` 기반 lazy loading + caching
- `get(name)`으로 전체 Result 객체 반환, `all()`로 전체 데이터 dict
- `guide()`로 사용 가능한 property 목록 rich 출력

**Notes 통합**
- `c.notes.inventory` / `c.notes["재고자산"]` 이중 접근
- K-IFRS 주석 12개 항목 통합 래퍼

**브랜딩**
- red/coral 색상 전환 (#ea4647), 아바타 마스코트 적용
- `analyze` → `fsSummary` 리네이밍

## [0.1.10] - 2026-03-08

### Added

- finance 모듈 8개 추가 (`articlesOfIncorporation`, `auditSystem`, `companyHistory` 등)
- 랜딩 전체 영어화, Workflow/ModuleCatalog/UseCases 섹션 신규
- 튜토리얼 4종 + Colab 노트북 추가

## [0.1.9] - 2026-03-08

### Added

- finance 모듈 15개 추가 (v0.1.8 + v0.1.9 통합)
  - `audit`, `boardOfDirectors`, `bond`, `capitalChange`, `contingentLiability`, `costByNature`, `internalControl`, `relatedPartyTx`, `sanction`, `shareCapital`
  - `affiliateGroup`, `fundraising`, `salesOrder`, `productService`, `riskDerivative`

### Fixed

- mdsvex 빌드 오류 수정

## [0.1.6] - 2026-03-07

### Changed

- `notesDetail` 키워드 23개로 확장, Pattern D 추가, `tableDf` 시계열 정규화

## [0.1.5] - 2026-03-07

### Added

- `notesDetail` 모듈 — K-IFRS 주석 상세 파싱
- `parseNotesTable` 범용 파서
- 테스트 48개

## [0.1.4] - 2026-03-07

### Changed

- `statements` 연결/별도 재무제표 자동 fallback

### Added

- `tangibleAsset` 모듈
- KindList auto-update GitHub Actions workflow (daily cron)

## [0.1.3] - 2026-03-07

### Changed

- `finance/` / `disclosure/` 패키지 분리

### Added

- KRX KIND 상장기업 목록 매퍼 (`getKindList`, `codeToName`, `nameToCode`, `searchName`)
- `companyOverview`, `business` 공시 서술형 모듈
- SvelteKit 랜딩 페이지 + SEO 최적화

## [0.1.2] - 2026-03-07

### Added

- SvelteKit docs 통합 (mdsvex + Shiki)
- 브랜딩 에셋 (아바타, favicon)

## [0.1.1] - 2026-03-07

### Added

- `affiliate` 모듈, stockCode API 전환
- 랜딩 페이지 기본 구축, quarterly 지원

## [0.1.0] - 2026-03-06

DartLab 최초 공개 릴리즈.

### Added

- `Company` 클래스 — 종목코드 기반 데이터 접근
- `loadData()` — GitHub Releases에서 Parquet 자동 다운로드
- finance 초기 5개 모듈 (`summary`, `statements`, `segment`, `dividend`, `employee`)
- disclosure 초기 2개 모듈 (`mdna`, `rawMaterial`)
- Polars 기반 DataFrame 처리
- GitHub Actions CI + PyPI trusted publishing
- 260+ 상장사 Parquet 데이터 (GitHub Releases)
