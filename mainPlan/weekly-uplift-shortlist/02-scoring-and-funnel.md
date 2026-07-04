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
- v0 등록 신호(안): PRICE 5 (mom5d·mom20d·mom60d와 52주고가근접·거래량surge z·저변동flag), FLOW 2 (smartMoneyZ60d·flowMomentum20d), EVENT 4 (orders·capital자사주·insider순매수·watcherDiff), FUND 5 (SUE·fundmom·piotroski·산업내valuation percentile·growth 패턴), TEXT 2 (narrative tone z·공시톤변화). 총 ~18개. 추가는 eventStudy 사전 근거 필수 (01 §4).

## 3. 벌크 우선 계산 경로 (메모리 강행규칙 정합)

- **PRICE family 는 Company 객체를 만들지 않는다.** gov/prices year shard 를 polars lazy 로 직독해 전종목 wide 계산 (Polars Rust 힙 OOM 가드: Company 1개 200~500MB, 전종목 루프 절대 금지).
- FUND/EVENT 는 scan 축(이미 전종목 prebuilt/provider 경로) 결과 DataFrame 을 그대로 join.
- bulkCapable=False 신호(FLOW의 smartMoneyZ, TEXT 일부, 종목별 quant 텍스트 축)는 **2-패스**: 1차 합성(벌크 신호만) 상위 ~300 종목에만 lazy fetch 후 재합성. 이 컷은 silent 가 아니라 로그+문서 명시 (전상장사 규약: 1차 패스는 전종목이 계산됨).
- 실행 프로세스는 단일. 병렬 agent/프로세스 금지 (dartlab import 순차 규약).

## 4. 합성 수학 (전부 rank 기반, 파라미터 최소)

1. 신호값 x_i → 방향 정렬 후 percentile rank r_i ∈ [0,1]. rank 는 outlier 에 강건해 winsorize 불필요.
2. family 점수 F = mean(r_i, 결측 제외). 참여 신호 0개면 F = null.
3. composite C = Σ w_f·F_f / Σ w_f (null family 제외). 참여 family < 2 이면 후보 제외(coverage 리포트에 집계).
4. 동점은 유동성(ADTV) 높은 쪽 우선 (임의성 제거, 규칙 명시).

## 5. 레짐 가중 (v0 = 고정 2 프리셋, 적합 금지)

- 판정 입력: `macro("종합", market="KR")` + `quant("레짐", 지수)` + `scanNarrativeRegime`. 3개 중 2개 이상 위험선호면 riskOn.
- 프리셋 (합 1.0, CONTEXT 는 가중치 선택으로만 작용):

| family | riskOn | riskOff |
|---|---|---|
| PRICE | 0.35 | 0.20 |
| FLOW | 0.20 | 0.15 |
| EVENT | 0.20 | 0.20 |
| FUND | 0.15 | 0.35 |
| TEXT | 0.10 | 0.10 |

- 수치는 사전 고정 선언값이다. 과거 데이터로 가중치를 최적화하지 않는다 (과적합 + "검증된 가중치" claim 유혹 차단). replay(03)는 이 고정값의 사후 성적을 측정할 뿐, 역으로 튜닝하지 않는다. 튜닝하려면 held-out 규약을 갖춘 별도 사이클로.

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
