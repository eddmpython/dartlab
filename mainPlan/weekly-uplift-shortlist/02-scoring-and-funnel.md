# 02. 엔진 판독기 계약과 메타 결합 : 전종목 x 전엔진 주간 판독

> v0.3 구조 전환(운영자 지시): "오를 기업을 선정하는" 신호 깔때기가 아니라, **엔진별 판독기가 매주 모든 회사에 자기 의견을 내고, 1주 뒤 전부 채점되어, 어떤 엔진이 어떤 종목에서 강한 근거인지가 데이터로 누적되는 시뮬레이터**를 짓는다. 후보 100/10 은 이 판독 원장의 파생 뷰다.

## 0. 왜 구조를 바꿨나 (v0.2 의 한계)

v0.2 는 엔진 출력을 익명 신호 컬럼으로 합성해 최종 목록만 채점했다. 그 구조에서는 (a) 어느 엔진이 강한 근거인지 알 수 없고, (b) 엔진별·종목별 정확도 프로파일이 안 쌓이며, (c) 학습 표본이 주당 발행 100행에 갇힌다. v0.3 은 판독을 엔진 단위로 보존해 봉인한다: 주당 표본 = 유니버스 x 판독기 수 (~2,800 x 8 ≈ 2만+ 행). 이 원장 자체가 제품의 핵심 자산이다.

## 1. EngineReading 계약 (모든 판독기의 공통 출력)

```python
@dataclass(frozen=True)
class EngineReading:
    stockCode: str
    reader: str            # 판독기 id (price/flow/event/fund/text/forecast/credit/context)
    asOf: str              # 판독 기준일 (그 시점까지의 데이터만, PIT)
    direction: int         # +1 상승 / -1 하락 / 0 기권·중립
    score: float | None    # -1~+1 연속 강도 (기권이면 null)
    horizon: int           # 5 (거래일)
    coverageOk: bool       # 판독에 필요한 데이터가 충분했는가
    abstainReason: str | None  # 기권 사유 (데이터 결측·커버리지 밖·신호 상충)
    refs: dict             # 근거 dateRef/datasetRef (엔진 evidence 규약)
```

- **기권(abstain)은 1급 출력이다.** 커버리지 없는 종목을 억지로 판독해 0 으로 채우지 않는다. 기권률·기권 사유 분포도 채점 대상 (기권이 과도한 판독기는 근거 엔진으로서 가치가 낮다는 것 자체가 측정 결과).
- 모든 회사에 대해 매주 발행한다. "판독함(방향±1) / 중립 / 기권" 셋 중 하나가 반드시 기록된다. 전상장사 규약: 판독 대상에서 시총·규모로 silent 제외 금지.

## 2. v0 판독기 8종 (엔진별 어댑터)

| reader | 원천 엔진 verb (재사용) | bulk 경로 | 기권 조건 |
|---|---|---|---|
| price | quant/signal momentum·volume + gov/prices wide | ✅ 전종목 벌크 (Company 루프 0) | 상장 20거래일 미만 |
| flow | gather("flow")·smartMoneyZ | ⚠ G1 전까지 lazy(1차 결합 상위 ~300 + 직전주 top 유지분) | 벌크 미커버 종목 = 기권 |
| event | scan orders·capital·insider + watch diff | ✅ scan 축이 이미 횡단면 | 최근 유효 이벤트 없음 = 중립(기권 아님) |
| fund | quant/alphas(SUE·fundmom·piotroski 등) + scan financial | ✅ prebuilt 횡단면 | 재무 미공시·결손 = 기권 |
| text | gather("narrative") tone + 공시톤 | ⚠ 태깅 커버리지 실측(G8) 후 확정 | 태깅 없음 = 기권 |
| forecast | quant("예측") conformal 5d | ⚠ 종목별 호출이라 전종목 불가. P0 에서 bulk 변형(gov/prices 직접 fit) 실측, 불가 시 결합 상위 후보군만 판독 + 나머지 기권 | 데이터 부족 error = 기권 |
| credit | credit 스코어카드 + scan audit/debt (하락·위험 방향 특화) | ✅ 횡단면 | 금융업 등 산식 밖 = 기권 |
| context | macro 레짐 + industry lifecycle + customs 수출 사이클 | ✅ 시장·산업 레벨 | 종목 단위 의견 없음: 산업 소속을 통한 틸트 판독 (약한 |score| 상한) |

- 판독기 내부 신호 구성은 v0.2 의 지평 정합 원칙(단기 reversal·수급 지속·이벤트 드리프트 우선)과 상관 중복 처리(|ρ|>0.7 클러스터 대표 1개, P0 실측 확정)를 그대로 상속한다.
- 판독기 추가·제거는 레지스트리 선언 변경으로만 (실행 중 동적 추가 없음).

