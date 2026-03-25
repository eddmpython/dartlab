# Landing — 개발 가이드

## SEO 규칙

### Meta 태그 원칙
- `app.html`에는 **정적 fallback meta 금지** — 각 페이지 `<svelte:head>`가 책임
- `og:locale`은 `ko_KR` 고정 (한국어 사이트)
- `og:description`, `twitter:description`은 한국어로 작성
- `brand.ts`의 `descriptionKo`를 한국어 description source of truth로 사용
- 영문 `description`은 영문 컨텍스트(SoftwareApplication schema 등)에서만 사용

### JSON-LD Schema.org
- **홈페이지**: Organization + WebSite + SoftwareApplication (3개)
- **블로그 글**: BlogPosting + BreadcrumbList + FAQ(선택) — `seo.ts` 함수로 생성
- **문서 페이지**: TechArticle + BreadcrumbList + FAQ(선택)
- **`APIReference` 사용 금지** — Schema.org에 없는 타입. `TechArticle` 사용
- **publisher는 인라인**: article JSON-LD의 publisher에 `name` + `logo` 필수 포함 (dangling `@id` ref 방지)
- FAQ는 `parseFaqFromMarkdown()`으로 마크다운 `## FAQ` 섹션에서 자동 추출

### 링크 정합성
- Footer, Header, product-bridge 등 내부 링크는 **실제 배포된 경로만** 사용
- 미배포 페이지(`/docs/about`, `/search` 등)로의 링크 금지
- 블로그 글 안의 docs 참조: 숫자 prefix 없이 slug만 사용 (예: `docs/tutorials/disclosure`)

### robots.txt
- 모든 봇 `Allow: /`
- AI 봇 7종 명시적 허용: GPTBot, ChatGPT-User, OAI-SearchBot, ClaudeBot, Google-Extended, PerplexityBot, Applebot-Extended
- 수정 시 `landing/static/robots.txt` 직접 편집

### Sitemap
- `postbuild.js`가 빌드 시 자동 생성 (`build/sitemap.xml`)
- `extraPages` 배열: 미배포 페이지 포함 금지
- docs + blog + category + series URL 자동 수집

## 이미지 규칙

### Lazy Loading 정책
| 위치 | loading | fetchpriority | 이유 |
|------|---------|---------------|------|
| Header avatar | eager (기본) | — | 항상 above-fold |
| Hero avatar | eager (기본) | `high` | LCP 후보 |
| Problem/CTA/Footer 아바타 | `lazy` | — | below-fold |
| 블로그 썸네일 | `lazy` | — | 리스트 항목 |
| 블로그 글 아바타 | `lazy` | — | 헤더 아래 |
| 외부 이미지 (buymeacoffee 등) | `lazy` | — | 비필수 |

### 이미지 속성 필수
- `width` + `height` 반드시 명시 (CLS 방지)
- `alt` 반드시 명시 (접근성)
- `decoding="async"` 비핵심 이미지에 추가

### WebP 변환 (완료)
- avatar PNG 12개 → WebP 변환 완료 (2.1MB → 318KB, **85% 절감**)
- 모든 avatar img 태그 → `<picture>` + `<source type="image/webp">` + PNG fallback
- 동적 썸네일도 `.replace('.png', '.webp')` 패턴으로 WebP 우선 제공
- og-image.png, icon-*.png, favicon.png은 PNG 유지 (meta 태그/파비콘 호환성)
- 새 아바타 추가 시 PNG + WebP 둘 다 생성 필수

## 폰트 규칙

### 현재 폰트 스택
1. **Pretendard Variable** (한글/영문 본문) — jsdelivr CDN
2. **Inter** (영문 보조) — Google Fonts, `display=swap`
3. **JetBrains Mono** (코드) — Google Fonts, `display=swap`

### 폰트 최적화 현황
- Google Fonts: `display=swap` 적용 완료
- Pretendard: `preconnect` 적용 완료, dynamic subset 사용
- `font-display: swap`은 외부 CSS에 의존 (직접 제어 불가)

## brand.ts — 중앙 설정

- `brand.ts`가 landing 전역 설정의 source of truth
- `description` (영문), `descriptionKo` (한국어) 이중 관리
- `data` 블록: HuggingFace 데이터셋 디렉토리/라벨 정의 (`dataConfig.py`와 동기)
- `color` 블록: Tailwind `dl-*` 테마 색상 원본
- 버전 변경 시 `syncBrand.js`가 CSS 변수로 전파

## 빌드 & 배포

- `npm run build` = prebuild(syncBrand + syncBlogAssets) → vite build → postbuild(sitemap + llms.txt + feed.xml)
- 어댑터: `@sveltejs/adapter-static` (GitHub Pages)
- 기본 prerender: `/*`, `/docs/`, `/blog/`
- postbuild.js: docs redirect, sitemap, RSS feed, llms.txt, llms-full.txt, markdown mirror 자동 생성
