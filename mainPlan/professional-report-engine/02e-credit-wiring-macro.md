# 02-E · 신용 라이브 배선 + 거시 민감도 강화 (전문가 스펙)

> 운영자 지시: **정직한 스킵 = 무능.** credit 엔진은 이미 강하다(79사 검증) — 라이브 미배선이
> 최고 ROI 의 격상이다. macro 민감도는 얕다(n≈3-5) — 스킵 말고 강화한다. 금지 = 날조.
> SSOT 개선만, 병렬 빌드 금지. 본 스펙은 코드 직독 증거(file:line) 기반, 재조사 없이 구현 가능한 깊이.

---

## 요약 (결론 먼저)

- **Part 1 (credit)**: dCR 20등급 + 7축 + forward PD 는 **Company 객체(BS/IS/CF + sectorThresholds
  + CHS + Notch)가 필수**라 브라우저 lean parquet 으로 재계산 불가. **TS 재구현(옵션 b)도 골든패리티
  유지 비용이 과대**. → **권장: 옵션 (a) — 프리빌드가 이미 회사별 `macroExposure` 를 publish 하는
  것과 동일 패턴으로 `credit` 패킷(grade·7축·PD·outlook)을 `finance.json` 에 publish**. 이건
  굽기(bake)가 아니라 **런타임 SSOT(credit 엔진)의 산출물을 prebuild offline 단계가 직렬화**하는
  것 — 이미 승인된 패턴(`macroExposure`)의 동형 확장이라 신규 배선·신규 SSOT 0.
- **forward PD** 는 전역 cohort 한 장(`transition.json`, KR 평균)이라 **등급→PD 룩업 20행 테이블 1회
  ship** 으로 끝(회사별 아님).
- **Part 2 (macro)**: 연간 n≈3-5 → **분기 history(관측수 4배) + 다변량(금리·환율·산업) + 회사 history
  부족 시 섹터 macro beta 로 위계 폴백**. 게이트 = nObs≥8·adjR²≥0.20·OOS 안정성. 게이트 실패시
  스킵 아니라 **섹터 단위 민감도로 폴백**.

---

# PART 1 — CREDIT 라이브 배선 (최고 ROI)

## 1.1 credit 엔진 SSOT 지도 (file:line)

| 구성요소 | 위치 | 핵심 |
|---|---|---|
| **단일 진입점** | `src/dartlab/credit/__init__.py:272 credit(axis, target)` · `:417 creditCompany(company, ...)` | gather 표준 axis-first. 79사 검증 docstring(`:283-284`, `:337-338`) |
| **메인 파이프라인** | `src/dartlab/credit/engine.py:193 evaluateCompany(company, *, detail, basePeriod)` | 3-Track 분기(A 일반 7축 / B 금융 5축 / C 지주) → 가중평균 → CHS PD → Notch 7룰 → 20등급 |
| **7축 산출** | `engine.py:345-434` (axis1 채무상환 … axis7 공시리스크) + `scoring/metrics.py calcAllMetrics` | 각 축 `{name, score, weight, contribution, metrics[]}` |
| **20등급 + PD 매핑** | `src/dartlab/synth/creditGradeTable.py:16 _GRADE_20_TABLE` · `:45 mapTo20Grade(score)` · `:57 estimatePD(grade)` | AAA(PD 0.00%)~D(100%). KIS 1998-2025 실측. 도메인-중립 SSOT |
| **forward PD ladder** | `src/dartlab/credit/scoring/migration.py:174 forwardPdLadder(counts=None, *, horizons=(1,3,5))` | CreditMetrics Cohort. M^h[grade,D] = h년 누적 PD. `:29 _DEFAULT_RATING_ORDER` 20등급 |
| **전이 행렬(전역)** | `migration.py:232 _loadTransition()` → `monitoring/history.py:_TRANSITION_PATH = data/credit/transition.json` | **단일 전역 cohort**(stockCode 단위 아님 — `history.py:77` "전체 KR 평균만"). 회사별 등급 history = `data/credit/history/{code}.json`(`history.py:91`) |
| **badge 헬퍼(이미 존재)** | `src/dartlab/ai/tools/creditBadge.py:20 getDcrBadge(company)` | `evaluateCompany(detail=False)` 호출 → `{grade, gradeRaw, score, healthScore, pdEstimate, outlook, investmentGrade, axes[], confidence}` dict. **Ask 모드 Company.panel 에 자동 부착(Track G)** — UI 배선만 부재 |
| **confidence** | `creditBadge.py:70 baseScore("ratio")` → 80 | method="ratio" deterministic |

