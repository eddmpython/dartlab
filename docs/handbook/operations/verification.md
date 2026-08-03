# 완료와 검증

완료는 임시 설계를 보관 상태로 바꾸는 일이 아니다. 구현 후 현재 사실을 코드와 공개 실행에서 다시 확인하고 handbook에 반영한 다음 임시 설계를 삭제한다. 설계 과정은 Git 이력이 보존한다.

## 완료 절차

1. 실제 사용자 여정을 공개 CLI, API 또는 UI에서 실행한다.
2. 실행 결과와 실패 상태를 코드 계약에 대조한다.
3. 현재 보장되는 동작과 제한만 handbook에 기록한다.
4. 코드, 테스트, README, Skill OS가 임시 설계를 인용하지 않는지 감사한다.
5. 임시 설계 폴더를 삭제한다.
6. 기능별 focused test, 생성 계약 drift, UI type check와 build를 실행한다.
7. Agent Runtime 변경은 실설치 CLI로 대상, 투자지표, 시점, 반대논지와 exact ref가 있는 질문을 실행한다.
8. GUI 변경은 `UI 검수 운영`의 desktop, tablet, mobile audit receipt와 스크린숏을 남긴다. 브라우저 제어가 없으면 시각 검증 미완료로 명시한다.

완료 문서에는 구현 단계, 할 일 체크박스, 진행률 ledger를 남기지 않는다. 미래 변경은 새 임시 initiative로 설계한다.
