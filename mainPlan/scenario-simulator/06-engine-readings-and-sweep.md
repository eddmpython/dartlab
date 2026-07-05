# 06. 엔진 판독·가정 sweep : 시뮬레이터의 "현재" 축 (검증 루프를 채우는 조각)

상태: v1.0 (2026-07-05 운영자 합의 "여기에 태우자". 토론 이력·P0 실측 = `../weekly-uplift-shortlist/05-progress-ledger.md`)
위치: 본 문서군의 시간축에서 **현재** 를 담당한다. 과거 = expectation 원장 채점(expectation-grid, 라이브 가동), 미래 = Play fan(05). 00 §8b 의 conditional-signature 판정("검증 루프 미완이라 시그니처가 될 설계")에서 비어 있다고 지목된 **그 검증 루프의 대규모 실장**이 본 축이다.

---

## 1. 본질 (합의 원문)

한곳(L2.5 `simulate`)에서 모든 하위 엔진을 호출해 데이터를 받고, 출처별·엔진 성격별로 투영해
한곳에서 의견화(판독)한다. 전량을 발행 시점에 봉인하고 5거래일 뒤 채점해 성적을 누적한다.
그 의견 위에 모든 방향과 if(이 방향이라면·이런 상황이라면)의 수백수천 가정을 돌린다.
수용된 규율 1건(다중검정): 종목 선정은 최고 성적 가정이 아니라 **가정 강건성(median)** 으로,
가정 자체도 판독처럼 봉인·채점되어 살아남는 가정이 가중을 얻는다. 최적은 사전 탐색의 선언이
아니라 원장의 사후 증명이다.

## 2. 판독 계약 (Reading)

```python
@dataclass(frozen=True)
class Reading:
    stockCode: str; market: str            # KR 전상장사 / US EDGAR (시장 내 완결, 혼합 순위 금지)
    surface: str                           # 표면 id (전수 레지스트리 키: "scan.orders"·"quant.momentum"·
                                           #  "allFilings.유상증자"·"panel.accrualsDelta" ...)
    asOf: str; horizon: int                # PIT 기준일 · 거래일 지평 (v0=5, 표면별 자연 지평 다중 가능)
    direction: int; score: float | None    # +1/-1/0(중립·기권) · 강도
    abstainReason: str | None              # 기권 1급 출력 (0 대체 금지, 기권률도 채점 대상)
    refs: dict                             # 근거 dateRef/datasetRef (출처는 여기 자연 기록)
```

모든 회사가 매주 표면마다 "판독/중립/기권" 셋 중 하나로 기록된다 (silent 누락 0, 전상장사 규약).

## 3. 표면 전수 등재 (선별 0)

레지스트리는 손으로 쓰지 않고 기존 카탈로그에서 자동 열거한다: `dartlab.scan()` 24축 ·
`dartlab.quant()` 46축 · allFilings 공시 타입(KR 일별 + US, rcept_dt 보존 = 과거 replay 가능) ·
extractionCatalog 개념(사업보고서·재무제표가 주연: 분기 도착 이벤트 + 재무x가격 괴리는 매주
재발화) · gather 축(price·flow·news·narrative·research) · L2 verb(analysis·credit·industry·macro).

**panel·사업보고서 탈탈털기 카탈로그의 실체 (2026-07-05 가동 확인)**: ① `core/extractionCatalog.py`
(L0) = 개념 카탈로그 SSOT 88개념·9카테고리(financialStatement·note·governance·capital·workforce·
debt·segment·narrative·filingMeta), `getExtractionConcepts()/getConcept()/resolveNoteKey()`.
② `frame/inventory.py` (L1.5) = 회사별 전 단위 전수 열거 `reportInventory(code)` (정규화 Panel
wide 에서 열거, round-trip 100%·collision 0). 둘 다 dossier 폐기(df41ee60e)에서 **의도 보존**된
자산이고 simulate(L2.5)가 하향 import 로 직접 소비한다 (계층 위반 0). 단, handle→값 추출
라우팅은 dossier 와 함께 제거되었으므로 **table.py(상 차리기)가 카탈로그 구동으로 직접 구현**
한다 (P1 범위. 개별 작업대 부활 아님: 시뮬레이터 내부 소비 전용).

- 방향화 규칙도 표면마다 선언 1줄로 기록. 방향 불가 표면은 빼지 않고 무방향 등재 + 양방향 채점.
- 죽은 표면은 목록에서 안 사라진다. 성적이 죽었음이 기록되고 가중이 0 으로 갈 뿐.
- 개별 데이터 작업대 신설 금지 (dossier 폐기 df41ee60e 선례). 호출계약은 엔진 소유 verb 로만.
  프론트 작업대(ui runtime fetch)만 별도 유지.

## 4. 주간 루프 : 판독 → 봉인 → 채점 (기존 원장 자산 재사용)

- 발행·봉인: `expectationCycle` 확장 `issueReadings` (issueMacro 동형. 유일 writer·append-only·
  issuedLive 규약 그대로). 선정 이전 전량 봉인 = selection bias 구조적 차단.
- 채점: 5거래일 후 시장 내 초과수익(유니버스 동일가중 + 지수 병기)으로 전 판독 채점.
- 성적표: 표면 x 시장 x 산업 x 레짐 x 지평. 수축(표면 ← 상관 클러스터 ← 전체) + 표본 게이트
  미달 "미검증" 라벨 = **03 §4.4 G16(coverage·PIT·skill 게이트) 정합** (새 게이트 발명 0).
  독립성 묶음은 분류표가 아니라 채점 데이터의 상관이 정한다.
- 09 §10 fatal② "forward-test write 끝단" 을 본 루프가 대규모로 채운다 (주간 전종목 x 전표면).

