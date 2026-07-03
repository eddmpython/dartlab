# 블로그 풍부화 (Blog Enrichment) PRD

> **비전**: 블로그를 "끝까지 읽히는" 표면으로. 강한 내러티브(쉽게·재밌게 = 장기 주가견인) + 이야기가 정하는 비주얼(무제한) + 크로스링크(블로그↔카드↔팟캐스트) + 라이브 데이터(분기 재무·회사 뉴스·증권사 리포트) + 상단 액션바(팟캐스트·카드·공유·터미널). **없는 슬롯은 숨김.**
> **무게중심**: 8할이 조립. 기존 자산(SubjectHub·CompanyFinancials·MiniFinChart·podcast index)이 있어 대부분 신규빌드가 아니다. 진짜 신규 = 회사별 라이브 뉴스/리포트 데이터 + 주가 캔들 차트뿐.

## 운영자 지시 (원문 요지)
크로스링크 상호 배선 · 라이브 재무는 분기 강제 · 회사별 최신 뉴스+증권사 리포트 라이브 · 팟캐스트 발행 시 블로그 상단에 팟캐스트/카드/공유/터미널 버튼 · 주가그래프 배선(터미널 것 재활용) · 기획에 네러티브 집중+비주얼 기획을 녹인다. 없는 건 없게.

## 자산 맵 (서브에이전트 실측)

| # | 기능 | 핵심 경로 | 현재 동작 | 갭 |
|---|---|---|---|---|
| 1 | 크로스링크 | `landing/src/lib/subjects/{subjects.ts,SubjectHub.svelte}`, `cards/PostModal.svelte`, `cards/contract.ts` | 블로그→팟캐스트 O(하단), 카드→블로그/팟캐스트 O. 조인=stockCode/topicSlug | **블로그→카드 없음** (`loadCarousels()` + code 필터 추가); 팟캐스트 `links` 맵 미소비 |
| 2 | 라이브 재무 | `components/blog/CompanyFinancials.svelte`, `runtime/.../finance/annual.ts`, `blog/[slug]/+page.server.ts` | parquet 직독 → 빌드타임 prerender, HF 재fetch 0. **연간(q4)만** | **분기 미지원**(`-4` 필터 고정). MiniFinChart embed로 우회 가능 |
| 3 | 뉴스/리포트 | `PostModal.svelte`, `build_carousel_contracts.py`(relatedNews), 터미널 `MarketFeed.svelte` | relatedNews=**정적 frontmatter**, 카드 모달 전용. 터미널 라이브뉴스=시장전체(종목무관) | **회사별 라이브 뉴스/증권사 리포트 소스 부재** (신규 데이터 파이프) |
| 4 | 상단 버튼 | `blog/[slug]/+page.svelte`(header), `cards/share.ts`(공유헬퍼) | header=badge/날짜/제목/요약. **버튼 0**, 공유는 카드모달만 | 액션바 신규 (링크·조인키·공유헬퍼는 이미 존재 → 조립) |
| 5 | 주가 그래프 | `ui/.../charts/MiniFinChart.svelte`(재무), `PriceChart.svelte`(주가), `cards/CardSlide.svelte`(재사용 예) | MiniFinChart=순수 SVG, **landing 이미 재사용**. PriceChart=klinecharts 무겁고 강결합 | 재무차트 embed 즉시; **주가(캔들) 차트는 landing 부재**(`priceChart` visual 미구현) |
| 6 | 팟캐스트 인덱스 | `_podcasts/_lib/publish_podcast.py`, R2 `index.json`, `subjects/model.ts` | published → index.json. 제목→URL: 회사면 `/terminal?sym=` 딥링크 | **`youtubeId` 전부 빈값**(운영 갭); YouTube Music=RSS 수동 제출만 |

## 페이징 (게이트)

