# 06. 퍼블릭 /scan 재작업 + DART/EDGAR 동시조회 (구현 완료, 눈검수 대기)

> 상태: P1~P4 구현 완료, **운영자 눈검수 + push 승인 대기** (2026-07-10).
> 근거: 21 에이전트 전문가 패널(8 영역 정찰 + 5 렌즈 설계 + 3 심사 + 5 주장 적대검증) + CDP 실브라우저 검증.
> 트리거: 운영자 "scan 라우터에서 뷰의 기능과 종목찾기와 레이아웃을 개선하고 다른 뷰어 스타일을 접목해 새로 만든다. dart 와 edgar 를 동시에 조회 가능한 메커니즘이 필요하다."

## 0. 패널이 뒤집은 것 (적대검증 5 주장 중 4 반증)

| 주장 | 판정 | 근거 |
|---|---|---|
| `terminal.css` 는 `.dlTerm` 스코프로 격리되어 통째 import 해도 안전하다 | **반증** | 805 줄부터 `.scrimWrap`·`.scrModal`·`.nd*`·`.scr*`·`.src*` 가 `.dlTerm` 접두 없이 전역이다. 게다가 `tUp/tDn` 이 green-up 이라 KR 빨강-up 표면의 상승색을 조용히 반전시킨다 |
| `viewer/CommandPalette.svelte` 를 scan 에 재사용할 수 있다 | **반증** | props 가 `SearchIndex`·`PanelTocResponse` 로 단일 회사 공시 panel 전용이다. `CompanySearch` 만 범용(`onpick`, `busy`) |
| `edgar/scan/finance.parquet` 만 있으면 US 를 그리드에 넣을 수 있다 | **부분 반증** | 파일은 공개(HTTP 200)가 맞고 DuckDB-WASM 이 읽는 것도 맞다. 그러나 산업 taxonomy(KSIC vs SIC) 와 통화가 충돌해 "넣기" 가 아니라 "격리해서 넣기" 다 |
| KR 과 US 를 한 그리드에 섞어도 조용한 오답은 없다 | **반증** | `terminal-shell/routeLoad.ts:74` 가 이미 KR 과 US 검색인덱스를 한 배열로 합치고, `revenue` 한 필드에 원 raw(1e11~1e14)와 조 USD(0.41)가 함께 산다. 지금 오답이 안 나는 이유는 가드가 아니라 **산업 문자열이 한글 vs 영문이라 우연히 안 겹친다**는 암묵 불변식뿐이다. `wonAsEok`(metrics.ts)는 무조건 1e8 로 나누고 "억원" 을 붙인다 |
| `/scan` 의 `page-head` 는 공유 헤더 SSOT 를 쓴다 | **생존(주장이 옳음)** | 공유 `Header.svelte` 는 상단에 별도로 얹혀 있고, `page-head` 는 자체 클래스로 만든 커스텀 컨트롤 스트립이다 |

심사 결과: **악마의 변호인 234 / 정보설계자 233** 이 상위. 즉 "새로 만든다" 의 정답은 전면 재작성이 아니라 **외과수술 + 못 섞게 만드는 계약**이었다.

## 1. 무엇을 만들었나

### 1.1 판정격자 (verdict.ts) . 종목찾기의 바닥

`evalCond` 가 결측을 **비대칭**으로 처리하고 있었다. 같은 null 이 `>=`·`<=`·`between` 에선 FAIL, `!=` 에선 PASS 였다 (`null != 5` 는 참). 그리고 `==`/`!=` 만 억원 스케일을 우회해 시가총액 `== 1000`(억원)이 raw `1e11` 과 비교되어 영원히 0 건이었다. 같은 함수가 `+page.svelte` 와 `ScreenBuilder.svelte` 에 두 벌 있었고 서로 달랐다.

조건 x 종목 = **PASS / FAIL / UNKNOWN** 격자를 1 급으로 만들었다. `members`·`nearMiss`·`funnel`·`coverage`·`relaxThreshold` 가 전부 그 격자의 파생이라 **새 fetch 가 0** 이다.

### 1.2 VerdictRibbon . 유일한 신규 컴포넌트

조건이 있을 때만 그리드 위에 한 줄. 실측 렌더:

