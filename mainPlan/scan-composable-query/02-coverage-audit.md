# scan 데이터 커버리지 감사: providers·gather·panel 사업보고서 탈탈털기 판정

> 방법: 사실 기반 3 조사(providers/gather 표면·scan 소비·panel 섹션 대조) + 전문 4관점 토론(전수원칙 집행관·도메인전문가·악마의변호인·통합PM). 2026-07-07. 파일:라인 그라운딩.
> 트리거: 운영자 "전문에이전트들과 토론해서 scan이 정말 providers·gather·특히 panel 사업보고서 전 섹션을 탈탈 털어쓰는지 확인해라."

## 판정 (한 줄)

**아니다. "털 수 있는데 안 트는" 상태다.** 손-큐레이션 게이트 2개가 거의 공짜인 정형표 ~11개(임원보수·자본증권·주주 = 거버넌스·희석·부실 알파)를 자르고, 매트릭스 노트(특수관계자·영업부문)와 정성 서술이 빠져 있다. 추출 카탈로그 88개념(DART 80) 중 scan 스크리닝 노출은 약 53(실효 ~51). 단, "88 전부를 scan 축으로"가 목표가 아니라 "수치화 가능은 자동 전수, 정성은 제 집(docs/frame)으로"가 정답이다.

## 정량 사실 (3 조사 확정)

- 추출 카탈로그 = **88 개념**(DART-side 80, US-only 8). 9 카테고리: financialStatement 6·note 35·governance 8·capital 4·workforce 7·debt 6·segment 2·narrative 10·filingMeta 2. (`core/extractionCatalog.py`)
- scan 노출 ≈ **53**: note 29 + 재무5표 6 + report 17 apiType + segment(salesByProduct). 실효 ~51(매트릭스 탈락).
- **손 게이트 3겹**: ① note `registered=True AND valueType∈(amount,rate)`(notes.py:89) → 35→29 ② report `SCAN_API_TYPES` 17/28 하드리스트(build.py:59) ③ panel `readNoteStatements` `~axisPath.contains("|")` depth-1 단일축만(cell.py:789) → 매트릭스 노트 셀0.
- **자기기만 신호**: notes.py:74 주석은 "카탈로그 SSOT 라 손 선별 0"이라 자칭하나 :89 술어가 text를 배제. SSOT 도출과 손 필터 부재는 별개 (술어 자체가 큐레이션). [[feedback_exhaustive_no_curation]] "등재 게이트가 아니라 사후 태그로 도태" 위반.
- **오태깅**: `salesOrder`·`rawMaterial`은 valueType=amount인데 category=narrative라 note 필터가 닿지 못함. contingencies·shareBasedComp도 구조적 수치인데 text 태깅.
- gather 측: macro 55지표 중 scan은 macroBeta로 ECOS 3개만. narrative/research/naverTheme/naverEtf/flow(외국인기관)/ownership 등 gather 축 다수 scan 미소비.

## 토론 합의 (수렴)

1. scan 은 사업보고서를 탈탈 털지 **못한다** (4관점 중 3 명시 NO, 도메인전문가 8갭으로 암묵 동의).
2. **report 17→28 de-gate** = 최고 ROI·거의 공짜(파서 이미 존재, buildReport 제네릭 분할)·최저위험. 악마의변호인도 임원보수·자본증권·주주는 "노출해야 할 진짜 갭"으로 인정.
3. **narrative 10(순수 산문)은 scan 축으로 만들면 안 됨** = 카테고리 오류. docs/search + frame/narrative 가 제 집. 전수원칙 집행관도 "억지 수치화 말고 text-verb(존재/전년diff)"라 동의.
4. **매트릭스 노트는 depth-1 필터 우회 금지** (pivot `first`가 조용히 데이터 드롭, 전 노트 개념 파괴). 전용 붕괴 추출기(salesByProduct 선례)로. 영업부문은 이미 salesByProduct 커버.
5. **도태는 census 성적표로** (빈 파일 = 정직 gap), 등재 게이트로가 아니라.

## 토론 발산 (긴장)

- 전수원칙 집행관: text 개념도 text-verb 축으로 전부 자동 등재.
- 악마의변호인: 진짜 scan 갭은 ~4개(기존 축 수치 확장), 나머지는 "scan 미노출 ≠ 갭"(제 집 있음). 80/80 목표는 [[feedback_plan_score_not_signature]] 함정.
- 통합PM: 중재 = 수치는 de-gate 자동, text는 flag 1열, 산문은 docs, 도태는 census.

## 처방: 27갭 3버킷 (통합PM 종합)

- **A. scan 수치 축 자동 등재 (~14)**: 임원보수 4·자본증권 3·주주 2(→ report de-gate) + salesOrder·productionCapacity·rawMaterial 3(정성-수치 prebuild) + 매트릭스 2(relatedParty 내부거래율 전용축·segments salesByProduct 확장).
- **B. 플래그/존재여부만 (~4)**: 자금사용 2(목적외 전용 편차)·우발부채·후속사건(존재 bool + 가능손실 금액). `define` where 에서 boolean 소비.
- **C. docs/search 라우팅 (~11)**: narrative 자유텍스트 7(businessOverview·riskFactors·mdna·rnd·majorContracts·governanceText·environment) + 정책산문(financialRiskMgmt·accountingPolicies·criticalEstimates). `crossSection=false` 태그 + frame/narrative(이미 존재) 노출, scan 축 신설 0.

## 정공법 로드맵

- **P1 (최우선·최저위험·신설 파서 0): 게이트 de-gate.** SCAN_API_TYPES 카탈로그 도출(17→28) + note `registered` 필터 제거·오태깅 valueType 교정. 노출 53→~64. 영향: `scan/builders/kr/report/build.py`·`notes.py`·`io/parquet.py`(`_REQUIRED_REPORT_FILES`는 HF 다운로드 완전성 가드로 유지, BUILD만 전수) + `tests/scan/test_prebuild_contract.py`·census baseline.
- **P2**: 매트릭스 2 전용 붕괴 추출기(salesByProduct 일반화) + 정성-수치 3 횡단 prebuild(frame/narrative 재사용).
- **P3**: 텍스트 존재 플래그(자금사용·우발부채) source="flag" 1열.
- **P4**: narrative 산문 `crossSection=false` 태그 + docs/search 라우팅 확정.

## 핵심 파일

`core/extractionCatalog.py` · `scan/builders/kr/notes.py:89` · `scan/builders/kr/report/build.py:59` · `providers/dart/report/types.py:10` · `providers/dart/panel/cell.py:789` · `scan/io/parquet.py:107`(다운로드 가드, 노출 게이트 아님) · `frame/narrative.py`·`frame/inventory.py`(회사별 전수 열거, round-trip 100%) · `scan/salesByProduct.py`(매트릭스 신호 선례) · `tests/audit/extractionCoverageCensus.py`(성적표).

## 남은 결정 (운영자)

P1 은 합의·저위험·운영자 원칙(exhaustive) 직접 이행이라 즉시 착수 후보. P2~P4 는 버킷 경계(특히 A/C 사이 salesOrder 류가 scan 수치냐 docs 냐)에 도메인 판단 여지 있음. narrative 를 scan 에 넣지 않는다는 4관점 합의는 확정.
