---
id: engines.industry
title: Industry
kind: curated
scope: builtin
status: observed
category: engines
purpose: Industry 엔진은 단일 종목을 산업 분류 (taxonomy.json) 의 공정 단계와 peer 그룹에 연결해 밸류체인 위치·동종 비교 맥락을 제공한다. 트리거 — '산업', '섹터', '업종', '밸류체인', 'industry'.
whenToUse:
  - Industry
  - industry
  - 산업 분석
  - 섹터 분석
  - 밸류체인
  - 공정 단계
  - peer 그룹
  - 동종업종
  - 산업 지도
  - 산업 라이프사이클
  - lifecycle
  - Vernon phase
  - 도입·성장·성숙·쇠퇴
inputs:
  - industryId 또는 종목코드 (Company-bound)
  - stage 필터 (선택)
  - summary / timeline / lifecycle 모드
outputs:
  - 산업 가이드 DataFrame
  - 공정·종목 DataFrame
  - 산업 위치 dict (Company-bound)
  - peer 종목 list
capabilityRefs:
  - industry
  - Company.industry
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.company
  - engines.scan
sourceRefs:
  - dartlab://skills/engines.industry
requiredEvidence:
  - target
  - industryId
  - stage
  - tableRef
  - executionRef
  - sourceRef
expectedOutputs:
  - 산업 ID / 산업명
  - 공정 단계 + 종목 list
  - 매출/영업이익 집계 (summary)
  - 연도별 공정 매출 추이 (timeline)
  - 라이프사이클 phase 시계열 (lifecycle — 도입·성장·성숙·쇠퇴)
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
failureModes:
  - 산업 ID 를 추측해 호출 — `dartlab.industry()` 가이드 미확인
  - 공정 단계명을 추측 — `dartlab.industry(industryId)` 결과의 공정 컬럼 미확인
  - summary 와 timeline 동시 호출 (둘 중 하나만)
  - peer 의 산업 분류 신선도 미확인 (taxonomy 운영자 수동 갱신)
forbidden:
  - 결손값을 0 으로 채우지 않는다.
  - peer 그룹을 추측해 답변하지 않는다 (반드시 industry() 결과 또는 Company.industry().peers 인용).
  - 공개 호출·반환 형태가 바뀌었는데 본 skill 갱신 없이 완료 처리하지 않는다.
examples:
  - 반도체 산업 공정 단계 확인
  - 삼성전자 밸류체인 위치 (전공정/후공정/장비)
  - 자동차 산업 peer 그룹 추출
  - 공정별 매출 집계 (summary)
  - 연도별 공정 매출 추이 (timeline)
  - 산업 라이프사이클 phase 분류 (lifecycle — Vernon 3-phase + 쇠퇴)
procedure:
  - 산업 목록 확인은 `dartlab.industry()` (가이드 DataFrame).
  - 산업 ID 정한 뒤 `dartlab.industry("semiconductor")` 로 공정·종목 확인.
  - 단일 기업 위치는 `dartlab.Company(code).industry()` — chainId·stage·confidence·peers dict.
  - 공정 매출 집계는 `dartlab.industry(industryId, summary=True)`; `year` 생략 시 실제 관측된 최근 연간 사업연도.
  - peer 그룹을 다른 엔진에 전달할 때는 종목코드 list 만 추출 (전체 dict 통째 전달 금지).
linkedSkills:
  - engines.company
  - engines.analysis
  - engines.scan
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-05-08'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
visualRefs:
  - "engines.viz.peerMatrix"
  - "engines.viz.tableBackedChart"
---

## 엔진 역할

`industry` 는 단일 종목을 *밸류체인 공정 단계* 와 peer 그룹에 연결하는 **L2 분석엔진** (산업 매퍼) 이다. 산업 분류 (`taxonomy.json`) 와 종목→공정 매핑 (`nodes.json`) 을 데이터로 들고 있고, 매칭/집계/lifecycle 파이프라인이 분석 표면을 만든다. 분류체계는 운영자가 JSON 직접 편집해 갱신.

회사 재무 인과는 `analysis`, 부도 위험은 `credit`, 시장 매크로는 `macro`, 정량 가격 신호는 `quant`, 횡단 후보 발굴은 `scan` (L1.5) 이 담당. industry 는 *산업 컨텍스트 분석* 을 다른 L2 엔진과 **동등한 도메인 격리** 로 제공한다 — 다른 L2 를 직접 import 하지 않고 결합은 L3 조합기 `story` 가 한다.