```
2,664 › ROE >= 20% [23] ?472 › 부채비율 <= 30% [1] ?455 › 1사   결측 459  근접 483
                                                      [ROE ≥ 6.5 · 20사]  [부채비율 ≤ 326.8 · 20사]
```

`?472` = 데이터가 없어 판정 불가한 종목 수. 탈락이 아니다. 완화 칩은 임계를 역산해 "이 값으로 바꾸면 20 사" 를 말한다.

### 1.3 DART + EDGAR 동시조회 . 못 섞게 만드는 계약

**신규 베이크 0.** `edgar/scan/finance.parquet` 은 이미 공개 HF 발행분이라 브라우저 DuckDB-WASM 이 직독해 US 노드를 만든다 (`edgarNodes.ts`).

`marketScope.ts` 가 세 가지를 기계적으로 막는다.

1. **교차시장 비교 가능성은 단위에서 도출한다** (손 선별 0). 무차원(`%`·`배`·`점`·등급)만 시장을 가로지른다. `crossMarketComparable(def)` 가 `def.unit` 으로 판정.
2. **전체 보기에서 통화 컬럼 정렬 차단.** `현재가(원)`·`시가총액(억원)` 헤더가 비활성되고 이유를 말한다. 실측: `blocked: ["현재가 (원)", "시가총액 (억원)"]`, `sortable: [ROE, PER, PBR, 부채비율, 영업이익률, ...]`.
3. **백분위·히트맵은 시장별 파티션.** KR 분포로 US 셀을 칠하면 히트맵이 통화 스케일차를 "좋음/나쁨" 색으로 위조한다.

US 에 없는 개념은 `NA`(빗금)로, 결측은 `·` 로 그린다. **둘은 다른 사실이다.**

### 1.4 EDGAR 데이터 정직화 (실측 기반, 억지 캡 아님)

| 문제 | 실측 | 처방 |
|---|---|---|
| 자본잠식 기업의 ROE | 8,035 사 중 **2,316 사(28.8%)** 가 equity <= 0. 적자 x 음의 자본이 양의 ROE 로 뒤집힘 | 분모가 양수일 때만 비율이 정의된다. `null`(UNKNOWN). ROE 최대 **13,220,194% -> 4,306%** |
| 티커 없는 filer | **2,868 행(35.7%)** 이 stockCode 에 CIK 가 들어감 (펀드·신탁). id 가 CIK 면 드릴다운도 성립 안 함 | 알파벳으로 시작하는 티커만. US 검색인덱스(`buildSearchIndexUs`)의 "openable 티커만" 과 같은 기준 |
| 조건 1 개일 때 근접후보 | US 단일조건에서 **근접 6,028 사** = 탈락자 전원 | 조건 2 개 이상에서만 nearMiss. 조건을 지우면 보이는 것을 근접후보라 부르지 않는다 |

### 1.5 레이아웃 . 낭비 공간 회수

- 분포가 없으면 320px 트랙을 예약하지 않는다 (전에는 placeholder 문구만 띄운 채 상시 점유).
- 조건이 걸리면 하단 발굴 피드를 접어 그 높이(244~278px)를 표에 돌려준다. 조건 없음 = 아직 찾는 중이니 피드가 출발점, 조건 있음 = 결과가 주인공.
- 행 높이 36 -> 30px (한 화면 종목수 +20%).
- 죽은 CSS 15 규칙 제거 (`.page-sub`·`.detail-*`·`.d-*`·`.ph-*`·`.filter-strip*`).

### 1.6 스타일 접목 . 통째 복사가 아니라 재스코프

`terminal.css` 의 `.dlTerm` 로컬 var 백킹 패턴(8~59 줄)만 가져와 `.scan-page` 루트에 이식했다. 하드코딩 hex 35 곳이 로컬 var 로 모였고, `--scan-warn` 은 `tokens.css --p-amber-400(#fbbf24)` 과 동일값 실측이라 토큰에 위임했다. 나머지 슬레이트 중립은 토큰 계열(gray/ink)과 hex 가 달라 값을 보존했다 (토큰 승격은 시각 회귀 위험이라 별도 사이클).

`terminal.css` 통째 import 는 하지 않는다. 전역 오염 + 상승색 반전.

## 2. 실브라우저 검증 (CDP)

헤드리스 `--screenshot` 은 네트워크 완료를 안 기다려 US 로드를 못 잡는다. CDP 로 DOM 이 실제로 채워질 때까지 기다려 읽었다.

