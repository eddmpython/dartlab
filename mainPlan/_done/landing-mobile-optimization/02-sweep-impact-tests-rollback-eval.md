# Phase 4 스윕 + 영향·함수·테스트·롤백·평가 (plan-deep 5섹션 게이트)

---

## Phase 4 — 나머지 surface 스윕 (스크린샷 매트릭스 기반)

방법: `cd landing && npm run dev`(5173) 기동 후 DevTools 모바일(375·414px)로 각 surface 캡처 → 낭비 여백·가로 overflow·터치타깃 점검 → surface 별 media query 보강. 알려진 의심처:

- `landing/src/routes/+page.svelte` (홈 히어로/섹션) — 히어로 패딩·CTA 버튼 폭·섹션 그리드. `landing/src/lib/components/sections/Header.svelte`(메인 nav, 직전 세션 Cards 추가됨) 모바일 메뉴 정렬.
- `landing/src/routes/blog/+page.svelte` · `landing/src/routes/blog/[slug]/+page.svelte` — 본문 max-width·코드블록 가로스크롤·카루셀 임베드.
- `landing/src/routes/viewer/company/[stockCode]/+page.svelte` — 뷰어 패널/표 모바일(가장 복잡, 별도 주의).
- `landing/src/routes/scan/+page.svelte` · `landing/src/routes/map/+page.svelte` — 스크리너 테이블·지도 컨트롤.
- `landing/src/routes/skills/+page.svelte` · `landing/src/lib/components/skills/CategorySidebar.svelte` — 사이드바 폰 붕괴.

스윕은 **실측 후 surface 별 최소 패치**(엣지투엣지·패딩 축소·overflow 차단 원칙 §3 적용). 각 surface 1 commit 또는 묶음 1 commit, 모두 UI = 자동 push 금지.

---

## 영향 파일

- `landing/src/routes/report/+page.svelte` — `<style>` 에 `@media(max-width:640px)` 블록 추가(엣지투엣지 sheet·유체 타이포·표/그리드 붕괴·scroll-margin). 기존 860 블록·데스크톱 규칙 무변경.
- `landing/src/routes/cards/+page.svelte` — `<style>` 에 640 블록 추가(피드 1열·gap/padding 축소·헤더 패딩).
- `landing/src/lib/cards/PostModal.svelte` — `<style>` 에 640 블록 추가(풀스크린 모달·100dvh·닫기 z-index/위치). 기존 820 스택 블록 무변경.
- `landing/src/lib/cards/CoverThumb.svelte` — **조건부**(스크린샷에서 겹침 시에만 radius 640 블록).
- `ui/packages/surfaces/src/terminal/terminal.css` — **조건부**(헤더 overflow 실측 시에만 `@media(max-width:360px)` brandTag 숨김·gap 축소). report·cards·terminal 공유 SSOT.
- Phase 4 스윕 대상(실측 후): `landing/src/routes/+page.svelte` · `landing/src/lib/components/sections/Header.svelte` · `landing/src/routes/blog/+page.svelte` · `landing/src/routes/blog/[slug]/+page.svelte` · `landing/src/routes/viewer/company/[stockCode]/+page.svelte` · `landing/src/routes/scan/+page.svelte` · `landing/src/routes/map/+page.svelte` · `landing/src/routes/skills/+page.svelte`.

자동 생성물 영향 — **없음**(CSS·마크업 한정, 빌드 산출 외 생성물 무관).

## 영향 함수/심볼

JS 심볼·public API 변경 **없음** — 본 작업은 `<style>` 블록과 그 안의 CSS 선택자 한정. 신규/변경 "심볼" = CSS 미디어쿼리 규칙:

- `report/+page.svelte::@media(max-width:640px)` — 신규. 선택자: `.sheet`·`.cover`·`.coverTitle`·`.coverTitle .code`·`.coverFacts`·`.coverFacts .fact:nth-child(2n)`·`.summaryTable td`·`.figTable td`·`.rptSection`·`.secHead`·`.secTitle`·`.bTableWrap`·`.bTable td/th`·`.bTable td.sparkCol`·`.clRow`·`.clLine`·`.rptFooter`·`.footSign`.
- `cards/+page.svelte::@media(max-width:640px)` — 신규. 선택자: `.feed`·`.grid`·`.cHeader`.
- `PostModal.svelte::@media(max-width:640px)` — 신규. 선택자: `.post`·`.postInner`·`.postLeft`·`.prScroll`·`.prHead`·`.postClose`.
- (조건부) `terminal.css::@media(max-width:360px)` — 신규. 선택자: `.dlTerm .topRight`·`.dlTerm .brandTag`.

camelCase/PascalCase 룰 — JS 심볼 신설 없음(해당 없음). CSS 클래스는 기존 명명 재사용.

## 테스트