## 공개 호출 방식

```python
import dartlab

# 1. 산업 목록 가이드
guide = dartlab.industry()
# → DataFrame: 산업ID · 산업명 · 공정수

# 2. 특정 산업의 공정·종목
nodes = dartlab.industry("semiconductor")
# → DataFrame: 공정 · 공정명 · 종목코드 · 종목명 · 역할 · 위치

# 3. 공정 단계 필터
fab_only = dartlab.industry("semiconductor", stage="fab")

# 4. 공정별 매출/영업이익 집계 (최근 관측 연간 사업연도)
summary = dartlab.industry("semiconductor", summary=True)
# → DataFrame: stage · 공정명 · 매출(조) · 영업이익(조) · 기업수 · 영업이익률(%) · coverageRatio

# 5. 연도별 공정 매출 추이
timeline = dartlab.industry("semiconductor", timeline=True)

# 6. 단일 기업의 산업 위치 (Company-bound)
c = dartlab.Company("005930")
position = c.industry()
# → dict: chainId · chainName · stage · stageLabel · confidence · matches · products · peers
```

## 강행 호출 룰 (agent 답변 품질 회귀 차단)

1. **단일 종목 산업 질문 = `Company.panel("IS").data.industryBadge` 1 회 인용** (Track E 자동 부착). `EngineCall("industry")` 별도 호출 금지 — industryBadge 가 이미 industryName · stageName · phase · peers · confidence 완전 형태.
2. **여러 종목 / 산업 전체 질문은 `EngineCall(apiRef="industry", args={...})` 1 차** — RunPython 직접 industry parquet 로드 금지.
3. **본문 안 산업명·phase·peers 에 `[tableRef:...]` inline 표기 필수**. lifecycle phase (도입/성장/성숙/쇠퇴) 는 `[conf:30]` 기본 (Vernon 3-phase 정의 기준 변동성).
4. **공정 (chainName) 비교는 같은 산업 안에서만**. cross-industry 비교는 한계 명시 필수.

## 호출 동작

`dartlab.industry()` (인자 없음) → 등록된 산업 목록 가이드 DataFrame.

`dartlab.industry(industryId)` → 해당 산업의 공정·종목 DataFrame. `stage` 로 특정 공정만 필터.

`summary=True` → `year` 기준 공정별 매출/영업이익 집계. `year=None`이면 finance 원장의 최근 연간 사업연도를 선택한다. `timeline=True` → 연도별 공정 매출 시계열. `lifecycle=True` → 산업 라이프사이클 phase 시계열 (Vernon 3-phase + 쇠퇴. 도입 ≥30% / 성장 10~30% / 성숙 0~10% / 쇠퇴 0% 미만 YoY). `concentration=True` → 산업 매출 시장구조 집중도 (HHI/CR3 + 상위 5사). `dynamics=True` → 이익 풀 동학(아래). `polarization=True` → 산업 양극화 교차검증(아래). 동시 사용 X. 우선순위 summary > timeline > lifecycle > concentration > dynamics > polarization.

`concentration=True` 해석 한계: 값은 **동일 회계연도 상장사 매출 기준** 상대 집중도다. 서로 다른 연도는 혼합하지 않으며 동일연도 표본 3사·커버리지 60% 미만이면 `unavailable`, 60~80%면 `partial`이다. 반환의 `상태·회계연도·커버리지(%)·제한사유`를 HHI와 함께 인용한다. 비상장·해외 매출 제외라 *절대 시장점유율이 아니다*. HHI 라벨("분산/중간/집중")은 DOJ 척도 차용일 뿐 시장 획정(market definition)을 거치지 않았으니 반독점 판정 어휘로 인용 금지. `calcSectorMetrics`(회사가 분포 어디 위치)와 직교한다. 이건 *산업 자체가 과점이냐 분산이냐*를 본다. 회사 단위 공급망 집중도(고객/거래처 HHI)는 `recipes.industry.supplyChainConcentration` 별도다.