| 뷰 | 유니버스 | 결과 | 확인 |
|---|---|---|---|
| KR | 2,664 | ROE>=20 + 부채<=30 -> **1 사**(SK스퀘어) | 결측 459 · 근접 483 · 완화칩 2 |
| US | **8,045** (가드 전) | ROE>=25 -> 1,609 사 | `NA` 셀 130 · DuckDB ready 3.4s |
| ALL | **7,830** (2,664 KR + 5,166 US, 가드 후) | ROE 정렬 | 통화 컬럼 2 개 정렬 차단 · `NA` 셀 300 |

## 영향 파일

- `ui/packages/surfaces/src/scan/verdict.ts` (신규) . 3-state 판정 SSOT + funnel/nearMiss/coverage/relaxThreshold/condLabel
- `ui/packages/surfaces/src/scan/marketScope.ts` (신규) . 시장 차원 + 교차비교 가능성 + 정렬 차단 + 시장별 백분위
- `ui/packages/surfaces/src/scan/edgarNodes.ts` (신규) . EDGAR 런타임 로더 (베이크 0)
- `ui/packages/surfaces/src/scan/VerdictRibbon.svelte` (신규) . 유일한 신규 컴포넌트
- `ui/packages/surfaces/src/scan/{verdict,marketScope,url}.test.ts` (신규) . 골든 벡터 + URL 계약 동결
- `ui/packages/surfaces/src/scan/Grid.svelte` . NA 셀 · 근접후보 amber 격리 · 시장별 히트맵 · 정렬 차단 헤더 · ROW_H 30
- `ui/packages/surfaces/src/scan/ScreenBuilder.svelte` . 자체 evalCond 삭제 · 미리보기 결측 노출
- `ui/packages/surfaces/src/scan/{index,marketChip,types,url}.ts` . 공개 표면 · US 칩 · `m` 키 · sanitize
- `landing/src/routes/scan/+page.svelte` . 판정격자 소비 · 시장 스위치 · 레이아웃 · 색 백킹
- `landing/vitest.config.ts` . surfaces scan 테스트를 같은 러너로

## 영향 함수/심볼

| 심볼 | 파일 | 변경 |
|---|---|---|
| `evalCond` | `landing/src/routes/scan/+page.svelte:257` | 삭제 -> `evalVerdict` (3-state) |
| `evalCond` (중복) | `ScreenBuilder.svelte:177` | 삭제 -> 같은 SSOT |
| `numericFilterValue` | `+page.svelte:240` | `normalizeNumeric` 으로 이관. 모든 op 에 동일 스케일 |
| `filteredNodes` | `+page.svelte:289` | `every(evalCond)` -> `grid.members` |
| `percentiles` | `+page.svelte:151` | `percentilesByMarket` (시장 파티션) |
| `cellHeatmapBg` | `Grid.svelte` | 행의 시장 분포를 쓰도록 `(rd, key, v)` |
| `handleSortClick` | `Grid.svelte` | `sortableKey` 가드 |
| `ROW_H` | `Grid.svelte:106` | 36 -> 30 (CSS `.row` 와 동시) |
| `pct` | `edgarNodes.ts` | 분모 `> 0` 강제 (자본잠식 ROE 부호뒤집힘 차단) |
| `nearMiss` | `verdict.ts` | `conds.length <= k` 면 빈 목록 |

## 테스트

- `verdict.test.ts` 23 . 회귀핀 3 종(`null != 5` -> UNKNOWN, `null >= 5` -> UNKNOWN, `marketCap == 1000` 억원 스케일) + 격자 파생 + 임계 역산.
- `marketScope.test.ts` 17 . 단위 도출 비교가능성 · 정렬 차단 + 사유 문장 · NA vs 결측 · 시장별 백분위(표본 부족은 분포 없음).
- `url.test.ts` 18 . `?q=` 계약 동결. v1(/screener) 하위호환 · sanitize · 왕복 · **`m` 키 additive**(옛 링크는 m 없이 KR).
- 전체: **vitest 145 pass**, `svelte-check` **0 error**.
- 실브라우저: CDP 프로브로 3 뷰 DOM 검증 (위 표).

## 롤백