## 5. 가정 sweep : 두 층, 한 원장

| 층 | 내용 | 기존 자산과의 정합 |
|---|---|---|
| 상황 가정 | "이 방향이라면·이런 상황이라면": 레짐 상태·명명 프리셋 (baseline/adverse/china_slowdown/rate_hike/semiconductor_down) | 신설 0: `getPresetScenarios("KR")` 1급 소비, `provenance=preset:{scenarioId}` (02 §명명 프리셋 A1 규약 그대로) |
| 결합 가정 | 표면 가중 스킴·게이트 강도·유동성 조건·합의 임계·지평 | 신규 경량 row. AssumptionLedgerRow(02 §2.5, 코드 0건 설계)의 규율을 첫 적용: 단위·기간 필수, source·status·반증조건(=사전등록 protocol) 필수 |

- 격자 수백~수천 벌은 판독 행렬(주 1회 계산) 위의 재조합이라 전부 벡터화 (P0 실측: 17년
  전종목 replay 4초 → 1,000벌 x 17년 = 분 단위).
- 선정 = 강건성(대다수 가정에서 반복 상위, median). 최고 성적 가정 인용 금지 (다중검정).
- 가정 벌도 매주 봉인·채점. 과거 sweep 은 bootstrap(issuedLive=False 영구 표기), 권위는 라이브만.
- 격자 범위 변경은 분기 사전등록으로만.

## 6. 파생 뷰 (제품 표면: 주간 상승후보 100 → 근거 10)

- board100(시장별) = 강건 합의 상위 100 + 표면별 의견 분해 + 커버리지·기권 + refs.
- top10 = 살아남은 가정들이 동시에 가리키는 곳 + red-flag 게이트(감사의견·자본잠식·credit
  최하등급+Altman 교차·시장조치 근사·유동성 최하위) + forecast 구간 비모순. 미달 주는 그 수만 발행.
- 근거 서사 = 판독 rank 나열 금지. 사업보고서 직독(frame·report: 세그먼트·수주잔고·리스크 문단
  변화)이 본체 + 해당 표면·가정의 성적표 인용(수축 추정치·표본·미검증 라벨).
- 언어 규율 = 본 문서군 발간표면 투자권유 lint(09 fatal①, T1 빌드완료) + never-claim 상속:
  "규칙 기반 후보. 투자 추천·자문 아님. 성과 보장 없음. 가격수익(배당·정조정 제외) 기준."
  US 는 생존편향 상방 왜곡 명시(G9 해소 전).

## 7. 모듈 배치 (전부 `simulate/` 내부, 신설 엔진 0)

reading.py(계약+임계 SSOT) · surfaces.py(자동 열거+방향화 선언) · table.py(상 차리기: 전종목 x
전표면, 무bake·벌크 우선·Company 루프 0) · opine.py(의견화) · sweep.py(격자+강건성) ·
board.py(파생 뷰) · runweek.py(주간 오케스트레이션) · readingScorecard.py(수축 성적표) +
expectationCycle 확장(issueReadings) + entry 확장(기존 `dartlab.simulate` 계열 verb 추가).
테스트는 `tests/simulate/` 미러. 상세 파일·단계·런북 = `../weekly-uplift-shortlist/02-build.md`
를 본 절이 승계 (P0 잔여 → P1 골격 → P2 sweep·파생 뷰 → P3 라이브 → P4 갭 → P5 UI).

## 8. P0 실측 근거 (2026-07-05, 완료분)

- KR 전종목 2016~2026 주간 판독 replay: 543주 = **3.7초**. 가격 표면 단독 edge 0 (base 0.428
  = hit 0.428) = 정직한 기준선. 수정주가 근사 가설은 검증 후 기각.
- US EDGAR: 가격 4,122 티커 전수 수령, 사용가능 54%·열화 46%(재bake 필요=G9). 546주 8.4초,
  전 연도 양(+)이나 생존편향 왜곡 명시.
- Company 메모리가드: 30사 순차 RSS ~900MB 정체 (순차 한정 완화 근거).
- 갭 원장 G1~G10 = `../weekly-uplift-shortlist/03-gaps.md`.
- **이벤트 표면 전수 실측 (2026-07-05)**: allFilings KR 2022-11~ 구간 29.3만 이벤트 x 320타입
  전수 채점 2.5초. 음(-) 표면이 두텁고 경제 정합 (신주인수권행사 -4.0%·거래정지해제 -2.3%·
  유상증자 청약 -2.0%·조회공시 -1.8%·최대주주변경 -1.8%·전환청구권 -1.5%). 방향화 선언의
  실측 근거 확보. 양(+) 평균은 우편향 이상치 견인이라 median·hit 동행 규율 확정.
- **sweep 실측 (2026-07-05)**: 200벌 x 543주 12.2초 (1,000벌 ≈ 1분). 다중검정 실증: 최고 가정
  +0.50%/주 vs 중앙값 +0.04%/주 (edge 0 신호 위 선택 편향). 강건 30종목 vs 최고가정 138종목
  교집합 3 → §5 의 median 강건성 규율이 실물로 검증됨.

## 9. 잔여 (P0 나머지 → 착수 중)

이벤트 표면 replay·sweep 프로토타입 = **완료 (§8)**. 잔여: 이벤트 표면을 판독 행렬에 편입해
기준선 대비 합의 성능 재실측 · panel PIT(정정 look-ahead)·fund 표면 실측 · 표면 상관 행렬 →
수축 묶음 · 뉴스 태깅 커버리지(G8). 데이터 한계: allFilings KR 과거 커버리지 = 2022-11~
(2016 replay 는 월별 백필 절차 필요, 운영자 트리거 존재).
