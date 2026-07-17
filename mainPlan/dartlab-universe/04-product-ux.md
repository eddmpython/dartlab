# 04. Product UX

## 1. 경험 원칙

- 우주는 배경 은유이고, 표와 근거가 분석의 본체다.
- 확대는 같은 점을 키우지 않고 query scope와 representation을 바꾼다.
- 위치는 industry, stage, time, predicate, hop 중 하나의 의미를 가진다.
- 색은 한 번에 하나의 metric만 표현한다.
- edge style은 evidence status를 표현한다.
- 시간과 근거를 숨긴 큰 숫자보다 작은 honest gap을 선택한다.
- graph를 사용할 수 없는 사람도 같은 답에 도달해야 한다.

## 2. 화면 구조

```text
Top bar
  Search seed | validAt | knownAt | share | diagnostics

Left Lens Tray
  Industry | Financial | Credit | Macro | Quant | Scan

Center Universe Scene
  Atlas | Industry | Company | Evidence focus

Right Claim and Evidence
  Claim ledger | falsifier | assertion timeline | source | limitations

Bottom Evidence and Time Ribbon
  sourcePublishedAt | availableAt | valid range | known range | revision | coverage
```

모바일은 Scene, Lens, Evidence를 탭으로 분리하고 선택 상태는 유지한다.

이 화면은 `/universe`에만 존재한다. `/map`은 기존 시장 지도 화면을 유지하며 두 route의 navigation link만 연결한다.

## 3. 첫 진입

`/universe` 첫 화면은 34개 산업 atlas만 연다.

- 제목: "DartLab Universe"
- subline: 산업 수, public entity 수, dataAsOf
- 검색: 회사, ticker, 산업
- workflow 추천: 변화 우주, 성장 지속성 Kill-Chain, 신용 취약 Kill-Chain, 한미 Twin
- 전체 2,664개 회사는 사용자가 industry 또는 companies lens를 열 때만 로드

우주 애니메이션 때문에 content가 늦게 보이면 실패다. reduced motion에서는 정적 배치로 바로 연다.

## 4. 관계의 시각 문법

| 상태 | 선 | 의미 |
|---|---|---|
| observed A/B | 실선 | exact sourceRef 확인 |
| corroborated | 이중 얇은 실선 | 독립 source 2개 이상 |
| derived C | 점선 | deterministic 계산 또는 rule |
| candidate D | 낮은 대비 점선 | 아직 근거 미확인 |
| disputed | 주황 파선 | assertion 충돌 |
| retracted | 취소선 timeline only | 현재 scene 기본 숨김 |
| scenario | 보라 이중 점선과 가정 glyph | 사용자가 적용한 가정 |

색은 relation type과 metric을 동시에 표현하지 않는다. type은 선 패턴 및 arrow marker, 선택된 metric은 node fill로 분리한다.

## 5. Evidence Drawer

엣지를 클릭하면 다음 순서로 보인다.

1. plain-language relation: "OCI가 삼성전자에 공급한다고 언급됨"
2. 상태 chip: observed, candidate, disputed
3. validAt, sourcePublishedAt, availableAt, knowledgeAsOf
4. assertion timeline
5. 근거 문서: 회사, 보고서, 접수번호, period, sectionPath
6. exact snippet 또는 table row
7. 추출 방식과 evidence class
8. provenance chain과 engine lens 결과
9. 한계: entity match, 비공개 상대, 단위, 전체 거래 대비 coverage

sourceRef를 못 찾으면 drawer는 빈 카드가 아니라 `unresolvedEvidence` reason과 다음 동작을 보여준다. 이 edge는 fact layer로 이동하지 않는다.

## 6. Time Lens

Time Lens는 슬라이더 하나가 아니다.

- 상단: `validAt`, 실제 유효 시점
- 하단: `knownAt`, 당시 알 수 있었던 cutoff
- revision marker: 정정 및 재공시
- data freshness rail: source별 dataAsOf

사용자가 knownAt을 과거로 옮기면 그 이후 공개된 assertion과 observation은 사라진다. 현재값을 과거 장면에 역주입하지 않는다.

## 6.1 제품 서명 workflow

### 변화 우주

산업과 회사 좌표는 고정하고 두 SourceSnapshotSet 사이의 created, corrected, retracted, newlyKnown, stale만 표시한다. 사용자가 변화 mark를 열면 before와 after evidence가 나란히 열린다. history exact replay가 불가능하면 현재 파생 신호와 exact replay를 구분한다.

### Thesis Kill-Chain

claim ledger를 assumption, fragility, trigger, tripwire, falsifier, verdict 순서로 연다. fact, deterministic derivation, gap, scenario는 평행 lane을 사용한다. falsifier 또는 requiredEvidence가 missing이면 결론 beat를 닫지 않는다.

### 판정 우주

조건과 회사의 교차 격자를 PASS, FAIL, MISSING, NOT_APPLICABLE로 표시한다. near-miss는 threshold 거리, unit, evidence, coverage를 함께 연다. 단일 빨강 및 초록 점수는 쓰지 않는다.

