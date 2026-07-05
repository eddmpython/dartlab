# 01. 신호 전수 인벤토리 + 갭 원장

> 원칙: 신호는 전부 **공개 계약(공개 verb + 인자)** 으로 소비한다. 내부 계층(sources/mixins) 직접 호출 금지. 각 신호는 PIT 주의(그 시점에 알 수 있었는가)를 명시한다. 상태 표기: ✅ = 공개 verb 실재(스펙+코드 확인) · ⚠ = 실재하나 커버리지/시차 실측 필요(P0 항목) · ❌ = 갭 원장행.
>
> v0.3 매핑: 아래 family 는 판독기(reader) 단위와 1:1 이다 (02 §2). 본 문서는 판독기가 소비할 원천의 전수 지도 + 갭 원장을 유지한다.

## 1. Family 정의 (독립성 기준)

| family | 담는 것 | 독립성 근거 |
|---|---|---|
| PRICE | 가격·거래량·변동성 횡단면 | 시장 데이터만 사용 |
| FLOW | 투자자별 수급 (외국인·기관) | 가격과 별개의 행위자 데이터 |
| EVENT | 공시 이벤트 (수주·자사주·내부자·대량보유·watcher diff) | 기업 행동 데이터 |
| FUND | 재무 팩터 (서프라이즈·펀더모멘텀·퀄리티·밸류) | 회계 데이터 |
| TEXT | 뉴스·공시 텍스트 톤 | 비정형 텍스트 |
| CONTEXT | 레짐·산업·매크로 틸트 (종목 공통 성분) | 시장 레벨. 개별 종목 rank 가 아니라 가중치/틸트로만 작용 |

"근거 합류" 판정은 PRICE~TEXT 5개 family 에서만 센다 (CONTEXT 는 가중치라 합류 카운트에서 제외).

## 2. 엔진별 신호 인벤토리

### 2.1 gather (L1) : 원자료 수확

| 신호 | 공개 verb | family | PIT/커버리지 주의 | 상태 |
|---|---|---|---|---|
| 전종목 일별 OHLCV·시총·발행주식수 (1995~) | `dartlab.gather("krx", ...)` / 엔진 내부 `hfBulk`(category govPrices) | PRICE | HF SSOT 일별 sync. asOf = 최종 거래일 | ✅ |
| 시장 지수 OHLCV | `dartlab.gather("krxIndex", "close", market=...)` | CONTEXT | 벤치마크·레짐 입력 | ✅ |
| 종목별 투자자 수급 | `dartlab.gather("flow", code, limit=30)` | FLOW | 전종목 벌크 없음(종목별 크롤·rate limit). 공표 T+0/T+1 시차 명시 | ⚠ → G1 |
| 뉴스 검색 | `dartlab.gather("news", 회사명)` | TEXT | untrusted 마커 규약. 종목 매핑 정밀도 실측 필요 | ⚠ → G8 |
| 내러티브 아카이브 (RSS+GDELT) | `dartlab.gather("narrative", market="KR", days=30)` | TEXT | 종목 태깅 커버리지 실측 필요 | ⚠ → G8 |
| 증권사 리서치 메타 인덱스 | `dartlab.gather("research", code)` | EVENT | 발간일 기준. 목표주가 필드 없음(메타만) | ⚠ → G4 |
| 내부자 거래 | `dartlab.gather("insider", code)` (DART_API_KEY) | EVENT | 보고일 기준 PIT. 매수=긍정 단순화 금지 (스톡옵션/의무보유 구분) | ✅ |
| 기관/외국인 보유·5% 대량보유 | `gather("ownership")` / `g.majorShareholders()` | FLOW/EVENT | filing date 기준 | ✅ |
| 배당/분할 이력 | `g.dividends()` / `g.splits()` | FUND | 주간 지평에선 이벤트성(배당락 주의)만 | ✅ |
| 매크로 원자료 (ECOS·FRED·ECB·BIS·OECD·IMF·관세청 customs) | `dartlab.gather("macro", ...)` / `gather.customs...series(hsCode)` | CONTEXT | customs 는 월별(기업실적 6~8주 선행). 주간 신호가 아니라 산업 틸트 | ✅ |
| 네이버 테마/업종 분류 | `dartlab.gather("naverTheme")` (로컬 전용) | CONTEXT | 재배포 금지. 공개 산출물 미포함 (승인 A4) | ⚠ |
| 정기공시 due 캘린더 | `Company(code).calendar(horizonDays=30)` (베타) | EVENT | 예정 이벤트. 실적 발표일 캘린더는 아님 | ⚠ → G3 |

