# scan 스크리너 OS (승계 SSOT)

> **실행순서 정정됨 (2026-07-10)**: `05-public-surface-prd.md` 를 먼저 읽어라. 본 문서는 퍼블릭 `/scan` 을 P5 로 밀어 순서를 틀렸고, `ecosystem.json` 성격과 `universe/engine.ts` 재무 소켓에 대해 사실 오류가 있다. 판정격자 개념은 유효하며 05 가 그것을 브라우저에 적용한다. 본 문서의 P1~P4 는 05 의 골든 conformance 벡터 통과를 선결로 한다.
> 상태: 설계 완료, 승인 대기 (2026-07-10). 본 문서가 폴더의 새 SSOT 머리다.
> 승계: `00-prd.md` (컴포저블 쿼리 Phase 1~3 완료, Phase 4 미착수) 를 흡수한다. Phase 4 는 본 계획의 P5 다.
> 동반 근거: `02-coverage-audit.md` (필드 커버리지), `03-narrative-grid-invention.md` (서술표 격자).
> 트리거: 운영자 "scan 을 라이브러리적으로 완전히 흡수하는 개념 + 혁신적 스크리너로 세워라."

## 0. 한 줄 판정

**dartlab 의 scan 은 훌륭한 데이터 공급기지만 스크리너로는 서 있지 못한다.** 조건을 거를 수는 있으나, 누구를 대상으로 (universe) 언제 기준으로 (asOf) 왜 걸렸는지 (explain) 어떻게 줄세우는지 (rank) 를 계약이 갖고 있지 않다. 그리고 27 축이 계산해 놓은 지능 중 스크리닝에 노출된 것은 5 축뿐이다.

### 실측 그라운딩 (2026-07-10, 본 세션 직접 측정)

| 사실 | 측정값 | 측정 방법 |
|---|---|---|
| scan 축 수 | 27 (데이터축 22 + 메타 5: account/ratio/note/fields/screen) | `_AXIS_REGISTRY` |
| `universe` 인자를 받는 축 | **0 / 27** | 27 축 구현 함수 `inspect.signature` 전수 |
| screen 에 노출된 축 | **5 / 22** (audit, debt, dividendTrend, liquidity, quality) | `_COMPOSITE_AXIS_FIELDS` 11 필드 |
| 미노출 축 | 17 (capital, cashflow, disclosureRisk, earningsFlash, efficiency, governance, growth, insider, ipo, macroBeta, narrativeMetric, network, orders, profitability, salesByProduct, valuation, workforce) | 집합 차 |
| 필드 카탈로그 총량 | 4,928 (report 3,940 / finance 873 / krx 41 / note 30 / krxIndex 24 / **axis 11** / valuation 6 / docs 3) | `_catalog()` |
| 재무 원천의 공시일 보유 | `finance.parquet.rcept_no[:8]` = 공시일. 2020~2026, 13.1M 행 | `pl.scan_parquet` 집계 |
| 연간보고서 공시 지연 | 중앙값 **78 일** (평균 98.8, 표준편차 81.8) | 4분기 IS 931 건, `filedAt - 기말` |
| 정정공시로 인한 판본 중복 | **0 %** (IS/BS/CF/CIS 8,686,240 그룹 전수) | `(종목,연도,보고서,제표,연결,계정)` 별 `rcept_no` 고유수 |
| PIT 유니버스 기반 | `gov/prices/universe-monthly.parquet` 443,422 행 · 11.91MB · 17 년 · `delistReason` · `retFwd1m/3m` 보유 | `ui/packages/surfaces/src/scan/universe/load.ts` |
| 프론트 스크리닝 중복 구현 | 약 2,800 LOC (`metrics.ts` 607 + `duckSql.ts` 1065 + `ScreenBuilder.svelte` 564 + `presets.ts` 178 + `universe/` ~390) | `wc -l` |

두 개의 측정이 설계를 결정한다.

1. **공시 지연 중앙값 78 일**. 오늘의 `scan("screen", ...)` 은 "지금 알 수 있는 사실"로 오늘을 판정한다. 이것을 과거 어느 날짜에 대해 재현할 방법이 없다. 그래서 스크린은 검증될 수 없고, 검증되지 않는 스크린은 의견이지 도구가 아니다. `filedAt <= asOf` 한 줄이면 look-ahead 가 0 이 된다. 정정 판본 중복이 0 % 라 이 규칙에 예외 처리가 필요 없다.
2. **`universe` 인자 27/27 부재**. `engines.scan` SKILL.md 는 `dartlab.scan(axis, universe={"industryHint": "반도체"})` 를 계약으로 문서화하지만 실제로 호출하면 `TypeError` 다. 문서가 없는 기능을 약속하고 있다. (SKILL.md 도 22 축과 27 축을 혼용한다.)