- **기존 자동 테스트 영향**: landing 의 CSS 단위 테스트 없음 → 자동 회귀 0. `tests/audit/checkUiDataWiring`(데이터 배선)·architecture 게이트는 데이터/import 무변경이라 **불영향**.
- **빌드 게이트(필수)**: `cd landing && npm run build` — `svelte-check` 0 error(타입·미사용·접근성). `vite build` 성공(manifest/sw 포함). 단, `BASE_PATH=/dartlab` 는 MSYS 경로변환 버그로 로컬 빌드 실패 가능(직전 세션 확인) → 로컬은 BASE_PATH 없이 빌드 검증, base 경로 정합은 CI(Linux)가 책임.
- **신규 검증(수동·필수)**: `feedback_ui_rules` 정량+눈검수 — 320/375/414/768/1024px 스크린샷 매트릭스(`01` 문서 표). **데스크톱 무회귀**(>640 변경 0 이므로 구조적 보장 + 스크린샷 대조). PostModal 은 실데이터 캐러셀 1편 열어 캡션 스크롤·닫기 확인.
- 테스트 실행은 dartlab Python 메모리 가드 무관(landing 은 npm). `bash tests/test-lock.sh` 해당 없음.

## 롤백

- Phase 별 **단일 논리 commit**(Phase1 report / Phase2 cards / Phase3 헤더 / Phase4 스윕은 surface 묶음). 각 commit 은 `git commit -o <명시 paths>`(CLAUDE.md 변경단위 룰).
- 실패·시각 회귀 시 `git revert <sha>` 한 줄로 원복 — CSS 추가뿐이라 부작용 없음. 자동 생성물 동기화 commit 없음(별도 revert 불요).
- 외부 API·SemVer(1.0.0) 영향 **없음**(UI 전용). deprecation shim 불요.
- `terminal.css` 변경 시 terminal·report·cards 3곳 동시 영향 → revert 도 3곳 동시 복구(단일 파일이라 자동).

## 평가 (개발자 렌즈 + PM 렌즈)

**개발자 렌즈** — 검토·반영:
- *무회귀 안전성*: 모든 변경이 `max-width` media query 안 → 데스크톱 cascade 불변. 구조적으로 회귀 불가(반영: 모든 블록을 640/360 안에 격리, 기존 규칙 치환 아닌 **추가**).
- *공유 SSOT 위험*: `terminal.css` 는 3 surface 공유 → 헤더 변경을 **조건부·360px 한정**으로 최소화하고 3곳 스크린샷 의무화(반영: Phase3 를 실측 게이트로 강등, 기본은 무변경).
- *엣지케이스*: (a) iOS dvh 미지원 → 820 블록 `max-height:92vh` 가 폴백 cascade(반영). (b) sparkCol 숨김으로 추이 손실 → line/bars 차트가 보완, 손실 미미(반영: 대안=폭축소를 스크린샷 후 택1로 명시). (c) `.coverTitle .code{display:block}` 로 표지 코드 줄내림 — 의도된 가독 개선. (d) 닫기버튼 z-index 충돌 → 5 로 상향(반영).
- *아키텍처/import 방향*: CSS·마크업만, 4계층 import·데이터 배선 무관. 공개 터미널 무중단(`feedback_ui_rules`) — 미배선 커밋 없음, 완결 단위만.
- *성능*: media query 추가는 런타임 비용 무시 가능. 신규 에셋·폰트·JS 0.

**PM 렌즈** — 검토·반영:
- *목표 적합*: 운영자 핵심 요구("report 쓸데없는 여백 없게 + 잘 읽히게", "cards 도")를 §3 원칙1(엣지투엣지 거터 제거)이 정면으로 푼다. report·cards 를 Phase1·2 로 우선(반영).
- *완결성*: "랜딩 전체" 요구 → Phase4 스윕으로 홈·blog·viewer·scan·map·skills 포함(반영). 단 스윕은 실측 기반이라 본 플랜에 픽셀까지 못 박지 않음 — **방법·대상·원칙은 박제, 픽셀은 스크린샷이 결정**(정당한 sweep 패턴, self-sufficiency 유지).
- *최고수준/정공법*: fallback·우회 없이 카드 은유 자체를 폰에서 해제하는 정공(반영). 과교정 방지 위해 헤더·CoverThumb 는 실측 조건부.
- *수용 기준 명확성*: `00` 문서 §4 Acceptance + `01` 검증 매트릭스로 합격선 고정(반영).
- *리스크*: 시각 회귀는 운영자 눈검수 게이트(UI 자동 push 금지)로 차단 — push 전 스크린샷 전수(반영).

**남은 단일 미결정**(구현 중 정공으로 즉결, 사용자 결심 불요): sparkCol 폰 처리 = 숨김 vs 폭축소 → 스크린샷 대조 후 가독 우월안 채택. brandTag 360 숨김 = overflow 실측 시에만.
