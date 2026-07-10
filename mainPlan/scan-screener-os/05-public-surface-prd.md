# 05. 퍼블릭 표면 우선 (04 정정 + P0 저작권 응급)

> 상태: 조사 완료, **P0 승인 대기** (2026-07-10). 본 문서가 `04-screener-os-prd.md` 의 실행 순서를 정정하고 대체한다.
> 근거: 8 영역 병렬 정찰(119 사실, file:line 그라운딩) + 3 렌즈 독립설계 + 3 심사 + 5 주장 적대검증.
> 트리거: 운영자 "랜딩에 scan 라우팅되어 있는데 무시하나."

## 0. 04 의 세 가지 오류 (정정)

운영자 지적이 맞다. 04 는 라이브러리를 먼저 고치고 퍼블릭 화면을 마지막(P5)에 두었다. 순서가 거꾸로였다. 조사 결과 04 의 사실관계 오류도 둘 더 나왔다.

| 04 의 주장 | 실측 | 판정 |
|---|---|---|
| 퍼블릭 프론트는 "붕괴시킬 중복 2,800 LOC" 이므로 마지막 | `/scan` 은 sitemap.xml:1509 등재 실물이고 `/screener`·`/map/screen` 이 전부 리다이렉트하는 **스크리너의 유일한 얼굴**. python `executeScreenSpec` 소비 0 | **순서 오류.** 라이브러리를 아무리 고쳐도 사용자 화면은 0mm 움직인다 |
| `ecosystem.json` 은 scan 20 축을 구운 것 | 2,664 노드 x 51 필드 + 18,418 엣지 **그래프 문서**. scan 27 축 중 **12 축**만 굽고, networkx Kamada-Kawai 레이아웃 x/y 좌표를 품는다 (`buildIndustryMap.py:477-502,910-911`). SQL 로 산출 불가 | **사실 오류.** 완전 제거 불가. metric/delta 층만 런타임 이관 가능 |
| `universe/engine.ts` 에 재무 스크린 소켓을 꽂는다 | `universe/ranking.ts:2` 가 명시한다. "재무 팩터 랭킹은 금지 (상폐사 재무 13.9% 생존편향)". `universe-monthly.parquet` 에 재무 컬럼 0 (`load.ts:26`) | **순진했다.** 랭킹 슬롯이 아니라 **새 PIT 재무 데이터층 신설** = 베이크 = 운영자 사전승인 사안 |

살아남은 것: **판정격자(VerdictGrid) 개념**. 그리고 그 개념의 적용지는 python 이 아니라 브라우저다.

## 1. P0 저작권 응급 정지 (다른 모든 것에 선행)

**네이버에서 스크랩한 전종목 밸류에이션이 공개 HF 데이터셋으로 매일 발행되고, 퍼블릭 스크리너가 브라우저에서 그것을 직접 읽어 화면에 렌더한다.** 5 단계 체인 전부 직접 확인했다.

1. `src/dartlab/scan/financial/valuation.py:88` . `from dartlab.gather.domains.naver import fetchPrice`
2. `valuation.py:121-129` `_RAW_SCHEMA` . 발행 컬럼 = `marketCap, per, pbr, dividendYield, current, snapshotAt`
3. `.github/workflows/valuationSnapshot.yml:14` cron 매일 . `prebuildValuation.py:52-56` `api.upload_file(repo_id="eddmpython/dartlab-data", path_in_repo="dart/scan/valuation.parquet")`
4. `landing/src/lib/data/valuationRuntime.ts:4` . 브라우저가 `dart/scan/valuation.parquet` 를 무인증 fetch. `curl -I` 로 302 확인 (= 공개)
5. `landing/src/routes/scan/+page.svelte:225,972` + `metrics.ts:518,604` . `per`·`pbr`·`dividendYield` 가 퍼블릭 그리드 컬럼

규칙 `[[feedback_copyright_no_prebuild_local_only]]` 는 정확히 이것을 금지한다. "Naver 스크랩... 프리빌드 파케·HF 발행·재배포 **절대 금지**. scan 노출은 valuation 처럼 **런타임 fetch 축으로만** (전종목 파케 금지)." 세 조항 모두 위반이다. HF 데이터셋 라이선스는 CC BY 4.0 (재배포 허용) 이라 노출이 더 무겁다. **기계 가드는 없다** (`valuationPublishLint` 는 투자권유 금어 lint 로 무관).