## 1. 개념: 스크리너는 필터의 곱이 아니라 판정격자다

지금 `executeScreenSpec` 은 조건마다 프레임을 만들고 `_innerJoinOnStock` 으로 곱한다. 이 한 줄이 스크리너의 모든 능력을 미리 잘라낸다.

```python
# fields.py:623 현재
result = frames[0]
for frame in frames[1:]:
    result = result.join(frame, on="stockCode", how="inner")
```

inner join 은 세 정보를 동시에 파괴한다.

- **탈락 사유**. 조건을 통과 못한 종목과 데이터가 없는 종목이 똑같이 사라진다. `missing > wrong` 이 repo 원칙인데 여기서는 missing 이 곧 fail 로 위조된다. `interest_expenses` 커버리지가 78 종목이던 사건 (00-prd 진행원장) 이 정확히 이 함정이었다.
- **근접 후보**. 조건 5 개 중 4 개를 통과한 종목은 스크리너의 가장 값진 산출물인데, 곱하는 순간 존재하지 않았던 것이 된다.
- **깔때기**. 2,661 종목이 어느 조건에서 몇 마리 죽었는지. 사용자는 이걸 봐야 조건을 조율한다.

### 흡수 개념: VerdictGrid

**조건 x 종목 = 판정 격자를 1급 시민으로 만든다. 통과 종목 목록은 그 격자의 요약 하나일 뿐이다.**

```
              cond0   cond1   cond2   cond3
005930/삼성    PASS    PASS    PASS    PASS      -> members
000660/하이닉스 PASS    PASS    FAIL    PASS      -> nearMiss(1)
068270/셀트리온 PASS   MISSING  PASS    PASS      -> 판정불능(데이터 gap), fail 아님
```

격자 하나에서 스크리너의 모든 능력이 파생된다. 새 엔진을 붙이는 것이 아니라, 이미 하고 있는 계산의 중간 산물을 버리지 않는 것이다.

| 파생 | 격자에서 얻는 법 |
|---|---|
| `members` | 전 조건 PASS 인 행 (현행 동작과 동일. 회귀 0) |
| `nearMiss(k)` | FAIL 이 정확히 k 개, MISSING 0 인 행 |
| `funnel` | 조건별 (통과수, 탈락수, 판정불능수) 누적 |
| `coverage` | 조건별 MISSING 비율. 유니버스를 죽이는 희소 필드를 즉시 지목 |
| `sensitivity` | 임계값을 흔들며 격자 재판정. "40 종목이 되게 하려면 ICR 을 2.0 -> 1.6" |
| `rank` | PASS 행에 가중 스코어. 격자와 직교 |
| `walk` | asOf 를 시간축으로 이동하며 격자 재생성 |

이것이 "scan 기능을 완전히 흡수하는 개념"이다. 축도, 필터도, 랭킹도, 백테스트도 전부 하나의 원시개념 위 파생이라, 새 능력을 붙일 때마다 표면이 늘지 않는다.

### 흡수 개념 2: 축은 screen 의 형제가 아니라 필드 공급자다

`screen` 은 `_AXIS_REGISTRY` 안에 다른 축과 나란히 앉아 있다. 구조가 거꾸로다. `screen` 은 축이 아니라 **축을 소비하는 엔진**이어야 한다.

- 지금: 22 데이터축 중 5 축의 11 컬럼만 사람이 손으로 골라 `axis.*` 로 등재.
- 개념: **모든 축의 모든 출력 컬럼이 자동으로 `axis.{axis}.{column}` 필드가 된다. 손 선별 0.**

`growth` 의 6 종 성장패턴, `cashflow` 의 8 종 현금흐름패턴, `efficiency` 의 CCC, `governance` 의 등급, `orders` 의 book-to-bill, `salesByProduct` 의 HHI, `macroBeta` 의 gdpBeta. 전부 이미 계산되어 있는데 스크리닝에서 부를 수 없다. 이건 `[[feedback_exhaustive_no_curation]]` 위반이다. 등재 게이트로 도태시키지 말고 전수 등재 후 census 성적표로 도태시킨다.

