# Simulate — 미래 리플레이 시뮬레이터 PRD Index

상태: 비전 PRD v0.5 (스위트 버전 — 2026-06-20 9인 전문가 패널 uplift: 시각 인코딩 SSOT·Driver Coverage Census·G16 Calibration·valuation coherence·라이프사이클 dispatch·초보 학습성 3종 *가산* 적용, **새 파일 추가 0 = 기존 문서 내 절/소절/표 행 신설만**, 검증 척추 절은 불변 / 직전 v0.4 2026-06-14 구현 정합 정정: simulate/ 결정론 코어 졸업[4노드 DAG·random.Random·proforma-FCFF·공개 verb] 반영 + 문서↔코드 발산 정합)
범위: 과거 근거 → 미래 시뮬레이션. 거시·지수·뉴스·공시·재무를 미래로 투영하고, if(가정)를 켜고/끄며, **재생버튼으로 미래가 시간순으로 펼쳐지는 퍼포먼스**를 결과물로 내는 DartLab의 정점 기능.

---

## 현재 구현 판정 (2026-07-13 코드 재감사)

- **실행 가능**: 회사 단위 결정론 4노드 경로(`macro.path -> rev.path -> proforma -> dcf`)는 KR 실데이터에서 동작한다. 삼성전자 최신 기준 TTM 매출 앵커 388.3조원, baseline 3년 경로와 주당 DCF가 재현됐다.
- **이번 P0 복구**: 분기 시리즈를 쓰도록 바로잡아 연간 4개년 합산 오류를 제거했다. 알 수 없는 scenario의 baseline 묵시 폴백과 프리셋보다 긴 horizon을 차단했다. net debt 결손의 0 대체를 제거하고, 기본 WACC·성장률·마진·탄성을 `assumptions`로 노출한다. `asOf`와 vintage를 노드 해시에 포함한다.
- **PIT 한계**: `asOf`는 이제 해당 재무 분기까지 실제 절단하지만, 원천 시리즈가 공시 접수일별 정정 전 값을 보존하지 않는다. 따라서 현재는 **fiscal-period PIT**만 가능하며 filing-vintage PIT는 미완료다. 과거 발행주식수도 없어 과거 주당 DCF는 기권한다.
- **제품 미완료**: Play UI, fan distribution, driver override, lens, 다중 분기 비교 표면은 아직 없다. 따라서 PRD 전체를 완성 제품으로 부르면 안 된다.
- **계약 미완료**: `dartlab.simulate(...)`와 `Company.simulate(...)`는 호출 가능하지만 `CLAUDE.md`의 계약 엔진 목록과 Skill OS에는 `simulate`가 없다. axis-dispatch 형태를 결정하고 등록하기 전까지 안정 공개 계약이 아닌 preview다.

상세 변경과 검증 증거는 [04-progress-ledger.md](04-progress-ledger.md)의 2026-07-13 항목을 따른다.

---

## 한 줄 결정

이 기능은 "주가 예측기"가 아니다. `asOf` 시점에 알려진 근거와 명시 가정을 고정한 뒤, **재생버튼을 누르면 그 가정 하에서 미래가 시간순으로 펼쳐지는(주가·사건·지표·재무) 결정론적 리플레이 퍼포먼스**다. 핵심 명제: *미래를 맞히려는 게 아니라, 명시된 가정 하에서 무슨 일이 벌어질 수 있는지를 확률 분포로 있는 그대로 보여준다.* scenario ≠ forecast.

---

## 핵심 결정 요약 (v0.2)