**핵심**: `getDcrBadge` 가 이미 보고서가 필요로 하는 정확한 패킷을 만든다. 신규 함수 0 — **배선만**.

## 1.2 현재 라이브 /report 의 격차 (file:line)

- 라이브 /report 는 **브라우저 재무비율 4축 점검표**만 보여준다:
  `landing/src/lib/report/build.ts:426 healthTable(axes[])` — 부채비율/유동비율/이자보상배율/FCF 4축을
  *나란히* 측정만. `:455` 라벨 명시 *"Python 신용등급 아님"*, `:643` 본문 *"dartlab 정밀
  신용등급(Python 7축 dCR)이 아니라 브라우저 재무비율 점검표"*.
- 즉 **진짜 dCR(20등급·7축 워터폴·forward PD)은 Python 에 살아있고 화면엔 0**. `build.ts:1443`
  에 `credit: '신용평가'` 엔진 라벨은 등록돼 있으나 **credit sourceEngine 섹션을 만드는 코드가 없다**
  (`build.ts` 전체에서 credit 섹션 빌더 부재 — buildEarningsPower·buildLiquidity·buildCapitalReturn·
  buildMarket·buildOwnership 5개만 존재).

## 1.3 배선 문제 — 런타임-SSOT 존중 (옵션 평가)

랜딩은 정적(`ssr=false`, 브라우저가 parquet 직독, 베이크 금지, Python 실행 불가). dCR 이 어떻게
*굽지 않고* 라이브에 도달하는가?

### 데이터 경로 실측 (Explore 추적 + 코드 증거)

1. **report 본문 재무**: `build.ts:1341 rt.finance.bundle(code)` → `ui/packages/runtime/.../sources/
   financeSource.ts loadTerminalFinance` → `core.requestParquetRows({origin:'hfRange', path:'dart/
   finance/{code}.parquet'})`. **parquet 직독**(HF range fetch). finance.json 안 씀.
2. **`finance.json` 소비처**: `.github/scripts/prebuild/buildFinanceJson.py:324` 가 회사별
   `data["macroExposure"] = calcMacroExposureFromAnnualRevenue(...)` 를 **이미 임베드**(`:17` 스키마
   주석). 소비처는 /scan 대시보드 — **/report 는 finance.json 미소비**(Explore §2).
3. **transition.json**: `.gitignore /data/` 로 미커밋. `history.py:116 _updateTransition` 가 등급 변동시
   증분 누적, `updateTransitionMatrix()` 운영자 cron 일괄. **전역 한 장**.

### 옵션 평가

| 옵션 | 내용 | 판정 |
|---|---|---|
| **(a) prebuild publish** | credit 엔진 산출물(grade·7축·PD·outlook)을 `getDcrBadge` 로 회사별 계산 → **`finance.json` 에 `credit` 키 추가**(macroExposure 와 동일 위치). 브라우저는 읽기만 | ✅ **권장**. `macroExposure` 가 이미 같은 패턴으로 승인됨. credit 엔진이 SSOT, prebuild offline 이 직렬화 — **굽기 아님**(런타임 SSOT 의 산출물 publish). 79사 검증 100% 보존(엔진 0 변경) |
| (b) TS 재구현 | dCR 7축·CHS·Notch·sectorThresholds 를 클라이언트 TS 로 포팅, 골든패리티 | ❌ macro-engine 선례는 **해석적 BVAR 2×2**(닫힌형). dCR 은 sectorThresholds 룩업 + 3-Track 분기 + CHS 시장보정 + Notch 7룰 + 시계열 smoothing — **수백 줄 + 영구 패리티 부채**. ROI 음수 |
| (c) 로컬 /api | 로컬서버가 Python credit 계산 | ❌ 퍼블릭 바닥 무중단 위반(`:8400` 없이 떠야 정상). 공개 /report 가 로컬 의존 불가 |

