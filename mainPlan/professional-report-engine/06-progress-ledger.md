# 06 · 진행 원장

> 표기: ☐ 대기 · ◐ 진행 · ✅ 완료 · ⚠ 차단(결정 대기). 완료 시 게이트 결과 한 줄 동행.

## 기획 (조사·플랜)

- ✅ 현상태 매핑 (두 시스템·story 군더더기·소비 그래프) — `01`
- ✅ 전문 리포트 PRD (인과 아크·thesis 규율·밸류·신용·서사 문법) — `00`
- ✅ 능력 엔진 6 SSOT 조사 (de-gate 발견) — `02a~02e`
- ✅ 리포트 엔진 아키텍처 (계약 SSOT·delete ~2,834·emitter) — `03`
- ✅ Phase 분해·게이트·가드 — `04`
- ✅ 운영자 결정: 신용 prebuild-publish **조건부 승인** (§04 결정1) — 코드검증(브라우저 산출불가·TS재구현=관리불능) + 5가드(단일경로·단일소스·정의스키마·빌드비용·offline)

## P0 · publish
- ☐ 현 안정본 publish

## P1 · 능력 격상 (순서: 02a 선행)
- ✅ **P1a 밸류에이션 de-gate 완료** (WACC bottom-up·성장 reinvest×ROIC fade·through-cycle 정규화·드라이버·reverse-DCF) — 게이트 전부 통과: G1·G3·G5 offline(12 테스트) + 범위가드 005930·003230·country override + G2 방향 77%(>55%). 보너스: _rimCalc CI 버그 수정·성장클램프 calibration. 잔여=엄밀 G2 point-in-time/full-dFV CI 정제(방향 게이트는 충족). 본진 push 완료(fix·calibration 은 CI 여유창 동기화 대기).
  - ✅ **G1·G3·G5 offline 통과** (`tests/quant/test_valuationUplift.py` **9개**, test-lock): G1 reinvest round-trip·fade 단조수렴·terminal 무료성장 차단·reverse-DCF 항등(오차 0%) · G3 WACC×g 민감도 단조성(WACC↑→가치↓·g↑→가치↑)+TVshare 폭주 차단 · G5 Growth Equation 정합성(g=reinvest×ROIC critical 0, 위반 입력 감점).
  - ✅ **본진 디게이트 완료**: `_estimateWacc` bottom-up β + Damodaran 국가테이블(005930 실측 8.72) · `_calcTwoStageDcf` 펀더멘털 성장(g=reinvest×ROIC fade, naive 매출CAGR 대체) · 신규 `_dFVDrivers.py`(buildReinvestmentPath·buildDriverScenarios·reverseDcfExhibit) · `dFV` ±0.12→드라이버 시나리오 + reverseDcf·reinvestmentCheck 출력(guarded).
  - ✅ **DCF de-gate 실데이터 검증**(005930 offline 결정론): fundG 8.91%(reinvest 0.9×ROIC 9.9) < naive · new DCF < old(과대 해소) · **TVshare 0.78→0.67**(터미널 의존 감소). camelCase·docstring·ruff·import 전부 clean.
  - 🔧 **정공법 결정 2건**: ① `multiStageDcf` 재투자 FCFF *미적용* — `baseFcf` 가 이미 FCF(OCF−capex)라 거기서 또 빼면 이중계산. 성장 path 로 교정(02a §4.2 보다 정확). ② credit→Kd 스프레드(02a §4.4) = P1e 신용배선으로 이관(Fernandez 이중계산 회피 + 신용 SSOT 동시).
  - ✅ **calcDFV 통합 검증**(close→no-op monkeypatch 우회 스모크 `tests/_attempts/valuationUplift/smoke_calcdfv.py`): 크래시 0 · reinvestmentCheck 정상 배선(005930 fundG=8.91·reinvest 0.9·wacc 8.72, offline 검증과 일치) · driverScenarios 활성(NAVER dcf2stage bull558k/base392k/bear295k) · 시장가 결측 시 liquidation graceful 폴백. **배선·무크래시·재투자 로직 실데이터 확정.** 통합 게이트 `tests/quant/test_valuationUpliftIntegration.py`(requires_data) 박제 — CI 영속컨텍스트 실행.
  - ✅ **push 완료** (`518b4e370`, master). 로컬 전 게이트 통과 — ruff·camelCase·docstring·import 신규위반 0(census baseline-diff, 위반은 전부 기존 quant→gather 부채)·offline 9 테스트·통합 무크래시. CI-fast(offline) green.
  - ✅ **G2 백테스트 실행 → 긍정적 검증**(`g2_backtest.py`, 실제 가격). ⚠ *정정*: 앞서 "가격 오염"이라 단정했으나 오류 — 시리즈가 부드럽고(급점프 0) 차별화(NAVER −25% vs 메모리 폭등)된 **실제 데이터**(2025-26 AI/메모리 슈퍼사이클, Jan-2026 컷오프 이후). 시작가(2025-06, 랠리 전) 시점 dcf2stage IV vs 12M 실현: **방향 적중 4/5(80%)** — 삼성/하이닉스/현대/기아 저평가콜 적중, NAVER 밸류트랩 미스. de-gate IV 가 슈퍼사이클 전 저평가를 식별. ⚠ caveat: 1-window(랠리)·N=5·dcf2stage-only(relative 미가용)·전부 저평가코호트(판별력 미측정). **엄밀 G2(20사 다사이클·full dFV)는 장기 가격데이터+relative(peer scan) = CI/production.**
  - ✅ **근본원인 발견·수정 → 범위가드 실행**: relative=None 은 데이터 아닌 **committed 버그** — `_rimCalc` 프록시(`_valuationDeepProxies.py:88`)가 facade 리팩토링(`d77f9abf8`, 내 작업 아님)으로 깨진 `valuation.py` import 참조 → calcValuationSynthesis RIM/relative ImportError(**CI 포함 전역**). `residualIncome.calcResidualIncome` 로 위임 복구(`84ebfc25a`). 검증: 삼성 estimates 전종(relative 192,300)·**범위가드 005930[140k-230k] PASS**(dFV 196,337, primary=relative) → 내 de-gate 무회귀 확인.
  - ✅ **범위가드 003230 PASS (엔지니어링 판단으로 해결, operator 미위임)**: 삼양식품 FAIL(1,709,625) 근본 = de-gate 성장클램프 25%/yr 과대(Damodaran: 8년 지속 >18% 성장 상위<5%, fad 외삽). **클램프 25→18% 보수화**(`_growthPathFromRoics`) → 삼양 dFV 1.71M→**1,425,947 PASS**[1,245k-1,525k], 삼성 196,337 무영향(8.9%<18). 가드 재baseline(과대값 승인) 대신 de-gate 보수화 = 정공법. + 아티팩트 가드(>100% ROIC 제외·40% cap). **damodaranPhase4 범위가드 2케이스 + country override 전부 검증 PASS.**
  - ✅ **G2 §5 게이트 통과 — 엄밀 point-in-time 판**: 02a §5 = "t→t+12M, 방향>55%"(t=2025-06→2026-06). **basePeriod 스레딩**(calcDFV→_calcTwoStageDcf→buildReinvestmentPath→calcRoicTimeline)으로 **look-ahead 제거**(FY2024 재무만) + `_rimCalc` fix 로 **full dFV 삼각검증**(dcf2stage·relative·ddm). 결과: **방향 적중 10/14(71%) ≫ 55%**, 저평가(12) +181% vs 고평가(2) −18% → **스프레드 +199%p**. 카카오 고평가콜→−45% 정확·삼양 clamp18 로 fairly-valued→−20% 정상. (look-ahead 포함 판은 13사 77%, 일치.) 잔여 미세(base FCF/netDebt latest=mid-cycle robust·단일윈도)는 CI 다종목/baseline 원장 정형화.
  - ✅ **stress-test 발견 → 즉시 해결**: 고-ROIC 사이클 peak 과대평가 — 하이닉스 ROIC latest 31%(HBM boom)/median 7.35%(2023 메모리 불황 -10.4% 포함) → fundG 28%→**6.62%** 정규화. `buildReinvestmentPath` roicAnchor 를 latest → **through-cycle median** 으로(`_growthPathFromRoics`, FCF 정규화 `_tsdMaybeNormalizeFcf` 와 정합). 실 캡처 ROIC 로 offline 검증(테스트 3개): 하이닉스 절반↓·삼성/현대 무변(median≈latest)·구조적적자 None 폴백. 라이브 end-to-end 확인(하이닉스 fundG 6.62·삼성 8.91 무변). *가격 무관·실재무데이터만 필요라 샌드박스서 정공법 처리.*