`dynamics=True` → 이익 풀 동학: 공정별 첫/끝해 영업이익 **levels(조)** + **argmax 리더 교체** 판정(끝해 1위 ≠ 첫해 1위 = **이동형**, 같으면 **집중형**) + **적자전환** 플래그(첫해>0·끝해<0). 해석 한계: **share(%) 미사용**(총합 zero-crossing 시 점유율 폭발 — 반도체 2023 -800%), levels만. **생존편향**(현 멤버십을 과거 연도에 소급 — 복원 불가)을 `생존편향주의` 컬럼으로 1급 표기. 4년 윈도라 "추세" 아닌 *방향 신호*. KO는 대부분 단일 stage 지배(집중형)·진짜 이동형은 희귀 — workhorse는 적자전환+levels이지 migration 라벨 아님. 미래 리더 예측·동학 점수화·이익흐름 Sankey 금지(folk통계/인과 함의).

`polarization=True` → 산업 양극화: **독립 두 자료원 교차검증**으로 "승자독식 심화 vs 동질 평준화" 판정. ① 마진 렌즈 = 멤버 영업이익률(OPM) **IQR(p75−p25)** 첫해→끝해 방향(확대/축소) + 끝해 레벨. ② 밸류 렌즈 = 멤버 **P/B(시총/자본) p90/p10** 분산(스냅샷). 둘 다 넓음 → 승자독식 심화·`교차검증=일치`, 둘 다 좁음 → 동질 평준화·일치, 갈리면 → 혼재·`불일치(렌즈 갈림)`. 2행 two-lens 표(마진·밸류 나란히). 해석 한계: **두 렌즈가 서로 다른 자료원**(제출재무 ↔ 시장가치)인 게 핵심 — 일치하면 한 자료원 인공물이 아닌 강건 신호, **불일치 자체가 통찰**(재무는 갈리는데 시장은 균등 평가). **음수자본 제외수**(`음수자본제외`) 인용·**생존편향**·5점 윈도(방향신호)·밸류 스냅샷(시점 1) 명시. 임계는 `_attempts/industryAnalysisLab/` 실측 분포 기반 라벨 경계(절대 진리 아님). 점유율·인과 주장 금지. `concentration`(산업이 과점이냐)과 직교 — 이건 *회사 간 격차가 벌어지나*.

`Company.industry()` → 단일 종목의 밸류체인 위치 dict — `chainId` (산업 ID), `stage` (공정), `confidence` (0~1 매칭 신뢰도), `peers` (같은 stage 종목코드 list). 매칭 실패 시 `None`.

분류체계 신선도는 `taxonomy.json` 의 운영자 수동 갱신 시점 — 신생 산업·신규 상장 직후엔 매칭 누락 가능.

## 대표 반환 형태

```text
dartlab.industry()
→ DataFrame
   산업ID : str         # 식별자 (semiconductor, automobile, ...)
   산업명 : str         # 한글
   공정수 : int         # 해당 산업의 공정 단계 수
```

```text
dartlab.industry("semiconductor")
→ DataFrame
   공정 : str           # 공정 단계 ID (fab, oSat, equipment, ...)
   공정명 : str         # 한글 공정명 (전공정 / 후공정 / 장비 / ...)
   종목코드 : str       # 6자리
   종목명 : str
   역할 : str           # 해당 공정에서의 역할
   위치 : str           # 밸류체인 상 위치
```

```text
dartlab.industry("semiconductor", summary=True, year="2024")
→ DataFrame  # stage 단위 profit-pool 집계
   stage : str          # 공정 단계 ID (fab, oSat, equipment, ...)
   공정명 : str         # 한글 공정명
   매출(조) : float      # stage Σ매출 (조원)
   영업이익(조) : float  # stage Σ영업이익 (조원)
   기업수 : int          # stage finance-join 회사수
   영업이익률(%) : float # revenue-weighted = Σ영업이익/Σ매출×100 (단순평균 아님), Σ매출 0 이면 null
   coverageRatio : float # opIncome 산출가능 / 기업수 (0~1, 결손 노출 — 0 채움 금지)
```