### 왜 (a)가 굽기가 아닌가 — 런타임-SSOT 정합

- **굽기 금지의 본질** = "런타임이 SSOT 에서 직독 가능한데 성능·편의로 사본/별도산출물을 신설"하는 것.
- credit dCR 은 **브라우저 런타임으로 직독 불가**(Company 객체·BS/IS/CF·sectorThresholds·CHS 종가
  cache 가 클라이언트에 없음 — lean parquet 행만 있음). 이건 *실측 런타임 불가*다.
- 그리고 **이미 동형 산출물(`macroExposure`)이 같은 prebuild 가 같은 finance.json 에 publish 중**.
  credit 추가는 **신규 산출물 신설이 아니라 기존 publish 패킷의 필드 확장** — 새 SSOT·새 배선 0.
- 따라서 운영자 directive(병렬 빌드 금지·SSOT 개선만)와 정합. `feedback_runtime_ssot_no_build_without_
  approval` 의 "런타임 정말 불가능"을 **실측으로 충족**(객체 부재).

## 1.4 클라이언트에 있어야 할 데이터 + 출처

`finance.json.companies[code].credit` 에 publish 할 패킷 (`getDcrBadge` 출력 + forward PD):

```jsonc
"credit": {
  "grade": "dCR-AA+", "gradeRaw": "AA+", "gradeCategory": "최우량",
  "score": 7.2, "healthScore": 92.8,          // 0=최우량
  "pdEstimate": 0.01,                          // 단년 PD (estimatePD)
  "outlook": "안정적", "investmentGrade": true,
  "axes": [ {"name":"채무상환능력","weight":25,"score":5.1,"contribution":1.3,
             "metrics":[{"name":"FFO/총차입금","value":...,"score":...}, ...]}, ... ],  // 7축 워터폴
  "captiveFinance": false, "holding": false, "sector": "...",
  "latestPeriod": "2025Q1",
  "notchAdjustment": {...|null}, "chsAdjustment": {...|null},  // 보정 투명성
  "methodologyVersion": "v4.0", "confidence": 80, "track": "A",
  "forwardPd": { "1y": 0.01, "3y": 0.05, "5y": 0.12 },        // forwardPdLadder[grade] 룩업
  "_note": "정기보고서 마감 후 30~45일 시차"
}
```

- **출처**: `grade`·`axes`·`pdEstimate`·`outlook` = `getDcrBadge(company)` 그대로
  (`creditBadge.py:61-72`). `gradeCategory` = `creditGradeTable.py:83`. `notch/chs/track` =
  `evaluateCompany` 반환(`engine.py:479-481`, detail 불요).
- **forwardPd**: `forwardPdLadder()` 전역 ladder DataFrame 에서 `grade` row 룩업 — **전역이라 회사
  루프 밖에서 1회 계산** 후 등급별 dict 로 회사에 join. (`transition.json` 부재시 degenerate→ladder
  생략, badge 의 단년 `pdEstimate` 만 유지 — 정직 폴백).

## 1.5 구체적 구현 단계

### Step 1 — prebuild 에 credit 임베드 (`buildFinanceJson.py`)

영향: `.github/scripts/prebuild/buildFinanceJson.py`
- 현재 `:321 data = _extract_annual(df, code)` 는 **lean(Company 미생성)**. credit 은 Company 가
  필요 → **OOM 가드 준수**해 회사를 *순차*로 생성(`CLAUDE.md` 병렬 agent≤2, Company 1개 200~500MB).
- `:316` import 옆에 `from dartlab.ai.tools.creditBadge import getDcrBadge` +
  `from dartlab.credit.scoring.migration import forwardPdLadder`.
- 루프 밖 1회: `pdLadder = forwardPdLadder()` → `{grade: {"1y":..,"3y":..,"5y":..}}` dict 화
  (transition.json 부재시 `None`).