공개 호출 계약은 바뀌지 않는다. `dartlab.scan("screen", spec={...})` 그대로다. spec 이 깊어질 뿐이다. (`operation.apiContract` 공개진입점정책 준수. 새 엔진, 새 축, 새 facade 신설 0.)

## 2. 결여된 네 개의 1급 개념

### 2.1 universe (누구를)

```json
"universe": {"market": "KOSPI", "industry": ["반도체"], "minMarketCap": 1e11, "minTurnover": 1e8, "exclude": ["관리종목"]}
```

주의: `dartlab.listing()` 은 **오늘 상장된 2,661 사**다. 이걸 유니버스로 쓰면 생존편향이 구조적으로 박힌다 (상장폐지된 회사가 애초에 없다). 과거 시점 유니버스의 정본은 `universe-monthly.parquet` 이며 `delistReason` 을 갖고 있다. `asOf` 가 없으면 listing, 있으면 universe-monthly 를 쓴다. 이 분기를 `explain.universeSource` 로 항상 노출한다.

### 2.2 asOf (언제 기준으로)

```json
"asOf": "2023-06-30"
```

규칙은 한 줄이다. **`rcept_no[:8] <= asOf` 인 공시만 본다.** 기말이 아니라 공시일 기준이라 결산월이 12 월이 아닌 회사도 자동으로 옳다 (실측에서 lag 이 음수로 나온 1 건이 바로 그 케이스였다). 정정 판본 중복 0 % 라 "그 시점에 보이던 판본" 선택 규칙이 필요 없다.

정직한 명명: 이것은 **가용성 시점정합 (availability PIT)** 이지 **판본 보존 시점정합 (vintage PIT)** 이 아니다. DART 가 원본을 덮어썼다면 우리는 그 사실을 모른다. 문서와 `explain` 에 그대로 적는다.

**경계 (조용한 오답 차단)**: `axis.*` 복합축 스캐너는 asOf 를 모른다. 최신 데이터로 계산한다. 그래서 `asOf` 와 `axis.*` 를 함께 쓰면 **ValueError** 다. 조용히 최신값을 섞지 않는다. P3 에서 스캐너에 asOf 를 관통시킨 축부터 해금한다.

### 2.3 rank (어떻게 줄세워)

`sort` 는 단일 필드 정렬이다. 스크리너는 다팩터 합성 점수가 필요하다. `define` 의 `zscore`/`percentile` + 스칼라 곱으로 절반은 이미 표현 가능하니, 1 급화는 **출력 계약**이다.

```json
"rank": {"score": "@compositeZ", "buckets": 5, "tieBreak": "krx.marketCap", "missing": "exclude"}
```
출력에 `rank`, `score`, `bucket` 컬럼을 낸다. `missing` 정책 (`exclude` / `worst` / `neutral`) 을 명시 강제한다. 결측을 조용히 0 이나 최하위로 채우는 것이 스크리너 최대의 거짓말이다.

### 2.4 explain (왜)

```json
"explain": true
```
`members` 옆에 `funnel`, `coverage`, `nearMiss`, `universeSource`, `asOfResolved`, `formula`, `datasetAsOf` 를 함께 반환한다. `engines.scan` SKILL.md 의 `requiredEvidence` (universe, datasetAsOf, filter, formula, table, executionRef) 는 지금 엔진이 **하나도 반환하지 않는다**. 모든 소비자가 각자 재구성한다. 엔진이 증거를 내면 그 재구성이 사라진다.

## 3. 스크린은 리스트가 아니라 가설이다 (혁신의 착지점)

`asOf` 가 생기는 순간 스크린은 시간축을 걷는다.

```python
dartlab.scan("screen", spec={..., "walk": {"from": "201001", "to": "202512", "rebalance": "Q"}})
```

매 리밸 시점에 spec 을 재평가해 멤버를 뽑고, `universe-monthly.parquet` 의 `retFwd1m/retFwd3m` 로 전진수익을 회계한다. **새로 구울 것이 없다.** 필요한 것이 전부 이미 있다.