### 2.2 scan (L1.5) : 횡단면 후보 발굴

| 신호 | 공개 verb | family | 주의 | 상태 |
|---|---|---|---|---|
| 신규수주 (book-to-bill) | `dartlab.scan("orders")` | EVENT | micro-cap 잡음 필터(매출 규모·계약 건수) 필수, amountSuspect 제외 | ✅ |
| 공시리스크 | `dartlab.scan("disclosureRisk")` | red flag | 단일 신호 단정 금지(5+ 신호 종합 규약) | ✅ |
| 내부자지분 변화 | `dartlab.scan("insider")` | EVENT | 위와 동일 | ✅ |
| 주주환원 (자사주·증자) | `dartlab.scan("capital")` | EVENT | 매입 vs 소각 구분 | ✅ |
| 밸류에이션·퀄리티·성장·수익성·효율·유동성·현금흐름·배당추이 | `dartlab.scan("valuation" 등 8축)` | FUND | 산업 분기 무시 통합 랭킹 금지 → 산업 내 percentile 로 소비 | ✅ |
| 감사리스크·부채구조·거버넌스 | `scan("audit"/"debt"/"governance")` | red flag | top10 자격 게이트 | ✅ |
| 거시베타 (재무 vs GDP/금리/환율) | `dartlab.scan("macroBeta")` | CONTEXT | 연간 단위. 주간 신호 아님, 틸트 매핑용 | ✅ |
| 신규상장 | `dartlab.scan("ipo")` | EVENT | 데이터 짧음. v0 는 flag 만 | ✅ |
| 공시 diff 중요도 (watcher) | `scan/watch` scorer (공개 verb 경로 P0 확인) | EVENT | topic 가중 + 키워드. 공개 계약 표면 확인 필요 | ⚠ |
| 시장 내러티브 레짐 (Pettitt) | `scan/narrativeRegime.scanNarrativeRegime` | CONTEXT | 시장 레벨. 레짐 가중 입력 | ✅ |
| 조건형 스크린 | `dartlab.scan("screen", spec=...)` | 위생 필터 | 유니버스 위생 조건 실행기로 재사용 | ✅ |

### 2.3 quant (L2) : 정량 신호·검증

| 신호 | 공개 verb | family | 주의 | 상태 |
|---|---|---|---|---|
| 모멘텀 (다중 lookback) | `quant("모멘텀", code)` + `quant/signal/momentum.py` | PRICE | 단일 lookback 단정 금지. 횡단면 계산은 벌크 경로(02 §3) | ✅ |
| 거래량 이상 (OBV·surge) | `quant("거래량")` + `signal/volume.py` | PRICE | 가격 추세 동반 확인 | ✅ |
| 변동성·유동성 (Amihud) | `quant("변동성"/"유동성")` | PRICE/위생 | ADTV 컷은 opt-in 명시 | ✅ |
| 수급 z (smartMoneyZ60d·flowMomentum20d) | `quant("시장맥락", code)` 내 flow 블록 | FLOW | 종목별 호출이라 벌크 불가 → G1 전까지 부분 커버 | ⚠ |
| 이익서프라이즈 SUE | `quant("surprise")` + `alphas/earningsSurprise.py` | FUND | PEAD 는 다분기 누적. 발표일 캘린더 갭 → G3 | ⚠ |
| 펀더-가격 모멘텀 | `quant("fundmom")` + `alphas/fundamentalMomentum.py` | FUND | KR 재현성 명시 | ✅ |
| 퀄리티 계열 (piotroski·qmj·qfactor·accruals·bab) | `quant(각 axis)` + `alphas/` | FUND | 미국 threshold KR 직접 적용 금지 문구 | ✅ |
| 공시심리·톤변화·이벤트신호·리스크텍스트 | `quant("공시심리"/"톤변화"/"이벤트신호"/"리스크텍스트", code)` | TEXT/EVENT | 종목별 호출. 벌크 커버리지 실측 (P0) | ⚠ |
| 5거래일 conformal forecast | `quant("예측", code, horizon=5)` | 게이트 | top10 방향 비모순 게이트 전용. 점예측 단독 인용 금지(구간 동행) | ✅ |
| 레짐 (HMM) | `quant("레짐", 지수)` | CONTEXT | 회고적 신호 conf 표기 | ✅ |
| 이벤트 스터디 | `quant/signal/eventStudy.py` | 검증 | 갭 신호 승격 시 사전 검증 도구 | ✅ |
| triple barrier 라벨 | `quant/labels/tripleBarrier.py` | 검증 | replay 라벨링 보조 | ✅ |
| 유니버스 백테스트 | `dl.quant.scanBacktest(df, style=...)` + strategy-lab U1 자산 | 검증 | 03 에서 소비 | ✅ |