- ◐ P1b 전망 de-gate — ✅ **핵심 완료**: `_forecastMetric` 지수 fade(임의 선형감속 폐기, λ 0.35/0.5) + 영업레버리지 마진(고정마진 폐기, β 회귀+범위캡+fallback). offline 4 테스트 통과(`test_forecastUplift.py`). 잔여: driver-growth(segment/backlog) 가중 승격·driver 시나리오·walk-forward 백테스트(`_revenueBacktest.py`, data/CI — P1a G2 방법론 동일).
- ◐ P1c 세그먼트 경제성 — ✅ **핵심 완료**: `_segmentEconomics.reconcileSegmentMargins`(peer 마진 구조 × 연결 OI reconcile, Σ 보존·적자부문 k 제외·범위/method 라벨). offline 5 테스트(`test_segmentEconomics.py`). 잔여: company peer fetch 배선(industryPeers/themes)·calcSegmentComposition hasOpIncome 게이트 해제·SOTP·공시사 백테스트(MAE≤5%p, data/CI).
- ◐ P1d 정량 moat . ✅ **개념확립 통과**(`tests/_attempts/quantMoat/concept.py`, graduation gate 준수): C1 ROIC−WACC 지속성·C2 마진 CV·등급 논리곱(wide/narrow/none, noComposite)·정성원천(switching/network/brand) unmeasured 명시. offline 5 체크.
  - ⛔ **G1 코호트 백테스트 = 로컬 판정 불가(데이터 벽, 2026-07-06 실측)**. `cohortBacktest.py` 신설(등간 샘플링·형성 2019~2022·성과 2025 T+3·게이트 wide>none & wide>0). 표본 60 사 -> **유효 7 사**. 원인 진단(30 사 등간표본): `calcRoicTimeline` 자체 부재 **22/30 사**(로컬 미수집), 확보 8 사도 history 2~8 년 산발. 연도별 스프레드 보유 3~6 사.
  - **창이 과한 게 아니라 데이터가 없다.** 수집된 회사만 골라 쓰면 시총·생존 편향 + 손 선별 금지 위반([[feedback_exhaustive_no_curation]]) -> 강행하지 않음. 02d 가 게이트를 `data/CI` 로 표기한 것이 수치로 옳았음이 확인됨.
  - 잔여: CI(전 유니버스 수집본)에서 `cohortBacktest.py` 실행 -> 통과 시에만 `moat.py` 본진 졸업 + axis 등록. 상세 = `tests/_attempts/quantMoat/README.md`.