```text
dartlab.industry("semiconductor", concentration=True)
→ DataFrame  # 산업 매출 시장구조 — 상위 5사 행 + 산업 집계(반복 첨부)
   종목코드/종목명 : str    # 상위 5사 (매출 내림차순)
   공정 : str              # stage key
   매출(억) : float         # 회사 매출 (억원)
   매출비중(%) : float      # 상장사 내 상대 비중 (= 회사매출/산업총매출, 절대점유율 아님)
   HHI : float             # 상장사 매출 기준 Herfindahl (0~10000), 전 행 동일값
   HHI라벨 : str            # 분산/중간/집중 (DOJ 척도 차용 — 반독점 판정 어휘 아님)
   상위3비중(%) : float     # CR3
   기업수 : int             # 매출 양수 상장사 수
   총매출(조) : float        # 산업 Σ매출 (조원)
   # 매출 양수 회사 0 이면 빈 DataFrame(스키마 보존). 비상장·해외매출 제외 한계 명시 필수
```

```text
dartlab.industry("battery", dynamics=True)
→ DataFrame  # 이익 풀 동학 — 공정별 행, 끝해 영업이익 내림차순
   공정명 : str            # stage 한글명
   첫해(조)/끝해(조) : float # 영업이익 levels (음수 그대로, share 미사용)
   변화(조) : float         # 끝해 - 첫해
   적자전환 : bool          # 첫해>0 & 끝해<0 (동학의 1차자료 증거)
   끝해리더 : bool          # 끝해 영업이익 1위 stage
   판정 : str              # 집중형(리더 고착) | 이동형(리더 교체)
   리더이동 : str           # "양극재 → 셀"(이동형) | "셀 고착"(집중형)
   윈도 : str              # 유효 연도 범위 (Σ영업이익>0 연도)
   생존편향주의 : str        # 현 멤버십 과거 소급 한계 — 답변 동반 필수
```

```text
dartlab.industry("pharma", polarization=True)
→ DataFrame  # 산업 양극화 — 2행 two-lens(마진·밸류 교차검증)
   렌즈 : str              # "마진(제출재무)" | "밸류(시장가치)"
   분산지표 : str           # "OPM IQR(%p)" | "P/B p90/p10"
   첫해값/끝해값 : float     # 마진=IQR 첫/끝해, 밸류=스냅샷(첫해 None)
   방향레벨 : str           # 마진 "확대/넓음" | 밸류 "넓음"
   n : int                # 유효 표본 수
   음수자본제외 : int        # 밸류 렌즈 자본≤0 제외수 (folk통계 가드) — 마진 행은 None
   양극화판정 : str         # 승자독식 심화 | 동질 평준화 | 혼재
   교차검증 : str           # 일치 | 불일치(렌즈 갈림) | 불가(한 렌즈 결손)
   윈도 : str              # 마진 유효 연도 범위
   생존편향주의 : str        # 현 멤버십 과거 소급 한계 — 답변 동반 필수
```

```text
Industry().edges(industryId="...", stockCode="...")
→ DataFrame  # 공급망/거래 관계 (공시인용 evidence)
   from코드/from이름 : str   # 공급사
   to코드/to이름 : str       # 매출처
   관계 : str               # supplier / customer / affiliate / investor
   산업 : str
   신뢰도 : float           # 0~1
   소스 : str               # docs_table(강) / network(출자) / docs(언급, 약)
   근거 : str               # 추출 본문 단서
   거래액 : float | None     # 억원 (공시 「주요 매입처」 추출, 누락 None — 0 채움 금지)
   의존도(%) : float | None  # 매입비중(supplier 매출처 의존도). 추출 천장 낮아 대부분 None
   # ★커버리지 빈곤은 화면 1급시민 — "SPLC식"·"Leontief/IO 승수" 과대포장 금지
```

```text
Company("005930").industry()
→ dict
   chainId : str             # "semiconductor"
   chainName : str           # "반도체"
   stage : str               # "fab" / "oSat" / "equipment" / "design" / ...
   stageLabel : str          # 한글 공정명
   confidence : float        # 0.0 ~ 1.0 매칭 신뢰도
   matches : list[str]       # 매칭 키워드
   products : list[str]      # 주요 제품
   peers : list[str]         # 같은 stage 종목코드
```

## 백분위·분포 경계 (SSOT)

