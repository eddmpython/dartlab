# 04. Progress Ledger

상태: PRD v0.3 (2026-06-13 12-에이전트 워크플로 심화 . 지수 차트 완전 명세 + 시뮬 backbone/데이터배선 코드-그라운드 재설계 + 적대검증 반영) + ★2026-06-20 9인 전문가 패널 uplift(아래 §0)
범위: 현재 확정 결정, 미작성/정정 갭, NEXT 시퀀스, 구현 전 체크리스트

---

## 2026-07-13 P0 제품 진실성 복구

코드 재감사에서 결정론 4노드 코어의 실현 가능성은 확인했지만, 제품 계약과 시점 규율에 치명적인 결함 6개가 확인됐다. 본 단계는 UI 확장이 아니라 잘못된 숫자와 과대 상태표시를 먼저 차단한 복구다.

| 항목 | 감사 전 | 복구 후 | 잔여 한계 |
|---|---|---|---|
| 재무 입력 | 연간 시리즈에 TTM을 적용해 최근 4개 연도를 합산 | 분기 시리즈 4개 분기 TTM | 분기 표준화 품질은 finance 엔진에 의존 |
| `asOf` | 결과 라벨만 변경, 입력값 동일 | 요청 분기까지 시리즈 실제 절단, effective/latest/requested 분리 | 공시 접수일·정정공시 vintage는 원천 부재 |
| scenario | 모르는 id도 baseline 계산 후 잘못된 id를 결과에 유지 | 유효 프리셋 외 즉시 `ValueError` | 사용자 정의 scenario는 미지원 |
| horizon | 10년 요청을 3개 벡터로 잘라 결과 horizon과 불일치 | 프리셋 경로 길이 밖 요청 거부 | 현재 프리셋은 최대 3년 |
| 결손·기본값 | net debt 결손을 0으로 대체, 기본 가정 비노출 | net debt 결손이면 주당 DCF 기권, 기본값을 `assumptions`로 노출하고 quality partial | 기본 가정 자체의 추정 모델은 후속 |
| 재현 해시 | 같은 수치면 다른 `asOf`도 동일 hash | `asOf/latestAsOf`를 hash 입력에 포함 | filing-vintage가 생기면 receipt-date도 포함 필요 |

**실측 증거**:

- 삼성전자 최신 분기 기준 `baseRevenue=388,338,879,000,000`, `baseMargin=24.24%`, `netDebt=-46,359,125,000,000`, `quality=ok`.
- baseline 3년 매출 경로 `398.8조 -> 413.2조 -> 429.5조`, 주당 DCF 약 `64,362원`. 이는 목표주가가 아니라 고정 가정의 조건부 변환이다.
- `tests/simulate` 199개 전부 통과. 신규 회귀는 scenario/horizon 거부, 분기 `asOf` 절단, 과거 shares 기권, net debt honest-gap, vintage hash, assumption/warning 품질 강등을 포함한다.

**현재 판정**: 결정론 계산 코어는 제품화 가능한 수준으로 복구됐다. 그러나 PRD 전체는 미완료다. filing-vintage PIT, 공개 axis/API/Skill OS 계약, Play UI, fan distribution, driver/lens가 남는다. 특히 호출 가능한 Python preview와 등록된 공개 계약을 같은 것으로 취급하지 않는다.

---

## 0. ★2026-06-20 9인 전문가 패널 uplift . 세 축 planScore 95 도달

