# 02. 스코어링과 깔때기 : 6단 설계

> 원칙: 스코어링 메커니즘은 **하나**다. 신호별 특수 케이스·키워드 규칙 더미·per-signal if 분기를 누적하지 않는다 (덕지덕지 금지). 신호의 개성은 전부 레지스트리 선언(방향·시차·커버리지)으로 표현하고, 합성기는 선언을 기계적으로 실행만 한다.

## 1. 깔때기 6단

```
S0 유니버스     listing("companies") 전상장사. 명시 제외만: 정리매매·스팩(명칭 규칙)·
               상장 후 20거래일 미만(신호 계산 불능). ADTV 하위 컷 = opt-in(기본 꺼짐).
               제외 건수·사유를 매 실행 로그로 남김 (no-silent-cap)
S1 신호 수확    레지스트리의 각 신호를 벌크 우선 경로로 계산 → 종목 x 신호 wide 격자
S2 rank 정규화  신호별 cross-sectional percentile rank (방향 정렬, 결측 null 유지)
S3 합성        family 점수 = 소속 신호 rank 평균(결측 제외) →
               composite = 레짐 가중 Σ w_f · F_f (참여 family ≥ 2 필수)
S4 board100    composite 상위 100 + family 분해·coverage·flags 동행
S5 top10       합류 룰 + red-flag 게이트 + conformal 비모순 → 근거 순위화
```

## 2. 신호 레지스트리 계약 (코드가 정본)

```python
@dataclass(frozen=True)
class SignalSpec:
    signalId: str          # 예: "mom20d", "smartMoneyZ", "ordersBookToBill"
    family: str            # PRICE | FLOW | EVENT | FUND | TEXT
    direction: int         # +1 = 높을수록 상승 근거, -1 = 낮을수록
    horizon: str           # 신호가 겨냥한 지평 명시 (본 제품은 "5d" 정합만 채택)
    fetch: str             # 공개 verb 경로 문자열 (예: "scan:orders", "quant:momentum")
    pitLagDays: int        # 데이터 공표 시차 (rank 계산 전 asOf 보정)
    bulkCapable: bool      # 전종목 벌크 계산 가능 여부 (False = lazy fetch 대상)
    minCoverage: float     # 이 커버리지 미만이면 해당 주 신호 자체를 비활성(로그)
```

- 등록·해제는 코드 리뷰를 타는 선언 변경이며, 실행 중 동적 추가 없음.

### 2.1 지평 정합 원칙 (신호 선택의 제1 기준)

5거래일 지평에서 레벨형 재무 랭크는 주간 알파 원천이 아니라 조건(게이트·틸트)이다. 주간 예측력이 문헌·실무에서 반복 확인된 부류를 우선한다: 단기 reversal, 잔차 모멘텀, 거래량 충격, 수급 지속, 이벤트 직후 드리프트(PEAD·수주·자사주). 느린 신호(밸류·퀄리티)는 가중을 학습(§5)에 맡기고 사전 우대하지 않는다.

- v0 등록 신호(안, 총 ~18):
  - PRICE 6: shortTermReversal5d(direction=-1)·잔차모멘텀20d·mom60d·52주고가근접·거래량충격 z·변동성
  - FLOW 3: smartMoneyZ60d·수급연속일수(외국인+기관 순매수 streak)·flowMomentum20d
  - EVENT 5: ordersBookToBill·자사주매입·insider순매수·watcherDiff·PEAD근사(SUE x 공시접수 후 경과일 감쇠, G3 승격 전 rcept_dt 기반)
  - TEXT 2: narrative tone z·공시톤변화
  - FUND 2: fundmom·산업내 valuation percentile
- 추가는 eventStudy 또는 replay 사전 근거 필수 (01 §4).

### 2.2 상관 중복(redundancy) 처리

같은 정보를 여러 이름으로 중복 가중하지 않는다. P0 에서 신호 간 rank 상관 행렬을 실측해, family 내 |ρ| > 0.7 클러스터는 대표 1개만 등록(또는 클러스터 평균을 1개 신호로 취급)한다. 등록 확정본이 레지스트리에 남고, 탈락 신호는 사유와 함께 01 갭 원장에 기록.

## 3. 벌크 우선 계산 경로 (메모리 강행규칙 정합)

- **PRICE family 는 Company 객체를 만들지 않는다.** gov/prices year shard 를 polars lazy 로 직독해 전종목 wide 계산 (Polars Rust 힙 OOM 가드: Company 1개 200~500MB, 전종목 루프 절대 금지).
- FUND/EVENT 는 scan 축(이미 전종목 prebuilt/provider 경로) 결과 DataFrame 을 그대로 join.
- bulkCapable=False 신호(FLOW의 smartMoneyZ, TEXT 일부, 종목별 quant 텍스트 축)는 **2-패스**: 1차 합성(벌크 신호만) 상위 ~300 종목에만 lazy fetch 후 재합성. 이 컷은 silent 가 아니라 로그+문서 명시 (전상장사 규약: 1차 패스는 전종목이 계산됨).
- 실행 프로세스는 단일. 병렬 agent/프로세스 금지 (dartlab import 순차 규약).

## 4. 합성 수학 : rank 는 정규화 골격이지 모델이 아니다

rank 정규화는 신호를 비교 가능하게 만드는 표준화 층이다 (outlier 강건·산업 중립화 가능·종목별 근거 분해 가능). 예측력은 그 위의 **가중 학습(§5)** 이 담당한다. "단순 랭크 평균" 은 §5 사다리의 최하단 폴백일 뿐 발행 기준이 아니다.

