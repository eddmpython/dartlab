# 랜딩 전체 모바일 최적화 — PRD·설계 원칙

> 상태: ★활성 (기획 박제, 구현 대기). 작성 2026-06-25.
> 범위 우선순위: **/report → /cards → 공통 헤더 → 나머지 surface 스윕**.
> SSOT 라우팅: [[ui]] · [[terminal_concept]] · `feedback_ui_rules` (12-col·shadcn·푸시 전 스크린샷 전수 눈검수·공개 터미널 무중단).

---

## 1. 목적 (왜) · 범위 (어디까지)

**목적** — GitHub Pages 랜딩(SvelteKit, base `/dartlab`)을 모바일에서 "쓸데없는 여백 없이 잘 읽히게" 만든다. 운영자가 직접 지목: **report 뷰는 낭비 여백 제거 + 모바일 가독성**, **cards 도 동일**, 그리고 **랜딩 전체**.

**범위** —
- **Phase 1 (핵심)**: `/report` 모바일 — 떠있는 A4 카드 거터 제거·유체 타이포·표/그리드 붕괴.
- **Phase 2 (핵심)**: `/cards` 모바일 — 피드 그리드 밀도·PostModal 풀스크린화.
- **Phase 3**: 공통 헤더(`terminal.css` topBar) 모바일 검증·보강 (report·cards·terminal 공유 SSOT).
- **Phase 4 (스윕)**: 나머지 surface — 홈(`/`)·blog·viewer·scan·map·skills — 375/414px 스크린샷 매트릭스 기반 낭비 여백·overflow 교정.

**비범위** — 신규 기능·레이아웃 재설계·신규 컴포넌트. 본 작업은 **CSS·반응형 마크업 한정**(JS 거동·데이터 배선 무변경). PWA·설치바·헤더 nav 는 이미 완료(직전 세션).

---

## 2. 현재 상태 실측 (조사 결과)

### 2.1 /report (`landing/src/routes/report/+page.svelte`)
- 헤더 `.rptHeader.dlTerm` = 터미널 topBar 재사용. `@media(max-width:640px)` 존재: `cmdBar` full-width, `perspLinks` order4 full-width 가로스크롤. terminal.css 640 이 `ghStars` 숨김. **헤더 기반은 양호**.
- 본문 모바일 대응 = `@media(max-width:860px)` **한 줄뿐**: `.sheet{max-width:calc(100vw-24px); padding:32px 22px 30px}` + `.coverTitle{28px}`.
- **낭비 여백 원천(우선 타깃)**:
  1. `.sheet` 가 다크 `--backdrop(#e8eaed/​#0a0c10)` 위에 뜬 카드 — `margin:28px auto 60px` + `border` + `border-radius:4px` + `box-shadow`(2겹) + 좌우 12px 거터(`calc(100vw-24px)`). 폰에서 양 끝 회색 거터 = 순수 낭비.
  2. 내부 패딩 데스크톱 `52px 56px` → 860 에서 `32px 22px`. 폰에선 여전히 큼.
  3. `.coverTitle 36px`(860→28px) — 폰에서 과대, 줄바꿈 위험.
  4. `.summaryTable td{padding:7px 28px 7px 0}` · `.figTable td{padding-right:24px}` — 우측 패딩이 좁은 화면에서 칸 낭비.
  5. `.clRow{grid-template-columns:54px 1fr auto}`(종합의견) — auto(출처라벨) 칸이 좁은 폭에서 압박.
  6. `.coverFacts{repeat(auto-fit,minmax(110px,1fr))}` + `border-right` 구분 — 폰에서 어색한 wrap.
- **양호(불변)**: `.bTableWrap{overflow-x:auto}` 가로스크롤 표 / `.toc` flex-wrap / `.barRow`·`.shareRow` 고정 소폭 라벨열 / 스파크라인.

### 2.2 /cards (`landing/src/routes/cards/+page.svelte`)
- 헤더 `.cHeader` sticky `padding:10px 18px`, topBar 재사용(640 공통 적용). **양호**.
- 피드 `.grid{repeat(auto-fill,minmax(340px,1fr)); gap:24px}` + `.feed{padding:24px 20px 80px}`. 360px 폰 → 1열(320px). 1열은 인스타 패턴이라 OK지만 **gap 24·padding 20 이 모바일 낭비**.
- `CoverThumb`(`landing/src/lib/cards/CoverThumb.svelte`) = 4:5, radius 16. badge 13px. **양호**, 모바일 미세 조정 여지(radius·서명 위치).
- `PostModal`(`landing/src/lib/cards/PostModal.svelte`) = `@media(max-width:820px)` 세로 스택(`max-height:92vh; overflow-y:auto`)까지 됨. **미흡**: `.post{padding:3vh 3vw}` 거터 + `.postInner{border-radius:14px; max-width:96vw}` → 폰에서 **풀스크린 미달**(양 끝·상하 거터 = 읽기 공간 낭비), 닫기버튼(`top:18px;right:22px`)이 스택 시 캐러셀 badge 와 겹칠 소지.