- 루프 안(`:320-332`): 회사별로
  ```python
  from dartlab.company import Company
  try:
      c = Company(code)
      badge = getDcrBadge(c)        # None 이면 credit 키 생략(금융사 fallback 부족 등)
      if badge:
          if pdLadder: badge["forwardPd"] = pdLadder.get(badge["grade"])
          data["credit"] = badge
      del c                          # 명시 해제 — OOM 가드
  except Exception:
      pass                           # 정직 스킵 — credit 키 부재 = UI 가 dCR 섹션 생략
  ```
- **성능 주의**: 전 상장사 Company 생성은 무겁다. **2단계 처리** 권장 — finance.json 의 lean 추출은
  유지(빠름), credit 은 **별도 `creditExposure.json`**(또는 finance.json 의 별 키) 로 분리해
  *증분/배치* 가능하게. (macroExposure 가 lean 경로라 빠른 것과 대조 — credit 만 Company 필요).
  단일 파일 선호시 finance.json 에 합치되 빌드 시간 한도(`:25` 주석 ~5분 → credit 포함시 증가) 재측정.

### Step 2 — US 경로 정직 처리

`.github/scripts/prebuild/buildFinanceJsonUs.py:141 result["macroExposure"] = None` 옆에
`result["credit"] = None` 추가. **이유**: `engine.py:285-292` 시장 가드 — US(EDGAR) 는 KR(WICS)
calibration 미검증이라 `evaluateCompany` 가 None 반환. UI 는 `credit==null` 이면 dCR 섹션 생략(정직).

### Step 3 — 보고서에 credit 섹션 빌더 추가 (`build.ts`)

영향: `landing/src/lib/report/build.ts` + `model.ts`(타입) + `perspectives.ts`(관점 등록)
- **신규** `buildCreditAssessment(credit, ctx)` — `healthTable`(`:426`)과 **공존**(폐기 아님:
  healthTable 은 브라우저 4축 *점검*, dCR 은 *전문 신용평가*. 둘은 다른 질문). 섹션:
  - **S1 종합 등급 카드**: `dCR-AA+ · 투자적격 · outlook 안정적 · 단년 PD 0.01%`. notch/chs 보정
    있으면 *근거 노출*(`engine.py AIContext:263` "grade+outlook 만 인용 금지").
  - **S2 7축 워터폴**: `axes[]` → contribution 막대(채무상환 25%·자본구조 …). 각 축 metrics 표.
    MiniFinChart SSOT 재사용(손수 차트 금지 — `reference_financial_graph_ssot`).
  - **S3 forward PD 사다리**: `forwardPd {1y,3y,5y}` → 누적 PD 라인. "h년 누적 PD" 명시
    (`migration.py AIContext:230`). transition 부재시 단년 PD 만.
  - **honest-skip**: `credit==null`(금융사 fallback·데이터부족) → "정밀 dCR 산출 불가 —
    브라우저 4축 점검표 참조" 행(healthTable 로 graceful).
- credit 섹션의 `sourceEngine:'credit'` → 기존 provenance 집계(`build.ts:1448-1453`)가 자동으로
  "신용평가" 엔진을 strip 에 노출.
- **배치**: `liquidity`(재무안정성) 관점 끝에 dCR 블록 추가가 자연스럽다(부채감당과 인접). 또는
  `perspectives.ts` 에 신규 관점 `'credit'` 등록 후 `buildReport`(`:1381` if-체인)에 분기 추가.
  권장 = **liquidity 관점에 흡수**(신규 탭 남발 회피 — `feedback_always_check_clutter`).

### Step 4 — 데이터 페치 배선

- /report 가 finance.json(credit 포함)을 읽도록: `buildReport`(`:1340` Promise.all)에 finance.json
  로드 추가(`loadJson('dashboards/finance.json')` 또는 분리시 `creditExposure.json`). 회사 credit 만
  슬라이스. **단일 data-fetch SSOT**(`dataCore.requestParquetRows` / `loadJson`) 경유 — 직접 URL 금지
  (`checkUiDataWiring` 강제).

