# 07. Integration Roadmap — 통합 터미널 비전 + 시퀀싱

상태: PRD v0.3 (2026-06-14 — 차트 suite 분리 후 **cross-category 브리지** 역할로 전환)
범위: 차트 suite(현재/과거 3 컴포넌트)와 시뮬레이션(미래)을 한 벌로 묶는 시퀀스, mainPlan 의존, 컴포넌트 간 의존성, Phase 로드맵.

> **★브리지 문서:** 컴포넌트 1~3(지수/레일/백테스팅)은 현재 UI surface가 소유한다. 07은 그 surface와 시뮬 코어를 잇는 유일한 cross-category 시퀀싱·공유 DNA·미래마커 이관 문서다. 의존은 현재 surface에서 미래 시뮬레이션으로만 흐른다.

---

## 0. 통합 비전 한 줄

**/terminal은 "차트에서 과거를 읽고(지수·공시·전략검증) 미래를 재생하는(시뮬레이터+Play)" 단일 작업대다.** 네 컴포넌트는 별개 기능이 아니라 같은 차트·같은 RunSpec·같은 ReportDock·같은 검증 척추를 공유하는 한 제품의 단면이다. 가치평가·신용은 시뮬의 읽기 방식(08·09 §4). 아키텍처 정합화(09)가 이 모두를 단일 SSOT로 묶는다.

---

## 1. 컴포넌트 4 + 2 파생 (문서 지도)

| # | 컴포넌트 | 문서 | 역할 |
|---|---|---|---|
| 1 | 지수 차트 | suite/01 | 차트 subject 전환(지수도 지표 계산) |
| 2 | 공시 이벤트 레일 | suite/02 | x축 아래 과거 공시 위치 |
| 3 | 백테스팅 Strategy Tester | suite/03 | 차트 전략 탐색 + 리포트 도크 |
| 4 | 시뮬레이션 + Play | 00·01·02·05 | ★미래 리플레이 코어 |
| 4v | 가치평가 보고서 | 08 | 시뮬 mode=whatif 단면 |
| 4c | 신용 보고서 | 09 §4 | 시뮬 solvency 뷰 |
| — | 아키텍처 정합화 | 09 | 시뮬레이터-앵커 부채 청산 |

---

## 2. 공유 DNA (왜 한 벌인가)

| 공유 자산 | 1 지수 | 2 레일 | 3 백테스트 | 4 시뮬 |
|---|---|---|---|---|
| PriceChart 인스턴스(soft-swap·draw·fullscreen) | subject | — | — | sim 모드 |
| RunSpec + provenance + asOf vintage | — | sourceRef | ✅ | ✅ |
| look-ahead 가드(t종가→t+1시가) | — | nextTradingDate | ✅ | ✅ |
| ReportDock 셸(mode 전환) | — | — | backtest | sim/valuation/credit |
| `nextTradingDateOnOrAfter` 트레이딩데이 snap | — | ✅ | — | ✅(미래 봉) |
| cross-panel highlight bus | — | ✅(우측행) | trade row | driver 클릭 |
| 검증 척추(scenario≠forecast·투자권유 금지) | 출처표기 | 인과금지 | 추천금지 | 가정노출 |

ReportDock(08 §5)은 **valuation 단일 모드로 시작**, backtest/sim mode는 각 엔진 졸업 시 추가(YAGNI 회피).

---

## 3. 컴포넌트 간 의존성 (시퀀스를 결정)

- **1 지수 → 독립**: 데이터 실재(gov/indices 105), IndexPort만. mainPlan 무관 선행 가능.
- **2 이벤트레일 → 과거만 독립, 미래 공시 마커는 4 의존**: 레일 PRD(suite/02)는 *과거 공시 위치*만 완결. **미래 공시 점선(예측 정기공시 예정일)은 시뮬 미래 캔버스(05 §3-2)가 있어야 표시할 곳이 생김 → 시뮬 트랙(4)으로 이관.** suite/02에서 데이터 계약(`DisclosureEvent`)만 준비.
- **3 백테스팅 → RunSpec/ReportDock/look-ahead DNA를 4와 공유**: 백테스팅 엔진(suite/03)이 RunSpec·ledger·과최적화 가드(DSR/PBO)를 먼저 안정화하면 시뮬이 흡수. **단 walk-forward DSR/PBO 인프라는 백테스팅 트랙이 SSOT, 시뮬은 재사용**(중복 신설 금지 — 09).
- **4 시뮬 → 1·2·3 흡수**: 지수=투영 대상, 레일=미래 공시 표현, 백테스트 도크=시나리오 리포트 도크. 엔진 09 Phase와 동기. 마지막.

---

## 4. 시퀀스 (각 완결·검증·푸시 후 다음)

1. **지수 차트**(suite/01) — 독립·즉시 가치. mainPlan 무관 선행(IndexPort 충돌 1회 확인).
2. **공시 이벤트 레일**(suite/02) — 과거 공시 위치 완결. `DisclosureEvent` 데이터 계약(미래 마커는 4로 이관).
3. **백테스팅 Strategy Tester**(suite/03) — RunSpec/ledger/provenance + 리포트 도크 + look-ahead 가드. DSR/PBO SSOT.
4. **시뮬레이션 + Play**(00·01·02·05·08·09) — 위 3 흡수. 09 Phase −1~7(부채 청산 ⨉ 코어 졸업). 마지막.

