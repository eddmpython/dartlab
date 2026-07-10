# 04 · Phase 분해 · 졸업 게이트 · 가드레일 · 결정사항

> operator 확정 순서: **능력 먼저(P1) → 리포트 엔진(P2) → 랜딩 동일소비(P3)**. 각 phase·sub-phase 는 독립 출하·롤백 가능. 각 능력은 졸업 게이트 통과 후 다음.

## P0 · 현상태 publish (선행)

라이브러리 안정화 단계 → 현 안정본 publish 후 착수. 능력 격상은 publish 뒤.

## P1 · 능력 엔진 격상 (SSOT de-gate + 검증)

밸류에이션이 의존 허브이므로 **02a 먼저**. 이후 병렬 가능하나 게이트 순서 유지.

| sub | 엔진 | 산출 | 졸업 게이트 (통과 전 리포트 미탑재) | 롤백 |
|---|---|---|---|---|
| P1a | 밸류에이션 (02a) | de-gate calcDFV·bottom-up WACC 배선·재투자성장·fade·reverse-DCF·가중삼각·`_dFVDrivers.py` | G1 단위항등 + G2 백테스트(20사 t+12M, 방향>55%·중앙오차 무회귀) + G3 민감도 + G5 consistency≥70 | de-gate edit revert(엔진 기존경로 보존) |
| P1b | 전망 (02b) | driver 계단·fade·영업레버리지 마진·`_revenueBacktest.py` | G1 MAPE≤8/15% + G2 방향≥70/60% + G3 밴드커버 + G4 skill>0 | forecast 기존 경로 유지(추가형) |
| P1c | 세그먼트 (02c) | 부문 마진 도출(배분+peer reconcile)·`calcOperatingSegmentSotp` | 공시사 백테스트 MAE≤5%p·커버≥80%·ρ≥0.6 (미통과 시 방향/믹스만) | `marginSource=derived` 플래그 off |
| P1d | 정량 moat (02d) | `analysis/financial/moat.py` 5성분 등급 + `unmeasured[]` | cohort 평균회귀 백테스트(wide vs none, T+3 fade 저항) | 신규 모듈이라 미배선 = 무영향 |
| P1e | 신용 라이브 + 매크로 (02e) | credit→finance.json publish · forward PD lookup · 매크로 분기/다변량/sector 폴백 | credit panel parity(byte동일)+79사 보존 · 매크로 β-stability(sign-flip<20%) | publish 필드 제거(엔진 0-변경) |

**P1a 가 P1d(moat fade)·P1e(Kd)·P1b(ROIC성장)의 선행** — 의존그래프(02 §2).

## P2 · 리포트 엔진 갈아엎기

1. **삭제 ~2,834 LOC**: `story/macro/`(1823)·`publisher.py`(327)·`sixAct.py`(268)·`dashboard.py`(121)·`sections/`(1). (reportTypes/templates 는 死코드 아님. emitter 가 대체하며 은퇴.)

   > ✅ **실행 완료 2026-07-06 (`682ca3bf3`), 단 목록 1 건 정정.** import 전수 census 로 死/生 을 갈라
   > `story/macro/`·`publisher.py`·`sixAct.py`·`sections/` **2,419 LOC 삭제**. `viz/generators::specSixActRadar`
   > 도 폐기(`c85c40147`, provenance 를 사라진 모듈로 주장하던 고아).
   > ⛔ **`dashboard.py`(121) 는 死코드가 아니다**: `.github/scripts/prebuild/buildStoryManifest.py:14` 가
   > `listDashboardQuestions`(고정 8 문항 팩)를 실사용한다. 소비자 이관 전엔 삭제 불가 → 존치.
   > 부수 발견: `engines/credit` SKILL.md·methodology.md 가 내부 모듈 `story.publisher.publishReport` 를
   > **공개 호출 예제로 노출**하고 있었다(공개계약 정책 위반). 등록 계약 `Company.story(type="credit")` 로 교체.
2. **emitter 신설**: `story/report.py::buildReportModel(company, perspective) -> ReportModel`(TypedDict), L3, self-calc 0, 기존 `builders/` + 격상 능력(02) 조립. `ai/agent.py` 본체 아님.
3. **계약 SSOT**: `ui/packages/contracts/src/reportModel.ts`(기존 `report.ts`/`ReportPort` 충돌 회피한 파일명) — ReportModel + 18블록 + Thesis/ValuationView/ScenarioSet/ForwardView. EvidenceRef·FinCard 재사용.
4. **소비자 마이그레이션**: `Company.report()`·`dartlab report` 추가(기존 `story()` 유지), 테스트 ~277 대부분 무변.

## P3 · 랜딩 동일 소비

1. landing `build.ts` → 같은 `ReportModel` emit(라이브, 브라우저, 베이크 0). 단일 fetch SSOT(`dataCore.requestParquetRows`) 유지.
2. `model.ts` = `reportModel.ts` re-export shim(기존 import 무회귀, 추가형).
3. **drift parity**: 6 상수만 박제(verdict 임계·window guard·peer cut·valuation model-selection·thesis 규율·arc 순서), N=5 회사 ~20 셀 golden-parity, `tests/run.py` 배선. 전체 스냅샷 parity 금지(유지비 폭탄).
4. **UI 게이트**: 푸시 전 스크린샷 전수 눈검수 + 운영자 명시 승인("푸시해"). 5관점·모바일·인쇄·라이트/다크 전수.

## 강행 가드레일