- **엔진**: 새 **L2.5 독립 묶음** `simulate/`(드라이버 DAG + 엣지 transfer 소유, leaf 계산은 L2 SSOT 호출). story 동급 L3 기각(story=순수 렌더러 "자체 계산 0"인데 simulate는 transfer 계산 소유) + 신규 L2 기각(L2↔L2 cross-import 금지) → `L2_PEERS` 미소속이라 analysis+macro+quant 동시 결합 합법. 톱레벨 verb = `dartlab.simulate(...)`, 단일 종목 = `Company.simulate(...)`, `mode=whatif|replay|walkforward` 흡수. 상세 = [01-engine-architecture.md](01-engine-architecture.md).
- **중심 산출물**: ★Play 미래 리플레이 — 기존 터미널 replay 상태기계(과거 되감기)의 미래 방향 대칭 확장. 새 재생 엔진 0. 미래 캔버스는 사전 계산된 결정론 path를 *드러내는 것*(매 프레임 재계산 아님). → [05-play-future-replay.md](05-play-future-replay.md).
- **데이터 모델**: AssumptionLedger(if 토글 SSOT) + ScenarioTree(분기) + EvidenceGraph(근거-드라이버, 인과 단정 금지). 분기 생성 싸게·가지치기는 결정론 엔진(회계 항등식·과거 베타). Morphological Field/CIB는 다축 확장(Phase 5+)으로 deferred.
- **AI 의견**: 결정론 엔진 = SSOT, AI = `ai/tools/` lens 도구가 내는 ref 첨부 의견 카드. 채택 판정 = 결정론 gate(순수 함수). graph/node/pass 0 추가(no-graph-regression). → [03-validation-ai-review.md](03-validation-ai-review.md).
- **★차트 suite 분리(2026-06-14)**: 현재/과거 차트 3 컴포넌트(주가/지수 차트·공시 이벤트 레일·백테스팅)는 현재 UI surface가 소유한다. 셋은 시뮬 미완 게이트와 무관하게 독립 출시할 수 있고 시뮬 Play(05)가 단방향으로 소비한다.
- **통합 시퀀싱(브리지)**: 지수(suite/01) → 공시 이벤트 레일(suite/02) → 백테스팅 Strategy Tester(suite/03) → 시뮬레이션+Play(시뮬 코어, 4). 07이 cross-category 브리지(시퀀스·공유 DNA·미래마커 이관). mainPlan(ui/packages 승격) 이후 착수. 단 차트는 mainPlan 무관 선행 가능. → [07-integration-roadmap.md](07-integration-roadmap.md).
- **착수 전 선결 kill-test — ✅ 완료(2026-06-14)**: ★MC 재현성(`_simMonteCarlo.py:145`·`pricetarget.py:278` 전역 `random.seed` → 로컬 `random.Random(seed)`, **stdlib·pyodide 안전 — numpy PCG64 아님**) + `:205` 덮어쓰기 버그 → 연도별 cumprod(`test_horizon_widens_cone` kill-test로 옛 버그 증명 후 전환). 단 이 수정은 *레거시 MC 경로*(`analysis/forecast/_simMonteCarlo`) 한정 — **신생 `simulate/` 결정론 코어에는 MC 노드가 아직 없다**(mc.distribution 후속 단계, 01 §5b). Play 결정론·URL 공유·TS 패리티의 척추. 09 P1.
- **경쟁 지형 + 시그니처 판정(2026-06-14, 웹검증 6서비스 + 12 agent 토론)**: 단일 제품도 우리 4축 조립(텍스트=untrusted 드라이버증거→결정론 pro-forma + det/ai 평행경합+Brier + forward-replay + reverseDCF 닻)을 다 안 함 — 단 부품(특히 융합)은 commodity라 **차별은 기술이 아니라 "조립+규율"**. 시그니처 = **`conditional-signature`(합의 61, KEEP 조건부)**: wedge는 실재(reverseDCF 닻+L2.5 앵커=코드, 경쟁 교집합 비어있음)하나 검증 루프가 미완이라 "strong-signature가 아니라 될 설계". 타사 개념 흡수 = **absorb-as-defer 4종**(A1 명명프리셋·A2 충격전파·A4 라이브레버·A7 Brier리더보드) + reject 잔여가드(A5 점확률·A6 fan σ) — 전부 *새 기능 0, 한계 라벨/defer-게이트*로만("깎아서 강함"). 전문 = 00 §8b, 흡수 거처 = 02·01·05·03·04.

