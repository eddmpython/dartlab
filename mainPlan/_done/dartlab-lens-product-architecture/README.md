# DartLab 분석 렌즈 제품화 아키텍처

✅ 구현 완료 (2026-07-18)

상태: 핵심 계약, 다섯 대표 제품, 상위 워크플로, Terminal, Ask, 공개 artifact 발행 경로 구현 및 40개 기업 성숙도 검증 완료  
작성 기준일: 2026-07-18  
범위: 저장소 전체 제품 구조, 공개 분석 렌즈, 상위 워크플로, README 설명 체계, 활성 mainPlan 포트폴리오

## 한 줄 판정

DartLab의 엔진격 폴더 구조는 유지한다. `analysis`, `credit`, `industry`, `quant`, `macro`를 축 카탈로그가 아니라 각각 대표 질문과 대표 결과를 가진 공개 분석 제품으로 강화하고, `story`, `simulate`, `ask`는 이 렌즈들의 증거 기반 결과를 조합하는 워크플로로 제한한다.

자동 선정 40개 기업 실데이터 검증에서 40/40 계산, hard issue 0, 모든 품질과 성능 gate를 통과했다. 따라서 과잉의 원인은 엔진 수가 아니라 일부 대표 제품 내부의 중복 계산과 전시장 데이터 적재였다고 확정한다.

## 이 계획이 필요한 이유

현재 DartLab은 기반이 부족한 프로젝트가 아니다. 비교 가능한 공시 데이터, Company와 panel, scan, 다섯 분석 렌즈, 보고서와 시뮬레이션까지 이미 넓은 능력을 갖고 있다. 문제는 다음과 같다.

1. 내부 구조와 레이어 번호가 제품 설명까지 올라와 사용자의 정신모형을 복잡하게 만든다.
2. 다수 렌즈의 기본 진입이 실제 판단보다 축 안내표를 먼저 반환한다.
3. 147개 축의 존재와 실행 가능성에 비해 대표 제품 경험과 의미 검증이 약하다.
4. 28개 활성 mainPlan이 핵심 제품 완성보다 수평 확장을 유도한다.
5. Story, Simulate, Ask가 안정된 렌즈 결과 계약보다 빠르게 확장되고 있다.

이 계획은 기존 엔진을 줄이거나 숨기는 계획이 아니다. 이미 만든 능력을 사용자에게 이해 가능하고 반복 가능한 제품으로 압축하는 상위 설계다.

## 문서 구조

| 문서 | 역할 |
|---|---|
| [00-product-prd.md](00-product-prd.md) | 제품 정의, 고정 결정, 범위와 비목표 |
| [01-current-state-audit.md](01-current-state-audit.md) | 저장소 실측, 엔진별 성숙도, 과잉 여부 판정 |
| [02-target-product-architecture.md](02-target-product-architecture.md) | 목표 제품 구조, 렌즈 헌장, 공통 결과 문법, API 전환 원칙 |
| [03-execution-roadmap.md](03-execution-roadmap.md) | 활성 계획 통합, 실행 순서, 완료 게이트와 지표 |
| [04-readme-information-architecture.md](04-readme-information-architecture.md) | README 제품 서사와 정보구조 개편안 |
| [05-implementation-ledger.md](05-implementation-ledger.md) | 실제 구현 위치, 검증 결과, 공개 배포와 운영 경계 |

## 상위 결정

이 폴더가 다음 사안의 제품 아키텍처 SSOT다.

- DartLab의 사용자 대상 제품 정의
- 다섯 공개 분석 렌즈의 역할과 경계
- Story, Simulate, Ask의 조합 책임
- mainPlan 간 우선순위와 선후관계
- README에서 내부 레이어를 제품 설명으로 사용하지 않는 원칙

각 하위 mainPlan은 자기 도메인의 상세 설계 SSOT를 계속 유지한다. 이 계획은 상세 산식이나 구현 계약을 복제하지 않고, 어떤 계획을 왜 먼저 완성하는지 통제한다.

## 기존 계획과의 관계

- `scan-screener-os`: 비교와 선별 제품의 실행 계획
- `professional-report-engine`: Story와 Report 프로그램으로 통합 관리
- `scenario-simulator`, `macro-simulation-engine`: Simulate 프로그램으로 통합 관리
- `first-party-ai`, `ai-workbench-connector`, `search-productization`: Ask와 Research 프로그램으로 통합 관리
- `terminal-data-download`: Experience 프로그램으로 통합 관리
- `dartlab-universe`: 핵심 렌즈와 대표 워크플로가 제품 게이트를 통과한 뒤 재평가할 장기 확장 계획

2026-07-26 운영자 판정으로 `periodic-report-dossier`, `polars-gpu-backend`,
`report-full-harvest`, `scan-note-cross-section`, `table-export`,
`terminal-improvement`, `web-notebook-runtime` 계획은 폐기했다. 삭제 전 상세 이력은
Git 기록에 남고, 현재 제품 책임은 위의 현역 계획과 구현 계약이 맡는다.

## 구현 결정 결과

1. 다섯 렌즈의 대표 질문과 결과 범위는 `product` 공통 외피와 엔진별 기존 payload 보존으로 확정했다.
2. 기존 무인자 가이드와 세부 축 호출은 변경하지 않았다. 대표 제품은 검증된 축에 additive하게 붙였다.
3. 활성 mainPlan은 본 계획의 P1부터 P4 우선순위 지도로 관리한다. 운영자가 폐기한 중복·보류 계획은 Git 이력만 보존한다.
4. README는 레이어 대신 제품 흐름으로 바꾸고 내부 레이어 규율은 루트 `ARCHITECTURE.md`로 이동했다.

구현과 검증의 상세 근거는 [05-implementation-ledger.md](05-implementation-ledger.md)가 정본이다.