- 전진수익 + 상장폐지 사유: `universe-monthly.parquet` (기승인 산출물)
- look-ahead 차단: `decisionYm < fillYm` 불변 (`universe/engine.ts` 에 이미 구현)
- 폐지 처리 이중실행 밴드 (낙관 0 손실 / 보수 -100 %): `universe/engine.ts` 에 이미 구현
- 유동성 컷 PIT: `universe/ranking.ts` 에 이미 구현

지금 그 엔진의 랭킹 신호는 가격 4 종 (`mom12_1`, `lowVol`, `high52w`, `liquidity`) 뿐이다. 05-universe-backtest 스펙이 스스로 적어 놓았다. "quant/alphas (local 재무, P1 미사용)". 즉 **재무 스크린을 꽂을 소켓이 비어 있는 채로 완성된 백테스터**다. 우리는 소켓을 채운다.

### 기존 `runScanBacktest` 는 폐기 대상이다

`quant/screen/scanBacktest.py:128` 은 **오늘의** scan 결과 상위 N 종목을 받아 과거 가격에 전략을 돌린다. 오늘 통과했다는 사실이 과거 매수 시점에 알려질 리 없고 (look-ahead), 오늘 상장되어 있다는 사실 자체가 생존 조건이다 (survivorship). Sharpe 2.45 같은 수치가 나오는 이유다. 삭제하지 말고 `walk` 로 재정의하되, docstring 과 SKILL 에 편향을 명시하고 신규 사용을 막는다.

## 4. 단계 (P1~P5)

전 단계 **신규 bake 0**. 런타임이 SSOT 에서 직독한다 (`CLAUDE.md` 런타임-SSOT 강행규칙).

| 단계 | 내용 | 산출 | 위험 |
|---|---|---|---|
| **P1** | VerdictGrid 내부화. `_innerJoinOnStock` -> `_buildVerdictGrid` + `members` 요약. `explain` / `funnel` / `coverage` / `nearMiss` 반환. 기존 반환 형태 무변경 (explain=false 기본) | 회귀 0, 근접후보/깔때기 즉시 획득 | 낮음. 순수 additive |
| **P2** | 축 전수 등재. `_AxisEntry.outputs` 선언 + `axis.*` 자동 카탈로그 생성 + 드리프트 가드. 5 축 -> 22 축 | 손 선별 0 | 중. 다축 spec 의 메모리 |
| **P3** | `asOf` + `universe`. `scanAccount`/`scanRatio` 투영에 `rcept_no` 추가, `filedAt <= asOf` 필터. universe 해석기 (listing / universe-monthly 분기) | 시점정합 스크리닝 | 중. axis 축과의 경계는 ValueError |
| **P4** | `rank` 1 급화 + `walk` (스크린 백테스트). `universe-monthly` 전진수익 회계 | 스크린이 검증 가능해짐 | 중. 결측 정책 강제 |
| **P5** | 프론트 붕괴 (구 Phase 4). `screens/*.json` 과 spec 을 프론트가 직접 소비. TS 2,800 LOC 중복 제거 | 4 중 구현 -> 1 SSOT | 시각 회귀. 눈검수 필수, 자동 push 금지 |

## 5. 데이터 계약 (spec 최종형)

```json
{
  "universe": {"market": "KOSPI", "minMarketCap": 1e11},
  "asOf":     "2023-06-30",
  "define":   {"icr": {"op": "div", "left": "finance.account.operating_profit",
                       "right": "finance.account.interest_expenses"},
               "zRoe": {"op": "zscore", "field": "finance.ratio.roe", "by": "industry"}},
  "where":    [{"field": "@icr", "op": ">", "value": 2},
               {"field": "finance.ratio.debtRatio", "op": "<", "value": 80}],
  "rank":     {"score": "@zRoe", "buckets": 5, "missing": "exclude"},
  "explain":  true,
  "limit":    40
}
```

키 6 개가 늘었고 (`universe`, `asOf`, `rank`, `explain`, `nearMiss`, `walk`), 전부 optional 이다. 하나도 안 주면 오늘 동작과 바이트 동일하다. `define`/`where`/`any`/`select`/`sort`/`limit` 문법은 불변이다.

## 영향 파일