경계선은 정확하다. `marketCap`·`current` 는 KRX 공식 OpenAPI 벌크(`gov/prices`)에 있어 발행 가능하다. **KRX 에 없는 `per`·`pbr`·`dividendYield` 세 컬럼만이 네이버 고유 파생**이며 곧 위반의 실체다.

### 조치 (승인 즉시, 순서 고정)

1. **발행 중단**: `valuationSnapshot.yml` cron 비활성 + `prebuildValuation.py` 업로드 경로 차단.
2. **원격 정리**: HF `dart/scan/valuation.parquet` 삭제 또는 발행가능 컬럼(`marketCap`,`current`,`snapshotAt`)만 남긴 재업로드. **운영자 명시 승인 필요** (원격 삭제는 되돌리기 어렵다).
3. **컬럼 공백 방지 (정공법)**: `per`·`pbr`·`dividendYield` 를 발행가능 원천으로 재계산한다. 새 스크랩 0, 새 원천 0.
   - `per = marketCap(KRX gov/prices) / netIncomeTTM(DART finance)`
   - `pbr = marketCap / total_stockholders_equity(DART)`
   - `dividendYield = DPS(DART dividend) x shares / marketCap`
4. **기계 가드 신설**: 필드 카탈로그에 `publishBoundary` 속성 동결 (`publishable` = DART + KRX gov / `localOnly` = 네이버). `tests/audit/publishBoundary.py` 가 HF 업로드 스크립트의 발행 컬럼과 대조해 `localOnly` 유출 시 PR 차단. 네이버 원본은 로컬 런타임 축(`scanValuation(refresh=True)`)으로만 남긴다.

이 P0 를 건너뛰고 제품 기능을 붙이면 위반을 확대재생산한다. 심사위원 3 인 중 3 인이 독립적으로 같은 결론을 냈다. `/scan` 그리드가 `per`/`pbr` 를 더 눈에 띄는 표면으로 만들기 때문이다.

## 2. 같은 병, 두 몸: 결측이 fail 로 위조된다

04 는 python `_innerJoinOnStock` 이 결측을 조용히 지운다고 했다. 프론트는 **더 나쁘다**. 비대칭으로 틀린다.

```javascript
// landing/src/routes/scan/+page.svelte:275-282
if (c.op === '==') result = v == expected;      // 느슨한 비교 + 억원 스케일 우회
else if (c.op === '!=') result = v != expected; // null != 5 -> true. 결측이 PASS
else {
  const num = numericFilterValue(node, c.metric);
  if (num === null || Number.isNaN(target)) result = false;  // 결측이 FAIL
  ...
}
```

같은 결측이 `>=`·`<=`·`between` 에서는 FAIL, `!=` 에서는 PASS 다. 그리고 `==`/`!=` 는 `numericFilterValue` 를 우회해 억원 스케일(`/1e8`)이 적용되지 않는다. 사용자가 시가총액 `== 1000` (억원) 을 입력하면 raw `1e11` 과 비교되어 영원히 0 건이다. `filteredNodes` 는 `every(evalCond)` 하드필터라 (`+page.svelte:289-307`) 결측 종목은 흔적 없이 사라진다.

**결론**: 판정격자는 boolean 이 아니라 **3-state (PASS / FAIL / UNKNOWN)** 여야 한다. UNKNOWN 은 members 에서 빠지되 coverage 와 nearMiss 에 별도 계상된다. 이것이 `missing > wrong` 의 기계적 구현이다.

## 3. 제품 우선 순서 (심사 승자 설계, 합계 170/300)

핵심 통찰: 근접후보·깔때기·결측정직·민감도·조건별 백분위는 **이미 로드된 `allNodes` 위 순수 클라이언트 재계산 파생**이다. 새 엔진 0, 새 축 0, 새 HF fetch 0. 지금 당장 된다.