---

## 문서 지도

**코어 (시뮬레이터 엔진·방법·검증):**
1. [00-product-prd.md](00-product-prd.md) — 제품 비전, 사용자 문제, 핵심 화면, 범위, scenario ≠ forecast 검증 척추.
2. [01-engine-architecture.md](01-engine-architecture.md) — 엔진 거처 L2.5 `simulate/`·verb·AI 보완/경합·성능·횡단면·계층 계약.
3. [02-assumption-and-simulation-method.md](02-assumption-and-simulation-method.md) — 가정 장부·vintage·bridge·절차 + §2B DriverRegistry 수렴/확장.
4. [03-validation-ai-review.md](03-validation-ai-review.md) — look-ahead 차단·walk-forward·품질 게이트·AI 패널·반증·출시 기준.
5. [04-progress-ledger.md](04-progress-ledger.md) — 현재 결정·문서 상태·워크스페이스 변동·NEXT 닫기 체크리스트.
5b. [06-engine-readings-and-sweep.md](06-engine-readings-and-sweep.md) — ★"현재" 축 (2026-07-05 합의 탑재): 전 하위 엔진 판독(표면 전수 등재·기권 1급)·전량 봉인·주간 채점·가정 sweep(강건성 median·가정도 봉인·명명 프리셋/AssumptionLedger 정합). 00 §8b 가 지목한 검증 루프 미완을 대규모로 채우는 조각. 파생 뷰 = 주간 상승후보 100→10. P0 실측 완료(KR 543주 replay 3.7초).

**제품 경험 (UI 단면):**
6. [05-play-future-replay.md](05-play-future-replay.md) — ★중심 산출물. Play 미래 리플레이·미래 캔버스·다중분기·if 토글 실시간·근거 인벤토리·graceful degradation.
7. [07-integration-roadmap.md](07-integration-roadmap.md) — 통합 시퀀싱 **브리지**(suite/01 지수→suite/02 이벤트레일→suite/03 백테스팅→시뮬+Play), 공유 DNA, 미래마커 이관, mainPlan 의존, Phase −1~7.

**발간·정합화 (시뮬의 읽기 방식):**
8. [08-valuation-report.md](08-valuation-report.md) — 시뮬레이터=가치평가 엔진 동형, 적정주가(reverseDCF 닻+조건부 범위), 프로급 보고서, 규제선 가드. 발간은 코어 졸업 후.
9. [09-architecture-consolidation.md](09-architecture-consolidation.md) — 시뮬레이터-앵커 부채 원장(DCF 5중·회귀 4중 등 16행)·신용=solvency 뷰·외과 청산 Phase 시퀀스. **앵커 양방향**: 역=leaf 수학 금지(`test_simulate_leaf_ssot`), 순=leaf 계약 drift CI red(`test_simulate_leaf_binding`, P16).

**★분리 (차트 suite, 현재/과거):**
- 주가/지수 차트, 공시 이벤트 레일, 백테스팅은 현재 UI surface가 소유한다. 시뮬이 단방향 소비하고 07 브리지가 시퀀싱한다.
- 과거 문서 번호 `06`, `11`, `10`은 각각 현재 차트, 이벤트 레일, 백테스팅 구현을 뜻한다. 새 계획은 번호별 보관 문서를 참조하지 않고 실제 component와 contract를 확인한다.

> ⚠ UI 토폴로지: 본 세션 중 터미널이 `landing/src/lib/terminal/` → **`ui/packages/surfaces/src/terminal/`로 이동**. 차트 suite 문서(특히 02·03) 본문의 `landing/.../terminal/...` 경로는 stale — 새 SSOT는 `ui/packages/surfaces`. v0.3 워크플로가 토폴로지 코드-그라운드 전수 확정(04 §3). 02 mode enum 본문 통일 완료. 남은 v0.1 잔재: 00(제품명). 상세 = 04 §4.

