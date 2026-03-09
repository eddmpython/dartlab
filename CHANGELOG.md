# Changelog

All notable changes to DartLab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
