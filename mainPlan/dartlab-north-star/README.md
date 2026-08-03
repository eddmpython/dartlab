# DartLab North Star Operating System

상태: local semantic measurement foundation과 첫 verified operator journey 구현 완료. 축별 점수표는 루트 README `## 북극성`에 라이브(2026-08-02, 원장 결정 4 번복).

범위: DartLab 전체 제품이 기능 수, 모델 호출 수, 페이지뷰가 아니라 검증 가능한 사용자 분석 결과를 기준으로 우선순위를 정하도록 북극성, 결과 수명주기, 증거 레지스트리, scorecard, 주간 운영 주기를 세운다.

이 폴더는 이니셔티브 계획이다. 구현이 끝나면 영구 계약은 `README.md`, handbook, Skill OS, `src/dartlab/productOutcome.py`, `tests/audit/northStarEvidence.py`로 승격하고 이 폴더를 삭제한다.

## 한 줄 결정

**DartLab의 북극성은 Weekly Verified Analysis Loops다. 실제 기업, 시장, 공시 또는 데이터 질문이 DartLab 정식 엔진을 거쳐 근거 있는 결과가 되고, 사용자가 그 결과의 정확한 evidence 또는 artifact를 확인했을 때만 한 건으로 센다.**

한국어 운영명은 `주간 검증 완료 분석 루프`, 안정 ID는 `weeklyVerifiedAnalysisLoops`를 사용한다.

현재 전역 값은 `미측정`이다. `landing`의 익명 site signal, 로컬 AI trace, 테스트 통과 수, mainPlan 완료 수는 북극성 분자가 아니다. 권위 있는 cohort가 생기기 전에 성장 목표를 만들지 않는다.

## xlpod에서 흡수하는 것

| xlpod 계약 | DartLab 적용 |
|---|---|
| 완결 workbook loop | 완결 verified analysis loop |
| 목표 하나당 primary goal 하나 | 모든 mainPlan 이니셔티브에 primary goal ID 하나 |
| 실행 증거 registry | `tests/audit/northStarEvidence.py` |
| 문서와 파일, CI runner drift 차단 | Skill OS goal ID와 gate 등록을 기계 대조 |
| semantic authority와 count authority 분리 | 로컬 outcome state와 집계 cohort 분리 |
| expand, improve, repair, revert 판정 | DartLab 주간 outcome review 판정 |
| 숫자 없는 상태에서 목표 발명 금지 | 현재 baseline `미측정`, 4주 권위 자료 전 목표 0 |
| README 축별 점수표와 총점 | 루트 README `## 북극성` 점수표 (2026-08-02 운영자 결정으로 도입, 원장 결정 4 번복) |

축별 점수표의 규율은 xlpod와 같다: 점수 근거는 실제로 도는 게이트와 실측 여정뿐이며, 자동으로 실행되지 않는 경로는 구현돼 있어도 점수로 세지 않는다. 재판정은 주간 outcome review에서만 한다. 흡수하지 않는 것은 workbook 고유 상태명과 계정 기반 D1 admission이다. DartLab에는 별도 제품 문법과 프라이버시 경계가 필요하다.

## 문서 지도

1. [00-product-outcome-contract.md](00-product-outcome-contract.md): 완결 분석 루프, 목표 ID, 가드레일, 제외 조건.
2. [01-metric-authority-and-privacy.md](01-metric-authority-and-privacy.md): semantic authority, count authority, 개인정보 최소화, scorecard.
3. [02-evidence-and-operating-cycle.md](02-evidence-and-operating-cycle.md): 증거 레지스트리, CI 등록, outcome brief, 주간 운영.
4. [03-implementation-plan.md](03-implementation-plan.md): 영향 파일, 심볼, 단계, 테스트, 롤백, 개발자와 PM 평가.
5. [04-progress-ledger.md](04-progress-ledger.md): 결정 원장, baseline, 구현 재개 지점.
6. [05-score-rubric.md](05-score-rubric.md): 8차원 능력 채점 기준(정의·앵커·축별 근거). 루트 README 점수표의 채점 정본.

## 다른 mainPlan과의 관계

- 현재 Agent Runtime은 첫 번째 실제 소비자다. primary goal은 `completeVerifiedAnalysisLoop`다.
- `ai-workbench-connector`: 외부 AI가 evidence를 조회하는 경로다. 원격 tool call 수는 분자가 아니며 evidence 확인까지 이어져야 한다.
- `first-party-ai`: 모델 tier나 생성량이 아니라 동일 verified analysis loop로 평가한다.
- 데이터, 검색, terminal, report 이니셔티브도 기능별 score를 만들지 않고 아래 goal ID 중 하나를 고른다.

## 착수 순서

```text
North Star Phase 0
  outcome contract + evidence registry + local scorecard
      -> Agent Runtime 실행
      -> first verified analysis vertical slice
      -> four complete evidence windows
      -> numeric target review
```

North Star Phase 0은 제품 기능을 추가하지 않는다. 제품 진행을 과장하지 못하게 만드는 측정 바닥이다.