---

## 버전 정책 + 스위트 버전

문서별 버전이 어긋나 혼란을 막기 위한 단일 규칙:

- **스위트 버전 = `v0.5`**(2026-06-20 — 9인 전문가 패널 uplift). 직전 v0.4(2026-06-14, 결정론 코어 졸업 정합)에 9인 전문가 패널의 개선 백로그를 *가산 적용*(새 파일 추가 0 = 기존 문서 내 절/소절/표 행 신설만): 시각 인코딩 SSOT 단일화(00 R8/R4 시각 문법·와이어프레임 포인터, 08 §3.2·05 정본)·Driver Coverage Census(회계품질 leaf 2종을 앵커 binding 게이트 안으로, 09 §0 표 7~8행 R3)·G16 Calibration(walk-forward DSR/PBO 과최적화 검증 게이트, 09 §10.3 R10)·valuation coherence(`_fnDcf` WACC-floor 0.5→dcf.py SSOT 1.0 통일, 09 §6 R16)·라이프사이클 dispatch(ScreenerModal→PriceChart 드릴다운 soft-swap, 00 §6.4 R23)·초보 학습성("경량 근사→정밀 딥다이브" toast·mini fan-spark 분위 sparkline, 00 §6.4). **개별 문서 헤더는 그 문서가 마지막으로 *내용 개정*된 시점의 minor를 단다**(README/09 = v0.5 수준 본 uplift 반영, 01/02/04/08 = v0.4 수준, 00/03/05 = uplift 가 닿은 절만 v0.5 라벨). 스위트 버전이 정본 — 개별 헤더는 *그 문서가 어디까지 따라왔나*의 표식이다.
  - **★R36 — version-header drift 정정(2026-06-20, 본문 불변·status 줄 표식만):** 정책이 "헤더=마지막 내용개정 minor"라 선언하나 실측 헤더는 `00`=「v0.2 정정 헤더」·`03`=「v0.2 정정」·`09`=「v0.3」로, 본문은 그보다 신선한 내용(00 v0.5 시각 문법·09 v0.5 R3~R51·03 v0.3 발간게이팅)을 담는다 = "표식" 주장과 byte 불일치. 봉합 = status 줄에 *마지막으로 따라온 minor 표식*을 1줄씩 append 해 README enum 과 정합: **`09`:3 끝 `+2026-06-20 v0.5`(✅ 본 라운드 적용 — 본 문서 owner)**, **`00`:3 끝 `+2026-06-20 v0.5 uplift`·`03`:3 「v0.2 정정」→「v0.2+v0.3 정정」(00/03 doc-owner 의 status-줄 sync — 본문 불변, 표식만)**. 본 README enum 이 그 표식의 SSOT — 헤더 minor 와 본문 내용의 gap 을 "2층 헤더(아래 줄)+status 표식"으로 있는 그대로 노출하지, 숨기지 않는다.
  - **★R43 stale SSOT boundary 정정(2026-06-20):** 직전 enum에서 시뮬 namespace에 없는 `06`을 삭제했다. `06/10/11`은 현재 UI surface가 소유하는 차트, 백테스팅, 이벤트 레일 컴포넌트이며 시뮬 버전 namespace와 별도 수명주기를 가진다.
- **minor 범프(0.x→0.x+1)** = 코드-그라운드 사실 정정 또는 새 결정이 한 문서 이상에 반영될 때. **patch(문구·오타)** = 헤더 갱신 없이 본문만 수정. **major(1.0)** = 본진 `simulate/` 졸업 + 발간 게이트가 *기계 강제*로 검증된 뒤(현 미충족 → 09 §10 fatal①~④: 발간표면 투자권유 lint[★T1 빌드·배선 완료]·forward-test write 끝단·gate/ledger/admission/lens·US 해금) **+ ⑤ simulate↔leaf 계약 drift 자동인식(`test_simulate_leaf_binding`, 앵커 순방향, 09 §6·P16)** — 엔진 변환 시 simulate silent 깨짐 0 의 5번째 conformance 표면.
- **2층 헤더(v0.1 본문 + v0.2 정정)** = 정정 헤더가 본문보다 우선(00·03). 정정 헤더가 정본, 본문은 미개정 잔재로 읽는다.
- **구현 정합 = 코드가 정본.** 문서 주장이 `src/dartlab/simulate/` 구현과 어긋나면 코드를 정본으로 문서를 고친다(반대 아님). "구현 완료"는 헤더 오버레이가 아니라 본문 텍스트까지 코드와 일치할 때만 ✅.