- `src/dartlab/scan/builders/kr/report/fields.py` (1,221 LOC). `_innerJoinOnStock` 을 `_buildVerdictGrid` 로 대체. `executeScreenSpec` 이 grid 를 만들고 요약을 낸다. `_loadFieldValues` 가 `asOf` 를 전파.
- `src/dartlab/scan/builders/kr/report/fieldCatalog.py`. `_compositeAxisCatalogRows` 를 `_AXIS_REGISTRY.outputs` 에서 자동 생성으로 교체. 하드코딩 `_COMPOSITE_AXIS_FIELDS` 11 개 제거.
- `src/dartlab/scan/router.py` (526 LOC). `_AxisEntry` 에 `outputs: tuple[AxisField, ...]` 필드 추가.
- `src/dartlab/scan/screen/__init__.py` (530 LOC). `scanScreen` 이 `explain` 반환형 (DataFrame 또는 ScreenResult) 분기.
- `src/dartlab/providers/dart/finance/scanAccount.py`. `_SCAN_ACCOUNT_BASE_COLS` 에 `rcept_no` 추가 (현재 투영에서 탈락). `_scanAccountFromMerged` 에 `asOf` 필터.
- `src/dartlab/scan/universe.py` (신규, L1.5). universe 해석기. `listing()` 과 `universe-monthly.parquet` 분기.
- `src/dartlab/scan/walk.py` (신규, L1.5). 시간축 spec 재평가 + 전진수익 회계.
- `src/dartlab/quant/screen/scanBacktest.py`. docstring 에 편향 명시, `walk` 로 라우팅.
- `src/dartlab/skills/specs/engines/scan/SKILL.md`. universe 허위 계약 정정, 22/27 축 표기 통일, spec 6 키 문서화.
- `ui/packages/surfaces/src/scan/{metrics,presets,duckSql}.ts`, `ScreenBuilder.svelte`, `universe/engine.ts` (P5 에서 spec 소비로 전환).
- `tests/scan/test_screen_verdict.py`, `tests/scan/test_screen_asof.py`, `tests/scan/test_axis_outputs_drift.py`, `tests/audit/scanOutputCensus.py` (축 출력 census 확장).

## 영향 함수/심볼

| 심볼 | 파일 | 변경 |
|---|---|---|
| `_innerJoinOnStock` | `scan/builders/kr/report/fields.py:623` | 제거. `_buildVerdictGrid` 로 대체 |
| `executeScreenSpec` | 같은 파일 `:119` | grid 기반 재작성. explain 분기 |
| `_loadFieldValues` | 같은 파일 `:348` | `asOf` 전파 |
| `_conditionFrame` | 같은 파일 `:287` | 프레임 대신 (pass, missing) 판정열 반환 |
| `_loadCompositeAxis` | 같은 파일 `:1191` | `asOf` 동반 시 ValueError |
| `_COMPOSITE_AXIS_FIELDS` | `report/fieldCatalog.py:17` | 제거. registry 도출 |
| `_catalog` | 같은 파일 `:148` | `_axisCatalogRows` 자동 생성 소비 |
| `_AxisEntry` | `scan/router.py:22` | `outputs` 필드 추가 |
| `_SCAN_ACCOUNT_BASE_COLS` | `providers/dart/finance/scanAccount.py:31` | `rcept_no` 추가 |
| `_scanAccountFromMerged` | 같은 파일 `:145` | `asOf` 필터 |
| `scanScreen` | `scan/screen/__init__.py:399` | explain 반환형 분기 |
| `runScanBacktest` | `quant/screen/scanBacktest.py:128` | 편향 명시 + walk 라우팅 |
| `resolveUniverse` (신규) | `scan/universe.py` | universe dict -> 종목 집합 + 출처 |
| `walkScreen` (신규) | `scan/walk.py` | spec + 윈도 -> 리밸 스냅샷 + NAV |

4 계층 검증: `scan/universe.py` 와 `scan/walk.py` 는 L1.5. L1 (`gather.bulkData.hfBulk`, `providers.dart.finance`) 만 import 한다. L2 (`quant`) 를 부르지 않는다. 역방향은 `quant.screen.scanBacktest` 가 `scan.walk` 를 부르는 형태 (L2 -> L1.5, 합법). L1.5 형제 (frame/synth/reference) cross import 0.

## 테스트