**P0 · 무빌드·무승인 (데이터 + 문서)**
- 데이터 워크벤치 채우기: 미등록 노트 type-extractor(지역별매출 NT_D831150 등 ~10종, 무빌드 `_attempts` 개념확립). 정본 = [[panel-note-extraction-ssot]] P0.
- 파이프라인 규율 명문화: PIPELINE.md 에 아래 "기획 규율" 반영(내러티브·비주얼·크로스링크·분기·라이브·버튼).

**P1 · UI (운영자 눈검수 + 승인 후 push; `landing/src`·`ui/**` 시각회귀 게이트)**
- MiniFinChart 블로그 embed → **분기 재무**(#2+#5 재무 동시, `CardSlide` 가 레퍼런스).
- 블로그 상단 **액션바**: 팟캐스트·카드·공유·터미널(발행된 슬롯만). 삽입점 = post-header, `subjectCode`/`subjectTopic` 재사용(#4).
- 블로그→카드 **크로스링크 섹션**: `loadCarousels()` + `code===subjectCode` 필터(#1). 없으면 숨김.
- `youtubeId` 값 주입 → 팟캐스트 유튜브 embed 활성(#6, 운영).

**P2 · 신규 데이터 (사전토론·승인 게이트)**
- 회사별 라이브 뉴스 + 증권사 리포트 파이프(#3). MarketFeed `rt.news.market()` 종목 필터 확장 또는 신규 소스.
- 주가 캔들 차트: landing 경량 신규 또는 terminal embed(#5 주가).

## 기획 규율 (PIPELINE.md 에 녹임)
- **내러티브**: 끝까지 읽히게·어렵지 않게·재밌게. 강한 내러티브 = 장기 주가견인. 어려운 내용일수록 비주얼을 강하게(제한 없음). blog-master-writer 게이트에 반영.
- **비주얼**: 이야기가 정한다(고정 템플릿 아님). 막별 차트·표·카드·주가그래프 배선. MiniFinChart 재무 + (P2) 주가 차트.
- **라이브**: 재무=분기 기준(최신성). 뉴스·리포트=회사별 라이브. 크로스링크·버튼·라이브 모두 **없으면 숨김**.

## NEVER
- 미완 슬롯 억지 표시(없으면 숨김). 정적 데이터를 라이브로 위장. UI 무단 push(눈검수·승인 게이트).

## 진행 원장
- 2026-07-03 기획: 서브에이전트 자산맵 실측 6기능 + 데이터 워크벤치 감사(추출엔진 완성·notesDetail 접근 확인). PIPELINE.md 데이터완주+이야기꺼리+막별 비주얼 기획 선반영(커밋 `1963d11`). 미착수(P0 데이터/문서만 무게이트).
- 2026-07-03 P1 착수(운영자 "푸시해" 명시 승인): 
  - **#5+#2 상단 액션바** = `landing/src/lib/blog/BlogActionBar.svelte` 신설. 팟캐스트(in-page 스크롤 `#related-podcast`)·카드뉴스(`?post=` 조인, code 매치)·터미널(`?sym=` 딥링크)·공유(navigator.share→클립보드). 발행 슬롯만 렌더(없으면 숨김). post-header 삽입. 블로그→카드 링크 갭 닫음.
  - **#3 분기 라이브 재무** = `annual.ts` 에 `buildQuarterlyFromRows`/`loadQuarterlyStatements`/`loadCompanyFinance`(parquet 1회 읽어 연간+분기 동시). flow 단일분기 환산은 financeSource `standalone` 라인 미러(검증 SSOT). BS=시점. `CompanyFinancials.svelte` 상단에 "분기 실적 · 최근 8분기"(IS ComboChart + IS/BS/CF 표) 추가, 연간 5개년은 아래 컨텍스트. `quarterly.test.ts` 7 테스트(YTD 차분·스냅샷·기간순서).
  - 검증: svelte-check 0 errors · runtime tsc 0 · vitest 14 pass · checkUiDataWiring PASS · em dash 0.
  - 남은 P1: `youtubeId` 값 주입(운영·실제 영상ID 필요). 남은 P2: 회사별 라이브 뉴스/증권사 리포트·주가 캔들(사전토론 게이트).