### 한미 Twin

KR과 US를 좌우 mirror lane에 놓고 동일 metric, disclosure topic, period, unit을 같은 축으로 비교한다. 한쪽 결손을 공간에서 숨기지 않는다.

## 7. Lens Tray

Lens Tray는 기존 엔진을 다시 구현하지 않는다.

| lens | 입력 | overlay | evidence |
|---|---|---|---|
| Industry | company or industry | stage, role, supply relation | industry ref |
| Financial | company set | growth, margin, cashflow | tableRef, valueRef, dateRef |
| Credit | company set | grade, weak axis | executionRef, valueRef |
| Macro | market and date | regime, transmission | dateRef, sourceRef |
| Quant | securities and range | momentum, risk, factor | tableRef, dateRef |
| Scan | universe and filter | rank, coverage, unknown | universe, formula, tableRef |

한 번에 primary lens 1개, comparison lens 1개만 허용한다. 6개 metric을 동시에 색과 크기로 겹치지 않는다.

## 8. 질문을 카메라로

public 기본은 구조화 control이다.

- seed: 회사 또는 산업
- relation: supplier, ownership, affiliation, filing
- time: validAt, knownAt
- evidence: A/B only, candidate 포함
- lens: financial, credit, macro, quant, scan
- grouping: industry, stage, market

AI 사용 가능 환경에서는 기존 Workbench가 같은 값을 채운 `UniverseFlightPlan`과 `ProjectionSpec`을 반환한다. 질문별 정규식 router와 템플릿 답변을 Universe에 만들지 않는다.

## 9. table 및 list 동등 표면

graph 아래 또는 대체 mode에 다음 열을 제공한다.

- subject
- predicate
- object
- status
- evidenceClass
- validAt
- availableAt
- sourcePublishedAt
- sourceRef
- selected lens metric
- omitted reason

정렬, 필터, 키보드 focus, CSV export는 table이 담당한다. graph에서 선택하면 table row도 선택되고 반대도 동일하다.

## 10. 3D Galaxy 렌즈

3D는 U5 optional이며 `U5-X01` uplift attempt를 통과해야 한다.

- truth, projection, evidence 계약은 2D와 byte-identical
- 별도 graph data를 받지 않음
- industry cluster를 은하, company를 별, relation을 궤도로 표현 가능
- discovery와 presentation용이며 exact 비교와 evidence 읽기는 2D 또는 drawer로 전환
- mobile, reduced motion, low GPU에서는 자동 비활성
- deep link는 camera state가 아니라 ProjectionSpec을 우선 저장
- 2D 대비 task 성공률 또는 발견률을 개선하지 못하면 기각

3D에서만 가능한 제품 기능은 만들지 않는다.

## 11. 공유와 재현

share URL에는 다음만 넣는다.

- schemaVersion
- snapshotSetId와 legacy buildId
- workflowId, beat index, optional flightId checksum
- seed IDs
- validAt, knownAt
- predicates, evidence policy
- lens capabilityRefs
- grouping, colorBy, sizeBy
- selected node 또는 edge ID

질문 원문, API key, raw evidence, 사용자 history는 넣지 않는다. 오래된 snapshotSetId의 source version을 복원할 수 없으면 현재 데이터 재실행과 원본 재현 불가를 분리해서 표시한다. legacy buildId만 있는 URL은 exact replay로 표현하지 않는다.

## 12. 접근성

- canvas와 SVG 모두 동등한 table view 제공
- 모든 node와 edge는 keyboard search 및 list focus 가능
- 색만으로 status 구분 금지
- `prefers-reduced-motion`에서 force animation과 scenario pulse 중단
- screen reader용 relation summary 제공
- 최소 hit target 44px
- node label 확대와 high contrast
- WebGL context loss 시 table 및 SVG 자동 전환

## 13. 제품 시나리오 acceptance

다음 여섯 시나리오를 실제 브라우저에서 통과해야 제품 입장을 허용한다.

1. atlas 첫 진입 후 34개 산업 변화 우주 열기
2. 두 knownAt 사이의 변화 하나에서 before와 after evidence 열기
3. 성장 지속성 Kill-Chain에서 가장 가까운 falsifier 열기
4. 삼성전자 1-hop에서 fact와 candidate를 분리하고 relation 원문 열기
5. knownAt을 과거로 옮겨 이후 assertion 제거
6. 삼성전자와 Apple의 같은 재무 metric, unit, source, gap 비교

각 시나리오는 graph 조작, table 동등 경로, share URL 재현을 모두 확인한다.

추가 route acceptance는 다음과 같다.

6. `/map` deep link와 기존 지도 작업이 회귀하지 않음
7. `/universe` refresh와 back/forward가 같은 ProjectionSpec을 복원
8. `/map`과 `/universe`가 artifact를 중복 fetch하지 않고 공유 cache key 사용
9. Canvas 또는 WebGL 실패 후 table에서 같은 claim과 receipt를 확인