- `tests/scan/test_screen_verdict.py` (신규). ① `members` 가 기존 inner join 결과와 **완전 일치** (회귀 0 의 기계 증명) ② PASS/FAIL/MISSING 3 상태 분리 ③ `nearMiss(1)` 이 FAIL 1 개 + MISSING 0 만 포함 ④ funnel 누적합이 유니버스 크기와 정합 ⑤ 결측 종목이 fail 로 계상되지 않음.
- `tests/scan/test_screen_asof.py` (신규, `requires_data`). ① `asOf="2024-01-01"` 결과에 `filedAt > 20240101` 행이 0 건 ② 같은 spec 을 asOf 없이 / 최신 asOf 로 부르면 동일 ③ `asOf` + `axis.*` -> ValueError ④ 결산월 비 12 월 회사가 lag 음수로 누락되지 않음.
- `tests/scan/test_axis_outputs_drift.py` (신규, `requires_data`). registry `outputs` 선언과 실제 스캐너 컬럼 일치. Phase 2b 의 드리프트 가드 패턴 재사용. 축을 하나씩 로드/해제해 OOM 안전 (`CLAUDE.md` Polars 힙 가드).
- `tests/scan/test_screen_walk.py` (신규). ① `decisionYm < fillYm` 불변 ② 폐지 종목이 유니버스에서 사라지지 않음 (생존편향 0) ③ 낙관/보수 밴드가 `universe/engine.ts` 결과와 수치 일치 (교차 구현 대조).
- `tests/audit/scanOutputCensus.py` (확장). 축별 출력 컬럼 census. 등재 후 DARK/THIN 도태 판정.
- 기존 회귀: `tests/scan/test_screen_define.py` 32 케이스, `tests/scan/test_axes.py`, `test_axes_full.py` 전부 무변경 통과.
- 게이트: `uv run python -X utf8 tests/run.py preflight` (27 게이트) + `dartlabGuard --scope l0-l15` (구조미러 + 4 계층) + `publicApiCoverage` (scan 축 수 불변) + `productSmoke --suite quick`.
- 메모리: 단일 파일 실행은 `bash tests/test-lock.sh tests/scan/<path> -m "requires_data" -v`. fixture scope `module`.

## 롤백 / 리스크

**롤백**: P1~P4 는 전부 spec 키 optional 이라 순수 additive 다. 각 단계는 독립 커밋이며 `git revert` 로 되돌아간다. 유일한 파괴적 변경은 P2 의 `_COMPOSITE_AXIS_FIELDS` 제거인데, 자동 생성이 같은 11 필드를 포함하는지 계약 테스트로 먼저 못박고 지운다. P5 는 프론트라 커밋만 하고 운영자 눈검수 전 push 금지 (`CLAUDE.md` 프론트 자동 push 예외).

**리스크와 처방**

| 리스크 | 실체 | 처방 |
|---|---|---|
| **OOM** (최대 위험) | 축 22 개 전수 등재 시 한 spec 이 여러 스캐너를 물면 Polars Rust 힙이 축당 수백 MB 로 쌓인다. 회수되지 않는다 | `_axisCache` 유지 + `maxAxisLoads` (기본 3) 초과 시 ValueError 로 조기 차단. `explain.materializedAxes` 로 무엇을 로드했는지 항상 노출 |
| asOf x axis 혼용 | 스캐너가 최신값을 계산해 조용히 섞임 | ValueError. 우회 없음. P3 에서 축별로 해금 |
| verdict grid 메모리 | 조건수 x 2,661 종목 boolean. 조건 20 개면 53k 셀 | 무시 가능. 격자는 boolean 2 열 (pass, missing) |
| universe-monthly 의존 | 프론트 HF 자산을 python 이 읽음 | 이미 `hfBulk` 경로 존재. `gov/prices/` 는 KRX 공식 OpenAPI 벌크라 발행 가능 (`[[feedback_copyright_no_prebuild_local_only]]`) |
| valuation 축 저작권 | `scanValuation` 은 네이버 실시간가 경유 | 스크리너 공개 표면은 `krx.*` (KRX 벌크) 우선. 네이버 계열은 로컬 런타임 축으로 유지 |
| P5 시각 회귀 | 프론트 2,800 LOC 교체 | 스크린샷 전수 눈검수 (`[[feedback_ui_rules]]`). 완결 단위만 push |

## 평가 (개발자 / PM)

### 전문 개발자 평가

핵심 변경이 `_innerJoinOnStock` 한 함수의 교체라는 점이 이 설계의 강도다. 조건 평가는 이미 종목별로 일어나고 있고, 우리는 그 중간 판정을 버리지 않고 격자에 적는 것뿐이다. 계산량은 늘지 않는다 (join 이 filter 로 바뀌고 boolean 2 열이 늘 뿐). 문자열 eval 이 없는 폐쇄 vocabulary 도, 단위 전파도, 위상정렬도 전부 그대로 산다.