**목표**: 각 분야 전문가 + UI/UX 전문가 관점으로 플랜을 *시각화 직관성·분석 전문성·예측 전문성* 95점까지 개선(운영자 지시). **결과: 세 축 모두 planScore 95 도달 확정**(설계 완전성 . 04 §4 #11 systemScore[빌드]와 분리, 코드부재≠감점).

| 축 | 시작 | 최종 | 핵심 닫힘 |
|---|---|---|---|
| 시각화직관성 | 66 | **95** | 시각 인코딩 SSOT(05 §10, 기존 HonestyFooter 3단·AuditStrip 1:1 확장)·레이아웃 와이어프레임(05 §0.5, TerminalSurface:370-376 colL 교체 코드근거)·ReportDock 거처(05 §8.1=StrategyDock fill 일반화)·Bridge Waterfall 시각 문법(08 §3.4)·초보 학습성 3종(05 §11·§12: 상태 카피·온보딩 ladder·TermGloss·disclosure-level) |
| 분석전문성 | 79 | **95** | Driver Coverage Census(02 §2C, 11-driver 실측 coverage% 명시 정량)·회계품질 leaf-binding(09 §0 7~8행+03 §5 producer 매트릭스+01 §5b quality.baseline)·base margin 정규화/COGS tier(02 §3.8)·checkValuationCoherence(01 §6.3, terminal-g·value-destructive·(d)영구초과수익 moat)·PeerSelection 회귀-조정+DoF 가드(03 §6.3)·라이프사이클 dispatch(01 §5b) |
| 예측전문성 | 82 | **95** | G16 Calibration 게이트(03 §4.4: coverage[over/under 대칭]·PIT·CRPS·skill+baseline 명명+pooled-only)·mc.distribution 측정 비모수 분포(01 §5b: regime-σ·empirical-quantile·cone 검증)·forensic→fan σ 하방 비대칭 전파(02 §3.7 FQ2)·DSR/PBO admission(09 §10.3)·driver 공분산 fan(02 §3.11)·coverage drift 2채널 decay(02 §2B.2)·look-ahead 3표면 assert(02 §2B.11) |

**과정**: 진단(9인 패널: 시각/분석/예측 각 3인)→23항 우선순위 백로그(3-Wave: A 문구즉시·B 사양게이트·C write-end 의존)→구현(6 문서-소유 에이전트 병렬, 569 insertions·충돌 0)→적대 재평가(94·95·94)→잔여 설계 갭 7건 외과 보강→확정 재평가(95·95·95).

**규율**: 전 개선 **honestySafe=true**(검증 척추 강화 또는 중립)·**새 파일 0**(기존 9문서 내 절/소절/표 행 신설만)·**새 패널/슬라이더/색 0**(기존 자산·토큰 재사용 = "깎아서 강함")·**코드 정본**(에이전트가 백로그 오류 코드 대비 정정: `cfoToNi`→`cfToNi`·`EnvironmentSnapshot` macroRegime 부재·`listing()` asOf 부재). 미구현부는 전부 design/졸업 AC/write-end 라이브 후 active 한계 라벨.

**잔여(=systemScore 빌드, planScore 갭 아님)**: 95 도달은 *설계*다 . 실제 구현(렌더러 2개·gate.py·ReportDock·mc.distribution·quality.baseline 노드·recordForecast write-end)은 09 §10 빌드티켓·_attempts 졸업 게이트 경유. write-end 라이브+held-out 데모(acceptance threshold) 후 design→proven 전환.

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

### 0c-20. 단계 0 바닥 수리 완료 (2026-07-07, 15 §4 이행)

- **수리 5건 + 실측 재판정**:
  ① _latticeOverlay 공분산 asOf 필터 (미래 매크로 격자 유입 차단) + PIT 회귀 테스트(미래 행 무영향).
  ② backtest 방향사전 trainWeekMax 배선 + **분할 기준 = 이벤트 커버리지 절반** (라벨 전체 기준이면 KR 이벤트(2022-11~)가 전부 OOS 라 train 공집합 = 방향사전 소멸 실측). 이벤트 표면은 OOS 주만 채점.
  ③ industryElasticity asOf 인자 (nested PIT. 덤 = 출력 정렬 결정론 정정: group_by 순회 순서 비결정 발견).
  ④ deathLabels: 절단 관측(상폐·장기정지) 보존. **실측 KR 580행/534종목, 절단 주 시장대비 평균 -13.4%p** = 숨어 있던 생존편향의 크기. corpAction 면제(죽음 자체가 채점 대상), uniMean 도 절단 포함.
  ⑤ kindList vintage 스냅샷 수집 개시 (변경일마다 corpListVintage/corpList_{date} 자동 축적, 소급 불가 자산).
- **공정 재판정 (OOS 분리 + 절단 포함 라벨)**: KR volShock t+8.95·ep t+3.06 인증 유지. **event.dilutionGovernance t+4.15(in-sample 확정) → t+2.95 OOS = 인증 강등(동물원구분불가)**. 방향은 양(+) 유지, 재인증은 라이브 누적의 몫. US 5종(발굴 2·인증 3) 전부 생존. tests 175 (신규 4).

### 0c-21. 단계 1 가격층 귀속 실측 = 층별 법칙 두께 계기판 (2026-07-07, 15 §5 이행)

- 주간 수익 3항 항등 분해 (모델 0, HR 동형: r = m + λ + ε) KR 600주 x 142만 관측, 2초. 항등 오차 1.1e-16 (기계 정밀도). 스크립트 = tests/_attempts/hierarchy/priceAttribution.py (gitignored, 수치가 정본).
- **층별 두께 (탑다운 통행증의 정직 한도)**: 시장층 = 종목 주간수익 시계열 R² 중앙 **15.2%**, 업종층 = 시장 차감 후 횡단면 분산의 **9.1%** (서브기간 8.6/9.8/9.1 = 안정), **고유층 ~75%**. 함의: 경제→산업 탑다운 채널이 나를 수 있는 것은 주간 변동의 ~1/4 이고, 나머지 3/4 은 회사 고유 = 레버·이벤트·재무 등 회사층 법칙의 관할 (회피 중심 설계의 정량 근거).
- **Gabaix granular 실증 (바텀업 "종목→경제 귀속")**: Herfindahl sqrt(Σw²) 중앙 0.186 (초집중 시장), Γ 주간 σ 1.94%p, **삼성전자 단독 |기여| = Γ 절대합의 47%**. 외부 앵커(순환 차단): **Γ(연합산) vs 수출 연변화 corr +0.69** (n=12년, 산업생산 +0.15·무역 -0.34). 대기업 고유충격이 실물(수출)과 동행 = 귀속 지도의 비순환 증거.
- 지도 생존편향 정량화: 현 스냅샷 업종맵의 과거 매칭률 2015 80% → 2026 92% (소급 12%p 열화. vintage 수집은 0c-20 에서 개시).
- 다음 = 15 §6 단계 2: multi-horizon 라벨 + hindcast.py (걸음수별 skill 곡선 = h* 실측).

### 0c-22. 단계 2 hindcast 시험장 = 첫 전개 면허 발급 (2026-07-07, 15 §6 이행)

- **신규 본진 1모듈 `hindcast.py`** (기획 승격 게이트 내 유일 허용 신규): fan(격자 스텝 분위 봉인·coverage/CRPS vs carry)·actualPath(origin vintage 베타 x 실현 경로 IC, nested PIT)·hStar(사전등록 규칙 hstar-v1, 곡선 통보고·셀 선별 금지). 선결재 = weeklyLabels horizonDays 일반화(5d 하드코딩 해제) + growLattice perStep 분포 캡처.
- **첫 h* 실측 (48 origins 2019~2026, 비중첩 8주 간격, 걸음 1~8)**:
  - 환경층: 4팩터 전부 cov90 이 [0.80, 1.00] 내 8걸음 완주 = **h*_env = 9 (관측 한계까지 유효)**. skill(carry 대비) fx 2.4~3.2x·oil 2.3~2.7x·rate10y 2.6~3.2x·rate 1.1~2.3x. 진단: cov50 은 장지평에서 0.35~0.5 로 명목(0.50) 하회 = 중앙 밴드가 좁은 편 (규칙 밖 진단, 커널 교차모멘트 보정 시 재검).
  - 회사층(actualPath, **조건부 = 실경로 가정 라벨 영구**): IC +0.048~+0.070, **t 전 걸음 +2.66~+4.26** = **h*_firm = 9**. 횡단면 평균 ~2,470종목.
- **판정**: 측정된 채널(매크로 분포 + 베타 반응)의 전개 면허 = 8주. 15 §7 walk 승격 게이트의 "h*>1 채널 증명" 충족 (잔여 = net 병기: IC 는 랭크라 비용 직결 아님, walk 의 결정 채점에서 비용바닥 차감으로 이행). fan 봉인 = issuedLive=False 기대 원장 합류 (스텝 분위, 멱등). tests 180 (신규 5)·fan 실행 15분/actualPath 2분.

### 0c-24. 거울 작업대(개념 #1 = 상태층) 완성 + 3중 적대감사 수렴 (2026-07-13)

시뮬레이터 4기둥(상태 x 법칙 x 개입 x 전개)의 **상태층**을 엔진 공개계약만으로 원점 재건. 옛 full.py
(table.py 내부리더·손10레인·손6계정) 폐기하고 거울 작업대(엔진 자기서술 반사 -> 물질화 -> 접기 -> 정규롱)
로 대체. 설계·판정 정본 = 18 문서.

**된 것 (DONE, 전부 green):**
- **작업대 기계 완성**: reflectAxes(loadCapabilities 소비, 손 축목록 0) -> materialize(공개계약 dartlab.
  {engine}("{axis}",item) 1회) -> foldToCanonical(shape family ~6 어댑터, 단일 정규롱) -> coverage 성적표
  + gap 원장. 자동흡수 = 새 축/계정 코드0(카탈로그 무target 전개), 새 엔진 손테이블2(_AXIS_REGISTRIES +
  _CALLABLE_MODULE_MAP, PR2 게이트가 회귀 감시).
- **5 PR**: PR1 declared 0->125/125(7c113f002) · 부채청산 skill산출물(3f9f3d625) · PR2 부채원장 게이트
  axisDeclaredCoverage(a955c9a5c) · PR3 순수커널 reference/capability/mirror.py L1.5(0cbaf1b89) · PR4 물질화
  드라이버 simulate/mirror.py L2.5(3aeac5bb2, simulate LAYERS L2 등록·workbenchPurity AST 가드).
- **청결 3라운드 = 버그 11 수정**: 1차 리뷰 4(3691d2e80) + 자가공격 1 캐시오염(bcf3c4b66) + 2차 리뷰 6
  (c8dafd4e5, ★치명=혼합dtype 프레임 unpivot String 승격으로 숫자 272,078개 소실) + 3차 리뷰 버그0 수렴
  (61e1b1044, inconsistency1+nit3 정리). 버그별 회귀테스트 전부 동행, 테스트 22 green.
- **실증**: KR 27,850,221행 정규롱(scan 계정860+비율13+17분석축 · quant 알파 · gather krx · macro), 정규
  스키마 (engine,axis,item,entity,entityName,period,value,valueText,lane,status,gapReason). 치명버그 수정
  전후 crossSection value(숫자) 724K->903K(문자로 죽었던 18만 되살아남). 사전빌드 0·Company 루프 0.
- **발명 3건 철회 확정**: laneHint·universeScope·guide extraColumns 는 returnType·stockRequired·_AxisEntry
  필드로 이미 존재. capability declared SSOT = builder._injectAxisRegistriesLive.

**해야 할 것 (TODO):**
- **★배선(최우선 결정 대기)**: 시나리오/E 엔진(estimate·hindcast·scenarioSim·scenarioTree·lattice·runweek·
  profile) **전부 table.py 소비, 워크벤치 0 소비** = 데이터 경로 이원. 작업대는 지어놨으나 시나리오가 아직
  안 씀. 결정: (1) 워크벤치를 시나리오 단일 상태원으로 통합(정공법, 기존 검증코드 배선 변경) vs (2) 이원
  공존(안전, 경로 영속 이원화). AI 판단 = 1번.
- **US(EDGAR) 물질화**: 커버리지 갭이지 기계 미완성 아님. 같은 작업대에 scan(...,market="us") 붙이면 자동
  흡수(edgar glob 17K파일 느려 KR 먼저 돌림).
- **나머지 3기둥**: 법칙 = hindcast h*=9 실측했으나 얇음(IC 0.05~0.07·고유75% 도달불가, 16 §6/§7) / 개입 =
  scenarioTree 탄성·SynthControl 설계만 / 전개 = walk.py 미빌드(16 §7 승격게이트).

**교훈(박제)**: 자평 "깨끗" 2회 틀림. 특히 27M "압도적 데이터"가 실제 오염(숫자 27만 소실)됐고 적대검증이
잡았지 내가 잡은 게 아님. 청결은 자평이 아니라 loop-until-dry 독립 적대검증이 답한다(3차 만에 버그0 수렴).
-> [[feedback_capability_over_honesty]] 반례가 아니라 실천: 갭을 검증으로 닫음.

### 0c-24. 실제 상태 전이와 paired 전략 비교 첫 수직절편 졸업 (2026-07-13)

- **전문 검토 3축 합의**: 설계, 계량, 적대 검토가 모두 현 4노드 경로를 "시뮬레이터"가 아니라
  단일 경로 시나리오 계산기로 판정했다. 핵심 결손은 명시적 `state(t) -> state(t+1)`, 개입 비용과
  지연, 동일 세계경로 위 전략 비교, 현금과 부채 피드백, 목적과 제약이었다.
- **개념확립 후 본진 승격**: `_attempts/worldEvolve`와 `_attempts/financialStep`,
  `_attempts/financialWorld`에서 킬테스트를 통과한 뒤 다음 3개 모듈을 졸업했다.
  - `simulate/world.py`: Variable, Action, Law, WorldState, ScenarioPath, Strategy, Constraint,
    Objective 계약과 다기간 전이, common path 전략 비교, step trace, Pareto, 재현 hash, 추천 gate.
  - `analysis/financial/stepProjection.py`: cash plug와 자동 차입이 없는 순수 1기간 재무 전이 leaf.
    현금, 부채, 이자, 운전자본, PPE, 자본이 매 기간 폐합된다.
  - `simulate/financialWorld.py`: 기존 `buildSnapshot`의 실제 재무 상태와 역사비율을 위 실행기에
    연결한다. CAPEX, 재고목표, 차입, 상환은 모두 명시 행동이다.
- **직접 증명**: 합성 세계에서 상태 피드백, 행동 lead time과 비용, 결측 차단, 동일 경로 비교,
  충격 지속기간에 따른 전략 순위 역전을 통과했다. 미검증 법칙이 하나라도 있으면 결과를
  `conditionalOnly`로 낮추고 자동 추천은 `None`으로 막는다.
- **실데이터 수직 스모크**: 삼성전자 2026-Q1 snapshot을 매출 388.3조원, 현금 73.3조원, 부채
  26.9조원의 초기 상태로 컴파일해 2개 경로, 2개 전략, 4기간을 전개했다. 최대 회계 상대잔차
  `2.1e-16`, 제약 오탐 0, 결과는 `conditionalOnly`, 추천 `None`이다. capacity headroom 20%와
  역사비율 경고는 assumptions에 남는다.
- **동반 결정론 수리**: `weeklyLabels`의 미래 기업행동 창이 종목 경계를 넘던 window shift를
  시장달력 self-join으로 교체했다. 격자 `hardenedTopK`의 동률 순서도 하방값, 기저점수, 종목코드
  보조키로 고정했다.
- **검증**: 신규 집중 21 통과, simulate와 신규 analysis leaf 전체 221 통과, ruff clean,
  Guard Index strict l0-l15 7/7과 외부게이트 6종 통과, public API coverage와 product smoke quick 통과.
- **정직한 잔여**: 확률 경로 생성과 calibration, filing revision vintage PIT, transition edge의
  hindcast admission, EDGAR 실제 회사 수직절편, closed-loop 정책, UI는 아직 미구현이다. 현재 성취는
  "진짜로 걷는 실행기와 KR 1사 연결"이지, 검증된 최적전략이나 예측확률의 완성이 아니다.

### 0c-30. 관측 상태 기반 폐루프 정책과 compact 대량경로 실행 (2026-07-13)

- **폐루프 정책 수직절편**: `StrategySpec`가 고정 행동 일정뿐 아니라 version과 provenance가 있는
  `policyFn`을 가질 수 있다. 정책 입력은 현재 step, 직전 기간까지 관측된 state와 직전 발행 행동뿐이다.
  현재 기간 shock, path 객체, 미래 결과는 구조적으로 전달하지 않는다. 같은 정책도 1기 수요가 달랐다면
  2기 재고 또는 투자 행동을 다르게 낼 수 있어, 사전에 고정한 전략표 비교를 넘어 feedback control을
  표현한다.
- **행동 지연 정합**: lead step이 있는 행동은 고정 schedule을 다시 읽지 않고 정책이 실제로 발행한
  action history에서 유효 행동을 찾는다. 정책 출력도 정적 전략과 같은 action id, finite, bounds 계약으로
  매 step 검증한다. 정책 함수와 version은 executable hash에 들어가고 각 path trace에 version과
  provenance가 남는다.
- **bounded-memory 실행**: `traceLimit`을 지정하면 전체 `strategy x path` trace를 반환 메모리에 쌓지
  않는다. 한 trace씩 전개해 평균과 worst 목적값 및 위반 수를 온라인 집계하고, 모든 trace는 순서가
  결속된 chain root에 포함한다. 따라서 compact와 full 실행은 같은 전체 `traceRoot`와 수치적으로 같은
  집계 목적값을 가지며, 반환 trace와 path별 objective 배열만 지정 상한으로 줄어든다. 결과에는 전체와
  보존 trace 수를 함께 기록한다.
- **exact compact CVaR**: compact 실행의 경로 목적값과 가중치만 OS 관리 임시 SQLite 파일로 흘리고,
  `(value, ordinal)` 인덱스 순서로 낮은 꼬리 질량을 읽어 full 실행과 같은 weighted CVaR을 계산한다.
  path trace와 path별 목적 배열은 메모리에 보존하지 않으며 집계 뒤 임시 연결을 닫는다. 근사 분위로
  대체하지 않는다. 대표 trace의 stratified retention, 정책 admission과 OOS 평가 인증은 후속이다.
- **메모리 실측**: 1,000 경로 x 2 전략 x 12기간, exact CVaR 10% 조건에서 Python tracemalloc
  실행 피크는 full 51.26MiB, compact 4.44MiB로 11.56배 감소했다. 전체 trace 2,000개 중 8개만
  보존했고 CVaR score는 1e-12 이내 동일했다. 이는 반환 trace 상한과 disk spill이 실제 메모리
  증가율을 끊는다는 수직절편이며, 더 큰 회사 재무 law 묶음의 처리량 benchmark는 후속이다.
- **검증**: `_attempts/closedLoopPolicy` 2건과 `_attempts/boundedWorldExecution` 2건을 먼저 통과시킨 뒤
  본진에 폐루프 반응, 현재 shock 비가시성, 실제 발행 행동의 lead 적용, 정책 executable hash,
  compact 집계와 전체 trace root 동일성, disk-spill exact CVaR 회귀를 승격했다.

### 0c-31. 경로 측도와 재무 브리지 PIT 결속 (2026-07-13)

- **전문 검토 3축 판정**: 현 fail-closed 정책 추천은 유지해야 한다. 자동 추천의 최소 계약은 동일 경로와
  동일 parameter draw를 공유한 baseline 1개와 candidate 1개의 시간순 OOS paired 비교이며, primary 평균
  목적의 경제적 유의한 하한, secondary weighted-CVaR 비열등, hard constraint를 원시 episode 원장에서
  재계산해야 한다. simulation path 수는 OOS origin 수가 아니며 caller가 적은 요약행이나 SHA digest는
  권한 증명이 아니다.
- **경로 인증 PIT 봉합**: `PathMeasureCertificate`가 `nOrigins`, `minOrigins`, coverage 허용오차,
  calibration hash, 규칙, 실제 지식 기준일과 이력 상태를 모두 digest에 보존한다. 발급 증거는
  `availableAt <= knowledgeAsOf`이고 요청한 history status와 일치해야 하며, 실행기는 digest와 exact cutoff를
  다시 계산한다. 인증서 field 변조, 다른 cutoff 재사용, 미래 또는 revised 증거의 as-known 승격 kill-test를
  본진에 승격했다.
- **날짜 우회 차단**: `WorldState`의 회계기간 `asOf`와 실제 `knowledgeAsOf`를 분리했다. admitted 법칙이나
  경로는 비교 가능한 초기 지식 기준일이 필수이고, 경로 자체도 `knowledgeAsOf`와 `asKnown` 이력을
  content hash에 포함한다. 따라서 `2024-Q4` 같은 fiscal label로 미래 법칙 인증서 검사를 건너뛸 수 없다.
- **재무 브리지 결속**: bridge 실행 초기 상태와 출력 경로에 source cutoff와 history status를 전파한다.
  결합 인증 hash와 audit에는 source certificate뿐 아니라 source path content hash, 빈티지, 시간격자와
  horizon을 포함한다. 2020 source 경로에 2025 법칙 인증을 끼우는 입력은 실행 전에 거부된다.
- **검증**: simulate 전체 267 통과, ruff clean, Guard Index strict L0-L1.5 7/7과 외부 gate 6종 통과.
- **정직한 잔여**: typed issuer와 append-only OOS episode 원장, parameter distribution 빈티지,
  paired block-bootstrap 정책 인증이 아직 없다. 이 셋이 완성되기 전에는 policy recommendation gate를
  열지 않는다. DART period-only/latest-retained와 EDGAR as-known의 provider-neutral `VintageRef` 결속도
  다음 단계다.

### 0c-29. 분기 전이, 파라미터 불확실성, 실행 인증 P0 보강 (2026-07-13)

- **전문가 재감사 결론**: 경로모형, DART와 EDGAR PIT, admission 적대검토에서 분기 grid에 연간
  파라미터를 네 번 적용할 위험, AAPL commercial paper 누락, 호출자가 성공 여부를 적은 증거행,
  인증 뒤 전역값 변경, 인증서와 실제 path 내용의 분리, 정책효과 인증 부재인데도 추천 가능한 계약을
  P0로 확인했다. 현재 실현 가능성은 높지만, 검증기와 예측기를 넘어서 의사결정 시뮬레이터가 되려면
  이 경계를 먼저 닫아야 한다는 판정이다.
- **분기 상태 졸업**: `compileEdgarQuarterlyFinancialState`가 최신 단독 분기 흐름을 상태 규모로 쓰고,
  네 개 연속 분기와 TTM 보조값을 함께 보존한다. 최근 날짜 네 개를 기계적으로 고르지 않고
  `fiscalThrough`에서 역으로 같은 재무 캘린더의 연속 구간을 찾는다. Q4는 직접 보고값을 우선하고,
  없으면 같은 연차보고서 cutoff 안의 FY-9M 잔차를 우선 사용하며, 마지막으로 FY-Q1-Q2-Q3를 쓴다.
  모든 파생값은 accession, tag, 기간의 입력 lineage를 남긴다.
- **시간단위 계약**: financial world, path, transition parameter에 frequency와 step span을 결속했다.
  연간 파라미터를 분기 world에 넣으면 실행 전에 차단하고, 단위도 성장률, 마진 증분, 금리를
  `perStep`으로 명시했다. 분기 파라미터를 명시한 경우에만 분기 상태와 분기 경로가 전개된다.
- **파라미터 불확실성 수직절편**: `ScenarioPath.parameterDraws`가 세율, 감가상각률, 운전자본 비율,
  생산능력 계수 등 선언된 전이 파라미터의 경로별 고정 추첨값을 보존한다. 한 경로의 값은 전 기간과
  모든 전략에 공통으로 적용돼 common random numbers 비교를 유지한다. 미선언 파라미터는 차단하고,
  실제 추첨값을 law trace, parameter hash, data vintage hash, admitted path content hash에 포함한다.
  현재는 외부에서 구성한 joint draw를 소비하는 단계이며 분포 추정과 draw generator 인증은 잔여다.
- **인증 P0 보강**: law evidence의 `passed` 주장을 신뢰하지 않고 수치와 연산자로 재계산한다. 인증서가
  model frequency와 맞지 않거나 initial state보다 미래 정보이거나, 인증 뒤 closure 또는 참조 전역값이
  바뀌면 실행 시점 재검증에서 차단한다. admitted path는 실제 shock, weight, 시간계약,
  parameter draw 전체의 content hash가 일치해야 한다. bridge 출력도 변환 결과 내용에 다시 결속한다.
- **추천 fail-closed**: 임의 64자리 action digest는 정책 효과 검증이 아니다. typed
  `PolicyEvaluationCertificate`가 생기기 전까지 자동 추천은 전부 비활성이고, 결과는
  `conditionalOnly`와 Pareto 비교까지만 허용한다.
- **실데이터 대조**: AAPL 2026-03-28 filing-vintage에서 최신 분기 매출 111.184B USD,
  TTM 매출 451.442B, 분기 영업이익 35.885B를 확인했다. 기존 부채 82.714B는 commercial paper
  1.997B 누락이었고, current와 noncurrent term debt에 이를 비중복 합산한 84.711B로 정정했다.
- **검증과 정직한 잔여**: parameter uncertainty attempt 2건과 quarterly attempt 2건을 선결한 뒤
  본진 회귀로 승격했고 `tests/simulate` 259건이 통과했다. DART 과거 revision PIT는 append-only
  접수 원장 없이는 여전히 불가능하다. joint parameter distribution의 OOS 인증, bounded-memory 대량
  경로, 관측에 따른 closed-loop policy, typed policy certificate, 공개 verb와 GUI는 다음 단계다.

### 0c-28. 연간 거시경로에서 회사 재무충격까지 인증 브리지 졸업 (2026-07-13)

- **빈 중간법칙 수리**: financial world는 수요 성장, 마진 증분, 차입금리를 사람이 직접 넣어야 했다.
  `simulate/financialBridge.py`가 명시 단위의 연간 거시 혁신을 회사별 demand log-growth,
  margin point-change, debt-rate change 계수로 옮긴다. 차입금리는 이전 기간 수준에 증분을 누적한다.
- **동일 실행기 재사용**: 브리지는 별도 계산 우회가 아니라 `LawSpec`과 `WorldModel`로 컴파일되고
  `simulateWorld`에서 실행된다. 따라서 선언 입력만 읽고 함수, 파라미터, 증거, 지평 인증을 기존
  세계 실행기와 동일하게 적용하며 결과를 `demandGrowth`, `marginChange`, `debtRate` path로 만든다.
- **승격 전파**: source macro path와 bridge law가 모두 admitted일 때만 두 인증서를 묶은 새
  certificate를 발급한다. bridge가 explicit assumption이면 admitted source도 `retrospectiveOnly`로
  강등한다. 주간 macro path를 연간 financial bridge에 넣으면 step contract에서 즉시 차단한다.
- **end-to-end**: 합성 연간 GDP와 금리 경로가 회사 재무 충격으로 변환되고, 그 경로가 잠재수요,
  생산능력, 손익, 현금, 부채 상태를 두 기간 전개하면서 매 기간 balance identity를 닫는 수직절편을
  본진 테스트로 고정했다.
- **검증**: `_attempts/financialBridge` 4건은 변경 전 collection 실패, 변경 후 4건 통과했다.
  본진 5건으로 승격했고 simulate 전체와 재무 leaf 255건, ruff, Guard Index strict L0-L1.5 7/7과
  외부 gate 6종이 통과했다.

### 0c-27. 전이법칙 인증서를 실행물과 검증지평에 바인딩 (2026-07-13)

- **임의 digest 반례 선결**: 기존 `LawSpec.certificateId`는 64자리 문자열이면 통과해 실제 함수,
  입력과 출력 계약, 파라미터, 검증자료와 무관했다. `_attempts/lawCertificateBinding`에서 임의 digest,
  인증 후 파라미터 바꿔치기, 검증지평 초과, revised history의 active 승격 4건을 먼저 실패시켰다.
- **실행물 결속**: `LawCertificate`가 law id와 version, evidence kind, 입출력과 action 계약 hash,
  parameter hash, 함수 bytecode와 closure hash, 검증행 hash, knowledge cutoff, history status, 연속 통과
  `maxAdmittedStep`, 규칙을 하나의 `certificateId`로 묶는다. digest와 실제 법칙을 모두 재계산해 비교한다.
- **승격 규율**: `measuredAssociation`과 `identifiedIntervention` 법칙은 인증서 없이는 컴파일되지 않는다.
  active 또는 identified 법칙은 `asKnown` 증거의 전 걸음 통과로 발급된 admitted 인증서만 허용한다.
  revised history는 `retrospectiveOnly`와 partial law까지만 가능하고 rejected는 blocked만 가능하다.
- **실행 지평 차단**: path 자체의 admitted horizon과 별개로 모든 admitted law의
  `maxAdmittedStep`을 검사한다. 경로가 길어도 회사 전이법칙이 두 걸음만 검증됐다면 세 번째 걸음은
  실행 전에 차단된다. 각 `LawTrace`에는 실제 certificate id가 남는다.
- **검증**: `_attempts` 4건은 변경 전 collection 실패, 변경 후 4건 통과했다. 본진 회귀 4건을
  승격했고 simulate 전체와 재무 leaf 250건, ruff, Guard Index strict L0-L1.5 7/7과 외부 gate
  6종이 통과했다.

### 0c-26. 잠재수요 상태와 마진 충격 의미 정식화 (2026-07-13)

- **죽은 수요 반례 선결**: 기존 전이는 생산능력에 막힌 실현 매출을 다음 기간 수요의 기준으로 다시
  사용했다. 따라서 수요 150, 생산능력 110인 세계에서 40의 미충족 수요가 사라졌고, 증설해도 이를
  회수할 수 없었다. `_attempts/financialStateDynamics` 4건이 이 결함과 `marginDelta` 의미 모호성을
  먼저 재현했다.
- **상태 전이 정정**: `FinancialState`에 회계상 매출과 별개인 `latentDemandRevenue`를 추가했다.
  수요 성장은 잠재수요에 적용하고 실현 매출은 `min(잠재수요, 생산능력)`으로 정한다. 다음 기간에도
  잠재수요를 보존하며 `unmetDemand`를 trace에 노출한다. 잠재수요는 비회계 상태라 balance identity에는
  넣지 않는다.
- **전략 의미 복구**: 생산능력 제약 기간의 capex는 당기 매출을 소급 변경하지 않지만, 다음 기간
  생산능력을 높여 보존된 미충족 수요를 실제 매출로 전환한다. 따라서 증설 전략의 효과가 단순 PPE
  증가가 아니라 수요 회수, 운전자본, 현금, 이익의 연쇄 전이로 나타난다.
- **마진 의미 고정**: `marginDelta`를 `marginChange`로 바꾸고 단위를 `ratioPointChangePerYear`로
  명시했다. 값은 절대 마진 수준이 아니라 직전 기간 대비 가산 증분이다. financial world와 law 버전을
  2로 올려 이전 실행과 같은 executable hash를 만들 수 없게 했다.
- **검증**: `_attempts` 4건은 변경 전 4건 실패, 변경 후 4건 통과했다. 본진 leaf에는 잠재수요 보존,
  증설 후 회수, 기간별 마진 증분, 음수 잠재수요 차단 회귀를 승격했다. simulate 전체와 재무 leaf
  246건, ruff, Guard Index strict L0-L1.5 7/7과 외부 gate 6종이 통과했다.

### 0c-25. 실행 신뢰경계 봉인, 공동 경험경로, EDGAR filing-vintage 상태 졸업 (2026-07-13)

- **전문가 3축 재감사**: 경로 계량, DART와 EDGAR PIT, 실행기 적대 검토를 독립 수행했다. 선언하지
  않은 충격과 발행 직후 행동을 법칙이 몰래 읽는 우회, 함수와 파라미터가 달라도 같은 run hash,
  인증서 없는 calibrated probability, 다목적 첫 목적 강제추천, 연간 TTM 상태와 주간 경로의 시간단위
  혼합이 실제 반례로 재현됐다.
- **실행 신뢰경계 수리**: `simulate/world.py`가 법칙별 선언 입력만 immutable context로 노출하고
  `issuedActions` 우회를 차단한다. 입력과 trace mapping을 깊은 복사 후 읽기전용으로 만들었다.
  `runHash`, `executableHash`, `parameterHash`, `dataVintageHash`, `resultHash`, `traceRoot`를 분리했고,
  law version과 parameter snapshot을 trace에 남긴다. identified intervention과 admitted path는 64자리
  certificate digest가 없으면 컴파일되지 않는다. NaN과 Inf weight, bounds, threshold도 차단한다.
- **추천 과장 차단**: 모든 path가 admitted가 아니면 `conditionalOnly`다. 단일 전략이나 baseline 없는
  비교는 추천할 수 없고, scalarization 없는 다목적은 `paretoOnly`가 상한이다. bootstrap 경로는
  `calibratedProbability`가 아니라 `empiricalResamplingMeasure`로 표기한다.
- **공동 경험경로 졸업**: `_attempts/empiricalWorldPaths`에서 prefix PIT, 공동행 보존, 블록 인접성,
  seed와 행순서 결정론, path count 확대 prefix, 표본부족 기권, h* 시간단위 결속을 증명한 뒤
  `simulate/empiricalPaths.py`와 `macroPaths.py`로 승격했다. `eventTime`과 `availableAt`, 변수 단위,
  frequency와 stepSpan을 필수로 둔다. 현재 macro 저장소는 release vintage가 없어 실제 4팩터 주간
  경로도 `revisedHistory`, `retrospectiveOnly`다.
- **h* 의미 정정**: 첫 실패 걸음을 그대로 면허라고 부르지 않고 마지막 전구간 통과 걸음인
  `maxAdmittedStep`으로 저장한다. 각 걸음에서 모든 필수 팩터가 표본수, 90% coverage, CRPS의 carry
  우월을 동시에 통과해야 한다. 기존 8주 거시 h*는 연간 TTM financial world에 재사용할 수 없다.
- **EDGAR as-known 상태 컴파일러 졸업**: `_attempts/edgarPitState`에서 original과 amendment cutoff,
  미래공시 append 불변, Net PPE 우선, debt total과 components 배타성, 동일 accession과 fiscal end,
  unit 충돌, balance closure를 증명한 뒤 `simulate/edgarPitState.py`로 승격했다. raw companyfacts를
  tag 선택 전 `filed <= knowledgeAsOf`로 자르고, stock 전 계정을 동일 accession에서 고르며,
  standalone 3분기와 FY residual로 Q4를 복원해 TTM을 만든다. 모든 값에 filedAt, accession, form,
  tag, unit, fiscal start와 end, observed 또는 derived 상태를 보존한다.
- **AAPL 실제 수직절편**: 2025-02-01 cutoff는 fiscalThrough 2024-12-28, 2026-07-13 cutoff는
  2026-03-28로 서로 다른 state hash와 accession을 만들었다. 최신 상태는 TTM 매출 451.442B USD,
  영업마진 32.64%, 현금 45.572B, 부채 82.714B, Net PPE 50.116B, 자본 106.491B다. 이를 연간
  재무 전이에 투입해 회계 폐합을 확인했지만 transition parameter가 명시 가정이므로 결과는
  `conditionalOnly`, 추천 `None`이다.
- **DART 정직성 강화**: snapshot의 assumption과 `periodScopedPitOnly` 경고가 최종 run까지 전달된다.
  debt 구성요소 일부 누락을 0으로 합산하지 않고 차단한다. 삼성전자 실제 수직절편은 계속 통과한다.
- **검증**: simulate 전체와 재무 전이 leaf 243건 통과, ruff clean, Guard Index strict L0-L1.5
  7/7과 외부 gate 6종 통과, public API coverage와 memory budget, product smoke quick 4종 통과.
- **정직한 잔여**: 현재 경험경로와 financial world 사이의 회사별 shock bridge는 admission이 없어
  연결하지 않았다. DART 과거 revision은 append-only 접수원장 없이는 복원 불가다. 금융 전이의
  잠재수요 상태, 분기 native 전이, law별 식별 certificate, parameter uncertainty, closed-loop 정책,
  bounded-memory 대량경로 실행, 공개 verb 교체, GUI는 후속이다.

### 0c-23. 네이티브 시그니처 C vs D 첫 실측 = "직독 마법" 기각, 상태조건 신호만 생존 (2026-07-07, 16 §7 결정적 실험 착수)

- **데모 (_attempts/nativejoint/cvsd.py, 개념확립 stage2)**: 세 앙상블의 per-company 주변분포를 완전동일 고정하고 결합구조만 상이하게 = variogram(결합민감 적정스코어)이 결합종속만 순수 격리. C=상태 analog 코호트 동시실현 직독, Dg=같은 주변+Gaussian copula, Ds=같은 주변+무조건 empirical copula. 우주=전기간 풀커버 상위시총 40종목(600주), origin 비중첩, 블록부트 t(자기상관 보정).
- **결과 (C우월 블록부트 t)**:
  - **C 대 Dg(비가우시안 꼬리) = 전 지표·전 지평 무신호** (variogram t -0.8~+0.2, 포트꼬리 t -1.2~+1.1, 동반붕괴 t 0.0~1.9). 동조건 Gaussian copula 가 실제 결합과 동점 = **"직독 not 재구성"·비가우시안 꼬리 주장 기각** (심사 예언 "가우시안화하면 사라짐" 실측 확인).
  - **C 대 Ds(무조건 재구성) = 상태조건 신호만 생존**: variogram t **+4.48(h1)·+3.02(h4)**·+2.37(h8), 동반붕괴 t +2.79(h1). 단 결정지표(포트꼬리) t~1 미달, 동반붕괴도 h4/h8 무신호.
- **판정**: 마법(직독)은 기각. 생존한 것 = **상태/레짐 조건부 회사간 결합종속 추정**(전수 동시성 substrate 가 같은 상태 공동실현을 충분히 줘 조건부 결합을 잰다). 실재하나(variogram t>3) 16 §7 시그니처 바(결정지표 t>3 집중) 미달 = **integration-grade**(Defend 층 CVaR/DRO 앙상블에 레짐조건 결합으로 편입할 자산이지 독립 시그니처 아님).
- **미검 잔여 (기각 범위 한정)**: 수익 대리·대형주 한정. 지급능력(자산-부채) 벡터·소형/부실 우주(꼬리 동반이 강한 곳)는 미측정 = 다른 문(졸업 refinement). 첫 read 이지 production certify 아님. survivorship(풀커버 선정)은 세 앙상블 공통이라 차이 C-D 는 덜 오염.

### 0c-19. 사상 바닥 확정 + 차기 기획 (2026-07-07, 운영자·AI 토론 + 패널 2회)

- **본질 재정의**: 시뮬레이터 = 상태 x 법칙 x 개입 x 시간 전개. 현 엔진 = 시뮬레이터가 아니라 검증 기반(정직 판정). 운영자 개념(출처별 원포맷 A+E 시계열·바텀업 귀속/탑다운 분해 하나의 지도·가정을 가보고 온다·재예보 검증) = 목적지 판정 (근거 3: 본질 충족·세계 수렴·패널 적대검증 생존). 속도 제한 = 전개 깊이 ∝ 측정된 법칙 두께 (기계화 = hindcast h*).
- 격자 3렌즈 검증(wf_afb6c135): 말단 리스크 오버레이 부품 강등 + 실결함 2(커널 교차모멘트 ~40% 감쇠·3^k 스케일이 팩터 자동흡수와 충돌). 기획 패널 7인(wf_dda7e79d): 설계 5렌즈 + 레드팀이 바닥 오염 4건 실증 (backtest 방향사전 in-sample·라벨 생존편향·격자 공분산 look-ahead·탄성 vintage 부재).
- **정본**: 15-walker-hindcast-plan.md (실행: 수리→귀속→hindcast, 승격 게이트) + 16-simulator-foundation.md (사상 바닥·죽은 가설 재론 금지 목록). 다음 착수 = 15 §4 바닥 수리 4건 (운영자 승인 대기). 보류: 통합 작업대 조회 뷰 초안(코드 미커밋 폐기, 개념은 15 §1 에 기록).

### 0c-18. US 라이브 루프 완성 = 전상장사(DART+EDGAR) 주간 사이클 (2026-07-07)

- **시장 무구분 원장 결함 2 (첫 US 라이브 시도가 실측으로 노출)**: ① readReadings 가 market 무필터라 KR 봉인이 US 같은 주 발행을 막고 보드가 KR 판독을 집음 ② 블록 파일명 `block_{week}` 시장 충돌. 정정 = readReadings(market) 필터·발행/보드/스프레드 시장 스코프·블록 `block_{market}_{week}` 시장별 독립 해시체인 (기존 KR 블록 rename 마이그레이션). 가드 테스트 = 같은 주 KR/US 독립 봉인.
- **US 베타·격자**: macroBetaByCodeWide 에 가격 주입(prices) 파라미터 = 글로벌 매크로(유가·rate10y 등) x US 가격상 → 격자 오버레이 시장 파라미터화 (KR 전용 게이트 해제) + profileAll US 베타 축 자동 등장.
- **실측**: US 202625~202626 발행 66,791+69,270행 x 11표면(US 레버 insiderCluster·lockupExpiry + credit=securitiesOffering + estimate.epFwd), 격자 오버레이 각 10종목 제거, **US 첫 라이브 채점 11,963행** (lockupExpiry +364bp n=65·high52 +211bp·ep +189bp / ret5 -51bp). tests 171 (신규 1)·가드 7/7.
- 운영자 개념 전제("전상장사 = DART + EDGAR") 라이브 충족: 이제 KR·US 모두 주간 한 방 자가 순환. 잔여 = US 업종맵(SIC 로컬 부재 실측, EDGAR submissions 별도 수집 필요 = 외부 데이터 항목)·US 가격 최신화(6/29, edgarPricesDaily CI 가 채움).

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
    - **치명 신규 ① models HF 배포 경로 0건** . pre-fit 적합이 `~/.dartlab/`(ephemeral)에만 저장돼 cron 켜도 소비처 영구 None. DATA_RELEASES 'models' 1줄 + `data/models/` 리다이렉트 + `_uploadModels`가 전체 배선의 load-bearing. 02 §2B.5.
    - **치명 신규 ② scanMacroBeta firm-level t-stat 수학적 부재** (연간 N=3, df=N−k≤−1). "N~13 기술"이 한 단계 더 낙관 → firmRefine은 t-stat 게이트 *계산 금지*(pooled에서만 valid), leave-last-k hitrate만. 01 §1 #7·02 §2B.1·§2B.9. **★:205 버그 수정 제안 `*=`도 틀림**(평균경로 소실) . per-year 성장계수 cumprod, 단 kill-test로 '기존이 버그'임 먼저 증명. 01 §12.

---

## 2. 작성 문서 + 상태

| 문서 | 상태 | 비고 |
|---|---|---|
| README | ✅ v0.2 | 문서지도·L2.5 정정 (06 v0.3 반영 1줄 갱신 필요) |
| 00-product-prd | ⏳ v0.1 잔재 | §6 5-pane 화면 토폴로지 → ✅ v0.4 정정 박스 적용(terminal-host 흡수, 별도 셸 0); 잔여 = §5 "Scenario Workbench" 제품명 sync |
| 01-engine-architecture | ✅ v0.3 | §5 노드 3중좌표·§6 NodeValue/실행기/gate/grounding·§12 byte-parity+:205 수식정정·§13b 격자구조·§1 #7(scanMacroBeta N=3) 심화 |
| 02-assumption-method | ✅ v0.3 | mode enum 본문 통일(replay/walkforward/whatif)·§2B.7 end-to-end 데이터배선·§2B.8 수렴증명·§2B.9 tier가드·§2B.10 스키마가드·§2B.5 models HF 배포 갭(치명) |
| 03-validation-ai-review | ✅ v0.3 | §9.3 발간 게이팅 반영(헤더 정본)·fatal① lint 빌드 정합(§4 #9) |
| 04-progress-ledger | ✅ v0.3 (본 문서) | . |
| 08-valuation-report | ✅ v0.4 | 가치평가 융합·발간 계약(코어 졸업 후)·fatal① lint 빌드 정합(발간표면 한정) |
| 09-architecture-consolidation | ✅ v0.3 | 부채 원장·앵커·신용 뷰·Phase 시퀀스·§10 4 fatal 빌드티켓(①✅ 빌드·배선) |
| 05-play-future-replay | ✅ v0.3 | ★중심 산출물. fan-band None구간 끊기·byte-parity 범위 명시 |
| 07-integration-roadmap | ✅ v0.3 | **cross-category 브리지로 전환**(차트 suite ⟶ 시뮬 단방향 시퀀싱·공유 DNA·미래마커 이관) |
| → 06/10/11 **분리** | ✅ 이동 | **`../_done/terminal-chart-suite/`로 git mv**(06→01 차트·11→02 레일·10→03 백테스팅). 번호 공백(00-05/07-09) 유지=cross-ref 안정. 상세 = suite README·07 브리지·§4(14) |

---

## 3. ★워크스페이스 변동 (이 세션 중 실측 . 중요)

mainPlan UI 플랫폼 리팩토링이 **이 세션 동안** 단계-4b~5-2b로 진척(git log 오늘). 핵심:
- **터미널 전체 이동**: `landing/src/lib/terminal/` → **`ui/packages/surfaces/src/terminal/`**(commit `ff9099ba0` "data/→lib/ git mv"). `landing`엔 `terminal-shell/{routeLoad,terminalShell}.ts`만 잔존.
- **결과**: PRD의 모든 `landing/.../terminal/...` UI 경로 stale. 새 SSOT = `ui/packages/surfaces/src/terminal/`(charts/PriceChart.svelte·chartState.svelte.ts 실재) + 포트 `ui/packages/contracts` + 런타임 `ui/packages/runtime`. 엔진 경로(`src/dartlab/*`)는 불변.
- **함의**: PRD가 "mainPlan 이후 착수"라며 가정한 post-refactor 토폴로지가 *조기 도래*. 05(Play)·06(지수)는 새 토폴로지로 재기반 필수. `chartState.svelte.ts` 실재 확인 → README "replay 상태기계 재사용" 옳음, 08 "부재" 정정 대상.
- ui/apps/local SvelteKit 앱 신설(단계-5), createLocalRuntime AiPort SSE 배선(단계-5-2b) . 로컬 고급 엔진 경로 진행 중.
- **★v0.3 워크플로 코드-그라운드 확정**: 정본 = `ui/packages/surfaces/src/terminal/charts/PriceChart.svelte`(klinecharts 1051줄). `ChartCtl`은 PriceChart **내부** 생성(`new ChartCtl` 1곳, setContext 0건) → CenterStack은 ctl 모름 ⟹ 06 v0.2 "ctl.subject 분기"는 컴파일 불가, 정정=CenterStack-local `$state`(06 §2.5). soft-swap은 실재하나 *회사 전환 전용*. replay 상태기계는 *과거 backward-only*(미래 sim.play 필드 신설 필요). 미래여백 0은 *무조건 적용*(05 §2 live 분기 신설 필요). PricePort 실제 메서드 = initial/older/loaded/govCandles/govRecent(PRD `indexInitial` 발명 폐기). `ui/shared/chart/PriceChart.svelte`는 별개 SVG 컴포넌트(혼동 금지).

---

## 4. NEXT . PRD 닫기 체크리스트 (v0.3 갱신)

### ✅ 완료 (v0.2→v0.3)
1. ~~05-play-future-replay.md~~ ✅ . ★중심 산출물 작성(v0.3 fan-band None구간 끊기 포함).
2. ~~06-index-chart.md~~ ✅ . v0.3 전면 대체(subject 소유권 seam·IndexPort catalog/search/series·US 부재 가드). **→ 2026-06-14 `_done/terminal-chart-suite/01-price-index-chart.md`로 분리(§4 #14).**
3. ~~07-integration-roadmap.md~~ ✅ . 시퀀스·의존성·Phase.
4. ~~02 mode enum 통일~~ ✅ . 본문 §2.3·§3.1 → `replay/walkforward/whatif` SSOT 단일.
5. ~~01 §1/§5/§6/§12/§13b 심화~~ ✅ . v0.3 워크플로(노드 3중좌표·NodeValue/실행기/gate·byte-parity·격자·N=3 #7).
6. ~~02 §2B 심화~~ ✅ . §2B.7 데이터배선·§2B.8 수렴증명·§2B.9 tier가드·§2B.10 스키마가드·§2B.5 models 배포 갭.
7. ~~06 OQ12(US 지수)~~ ✅ . 운영자 결정=FRED 채택, 종가 라인 subject로 06 v0.4 통합. FRED 데이터 라이브 실측(SP500/NASDAQ/다우/VIX 4종)·종가전용 지표 3분기 매트릭스·candleStyle 격리. 잔여=구현만.

### 🔨 엔진 착수 . L2.5 `simulate/` (P1 ①② 완료 후 다음, execution-ready scope 2026-06-14)
> ⚠ **이건 대형 engine-add . 신선한 집중 + dartlabGuard 선행 필수**(master-red 교훈: 아키텍처 변경 rush 금지). `.claude/skills/engine-add` 절차 동반.

✅ **개념검증 + foundation 졸업 완료(2026-06-14)** . ★layer subtlety 는 **§10 born-clean 으로 해소**(아래 "1." 의 a/b/c 고민 불필요): simulate/ 는 *소비처 0 신생, 기존 simulation.py 무접촉* → transfer 는 L2.5 에 새로 태어나고(synth L1.5 상수만 forward import) legacy `_applyMacroShock` 잔존(§4 move 는 L2→L2.5 역방향이라 *회피*, BC 위임은 성숙 후 별도). 
  - `_attempts/scenarioSimulate/` 개념검증 PASS(born-clean DAG·transfer byte-identical·buildProforma leaf·결정론).
  - **본진 `src/dartlab/simulate/` 졸업**: `sheet.py`(NodeValue/DriverNode/DriverSheet+computeInputsHash+buildOrder Kahn+evaluateSheet, lens 심볼 부재=invariant-1) + `transfer.py`(transferMacroToFundamentals/transferRevenuePath). LAYER_OF simulate:2.5 등록(indexer.py+test_import_direction.py, downward-only). 검증: dartlabGuard exit 0·22 테스트·9섹션 docstring·born-clean.
  - ✅ **deterministic core 졸업(2026-06-14, `096e84c43`)**: `registry.py`(buildSnapshot read-once + 4 노드 _fnMacroPath/_fnRevPath/_fnProforma/_fnDcf . ★dcf=proforma FCF 기반 FCFF 폴백, `calcDFV` 아님[calcDFV 는 외부 proforma 무시 → scenario-coherence 깨짐]) + `run.py`(runScenario→SimulationResult+NodeAudit). 4노드 DAG end-to-end·32 테스트·dartlabGuard exit 0·결정론.
  - ✅ **공개 verb 졸업(2026-06-14, `ac3905fd9`)**: `simulate/entry.py`(톱레벨 `dartlab.simulate(code, *, scenario, horizon, asOf)` thin wrapper, KR 전용 가드=market!='KR', 9섹션) + `Company.simulate(...)` 메서드 + `__init__.py` lazy map+`__all__`+callable-module 충돌 패치(서브패키지=verb 동명) + `rules.py` FROZEN_PROVIDER_COMPANY_SURFACE 등록. **EngineCall 자동등록**(allowlist=라이브 capability 카탈로그 from `__all__`+Company public methods, 별도 파일 0). 결정론 subset(scenario/horizon/asOf)만 . drivers/lens/mode 는 인자조차 미추가(inert stub=clutter, 후속 phase). 검증: dartlabGuard exit 0·apiContractAudit exit 0(docstring+annotation 충족, contract dir repo-wide 미존재)·test_verb 4 passed·실호출 005930 adverse<baseline.
  - **다음 phase**: lens 보조(`ai/tools/lens.py`, 비결정론 평행 보완·no-graph-regression) · drivers/mode 인자(다중 드라이버 override + whatif/replay/walkforward) · Play 미래리플레이(05) · DriverRegistry 수렴(pooled-panel transfer) · US 프리셋(KR 가드 해제 선결) · (선택)import-linter pyproject contract entry.

**1. (해소됨 . born-clean) transfer 외과 추출 (01 §4) 의 layer subtlety 기록 보존**:
- `_applyMacroShock`(`simulation.py:180-235`) → `simulate/transfer.py::transferMacroToFundamentals`(rename) 이사.
- 실측 호출/proxy: `_applyMacroShock` 호출자 = `_simMonteCarlo.py:184`·`_simScenario.py:199`(둘 다 함수내부 lazy proxy `_simMonteCarlo.py:36-38`·`_simScenario.py:35-38`) + `__init__.py:27` re-export. (`_simHistorical` proxy 는 `_extractBaseMetrics`/`_extractVolatility` 용이지 `_applyMacroShock` 아님.)
- **★발견(PRD 미기재)**: 호출자 `_simScenario`/`_simMonteCarlo` 가 **L2**(`analysis/forecast`)인데 transfer 를 simulate/(**L2.5**)로 옮기면 **L2→L2.5 역방향 import = layer 위반**(viz→providers DIP 위반과 동류, F1.7 재발). ⟹ transfer 단독 이사로는 부족 . 옵션: (a) `simulation/` 시뮬 서브시스템 전체를 simulate/ 로 이주(큰 이동) / (b) DI Protocol(transfer 를 L0 protocol+L2.5 register, L2 가 get) / (c) 01 의 "묶음이 leaf 호출" 의미를 재확인(simulate 가 _simScenario 를 *호출*하지 _simScenario 가 transfer 를 호출 안 하게 재배선). **착수 전 01 §3~§5 재정독 + 호출방향 확정 필수** . 안 하면 architecture-l0-l15 FAIL.
- 부수: proxy 4 dissolve(no_import_evasion 부채 청산), import-linter contract(`pyproject.toml`)+`test_l2_no_cross_import`(L2_PEERS)+`test_l15_entry_rule` 에 simulate L2.5 등록, byte-identical 검증.

**2. 이후**: DriverNode/DriverSheet(`simulate/sheet.py`) + 위상정렬 실행기 + gate/grounding(01 §6) → AI lens(`ai/tools/lens.py`, no-graph-regression) → Play(05). 공개 verb `dartlab.simulate(...)`(01 §3).

### ⏳ 남은 정합성 (v0.1 잔재 + lint 범위)
7. ✅ **00 v0.2 동기화(2026-06-14)** . §2 본문 "Scenario Workbench" → `simulate` 치환, §7.2 #9 비범위에 simulate=L2.5 합법성 예외 1줄 추가. §5 "Valuation Report + Credit View = simulate 발간 단면" 은 v0.2 정정 헤더가 이미 정본 우선으로 커버(본문 전면개정은 선택, 미실시). 정정 헤더 + 본문 잔재 치환으로 doc정합 닫음.
8. ✅ **03 §9.3 발간 게이팅(2026-06-14)** . 03 v0.2 정정 헤더(line 7)가 이미 "발간 모드는 코어 SimulationResult 실측 확정 후를 본진 승격 기준에 추가"로 정본 커버. 08 §11 우선순위 역전 가드 반영 완료(헤더 정본).
9. ✅ **fatal① T1 금지어 lint 신설·CI배선 완료(2026-06-14)** . `tests/audit/valuationPublishLint.py`(+test) 발간 표면(`reportType: simulation` 마크다운) 한정 스캔, `tests/run.py:140` GATES lint 체인·green no-op·6 unit PASS. leaf 3파일(priceImplied·_valuationOther·pricetarget)은 `_isSimulationReport`가 `.py` 영원히 미스캔(옛 "2/3파일" src-스캔 모델 무효 . 발간 누출은 §2.3 어댑터가 drop). 잔여=T2 발간 표면(Phase 6). 03/07/08/09 "lint 미존재" 서술 stale 정정 동반.
10. **README 1줄** . 06 v0.3 반영(완료) + 06 문서지도 갱신(완료).
11. ★**빌드티켓 천장(09 §10)** . fatal① T1 ✅·Phase 0 ✅. 잔여 천장 = fatal②(forwardTest recordForecast write·models HF)/fatal③(gate/ledger/admission/lens)/fatal④(US threading) = **SYSTEM(미빌드 코드) 천장이지 PLAN 결함 0** . 설계는 09 §10 에 파일·시그니처·테스트게이트·phase 까지 execution-ready 로 닫혀 있고, 미빌드는 *코드 부재*지 *설계 미결*이 아니다(채점규칙: 코드부재≠감점). ★**planScore SSOT = §0(세 축 planScore 95)가 정본**(2026-06-20 R12 봉합 . 직전 "planScore=100" 표기는 본 항 1곳에만 있던 SSOT 분열이라 §0 로 강등): 본 항은 그 95의 *빌드측 근거*다 . fatal①~④ = SYSTEM 천장, PLAN 결함 0(설계는 execution-ready). systemScore=빌드 진행률(현 fatal① 1/4). **한 문서 한 점수**(100 vs 95 모순 제거) . planScore 정본은 §0, 본 항은 systemScore 분리 근거. 두 축 혼동 금지.
12. ★**타사 개념 흡수 토론 반영(2026-06-14, 경쟁 6서비스)** . 12 agent 토론+적대검증으로 흡수후보 9종 판정: 5종(A3·A6·A8·A9 already + A5 honesty 위반 reject)·4종 **absorb-as-defer**(새 기능 0, 한계 라벨/defer-게이트로만). PRD 반영 완료: A1 preset 출처 라벨+미검증 warning 시나리오-레벨 전파(02 §2.3, **졸업 AC**) / A2 임의충격 UX defer(02 §2B.3, 01 §4 already-have 명기) / A4 라이브 레버 = dirty recompute+S_T 격자 선결 defer(05 §4) / A6 fan band σ provenance 실선/점선 시각 규율(01 §5b·05 §3) / A7 공개 Brier 리더보드 write-end 후 defer(03 §9.3) / A5 점확률 발간 금지 가드(02 §2.3). 시그니처 판정=**conditional-signature(합의 61, KEEP 조건부)** . 00 §경쟁 지형·시그니처 박제. 잔여 졸업 AC = A1 warning 전파 실배선(write-end dead chain 동일 선결).
13. ★**A4 라이브 레버 졸업 의존** . live 레버(드래그→즉시 재렌더)는 lens/drivers phase(`_dirtyClosure` dirty recompute 01 §6.2·§13b-1 + Sobol S_T 격자 OQ11) 의존으로 deferred. 그 전엔 landing=사전 동결 격자 lookup·격자 밖 토글="로컬 재계산 필요" 한계 라벨(05 §4).
14. ★**차트 suite 분리 완료(2026-06-14, 운영자 go)** . 현재/과거 차트 3 컴포넌트(06 지수→01 차트·11 레일→02·10 백테스팅→03)를 **`mainPlan/_done/terminal-chart-suite/`로 git mv**(이력 보존). 절단면=**시간축**(현재/과거=suite, 미래=시뮬). **단방향 의존**(suite ⟶ 시뮬 05 Play, 역참조 0 . 시뮬-앵커 사상 동형). 07 = cross-category 브리지로 전환(시퀀스·공유 DNA·미래마커 이관). 시뮬 번호 공백(00-05/07-09) 유지=cross-ref churn 0. 갱신 동반: scenario-simulator README 문서지도·07·00:상태박스·05:37/48 형제참조·suite README 신설·terminal-chart-suite H1 renumber+참조규약. **이유=셋이 시뮬 미완 게이트(write-end·admission)에 인질로 안 잡히고 독립 출시 가능**(분리의 핵심 이득). 메모리 포인터 갱신 동반(시뮬+백테스팅+이벤트레일+terminal-improvement 경계). ⚠ `project_terminal_improvement` 경계 노트("지수/이벤트레일=scenario-simulator")가 stale→terminal-chart-suite로 정정 필요.

---

## 5. Open Questions (v0.2 . v0.1 미결 close 후 잔여)

> v0.1 OQ1(verb 위치)·계층 결정은 01 §3이 close. **2026-06-14 완성도 검토(구현자 시뮬레이션)로 OQ2~13 대부분 resolve-now 결정**(아래 ✅, 코드/1차원리 근거)·OQ11=데모 명세 확정(🔬)·OQ1=거시 AR/VAR 데모/빌드 의존(천장). 잔여 진짜 미결은 데모-보정 *값*뿐(규칙·설계는 결정됨).

1. 거시 미래경로 예측(AR/VAR) . 부재 확정(01 §9). 별도 _attempts 라운드 시점(데모/빌드 의존 천장, 09 §10 잔여).
2. ✅ **결정(rule)**: pooled 풀 경계 = **IndustryGroup(sub-sector) 기본 → pooled-N<60 이면 부모 WICS-11 Sector 승격 → 여전히 <60 이면 DEFAULT_ELASTICITY+warnings**. 근거: macro-β 식별 DoF≈time-DoF T(Moulton, §2B.1)라 풀 *폭*은 β t-stat 못 높임(기업이질성 정밀도만); SECTOR_ELASTICITY 이미 sub-sector grain(35키), `_resolveSectorKey`(_valuationHelpers.py:55) 가 industryGroup.name→2층 구조 보유(새 코드 0). **데모 필수 = 경계 임계값만**(IG풀 vs 승격이 leave-last-k=4 OOS partial-R²로 갈리는 지점). 02 §2B.1/§2B.11.
3. ✅ **결정(아키텍처)**: AI lens 노출 = **fork/큰-gap 노드만**. '전 근거 나열'은 결정론 provenance/refs(run.py NodeAudit 전 노드)가 이미 충족 . AI 의견은 약한-det fork 의 DisagreementLedger 로만 표면. 노출 *수준*은 비용/환각/원칙(불변2)으로 결정(데이터 무관); 데모는 FORK_THR/grounding 임계 *값*만 보정. 01 §6.4.
4. ✅ **결정**: `universe=` 횡단면 UI = 기존 **ScreenerModal** 흡수(새 셸/라우트/둘째차트 0). 노출랭킹=ScreenerModal 리스트+노출-스코어 컬럼(scan 위임), 행클릭=기존 onPick(code)→PriceChart subject+단일사 full DAG(01 §13c). 정본=07 시퀀스 4 + 00 §6.4(옛 '06/07' 라우팅 정정 . 06 은 무관).
5. ✅ **결정(빌드 의존 순서)**: (1) ReportDock valuation 단일모드 먼저(08 §5 YAGNI) → (2) P7 졸업(extractChsFeatures 가 proformaStatement 수신, 본체 0줄, 09 §4.3 . 현 `chsFeatures.py:18` 미수신) → (3) credit mode(09 Phase 5). credit mode 를 P7 전에 켜면 actual-only dead 탭. 정본=09 §4.5.

### v0.3 신규 잔여 (워크플로 심화)

6. ✅ **결정**: driverPrefit = **주간 dataPrebuild FULL 경로**(일 cron `0 17 * * 0`)에 한 step(증분 prebuild-scan 아님). driverDecay(forwardTest persistence/G5)는 별도 분기 cron 유지. 근거: scanMacroBeta 가 **연간 컬럼만**(macroBeta.py:113)+pooled-β DoF≈연간 time-DoF라 분기 공시는 연간 design matrix 거의 불변 → 증분 재적합=같은 (XtX) 재계산 낭비+churn. dataPrebuild.yml 에 prebuild-scan+prebuild-full 이미 존재라 full 편입=새 cron 0(prefit=design-matrix 주기 vs decay=outcome-vintage 주기). 02 §2B.7.
7. ✅ **결정**: tier 는 axis 에서 **파생**(저장 안 함): `tier='core' if card.axis in {6 exogenousAxes 문자열값} else 'exploratory'`. 운영자 수동=카드별 override 플래그만(기본 빈값). 근거: `ExogenousIndicator`(exogenousAxes.py:34)에 axis 있으나 tier 필드 없음; 척추 6축=그 6 문자열값, 뉴스·customs 미등록(candidate)→core/exploratory 가 axis 와 1:1. 저장 tier=axis 동어반복+drift. ⚠ `EXOGENOUS_AXES` 명명 상수 없음 . 6 문자열리터럴 또는 파생집합(`{ind.axis for ind in indicators}`, exogenousAxes.py:461) 참조. 02 §2B.3.
8. ✅ **결정**: mc.distribution `deps=(proformaId,)` . proforma 노드의 **FCF 벡터(`NodeValue.vector`)** 에 의존(leaf 아님). mean path=proformaNv.vector(단일 SSOT), noise σ=snapshot elasticity. 벡터화 noise 만(buildProforma 재호출 0 . `_simMonteCarlo.py:203-211` cumprod=OOM 없음). **`NodeValue.frozenInputs` 확장 불필요**(mc 는 proforma mean vector+σ 소비, macro 분포 파라미터 아님 . '직접계산 vs deps' 이분법 해소). byte-parity 제외(RNG), 분포통계 ±ε 만. 01 §5b.
9. ✅ **완료(close)**: :205 cumprod 전환 완료(09 P1, `ad112b171` cumprod + `fe9e66c0a` seed isolation). kill-test `test_horizon_widens_cone` 가 옛 cone-일정 버그 증명 후 전환. §4 P1 ②·§6 체크리스트 [x] 와 중복 . open 목록서 닫음.
10. ✅ **결정**: groundingCheck(b) 수치 범위 출처 = **snapshot 실측 base metrics ± 고정 tol**(`snapshot.baseRevenue/baseMargin`, registry.py:188 실측 키)을 단일 규칙으로. 약한 det 자체분포 금지(순환). `AssumptionLedgerRow`(코드 0건) 제거. ledger-row 없는 노드: (b) 기권→fork(det-분포 폴백 아님)=abstention-over-circular. gate.py 설계 계약으로 박음(데이터 무관). 01 §6.3.
11. 🔬 **데모 명세 확정(데이터 의존, 실험 닫음)**: Sobol S_T 컷오프 . 표본=척추 6섹터×2사=12 + 토글 8~10; 추정기=Saltelli/Sobol N_base=1024(≤12,288 결정론 DAG eval, 벡터화); 타깃=dcf perShare+terminalRevenue; **판정=컷오프 재정의 'top-6 토글 누적 S_T≥0.9'**(k≤6 보장, 고정 0.05 폐기); robustness=seed×3+bootstrap CI+cross-firm Kendall τ(τ 불안정 시 글로벌 컷오프 기각, per-firm top-6 폴백). 근거: src 에 variance-Sobol 부재(sensitivityAnalysis=OAT tornado), S_T 는 입력분포×출력비선형 의존이라 a priori 결정 불가. 02 §2B.11·01 §13b.
12. **(close . 운영자 결정=FRED 채택)** ★US 지수(SP500/NASDAQ/다우/VIX) = **FRED 종가 라인 subject로 06 통합 확정**. 운영자 결정 '미국 지수는 FRED 고려' 반영. 로컬 `data/macro/fred/observations.parquet` 실측으로 4종 라이브 확정(SP500 2609행 2016~·NASDAQCOM 14440행 1971~·DJIA 2609행 2016~·VIXCLS 9508행 1990~) . '데이터 전무(grep 0건)' 정정(grep은 ui 코드 미배선이지 데이터 부재 아님). KR=OHLCV 캔들 / US=종가(o=h=l=c, v=0) degenerate candle + `candleStyle='area'`. 새 차트·포트 0(IndexRef.market 분기 + 변환 1함수). 종가전용 제약=캔들·ATR·KDJ·CCI·WR·DMI·ICHI·AO·CR·VP 불가(06 §4.2), MA/RSI/MACD/BOLL 등 close-기반만 정상. 06 §3.2~§3.6·§6. **잔여=구현만**(데이터 선결 0). 표면 선호 1건(macroSource srcCache 공유 vs 소스 독립, 06 §7 OQ2).
13. ✅ **결정(경로, 실행 후속)**: 별도 `indexCompares: IndexRef[]` 슬롯(compares 의 IndexRef 확장 *기각*). 근거: `ctl.compares` 는 `{code,name}[]`(chartState:97)라 IndexRef 재구성 불가, compares 확장은 N사 compare 경로 회귀. indexCompares=가산적·회귀 0. 실행=06-subject 후 별트랙(US 벤치마크는 forward-fill 캘린더 정렬 선행). 06 §7.

---

## 6. 구현 전 체크리스트

- [x] main memory 포인터 (project 메모리 . 본 세션 추가 예정)
- [x] 엔진 거처 L2.5 simulate 확정·근거 기록 (01)
- [x] driver 수렴/확장 메커니즘 (02 §2B)
- [x] AI 보완/경합 + no-graph-regression (01 §6)
- [x] 가치평가·신용 = simulate 뷰 (08·09 §4)
- [x] 부채 원장 + 외과 시퀀스 (09)
- [x] **MC seed kill-test 선결 (P1) . ①② 완료(2026-06-14)**
  - ✅ **① MC 시드 전역오염 격리**(commit `fe9e66c0a`): `_simMonteCarlo.py`·`pricetarget.py` 의 전역 `random.seed`/`random.gauss` → 로컬 `rng = random.Random(seed)` 인스턴스. **동일 seed→동일 Mersenne 시퀀스라 동작 무변경**, 전역 RNG 오염만 제거. ★spec 의 numpy PCG64 대신 stdlib `random.Random` 채택 . 동작 무변경·`외부 의존성 제로`(pyodide 안전) 보존·jumpable streams 는 simulate 엔진이 필요할 때 재방문. test_simulation 29 PASS.
  - ✅ **② MC 호라이즌 cone 누적**(commit `ad112b171`): `:205` 내부 루프가 `simRev`/`simMargin` 을 매년 덮어써 마지막 해 노이즈만 반영(호라이즌 무관 cone 일정 = 버그). fix = 연도별 성장계수 cumprod(`cumRevFactor*=1+revNoise`) + margin 가산 random-walk(`cumMarginNoise+=`), mean path 보존. **kill-test `test_horizon_widens_cone`**: 옛 코드 FAIL(cv h=1 0.2251 ≈ h=3 0.2228 = 버그 증명) → cumprod 후 PASS(cone 확대). 전체 30 MC PASS(정성 회귀 0). 옛 `*=` 단순수정은 평균경로 소실이라 기각. 운영자 가시 기록 = kill-test + 커밋.
- [ ] 05/06/07 작성 + 00/02/03 v0.2 동기화 (NEXT §4)
- [ ] 워크스페이스 새 토폴로지(ui/packages/surfaces) 반영 (05/06)
- [ ] 착수 = mainPlan 완료 후 (조기 진척 중 . 의존성 07에서 확정) + 운영자 go


## 2026-07-05 : 06 "현재" 축 탑재 (운영자 합의)

- 신규 문서 06-engine-readings-and-sweep.md: 전 하위 엔진 데이터를 한곳에서 모아 출처·성격별
  판독(표면 카탈로그 자동 전수 등재, 선별 0) → 전량 봉인(issueReadings, issueMacro 동형) →
  주간 채점(G16 정합 수축 성적표) → 가정 sweep(상황 가정=명명 프리셋 소비, 결합 가정=
  AssumptionLedgerRow 규율 첫 적용, 선정=강건성 median, 가정도 봉인·채점).
- 00 §8b conditional-signature 의 "검증 루프 미완"을 채우는 조각. 09 §10 fatal②(forward-test
  write 끝단)를 주간 전종목 규모로 실장.
- 토론 이력(v0.1~v0.6.1)·P0 실측·갭 원장 = ../weekly-uplift-shortlist/ (아카이브 전환).
- 원칙 확정 반영: 개별 데이터 작업대 폐기(dossier df41ee60e), 호출계약은 엔진 소유 verb 로만.