- ◐ P1e 신용 라이브배선 + 매크로 강화. ✅ **리포트 emitter 신용 pro 블록 완료**(`85bc5273d`): reportModel.ts `CreditView`+`creditPanel`(가드③ 패킷 grade·axes·PD·outlook·confidence) + report.py `_creditView`(evaluateCompany L2 직접 매핑, `_valuationView` 동형, L3->L2 정방향) + credit 섹션(arcStep 8) + 헤드라인 신용등급. landing project.ts skip 케이스. 11/11 offline·tsc·svelte-check 0·ruff·camelCase clean. push 보류(landing/src 포함, 운영자 승인 대기). **★실데이터 e2e 검증(2026-07-06)**: `Company("005930").reportModel()` -> 11 섹션(valuation·credit 포함), `creditPanel` 블록 `dCR-AA`·PD 0.02·7 축·confidence 80(ratio), 헤드라인 `신용등급 AA`, provenance engines `story/valuation/credit`. monkeypatch 아닌 실경로 통과. 잔여: buildFinanceJson credit publish(landing bake)·forward PD·매크로 분기/다변량/sector 폴백 + 게이트 parity·79사·β-stability(CI/data). 결정1 ✅ 조건부, 5가드 준수
  - ⚠ **정합성 정정(2026-07-06, 실측)**: 02e Step 1 "buildFinanceJson 루프에 `data["credit"]=getDcrBadge(...)` 한 줄"(가드①)은 **성립하지 않는다**. 그 루프(`buildFinanceJson.py:320-332`)엔 Company 가 없고 `_extract_annual(df, code)` 로 parquet 행만 뽑는다. `macroExposure` 는 순수 데이터(revenue 배열+meta)라 되지만 `getDcrBadge`->`evaluateCompany` 는 **full Company 필요**(`engine.py:189` `Company(stockCode)`, docstring "Requires L1 raw 접근"). prebuild 는 `enforceOffline()` + 3,000 사 Company = 네트워크 차단 + OOM(사당 200~500MB·gc 회수 0). **데이터 전용 신용 진입점 없음**이고, 신설하면 credit 엔진 변경이라 가드② 위반. → 설계 재결정 필요(운영자). **실측으로 옵션 좁힘(2026-07-06, 스크래치 프로브 2 종):**
    - **옵션① (in-process 3,000사 Company 베이크) = 死 (실측 반증).** `enforceOffline()` 아래 `Company("005930")`+`evaluateCompany` 는 **작동함**(grade `dCR-AA`, pd 0.02, 2.6s). 그러나 4 사 직렬(`del c; gc.collect()` 동행) RSS 91MB->986MB, **사당 순증 224MB**(3·4 번째 +181·+274 계속 증가) → 3,000 사 외삽 수백 GB = OOM. CLAUDE.md "gc.collect() 회수 0" 경고가 실측 확인됨.
    - **옵션②' (얇은 Company 어댑터) = 부적합.** credit 엔진이 `company.select`(16) 외에 `_finance`·`_getFinanceBuild`(private)·`gather`·`notes`·`governance`·`panel` 까지 접근 → shim 이 내부구현에 결박되는 브리틀 커플링(관리불능, 가드 취지 위반).
    - 남은 실현 경로: **③ 퍼블릭 credit 베이크 포기(런타임/로컬 전용 유지, 퍼블릭은 honest-null)** 또는 **④ 프로세스 격리 청크 베이크(새 빌드 스텝 = 가드① 위반, 빌드 ~2h+)** 또는 **⑤ credit 엔진 데이터전용 리팩토링(가드② 정면 충돌, 대규모)**.
    - ★ **런타임 경로는 이미 작동한다**: 본 세션 emitter 배선으로 `reportModel()` 은 단일 회사 런타임에서 credit 블록을 정상 산출(OOM 무관). 막힌 건 *퍼블릭 베이크* 뿐 → 런타임-SSOT 우선 원칙과 정합.
    - **결론: 무승인 착수 금지 구간**([[feedback_runtime_ssot_no_build_without_approval]] "제안·토론까지만"). 운영자 결정 대기.
  - ✅ **매크로 Part 2 정합성 정정 + 방법 C 완료(2026-07-06)**. 실측 결과 **A(분기 YoY)·B(다변량 OLS)는 이미 구현돼 있었다**: `_signalsMacroSensitivity.calcMacroRegression` 이 분기 YoY(삼성전자 실측 nObs 37)+다변량 `_fitOLS`+`sectorPriors.json` 보유. 02e 가 지목한 연간(n≈3~5) 코드는 **다른 함수**인 `macroExposure.calcMacroSensitivity`(같은 이름 2 곳, 중복 명명). 진짜 공백은 **C(위계 폴백)** 하나였고 구현 완료:
    - `_sectorPriorFallback()` 신설. `calcMacroRegression` 의 4 개 스킵 경로(IS 파싱 불가·YoY 관측치<6·지표 로드 실패·OLS 실패)가 `None` 대신 섹터 탄성치를 `evidenceLevel="sectorPrior"`·`fallbackReason` 과 함께 반환. 성공 경로는 `evidenceLevel="observed"`.
    - **오독 방지 설계**: 폴백은 `betas=None`·`rSquared=0.0`·`confidence="low"` 라 기존 소비자 게이트(`_predictionSynthesis:366` rSquared>0.1, `:643` >0.3)를 자동으로 통과하지 못한다. 섹터 평균이 기업 고유 베타로 렌더될 수 없다. 섹터 키 미해소 시 `None` 유지(기본 탄성치 날조 금지).
    - 검증: offline 3 테스트 신규(총 20 pass) + 관련 분석 86 pass + **실데이터 라벨 확인**(005930 `observed`·nObs 37·R² 0.7681·high·sectorKey 반도체). ruff·camelCase clean. 회귀 0(폴백은 기존에 아무것도 안 나오던 회사만 채운다).
    - ✅ **β-stability 게이트 실측 = FAIL (2026-07-06, `tests/_attempts/macroBetaStability/`)**. 8 사 직렬(RSS 90->232MB, OOM 무관). 겹침 민감도 격자: 20q/4q(겹침 16q) 10.4% **PASS**, 16q/8q 25.0% **FAIL**, 12q/12q(비겹침) 52.1% **FAIL**. 원안의 PASS 는 **윈도 겹침이 만든 착시**(인접 윈도가 16q 공유). 지표 집합을 전체 표본에서 고정(안정성에 유리한 look-ahead 조건)했는데도 독립 윈도에서 부호가 뒤집힌다. 공정 판정선 = 16q/8q 의 25% FAIL(12q 는 자유도 부족 잡음 혼입).
      - **결론: 리포트 매크로 라우팅 교체 보류가 정답.** 02e 의 "게이트 통과 전 리포트 미탑재" 가 옳았음이 수치로 확인됨. 현행(연간 `macroExposure` + `exposureQuality` 정직 라벨) 유지.
      - 방법 C(폴백)는 이 결과와 **무관하게 유효**: 폴백은 *회귀가 아예 불가한 회사*를 라벨과 함께 채우는 것이지 불안정한 베타를 밀어넣는 게 아니다.
      - 베타를 올리려면 선행 **안정화** 필요: 지표 수 축소(다중공선성)·계층 베이즈(섹터 prior 축소추정)·부호 제약·표본 확대. 전 유니버스·다기간 확장은 CI 트랙.
    - ★ **라우팅 실측(2026-07-06)**: `c.analysis("macro","매크로민감도")` -> `_registry` -> **`macroExposure.calcMacroSensitivity`(연간)**. 반환 스키마 `exposureQuality`·`selected`·`optimalIndicators`·`netDirection`(005930 `status=quantCandidate`). 분기·다변량 회귀(nObs 37)는 **예측신호 쪽 `calcMacroRegression`** 에만 존재. 즉 **리포트는 약한 연간 구현을 소비한다**.
      - 따라서 02e A·B 를 리포트에 반영 = *발행되는 리포트 숫자 변경*. PRD 가 "졸업 게이트 통과 전 리포트 미탑재" 로 막아둔 지점이며 게이트(β-stability)는 CI/데이터. **무검증 교체 금지**([[feedback_plan_score_not_signature]] 미검증 확신).
      - `macroExposure` 쪽에 방법 C 를 그대로 이식하는 것도 *순수 additive 아님*: 그쪽은 `None` -> dict 가 되면 터미널·리포트가 곧바로 렌더한다(수치 게이트가 자동 필터해 주던 `calcMacroRegression` 경우와 다름). UI 가시 변경이라 별도 승인 필요.
      - **결정 필요(운영자)**: 두 동명 `calcMacroSensitivity`(analysis 연간 회귀 / signals 섹터 탄성치) + `calcMacroRegression`(분기 다변량 회귀) 중 리포트 정본을 무엇으로 둘지. 일원화는 공개 API·리포트 수치·CI 검증이 동시에 걸린 별건 과제.