산업 분포 위 회사 위치(백분위)는 **단일 산식 + 모집단 파라미터화**다 — 순위는 라이브 `pctRank`(모집단 무관 순수함수)로 peer 모집단(업종/시장/전체)만 바꿔 계산하고, "3갈래 분기"는 없다(터미널 `industryPercentile`·`percentileIn` 동일 산식 공유). 분포 **밴드** 소스는 의도된 이원화 — 퍼블릭은 prebuilt `industryStats.json`(KSIC 섹터·동일가중·상장 primary사 p10~p90), 로컬은 라이브 `quantileBand` 5분위. 둘 다 **KRX 시총가중 업종지수가 아니다**(분포출처 라벨 강제, 공식 업종지표는 외부 link-only).

- **industry 소유**: 섹터 분포 위 1점 읽기/깔때기(읽기). peer **N사 정밀 비교**는 `compare()`(셀 정렬 매트릭스, 백분위 토큰 0) — industry 가 재구현하지 않고 교차참조만.
- `marketShare`(상장사매출비중)는 시장점유율 아님(분모=상장 구성사 매출 합). "점유율" 라벨 사칭 금지.

## evidence 기준

산업 답변은 `target` (종목코드) · `industryId` · `stage` · taxonomy `dataAsOf` (운영자 갱신 시점) 를 남긴다. `confidence < 0.5` 면 매칭 신뢰도 낮음을 답변에 명시.

## Company.panel 응답에 industryBadge 자동 부착 — 단일 종목 답변 권장 경로

`Company.panel(topic)` (또는 `EngineCall(apiRef="Company.panel")`) 의 반환 `data` dict 에 `industryBadge` 가 자동 부착된다 (Track E). 단일 종목 답변이면 별도 `industry()` 호출 불필요:

```text
data.industryBadge = {
    industryId: "semiconductor",
    industryName: "반도체",
    stage: "fab",
    stageName: "전공정(FAB)",
    role: "제조",
    stream: "midstream",
    phase: "재도약",          # 라이프사이클 5 phase: 도입·성장·성숙·재도약·쇠퇴
    peers: [{stockCode, corpName}, ...],
    confidence: 73,
    confidenceMethod: "ratio",
}
```

단일 종목 헤더 chip 양식: `🏭 {industryName} · {stageName} · {phase} [conf:{confidence}]`.

## EngineCall (agent 경로) args 매핑

| `dartlab.industry(...)` | `EngineCall(apiRef="industry", args=...)` |
| --- | --- |
| `dartlab.industry()` 가이드 | `{}` (빈 dict) |
| `dartlab.industry("semiconductor")` | `{"industryId": "semiconductor"}` |
| `dartlab.industry("semiconductor", stage="fab")` | `{"industryId": "semiconductor", "stage": "fab"}` |
| `dartlab.industry("semiconductor", summary=True, year="2024")` | `{"industryId": "semiconductor", "summary": true, "year": "2024"}` |
| `dartlab.industry("semiconductor", concentration=True)` | `{"industryId": "semiconductor", "concentration": true}` |
| `dartlab.industry("battery", dynamics=True)` | `{"industryId": "battery", "dynamics": true}` |
| `dartlab.industry("pharma", polarization=True)` | `{"industryId": "pharma", "polarization": true}` |
| `Company("005930").industry()` | `{"stockCode": "005930"}` (apiRef="Company.industry") |

`summary` · `timeline` · `lifecycle` · `concentration` · `dynamics` · `polarization` 동시 X — 우선순위 summary > timeline > lifecycle > concentration > dynamics > polarization.

## 기본 실행 순서

1. **단일 종목 산업 위치** — `Company.panel(...).data.industryBadge` 그대로 인용 (자동 부착, 추가 호출 불필요).
2. **산업 ID 모를 때 가이드** — `dartlab.industry()` 로 목록.
3. **산업 전체 횡단 / 공정별 집계** — `dartlab.industry(industryId, summary=True, year=...)`.
4. **연도별 라이프사이클 phase 추적** — `dartlab.industry(industryId, lifecycle=True)`.
5. peer 그룹은 `industryBadge.peers[].stockCode` 또는 `Company.industry().peers` 추출 → `analysis` / `scan` / `quant` 전달.
6. 매칭 실패 (None 반환) 시 추측 X — 산업 분류 미등록 명시.

## 기본 검증

스킬은 공개 실행 문서다. `dartlab.industry()` 시그니처·반환 컬럼·`Company.industry()` 반환 키가 바뀌면 본 파일을 같은 변경에서 갱신한다.
