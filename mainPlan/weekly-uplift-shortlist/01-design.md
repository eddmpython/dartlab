# 01. 설계 : 계약 · 표면 전수 등재 · 판독-봉인-채점 · 가정 sweep

## 1. 본질 (합의 원문)

한곳(L2.5 `simulate` 엔진, 기존 확장)에서 모든 하위 엔진을 호출하고, 그들의 데이터를 받아, 그들의 성격과
카테고리를 투영해 한곳에서 의견화한다. 그 의견 위에 모든 방향과 if(이 방향이라면·이런
상황이라면)의 수백수천 가정을 돌린다. 수용된 수정 1건: 종목 선정은 최고 성적 가정이 아니라
**가정 강건성**으로, 가정 자체도 **봉인·채점**되어 살아남는 것이 가중을 얻는다.

## 2. 판독 계약 (Reading)

```python
@dataclass(frozen=True)
class Reading:
    stockCode: str         # 종목 (KR 6자리 / US ticker)
    market: str            # KR | US (시장 내 완결, 혼합 순위 금지)
    surface: str           # 판독 표면 id (전수 레지스트리 키. 예: "scan.orders", "quant.momentum",
                           #  "allFilings.유상증자", "panel.accrualsDelta")
    asOf: str              # 판독 기준일 (그 시점까지의 데이터만, PIT)
    horizon: int           # 거래일 (v0=5. 표면별 자연 지평 다중 발행 가능)
    direction: int         # +1 / -1 / 0(중립·기권)
    score: float | None    # -1~+1 강도 (기권 null)
    abstainReason: str | None
    refs: dict             # 근거 dateRef/datasetRef (출처는 여기 자연 기록, 별도 귀속 체계 없음)
```

- 기권은 1급 출력: 데이터 없는 종목-표면을 0 으로 채우지 않는다. 기권률도 채점 대상.
- 전상장사 규약: 모든 회사가 매주 표면마다 "판독/중립/기권" 셋 중 하나로 기록된다. silent 누락 0.

## 3. 표면 전수 등재 (선별 0)

판독 표면 레지스트리는 손으로 쓰지 않고 기존 카탈로그에서 자동 열거한다. 열거 원천:

| 원천 | 표면 예 | 비고 |
|---|---|---|
| `dartlab.scan()` 축 가이드 (24) | scan.orders·scan.insider·scan.growth... | 횡단 작업대 |
| `dartlab.quant()` 축 가이드 (46) | quant.momentum·quant.surprise·quant.괴리... | 의견 축 |
| allFilings 공시 타입 목록 | allFilings.유상증자·수주·자사주·소송... | rcept_dt 보존 = 과거 replay 가능. KR `data/dart/allFilings` + US `data/edgar/allFilings` 실측 확인 |
| extractionCatalog 개념 (panel·재무제표) | panel.SUE·accrualsDelta·segMixChange·재무x가격 괴리 | 사업보고서·재무제표가 주연 (분기 도착 이벤트 + 가격과의 상호작용은 매주 재발화) |
| gather 축 (price·flow·news·narrative·research...) | flow.smartMoneyZ·news.tone | 원자료 스트림 |
| L2 verb (analysis·credit·industry·macro) | credit.deltaGrade·industry.cycle | 엔진 의견 |

- **방향화 규칙도 선언이다**: 표면마다 "값 → ±1/중립" 규칙을 레지스트리에 한 줄씩 선언 기록.
  방향을 정할 수 없는 표면은 빼지 않고 **무방향으로 등재해 양방향 모두 채점**한다 (선별이
  숨어들 유일한 구멍을 봉쇄).
- 죽은 표면은 목록에서 사라지지 않는다. 성적이 죽었음이 기록되고 가중이 0 으로 갈 뿐.
- 신규 표면 추가 = 카탈로그에 새 축/타입이 생기면 자동 후보 등재. 수동 추가는 없다.

## 4. 주간 루프 : 판독 → 봉인 → 채점

- 매주 각 시장 마감 후: 상 차리기(전종목 x 전표면 스냅, 무bake 직독) → 판독 → **전량 봉인**
  (선정 이전 봉인 = selection bias 구조적 차단. writer 는 기존 L2.5 원장 유일 collector).
