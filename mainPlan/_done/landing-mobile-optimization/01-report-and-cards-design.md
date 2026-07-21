# Phase 1·2 — /report·/cards 모바일 구체 설계 (구현 명세)

> 자기충족 명세: 아래 CSS 블록을 해당 `<style>` 끝의 반응형 구역에 추가/치환한다. 모두 **모바일 한정 media query** — 데스크톱(>640) 규칙은 건드리지 않는다(무회귀). 색·토큰은 기존 `--*` 변수 재사용(신규 토큰 0).

---

## Phase 1 — `/report` (`landing/src/routes/report/+page.svelte`)

### 1.1 떠있는 A4 카드 → 폰 엣지투엣지 (최고 ROI)
현재 `@media(max-width:860px)` 블록(태블릿)은 **보존**하고, 그 아래에 640 단계를 **추가**한다. 기존:

```css
@media (max-width: 860px) {
  .sheet { max-width: calc(100vw - 24px); padding: 32px 22px 30px; }
  .coverTitle { font-size: 28px; }
}
```

추가할 블록:

```css
/* ── 폰 — '떠있는 용지' 은유 해제: 카드 크롬(margin·radius·shadow·side border) 제거하고
   콘텐츠가 뷰포트 폭을 꽉 채운다. backdrop 회색 거터 소멸 = 낭비 여백 0. ── */
@media (max-width: 640px) {
  .rptRoot { font-size: 13px; }
  .main { padding: 0; }
  .sheet {
    width: 100%; max-width: 100%; margin: 0; padding: 18px 14px 36px;
    border-left: 0; border-right: 0; border-top: 0; border-radius: 0;
    box-shadow: none;
  }
  /* 표지 — 유체 타이포, 과대 헤딩 억제 */
  .cover { padding: 4px 0 16px; margin-bottom: 18px; }
  .coverKicker { font-size: 11px; margin-bottom: 8px; }
  .coverTitle { font-size: clamp(21px, 6.4vw, 28px); margin-bottom: 12px; line-height: 1.12; }
  .coverTitle .code { display: block; margin: 6px 0 0; font-size: 13px; }
  .coverIntro { font-size: 12.5px; margin-top: 12px; }
  /* coverFacts — right-border 격자 → 2열 + bottom-border(폰에서 깔끔히 쌓임) */
  .coverFacts { grid-template-columns: 1fr 1fr; }
  .coverFacts .fact { padding: 8px 12px 8px 0; border-right: 1px solid var(--bd); border-bottom: 1px solid var(--bd); }
  .coverFacts .fact:nth-child(2n) { border-right: 0; }

  /* 통합 리드·블록 — 패딩·헤딩 축소 */
  .overviewLead { padding: 13px 13px; margin-bottom: 18px; }
  .ovThesis { font-size: 12.5px; }
  .block { margin-bottom: 20px; }
  .leadProse { font-size: clamp(13.5px, 4vw, 15px); }

  /* 요약·figure 표 — 우측 과패딩 축소(좁은 폭 칸 확보) */
  .summaryTable td { padding-right: 14px; }
  .figTable td { padding-right: 14px; }

  /* 본문 섹션 — 번호·제목 유체화, scroll-margin 헤더 높이 보정 */
  .rptSection { margin-bottom: 22px; scroll-margin-top: 132px; }
  .secHead { gap: 9px; margin-bottom: 11px; padding-bottom: 8px; }
  .secNo { font-size: 13px; }
  .secTitle { font-size: clamp(16px, 5vw, 19px); }
  .secSrc { font-size: 9.5px; padding: 2px 5px; }

  /* 표 — 가로스크롤 유지 + 셀 패딩 축소 + 우측 스크롤 힌트 페이드 */
  .bTableWrap { margin: 10px 0; -webkit-overflow-scrolling: touch; position: relative; }
  .bTable td, .bTable th { padding-left: 8px; padding-right: 8px; }
  .bTable td.sparkCol, .bTable th.sparkCol { display: none; } /* 폰에선 스파크열 숨김(숫자 격자 우선) */

  /* 종합 의견 — 3열 그리드 → 2행 스택(라벨/출처 한 줄, 본문 아래) */
  .clRow { grid-template-columns: 1fr auto; gap: 4px 10px; padding-left: 10px; }
  .clLine { grid-column: 1 / -1; font-size: 12.5px; }

  /* 푸터 — 서명/면책 촘촘히 */
  .rptFooter { margin-top: 24px; }
  .footSign { font-size: 11px; gap: 5px; }
}
```

근거:
- `.coverTitle .code{display:block}` — 데스크톱은 제목 옆 인라인 코드(margin-left:11px)지만 폰에선 긴 회사명+코드가 한 줄 못 들어가 줄바꿈이 지저분 → 코드만 아래 줄로.
- `.bTable td.sparkCol{display:none}` — 스파크열(74px)은 폰 가로스크롤에서 숫자 격자를 더 밀어낸다. 추이는 본문 line/bars 차트가 별도로 있어 손실 미미. (대안: 유지하되 폭 축소 — 스크린샷 비교 후 택1, **기본=숨김**.)
- `.clRow` 본문(`.clLine`)을 `grid-column:1/-1` 로 풀어 라벨+출처는 윗줄, 문장은 아랫줄 풀폭 → auto 칸 압박 해소.