---

## 검증 척추 (전 문서 관통)

거시·beta·뉴스의 미래는 **예측하지 않고 가정으로 받는다**(scenario ≠ forecast). 회계 항등식(BS 균형·CF 재조정)만 강하게 주장한다. 단일 점추정 금지(fan chart 기본). 결손은 0 대체 금지(missing/blocked/partial 라벨). AI 숫자는 fact 미승격(hypothesis). look-ahead 차단(t종가신호 → t+1시가). 출력에 추천/단정 표현 금지. 본진엔 졸업 게이트 통과 전까지 0줄(시작 = `tests/_attempts/scenarioSimulator/`).

- **★R58 — 근사/미검증 라벨 접근성 (색무관 텍스트 항상 동반 + 200% 확대, 2026-06-20, 적대 레드팀).** 근사·미검증 구간을 amber(`var(--amber, #fb923c)`) 11px 점선 배지로 박는 규율(05 §1.1·08 §3.4)은 통과하나, *11px amber 점선만이 유일 신호*일 때 두 접근성 결함이 생긴다: (1) WCAG SC 1.4.1 — 의미가 "amber 색 + 점선 테두리" 두 *시각* 채널뿐이라 스크린리더(SR) 미도달·색맹 사각, (2) SC 1.4.4 — 11px 가 텍스트 200% 확대 대응 미명시. ⟹ 검증 척추에 박는다: **`근사`(또는 `미검증`) 텍스트 라벨을 색과 무관히 *항상* 동반**(amber 는 강조지 *정보의 유일 운반체가 아님* — 텍스트가 SR·색맹·흑백 인쇄 모두에 도달) + **200% 확대 시 11px→레이아웃 깨짐 0**(배지가 줄바꿈/overflow 없이 확대 — 05/08 amber 배지 전수로 확장, 일부만 명시된 것을 전 배지 규율로). 새 색·새 컴포넌트 0(기존 amber 토큰·기존 배지 재사용 = 텍스트 라벨 1개 동반만).
  - **★코드 정본 정정(배경 토큰 SSOT 분리, R17 동일 SSOT):** 근사 배지의 거처 = ReportDock(=`StrategyDock.svelte` fill 일반화)이며 그 배경 fallback 리터럴은 **`var(--dl-bg-base, #0a0e15)`·`var(--dl-bg-raised, #0e141f)`**(`StrategyDock.svelte:396/441/470` 등 실측 = ReportDock-local fallback). ⚠ 이 두 값은 *StrategyDock fallback 리터럴*이지 **글로벌 토큰 SSOT 가 아니다** — `ui/packages/design/src/styles/tokens.css:17-18` 의 canonical `--dl-bg-base: #0f0f10`/`--dl-bg-raised: #16171a` 와 *다르다*(터미널 surface 가 자기 fallback 을 별도 박은 표면, 실측 drift). 따라서 README 가 배경 토큰을 인용할 때는 "ReportDock fallback = `#0a0e15`/`#0e141f`(StrategyDock 실측), 글로벌 토큰 SSOT = `#0f0f10`/`#16171a`(tokens.css)" 로 *두 층을 분리*해 적는다(한쪽을 SSOT 로 오인=환각 — rank17 토큰 인용과 동일 규율). amber=`#fb923c`(`--amber` fallback, `terminal.css:777` 등 실측)는 단일 SSOT 일치.