- ⛔ 런타임-SSOT: 베이크 금지. P3 브라우저 직독·parity, 굽지 않음.
- ⛔ no-graph-regression: emitter 는 평범한 함수(`*Loop`/5패스 노드 0), companyStory MCP 부활 금지. `checkAgentBoundary.py`.
- ⛔ find-SSOT-improve: P1 전부 정본 모듈 in-place(병렬빌드 0).
- ⛔ 날조 금지: 모든 추정 = 방법·가정 노출 + 게이트 검증. 미검증 확신 금지.
- ⛔ OOM 가드: 백테스트 module-scope fixture·직렬 load. ⛔ master only·변경단위 commit·UTF-8.
- ⛔ _attempts 졸업: moat(02d)는 `tests/_attempts/quantMoat/` 개념확립 후 `analysis/financial/moat.py` 본진.

## 운영자 결정 (확정)

1. **신용 prebuild-publish (02e P1) — ✅ 조건부 승인 (2026-06-26).** 코드 검증 완료: `evaluateCompany`(`creditBadge.py:40-44`)는 full Company(재무3표·sector 임계·CHS·7축·Notch) 필요 → 브라우저 산출 불가. TS 재구현은 *79사 검증모델 2중 구현 = 영구 parity 부담 = 관리불능* 이라 더 나쁨. `macroExposure` 가 *이미* 같은 루프에서 finance.json 에 임베드(`buildFinanceJson.py:324`) → 같은 단일 빌드에 한 줄 추가. **즉 publish 가 덜-덕지덕지한 선택.**

   **관리 가능 가드 (덕지덕지·관리불능 방지 — operator 조건):**
   - ① **단일 경로만**: `buildFinanceJson.py` 의 기존 루프에 `data["credit"]=getDcrBadge(...)` 한 줄. *새 파일·새 파이프라인·새 빌드 스텝 금지.*

     > ⛔ **가드① 전제는 성립하지 않는다 (2026-07-06 실측 반증).** 그 루프(`buildFinanceJson.py:320-332`)엔
     > **Company 객체가 없다**. `_extract_annual(df, code)` 로 parquet 행만 뽑는다. `macroExposure` 는 순수
     > 데이터(revenue 배열+meta)라 되지만, `getDcrBadge → evaluateCompany` 는 **full Company 를 요구**한다
     > (`credit/engine.py:189` `Company(stockCode)`, docstring "Requires L1 raw 접근").
     > 오프라인 자체는 가능하다(`enforceOffline()` 아래 `Company("005930")`+`evaluateCompany` = `dCR-AA`, 2.6s).
     > 그러나 **메모리가 막는다**: 4 사 직렬 + `del` + `gc.collect()` 에도 RSS 91MB→986MB, **사당 순증 224MB**
     > → 3,000 사 외삽 수백 GB **OOM**. CLAUDE.md "gc.collect() 회수 0" 이 실측 확인됨.
     > "얇은 Company 어댑터" 도 불가: 엔진이 `select` 외에 `_finance`·`_getFinanceBuild`(private)·`gather`·
     > `notes`·`governance`·`panel` 까지 접근한다(브리틀 커플링 = 관리불능, 가드 취지 위반).
     >
     > **남은 실현 경로(운영자 결정 필요)**: ③ 퍼블릭 credit 베이크 포기(런타임/로컬 전용, 퍼블릭은
     > honest-null. §1.6 G3 가 이미 설계한 폴백) · ④ 프로세스 격리 청크 베이크(새 빌드 스텝 = 가드① 완화 필요,
     > 3,000 사 × 2.6s ≈ 2.2h) · ⑤ credit 엔진 데이터전용 리팩토링(가드② 정면 충돌, 대규모).
     > ★ **런타임 경로는 이미 작동한다**: `reportModel()` 이 단일 회사 런타임에서 `creditPanel` 을 정상 산출
     > (`85bc5273d`, 삼성전자 `dCR-AA`·PD 0.02·7 축). 막힌 것은 *퍼블릭 베이크* 뿐이다.
   - ② **단일 소스**: Python credit 엔진 0-변경. *TS 재구현 영구 금지*(2중 구현이 곧 관리불능).
   - ③ **정의된 스키마**: credit packet(grade·gradeRaw·axes·pdEstimate·outlook·confidence)을 `reportModel.ts` 계약 필드로 *명시 정의*. loose blob 금지.
   - ④ **빌드비용 관리**: per-company `evaluateCompany` ×~3,000사 = OOM 가드(module-scope·직렬·BoundedCache) + 빌드시간 측정·기록. forward PD 는 20행 grade→PD lookup 1회 ship(per-company 루프 밖 join).
   - ⑤ **offline 가드**: `offlineGuard.enforceOffline()` 적용(prebuild = offline only). `macroExposure` 와 동일 거버넌스(staleness = 동일 rebuild 케이던스, 새 미관리 산출물 0).
2. **순서 확정**: P1(능력)→P2(엔진)→P3(랜딩) — operator 확정. P1 내 02a 선행 확정.

## 리스크 요약

| 리스크 | 완화 |
|---|---|
| 백테스트 OOM | module-scope fixture·직렬·BoundedCache |
| 격상이 기존 답변 회귀 | de-gate 는 추가형, 기존 경로 G4 무회귀 게이트 |
| credit publish 가 덕지덕지·관리불능化 | §결정1 5가드(단일경로·단일소스·정의스키마·빌드비용·offline). ✅ 조건부 승인 |
| 두 빌더 drift | 6상수 parity(전체 아님) |
| UI 시각 회귀 | 스크린샷 눈검수 + 운영자 승인 push |