## 3. 판독기 내부 합성 (reader 는 자기 의견만 낸다)

- v0: 소속 신호의 cross-sectional percentile rank 평균 → score ∈ [-1,+1] 스케일. direction = score 부호, |score| < 중립 밴드(사전 선언)면 0.
- v1 승격 경로: 판독기별 성적이 원장에 쌓이면 reader 내부 가중을 주간 횡단면 회귀(Fama-MacBeth + shrinkage, purged walk-forward 검증)로 승격한다. v0.2 의 가중 사다리는 폐기가 아니라 **reader 내부로 이동**한 것.
- reader 끼리는 서로의 출력을 보지 않는다 (독립성이 합류 근거의 전제).

## 4. 채점과 엔진 성적표 (이 제품의 핵심 산출물)

매주 5거래일 경과 후 전 reading 채점:

- **hit**: 유니버스 초과수익(동일가중 평균 대비)의 부호와 direction 일치. 중립·기권은 hit 계산에서 제외하되 별도 집계.
- **강도 진단**: score 와 실현 초과수익의 주간 rank-IC (내부 진단 전용, 대외 수치 claim 금지).
- **분해 축**: reader 전체 → 산업 → 규모 버킷 → 레짐 → 종목. "어떤 엔진이 강한 근거인가"와 "어떤 종목·산업에서 정확한가"가 이 분해에서 나온다.
- **소표본 규율 (불가침)**: 종목 단위는 연 52관측이라 잡음이 크다. empirical-Bayes 수축: 종목 추정치 ← 산업 추정치 ← reader 전체 추정치로 shrink. 표본 게이트 미달 세그먼트는 "미검증" 라벨 강제 (expectation-grid 02 §4 상속). 수축 전 원시 hit rate 를 근거로 인용 금지.

## 5. 메타 결합 : 측정된 신뢰도가 가중치다

- reader 가중 w_r = shrunk trailing 초과적중률 (지수 감쇠 창, 사전 선언). 산업별 프로파일 (reader x 산업) 을 우선 적용, 종목 단위 프로파일은 표본 게이트 통과 세그먼트에서만.
- combined score(종목) = Σ w_r(산업) · score_r / Σ w_r (기권 reader 제외, 참여 reader < 2 이면 후보 제외 + coverage 집계).
- **cold start**: live 원장이 없는 초기엔 17년 주간 PIT replay 로 판독기별 의사-성적을 bootstrap 한다 (전 레코드 issuedLive=False 영구 표기, 03 §3). live 누적이 쌓일수록 지수 감쇠가 replay 성분을 자연 대체.
- 가중 갱신은 주간 채점 후 자동이되, 게이트·수축 파라미터 변경은 분기 사전등록으로만.

## 6. 깔때기 (파생 뷰로 재정의)

```
S0 위생      전상장사, 명시 제외만 (정리매매·스팩·상장 20거래일 미만). no-silent-cap 로그
S1 판독      8 판독기 x 전종목 EngineReading 발행
S2 봉인      readings 전량 ledger 봉인 (top 선정 전에 봉인 = selection bias 원천 차단)
S3 메타결합  신뢰도 가중 combined score
S4 board100  combined 상위 100 + reader 별 의견 분해 동행
S5 top10     합류 룰: 신뢰 상위 독립 reader ≥ 3 이 동일 방향(+1) + red-flag 게이트(credit/audit/
             disclosureRisk/유동성) + forecast reading 비모순. 순위 = (합의 reader 수, combined score).
             통과 < 10 이면 그 수만큼만 발행
```

## 7. 출력 스키마와 결측 규약

- readings 테이블(전종목 x reader), board100, top10 dossier, reader scorecard 4종. 모든 수치에 asOf/dateRef, 결측은 null 유지 (0 대체 0건).
- top10 dossier 의 근거 서술이 바뀐다: "신호 값" 나열이 아니라 **"reader 별 의견 + 그 reader 의 해당 산업 트랙레코드(수축 추정치·표본 수·미검증 여부)"** 를 함께 싣는다. 근거의 강도가 주장이 아니라 성적표 인용이 된다.
- 주간 스냅샷은 `data/shortlist/` parquet append (재현성).

## 8. 기존 axis 회피 룰 정합 (유지)

- 단일 신호·단일 reader 단정 금지: 합류 룰이 다엔진 합의를 강제.
- scan 후보를 검증 없이 투자 결론 확정 금지: top10 은 조사 착수 목록 + dossier 검증 동행.
- 결손 0 대체 금지: 기권 1급 출력.
- 성과 보장·"검증된 팩터" 어휘 금지: 성적표는 항상 기간·벤치마크·표본·미검증 라벨 동행.