## 1.6 검증 / 졸업 게이트 (Part 1)

- **G1 패널-가용성(panel-availability)**: prebuild 후 finance.json 의 N개 무작위 회사 `credit` 키가
  `dartlab.credit.credit(code)` Python 직접 호출과 **byte-동일**(grade·score·axes). 같은 엔진
  호출이므로 항등 — 차이나면 직렬화 버그. 테스트: `tests/audit/` 에 `checkCreditPublishParity.py`
  (샘플 20사, finance.json[code].credit vs `credit(code)`).
- **G2 79사 검증 보존**: 엔진(`credit/**`) **0 변경**이 불변식. `tests/` credit 회귀(기존 79사
  검증셋)가 그대로 green — publish 는 호출부일 뿐. 회귀 가드: AST census 로 `credit/` diff 0 확인.
- **G3 honest-skip 렌더**: credit==null(금융사·미상장) 회사가 빈칸 아니라 healthTable 폴백으로
  graceful — Playwright 실측 스크린샷(`feedback_ui_rules` 푸시 전 눈검수).
- **G4 US 정직 None**: US 회사는 finance-us.json[code].credit==null, UI dCR 섹션 미렌더.

---

# PART 2 — 거시 민감도 강화

## 2.1 macro SSOT 지도 (file:line)

| 구성요소 | 위치 | 한계 |
|---|---|---|
| **회사 민감도 회귀** | `src/dartlab/analysis/financial/macroExposure.py:322 calcMacroSensitivity(company, *, basePeriod)` | **연 매출 YoY vs 연평균 macro 변화율 OLS**(`:17 MACRO_EXPOSURE_METHOD`). 업종최적 3 + 범용 3(금리/환율/IPI) 중 R² 높은 쪽 |
| **품질 게이트** | `macroExposure.py:97 _qualityFromSelected` | `:119 nObs<MIN_OBS(5)` 또는 `:121 rSquared<0.2` → `missingEvidence` → status `qualitativeOnly`. `:100-113` selected 비면 **status="blocked"** |
| **관측수 천장** | `:399 len(yCols)<4 → None` · `:427 len(years)<3 → None` · `:204 len(gSubset)<2` | **연간 5Y parquet → 성장률 4개 → 변화율 3-4개**. n≈3-5 구조적 천장. adjR² 없음(과적합) |
| **prebuild publish** | `:243 calcMacroExposureFromAnnualRevenue(*, years, revenue, macroAnnual, ...)` | Company 없이 lean. finance.json `macroExposure` 키(`buildFinanceJson.py:324`) |
| **지표 룩업** | `gather.mapping.exogenousAxes.getExogenousIndicators(stockCode=)` | 업종×제품 최적 외생지표 |
| **시장 macro 엔진** | `dartlab.macro(axis, target)` — `providers/dart/company.py:4992 macro(axis, target)` · cycles/rates/transmission | 사이클·금리·전이(시장 단위, 회사 매출 결박 아님) |
| **터미널 macroLens(선례)** | `ui/packages/surfaces/src/terminal/lib/macroLens.ts:55 evidenceLevel:'observed'\|'sectorPrior'\|'template'` | **이미 위계 폴백 개념 보유** — 회사 관측 없으면 sectorPrior. Part 2 가 백엔드로 승격 |

## 2.2 격차

- **n≈3-5**: 연간 5Y → 성장률 차분 → 변화율 차분 = 자유도 1-2. **R²<0.20 자동 차단 빈번**
  (`_qualityFromSelected:121`). 단변량 OLS 라 금리·환율·사이클 **동시 통제 불가**(누락변수 편의).
- **adjusted R² 없음** → 소표본 과적합을 R²↑로 오인. p값·신뢰구간 0.

## 2.3 강화 방법 (통계)

### 방법 A — 분기 history (관측수 ~4배)

- `calcMacroSensitivity` 의 연 매출(`:389 select("IS",["매출액"])` 연환산)을 **분기 매출 YoY**
  (`build.ts` 분기 윈도 패턴 — 계절성은 YoY 로 제거, `:284` 선례)로 교체. 5Y → **분기 ~20개 →
  YoY 16개**. macro 도 분기 평균(`:459 group_by year` → `group_by_dynamic quarter`).