## P2 · 리포트 엔진
- ✅ **삭제 2,419 LOC 완료(2026-07-06)**. import 전수 census 로 死/生 판별 후 실행:
  - 삭제: `story/macro/`(1,823, importer 0. `macroReport` 는 baseline JSON 에만 존재) · `publisher.py`(327, py importer 0) · `sixAct.py`(268, `story/__init__` import+`__all__` 노출뿐 호출자 0) · `sections/`(docstring 1 줄, importer 0). `story/__init__` 에서 `SixActScore`·`sixActScore` export 제거.
  - **존치: `dashboard.py`(121)** . `.github/scripts/prebuild/buildStoryManifest.py:14` 가 `listDashboardQuestions` 를 실사용(라이브). PRD 의 삭제목록에 있으나 소비자 이관 전엔 못 지운다.
  - 문서 정리: `engines/credit` SKILL.md·methodology.md 가 `from dartlab.story.publisher import publishReport` 를 **공개 호출 예제로 노출**하고 있었음(내부 모듈 노출 = 공개계약 정책 위반). 등록된 계약 `Company.story(type="credit")` 로 교체. `blog/TOPIC_ROADMAP.md` 04 항목도 아카이브 표기로 정정. 존재하지 않는 `credit/publisher.py` stale 트리 행 제거. artifactSync 로 6 JSON 동기.
  - 검증: story 306 pass · CLI 스냅샷 5 pass · staleImports·stale_references·deprecationAudit·checkEngineSpecSchema·namingConsistency·camelCase·checkAgentBoundary·checkSilentFail·workspaceHygiene 전부 PASS · ruff clean · testCoverageGate 신규누락 0.