1. 신호값 x_i → 방향 정렬 후 percentile rank r_i ∈ [0,1] (필요 신호는 산업 내 rank). winsorize 불필요.
2. 신호 rank 벡터 → §5 에서 학습된 가중으로 선형 결합 = composite C. 선형을 고수하는 이유: 종목별 점수를 신호 기여도로 분해해 evidence dossier 에 그대로 실을 수 있다 (비선형 ML 은 이 근거 분해가 깨져 top10 의 "근거" 정의와 충돌).
3. family 점수 F 는 발행 표면의 설명 축으로 유지 (합류 룰 §6 입력). F = mean(소속 신호 r_i, 결측 제외), 참여 0개면 null.
4. 참여 family < 2 이면 후보 제외(coverage 리포트 집계). 동점은 유동성(ADTV) 높은 쪽 우선.

## 5. 가중 사다리 (weighting ladder) : 임의 상수 금지, 학습은 규율 하에

| 층 | 방법 | 지위 |
|---|---|---|
| W0 | 동일가중 rank 평균 | 폴백·디버깅 베이스라인 전용. 단독 발행 금지 |
| **W1 (정본)** | 주간 Fama-MacBeth 횡단면 회귀 + shrinkage | P0 replay 하네스에서 학습·검증 후 발행 가중 |
| W2 (이연) | 정규화 선형 랭커 (ridge / top-분위 logistic, numpy-only) | W1 성적 원장 누적 후 승격 검토 |

### W1 상세

- 매주 t (17년 ≈ ~880개 횡단면): 유니버스 초과 fwd 5거래일 수익률을 표준화 신호 rank 벡터에 회귀 → 계수 b_t (numpy lstsq, 신규 의존성 0).
- 발행 가중 w_j = 부호안정성 게이트(계수 부호 일관률 미달 신호는 0) x shrinkage(rolling mean b_j, λ 사전 선언).
- 레짐 조건부: riskOn/riskOff 주차 부분집합별 계수 평균으로 산출 (고정 프리셋 표 폐기. 레짐 판정 입력은 기존대로 `macro("종합")` + `quant("레짐")` + `scanNarrativeRegime` 2/3 다수결).
- 검증: purged walk-forward (embargo ≥ 1주, 5d 라벨 겹침 차단) fold 별 OOS 분위 스프레드 밴드 (03 §2).
- 라이브 규율: 가중 재추정은 분기 1회·사전등록 protocol 로만. 주중 변경 금지 (레코드 오염). 회귀 계수·t-stat 은 가중 산출 내부용이며 대외 수치 claim 에 쓰지 않는다 (03 §5).
- 비선형 ML(GBM 등) 을 이연하는 이유: 신규 의존성 + 과적합 표면적 + 근거 분해 불가. W1 성적 원장이 쌓여 선형의 한계가 실측되면 그때 별도 사이클로 상정.

## 6. top10 합류(confluence) 룰

board100 안에서:

1. **합류 카운트 k** = F_f ≥ 0.80 (해당 family 유니버스 상위 20%) 인 family 수. k ≥ 3 필수.
2. **red-flag 게이트 (하나라도 걸리면 top10 자격 박탈, board100 에는 flag 표기 유지)**:
   - 감사의견 비적정 / 자본잠식 (scan audit·debt)
   - credit 최하등급 + Altman distress 동시 (교차 확인, 단일 지표 단정 금지 규약 준수)
   - disclosureRisk 상위 신호 3개 이상 동시
   - 시장조치·관리종목 (G5 승격 전엔 kindList 근사 + 한계 flag)
   - 유동성 최하위 분위 (체결 불능 수준)
3. **conformal 비모순**: `quant("예측", code, horizon=5)` 90% 구간 상단이 0 이하이면 탈락 (점예측이 아니라 구간으로 판정. 구간이 0 을 걸치는 것은 허용하되 dossier 에 그대로 공개).
4. 순위화: (k 내림차순, C 내림차순). 통과 종목이 10 미만인 주는 **그 수만큼만 발행** (억지로 10 채우기 금지. 부족분은 "이번 주 합류 미달" 로 원장 기록).

## 7. 출력 스키마와 결측 규약

- board100/top10 스키마는 00 §3. 추가 규약:
  - 결측은 null 그대로. 0 대체·평균 대체 0건 (scan forbidden 상속).
  - 모든 수치 컬럼에 asOf/dateRef 동행. 신호별 원천 verb 를 refs 에 기록해 재현 가능.
  - coverage 컬럼: "18개 중 14개 신호 참여" 식의 정수 쌍. family 단위도 병기.
- 주간 실행 결과는 로컬 `data/shortlist/`(DATA_RELEASES 등록 후) parquet append. ledger 봉인과 별개로 board 전체 스냅샷 보존 (재현성).

## 8. 이 설계가 기존 axis 회피 룰을 어기지 않는 근거

- "단일 신호로 단정 금지" 계열 룰: 합류 룰 자체가 다신호 종합을 강제.
- "scan 후보를 검증 없이 투자 결론으로 확정 금지": top10 은 결론이 아니라 조사 착수 목록이며 dossier 에 analysis/credit 검증 동행.
- "screen 상위를 곧바로 매수 추천 금지": never-claim 문구 봉인 + 추천 어휘 0.
- "결손 0 대체 금지": §7.
- "universe·기준일·필터·계산식 없이 후보 발굴 완료 금지": board 스키마가 전부 동행.