| 단계 | 내용 | 사용자가 얻는 답 | 비용 |
|---|---|---|---|
| **P1** | 결측 정직. `evalCond` 를 `eval.ts` 로 추출 + 3-state 화 + `coverageStats`. Grid 헤더에 컬럼별 커버리지 마이크로바 (n/2664) | "이 지표는 3,000 사 중 몇 사에 있나" | fetch 0. 가장 쌈 |
| **P2** | 깔때기 + 민감도. `VerdictFunnel.svelte` 1 개를 filter-strip 아래 | "어느 조건이 실질 컷인가. 40 종목 되려면 임계값을 얼마로" | 신규 컴포넌트 1 |
| **P3** | 근접후보. `nearMiss` + Grid amber 존 + 푸터 토글 | "아깝게 1 개 못 맞춘 회사" (체감 최대) | prop 추가 |
| **P4** | 조건별 백분위. `CellTooltip` 한 줄 | "이 회사는 이 조건에서 어디쯤인가" | 신규 컴포넌트 0 |
| **P5** | 정직한 바스켓 궤적. `UniverseSpec.memberCodes` (buckets 강제 1) + 생존편향 hero 차단 배너 | "이 스크린을 지금 들고 있었으면" | engine 3 줄 |
| **P6** | **착수 금지.** 생존편향 없는 PIT 리밸 백테스트는 `universe-monthly` 에 per-ym 재무 멤버십 컬럼 신설 = 베이크. 운영자 사전승인 사안. **제안까지만** | "이 스크린이 과거에 돈이 됐나" | 승인 게이트 |

### P5 의 정직 규율 (최대 리스크)

정적 바스켓 궤적을 사용자가 "백테스트" 로 오독하면 생존편향 결과를 신뢰한다. 배너 라벨로는 부족하다. `engine.ts:169` 의 `headlineSuppressed` 패턴을 그대로 적용해 **hero 숫자 자체를 차단**하고 `spreadEndPct` 를 표기하지 않는다. `id !== stockCode` 종목(우선주 등) 조인 실패 수를 "매칭 M/N 사" 로 정직 표기한다.

### near-miss 격리 규율

셀 히트맵 분위(p10/p90)는 **members 만으로** 계산을 유지한다. near-miss 행을 섞으면 랭킹과 히트맵이 오염된다. amber 존으로 시각 격리한다.

## 4. 라이브러리는 프론트를 따라간다 (역전)

04 는 python spec 이 SSOT 이고 프론트가 소비하기를 원했다. 조사 결과 그 방향은 지금 불가능하다. pyodide 노트북은 KRX listing 부재로 `scan("screen")` 자체가 안 돌고, `EngineCall` 은 spec 을 무시하고 축만 실행한다. python spec 엔진의 실사용 표면은 **라이브러리 직호출 + 미배포 왓처** 둘뿐이다.

그래서 SSOT 는 코드가 아니라 **의미론**이어야 한다.

- `eval.ts` (TS) 와 `_applyCondition` (python) 이 **골든 conformance 벡터** 한 파일(`tests/fixtures/screenConformance.json`)을 공유한다.
- 벡터에 실측 발산 3 핀을 회귀핀으로 박는다. `!=`-on-null, `==`-loose, 억원 단위 우회.
- python 판정격자(04 의 P1)는 같은 벡터를 통과해야 병합된다.

이러면 언젠가 프론트가 python spec 을 소비하게 되어도 답이 갈리지 않는다. 지금 당장 배선을 옮기지는 않는다 (미증명 registry 에 소비자 선배선 금지).

## 5. 병행 부채 (본 계획 범위 밖, 기록만)

- **raw SQL 이 이미 퍼블릭에 노출**. `SqlNotebook`/`SqlEditor` 가 `finance-lite` 에 임의 SELECT 를 허용한다. `finance-lite` 는 연결/별도·분기누적·동의어를 담은 raw long-form 이라 python resolver 를 우회하면 조용한 오답이 난다. `00-prd` F3 의 "raw SQL 계약 노출 금지" 판정과 문언상 충돌한다. 층위(탐색 표면 vs 스크린 계약)가 다르다는 반론 여지는 남는다. **운영자 판정 필요.**
- **UI 데이터 배선 규칙 우회**. `landing/src/lib/data/duckdb.ts` 가 자체 `HF_RESOLVE` + `read_parquet` 로 코어와 origins 레지스트리를 우회한다. 게이트 `checkUiDataWiring` 의 글롭이 `adapters/**/sources` 로 한정되어 `surfaces`·`landing` 을 못 본다. 사각지대다.
- **결과셋 CSV export 부재**. 필터·정렬된 실제 스크린 결과를 파일로 가져갈 경로가 메인 그리드에 없다. CSV 는 데이터탐색 모달의 raw 테이블에서만 가능하다.