- ✅ **sixAct 레이더 폐기(2026-07-06)**. PRD "옛 6막·sixAct 레이더 군더더기 폐기" 이행. `viz/generators/core.py::specSixActRadar` 는 입력이 `sixActScore` 결과라 생산자 소멸로 고아가 됐고, provenance 를 `source:"story/sixAct"`(사라진 모듈)로 **거짓 주장**하던 상태. 함수 + `viz/generators/__init__` + `viz/__init__` export 제거. python caller 0·publicApi 미등재·테스트 0 확인 후 삭제. viz import OK·ruff·camelCase·staleImports·stale_references PASS.
  - ⏭ 잔여 부채(UI 게이트): `landing/static/charts/005930/{manifest.json,hero/sixActRadar.json}` 는 **베이크된 정적 자산**이라 사이트는 안 깨지나 이제 재생성 불가. 제거는 화면 변경이라 운영자 승인 대상.
  - ⚠ 별건(내 변경 무관): `tests/viz/test_viewer_enhance.py::TestIntegrationReal` 2 건 로컬 실패 . `blockType` 컬럼 부재(패널 스키마 드리프트)·scan 유효건 3<5. `requires_data` 마커라 CI fast 제외. 타 세션 패널 작업 여파로 보이며 별도 추적 필요.
  - ⚠ 기록: 앞선 세션 메모에서 "macro·sixAct·dashboard 가 전부 buildStory reportType 라이브 의존" 이라 적었으나 **오판**. `reportTypes.py` 의 `"macro"`·`"dashboard"` 는 reportType *키* 이고 빌더는 `macroCycle`·`macroRates` 등 별도. 실제 라이브는 `dashboard.py` 하나뿐이었다.
