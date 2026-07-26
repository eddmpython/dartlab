# 03. 실행 로드맵

## 0. As-built 상태

| 단계 | 상태 | 구현 결과 |
|---|---|---|
| Phase 0 | 완료 | Lens Product v1 계약, 상태와 시점 검증, 기존 API additive 호환 |
| Phase 1 | 완료 | Analysis `종합평가` 대표 제품과 Story 소비 |
| Phase 2 | 완료 | Scan screen SSOT, Python과 UI conformance, 세 상태 판정, preset과 export |
| Phase 3 | 완료 | Credit 등급, 하방 시나리오, tripwire와 Industry 가치사슬, peer, profit pool 제품 |
| Phase 4 | 완료 | Quant `괴리`와 Macro `전파` 대표 제품 |
| Phase 5 | 완료 | Report의 lensProducts와 Scenario assumptionLedger, 하위 사실 재계산 방지 |
| Phase 6 | 완료 | Ask refs, local/public runtime lens port, Terminal 독립 렌즈 패널, 전 상장사 shard artifact 발행 workflow |

M5의 장기 calibration과 실제 사용 지표는 배포 후 계속 누적하는 운영 지표다. 본 계획의 구현 완료 게이트는 M3 대표 질문과 M4 채널 의미 및 artifact 계약까지다. 상세 검증은 [05-implementation-ledger.md](05-implementation-ledger.md)를 따른다.

## 1. 실행 원칙

1. 구조 개편보다 대표 제품 완성을 우선한다.
2. 한 번에 하나의 대표 사용자 작업을 끝낸다.
3. 신규 축과 신규 route는 기존 계약으로 해결 불가능하다는 증거가 있을 때만 추가한다.
4. 하위 렌즈가 M3에 도달하기 전에 상위 조합 표면을 확장하지 않는다.
5. 각 단계는 기능 존재가 아니라 의미 제품 게이트로 종료한다.

## 2. 네 개 상위 프로그램

### P1. Truth Spine

목표: 모든 렌즈가 같은 기업, 기간, 단위, 근거와 최신성 위에서 계산되게 한다.

포함 범위:

- provider parity
- panel 추출과 note SSOT
- sourceRef와 데이터 최신성
- Company, panel, compare
- DART와 EDGAR 시장 차이
- 데이터 다운로드와 재현

관련 활성 계획:

- `panel-extraction-workbench-ssot`
- `content-asset-ssot`
- `edgar-terminal-reach`
- `pyproc-runtime-ssot`
- `terminal-data-download`

### P2. Lens Products

목표: 다섯 공개 렌즈를 대표 질문과 대표 결과가 있는 제품으로 마감한다.

포함 범위:

- Analysis 대표 분석
- Credit 등급과 하방 위험
- Industry 가치사슬과 peer
- Quant 기대와 가격 반응
- Macro 기업 전달경로
- 공통 결과 문법
- 제품 의미 게이트

관련 기존 계획과 자산:

- 완료된 `macro-lens-redesign`
- 완료된 `macro-analysis-superstrengthen`
- 완료된 `industry-analysis-lab`
- 완료된 `company-analysis-report`
- `expectation-grid`
- `financial-statement-lab`

완료 폴더의 산출물은 새로 재구현하지 않고 현재 렌즈의 재료로 사용한다.

### P3. Decision Applications

목표: 렌즈 결과를 실제 조사와 판단 작업으로 조합한다.

하위 프로그램:

| 통합 프로그램 | 흡수할 계획 |
|---|---|
| Screener | scan-screener-os |
| Report | professional-report-engine, dartlab-story-curriculum |
| Scenario | scenario-simulator, macro-simulation-engine, expectation-grid |
| Research index | brokerage-research-index |

현역 폴더는 상위 roadmap에서 하나의 종료 조건과 순서를 공유한다. 운영자가 폐기한
중복 계획의 상세 문서는 Git 이력에서만 보존한다.

### P4. Experience and Distribution

목표: 같은 제품을 여러 채널에서 의미 차이 없이 사용하게 한다.

하위 프로그램:

| 통합 프로그램 | 흡수할 계획 |
|---|---|
| Ask와 Research | first-party-ai, ai-workbench-connector, search-productization |
| Terminal | terminal-data-download |
| Learn | tutorial-guide |
| Public presentation | landing-mobile-optimization, content-asset-ssot |

## 3. 보류 계획

보류는 폐기가 아니라 제품 선후관계 판정이다.

| 계획 | 판정 | 재개 조건 |
|---|---|---|
| dartlab-universe | 보류 | 다섯 렌즈 중 핵심 3개가 M3, Report 또는 Screener가 M4 |
| cards-knowledge-network | 보류 | Ask와 Search의 실제 지식 연결 요구가 반복 확인됨 |
| innovation-stack-research | 탐색만 유지 | 현재 제품 병목과 직접 연결된 기술만 승격 |

`edgar-terminal-reach`는 장기 확장이 아니라 시장 parity이므로 Truth Spine 안에서 유지한다. 다만 새 미국 전용 제품 확장은 한국 대표 제품 완성도와 같은 게이트를 적용한다.

### 운영자 폐기 기록

2026-07-26에 `periodic-report-dossier`, `polars-gpu-backend`,
`report-full-harvest`, `scan-note-cross-section`, `table-export`,
`terminal-improvement`, `web-notebook-runtime`를 폐기했다. 이 항목들은 재개 대기
백로그가 아니며, 필요하면 새 근거와 새 PRD로 다시 제안해야 한다.

## 4. 단계별 실행

### Phase 0. 제품 계약 동결

목표:

- 본 상위 설계 승인
- 신규 엔진과 신규 축의 수평 확장 동결
- 다섯 렌즈 대표 질문 확정
- 공통 결과 문법을 기존 타입에 매핑
- 의미 제품 게이트와 기준 기업군 정의