- 5거래일 후: 시장 내 초과수익(유니버스 동일가중 + 시장지수 병기)으로 전 판독 채점.
- 성적표: 표면 x 시장 x 산업 x 레짐 x 지평. 소표본은 수축(표면 ← 상관 클러스터 ← 전체)으로
  방어, 표본 게이트 미달은 "미검증" 라벨 강제. 독립성·묶음은 분류표가 아니라 **채점 데이터의
  상관**이 정한다.
- 지평 다중화: 표면은 자기 자연 지평(5d/20d/60d)으로 발행 가능. 재무 표면을 5d 에 강제해
  억울한 성적을 만들지 않는다.

## 5. 가정 sweep (시뮬레이터의 본질)

- 가정(assumption set) = 결합 구성 1벌: {표면 가중 스킴, 레짐 상태, 지평, 게이트 강도, 유동성
  조건, 합의 임계}. 격자로 수백~수천 벌 생성.
- 각 가정은 판독 행렬(주 1회 계산) 위의 재조합이라 전부 벡터화된다. 실측 근거: 17년 전종목
  replay 4초 → 가정 1,000벌 x 17년도 분 단위.
- **선정 = 강건성**: 가정 대다수에서 반복 상위인 종목 (median 기준, max 금지).
- **가정도 봉인·채점**: 유망 가정 벌은 매주 라이브 봉인되어 5거래일 채점. 과거 sweep 은 후보
  가정 bootstrap 일 뿐(issuedLive=False 영구 표기), 권위는 라이브 성적만.
- 가정 격자 자체의 변경(파라미터 범위)은 분기 사전등록으로만.
- **AssumptionLedger 통합 (중복 신설 금지)**: 가정 벌의 계약은 scenario-simulator 가 설계해 둔
  AssumptionLedger(if 토글 SSOT) 를 따른다. 본 sweep 이 그 데이터 모델의 첫 실구현이 되고,
  미래 fan(scenario 잔여 단계)이 같은 원장을 재사용한다. 별도 가정 포맷 신설 = 덕지덕지.

## 6. 파생 뷰 (제품 표면)

- board100 (시장별): 강건 합의 상위 100 + 표면별 의견 분해 + 커버리지·기권 + refs.
- top10: 살아남은 가정들이 동시에 가리키는 곳 (강건성 순위 + red-flag 게이트: 감사의견·
  자본잠식·credit 최하등급+Altman 교차·시장조치 근사·유동성 최하위 + forecast 구간 비모순).
  통과 < 10 이면 그 수만큼만 발행.
- 근거 서사: 판독 rank 나열 금지. **사업보고서 직독**(frame·report: 세그먼트 매출 구성·수주
  잔고·리스크 문단 변화)이 본체이고, 표면·가정의 성적표 인용(수축 추정치·표본·미검증 라벨)이
  동행한다.

## 7. 정직 규약 (불가침, terminal-strategy-lab never-claim 상속)

1. 산출물 고정 문구: "규칙 기반 후보. 투자 추천·자문 아님. 성과 보장 없음. 가격수익(배당·정조정 제외) 기준."
2. "검증된 팩터"·"시장을 이긴다"·"적중률 보장" 어휘 0 (grep 게이트).
3. replay 수치는 밴드·표본 수 동행. IC·t-stat 대외 단정 금지 (내부 진단 전용).
4. 가격 보존형 유니버스(폐지 사유 미구분) 문구. US 는 생존편향 상방 왜곡 명시 (G9 해소 전).
5. 라이브 표본 게이트 통과 전 "미검증" 라벨 강제. 미빌드 성능 주장 금지.
6. 다중검정 규율: 가정 sweep 의 최고 성적 인용 금지. 강건성 분포와 라이브 성적만 인용.

## 8. 사전 검증 (P0 실측이 이미 확보한 것)

- KR 전종목 주간 replay 543주 = 3.7초, US 546주 = 8.4초 (05 원장). 루프 비용은 0 에 수렴.
- 가격 표면 단독 KR edge 0 = 정직한 기준선. 개선은 표면 추가(이벤트·재무)의 기여로 측정.
- allFilings(KR 일별·US)·gov/prices 17년·EDGAR panel 7,391 실재 확인. US 가격 열화 46% = G9.