### 2.4 나머지 엔진

| 엔진 | 역할 | 소비 방식 | 상태 |
|---|---|---|---|
| analysis (L2) | 재무 인과 해석 | top10 dossier 의 재무 건전성 서술 (매크로민감도 포함) | ✅ |
| credit (L2) | 부도위험 스코어카드 | red-flag 게이트 (최하등급 + Altman distress 교차 시 탈락) | ✅ |
| industry (L2) | 밸류체인·lifecycle·peers | 산업 내 percentile 분기 + peer 대비 위치 서술 | ✅ |
| macro (L2) | 레짐 판정 (cycle·rates·sentiment·종합) | 주간 레짐 스냅샷 → family 가중 프리셋 선택 | ✅ |
| frame (L1.5) | 정기보고서 인벤토리·정성 노트 | top10 dossier 의 정성 근거 인용 | ✅ |
| search (L1.5) | 공시 원문 역인덱스 | dossier 작성 시 근거 원문 확인 | ✅ |
| listing (facade) | 전종목·공시 메타 카탈로그 | 유니버스 스켈레톤 + 이벤트 타임라인 url | ✅ |
| simulate (L2.5) | expectation ledger + 채점기 | 봉인·채점 척추 (A2) | ✅ |
| story (L3) | 보고서 조합 | top10 dossier 산문 조립 | ✅ |
| viz/dashboard | 시각화 | P5 (터미널 표면) 전까지 CLI 표만 | ✅ |
| ai/mcp (L4) | Ask Workbench | dossier 를 workbench ref 규약으로 노출 (후속) | ✅ |
| edgar/mappers/data/panel | 기반 데이터 | KR v0 범위에선 panel 재무 시계열의 원천으로 간접 소비 | ✅ |

### 2.5 EDGAR(US) 대응 원천 : 시장 파라미터화의 실측 근거

같은 판독기 계약을 US 에 적용할 때의 원천 매핑. fund/event/text/credit 은 기존 자산으로 즉시 가능, price/flow/forecast 는 갭(G9·G10)이 선결.

| reader | US 원천 (기존 자산) | 상태 |
|---|---|---|
| fund | EDGAR panel (gather raw XBRL 자급 파싱) + scan DART+EDGAR 겸용 축 (account·ratio·capital·debt) + alphas | ✅ |
| event | `listing("filings", corp=ticker)` (8-K·10-Q 등 form_type) + watcher diff (`_HIGH_WEIGHT_TOPICS` 에 10-K item 이미 등록) + Form 4 내부자 | ✅/⚠ (8-K item 코드 이벤트 분류는 P0 실측) |
| text | 10-K/10-Q Risk Factors·MD&A 톤 (frame/search) + narrative US | ⚠ 커버리지 실측 |
| credit | credit 스코어카드 + Altman (US 원산 모델이라 오히려 정합) | ✅ |
| price | 종목별 `gather("price", "AAPL")` 만 존재. **전종목 일별 벌크 없음** | ❌ → G9 |
| flow | KR 수급 개념의 US 대응물 = FINRA 공매도 잔고(격주)·13F(분기)·Form 4 | ❌ → G10 |
| forecast | `quant("예측", "AAPL")` 종목별 가능, 벌크는 G9 종속 | ⚠ |
| context | macro US (FRED)·regime·산업 lifecycle | ✅ |

- 채점 벤치마크: US 유니버스 동일가중 평균 + S&P500. 시장 간 rank 혼합 금지 (시장 내 완결).
- US 유니버스 정의: EDGAR panel 커버 상장사 전체 (완전 커버 원칙 KR 과 동일, top-N 컷 금지).

## 3. 갭 원장 (부족 데이터·개념 전수)

> 각 갭: 무엇 / 왜 1주 지평에 중요한가 / 현재 상태 / 승격 경로 / 게이트.