## 영향 파일

- `.github/workflows/valuationSnapshot.yml` . cron 비활성 (P0)
- `.github/scripts/sync/prebuildValuation.py` . 업로드 컬럼 화이트리스트 (P0)
- `src/dartlab/scan/financial/valuation.py` . `_RAW_SCHEMA` 발행/로컬 분리, 네이버 경로 로컬 전용 강등 (P0)
- `src/dartlab/scan/builders/kr/valuationBuild.py` . 발행가능 원천 재계산 경로 (P0-3)
- `tests/audit/publishBoundary.py` (신규) . `localOnly` 유출 PR 차단 게이트 (P0-4)
- `src/dartlab/scan/builders/kr/report/fieldCatalog.py` . 필드당 `publishBoundary` 속성 (P0-4)
- `ui/packages/surfaces/src/scan/eval.ts` (신규) . 3-state 판정 의미론 SSOT (P1)
- `ui/packages/surfaces/src/scan/verdict.ts` (신규) . `buildVerdictGrid` / `coverageStats` / `buildFunnel` / `nearMiss` / `sensitivity` / `conditionPercentile` (P1~P4)
- `landing/src/routes/scan/+page.svelte` . `evalCond`·`numericFilterValue` 를 `eval.ts` 로 이관, `filteredNodes` 를 격자 소비로 (P1~P3)
- `ui/packages/surfaces/src/scan/Grid.svelte` . 헤더 coverage 마이크로바, near-miss amber 존 (P1, P3)
- `ui/packages/surfaces/src/scan/VerdictFunnel.svelte` (신규) . 유일한 신규 컴포넌트 (P2)
- `ui/packages/surfaces/src/scan/CellTooltip.svelte` . 조건별 백분위 한 줄 (P4)
- `ui/packages/surfaces/src/scan/universe/{types.ts,engine.ts}` + `UniverseBacktester.svelte` . `memberCodes` 바스켓 모드 + hero 차단 (P5)
- `ui/packages/surfaces/src/scan/ScreenBuilder.svelte` . 자체 `evalCond` 제거, `eval.ts` 소비 (P1)
- `tests/fixtures/screenConformance.json` (신규) . python/TS 공유 골든 벡터
- `landing/src/lib/data/valuationRuntime.ts` . 발행가능 컬럼만 읽도록 (P0-3)

## 영향 함수/심볼

| 심볼 | 파일 | 변경 |
|---|---|---|
| `evalCond` | `landing/src/routes/scan/+page.svelte:257` | `eval.ts` 이관 + boolean -> `Verdict` (PASS/FAIL/UNKNOWN) |
| `numericFilterValue` | 같은 파일 `:240` | 모든 op 에 `filterScale` 동일 적용 (`==`/`!=` 우회 제거) |
| `filteredNodes` | 같은 파일 `:289` | `every(evalCond)` -> `grid.members` |
| `evalCond` (중복) | `ScreenBuilder.svelte:177` | 삭제. `eval.ts` 단일 소비 |
| `_RAW_SCHEMA` | `scan/financial/valuation.py:121` | `_PUBLISHABLE_SCHEMA` / `_LOCAL_SCHEMA` 분리 |
| `_upload` | `.github/scripts/sync/prebuildValuation.py:33` | 발행 컬럼 화이트리스트 강제 |
| `fetchValuationRaw` | `scan/financial/valuation.py:143` | 로컬 전용 표기 + prebuild 경로에서 분리 |
| `buildVerdictGrid` (신규) | `surfaces/src/scan/verdict.ts` | `(nodes, conds) -> Verdict[][]` |
| `coverageStats` (신규) | 같은 파일 | 컬럼별 `{valid, total}` |
| `buildFunnel` (신규) | 같은 파일 | 조건별 `{pass, fail, unknown}` 누적 |
| `nearMiss` (신규) | 같은 파일 | FAIL 정확히 k, UNKNOWN 0 |
| `eligibleRanked` | `universe/ranking.ts` | `memberCodes` 자격필터 수용 (랭킹신호 아님) |
| `runUniverse` | `universe/engine.ts:77` | `UniverseSpec.memberCodes` 시 buckets=1 바스켓 모드 |