`asOf` 는 더 얌전하다. `rcept_no` 는 이미 parquet 에 있고 (`_SCAN_ACCOUNT_BASE_COLS` 투영에서만 빠져 있다) 필터는 push-down 된다. 정정 판본 중복이 실측 0 % 라 "어느 판본을 볼까" 라는 어려운 문제 자체가 존재하지 않는다. 새 파케이를 굽지 않으므로 런타임-SSOT 강행규칙과 충돌하지 않는다.

가장 무서운 것은 OOM 이지 로직이 아니다. 축 22 개를 필드로 열면 사용자는 당연히 여러 축을 한 spec 에 섞는다. `maxAxisLoads` 가드가 없으면 이 설계는 첫날 죽는다. 그래서 가드를 P2 와 같은 커밋에 넣는다.

미해결로 남기는 것: `walk` 의 정확도는 `universe-monthly.parquet` 의 월말 격자에 묶인다. 일간 리밸런싱은 불가능하다. 이건 한계로 문서화하고 억지로 넘지 않는다.

### PM 평가

지금 dartlab 의 스크리너는 "조건에 맞는 40 종목"을 준다. 사용자가 실제로 원하는 것은 그게 아니다. **왜 이 40 개인지, 41 번째는 무엇을 놓쳤는지, 이 조건이 과거에 돈이 됐는지**를 원한다. 세 질문 다 지금 답할 수 없고, 셋 다 판정격자 하나에서 나온다.

경쟁 스크리너 (증권사 HTS, 각종 웹 스크리너) 와의 차이는 필드 개수가 아니다. 4,928 필드는 이미 충분하다 못해 과하다. 차이는 두 가지다. ① **시점정합**. 대부분의 무료 스크리너는 오늘 데이터로 과거를 판정한다. 우리는 공시일을 갖고 있어서 안 그럴 수 있다. ② **정직한 결측**. 조건을 못 넘은 종목과 데이터가 없는 종목을 구별해서 보여주는 스크리너를 나는 본 적이 없다.

ROI 관점의 순서도 분명하다. P1 은 코드 한 함수 교체로 근접후보와 깔때기를 얻는다. 가장 싸고 사용자 체감이 가장 크다. P5 는 가장 비싸고 (프론트 2,800 LOC) 가장 늦어야 한다. 백엔드가 옳아지기 전에 프론트를 갈아엎으면 두 번 갈아엎는다.

경계할 것: 이 계획의 성공 지표는 PRD 점수가 아니라 **`walk` 가 실제 스크린 하나에 대해 분위 스프레드를 뱉는가**다 (`[[feedback_plan_score_not_signature]]`). P4 가 실측을 못 내면 P1~P3 은 잘 만든 배관일 뿐이다. flagship 은 `financialStabilityDrawdown.json` 으로 고정하고, "하락장 재무안전 종목이 정말 하락장에서 덜 빠졌는가" 를 숫자로 답하는 것을 졸업 조건으로 삼는다.

## Do-not-build (덕지덕지 차단)

- 새 엔진 / 새 축 / 새 facade. 계약은 `dartlab.scan("screen", spec)` 하나다.
- raw SQL 을 계약으로 노출 (00-prd F3 판정 유지. 동의어/CFS-OFS/Q4 standalone 의미론이 Python resolver 에 산다).
- `walk` 를 위한 신규 bake. `universe-monthly.parquet` 로 충분하다. 부족함이 실측되면 그때 운영자 승인 후 논의한다.
- 결측을 0 또는 최하위로 자동 대체하는 어떤 경로도 금지. `rank.missing` 명시 강제.
- `asOf` 와 `axis.*` 의 조용한 혼용. 최신값 fallback 금지, ValueError.
- 문자열 eval, 자동 spec 생성기, LLM 이 만든 spec 의 무검증 실행.
- 프론트 선배선. 백엔드 계약이 실측으로 굳기 전 TS 를 손대지 않는다.

## 진행 원장

- 2026-07-10: `scan-composable-query` -> `scan-screener-os` 승계. 27 축 universe 인자 0/27, axis 노출 5/22, 공시지연 중앙값 78 일, 정정 판본 중복 0 % 실측. 판정격자 개념 확립. 설계 완료, **운영자 승인 대기** (P1 착수 전).