### G1. 전종목 일별 투자자별 수급 벌크 백본 ★최고 ROI

- **무엇**: 외국인·기관·개인 순매수 일별 전종목 히스토리의 HF SSOT sync (gov/prices 와 동일 패턴, 예: `gov/flows`).
- **왜**: 1주 지평에서 수급 합류(외국인+기관 동시 순매수 z)는 PRICE 와 독립인 최상위 신호 family 인데, 현재는 종목별 크롤(rate limit)이라 전종목 횡단면 계산이 사실상 불가.
- **현재**: `gather("flow", code)` 종목별 ✅ / 벌크 ❌. `quant("시장맥락")` 의 smartMoneyZ 는 단일 종목용.
- **승격 경로**: KRX OpenAPI 또는 공공데이터포털 투자자별 거래실적 endpoint 실측 → `.github/scripts/sync/` 신설 수집기(무료 키) → DATA_RELEASES 등록 → `hfBulk` 패턴 소비.
- **게이트**: 신규 sync 파이프라인 = 운영자 승인 A3. 승격 전 FLOW family 는 "board100 후보 대상 lazy fetch(상위 ~300 종목만 종목별 호출)" 부분 커버로 운영하고 커버리지를 정직 표기.

### G2. flow 엔진 5축 (공매도 잔고·대차잔고·프로그램매매·블록딜)

- **왜**: 공매도 잔고 감소+가격 반등(short covering), 대차잔고 급증 등은 주간 지평 대표 신호. `engines.flow` 가 이미 drafted 스펙으로 존재 (quantGap Tier 1).
- **현재**: 스펙만 ❌ (status=drafted, 데이터 인프라 선결 명시).
- **승격 경로**: KRX 공매도통계(무료) + 예탁원 대차 endpoint 실측 → G1 과 같은 sync 패턴 → `dartlab.flow` 엔진 활성 → FLOW family 에 신호 2~3개 추가.
- **게이트**: G1 이후. 별도 사이클 (본 플랜 범위 밖, 원장 기록만).

### G3. 실적 발표일 캘린더 + PEAD 윈도우 개념

- **왜**: 서프라이즈 신호(SUE)는 "발표 직후 몇 주" 윈도우에서 의미가 있다. 지금은 발표일 데이터가 없어 서프라이즈가 "언제 신호인지" 모른다.
- **현재**: `Company.calendar`(정기공시 due, 베타) ⚠ + allFilings 월별 parquet 에 실적 공시 접수일 존재 ✅. 조합 개념 미구현 ❌.
- **승격 경로**: allFilings 에서 분기/반기/사업보고서 + 영업(잠정)실적 공시의 rcept_dt 를 종목별 이벤트 시계열로 표준화 (신규 수집 불필요, 기존 SSOT 가공 = scan 축 후보 `earningsCalendar`). SUE 신호에 "발표 후 경과 거래일" 필드 부여.
- **게이트**: P4. 신규 데이터 소스가 아니라 기존 allFilings 가공이므로 승인 부담 낮음.

### G4. 목표주가·투자의견 히스토리

- **왜**: 리서치 발간 + 목표가 상향은 주간 지평 이벤트 신호.
- **현재**: `gather("research")` 메타(제목·발간일) ✅, 목표가 필드 ❌.
- **승격 경로**: 리서치 제목 텍스트에서 상향/하향 키워드 추출(로컬 파싱, 재배포 없음)을 v1 근사로. 정식 목표가 데이터는 무료 재배포 가능 소스가 확인되기 전까지 보류.
- **게이트**: 저작권·재배포 검토 선행. v0 은 "리서치 발간 빈도 증가" 만 EVENT 보조 신호로.

### G5. KRX 시장조치 데이터 (투자주의·경고·위험, 관리종목, 거래정지)

- **왜**: (a) 유니버스 위생의 정본 데이터, (b) 시장조치 지정/해제 자체가 강한 단기 신호(주로 역방향 리스크).
- **현재**: kindList 의 시장구분으로 부분 근사 ⚠. 지정 이력 데이터 ❌.
- **승격 경로**: KRX 시장조치 공시(무료 공개) 수집기 → 위생 필터 정본화 + red-flag 게이트 입력.
- **게이트**: P4, sync 신설이므로 승인 동반. 그 전까지 위생 필터의 한계를 flags 로 명시.

