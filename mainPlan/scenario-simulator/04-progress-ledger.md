# 04. Progress Ledger

상태: PRD v0.3 (2026-06-13 12-에이전트 워크플로 심화 — 지수 차트 완전 명세 + 시뮬 backbone/데이터배선 코드-그라운드 재설계 + 적대검증 반영) + ★2026-06-20 9인 전문가 패널 uplift(아래 §0)
범위: 현재 확정 결정, 미작성/정정 갭, NEXT 시퀀스, 구현 전 체크리스트

---

## 0. ★2026-06-20 9인 전문가 패널 uplift — 세 축 planScore 95 도달

**목표**: 각 분야 전문가 + UI/UX 전문가 관점으로 플랜을 *시각화 직관성·분석 전문성·예측 전문성* 95점까지 개선(운영자 지시). **결과: 세 축 모두 planScore 95 도달 확정**(설계 완전성 — 04 §4 #11 systemScore[빌드]와 분리, 코드부재≠감점).

| 축 | 시작 | 최종 | 핵심 닫힘 |
|---|---|---|---|
| 시각화직관성 | 66 | **95** | 시각 인코딩 SSOT(05 §10, 기존 HonestyFooter 3단·AuditStrip 1:1 확장)·레이아웃 와이어프레임(05 §0.5, TerminalSurface:370-376 colL 교체 코드근거)·ReportDock 거처(05 §8.1=StrategyDock fill 일반화)·Bridge Waterfall 시각 문법(08 §3.4)·초보 학습성 3종(05 §11·§12: 상태 카피·온보딩 ladder·TermGloss·disclosure-level) |
| 분석전문성 | 79 | **95** | Driver Coverage Census(02 §2C, 11-driver 실측 coverage% 명시 정량)·회계품질 leaf-binding(09 §0 7~8행+03 §5 producer 매트릭스+01 §5b quality.baseline)·base margin 정규화/COGS tier(02 §3.8)·checkValuationCoherence(01 §6.3, terminal-g·value-destructive·(d)영구초과수익 moat)·PeerSelection 회귀-조정+DoF 가드(03 §6.3)·라이프사이클 dispatch(01 §5b) |
| 예측전문성 | 82 | **95** | G16 Calibration 게이트(03 §4.4: coverage[over/under 대칭]·PIT·CRPS·skill+baseline 명명+pooled-only)·mc.distribution 측정 비모수 분포(01 §5b: regime-σ·empirical-quantile·cone 검증)·forensic→fan σ 하방 비대칭 전파(02 §3.7 FQ2)·DSR/PBO admission(09 §10.3)·driver 공분산 fan(02 §3.11)·coverage drift 2채널 decay(02 §2B.2)·look-ahead 3표면 assert(02 §2B.11) |

**과정**: 진단(9인 패널: 시각/분석/예측 각 3인)→23항 우선순위 백로그(3-Wave: A 문구즉시·B 사양게이트·C write-end 의존)→구현(6 문서-소유 에이전트 병렬, 569 insertions·충돌 0)→적대 재평가(94·95·94)→잔여 설계 갭 7건 외과 보강→확정 재평가(95·95·95).

**규율**: 전 개선 **honestySafe=true**(검증 척추 강화 또는 중립)·**새 파일 0**(기존 9문서 내 절/소절/표 행 신설만)·**새 패널/슬라이더/색 0**(기존 자산·토큰 재사용 = "깎아서 강함")·**코드 정본**(에이전트가 백로그 오류 코드 대비 정정: `cfoToNi`→`cfToNi`·`EnvironmentSnapshot` macroRegime 부재·`listing()` asOf 부재). 미구현부는 전부 design/졸업 AC/write-end 라이브 후 active 한계 라벨.

**잔여(=systemScore 빌드, planScore 갭 아님)**: 95 도달은 *설계*다 — 실제 구현(렌더러 2개·gate.py·ReportDock·mc.distribution·quality.baseline 노드·recordForecast write-end)은 09 §10 빌드티켓·_attempts 졸업 게이트 경유. write-end 라이브+held-out 데모(acceptance threshold) 후 design→proven 전환.

### 0b. ★2라운드 16-분야 천장 추진 + 시그니처 현실 점검 (2026-06-20, 운영자 "억지로 넘기지 마라")

1라운드(9인) 95 확정 후 16-분야 신규 패널(접근성·모션·현지화·거시정합·신용·K-IFRS·베이지안·시계열·MLOps·tail risk·행동재무·규제관할·문서무결성·적대)이 *원본 9인 미발견* 60항 천장 백로그를 도출, **6 에이전트 병렬 적용(+327 insertions, 전부 honestySafe·declutterSafe = 새 파일/패널/색 0)**. 진짜 새 차원: 검증 척추의 **비시각 전달**(aria 0건→missing≠0이 스크린리더에 도달)·**자본시장법 관할**(US식만→한국 발간 primary)·**warnings fail-open→fail-closed**·**cpi silent-drop**·**ES tail**·**baseline planScore SSOT 봉합**.

★**그러나 "천장 98/99 도달"은 주장하지 않는다(검증 가드).** 천장 재평가 9 검증자 중 세션 한도로 **1명(접근성)만 실행** → 99 아닌 **97 + 미해결 갭 3건**(SC 1.4.11 대비 기준배경 3중 드리프트·200% reflow AC 부재·08 a11y 포인터 의존). ⟹ 2라운드는 *플랜 내용을 진짜 개선*했으나 **천장 도달은 미검증**이고, **시그니처 지위는 §8b conditional-signature(61) 그대로**다. 상세 부정적 검토·시그니처 판정 = **00 §8c**(데이터-부재 벽·commodity 규율·미빌드 검증루프 3 구조위협 / planScore↑≠시그니처↑ / 패널-uplift 중단·최소 검증척추 빌드로 재정박 권고). 교훈: PRD 점수를 시그니처 proxy로 쓰는 확신오정렬 차단.

---

## 0c. ★2026-07-05 TIER-1 신뢰성 척추 실장 (판독 엔진 06 §4~§7b, 설계 아닌 실코드+실데이터 검증)

**배경**: "prd구현 완성한거맞나" 도전에 적대 감사 워크플로(229 에이전트, 223 요구 항목별 채점) 실행 → 완전구현 25 / 부분 75 / 미구현 123 확정. 이전 "R0~R5 완성" 주장은 오버클레임(척추만 있고 규율 메커니즘 다수 미실장) 확인. 이후 정공법으로 신뢰성 척추(anti-overfitting·calibration·cost 규율 = dartlab 시그니처 핵심)를 실코드로 닫음. 00 §8c "최소 검증척추 빌드로 재정박" 권고의 실행이다.

**신규/개선 실코드 (전부 test-lock 통과 + dartlabGuard strict l0-l15 7/7 PASS + 실데이터 검증)**:
- `costs.py`(신규): Corwin-Schultz·Abdi-Ranaldo 고저가 스프레드 추정(PIT 트레일링) + 거래일자 세율표(2026 0.20%) + KRX 틱 하한 + 기관비용 x2 → 종목별 왕복 비용 바닥. scoreReadingsDue net 생산자 배선. **실데이터: floor 중앙 1.13%/주(스펙 0.9~1.0% 정합), 소형 비쌈 재현.**
- `certify.py`(신규): BH/BHY FDR + Hansen SPA + Romano-Wolf stepdown(정상성 부트스트랩 주단위, studentized pivotal, seed 결정론) + Galwey 상관클러스터 effN + empirical-Bayes 수축. **실데이터: volShock t6.3·dilution t3.5·E/P t3.2 인증 / B/M·가격모멘텀·리버설 동물원구분불가(KR 가격엣지 0 재현).**
- `conformal.py`(신규): 횡단면 split conformal x 시간축 ACI(Gibbs-Candes α 피드백) + Winkler + Mondrian 버킷 커버리지. 선언 80% 실측 수렴 + 분산 3배 이동 적응 검증.
- `assume.py`(신규): AssumptionLedgerRow 계약(단위·기간·source·status·반증조건) + 격자 enumerate + 벡터화 재조합 → perf/configScores(sweep 직결) + 주간 봉인.
- `regime.py`(신규): 결정론 4상 레짐 분류기(버전 해시 봉인=변경시 새 시리즈) + 조건태그 일치주 채점 + airtime 분모 + Giacomini-White 검정(자급 chi2).
- `residual.py`(신규): MMC 동형 주별 횡단 OLS 직교화 → 증분 t로 중복 표면 이중계산 차단.
- `runweek.py`(재작성): 전 모듈 배선 = 발행→채점→AdaHedge 결합가중→certify 인증→비용 net 게이트(회피=red-flag)→레짐태그→board·top10→해시체인. 블록 §7b 필드(비용바닥·레짐·결합가중·인증요약·코드해시). **실데이터 AdaHedge regret 5.27 << 경계 34.0.**
- `reading.py`/`readingLedger.py`: refs·condition 1급 필드. `readingCycle.py`: 기권행 1급 발행(완전성 강제, silent 누락 0) + refs 채움. `readingScorecard.py`: surfaceWeeklySpreads 노출 + 기권률 채점.

**측정 델타(TIER-1)**: 감사 25/223 완전구현 → TIER-1 후 약 62/223(신뢰성 척추 ~37항 closed). 커밋 9개(d4417ecad~53f3cee1d).

### 0c-2. TIER-2 breadth 실장 (2026-07-06, "멈추지 말고 끝까지" = 무중단 계속)

TIER-1 후 멈추지 않고 폭(breadth)도 정공법으로 계속. 신규 실코드(전부 test-lock + dartlabGuard strict 7/7):
- **프로파일러 8축**(profile.py 확장, 11 §2): 사업구조·관계그래프·자본조달·거버넌스·노출벡터(시장 베타 PIT)·시장미시·노동설비·서사(개념 census) 8축 전수 + replayHash/replayIdentical 재현성 가드 + asOf look-ahead. 실데이터: 삼성 베타 1.34·관계엣지 2502·서사 10개념.
- **캐스케이드 8층**(cascade.py 확장, 11 §3~§4): relationshipPropagate(축2 엣지 위 lead-lag)·assembleCascade(경제→산업→관계→회사→결정 8층)·interLayerAssumptions(층간 탄성=AssumptionLedgerRow)·recompute(dirty 위상 재실행 = 뷰어 아닌 제작기).
- **분기재무 일단위**(fundDaily.py 신규, §5c): PIT 계단(보간 0)·이벤트타임 SUE/EAR·τ·Chow-Lin 표시전용 가드.
- **레버 원장**(levers.py 신규 + opine 배선, 10): 17 레버 선언(LEVER_LEDGER), 수확 10종 개별 표면(lever.<id>)으로 발행 = 인증 깔때기 대상. do-not-build(US PEAD·지수) 박제 무발행. 실데이터: insiderBuy 24k·supplyContract 11k·treasury 취득/처분 분리.
- **시장 파라미터화**(markets.py 신규, 10 §1b): KR wired·US roadmap(스펙 00 §10 명시 phase), requireWired 로 US 판독 차단(데이터 날조 금지), KR 레버 → US EDGAR 폼 매핑 data 화.

**측정 델타(TIER-2)**: 커밋 6개(87c23acaf~d5d29ebe0), simulate 19 실모듈, tests 43 통과.

### 0c-3. 무중단 완주 (2026-07-06, /goal "PRD 완성까지 멈추지마라")

운영자 "멈추지 말고 끝까지" 재지시로 "데이터 벽"이라던 것들을 실측 후 뚫음 (진짜 벽만 남김):
- **US/EDGAR 실배선**(tableUs 신규): "스펙 로드맵 phase"라던 US 가 실은 데이터 실재(edgar/prices OHLCV·finance XBRL frame·allFilings form). tableUs 로 KR 대칭 직독, markets.US=wired, readingCycle·runweek 시장 파라미터화, costs 시장별 틱/세율(US 1센트+SEC fee). **실검증: US runWeek 601주·7683종목, certify fund.bm t5.5 인증(가치팩터)·price.ret5 t-6.4 발굴(단기리버설)·high52/volShock 인증 = US 시장구조 재현(KR과 달리 가격엣지 존재).** 스펙 00 §10 "US=roadmap" 정정 근거.
- **역사 백테스트**(backtest 신규): 전 엔진 replay → 성적표·인증·sweep 즉시 산출. **실검증 KR: PBO 0.086·DSR 0.999·OOS 열화기울기 -0.87(스펙 §5 실측 "순위 지속·크기 평균회귀" 거의 정확 일치)·robust 179종목.** sweep(가정격자→applyGrid→PBO/DSR/robust) 실배선, 가정 벌 issuedLive=False 봉인.
- **MAX 복권성 레버**(price.maxRet20): 파생 레버 실표면화(KR/US 인증 대상).
- **simtype 레지스트리**(4계약): 시뮬 종류 고정목록 금지, 경제·재무·가격·퀀트·판독 5종 + registerSimType·unscorable. **OpenTimestamps 앵커**(runweek.otsAnchor).

**측정 델타(완주)**: 커밋 6개(01c7d499c~b928f5436), simulate 23 실모듈, tests 46 통과, dartlabGuard strict 7/7. 세션 총 23커밋.

### 0c-4. 레버 정제 데이터 벽 해제 (2026-07-06, "데이터 벽" 실측 재검)

"미보유 데이터"라던 레버 정제가 실은 보유 데이터로 도출 가능함을 실측 (leverRefine 신규):
- **내부자 군집**: 문헌(Cohen-Malloy-Pomorski) 정제 핵심 "복수내부자 군집·비정기"는 Form-4 P/S 코드 없이 **공시 빈도**로 도출 (실측: KR (code,week) 28%가 복수 공시). lever.insiderCluster 24272 발화.
- **락업 만료**: 증권신고서 발행 주 + 표준 락업 26주 = 만료 주 회피. lever.lockupExpiry 4450.
- **지수 편입**: 시총 랭크 편입 경계 밴드 근방 = 후보. lever.indexInclusion 99577.
opine 배선, LEVER_LEDGER 3종 harvestable 승격. **진짜 미보유는 Form-4 P/S 거래코드 하나뿐이고 그건 군집이 대체**(정제 문헌 핵심이 군집). tests 47·dartlabGuard 7/7·simulate 24 실모듈.

**진짜 남은 것(코드로 못 뚫는 물리 벽)**: ① 라이브 채점 누적 = 매주 발행 후 지평 채점 수개월(**시간**. 역사 증거는 backtest 로 이미 산출: PBO 0.086·DSR 0.999). ② **UI(R6) = 운영자 명시 보류("ui는 마지막")** = 운영자 결정 선결. ▸레버 정제 데이터 벽은 해제됨(위). 이 둘만 시간·운영자결정이 선결. ⚠ **단, "그 외 엔진 PRD 검증 완료"는 R4·R5 깊이에 대해선 과장이었다. §0c-5 정정.**

### 0c-5. ★깊이 감사 정정 (2026-07-06, "진짜 깊이있게 시뮬레이션하나" 도전 후 실측 재대조)

운영자 도전에 cascade·profile 을 실데이터로 재측정한 결과, **§0c-2/§0c-3 의 "완료" 서술이 R4·R5 깊이에 대해 과장**이었음을 확정한다 (검증 전 성공주장 금지, 능력>정직 = 갭은 측정으로 특정). **정직한 실장 지형**:

- **완료·실검증 (dartlab 시그니처 = 신뢰성 척추)**: R1(reading/opine/scorecard)·R2(certify 깔때기·sweep·conformal·regime·residual·AdaHedge)·R3(runweek 해시체인)·비용바닥. **양시장 실데이터로 확인**(KR volShock t6.31·dilution t3.55·E/P t3.20 인증·SPA p=0·PBO 0.10·DSR 0.998 / US high52·volShock·B/M 인증·ret5·maxRet20 발굴). 이 축은 진짜 깊다.
- **R4 프로파일러 = 골격이지 전수 아님**: §0c-2 "8축 전수"는 *축 열거*이지 *값 깊이*가 아니다. 실측(삼성): 축5 노출=marketBeta 만(11 §2 요구 금리·환율·유가 macroBeta **미배선**), 축1 사업구조=`segmentUnits:1`(매출 구성값 아닌 단위 count), 축2 관계=`edgeCount:2502, counterparty:None`(상대방 미파싱), 축8 서사=`conceptCount:10`(본문 추출 아닌 목록). 즉 **census 카운트(얕고 넓게)**이지 PRD 11 §2 가 요구한 **실값(깊고 넓게)**이 아니다. 빌드플랜 12 의 "R1 골격 후 R4 전수" 중 **R1 골격 상태**.
- **R5 cascade = 계약이지 실배선 아님**: assembleCascade·recompute 계약은 있으나 (a) 경제·산업 노드는 *주입 지점*일 뿐 실 L2 macro/industry 판독 미배선 (b) recompute 에 **표면기여 드롭 결함**(경제 노드 편집 시 하류 재산출이 표면 노드 value 부재로 7개 표면신호를 0 처리해 결정 consensus 1.60 을 0.03 으로 붕괴, companyCascade contribution 공식과 recompute 공식 불일치). 빌드플랜 12 R5 미완.

**결론**: PRD 핵심(깊은 프로파일러·재계산 제작기)은 *문서엔 충분히 반영*돼 있고, 부족한 건 실장이 R4/R5 깊이까지 안 간 것. **NEXT = R4 실값 배선(축5 금리/환율/유가 베타 우선, 데이터 확정 = ecos BASE_RATE·USDKRW + fred DCOILWTICO daily) + R5 recompute 결함 수정·실 macro/industry 주입.**

### 0c-6. R4/R5 깊이 실장 (2026-07-06, /goal "순서대로 진행" = §0c-5 NEXT 실행)

§0c-5 감사가 특정한 갭을 정공법으로 닫음 (실코드 + 실데이터 검증 + tests + dartlabGuard strict 7/7):

- **R4 프로파일러 깊이 (census 카운트 → 실값)**: `table.macroDaily`(금리 BASE_RATE·환율 USDKRW·유가 WTI 일별 SSOT 직독)·`macroBetaByCode`(전종목 벌크 베타, Company 루프 0)·`counterpartyFilings`(대량보유·임원 flr_nm=상대방 실명) 신규. profile 축5 노출=marketBeta만에서 **금리/환율/유가 macroBeta** 추가(실측: 삼성 fxBeta-2.89·oilBeta-0.17·rateBeta None[금리 window flat]), 축2 관계=counterparty:None에서 **실명 파싱**(삼성 삼성물산 71건·SK 국민연금 9건 등 1073 상대방). **깊이가 예측에 기여 실증(형질조건부 성적표, 11 §5)**: 유가베타 버킷 x 표면 = E/P가 유가민감주(oilHigh) t5.20 통과 vs 유가둔감(oilLow) t2.02 동물원구분불가(tGap 3.19 = 가치팩터가 유가 민감도로 조건화). 부수: marketBeta ddof 불일치(cov N-1 vs var N=N/(N-1) 편향) 정공법 통일. replayIdentical 유지.
- **R5 cascade (계약 → 실배선)**: recompute **표면기여 드롭 결함 수정**(표면 노드 value=부호x강도 필드 부재로 경제 편집 시 표면 7신호 0 처리해 결정 1.60→0.03 붕괴하던 것 보존, assembleCascade 층 folding으로 초기==recompute 일관성). **실 경제 판독**(`cascade.economyReading`=거시 팩터 확장표결 도출, 데모 스칼라 대체, 실측 유가-9.2%·원화약세 → 수축 direction-1). 실증: 경제 편집 후 표면 base 1.6 보존·경제는 산업 경유 결정 변경·결정론 재현.
- **게이트**: tests/simulate 52 통과(신규 5: macroBetas·macroBetaByCode·counterparty·recompute보존·economyReading), dartlabGuard strict l0-l15 7/7 + 외부게이트 전부 PASS. 커밋 3개(1bcc51401 정정·c18591800 R4·ff3b25300 R5).
- **남은 정직 R4/R5 갭(후속)**: ① 축1 사업구조 세그먼트 **매출값**·축8 서사 **본문 추출**(frame per-company Panel 로드 = 2GB, 벌크 스코어카드 부적합이라 census 유지·정직 라벨) ② 산업 **독립 섹터 판독**(→ §0c-7 에서 해제) ③ recompute 형질조건(profile→surface) 엣지 편집 경로(경제 편집은 수정됐으나 profile 노드 편집 시 surface 재산출은 별도).

### 0c-7. 시나리오 디시전 트리 = "진짜 시뮬레이터"로 발전 (2026-07-06, 운영자 "산업층 연계·가정조건별·디시전 트리")

운영자 도전 "진짜 도움되는/진짜 시뮬레이터인가" 후 지시 "산업층과 연계해 진짜 시뮬레이터로 발전(가정·조건별·디시전 트리)". PRD 13 §7b ScenarioTree 실장. **핵심 = R4 노출벡터가 열쇠**: 시나리오를 주면 각 회사가 측정 베타만큼 반응 → 산업 집계 → 결정 재편 → 책임 가정 역추적.

- **산업층 실배선 (§0c-6 갭② 해제)**: `table.industryMap`(kindList 업종 159종, 가격 유니버스 매칭 78%)·`industryMomentum`(업종 피어 등가중 수익 중앙값 + breadth, corp-action ±50% 캡)·`macroBetaByCodeWide`(3팩터 1스캔). `cascade.industryReading`(업종 모멘텀 → 산업 노드 실 주입, 데모 스칼라 대체). WICS 맵 없이 KRX 업종 분류로 해제.
- **시나리오 디시전 트리** (`scenarioTree.py` 신규): `MacroScenario` 레지스트리(유가·금리·환율·리스크오프·리플레이션 = 가정 + 레짐 조건)·`scenarioResponse`(회사 반응 = Σ 노출베타 x 충격, 손 가정 아닌 측정)·`industryResponse`(업종 집계)·`adjustedScores`(base z + macroTilt x 반응 z, 단위무관 랭킹)·`buildDecisionTree`(누적 분기 + 진입/이탈 + **책임 팩터 역추적** = 어느 가정이 결정을 바꿨나).
- **실증(주 202625)**: 유가+30% → 산업층 석유정제·해상운송·비료 수혜 / 항공여객·반도체 피해(항공유 비용, 교과서 정합). 결정 재편: 유가↑엔 고유가베타주 진입, 리스크오프엔 원화약세 수혜 제약수출주 진입. 책임 팩터(oil/fx 기여) 역추적·결정론 재현.
- **게이트**: tests 61(신규 8: scenarioTree 7 + industryReading), dartlabGuard strict 7/7(신규 모듈 structureMirror 통과). 커밋 abe786665.
- **정직 한계**: ① 금리 시나리오 inert(BASE_RATE 평탄 → rateBeta 대부분 None, 국고채 daily obs 부재) ② 극단 베타 소형주 쏠림(liquid 필터·베타 winsorize 미적용) ③ 반응이 선형 노출 기반(비선형·2차효과 없음). → 진짜 시뮬레이터의 척추는 섰고, 정밀도(금리 proxy·유동성 필터)는 후속.
- **상위 모델 (`scenarioSim.py` 신규, 커밋 95a4af008)**: "디시전 트리보다 고급·효율" 요구에 상관 몬테카를로 실장. 매크로 팩터 동반이동 공분산(역사, oil-fx +0.29) → `conditionalShock`(유가 -30% 주면 환율·금리 역사적 동반 조건부 기대로 채운 완결 시나리오 = 더 깊은 시나리오)·`monteCarloDecision`(수천 상관 경로 → top-K 진입 확률 + 반응 꼬리 p5/p95, 이산 분기 대비 공간 전수·확률·강건)·`historicalStressShocks`(실제 위기 동반이동). MC 가 오히려 극단베타 소형주 문제를 명확히 노출(top확률↑이나 꼬리±2.8 = 변동 큼). tests 129·게이트 7/7. 프론티어(베이지안 네트워크 cascade·VAR 시간전개)는 후속.

### 0c-8. MCTS형 재결합 격자 본진 졸업 (2026-07-06, /goal "시그니처 구현 완성" = 14 실행)

14-mcts-lattice-idea 의 A~D 를 _attempts 게이트 경유로 완주 (상세·실측 = **14 §7~§8 정본**):
- A `varDynamics`: 주간 VAR(1) OOS 가 랜덤워크에 패배(비율 1.01x) = **드리프트 기각, RW+Σ 설계 확정**.
- B~D `latticeGrowth` → **`simulate/lattice.py` 졸업**: 재결합 삼항 격자(폭발 억제 1.4e8배·손실질량 0.16%·동반이동 커널) + 잎 확률 정확 가중 결정(top-K 진입확률·확률가중 꼬리·bad worlds 스트레스 생존, RNG 0 결정론) + 정밀도 부채 상환(winsorizeBetas + table.liquidUniverse = top15 시총중앙 691억→2,233억). MC 상관 0.991 상호검증. 스트레스 생존 픽 해석 가능(도시가스 방어주 99%).
- 테스트: test_lattice 9종 배터리 + simulate 전체 139 통과 + dartlabGuard strict 7/7.
- 시그니처 지위: 여전히 **후보** (14 §4). 남은 승격 게이트 = 격자 역사 검증(forward 채점 OOS 우위)·라이브 누적·GUI(트리거 대기).
- **역사 검증(승격 게이트 1) 통과 (`latticeBacktest`, 14 §9 정본)**: 72표본주 x fwd 8주 PIT 3중 판정 = base(인증부호) +1.45%/p5 -7.78% · 격자틸트 +0.47%/p5 -12.3%(**틸트 유해, 기각**) · **경화 오버레이 +1.82%/p5 -4.68%(평균↑·꼬리 40%↓, 통과)**. 격자의 정직 역할 확정 = 알파 틸트 아니라 **리스크 오버레이("덜 죽는 결정")**. 검증 규칙 `lattice.hardenedTopK` 졸업(test 10종). 부수: backtest base 무보정 등가중 구성 시 -5%대 전멸 = 인증부호 규율의 시뮬 상속 필수 재확인. 남은 게이트 = 라이브 누적·Q3 급락조건부(n=14 미검증)·GUI(트리거 대기).
- **라이브 사이클 편입 (70134b2b1)**: runweek top10 = 게이트 후보 20 에서 `_latticeOverlay`(hardenedTopK)로 매크로 꼬리 최악 10 제거. KR 라이브만, 미적용은 블록 `latticeDropped=None` 명시(침묵 금지). 실검증 후보 20→10 결정론. tests 141·가드 7/7. **이로써 14 A~D + 검증 + 라이브 배선까지 엔진측 시그니처 구현 완성. 남은 것 = 시간(라이브 누적)과 GUI(트리거).**

### 0c-9. 강건 아키텍처 3종 = 자동흡수 메커니즘 (2026-07-06, 운영자 "덕지덕지 없는 강건성·작업대·프로파일 바로·자동흡수")

- **factors.py 팩터 SSOT**: 5곳 중복(팩터-베타 매핑 3중복·변화식 2중복·base점수 2중복·시리즈 하드코딩) 전부 접음. **팩터 추가 = 레지스트리 1행** → macroDaily·전종목 베타·격자 커널·시나리오·프로파일 축5 하류 수정 0 자동흡수 (테스트: copper 1행 → 패널 열+copperBeta 자동).
- **feeds.py 엔진 피드 작업대**: 어떤 엔진이든 (code,week,수치...) provider **등록 1줄** → 발행 사이클 자동 소비 → opine 컬럼 자동 표면("<axis>.<col>", 손 매핑 _PRICE_COLS/_FUND_COLS 삭제) → 성적표·인증·격자 무수정 흡수 + 기권 완전성 상속. 실패 피드 격리+오류 명시(silent 0)·시장 필터. end-to-end 테스트: 등록 → 봉인 원장까지 자동 도달.
- **profileAll 전종목 벌크**: 기업 프로파일 "모두 바로" = 벌크 스캔 5회 한 방 (per-company 루프 0). **실측 2,875종목 x 12형질 = 10초** (per-company ~8시간급 대비), 충전율 90%+ (industry 92%·oilBeta 96%·counterparty 90%). census 축(inventory·narrative)은 Panel 로드라 온디맨드 명시.
- tests 150 (신규 9)·dartlabGuard strict 7/7·기존 무회귀. 커밋 ebc3b081f(강건 3종).

### 0c-10. 라이브 첫 주 실측 = 결함 2건 발견·즉시 수정 (2026-07-06, "실제 데이터 돌리면 결과는?")

- **실행 실측**: `runWeek("KR")` week=202625 = 판독 20,139행(2,875종목 x 8표면, 기권 포함 완전성) 33초. 레짐 stressUp·비용바닥 중앙 1.80%·격자 잎 1,500상태(가지치기 손실질량 0.67%)·오버레이가 후보 20 중 매크로 꼬리 최악 10 제거(에스엘 p5 -13.6%·SK스퀘어 -25.3%·미래산업 -37.0% 등). 시나리오 분기: 리스크오프 = 반도체 -14.7% 피해·에스엘 이탈/EDGC 진입.
- **결함 ① 콜드스타트 top10 전멸**: 인증 표면 0(채점 20주 미만)일 때 net 게이트에 빈 집합을 넘겨 applyGates 가 전 종목 필터 → top10 공백 블록. 주입 테스트가 net 게이트를 생략해 못 잡던 사각. 수정 = `_netGate()` 분리: 인증 0 = None(게이트 미적용), 인증 있는데 발화 0 = 빈 집합(통과 0 이 정직).
- **결함 ② 재실행 예외**: 같은 주 재발행이 원장 append-only ValueError 로 runWeek 전체 크래시(봉인 후 크래시 시 블록 복구 불가). 수정 = issueReadings 가 이미 봉인된 주는 스킵(return 0) + `_lastHash(dir, week)` 재발간 자기참조 방지.
- 회귀 가드: testNetGateColdStartNotApplied·testRunWeekRerunSameWeekSafe. tests 152·재실행 판독 중복 0 실측.
- **정직 잔여**: certify None(채점 이력 20주 미만 = 라이브 누적 시간 문제), 채점 pending(가격 데이터가 202625 주까지라 forward 5일 라벨 미형성 → 다음 sync 후 자동 채점), rate 팩터 불활성(월단위 BASE_RATE 로 rolling 베타 ~0, 일단위 국채 시리즈 필요 = 기록된 기존 갭).

### 0c-11. 4단 파이프 실장 = 작업대→E 연장→프로파일→조건부 시나리오 (2026-07-06, 운영자 개념 승인 "진행해라 정공법으로")

- **개념(운영자)**: ① 전 엔진 데이터 1 포맷 작업대(전상장사=DART+EDGAR) ② 시계열에 E(예측) 연장선 ③ 그것만 봐도 다 아는 회사 프로파일 ④ 시나리오 시뮬. 규율 2: E 는 표식 층(피처 역류 금지)·전부 봉인 채점.
- **② E 층 `estimate.py`**: 방법은 실측 백테스트로 선택(KR 6.4만 표본/계정): 흐름 계정=전년동기 seasonal(상대오차 0.214 vs carry 0.741, DART 누적 관행 면역), 저량=carry(0.044). 성장 외삽 전 계정 패배 기각(VAR 교훈 동형). 밴드=분위 5점(점 예측 금지 계약), 스케일은 베이크 없이 런타임 PIT 오차분위(자기 이력>=8 else 계정 풀링). 전부 expectationLedger 봉인(pinball/CRPS 채점). **실봉인 KR 62,579·US 108,621행**(e-v2), 같은 vintage 재발행 스킵.
- **실행이 잡은 결함 3**: (a) **scanFinanceGrid 연결/별도 혼입**(삼성 매출 333조 CFS vs 238조 OFS 접수순 뒤섞임 → CFS 우선 정정, ep/bm 표면 입력까지 정화, CODE_VERSION reading-v3) (b) **E 밴드 |앵커| 분모 폭발**(삼성 순이익 p95 3,791조 → 최근 4분기 평균 규모 분모로 149조 정상화, e-v1 기각 박제) (c) **금리 시나리오 단위 100배 과소**(rate 시리즈 percent 단위 0.5~5.25 인데 shock 0.01 → 1.0 정정. 이래서 금리 시나리오 전반응 0.00% 였음).
- **① 작업대 채움 `enginefeeds.py`**: industry=업종 동행 모멘텀(159 업종 중앙)·credit=자금조달 52주 압력(surfaces.FINANCING_EVENTS SSOT 승격, KR 3종/US securitiesOffering). 라이브 경로 멱등 설치(주입 테스트 격리). **실봉인 완주: industry.indMom 2,875행·credit.fin52w 2,875행(기권 2,231 = 발화형 희소 설계) = 표면 10개.** 부호 선험 강제 없음(채점이 정함).
- **③ profileAll E·US**: market 파라미터(KR 20형질·US 15형질, 미배선 축 정직 부재) + E 열(revenueE/netIncomeE ± 밴드 + 대상분기). 실측 KR 2,875 x 20 (11초, revenueE 충전 76%)·US 7,074 x 15 (16초, 45% = XBRL frame 결손 정직).
- **④ 조건부 E `scenarioTree.industryElasticity/conditionalE`**: 업종-분기 중앙 YoY 를 분기 공통효과 차감 후 팩터 시계열 회귀(풀링 금지 = 가짜 검정력 차단. 차감 전 t>=3 30쌍 전부 rate 양(+) = 인플레 공통추세 교란 실측, 차감 후 7쌍 = 소프트웨어·정보서비스·통신 금리 음(-) 듀레이션 채널로 경제 정합). **인증 쌍만 E 이동, 나머지 기권 명시**: 리스크오프 실측 = 매출 E 2,248행 중 247행 조건화(소프트웨어 -4.3%·전기통신 -5.2%·연료가스 +11.2%).
- **E 소비 루프 폐합 `estimate.epFwd` 피드**: 전방 E/P(다음 분기 순이익 E p50 / 시총) 를 estimate 피드로 등록 = E 층이 판독 사이클로 소비되는 3번째 피드. E 는 PIT 과거의 결정론 함수라 look-ahead 0 (역류 아님, 별도 표식 표면). trailing fund.ep 대비 전방 정보 유무는 성적표가 측정. 실봉인 2,875행(기권 683) = **표면 11개**. 라이브 누적만(과거 주 backfill 은 주별 vintage 재계산 필요 = 정직 라벨).
- **runWeek E 심장박동**: 주간 라이브 런이 E 봉인(sealEstimates, 같은 vintage 멱등 스킵)·채점(scoreEstimatesDue)을 자동 실행하고 블록에 `estimateSummary` 봉인 (주입 경로 = None 명시, 실패 = 격리 + 블록에 오류 명시). 실측: week 202625 재실행 = {'sealed': 0, 'scored': 0, 'asOf': '20260619'} (멱등 확인). 운영자 개입 없이 분기 실적 도착 시 자동 채점 누적.
- tests 166(신규 16)·dartlabGuard strict 7/7 + 외부 게이트 6 PASS. E 는 판독 피처로 역류하지 않음(06 §5c 보간 금지 유지).
- **정직 잔여**: E 채점은 다음 분기 실적 도착부터(시간 문제). US 프로파일 industry·베타·counterparty 미배선(EDGAR docs 에 SIC 부재 실측 = 별도 소스 필요). 탄성은 rate 지배(oil/fx 통과 0 = 강제 배선 안 함). Q4 흐름값 = DART 연간누적 관행(seasonal 면역이나 표시 개선 여지 = Q4 단분기 도출은 차기 검토).

### 0c-12. rate10y 팩터 1행 등록 = 자동흡수 실전 증명 + 격자 beam 스케일 (2026-07-06)

- **기록된 갭 해소**: "rate 팩터 불활성(월단위 BASE_RATE 계단 = rolling 베타 죽음, 일단위 시리즈 필요)" 갭을 **fred SSOT 에 이미 저장돼 있던 DGS10**(일단위 미국채 10Y)으로 해소. `factors._REGISTRY` 1행 = 하류 수정 0: 베타 충전 **437종목(월단위) → 3,277 전종목 100%**, 공분산 축 4, 금리 시나리오 유효 반응(금리 -100bp = 교육·시설관리 하방 등), 프로파일 축5·탄성 회귀 자동 포함. 금리 시나리오는 rate(정책)+rate10y(장기) 동폭 충격(단순화 명시).
- **격자 beam 스케일 결함**: k=4 에서 beam 1500 = 손실질량 49% 실측 → beam 을 팩터 수에 스케일(1500 x 10^(k-3), 상한 5만): k=4 beam 15000 = 0.98% (k=3 기준선 0.67% 동급), 5.5초.
- 관용성 2 정정: industryElasticity 데이터 부재 팩터 스킵(factorChanges 동형), 프로파일 베타 테스트 레지스트리 전수화. tests 166·라이브 runWeek 4팩터 완주(top10 일관).

### 0c-13. Q4 단분기 도출 = 실측 기각 (2026-07-06, 측정이 아이디어를 도태)

- 가설: DART Q4 흐름값 = 연간누적 관행이 E 밴드 스케일을 왜곡(trailing 4슬롯 평균에 연간치 혼입) → Q4 단분기(연간 - Q1~Q3 합, 산술 항등) 도출로 개선?
- 실측: 도출 가능 85%(58,351건)·삼성 2025 Q4 단분기 93.8조 정확·스케일 왜곡 1.77x → 1.02x 해소 확인. **그러나 seasonal E 상대오차가 전 계정 악화** (매출 0.132 → 0.180, 영업이익 0.572 → 0.856, 순이익 0.844 → 1.084): 연간 합산은 분기 노이즈 상쇄로 더 예측 가능, 단분기 잔차는 4개 수치 오류 집중. 도출 매출 음수 4.2%(데이터 오류) = 무가드 사용 위험.
- **판정: 배선 안 함.** 밴드 캘리브레이션은 d 이력·적용이 같은 관행을 공유해 평균 보존(슬롯 조건부는 아님). 재방문 트리거 = 라이브 CRPS/PIT 채점에서 슬롯별 miscalibration 실측 시 (슬롯 조건부 밴드로).

### 0c-14. epFwd 엣지 실측 = 랭킹 알파 없음 (2026-07-06, E 역할 정직 확정)

- 역사 49주 샘플(2019~, 8주 간격) top-bottom 5분위 forward 5일 스프레드: **epFwd -2.5bp (t -0.14) = 엣지 0**, trailing ep +29.9bp (t +1.62), 두 신호 주간 스프레드 상관 0.86 (전방 E/P = trailing 의 노이즈 낀 복제. seasonal E ≈ 전년 값이므로 구조적 귀결).
- **E 층의 가치 = 랭킹 알파가 아니라** ① 연장선(회사 이해·프로파일) ② 분위 밴드(불확실성 봉인·채점) ③ 조건부 시나리오(탄성 인증 업종의 E 분기). 표면은 등재 유지(도태는 인증 깔때기: 무인증 = 무가중이 자연 처리). 몇 달 기다릴 라이브 채점을 역사 샘플로 선제 측정한 것.

### 0c-15. 데이터 갱신 → 라이브 3주 완주 + 주말 스냅샷 잠복 결함 정정 (2026-07-06~07)

- **로컬 미러 갱신**: 수집 CI 는 정상(가격 sync 당일 성공)인데 로컬 data/ 가 6/19 에 멈춰 있던 것 → HF SSOT 직다운로드로 가격(~7/3)·매크로(fred ~7/4)·allFilings(~7/6) 갱신. prebuild=offline HF 다운로드 규약 경유.
- **주말 스냅샷 잠복 결함**: priceWeekly(KR·US 동일)가 docstring 과 달리 스냅샷 미구현 = 일별 raw 에서 거래일마다 판독이 나가 **주간 판독 5배 중복 봉인** (옛 로컬 2026 파일이 우연히 주간형이라 잠복, 정본 일별 raw 로 갱신하자 발현). 정정 = (code, week) 마지막 거래일 1행 + **발행부 불변식 가드**(연속 표면 중복 = 즉시 ValueError, silent 봉인 차단). ⚠ US 601주 백테스트 수치는 일중복 판독 기반(주간 평균 근사라 방향 유효하나 스냅샷 정정 후 재실행 권장 = 차기).
- **발간 전 원장 재구축**: 오염 봉인(당일 생성 로컬 원장, 미발간)을 삭제 후 고친 엔진으로 202625~202627 재발행. 중복키 0·주당 ~29.7k~30.3k 판독 x **23표면**(신선한 allFilings 로 레버 전군 발화 + 피드 3).
- **첫 라이브 성적표(2주 채점 45,958행, 이론 정합)**: treasuryAcquire +612bp(n=21)·lockupExpiry +448bp(n=54)·fund.bm +207bp·**industry.indMom +169bp(신규 피드 첫 성적)**·fund.ep +132bp / maxRet20 -235bp(복권성 회피 = 음수 확인)·ret5 -80bp(단기 반전). 2주 소표본 = 인증은 20주 후 깔때기가 판정.

### 0c-16. 매크로 E = 격자 자신의 성적표 (2026-07-07)

- `lattice.factorMarginals`(잎 분포의 팩터별 가중 분위 5점) → `estimate.sealMacroOutlook/scoreMacroDue`: 격자가 행동 근거로 쓰는 8주 분포를 그대로 기대 원장에 봉인하고 대상일 도래 시 coverage/CRPS 채점 = **격자 분포가 현실을 커버하는지 격자 스스로 채점받는다**. runWeek E 심장박동에 KR 라이브 배선 (estimateSummary.macroSealed/macroScored).
- 실봉인 4행 (rate ±0.21%p·fx ±5%·oil 71.9 p5 53.9~p95 89.9·rate10y ±0.44%p, 8주 지평). 기존 CI expectationCycle 의 매크로 기대(CPI·기준금리·환율)와 **같은 ExpectationSpec 계약으로 자연 합류** (검증 척추 재사용 실증). tests 170 (신규 2).

### 0c-17. 스냅샷 정정 후 KR/US 역사 백테스트 재실행 = 인증 척추 생존·강화 (2026-07-07)

- 0c-15 의 "재실행 권장"을 즉시 이행: `backtest("US")` 599주·`backtest("KR")` 598주 (중복 제거된 주말 스냅샷 판독).
- **US**: B/M t+5.17(기록 5.5 유지·인증), ret5 t-10.59(기록 -6.4 → 강화·발굴), maxRet20 t-11.26(복권성 회피 최강 발굴), volShock +5.00·high52 +4.21 인증, spaP 0.000·PBO 0.0013. **KR**: volShock t+9.74(기록 6.3 → 강화)·dilutionGovernance +4.15·E/P +3.03(기록 3.2 유지) 인증, spaP 0.000·PBO 0.030·DSR 0.999.
- **US DSR 해석 정정**: 가정 벌 DSR 0.999(기록) → 0.0007. KR 은 dedup 후에도 DSR 0.999 유지 = 계산 경로 정상이므로, **기록된 US 0.999 가 중복 버그(일중복 의사분산)의 산물이었을 가능성이 높다**. 정합적 해석: US 최강 신호 2개가 회피형 음(-) 발굴(maxRet20 -11.3·ret5 -10.6)이라 롱 탑K 결합 포트 Sharpe 가 약한 것 = 표면 정보력(t)과 롱 포트 수익성은 별개. US 결합은 회피/오버레이 용도로 쓰는 게 측정 정합 (수치 과신 기록을 실측으로 강등).

---

> ⚠ v0.1 폐기 박제: 이전 04는 "초기 아키텍처 = story 동격 L3 `scenarioWorkbench`, 공개 verb `dartlab.scenario`(미결)"을 현재 결정으로 들고 있었다. **01 §3이 이를 코드로 기각**했다(story=순수 렌더러라 동거 불가, `scenario` 명사형은 `macro.scenarios`/`ScenarioOverlay` 충돌). 본 v0.2가 정본.

---

## 1. 현재 확정 결정 (v0.2)

1. 제품은 주가 예측기가 아니라 **조건부 손익-주가 시뮬레이터 + 재생(Play) 미래 리플레이**. scenario≠forecast.
2. **엔진 거처 = 새 L2.5 독립 묶음 `src/dartlab/simulate/`** (드라이버 DAG + 엣지 transfer 소유, leaf 계산은 L2 SSOT 호출). story 동급 L3 기각, 신규 L2 기각(L2↔L2 cross 금지). `L2_PEERS` 미소속이라 analysis+macro+quant 동시 결합 합법. → 01.
3. **공개 verb = `dartlab.simulate(...)` / `Company.simulate(...)`**, `mode=whatif|replay|walkforward`·`universe`(횡단면=scan 위임) 흡수. `scenario` 명사형 verb 기각. → 01 §3.
4. **AI = 노드 평행 `.det`/`.ai` 슬롯.** 목적=보완(약한 노드를 grounding 통과 AI로 교체→결론 개선), 경합(평행 보존+Brier 사후채점)=그 보완이 진짜인지 검증하는 안전장치. 블렌딩 금지. AI 코드=`ai/tools/lens.py`(no-graph-regression). → 01 §6.
5. **driver 수렴/확장 = DriverRegistry**(카드+6게이트 입장, pooled-panel transfer). factor-zoo 규율(다중검정·OOS·차원붕괴·민감도 가지치기·decay). → 02 §2B.
6. **중심 산출물 = Play 미래 리플레이**(기존 터미널 replay 상태기계 미래방향 대칭 확장). 미래 캔버스 개방(EOD "여백 0"은 live 모드 한정). → 05(미작성).
7. **가치평가 = simulate(mode="whatif")의 정적 단면.** 적정주가=조건부 범위+reverseDCF 닻(단일 목표가·rating 금지). 신용=solvency 뷰(같은 단면의 지급능력 렌즈). 보고서=story 렌더, 발간=`story/publisher.py`. → 08·09 §4.
8. **시뮬레이터-앵커 = 정합화 원리.** "모든 시뮬 숫자=하나의 SSOT leaf"가 DCF 5중·회귀 4중·축 이중화를 구조적으로 청산. 실행은 외과적·census 단조·byte-identical·무중단(빅뱅 금지). → 09.
9. 결손은 0 대체 금지(missing/blocked/partial). 결과는 ref+quality gate status+provenance. look-ahead 차단(t종가→t+1시가). 단일 base 금지(bear/base/bull).
10. **v0.3 심화(12-에이전트 워크플로, 코드 그라운드)** 4 정정 박제:
    - **노드 차원폭발 차단 = 3중 좌표 (driverId, scenarioId, periodKey).** rev.path = 시나리오당 1노드, 연도·분기는 `NodeValue.vector`가 흡수 → 노드 수 O(driver×branch)≈24(폭발 아님). 01 §5.
    - **데이터 추가 = exogenousAxes 1줄(수동) → 전 과정 자동(driverPrefit→admission→decay).** if 상한 = 검증된 축 수(6~8), 시리즈 수와 독립(Stock-Watson). 02 §2B.7~2B.9.
    - **치명 신규 ① models HF 배포 경로 0건** — pre-fit 적합이 `~/.dartlab/`(ephemeral)에만 저장돼 cron 켜도 소비처 영구 None. DATA_RELEASES 'models' 1줄 + `data/models/` 리다이렉트 + `_uploadModels`가 전체 배선의 load-bearing. 02 §2B.5.
    - **치명 신규 ② scanMacroBeta firm-level t-stat 수학적 부재** (연간 N=3, df=N−k≤−1). "N~13 기술"이 한 단계 더 낙관 → firmRefine은 t-stat 게이트 *계산 금지*(pooled에서만 valid), leave-last-k hitrate만. 01 §1 #7·02 §2B.1·§2B.9. **★:205 버그 수정 제안 `*=`도 틀림**(평균경로 소실) — per-year 성장계수 cumprod, 단 kill-test로 '기존이 버그'임 먼저 증명. 01 §12.

---

## 2. 작성 문서 + 상태

| 문서 | 상태 | 비고 |
|---|---|---|
| README | ✅ v0.2 | 문서지도·L2.5 정정 (06 v0.3 반영 1줄 갱신 필요) |
| 00-product-prd | ⏳ v0.1 잔재 | §6 5-pane 화면 토폴로지 → ✅ v0.4 정정 박스 적용(terminal-host 흡수, 별도 셸 0); 잔여 = §5 "Scenario Workbench" 제품명 sync |
| 01-engine-architecture | ✅ v0.3 | §5 노드 3중좌표·§6 NodeValue/실행기/gate/grounding·§12 byte-parity+:205 수식정정·§13b 격자구조·§1 #7(scanMacroBeta N=3) 심화 |
| 02-assumption-method | ✅ v0.3 | mode enum 본문 통일(replay/walkforward/whatif)·§2B.7 end-to-end 데이터배선·§2B.8 수렴증명·§2B.9 tier가드·§2B.10 스키마가드·§2B.5 models HF 배포 갭(치명) |
| 03-validation-ai-review | ✅ v0.3 | §9.3 발간 게이팅 반영(헤더 정본)·fatal① lint 빌드 정합(§4 #9) |
| 04-progress-ledger | ✅ v0.3 (본 문서) | — |
| 08-valuation-report | ✅ v0.4 | 가치평가 융합·발간 계약(코어 졸업 후)·fatal① lint 빌드 정합(발간표면 한정) |
| 09-architecture-consolidation | ✅ v0.3 | 부채 원장·앵커·신용 뷰·Phase 시퀀스·§10 4 fatal 빌드티켓(①✅ 빌드·배선) |
| 05-play-future-replay | ✅ v0.3 | ★중심 산출물. fan-band None구간 끊기·byte-parity 범위 명시 |
| 07-integration-roadmap | ✅ v0.3 | **cross-category 브리지로 전환**(차트 suite ⟶ 시뮬 단방향 시퀀싱·공유 DNA·미래마커 이관) |
| → 06/10/11 **분리** | ✅ 이동 | **`../_done/terminal-chart-suite/`로 git mv**(06→01 차트·11→02 레일·10→03 백테스팅). 번호 공백(00-05/07-09) 유지=cross-ref 안정. 상세 = suite README·07 브리지·§4(14) |

---

## 3. ★워크스페이스 변동 (이 세션 중 실측 — 중요)

mainPlan UI 플랫폼 리팩토링이 **이 세션 동안** 단계-4b~5-2b로 진척(git log 오늘). 핵심:
- **터미널 전체 이동**: `landing/src/lib/terminal/` → **`ui/packages/surfaces/src/terminal/`**(commit `ff9099ba0` "data/→lib/ git mv"). `landing`엔 `terminal-shell/{routeLoad,terminalShell}.ts`만 잔존.
- **결과**: PRD의 모든 `landing/.../terminal/...` UI 경로 stale. 새 SSOT = `ui/packages/surfaces/src/terminal/`(charts/PriceChart.svelte·chartState.svelte.ts 실재) + 포트 `ui/packages/contracts` + 런타임 `ui/packages/runtime`. 엔진 경로(`src/dartlab/*`)는 불변.
- **함의**: PRD가 "mainPlan 이후 착수"라며 가정한 post-refactor 토폴로지가 *조기 도래*. 05(Play)·06(지수)는 새 토폴로지로 재기반 필수. `chartState.svelte.ts` 실재 확인 → README "replay 상태기계 재사용" 옳음, 08 "부재" 정정 대상.
- ui/apps/local SvelteKit 앱 신설(단계-5), createLocalRuntime AiPort SSE 배선(단계-5-2b) — 로컬 고급 엔진 경로 진행 중.
- **★v0.3 워크플로 코드-그라운드 확정**: 정본 = `ui/packages/surfaces/src/terminal/charts/PriceChart.svelte`(klinecharts 1051줄). `ChartCtl`은 PriceChart **내부** 생성(`new ChartCtl` 1곳, setContext 0건) → CenterStack은 ctl 모름 ⟹ 06 v0.2 "ctl.subject 분기"는 컴파일 불가, 정정=CenterStack-local `$state`(06 §2.5). soft-swap은 실재하나 *회사 전환 전용*. replay 상태기계는 *과거 backward-only*(미래 sim.play 필드 신설 필요). 미래여백 0은 *무조건 적용*(05 §2 live 분기 신설 필요). PricePort 실제 메서드 = initial/older/loaded/govCandles/govRecent(PRD `indexInitial` 발명 폐기). `ui/shared/chart/PriceChart.svelte`는 별개 SVG 컴포넌트(혼동 금지).

---

## 4. NEXT — PRD 닫기 체크리스트 (v0.3 갱신)

### ✅ 완료 (v0.2→v0.3)
1. ~~05-play-future-replay.md~~ ✅ — ★중심 산출물 작성(v0.3 fan-band None구간 끊기 포함).
2. ~~06-index-chart.md~~ ✅ — v0.3 전면 대체(subject 소유권 seam·IndexPort catalog/search/series·US 부재 가드). **→ 2026-06-14 `_done/terminal-chart-suite/01-price-index-chart.md`로 분리(§4 #14).**
3. ~~07-integration-roadmap.md~~ ✅ — 시퀀스·의존성·Phase.
4. ~~02 mode enum 통일~~ ✅ — 본문 §2.3·§3.1 → `replay/walkforward/whatif` SSOT 단일.
5. ~~01 §1/§5/§6/§12/§13b 심화~~ ✅ — v0.3 워크플로(노드 3중좌표·NodeValue/실행기/gate·byte-parity·격자·N=3 #7).
6. ~~02 §2B 심화~~ ✅ — §2B.7 데이터배선·§2B.8 수렴증명·§2B.9 tier가드·§2B.10 스키마가드·§2B.5 models 배포 갭.
7. ~~06 OQ12(US 지수)~~ ✅ — 운영자 결정=FRED 채택, 종가 라인 subject로 06 v0.4 통합. FRED 데이터 라이브 실측(SP500/NASDAQ/다우/VIX 4종)·종가전용 지표 3분기 매트릭스·candleStyle 격리. 잔여=구현만.

### 🔨 엔진 착수 — L2.5 `simulate/` (P1 ①② 완료 후 다음, execution-ready scope 2026-06-14)
> ⚠ **이건 대형 engine-add — 신선한 집중 + dartlabGuard 선행 필수**(master-red 교훈: 아키텍처 변경 rush 금지). `.claude/skills/engine-add` 절차 동반.

✅ **개념검증 + foundation 졸업 완료(2026-06-14)** — ★layer subtlety 는 **§10 born-clean 으로 해소**(아래 "1." 의 a/b/c 고민 불필요): simulate/ 는 *소비처 0 신생, 기존 simulation.py 무접촉* → transfer 는 L2.5 에 새로 태어나고(synth L1.5 상수만 forward import) legacy `_applyMacroShock` 잔존(§4 move 는 L2→L2.5 역방향이라 *회피*, BC 위임은 성숙 후 별도). 
  - `_attempts/scenarioSimulate/` 개념검증 PASS(born-clean DAG·transfer byte-identical·buildProforma leaf·결정론).
  - **본진 `src/dartlab/simulate/` 졸업**: `sheet.py`(NodeValue/DriverNode/DriverSheet+computeInputsHash+buildOrder Kahn+evaluateSheet, lens 심볼 부재=invariant-1) + `transfer.py`(transferMacroToFundamentals/transferRevenuePath). LAYER_OF simulate:2.5 등록(indexer.py+test_import_direction.py, downward-only). 검증: dartlabGuard exit 0·22 테스트·9섹션 docstring·born-clean.
  - ✅ **deterministic core 졸업(2026-06-14, `096e84c43`)**: `registry.py`(buildSnapshot read-once + 4 노드 _fnMacroPath/_fnRevPath/_fnProforma/_fnDcf — ★dcf=proforma FCF 기반 FCFF 폴백, `calcDFV` 아님[calcDFV 는 외부 proforma 무시 → scenario-coherence 깨짐]) + `run.py`(runScenario→SimulationResult+NodeAudit). 4노드 DAG end-to-end·32 테스트·dartlabGuard exit 0·결정론.
  - ✅ **공개 verb 졸업(2026-06-14, `ac3905fd9`)**: `simulate/entry.py`(톱레벨 `dartlab.simulate(code, *, scenario, horizon, asOf)` thin wrapper, KR 전용 가드=market!='KR', 9섹션) + `Company.simulate(...)` 메서드 + `__init__.py` lazy map+`__all__`+callable-module 충돌 패치(서브패키지=verb 동명) + `rules.py` FROZEN_PROVIDER_COMPANY_SURFACE 등록. **EngineCall 자동등록**(allowlist=라이브 capability 카탈로그 from `__all__`+Company public methods, 별도 파일 0). 결정론 subset(scenario/horizon/asOf)만 — drivers/lens/mode 는 인자조차 미추가(inert stub=clutter, 후속 phase). 검증: dartlabGuard exit 0·apiContractAudit exit 0(docstring+annotation 충족, contract dir repo-wide 미존재)·test_verb 4 passed·실호출 005930 adverse<baseline.
  - **다음 phase**: lens 보조(`ai/tools/lens.py`, 비결정론 평행 보완·no-graph-regression) · drivers/mode 인자(다중 드라이버 override + whatif/replay/walkforward) · Play 미래리플레이(05) · DriverRegistry 수렴(pooled-panel transfer) · US 프리셋(KR 가드 해제 선결) · (선택)import-linter pyproject contract entry.

**1. (해소됨 — born-clean) transfer 외과 추출 (01 §4) 의 layer subtlety 기록 보존**:
- `_applyMacroShock`(`simulation.py:180-235`) → `simulate/transfer.py::transferMacroToFundamentals`(rename) 이사.
- 실측 호출/proxy: `_applyMacroShock` 호출자 = `_simMonteCarlo.py:184`·`_simScenario.py:199`(둘 다 함수내부 lazy proxy `_simMonteCarlo.py:36-38`·`_simScenario.py:35-38`) + `__init__.py:27` re-export. (`_simHistorical` proxy 는 `_extractBaseMetrics`/`_extractVolatility` 용이지 `_applyMacroShock` 아님.)
- **★발견(PRD 미기재)**: 호출자 `_simScenario`/`_simMonteCarlo` 가 **L2**(`analysis/forecast`)인데 transfer 를 simulate/(**L2.5**)로 옮기면 **L2→L2.5 역방향 import = layer 위반**(viz→providers DIP 위반과 동류, F1.7 재발). ⟹ transfer 단독 이사로는 부족 — 옵션: (a) `simulation/` 시뮬 서브시스템 전체를 simulate/ 로 이주(큰 이동) / (b) DI Protocol(transfer 를 L0 protocol+L2.5 register, L2 가 get) / (c) 01 의 "묶음이 leaf 호출" 의미를 재확인(simulate 가 _simScenario 를 *호출*하지 _simScenario 가 transfer 를 호출 안 하게 재배선). **착수 전 01 §3~§5 재정독 + 호출방향 확정 필수** — 안 하면 architecture-l0-l15 FAIL.
- 부수: proxy 4 dissolve(no_import_evasion 부채 청산), import-linter contract(`pyproject.toml`)+`test_l2_no_cross_import`(L2_PEERS)+`test_l15_entry_rule` 에 simulate L2.5 등록, byte-identical 검증.

**2. 이후**: DriverNode/DriverSheet(`simulate/sheet.py`) + 위상정렬 실행기 + gate/grounding(01 §6) → AI lens(`ai/tools/lens.py`, no-graph-regression) → Play(05). 공개 verb `dartlab.simulate(...)`(01 §3).

### ⏳ 남은 정합성 (v0.1 잔재 + lint 범위)
7. ✅ **00 v0.2 동기화(2026-06-14)** — §2 본문 "Scenario Workbench" → `simulate` 치환, §7.2 #9 비범위에 simulate=L2.5 합법성 예외 1줄 추가. §5 "Valuation Report + Credit View = simulate 발간 단면" 은 v0.2 정정 헤더가 이미 정본 우선으로 커버(본문 전면개정은 선택, 미실시). 정정 헤더 + 본문 잔재 치환으로 doc정합 닫음.
8. ✅ **03 §9.3 발간 게이팅(2026-06-14)** — 03 v0.2 정정 헤더(line 7)가 이미 "발간 모드는 코어 SimulationResult 실측 확정 후를 본진 승격 기준에 추가"로 정본 커버. 08 §11 우선순위 역전 가드 반영 완료(헤더 정본).
9. ✅ **fatal① T1 금지어 lint 신설·CI배선 완료(2026-06-14)** — `tests/audit/valuationPublishLint.py`(+test) 발간 표면(`reportType: simulation` 마크다운) 한정 스캔, `tests/run.py:140` GATES lint 체인·green no-op·6 unit PASS. leaf 3파일(priceImplied·_valuationOther·pricetarget)은 `_isSimulationReport`가 `.py` 영원히 미스캔(옛 "2/3파일" src-스캔 모델 무효 — 발간 누출은 §2.3 어댑터가 drop). 잔여=T2 발간 표면(Phase 6). 03/07/08/09 "lint 미존재" 서술 stale 정정 동반.
10. **README 1줄** — 06 v0.3 반영(완료) + 06 문서지도 갱신(완료).
11. ★**빌드티켓 천장(09 §10)** — fatal① T1 ✅·Phase 0 ✅. 잔여 천장 = fatal②(forwardTest recordForecast write·models HF)/fatal③(gate/ledger/admission/lens)/fatal④(US threading) = **SYSTEM(미빌드 코드) 천장이지 PLAN 결함 0** — 설계는 09 §10 에 파일·시그니처·테스트게이트·phase 까지 execution-ready 로 닫혀 있고, 미빌드는 *코드 부재*지 *설계 미결*이 아니다(채점규칙: 코드부재≠감점). ★**planScore SSOT = §0(세 축 planScore 95)가 정본**(2026-06-20 R12 봉합 — 직전 "planScore=100" 표기는 본 항 1곳에만 있던 SSOT 분열이라 §0 로 강등): 본 항은 그 95의 *빌드측 근거*다 — fatal①~④ = SYSTEM 천장, PLAN 결함 0(설계는 execution-ready). systemScore=빌드 진행률(현 fatal① 1/4). **한 문서 한 점수**(100 vs 95 모순 제거) — planScore 정본은 §0, 본 항은 systemScore 분리 근거. 두 축 혼동 금지.
12. ★**타사 개념 흡수 토론 반영(2026-06-14, 경쟁 6서비스)** — 12 agent 토론+적대검증으로 흡수후보 9종 판정: 5종(A3·A6·A8·A9 already + A5 honesty 위반 reject)·4종 **absorb-as-defer**(새 기능 0, 한계 라벨/defer-게이트로만). PRD 반영 완료: A1 preset 출처 라벨+미검증 warning 시나리오-레벨 전파(02 §2.3, **졸업 AC**) / A2 임의충격 UX defer(02 §2B.3, 01 §4 already-have 명기) / A4 라이브 레버 = dirty recompute+S_T 격자 선결 defer(05 §4) / A6 fan band σ provenance 실선/점선 시각 규율(01 §5b·05 §3) / A7 공개 Brier 리더보드 write-end 후 defer(03 §9.3) / A5 점확률 발간 금지 가드(02 §2.3). 시그니처 판정=**conditional-signature(합의 61, KEEP 조건부)** — 00 §경쟁 지형·시그니처 박제. 잔여 졸업 AC = A1 warning 전파 실배선(write-end dead chain 동일 선결).
13. ★**A4 라이브 레버 졸업 의존** — live 레버(드래그→즉시 재렌더)는 lens/drivers phase(`_dirtyClosure` dirty recompute 01 §6.2·§13b-1 + Sobol S_T 격자 OQ11) 의존으로 deferred. 그 전엔 landing=사전 동결 격자 lookup·격자 밖 토글="로컬 재계산 필요" 한계 라벨(05 §4).
14. ★**차트 suite 분리 완료(2026-06-14, 운영자 go)** — 현재/과거 차트 3 컴포넌트(06 지수→01 차트·11 레일→02·10 백테스팅→03)를 **`mainPlan/_done/terminal-chart-suite/`로 git mv**(이력 보존). 절단면=**시간축**(현재/과거=suite, 미래=시뮬). **단방향 의존**(suite ⟶ 시뮬 05 Play, 역참조 0 — 시뮬-앵커 사상 동형). 07 = cross-category 브리지로 전환(시퀀스·공유 DNA·미래마커 이관). 시뮬 번호 공백(00-05/07-09) 유지=cross-ref churn 0. 갱신 동반: scenario-simulator README 문서지도·07·00:상태박스·05:37/48 형제참조·suite README 신설·terminal-chart-suite H1 renumber+참조규약. **이유=셋이 시뮬 미완 게이트(write-end·admission)에 인질로 안 잡히고 독립 출시 가능**(분리의 핵심 이득). 메모리 포인터 갱신 동반(시뮬+백테스팅+이벤트레일+terminal-improvement 경계). ⚠ `project_terminal_improvement` 경계 노트("지수/이벤트레일=scenario-simulator")가 stale→terminal-chart-suite로 정정 필요.

---

## 5. Open Questions (v0.2 — v0.1 미결 close 후 잔여)

> v0.1 OQ1(verb 위치)·계층 결정은 01 §3이 close. **2026-06-14 완성도 검토(구현자 시뮬레이션)로 OQ2~13 대부분 resolve-now 결정**(아래 ✅, 코드/1차원리 근거)·OQ11=데모 명세 확정(🔬)·OQ1=거시 AR/VAR 데모/빌드 의존(천장). 잔여 진짜 미결은 데모-보정 *값*뿐(규칙·설계는 결정됨).

1. 거시 미래경로 예측(AR/VAR) — 부재 확정(01 §9). 별도 _attempts 라운드 시점(데모/빌드 의존 천장, 09 §10 잔여).
2. ✅ **결정(rule)**: pooled 풀 경계 = **IndustryGroup(sub-sector) 기본 → pooled-N<60 이면 부모 WICS-11 Sector 승격 → 여전히 <60 이면 DEFAULT_ELASTICITY+warnings**. 근거: macro-β 식별 DoF≈time-DoF T(Moulton, §2B.1)라 풀 *폭*은 β t-stat 못 높임(기업이질성 정밀도만); SECTOR_ELASTICITY 이미 sub-sector grain(35키), `_resolveSectorKey`(_valuationHelpers.py:55) 가 industryGroup.name→2층 구조 보유(새 코드 0). **데모 필수 = 경계 임계값만**(IG풀 vs 승격이 leave-last-k=4 OOS partial-R²로 갈리는 지점). 02 §2B.1/§2B.11.
3. ✅ **결정(아키텍처)**: AI lens 노출 = **fork/큰-gap 노드만**. '전 근거 나열'은 결정론 provenance/refs(run.py NodeAudit 전 노드)가 이미 충족 — AI 의견은 약한-det fork 의 DisagreementLedger 로만 표면. 노출 *수준*은 비용/환각/원칙(불변2)으로 결정(데이터 무관); 데모는 FORK_THR/grounding 임계 *값*만 보정. 01 §6.4.
4. ✅ **결정**: `universe=` 횡단면 UI = 기존 **ScreenerModal** 흡수(새 셸/라우트/둘째차트 0). 노출랭킹=ScreenerModal 리스트+노출-스코어 컬럼(scan 위임), 행클릭=기존 onPick(code)→PriceChart subject+단일사 full DAG(01 §13c). 정본=07 시퀀스 4 + 00 §6.4(옛 '06/07' 라우팅 정정 — 06 은 무관).
5. ✅ **결정(빌드 의존 순서)**: (1) ReportDock valuation 단일모드 먼저(08 §5 YAGNI) → (2) P7 졸업(extractChsFeatures 가 proformaStatement 수신, 본체 0줄, 09 §4.3 — 현 `chsFeatures.py:18` 미수신) → (3) credit mode(09 Phase 5). credit mode 를 P7 전에 켜면 actual-only dead 탭. 정본=09 §4.5.

### v0.3 신규 잔여 (워크플로 심화)

6. ✅ **결정**: driverPrefit = **주간 dataPrebuild FULL 경로**(일 cron `0 17 * * 0`)에 한 step(증분 prebuild-scan 아님). driverDecay(forwardTest persistence/G5)는 별도 분기 cron 유지. 근거: scanMacroBeta 가 **연간 컬럼만**(macroBeta.py:113)+pooled-β DoF≈연간 time-DoF라 분기 공시는 연간 design matrix 거의 불변 → 증분 재적합=같은 (XtX) 재계산 낭비+churn. dataPrebuild.yml 에 prebuild-scan+prebuild-full 이미 존재라 full 편입=새 cron 0(prefit=design-matrix 주기 vs decay=outcome-vintage 주기). 02 §2B.7.
7. ✅ **결정**: tier 는 axis 에서 **파생**(저장 안 함): `tier='core' if card.axis in {6 exogenousAxes 문자열값} else 'exploratory'`. 운영자 수동=카드별 override 플래그만(기본 빈값). 근거: `ExogenousIndicator`(exogenousAxes.py:34)에 axis 있으나 tier 필드 없음; 척추 6축=그 6 문자열값, 뉴스·customs 미등록(candidate)→core/exploratory 가 axis 와 1:1. 저장 tier=axis 동어반복+drift. ⚠ `EXOGENOUS_AXES` 명명 상수 없음 — 6 문자열리터럴 또는 파생집합(`{ind.axis for ind in indicators}`, exogenousAxes.py:461) 참조. 02 §2B.3.
8. ✅ **결정**: mc.distribution `deps=(proformaId,)` — proforma 노드의 **FCF 벡터(`NodeValue.vector`)** 에 의존(leaf 아님). mean path=proformaNv.vector(단일 SSOT), noise σ=snapshot elasticity. 벡터화 noise 만(buildProforma 재호출 0 — `_simMonteCarlo.py:203-211` cumprod=OOM 없음). **`NodeValue.frozenInputs` 확장 불필요**(mc 는 proforma mean vector+σ 소비, macro 분포 파라미터 아님 — '직접계산 vs deps' 이분법 해소). byte-parity 제외(RNG), 분포통계 ±ε 만. 01 §5b.
9. ✅ **완료(close)**: :205 cumprod 전환 완료(09 P1, `ad112b171` cumprod + `fe9e66c0a` seed isolation). kill-test `test_horizon_widens_cone` 가 옛 cone-일정 버그 증명 후 전환. §4 P1 ②·§6 체크리스트 [x] 와 중복 — open 목록서 닫음.
10. ✅ **결정**: groundingCheck(b) 수치 범위 출처 = **snapshot 실측 base metrics ± 고정 tol**(`snapshot.baseRevenue/baseMargin`, registry.py:188 실측 키)을 단일 규칙으로. 약한 det 자체분포 금지(순환). `AssumptionLedgerRow`(코드 0건) 제거. ledger-row 없는 노드: (b) 기권→fork(det-분포 폴백 아님)=abstention-over-circular. gate.py 설계 계약으로 박음(데이터 무관). 01 §6.3.
11. 🔬 **데모 명세 확정(데이터 의존, 실험 닫음)**: Sobol S_T 컷오프 — 표본=척추 6섹터×2사=12 + 토글 8~10; 추정기=Saltelli/Sobol N_base=1024(≤12,288 결정론 DAG eval, 벡터화); 타깃=dcf perShare+terminalRevenue; **판정=컷오프 재정의 'top-6 토글 누적 S_T≥0.9'**(k≤6 보장, 고정 0.05 폐기); robustness=seed×3+bootstrap CI+cross-firm Kendall τ(τ 불안정 시 글로벌 컷오프 기각, per-firm top-6 폴백). 근거: src 에 variance-Sobol 부재(sensitivityAnalysis=OAT tornado), S_T 는 입력분포×출력비선형 의존이라 a priori 결정 불가. 02 §2B.11·01 §13b.
12. **(close — 운영자 결정=FRED 채택)** ★US 지수(SP500/NASDAQ/다우/VIX) = **FRED 종가 라인 subject로 06 통합 확정**. 운영자 결정 '미국 지수는 FRED 고려' 반영. 로컬 `data/macro/fred/observations.parquet` 실측으로 4종 라이브 확정(SP500 2609행 2016~·NASDAQCOM 14440행 1971~·DJIA 2609행 2016~·VIXCLS 9508행 1990~) — '데이터 전무(grep 0건)' 정정(grep은 ui 코드 미배선이지 데이터 부재 아님). KR=OHLCV 캔들 / US=종가(o=h=l=c, v=0) degenerate candle + `candleStyle='area'`. 새 차트·포트 0(IndexRef.market 분기 + 변환 1함수). 종가전용 제약=캔들·ATR·KDJ·CCI·WR·DMI·ICHI·AO·CR·VP 불가(06 §4.2), MA/RSI/MACD/BOLL 등 close-기반만 정상. 06 §3.2~§3.6·§6. **잔여=구현만**(데이터 선결 0). 표면 선호 1건(macroSource srcCache 공유 vs 소스 독립, 06 §7 OQ2).
13. ✅ **결정(경로, 실행 후속)**: 별도 `indexCompares: IndexRef[]` 슬롯(compares 의 IndexRef 확장 *기각*). 근거: `ctl.compares` 는 `{code,name}[]`(chartState:97)라 IndexRef 재구성 불가, compares 확장은 N사 compare 경로 회귀. indexCompares=가산적·회귀 0. 실행=06-subject 후 별트랙(US 벤치마크는 forward-fill 캘린더 정렬 선행). 06 §7.

---

## 6. 구현 전 체크리스트

- [x] main memory 포인터 (project 메모리 — 본 세션 추가 예정)
- [x] 엔진 거처 L2.5 simulate 확정·근거 기록 (01)
- [x] driver 수렴/확장 메커니즘 (02 §2B)
- [x] AI 보완/경합 + no-graph-regression (01 §6)
- [x] 가치평가·신용 = simulate 뷰 (08·09 §4)
- [x] 부채 원장 + 외과 시퀀스 (09)
- [x] **MC seed kill-test 선결 (P1) — ①② 완료(2026-06-14)**
  - ✅ **① MC 시드 전역오염 격리**(commit `fe9e66c0a`): `_simMonteCarlo.py`·`pricetarget.py` 의 전역 `random.seed`/`random.gauss` → 로컬 `rng = random.Random(seed)` 인스턴스. **동일 seed→동일 Mersenne 시퀀스라 동작 무변경**, 전역 RNG 오염만 제거. ★spec 의 numpy PCG64 대신 stdlib `random.Random` 채택 — 동작 무변경·`외부 의존성 제로`(pyodide 안전) 보존·jumpable streams 는 simulate 엔진이 필요할 때 재방문. test_simulation 29 PASS.
  - ✅ **② MC 호라이즌 cone 누적**(commit `ad112b171`): `:205` 내부 루프가 `simRev`/`simMargin` 을 매년 덮어써 마지막 해 노이즈만 반영(호라이즌 무관 cone 일정 = 버그). fix = 연도별 성장계수 cumprod(`cumRevFactor*=1+revNoise`) + margin 가산 random-walk(`cumMarginNoise+=`), mean path 보존. **kill-test `test_horizon_widens_cone`**: 옛 코드 FAIL(cv h=1 0.2251 ≈ h=3 0.2228 = 버그 증명) → cumprod 후 PASS(cone 확대). 전체 30 MC PASS(정성 회귀 0). 옛 `*=` 단순수정은 평균경로 소실이라 기각. 운영자 가시 기록 = kill-test + 커밋.
- [ ] 05/06/07 작성 + 00/02/03 v0.2 동기화 (NEXT §4)
- [ ] 워크스페이스 새 토폴로지(ui/packages/surfaces) 반영 (05/06)
- [ ] 착수 = mainPlan 완료 후 (조기 진척 중 — 의존성 07에서 확정) + 운영자 go


## 2026-07-05 : 06 "현재" 축 탑재 (운영자 합의)

- 신규 문서 06-engine-readings-and-sweep.md: 전 하위 엔진 데이터를 한곳에서 모아 출처·성격별
  판독(표면 카탈로그 자동 전수 등재, 선별 0) → 전량 봉인(issueReadings, issueMacro 동형) →
  주간 채점(G16 정합 수축 성적표) → 가정 sweep(상황 가정=명명 프리셋 소비, 결합 가정=
  AssumptionLedgerRow 규율 첫 적용, 선정=강건성 median, 가정도 봉인·채점).
- 00 §8b conditional-signature 의 "검증 루프 미완"을 채우는 조각. 09 §10 fatal②(forward-test
  write 끝단)를 주간 전종목 규모로 실장.
- 토론 이력(v0.1~v0.6.1)·P0 실측·갭 원장 = ../weekly-uplift-shortlist/ (아카이브 전환).
- 원칙 확정 반영: 개별 데이터 작업대 폐기(dossier df41ee60e), 호출계약은 엔진 소유 verb 로만.