- **게이트**: `MIN_OBS` 5→**8**(분기 8 = 2년). nObs<8 면 방법 C 폴백.

### 방법 B — 다변량 (금리 + 환율 + 사이클)

- 단변량 3회 → **다변량 OLS 1회**: `ΔrevYoY ~ β1·Δrate + β2·Δfx + β3·Δipi`(또는 업종최적 3축).
  현재 R² 수동 계산(`:499-505`)을 `numpy.linalg.lstsq`(이미 credit 이 numpy 사용 — `migration.py:21`)
  로 교체. **adjusted R²** = `1-(1-R²)(n-1)/(n-k-1)` 산출.
- **다중공선성 가드**: 회귀자 상관>0.8 이면 드롭 또는 PCA 1축. VIF 보고.
- **출력 확장**: `selected` 의 회귀를 *공동* 계수 + 표준오차 + p값으로. `exposureQuality` 에
  `adjRSquared`, `coef[]`, `pValues[]`, `vif[]` 추가.

### 방법 C — 위계 폴백 (회사 history 부족 시) ★ 핵심

- 회사 nObs<8 이거나 adjR²<0.20 → **섹터 단위 macro beta** 를 회사 노출 mix 에 적용:
  1. 섹터 macro beta = **같은 WICS 섹터 전 회사 분기 매출 YoY 패널 풀링 회귀**(회사 효과 흡수
     = pooled OLS 또는 fixed-effect). 표본 수십~수백배 → adjR² 안정. `scan` 패널(전종목 재무)이
     입력 — `data/dart/scan/finance.parquet`(prebuild 와 동일 소스).
  2. 회사 노출 mix = 회사의 매출 구성(수출비중·업종)으로 섹터 beta 를 *가중*. 노출 mix 부재시
     섹터 beta 그대로(coverage="sector").
  3. macroLens 의 `evidenceLevel`(`macroLens.ts:55`)과 정합: 회사회귀=`observed`,
     섹터폴백=`sectorPrior`, 둘 다 실패=`template`(정성). **스킵 없음**.

### 산출 계약 (`exposureQuality` 확장)

```jsonc
"exposureQuality": {
  "status": "quantCandidate|qualitativeOnly|sectorFallback|blocked",
  "method": "quarterly_revenue_yoy_multivar_ols | sector_pooled_beta",
  "coverage": "company|sector",          // sector = 폴백
  "evidenceLevel": "observed|sectorPrior|template",
  "nObs": 16, "rSquared": 0.34, "adjRSquared": 0.27,
  "coef": [...], "pValues": [...], "vif": [...],
  "window": "2021Q1-2025Q1 quarterly", "frequency": "quarterly",
  "sourceRef": "analysis.macroExposure:{code}", "sourceRefs": [...]
}
```

## 2.4 품질 게이트 + 정직 경계 (Part 2)

- **게이트(승격)**: `nObs≥8` AND `adjRSquared≥0.20` AND 최소 1개 계수 `p<0.10` → `status=
  "quantCandidate"`, `evidenceLevel="observed"`.
- **폴백(스킵 아님)**: 회사 게이트 실패 → 섹터 pooled beta(`coverage="sector"`,
  `evidenceLevel="sectorPrior"`). 섹터도 표본<30 또는 adjR²<0.20 → `status="qualitativeOnly"`
  + 정성 전이(macroLens transmission edge). **빈칸/스킵 금지** — 항상 한 단계 내려가 답한다.
- **honest boundary 명시**: 폴백 사용시 화면에 *"회사 자체 표본 부족 → 섹터(WICS XXX) 평균
  민감도로 추정"* 단서. 추정을 관측으로 위장 금지(`feedback_plan_score_not_signature` — 미검증
  주장 금지).

## 2.5 검증 / 졸업 게이트 (Part 2)