각 단계 `feedback_ui_rules` 준수(푸시 전 스크린샷 전수 눈검수·공개 터미널 무중단·미배선 커밋·완결 단위만). landing + ui/web(임베드) 둘 다 무중단.

---

## 5. mainPlan 의존 (★조기 진척 반영)

- **이 세션 중 mainPlan이 단계-4b~5로 진척** → 터미널이 `landing/src/lib/terminal/` → **`ui/packages/surfaces/src/terminal/`로 이동**(commit ff9099ba0). 즉 PRD의 모든 `landing/.../terminal/...` UI 경로 stale, 새 SSOT=`ui/packages/surfaces`(04 §3).
- **착수 시점**: 시뮬 코어(4)·발간(08)·UI(05/06)는 mainPlan 완료(터미널 ui/packages 정착) 후. 지수(1)는 선행 가능하나 IndexPort가 신 port 레지스트리(`createPublicRuntime` 16+포트)와 정합하는지 1회 확인.
- **포트 원칙 정합**: 모든 새 포트(IndexPort 등) required·silent fallback 금지·conformance(mainPlan 원칙). AI 3-티어(advanced/onDevice/deterministic)는 기능 가용성, 공개 AskDrawer 회귀 금지·열화 UX 숨김 금지.

---

## 6. 통합 Phase 로드맵 (09 Phase와 인터리빙)

> 엔진 Phase 번호(−1~7) 정본 = 09 §7; A/B 는 컴포넌트 삽입 phase, fatal①~④ 매핑은 본 표 셀 인라인. 별도 cross-walk 표 신설 금지(번호 이미 1:1 동일 좌표).

| Phase | 내용 | 컴포넌트 | 게이트 |
|---|---|---|---|
| **−1** | 무위험 즉시 청산(P14·P15·가짜 docstring·dead code) | 정합화 | `stale_references`·`vulture` |
| **0** ✅ | MC seed kill-test(전역 `random.seed`→로컬 `random.Random(seed)`, stdlib·PCG64 아님; `:205` cumprod) | 시뮬 척추 | `test_horizon_widens_cone`(완료, 09 P1) |
| **1** | 계약 동결(레이어·importlinter·census baseline, 코드 0줄) | 정합화 | census 현 baseline green |
| **A(병행)** | 지수 차트(IndexPort+subject) | 1 | svelte-check·스크린샷 |
| **2** | transfer 적출(lazy-proxy 소멸)·byte-identical 골든 | 시뮬 코어 | `test_import_direction` |
| **3** | DriverSheet + DCF 수렴(5→2 census, 09 §7 Phase 3/P3 — proforma-FCFF·calcDFV 2 정당경로) | 시뮬 코어 | byte-identical |
| **4** | 회귀 수렴 + DriverRegistry 게이트 + 이벤트레일 데이터 계약 + **★fatal②(P9a/b/c/f write primitives)** | 시뮬·정합화·2 | census·admission·**`test_forwardTestWrite`** |
| **5** | 졸업⑤~⑧ 본진 + 신용 통합 + **★fatal③(simulate/{ledger,admission,gate}.py + ai/tools/lens.py)** | 시뮬·신용 | engine-add 5점·lint-imports·**`test_{ledger,admission,gate}`** |
| **B** | 백테스팅 Strategy Tester(RunSpec·ReportDock·DSR/PBO) | 3 | 백테스팅 AC(suite/03) |
| **6** | 발간 단면(가치평가·신용 보고서·Play UI·ReportDock mode) + **★fatal①(금지어 lint T1+T2 발간표면)** | 4v·4c·05 | `test_story_no_self_calc`·**`test_valuationPublishLint`**·스크린샷 |
| **7** | 잔여 9섹션 docstring(만질 때만) | 전체 | `docstring9Section` |

★**fatal④(US 해금) = Phase A 와 병행 선행 가능**(지수와 동급, 의존 0): `simulate/{entry,registry,run,transfer}.py`+`synth/scenario.py`+`test_verb`/`test_run` — fatal①②③ 무관, 천장 상승 즉시 1건. registry/run 은 엔진트랙 Phase4 최신 위 rebase(09 §10.4 동시세션). ★**fatal①T1(lint) = ✅ 빌드·CI배선 완료**(2026-06-14, 발간 표면 0파일 green no-op·src 미스캔 CI red 0·6 unit PASS, 09 §10.1) — Phase 6 의 T2(발간 표면)와 독립.

핵심: 지수(A)·**fatal④(US)·fatal①T1** 는 1과 병행 선행, 백테스팅(B)은 3·4 사이 RunSpec 안정화, 시뮬 코어가 모두를 4~6에서 흡수. **4 fatal 빌드 티켓 완전 명세 = 09 §10 SSOT.**

---

## 7. 한 줄 종합

네 컴포넌트는 같은 차트·RunSpec·ReportDock·검증 척추를 공유하는 한 제품. 지수(선행)→이벤트레일(과거)→백테스팅(RunSpec)→시뮬+Play(흡수, 마지막). 미래 공시 마커는 이벤트레일에서 시뮬로 이관, DSR/PBO는 백테스팅 SSOT를 시뮬이 재사용. mainPlan 완료(터미널 ui/packages 정착) + 운영자 go 후 착수. 정합화(09)가 전 과정에서 부채를 외과적으로 청산.