### 2.3 공통 헤더 (`ui/packages/surfaces/src/terminal/terminal.css`)
- `.topBar{height:36px; gap:14px}` + `@media(max-width:640px){flex-wrap:wrap; cmdBar order3 full; cmdInput 16px; ghStars 숨김}`. report·cards·terminal 3 곳 공유 SSOT.
- **검증 필요**: report 헤더 1행 = brand + topRight(테마토글 + BrandSwitch + BrandSocial 아이콘들). 320~360px 에서 줄바꿈/overflow 가능성 — **스크린샷 눈검수 후 판단**(과교정 금지).

### 2.4 나머지 (47개 media query / 31파일 = 부분 커버)
- blog `[slug]`(4) · map(3) · viewer-dev(3) 은 상대적 충실. 홈 `/`(Section 1) · scan(1) · skills(1) 등은 얕음. Phase 4 스윕에서 실측.

---

## 3. 설계 원칙 (모바일 우선 정련 — "강함은 깎아서")

> [[feedback_always_check_clutter]]: 패널·특수케이스 **추가가 아니라 제거**로 강화. 본 작업의 정수 = *지우기*(거터·과대 패딩·카드 크롬).

1. **엣지투엣지 — 거터를 죽인다.** 폰(<640)에서 `.sheet`/`.postInner` 의 "떠있는 카드" 크롬(side margin·border-radius·box-shadow·좌우 border) 제거 → 콘텐츠가 뷰포트 폭을 꽉 채우고 backdrop 거터 소멸. **최고 ROI 단일 변경.**
2. **유체 타이포(`clamp`).** 고정 px 헤딩을 `clamp(min, vw, max)` 로 — 과대 헤딩의 줄바꿈·과소 본문의 가독성 동시 해결. 표 숫자는 `tabular-nums` + `nowrap` 유지(숫자 줄바꿈 금지).
3. **표는 가로스크롤 유지 + 신호 + 패딩 축소.** `.bTableWrap` 가로스크롤은 보존(panel wide 정체성 — 숫자 격자 보존, [[feedback_panel_wide_identity]]). 모바일에서 셀 패딩 축소 + 우측 페이드 힌트로 "스크롤 가능" 신호.
4. **그리드는 깔끔히 붕괴.** `.clRow`·`.coverFacts` 등 다열 그리드는 폰에서 스택 또는 2열로. 고정 소폭 라벨열(`.barRow`·`.shareRow`)은 불변.
5. **헤더 밀도.** 기존 640 wrap 보존. 과교정 금지 — 스크린샷이 overflow 를 보일 때만 gap/라벨 축소.
6. **터치 타깃 ≥ 40px** 유지(닫기·탭·재생). iOS 입력 줌 방지 `font-size:16px`(이미 적용).

**브레이크포인트 전략** — 1차 모바일 = `max-width:640px`(기존 헤더 query 와 일치·일관). report 의 기존 `860px`(태블릿 단계)는 보존, 그 안쪽에 `640px` 단계 추가.

---

## 4. 수용 기준 (Acceptance)

- [ ] 375px·414px 폭에서 /report: 좌우 회색 거터 0, 본문이 화면 폭 채움, coverTitle 줄바꿈 안정, 표 가로스크롤 동작, 종합의견·coverFacts 가독.
- [ ] /cards: 피드 1열 거터 축소, PostModal 폰에서 풀스크린(상하좌우 거터 0), 닫기버튼 비충돌, 캡션 스크롤 정상.
- [ ] 공통 헤더 3곳(terminal·report·cards) 1행 brand+SNS 줄바꿈 없이 정렬(또는 의도된 2행), 가로 overflow 0.
- [ ] `npm run build`(svelte-check) 0 error. 데스크톱(>640) 시각 **무회귀**(스크린샷 대조).
- [ ] 운영자 스크린샷 전수 눈검수 통과 후에만 push (UI = 자동 push 금지, CLAUDE.md 예외).

상세 설계 → `01-report-and-cards-design.md`. 영향/테스트/롤백/평가 → `02-sweep-impact-tests-rollback-eval.md`.
