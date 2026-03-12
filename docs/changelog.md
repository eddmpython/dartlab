---
title: Changelog
---

# Changelog

All notable changes to DartLab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- `Company.search()` → `KRCompany.search()`로 변경 (팩토리 함수에 staticmethod 부재 문제)
- `Company()` 반환 타입 힌트 수정

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