## 테스트

- `tests/fixtures/screenConformance.json` (신규). 골든 벡터. 각 케이스 = `{field, value, op, threshold, expect: PASS|FAIL|UNKNOWN}`. 회귀핀 3 종 필수 포함: ① `null != 5` -> UNKNOWN (현재 TS 는 PASS) ② `marketCap == 1000` 억원 스케일 적용 ③ `null >= 5` -> UNKNOWN (현재 TS 는 FAIL).
- `ui/packages/surfaces/src/scan/eval.test.ts` (신규, vitest). 골든 벡터 전수 통과.
- `tests/scan/test_screen_conformance.py` (신규). python `_applyCondition` 이 **같은 벡터**를 통과. 두 구현의 의미론 동결.
- `ui/packages/surfaces/src/scan/verdict.test.ts` (신규). ① `members` 가 기존 `every(evalCond)` 결과와 일치 (회귀 0. 단 위 3 핀 제외, 그건 의도된 정정) ② `nearMiss(1)` 이 FAIL 1 + UNKNOWN 0 만 ③ funnel 누적합 = 유니버스 크기 ④ coverage 가 UNKNOWN 을 fail 로 계상하지 않음.
- `tests/audit/publishBoundary.py` (신규). ① 모든 카탈로그 필드에 `publishBoundary` 존재 ② HF 업로드 스크립트가 쓰는 컬럼에 `localOnly` 0 건 ③ `valuation.parquet` 발행 스키마에 `per`/`pbr`/`dividendYield` 부재.
- URL 회귀: 기존 `?q=` base64 페이로드 스냅샷 20 건. `sanitizePayload` 화이트리스트라 크래시는 없으나 결과 이동을 스냅샷으로 박제.
- 게이트: `uv run python -X utf8 tests/run.py preflight` + `npm run check` (landing) + `npm run test` (surfaces vitest).
- **눈검수 필수**: P1~P5 는 전부 프론트. 스크린샷 전수 검수 전 push 금지 (`[[feedback_ui_rules]]`).

## 롤백

- **P0** 은 되돌리면 안 되는 방향의 변경이다 (위반 정지). cron 비활성은 yml 한 줄 revert 로 복구 가능하나, 복구해서는 안 된다. HF 원격 삭제만이 비가역이라 **운영자 명시 승인 전 실행 금지**.
- **P1~P4** 는 순수 클라이언트 파생이라 HF fetch 도 데이터 계약도 건드리지 않는다. 컴포넌트 단위 revert.
- **P1 의 유일한 파괴적 변경**은 `evalCond` 3-state 화다. 기존 `?q=` 공유 URL 의 결과가 3 핀에서 이동한다. 이것은 버그 정정이므로 의도된 이동이며, 스냅샷 테스트로 이동 범위를 못박고 릴리즈 노트에 적는다.
- **P5** 는 `UniverseSpec` 에 optional 필드 1 개 추가라 기존 4 랭킹신호 경로 무변경.
- **P6 은 착수하지 않는다.** 베이크 승인 게이트.

## 평가 (개발자 / PM)

### 전문 개발자 평가

P1~P4 가 새 데이터를 한 바이트도 안 부른다는 점이 이 계획의 강도다. `allNodes` 는 이미 메모리에 있고, `evalCond` 는 이미 종목마다 돌고 있다. 우리는 그 boolean 을 3-state 로 넓히고 중간 결과를 버리지 않을 뿐이다. 신규 컴포넌트는 `VerdictFunnel.svelte` 하나다.

