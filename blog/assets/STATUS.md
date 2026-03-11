# Blog Assets

블로그 글에 포함되는 SVG 일러스트레이션.

## 네이밍 규칙

`{블로그번호}-{camelCase또는kebab설명}.svg`

- 블로그 번호 3자리 (001, 002, 003)
- 블로그 파일명과 프리픽스 일치

## 빌드 연동

`landing/scripts/syncBlogAssets.js`가 `prebuild` 시점에 이 폴더를 `landing/static/blog/assets/`로 동기화한다.
마크다운에서는 `/blog/assets/파일명.svg`로 참조하면 `svelte.config.js`의 `rehypeBaseUrl` 플러그인이 base path를 자동 주입한다.

## 파일 목록

### 001 — DART의 모든 것
- `001-disclosure-flow.svg` — 전자공시 흐름도 (기업 → DART → 투자자)
- `001-annual-report-structure.svg` — 사업보고서 12개 섹션 구조 + 분기 누적 보고
- `001-notes-deep-dive.svg` — 재무제표 주석 상세 (한 줄 요약 vs 주석 디테일)
- `001-notes-category-map.svg` — 주석 40개 항목 카테고리 맵 (분석 우선순위)

### 002 — OpenDART, 솔직한 리뷰
- `002-dart-timeline.svg` — DART 27년 역사 타임라인 (1999~2027)
- `002-api-categories.svg` — OpenDART 83개 API 6개 카테고리 구조
- `002-opendart-vs-edgar.svg` — OpenDART vs SEC EDGAR 비교
- `002-api-limit-simulation.svg` — OpenDART 호출 제한 시뮬레이션 (시장 전체 수집 관점)

### 003 — 재무제표, 숫자만 보면 안 되는 이유
- `003-beyond-numbers-hero.svg` — Numbers Only vs Full Picture
- `003-same-numbers-different-stories.svg` — 같은 숫자, 다른 이야기 4가지
- `003-analysis-depth-pyramid.svg` — 분석 깊이 5단계 피라미드
- `003-footnote-risk-signals.svg` — 주석 기반 리스크 신호 보드 (차입금/재고/충당/부문)

### 004 — 사업보고서 텍스트, 이렇게 읽는다
- `004-reading-strategy.svg` — 읽기 전략 (우선순위별 4단계 + 페이지 분포)
- `004-industry-reading-focus.svg` — 업종별 핵심 읽기 포인트 6개 업종
- `004-industry-priority-matrix.svg` — 업종별 우선 확인 항목 매트릭스

### 005 — 파이썬으로 재무제표 분석하기
- `005-analysis-pipeline.svg` — 분석 파이프라인
- `005-account-mapping.svg` — 계정 표준화 개요
- `005-quarterly-conversion.svg` — 누적값→독립분기 변환
- `005-dartlab-layers.svg` — DartLab 엔진 레이어
- `005-python-capabilities.svg` — 파이썬의 역할/한계
- `005-account-mapping-pipeline.svg` — 7단계 계정 매핑 상세 파이프라인

### 006 — EDGAR의 모든 것
- `006-edgar-structure-map.svg` — EDGAR form 지도 (정기/수시/포지션 분류)
- `006-dart-vs-edgar-deep.svg` — DART vs EDGAR 심층 비교 매트릭스
- `006-edgar-reading-workflow.svg` — EDGAR 4단계 읽기 워크플로
- `006-edgar-deadline-matrix.svg` — 주요 form 제출기한 매트릭스 + 해석 포인트
- `006-filing-calendar-rhythm.svg` — form별 공시 리듬 타임라인 (분기/연간)
- `006-filing-lifecycle.svg` — 이벤트 공시에서 정기보고 반영까지 라이프사이클
- `006-korean-investor-checklist.svg` — 한국 투자자용 EDGAR 실전 체크리스트

### 007 — 통합 EDGAR 실전 플레이북
- `007-edgar-form-tracking.svg` — 10-K/10-Q/8-K/20-F/6-K/13F 통합 추적 맵
- `007-why-integrated.svg` — 분리 독해 vs 통합 독해 차이
- `007-10k-reading-order.svg` — 10-K 내부 권장 읽기 순서
- `007-event-to-metric-map.svg` — 8-K 이벤트와 재무 지표 연결 맵
- `007-fpi-bridge.svg` — 외국기업(FPI) 20-F/6-K 브리지 구조
- `007-6k-timing-bridge.svg` — 본국 공시-EDGAR-정기보고 반영 타임라인
- `007-13f-signal-framework.svg` — 13F 활용 가능/금지 프레임
- `007-integrated-decision-tree.svg` — 통합 분석 의사결정 트리
- `007-search-intent-map.svg` — 검색 유입 의도별 답변 프레임

### 008 — 사업의 내용, 이 섹션이 투자 판단을 바꾼다
- `008-business-section-map.svg` — II.사업의 내용 핵심 5축 맵
- `008-same-growth-different-quality.svg` — 같은 성장률, 다른 품질 비교
- `008-ten-minute-checklist.svg` — 10분 실전 독해 체크리스트
- `008-market-competition-lens.svg` — 시장/경쟁 해석 렌즈
- `008-customer-concentration-risk.svg` — 고객 집중 리스크 경로
- `008-cost-pass-through-grid.svg` — 원가 전가 가능성 매트릭스
- `008-cross-validation-loop.svg` — II-재무제표-주석/감사 교차검증 루프
- `008-common-mistakes-heatmap.svg` — 자주 하는 실수 영향도 히트맵

### 009 — EDGAR 개별공시 원문 접근 가이드
- `009-edgar-access-path.svg` — submissions→URL조립→원문 접근 경로
- `009-edgar-url-builder.svg` — accession/CIK 기반 원문 URL 조립 규칙
- `009-edgar-api-stability-guide.svg` — EDGAR 수집 안정성 체크리스트