- 4 커밋 분리 (판정격자 / 동시조회+레이아웃 / 색 백킹 / 문서). 각각 `git revert` 로 독립 복구.
- `?q=` 스키마는 `m` optional 추가뿐이라 옛 공유 링크 무변경. 스키마 동결 테스트가 지킨다.
- 유일한 의도적 동작 변경은 결측 3 종 핀이다. 버그 정정이며 골든 벡터가 이동 범위를 못박는다.
- **push 보류.** 프론트 변경은 운영자 눈검수 + 명시 승인 후에만 (`[[feedback_ui_rules]]`).

## 평가 (개발자 / PM)

### 전문 개발자 평가

가장 값진 발견은 코드가 아니라 데이터였다. EDGAR ROE 최대값이 1,322 만 %였고 원인은 자본잠식 2,316 사의 부호뒤집힘이었다. 이건 캡을 씌울 문제가 아니라 **분모가 양수일 때만 비율이 정의된다**는 회계의 문제다. 실브라우저로 눈으로 보지 않았으면 테스트 145 개가 전부 초록인 채로 나갔다.

`terminal.css` 를 안 가져온 것도 실측이 막았다. 문서 주석은 "모든 선택자 `.dlTerm` 하위" 라 적혀 있지만 805 줄부터 전역이다. 주석을 믿었으면 landing 전체에 모달 클래스를 뿌렸다.

남은 부채: `Grid.svelte` 내부에도 하드코딩 슬레이트가 남아 있다. 그 파일은 2,664 행 가상스크롤을 지탱하는 검증된 코어라 이번에 건드리지 않았다. `metrics.ts` 의 `wonAsEok` 은 여전히 무조건 억원을 붙이는데, US 절대금액 컬럼이 `NA` 로 막혀 있어 지금은 노출되지 않는다. 통화 포맷터는 다음 사이클.

### PM 평가

운영자 지적이 정확했다. `/scan` 은 sitemap 등재 실물이고 `/screener`·`/map/screen` 이 전부 리다이렉트하는 스크리너의 유일한 얼굴인데, 직전 플랜(04)은 그걸 마지막 단계로 밀어 두고 파이썬 라이브러리부터 손보게 짜여 있었다. 화면이 0mm 도 안 움직이는 계획이었다.

체감 순서는 실측이 정했다. "조건 넣었더니 0 건" 의 원인이 임계값인지 데이터가 없어서인지 지금까지 알 방법이 없었다. 리본 한 줄이 `?472`(판정 불가)를 말하는 순간 그 좌절이 사라진다. 새 데이터 fetch 는 0 이다.

DART+EDGAR 는 "합치기" 가 아니라 "못 섞게 만들기" 로 정의해야 제품이 된다. 7,830 사를 한 표에 놓되 통화 컬럼 정렬을 헤더에서 막고, 시장별로 히트맵을 나누고, 없는 개념을 `NA` 로 그린다. 정직이 기능이다.

다음 결정 3 개는 운영자 몫이다. ① 눈검수 후 push ② `page-head` 를 공유 헤더 SSOT 로 옮길지 (지금은 커스텀 스트립) ③ US 절대금액 컬럼을 통화 포맷터와 함께 열지, 계속 `NA` 로 둘지.

## Do-not-build

- `terminal.css` 통째 import (전역 오염 + 상승색 반전).
- `viewer/CommandPalette` cross-import (props 가 공시 panel 전용).
- 전체 보기에서 통화 컬럼 정렬 허용.
- KR 34 KSIC 를 US SIC 에 덮어쓰기 (오분류 위조). `SIC:*` 네임스페이스 격리 유지.
- `universe-monthly.parquet` 에 재무 컬럼 신설 (베이크. 운영자 사전승인 사안).
- 네이버 파생 `per`/`pbr`/`dividendYield` 를 새 정렬키·US 컬럼·발굴축으로 확대 (05 의 P0 미해결).
- `Grid.svelte` 가상스크롤·colWidth·stickyOffsets 재작성 (2,664 행을 지탱하는 검증 코어).
- 눈검수 전 push.

## 진행 원장

- 2026-07-10: 21 에이전트 패널(8 정찰 + 5 설계 + 3 심사 + 5 적대검증). 판정격자 + 동시조회 + 레이아웃 + 색 백킹 구현. vitest 145 pass · svelte-check 0 error · CDP 3 뷰 실검증. **눈검수 + push 승인 대기.**