### G6. 공개 가능한 테마/공행성 군집 개념

- **왜**: "같은 테마가 함께 움직인다"는 1주 지평의 지배적 현상인데 naverTheme 은 재배포 금지라 공개 산출물에 못 쓴다.
- **현재**: industry taxonomy(공개) ✅, naverTheme(로컬) ⚠, 공개 군집 ❌.
- **승격 경로**: gov/prices 수익률 상관 기반 co-movement 클러스터링(자체 계산 = 재배포 문제 0)을 신규 개념 `priceCluster` 로 설계. 클러스터 모멘텀(소속 군집의 최근 5~20일 상대강도)을 CONTEXT→PRICE 보조 신호로 승격.
- **게이트**: P4 (신규 개념. _attempts 게이트 통과 필수).

### G7. 5거래일 지평 전용 횡단면 검증 하네스

- **왜**: 기존 replay 자산(strategy-lab U1)은 분기 리밸런스 중심. 본 제품은 주간·5거래일 forward 라 지평 변형이 필요.
- **현재**: buildUniversePanel + scanBacktest + tripleBarrier ✅. 주간 지평 wrapper ❌.
- **승격 경로**: P0 에서 _attempts 로 주간 replay 하네스 실측 (03 §3). 신규 통계 발명 없이 기존 자산 조합.
- **게이트**: P0 자체가 이 갭을 닫는다.

### G8. 뉴스·내러티브의 종목 태깅 커버리지 실측

- **왜**: TEXT family 가 대형주만 커버하면 전상장사 규약과 충돌한다 (커버리지 편향 = 시총상위 silent 편향).
- **현재**: narrative archive ✅, 종목 매핑 정밀도 미실측 ⚠.
- **승격 경로**: P0 실측 (전상장사 대비 태깅률·소형주 태깅률). 낮으면 TEXT family 를 "커버 종목에만 참여 + coverage 컬럼 정직 표기"로 운영 (0 대체 금지 규약이 편향을 자동 방어).
- **게이트**: P0 측정 항목.

### G9. US 전종목 일별 가격 벌크 백본 (EDGAR 통합의 선결)

- **무엇**: KR gov/prices 에 대응하는 US 전상장 일별 OHLCV·시총 HF SSOT.
- **왜**: US price/forecast reader 와 US 주간 채점(실현 수익률 join) 모두 이것에 종속. 종목별 `gather("price", ticker)` 로는 전종목 주간 발행·채점이 불가.
- **현재**: 종목별 조회 ✅ / 벌크 ❌. EDGAR 는 가격 데이터를 제공하지 않음.
- **승격 경로**: 무료·재배포 가능 소스 실측 (Stooq EOD 등 후보. 라이선스·재배포 조건 문서 확인이 첫 스텝) → sync 수집기 → DATA_RELEASES 등록. 재배포 불가 소스만 있으면 로컬 캐시 전용 경로로 강등하고 공개 표면 제한 명시.
- **게이트**: P0 소스 실측 → A5 상정. 그 전까지 US 는 fund/event/text/credit reader 만 활성 (채점은 종목별 가격 조회로 top 후보 한정 병행, 전량 채점은 백본 확보 후).

### G10. US flow 대응물 (FINRA 공매도 잔고·13F·Form 4)

- **왜**: KR 수급 reader 의 US 대응. 공매도 잔고 변화(격주)·기관 보유 변화(13F 분기)·내부자(Form 4)는 전부 무료 공개 소스.
- **현재**: ❌ (Form 4 는 EDGAR filings 메타로 부분 접근 가능).
- **승격 경로**: SEC/FINRA 무료 endpoint 실측 → gather 축 또는 sync. 빈도가 주간보다 성겨서(격주·분기) pitLagDays 를 크게 선언하고 이벤트성 reader 로 소비.
- **게이트**: G9 이후 별도 사이클.

## 4. 인벤토리 사용 규칙

- 신호 추가는 이 문서가 아니라 코드의 신호 레지스트리(02 §2)가 정본이 된 뒤, 문서는 갭 원장만 유지한다 (SSOT 이중화 방지).
- 새 신호 후보는 "덕지덕지 self-check" (feedback_always_check_clutter) 를 통과해야 한다: 기존 family 에 흡수 불가한가, eventStudy/replay 사전 근거가 있는가, 커버리지가 전상장사 규약과 충돌하지 않는가.
