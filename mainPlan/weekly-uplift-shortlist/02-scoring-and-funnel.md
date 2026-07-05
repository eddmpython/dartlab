# 02. 엔진 판독기 계약과 메타 결합 : 전종목 x 전엔진 주간 판독

> v0.3 구조 전환(운영자 지시): "오를 기업을 선정하는" 신호 깔때기가 아니라, **엔진별 판독기가 매주 모든 회사에 자기 의견을 내고, 1주 뒤 전부 채점되어, 어떤 엔진이 어떤 종목에서 강한 근거인지가 데이터로 누적되는 시뮬레이터**를 짓는다. 후보 100/10 은 이 판독 원장의 파생 뷰다.
>
> v0.4 정정(운영자 지시): 판독기 단위 = **dartlab 엔진 그 자체** (engine.axisGroup). 독립성은 판독기 정체성이 아니라 **family 태그**로 관리한다 (§2.1).
> v0.5 정정(운영자 방향): 판독은 외부 어댑터가 아니라 **각 엔진의 자체판독 verb** 가 발행한다. L1.5 데이터 작업대(scan·frame) 1회 + L2 엔진(quant·analysis·credit·macro·industry) 1회씩. 수집·봉인·채점은 simulate(L2.5)가, board100/top10 파생 뷰는 얇은 L3 shortlist 가 담당 (04 §1).

## 0. 왜 구조를 바꿨나 (v0.2 의 한계)

v0.2 는 엔진 출력을 익명 신호 컬럼으로 합성해 최종 목록만 채점했다. 그 구조에서는 (a) 어느 엔진이 강한 근거인지 알 수 없고, (b) 엔진별·종목별 정확도 프로파일이 안 쌓이며, (c) 학습 표본이 주당 발행 100행에 갇힌다. v0.3+ 는 판독을 엔진 단위로 보존해 봉인한다: 주당 표본 = 유니버스 x 판독기 수. 이 원장 자체가 제품의 핵심 자산이다.

v0.4 의 핵심 추가 통찰: **라이브 주간 운영에서는 엔진 verb 호출이 그 자체로 PIT 다.** 매주 호출 시점의 데이터로 판독하고 즉시 봉인하므로, 과거 재구성이 불가능한 엔진도 오늘부터 트랙레코드를 시작할 수 있다 (expectation-grid 의 "오늘 시작한 쪽만 가지는 시간 해자" 그대로). 과거 replay bootstrap 은 가격·재무처럼 PIT 재구성이 가능한 엔진만 하고, 나머지는 live-only 로 정직하게 표기한다.

## 1. EngineReading 계약 (모든 판독기의 공통 출력)