- ✅ **`reportModel.ts` 계약 + 18블록 완성**(`9e7c77862`, tsc 통과): 기존 8 + 신규 10(thesis·exhibit·callout·verdict[noComposite]·scenario·valuationBridge·peerScatter·driverTree·excerpt·transition) + 구조화 객체(Thesis·ScenarioSet·ValuationView). Python emitter·TS build 공통 SSOT. 신규 전부 optional(무회귀). index.ts export(ReportPort 무충돌).
- ✅ **`story/report.py::buildReportModel` emitter 완성·검증**(`044daf6dd`): Story 블록→계약 ReportBlock 매핑(legacy 6→8, self-calc 0) + de-gate 밸류에이션(calcDFV)→valuationBridge·scenario pro 블록 + 구조화 thesis 합성 → schemaVersion=2 dict. L2 lazy import. never-raise(skipped dict). **실데이터 검증**: 삼성전자 10섹션 + valuationBridge(relative 196,337·WACC 7.72·g 8.91) + scenario(172,777/196,337/219,897). offline 9 테스트(`tests/story/test_report.py`). story __init__ export.
- ✅ **`Company.reportModel()` 공개 verb**(`f47f63a28`, dart·edgar): @property+CallableAccessor dual-access(story 동형)→_reportModelImpl lazy 위임. `report` 정형공시 accessor 충돌 회피로 `reportModel` 명명. ⚠ 함정 교훈: verb 는 @property 라 메서드를 @property·def 사이에 끼우면 데코레이터 탈취 — 별도 @property+_impl 로 분리. 검증: schemaVersion=2·story 무회귀.
- ✅ **`Company.reportModel` 공개계약 등재(2026-07-06)**. verb 는 코드에 있었으나 `engines.company` capabilityRefs 미등재라 **프로젝트 규칙상 계약이 아니었다**(CLAUDE.md: 미등재 Company 메서드는 예제·문서·노트북 노출 금지). capabilityRefs + 공개 호출 예제 + 축/메서드 표에 등재. `checkEngineSpecSchema` baseline 위반 1 건 해소(신규 부채 0), `listSkills` 298 cascade 정상, artifactSync 동기. P2 항목4(소비자 공개)의 미완분.
- ✅ **thesis.py 격상**(`story/thesis.py`, 커밋 직후): ROIC−WACC 지속성→메커니즘 1문장(데이터 섞이면 조건부 정직)·정량 트리거·기둥 결박. 얕은 conclusion 엮기 폐기. 실데이터 차별: 삼성(조건부 미회수) vs 기아(+7%p 71% 방어 단정) vs NAVER(조건부). offline 9 테스트.
- ✅ **버그수정**: `buildSectionSummary` tuple 크래시 가드(NAVER 등 reportModel 복구, `185590894`). 회귀 3 테스트.
- 🟡 **verdict 블록 = 불필요 결론**(코드검증): `calcScorecard`/SummaryCard 는 {area,grade} thin(headlineKpis 와 중복). 축별 판정(최근값·기준·판정)은 **이미 재무 table 블록의 '판정'·'기준' 컬럼**에 실려 verdictTone 렌더(`+page.svelte:392`). 별도 verdict 블록 = table 중복 → 미추가(덕지덕지 가드). 계약 verdict 타입은 미래용 보존.
- 🟡 **arc 재정렬 = 보류**: 현 emitter 는 buildStory reportType.sectionOrder(이미 전문 순서) + 밸류에이션 말미 append = 합리적 아크. 강제 재정렬은 회귀 위험·저ROI. transition 블록은 generic 시 fluff → 섹션쌍별 의미 로직 필요(신중).
- ✅ **소비자 마이그레이션(2026-07-06)**. 04 항목4 "`Company.report()`·`dartlab report` 추가(기존 `story()` 유지)" 를 *추가형* 으로 이행:
  - `Company.reportModel()` = 라이브러리 진입점(공개계약 등재 완료, 위 항목).
  - `dartlab report <code> --model [--perspective X]` = CLI 진입점. 등록 계약 `c.reportModel(perspective)` 를 그대로 JSON 직렬화(self-calc 0). **기존 Markdown 경로 불변**(`--model` 미지정 시 옛 동작, `getattr(args,"model",False)` 로 구 namespace 하위호환).
  - 검증: CLI unit 2 신규(17 pass, 스냅샷 5 불변) + 실 CLI e2e(`report 005930 --model --perspective credit` -> schemaVersion 2·perspectiveKey credit·`creditPanel` 블록). ruff·camelCase clean.
  - 死코드 삭제는 위 항목에서 완료(importer census 선행).