`eval.ts` 추출은 겉보기보다 위험하다. `+page.svelte` 의 `evalCond` 와 `ScreenBuilder.svelte` 의 `evalCond` 는 이미 미세하게 다르고(문자열 비교 경로), 둘을 합치는 순간 저장된 `?q=` URL 의 결과가 움직인다. 골든 conformance 벡터를 먼저 쓰고 추출을 나중에 하는 순서를 지켜야 한다. 벡터 없이 추출하면 발산 버그를 SSOT 로 박제한다.

P6 를 잘라낸 것이 이 계획에서 가장 중요한 판단이다. 04 는 "완성된 백테스터에 소켓을 꽂는다" 고 썼지만, `ranking.ts:2` 가 이미 재무 랭킹을 금지해 두었고 그 이유(상폐사 재무 13.9%)는 데이터의 성질이지 배선의 문제가 아니다. PIT 재무 멤버십 패널을 구우려면 상장폐지 회사의 과거 재무가 필요한데 그게 13.9% 밖에 없다. 여기서 억지로 나아가면 생존편향을 백테스터 안으로 다시 들여온다.

### PM 평가

가장 급한 것은 기능이 아니라 P0 다. 네이버 파생 지표 3 개가 CC BY 4.0 데이터셋으로 매일 나가고 있고 기계 가드가 없다. 이건 우선순위 논쟁의 대상이 아니다. 그리고 아이러니하게도 `/scan` 그리드에서 가장 눈에 띄는 컬럼이 바로 그 `per`/`pbr` 다. 제품을 키우면 노출도 커진다.

기능 순서는 체감으로 정했다. 사용자가 가장 자주 겪는 좌절은 "조건을 넣었더니 0 건" 인데, 그 원인이 임계값인지 데이터가 없어서인지 지금은 알 방법이 없다. P1 의 커버리지 바 하나가 그 좌절을 없앤다. fetch 0 이고 코드도 가장 적다. 그다음이 깔때기, 그다음이 근접후보다. 근접후보는 체감이 가장 크지만 격자가 먼저 서야 한다.

경계할 것: P5 는 "백테스트" 가 아니다. 오늘 통과한 종목을 과거에 들고 있었다고 가정한 궤적일 뿐이고 생존편향과 look-ahead 를 둘 다 갖는다. 라벨로 경고하는 것으로는 부족하다는 것이 `universe/engine.ts` 가 이미 배운 교훈이라(`headlineSuppressed`), 같은 기전으로 hero 숫자를 아예 막는다. 정직하지 못한 숫자를 크게 보여주느니 안 보여준다.

성공 지표는 PRD 점수가 아니라 화면이다 (`[[feedback_plan_score_not_signature]]`). P1 이 끝나면 `/scan` 에서 아무 컬럼이나 눌렀을 때 "2,664 사 중 78 사에만 있음" 이 뜬다. 그게 뜨면 성공이고 안 뜨면 배관이다.

## Do-not-build

- P0 이전에 P1 착수. 위반 위에 제품을 쌓지 않는다.
- 골든 벡터 없이 `eval.ts` 추출. 발산 버그를 SSOT 로 박제한다.
- `universe-monthly.parquet` 에 재무 컬럼 신설 (베이크. 운영자 사전승인 없이 금지).
- near-miss 행을 히트맵 분위 계산에 포함.
- P5 결과에 hero 숫자·`spreadEndPct` 표기.
- 회색 편집성 각주로 커버리지 설명 (`[[feedback_no_editorial_microcopy]]`). 데이터값 `n/총` 만.
- 눈검수 전 push.
- `ecosystem.json` 완전 제거 시도 (레이아웃 x/y 는 SQL 불가).

## 진행 원장

- 2026-07-10: 8 영역 병렬 정찰(19 에이전트, 119 사실) + 3 렌즈 설계 + 3 심사 + 5 주장 적대검증. 04 의 순서 오류 + 사실 오류 2 건 정정. **P0 저작권 위반 확정** (5 단계 체인 직접 검증, 무인증 302). 심사 승자 = 퍼블릭 제품 설계자(170/300). 적대검증 생존 3 / 반증 2 (`ecosystem.json = scan 축 베이크` 반증, `valuation 은 발행금지 원천이 아니다` 반증). **P0 승인 대기.**