```python
@dataclass(frozen=True)
class EngineReading:
    stockCode: str
    engine: str            # 판독기 id = 엔진(.축그룹). 예: "quant.momentum", "scan.orders", "credit"
    family: str            # 독립 정보원 태그: PRICE|FLOW|EVENT|FUND|TEXT|CONTEXT (합류 카운트 단위)
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

### 2.1 두 단위의 분업 : engine (성적표 단위) vs family (독립성 단위)

- **engine** 이 성적표·메타 가중의 단위다. "어떤 엔진이 강한 근거인가"는 이 축으로 답한다. 엔진 안에서 성격이 다른 축 무리는 `engine.axisGroup` 으로 분리 발행한다 (예: quant 의 가격축과 재무축은 정보원이 달라 quant.momentum / quant.alphas 로 분리).
- **family** 는 합류(confluence) 카운트의 단위다. 같은 재무제표에서 나온 quant.alphas 와 scan.financial 이 동시에 긍정이어도 독립 2표가 아니라 FUND 1표다. 이 태그가 없으면 같은 데이터의 메아리가 근거로 둔갑한다.

## 2. v0 판독기 목록 (각 엔진의 자체판독 verb, 전 엔진)

| engine (판독기) | 호출하는 공개 verb 작업대 | family | replay 가능성 | 기권 조건 |
|---|---|---|---|---|
| quant.price | `quant` 가격축 + gov/prices 벌크 (quant/signal) | PRICE | ✅ 2016~ (실측 완료) | 상장 20거래일 미만 |
| quant.flow | `quant("수급")` (gather flow 하향 소비) | FLOW | ❌ live-only (G1 승격 시 ✅) | 벌크 미커버 = 기권 |
| scan.events | `scan("orders"/"capital"/"insider")` + watch diff | EVENT | ⚠ rcept_dt 재구성 실측 (다음 사이클) | 최근 유효 이벤트 없음 = 중립 |
| scan.financial | `scan("growth"/"quality"/"cashflow"...)` 8축 | FUND | ⚠ 분기+rcept 근사 | 재무 미공시 = 기권 |
| quant.alphas | `quant("surprise"/"fundmom"/"piotroski"...)` + panel 심화 (01 §2.6) | FUND | ⚠ rcept 라벨 근사 | 재무 결손 = 기권 |
| quant.forecast | `quant("예측")` conformal 5d | PRICE | ⚠ bulk 변형 실측 | 데이터 부족 = 기권 |
| quant.text | `quant("공시심리"/"톤변화")` + `gather("narrative")` | TEXT | ❌ live-only (G8 실측 후) | 태깅 없음 = 기권 |
| analysis | `c.analysis(...)` 재무 인과 요약의 방향화 | FUND | ❌ live-only | 산식 밖 = 기권 |
| credit | `CreditScorecard` + `scan("audit"/"debt")` | FUND(위험) | ⚠ 재무 기반 부분 재구성 | 금융업 등 산식 밖 = 기권 |
| industry | `industry()` lifecycle·밸류체인 위치 | CONTEXT | ❌ live-only | 미분류 산업 = 기권 |
| macro | `macro("종합"/"cycle")` 레짐 틸트 (산업 경유) | CONTEXT | ⚠ 지표 이력으로 부분 | 종목 직접 의견 없음 (|score| 상한) |
| frame.notes | 정기보고서 노트 변화 (frame/narrative·inventory) | TEXT/EVENT | ❌ live-only | 노트 부재 = 기권 |

- 판독 주체에 gather(L1)는 없다: 수집 엔진은 원자료만 내고, 가격·수급의 의견화는 quant 소유 (04 §1.1). 시작 구성은 위 12개 전부가 아니어도 된다: P1 은 replay 가능 4~5개로 출발하고, **live 봉인은 전 엔진 동시 시작** (live 는 어댑터만 있으면 비용이 verb 호출뿐).
- 판독기 내부 신호 구성은 v0.2 의 지평 정합 원칙(단기 reversal·수급 지속·이벤트 드리프트 우선)과 상관 중복 처리(|ρ|>0.7 클러스터 대표 1개, P0 실측 확정)를 그대로 상속한다.
- 판독기 추가·제거는 선언 변경으로만 (실행 중 동적 추가 없음). 판독 로직은 그 엔진이 소유(자체판독)하고, simulate 수집기와 shortlist 파생 뷰는 발행 0 (공동 작업대 SSOT 규약).

## 3. 판독기 내부 합성 (reader 는 자기 의견만 낸다)

- v0: 소속 신호의 cross-sectional percentile rank 평균 → score ∈ [-1,+1] 스케일. direction = score 부호, |score| < 중립 밴드(사전 선언)면 0.
- v1 승격 경로: 판독기별 성적이 원장에 쌓이면 reader 내부 가중을 주간 횡단면 회귀(Fama-MacBeth + shrinkage, purged walk-forward 검증)로 승격한다. v0.2 의 가중 사다리는 폐기가 아니라 **reader 내부로 이동**한 것.
- reader 끼리는 서로의 출력을 보지 않는다 (독립성이 합류 근거의 전제).

## 4. 채점과 엔진 성적표 (이 제품의 핵심 산출물)

매주 5거래일 경과 후 전 reading 채점:

- **hit**: 유니버스 초과수익(동일가중 평균 대비)의 부호와 direction 일치. 중립·기권은 hit 계산에서 제외하되 별도 집계.
- **강도 진단**: score 와 실현 초과수익의 주간 rank-IC (내부 진단 전용, 대외 수치 claim 금지).
- **분해 축**: engine 전체 → 산업 → 규모 버킷 → 레짐 → 종목. "어떤 엔진이 강한 근거인가"(운영자 질문의 단위)와 "어떤 종목·산업에서 정확한가"가 이 분해에서 나온다.
- **소표본 규율 (불가침)**: 종목 단위는 연 52관측이라 잡음이 크다. empirical-Bayes 수축: 종목 추정치 ← 산업 추정치 ← engine 전체 추정치로 shrink. 표본 게이트 미달 세그먼트는 "미검증" 라벨 강제 (expectation-grid 02 §4 상속). 수축 전 원시 hit rate 를 근거로 인용 금지.

## 5. 메타 결합 : 측정된 신뢰도가 가중치다

- engine 가중 w_e = shrunk trailing 초과적중률 (지수 감쇠 창, 사전 선언). 산업별 프로파일 (engine x 산업) 을 우선 적용, 종목 단위 프로파일은 표본 게이트 통과 세그먼트에서만.
- **family 내 메아리 통제**: 같은 family 의 엔진들은 먼저 family 점수로 (신뢰도 가중) 평균한 뒤 family 간 결합한다. 같은 재무제표에서 나온 의견 셋이 세 배 가중되는 것을 구조로 차단.
- combined score(종목) = Σ w_f · familyScore_f / Σ w_f (기권 제외, 참여 family < 2 이면 후보 제외 + coverage 집계).
- **cold start**: live 원장이 없는 초기엔 17년 주간 PIT replay 로 판독기별 의사-성적을 bootstrap 한다 (전 레코드 issuedLive=False 영구 표기, 03 §3). live 누적이 쌓일수록 지수 감쇠가 replay 성분을 자연 대체.
- 가중 갱신은 주간 채점 후 자동이되, 게이트·수축 파라미터 변경은 분기 사전등록으로만.

## 6. 깔때기 (파생 뷰로 재정의)

```
S0 위생      전상장사, 명시 제외만 (정리매매·스팩·상장 20거래일 미만). no-silent-cap 로그
S1 판독      전 엔진 자체판독 x 전종목 EngineReading 발행 (simulate 가 순회 수집)
S2 봉인      readings 전량 ledger 봉인 (top 선정 전에 봉인 = selection bias 원천 차단)
S3 메타결합  신뢰도 가중 combined score
S4 board100  combined 상위 100 + reader 별 의견 분해 동행
S5 top10     합류 룰: 긍정(+1) 판독이 서로 다른 family ≥ 3 을 덮음 + red-flag 게이트(credit/audit/
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