종료 조건:

- 각 렌즈가 한 문장 질문과 대표 결과 schema를 가짐
- 기존 public API와 변경 후보가 구분됨
- 활성 계획이 P1부터 P4 및 보류로 분류됨

### Phase 1. Analysis 대표 제품

목표:

- 22축을 사업, 이익, 현금, 자본배분, 가치, 위험의 인과 결과로 조립
- 축 지식 없는 대표 호출 또는 대표 제품 경로 제공
- 결론, 동인, evidence, gaps, falsifier 포함
- 기준 기업군 의미 검증

종료 조건:

- 대표 질문이 Python과 Terminal에서 완료됨
- 상위 Story가 같은 결과를 소비함
- 블로그 또는 문서 예제가 개별 축 나열보다 대표 분석을 우선함

### Phase 2. Scan과 Screener 마감

목표:

- 완성된 scan JSON spec을 public UI가 직접 소비
- Python, watcher, frontend의 스크린 의미 통일
- 저장, 재실행, 결과 설명, 내보내기 완성

종료 조건:

- 대표 스크린이 같은 spec으로 Python과 UI에서 동일 멤버를 반환
- 조건별 데이터 커버리지와 제외 이유를 노출
- 실제 사용 가능한 독립 제품 M4 도달

### Phase 3. Credit과 Industry 강화

Credit 목표:

- 기본 dCR 제품에 등급 동인, 만기, 유동성, 하방 시나리오, tripwire 결합

Industry 목표:

- peer 선정 근거, 가치사슬, 산업 단계, profit pool, 관계 최신성 강화
- 다른 렌즈가 동일 peer와 산업 문맥을 소비

종료 조건:

- 두 렌즈 모두 M3
- Analysis와 Report에서 재계산 없이 소비

### Phase 4. Quant와 Macro 집중화

Quant 목표:

- 48축 전시보다 펀더멘털 변화, 시장 기대, 가격 반응의 불일치를 대표 제품으로 확정

Macro 목표:

- regime에서 산업과 기업 재무로 이어지는 전달경로를 대표 제품으로 확정
- 테스트 밀도와 기준 기업 검증 보강

종료 조건:

- 두 렌즈 모두 축 지식 없이 대표 질문 완료
- Macro 전달경로가 지표 나열 없이 기업 영향까지 닫힘
- Quant 판단이 가격 지표 나열이 아니라 공시 펀더멘털과 연결됨

### Phase 5. Report와 Scenario 통합

Report 목표:

- 대표 보고서 하나를 thesis, evidence, bear case, falsifier까지 마감
- 다수 템플릿 조합은 대표 보고서 완료 후 확장

Scenario 목표:

- Analysis, Credit, Macro, Quant 결과와 Assumption Ledger를 입력으로 사용
- 과거 replay와 미래 what-if 분리
- 단일 예측값 대신 조건부 범위와 실패 조건 제공

종료 조건:

- 하위 렌즈 사실 재계산 0
- target, asOf, dataAsOf, evidence가 끝까지 보존됨
- 대표 Report와 Scenario가 M4

### Phase 6. Ask와 Terminal 통합

목표:

- 종목과 시점 문맥을 유지하며 다섯 렌즈를 오감
- Ask가 같은 렌즈 결과를 설명하고 근거로 돌아감
- 새 route 추가보다 기존 Terminal의 통합 작업공간 완성

종료 조건:

- 동일 질문의 Python, Terminal, Ask 의미 parity
- 결과 저장, 공유, 내보내기, 재실행 가능
- 사용자가 내부 레이어를 몰라도 전체 조사 흐름 완료

## 5. 공개 렌즈 완료 게이트

렌즈를 제품 완료로 선언하려면 다음을 모두 통과해야 한다.

1. 축 이름 없이 대표 질문에 답한다.
2. 결론과 핵심 동인이 있다.
3. 결론이 근거와 원문에 닿는다.
4. asOf와 dataAsOf가 분리된다.
5. missing, blocked, stale을 0이나 정상으로 위장하지 않는다.
6. confidence와 coverage의 의미가 명시된다.
7. 반증 조건 또는 tripwire가 있다.
8. 기준 기업군에서 의미 정확성을 검증한다.
9. Python, Terminal, Ask에서 같은 의미를 보존한다.
10. 결과를 저장, 내보내기, 재실행할 수 있다.

## 6. 지표

### 제품 지표

- 첫 유용한 결과까지 필요한 호출 수
- 축 선택 없이 대표 작업을 완료한 비율
- 대표 결과 usable, partial, blocked 비율
- 렌즈별 재실행 및 drilldown 비율
- Screener 저장 및 재실행 비율
- Report, export, share 사용 비율

### 신뢰 지표

- evidence 연결률
- asOf 및 dataAsOf 표시율
- 데이터 최신성 위반 수
- missing을 정상값으로 처리한 회귀 수
- 기준 기업군 의미 판정 정확도
- 시나리오 look-ahead 위반 수

### 유지보수 지표

- UI의 Python 의미 재구현 수
- 같은 계산의 중복 구현 수
- 렌즈 형제 간 비승인 import 수
- 상위 워크플로의 하위 사실 재계산 수
- public API와 문서 예제 parity

## 7. 즉시 하지 않을 일

- 148번째 축 추가
- 새 분석 엔진 추가
- 다섯 렌즈를 하나의 종합점수로 합치기
- Universe public 확장
- 모든 Report 템플릿 동시 완성
- Quant 범용 기술분석 범위 확대
- Macro 외부 지표 종류 확대
- 측정 없이 GPU 경로를 기본 backend로 전환
- README와 제품 UI에 내부 레이어 설명을 다시 전면 배치