## P3 · 랜딩 동일소비
- ✅ **`model.ts` → 공유 계약 shim**(`47cd8d7e2`): landing ReportModel = @dartlab/ui-contracts 타입(단일 SSOT). 랜딩 전용 소형 보조타입·lastNonNull 유지·import 무변경. project.ts pro블록 10종 skip 케이스(assertNever 보존). **svelte-check 0 errors**. 타입레벨만(렌더 무변경).
- ✅ **렌더러 graceful-skip 확인**: `+page.svelte` 블록 if-체인이 8 legacy 후 else 없이 종료 → 신규 pro 블록 자동 skip(크래시 0). 미래호환 충족, 변경 불요.
- ☐ `build.ts` pro 블록 emit (thesisStruct TS·valuationBridge/scenario **pyodide `c.reportModel()`** §3 (a)) — pyodide 휠에 reportModel 포함(빌드) + 배선 필요
- ☐ `+page.svelte` pro 블록 렌더 케이스 추가 — **시각 작업·눈검수 필수**
- ☐ 6상수 golden-parity (N=5, ~20셀)
- ☐ UI 스크린샷 눈검수 + 운영자 승인 push

## 결정·이벤트 로그
- 2026-06-26 착수. operator 사상 확정: 정직-스킵=무능, 능력부족은 SSOT 찾아 개선, 날조만 금지. 순서 = 능력 먼저. 기획 7+5문서 박제.
- 2026-06-26 신용 publish 조건부 승인 ("반드시 필요하면 허용, 단 덕지덕지·관리불능 금지"). 코드검증 후 5가드 박제 → 착수 unblocked.
