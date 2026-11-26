# mainPlan

앞으로 지을 임시 설계와 작업 순서다. 영구 문서나 현재 제품 계약의 정본이 아니다. 현재 동작의 정본은 Skill OS (`src/dartlab/skills/specs/**`, 진입 `start.dartlabSkillOs`) 다.

한 initiative는 폴더 하나다. 구현이 끝나면 코드와 실제 실행에서 확인한 현재 계약을 Skill OS 운영문서 (`specs/operation/**` 등) 에 반영하고 해당 initiative 폴더를 삭제한다. 완료는 이니셔티브 문서의 이관·승격이 아니라 확정 사실의 SSOT 반영이다. `_done`으로 옮기지 않는다. 영구 자산은 mainPlan을 인용하지 않는다.

상태 범례: 🟢 활성 구현 · 🟡 부분 구현 · ⚪ 미착수 임시 설계

## 실행 규칙

1. 착수할 때 initiative 하나를 큰 작업 카테고리로 고정한다. 내부 구현은 작은 논리 단위로 검증하고
   커밋하되, 해당 initiative의 구현과 종료 조건을 모두 끝내기 전에는 다른 initiative로 이동하지 않는다.
2. mainPlan 작성자는 저장소 수정, 정식 테스트, 실데이터 probe, 허용된 도구와 계정, 공개 API 등
   자력으로 수행할 수 있는 모든 경로를 구체적인 구현 작업과 종료 조건으로 싣고 실제로 소진한다.
   자력 경로가 남은 일을 외부 의존, 운영자 작업, 후속 initiative, 승인 대기로 밀어내지 않는다.
3. 모든 자력 경로를 소진한 뒤에도 새 권한, 새 자격증명, 제3자 승인, 시간 경과가 반드시 필요할 때만
   외부 조건으로 기록한다. 그 조건과 독립적인 구현은 같은 initiative 안에서 계속 끝낸다.
4. 구현, 정식 테스트, 현재 Skill OS 계약이 끝난 initiative는 관련 커밋과 잔여를 확인한 같은 사이클에
   폴더째 삭제한다. 완료 상태, 진행 원장, `_done` 보관 폴더를 남기지 않는다.
5. 착수하지 않을 설계를 "운영자 go 대기"로 쌓아 두지 않는다. 지금 하지 않을 설계는 폴더를 지우고,
   코드에 남은 일만 진행 중인 initiative로 옮긴다. 지운 설계는 git 기록에서 꺼낸다.

## 진행 중

2026-11-27 기획 정리로 폴더 20개 가운데 17개를 지우고 3개를 남겼다. 지운 폴더에서 코드에 남은 일은
`v1-readiness-review/02-closed-plan-leftovers.md`로 옮겼다. 순서는 v1.0 점검을 먼저 끝내고 이용자 측정으로 간다.
시뮬레이터는 2026-09-30까지 작업했고 2026-08-04 결정으로 `src/dartlab/simulate`의 공개 계약 밖 코드가 이 기획 소속이라 남겼다.

| 폴더 | 상태 | 한 줄 |
|---|---|---|
| [v1-readiness-review](v1-readiness-review/) | 🟡 | v1.0.0 준비도 전수 검토. 계층별 검토(L0~L4)와 엔진별 재판정은 2026-08-04에 끝났고, 1.0.0 게이트 미달 항목(복잡도, 미테스트 공개 함수)과 남은 부채, 닫은 기획의 잔여를 처리한다. |
| [dartlab-north-star](dartlab-north-star/) | 🟡 | 북극성 `Weekly Verified Analysis Loops`. outcome 계약과 로컬 기록(`productOutcome.py`)은 있고, 증거 감사 게이트와 scorecard, 실제 이용자 측정은 없다. 축별 점수표는 루트 README `## 북극성`이 정본이다. |
| [scenario-simulator](scenario-simulator/) | 🟡 | `scenario`·`strategies` 공개 계약은 Skill OS `engines/simulate`에 있다. AAPL 실제 이력 17쌍 검증에서 현재 모델 오차가 직전 상태 유지 기준보다 커 다음 일은 오차가 나는 거래 확인이다. Play UI, 공개 fan, 전략 비교의 AI 연결과 미도달 스택 결함 9건이 남았다. |