### 1.2 헤더 scroll-margin 보정
모바일에서 헤더가 wrap 으로 높아진다(brand행+검색행+관점탭행 ≈ 3행). `.tocItem`/`scrollSec` 앵커가 sticky 헤더 밑에 가리지 않게 `.rptSection{scroll-margin-top:132px}` (위 블록 포함). 기존 데스크톱 100px 유지.

---

## Phase 2 — `/cards`

### 2.1 피드 그리드 밀도 (`landing/src/routes/cards/+page.svelte`)
`<style>` 끝에 추가:

```css
/* 폰 — 1열 피드 거터 축소(인스타 패턴 유지, 양 끝 낭비 제거) */
@media (max-width: 640px) {
  .feed { padding: 12px 12px 64px; }
  .grid { grid-template-columns: 1fr; gap: 14px; }
  .cHeader { padding: 8px 12px; }
}
```

`grid-template-columns:1fr` 로 명시(기존 `minmax(340px,1fr)` 도 360폰에서 1열이지만, 320폰에서 트랙이 340 요구→약간의 overflow 위험 → 1fr 로 확정).

### 2.2 PostModal 폰 풀스크린화 (`landing/src/lib/cards/PostModal.svelte`)
기존 `@media(max-width:820px)`(세로 스택) **보존**, 아래에 640 단계 추가:

```css
/* 폰 — 모달을 화면 꽉 채움(거터 0). 카드 위 / 캡션 아래 한 흐름으로 스크롤. */
@media (max-width: 640px) {
  .post { padding: 0; background: #050811; backdrop-filter: none; }
  .postInner {
    width: 100vw; max-width: 100vw; height: 100dvh; max-height: 100dvh;
    border: 0; border-radius: 0;
  }
  .postLeft { aspect-ratio: 1080 / 1350; }
  .prScroll { padding: 16px 14px 28px; }
  .prHead { padding: 12px 14px; }
  /* 닫기 = 상단 고정(캐러셀 badge 와 비충돌하게 좌상단 안전영역). 터치 44px. */
  .postClose {
    top: calc(8px + env(safe-area-inset-top, 0px)); right: 12px;
    width: 38px; height: 38px;
  }
}
```

근거:
- `height:100dvh`(dynamic viewport) — iOS Safari 주소창 가변 높이에서 잘림 방지. `100vh` 폴백은 dvh 미지원 브라우저용으로 기존 820 블록의 `max-height:92vh` 가 cascade 로 남으므로 안전.
- `.postClose` 좌상단 이동 안 함(우상단 유지)이되 캐러셀 `.badge`(우상단 회사명)와 겹침 → **닫기는 우상단, badge 는 Deck 내부 top:14px right:16px**. 닫기(38px, top 8px right 12px)가 badge 위로 떠야 함 → `z-index:2`(기존) < Deck badge `z-index:3`. **충돌 해소: 닫기 z-index 를 5 로 올린다**(아래 1.2 표에 포함). 추가 규칙:

```css
@media (max-width: 640px) { .postClose { z-index: 5; } }
```

### 2.3 CoverThumb 미세 (`landing/src/lib/cards/CoverThumb.svelte`) — 선택
피드 1열에서 radius 16 은 과하지 않아 **기본 무변경**. 스크린샷에서 서명/badge 가 좁은 폭에서 겹치면 그때 `@media(max-width:640px){.frame{border-radius:12px}}` 추가(과교정 금지 — 실측 후 판단).

---

## Phase 3 — 공통 헤더 (`ui/packages/surfaces/src/terminal/terminal.css`)

기존 640 query 보존. **스크린샷 선검수** 후 overflow 가 실제로 보일 때만:

```css
@media (max-width: 360px) {
  .dlTerm .topRight { gap: 8px; }
  .dlTerm .brandTag { display: none; } /* 초소형 폰 — 'report'/'cards' 태그 숨겨 brand+SNS 1행 확보 */
}
```

이 블록은 **조건부**(실측 overflow 시에만 적용). report·cards·terminal 3곳 동시 영향 → 3곳 모두 스크린샷.

---

## 검증 매트릭스 (구현 후)

| 폭 | /report | /cards 피드 | PostModal | 헤더 3곳 |
|---|---|---|---|---|
| 320px | 거터0·제목줄바꿈·표스크롤 | 1열·gap14 | 풀스크린·닫기 | overflow0 |
| 375px | 〃 | 〃 | 〃 | 〃 |
| 414px | 〃 | 〃 | 〃 | 〃 |
| 768px(태블릿) | 860 블록(무회귀) | minmax 2열 | 820 스택 | wrap |
| >1024(데스크톱) | **무회귀** | **무회귀** | **무회귀** | **무회귀** |
