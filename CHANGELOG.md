# Changelog

All notable changes to DartLab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- `server/resolve.py`, `server/__init__.py`에서 `Company.search()` → `KRCompany.search()`로 변경
- `Company()` 팩토리 함수 반환 타입 힌트를 forward reference(`"KRCompany"`)로 수정

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