- **G1 OOS 안정성(out-of-sample)**: 분기 패널을 **시간 분할**(앞 70% train / 뒤 30% test). train
  beta 부호·크기가 test 구간에서 유지(부호 flip 비율 <20%, beta 비율 0.5~2.0). flip 빈번 = 과적합
  → 게이트 fail → 섹터 폴백. 테스트: `tests/analysis/test_macro_exposure_quality.py`(기존
  `:test_prediction_*` 동반) 에 `test_oos_beta_stability` 추가.

  > ⛔ **G1 실측 = FAIL (2026-07-06, `tests/_attempts/macroBetaStability/`).** 8 사 롤링 윈도로
  > `calcMacroRegression`(분기 다변량) 베타 부호를 쟀다. **겹침을 줄이면 게이트가 무너진다**:
  > 20q/4q(겹침 16q) 평균 flip **10.4% PASS** · 16q/8q(겹침 8q) **25.0% FAIL** ·
  > 12q/12q(비겹침) **52.1% FAIL**.
  >
  > ★ **측정 함정**: 겹치는 롤링 윈도는 인접 창이 데이터를 대부분 공유해 flip 을 **구조적으로 과소평가**
  > 한다. G1 은 **비겹침(또는 겹침 ≤ 절반) 윈도**로 재야 한다. 원안의 10.4% PASS 는 착시였다.
  > 조건은 오히려 관대했다(지표 집합을 전체 표본에서 고정 = look-ahead 이점). 그런데도 실패한다.
  > 공정 판정선 = 16q/8q 의 **25% FAIL**(12q 는 자유도 부족 잡음 혼입).
  >
  > **귀결**: 리포트의 매크로 민감도를 분기 다변량 회귀로 **라우팅 교체하면 안 된다.** 본 스펙의
  > "게이트 통과 전 리포트 미탑재" 가 옳았다. 현행(연간 `macroExposure` + `exposureQuality` 정직
  > 라벨) 유지. 베타 승격 전 **안정화 선행 필요**: 지표 수 축소(다중공선성) · 계층 베이즈(섹터 prior
  > 축소추정) · 부호 제약 · 표본 확대.
  >
  > 부기: §2.3 이 요구한 **방법 A(분기 YoY)·B(다변량 OLS)는 이미 구현되어 있었다**
  > (`_signalsMacroSensitivity.calcMacroRegression`, 삼성전자 실측 nObs 37). §2.3 이 지목한 연간
  > 코드는 **동명의 다른 함수** `macroExposure.calcMacroSensitivity` 다. 진짜 공백은 **방법 C(위계
  > 폴백)** 하나였고 `50804d441` 로 구현·검증 완료.
- **G2 섹터 폴백 sanity**: 섹터 pooled beta 부호가 도메인 사전(금리↑→차입의존 섹터 매출↓)과
  정합. 위반시 보고(데이터 오염 신호).
- **G3 prebuild 패리티**: `calcMacroExposureFromAnnualRevenue`(lean) 와 `calcMacroSensitivity`
  (Company) 가 같은 회사에서 동일 selected 지표·동일 status — 두 경로 발산 가드.

---

# 통합 (Integration)

## I.1 credit 섹션 ↔ risk 섹션

- dCR 7축의 **공시리스크(axis7)·재무신뢰성(axis6)·사업안정성(axis5)** 이 보고서 risk 서술의
  정량 앵커. credit 섹션 → liquidity(재무안정성) 관점에 흡수(§1.5 Step3). `notchAdjustment`
  (`engine.py:479`) 의 하향 notch 사유(재무약화·지배구조)가 risk bear 시나리오 입력.

## I.2 credit ↔ WACC cost-of-debt (02a 연결) ★

- **02a `02a-valuation-uplift.md:189-190` §4.4** 가 이미 명세: `company.credit("등급") → dCR 20등급
  → Kd 스프레드 테이블`(`reference/data/creditSpreadTable.json`, `{AAA:+30bp … CCC:+1000bp}`),
  `Kd = Rf + creditSpread(grade)`. **이중계산 회피**(Fernandez): 신용을 Kd 입력으로 단일화,
  qualityWACC 의 creditSpread 가감 제거(`02a:247 R4`).
