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

### 002 — OpenDART, 솔직한 리뷰
- `002-dart-timeline.svg` — DART 27년 역사 타임라인 (1999~2027)
- `002-api-categories.svg` — OpenDART 83개 API 6개 카테고리 구조
- `002-opendart-vs-edgar.svg` — OpenDART vs SEC EDGAR 비교

### 003 — 재무제표, 숫자만 보면 안 되는 이유
- `003-beyond-numbers-hero.svg` — Numbers Only vs Full Picture
- `003-same-numbers-different-stories.svg` — 같은 숫자, 다른 이야기 4가지
- `003-analysis-depth-pyramid.svg` — 분석 깊이 5단계 피라미드

### 004 — 사업보고서 텍스트, 이렇게 읽는다
- `004-reading-strategy.svg` — 읽기 전략 (우선순위별 4단계 + 페이지 분포)
- `004-industry-reading-focus.svg` — 업종별 핵심 읽기 포인트 6개 업종

### 006 — EDGAR의 모든 것
- `006-edgar-structure-map.svg` — EDGAR form 지도 (정기/수시/포지션 분류)
- `006-dart-vs-edgar-deep.svg` — DART vs EDGAR 심층 비교 매트릭스
- `006-edgar-reading-workflow.svg` — EDGAR 4단계 읽기 워크플로
- `006-edgar-deadline-matrix.svg` — 주요 form 제출기한 매트릭스 + 해석 포인트
- `006-filing-lifecycle.svg` — 이벤트 공시에서 정기보고 반영까지 라이프사이클
- `006-korean-investor-checklist.svg` — 한국 투자자용 EDGAR 실전 체크리스트