- **본 스펙의 기여**: Part 1 이 publish 하는 `credit.grade` 가 **바로 그 02a Kd 입력**. /report 의
  DCF(02a) 와 credit 섹션이 **같은 dCR grade 를 공유** → 신용등급↔할인율↔밸류 일관. 별도 계산 0.
- 배선: 02a `_investmentAnalysisRoic.py:_estimateWacc`(`02a:154`) 가 creditGrade 주입받을 때,
  finance.json 의 `credit.grade`(Part 1 publish) 를 클라이언트 DCF 가 직접 읽어 Kd 산출 — Python
  재호출 불요.

## I.3 macro ↔ forward-view (포워드 전망, 02b 연결)

- 강화된 macro 민감도(`coef[]` + `evidenceLevel`)가 **02b forecast** 의 거시 시나리오 입력.
  forwardPdLadder(credit) 의 1/3/5y PD 와 macro forward 민감도가 **forward-view 섹션에서 결합**:
  "금리 +100bp·환율 +5% 시 매출 βΔ → 신용 notch 압력 → PD 이동". macro=매출 채널, credit=상환
  채널을 한 forward 서술로.

---

# 리스크 (Risks)

| # | 리스크 | 완화 |
|---|---|---|
| R1 | **prebuild credit 빌드 시간**: 전 상장사 Company 생성 무거움(OOM·시간) | credit 을 별 파일/배치 분리(§1.5 Step1). 순차 생성 + `del c`. 빌드 한도 재측정 후 단일 vs 분리 결정 |
| R2 | **credit==null 다발**(금융사 Track B fallback·미상장·데이터 부족) | honest-skip 폴백(healthTable). null 비율 모니터 — 과다시 엔진 fallback 점검(별도 트랙) |
| R3 | **transition.json 부재** → forward PD 사다리 degenerate | 단년 PD(`pdEstimate`) 만 ship, 사다리 생략. 운영자 `updateTransitionMatrix()` cron 으로 채움 |
| R4 | **finance.json 크기 증가**(credit 7축 metrics 임베드) | axes metrics 는 detail=False(요약)만. 필요시 creditExposure.json 분리 |
| R5 | **macro 다변량 다중공선성**(금리·환율 상관) | VIF 가드 + 드롭/PCA(§2.3 B). adjR² 보고로 과적합 노출 |
| R6 | **섹터 폴백 오정렬**(섹터 평균이 회사와 무관) | 노출 mix 가중 + evidenceLevel="sectorPrior" 단서. OOS G1 게이트 |
| R7 | **이중계산**(credit 을 risk·WACC 양쪽 페널티) | Kd 단일화(02a R4). 본 스펙은 grade publish 만, 가감 로직은 02a SSOT |
| R8 | **굽기 오해**(finance.json publish 를 베이크로) | §1.3 정합 논거 — 런타임 직독 불가(객체 부재) 실측 + macroExposure 선례. 운영자 승인 사항 |
| R9 | **시각 회귀**(/report UI 변경) | UI 자동 push 금지 — 운영자 눈검수 후만(`CLAUDE.md` UI push 예외, `feedback_ui_rules`) |

---

## 영향 파일 요약

**Part 1**: `.github/scripts/prebuild/buildFinanceJson.py`(credit 임베드) ·
`buildFinanceJsonUs.py`(null) · `landing/src/lib/report/build.ts`(buildCreditAssessment) ·
`model.ts`(타입) · `perspectives.ts`(선택) · `tests/audit/checkCreditPublishParity.py`(신규).
재사용(변경 0): `credit/engine.py`·`creditBadge.py`·`creditGradeTable.py`·`migration.py`.

**Part 2**: `src/dartlab/analysis/financial/macroExposure.py`(분기·다변량·섹터폴백) ·
`_signalsMacroSensitivity.py`(동반) · `tests/analysis/test_macro_exposure_quality.py`(OOS).
신규 섹터 pooled beta = `data/dart/scan/finance.parquet` 패널 입력(별도 빌드 아님 — scan SSOT).
