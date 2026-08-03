# Agent Runtime 운영

## 준비 확인

```powershell
uv run python -X utf8 -m dartlab agent status --refresh
```

각 런타임에서 설치, 인증, 프로토콜, DartLab MCP 연결이 모두 준비됐는지 확인한다. 설치나 연결은 먼저 계획을 출력해 `argv`와 `digest`를 검토한 다음 동일 digest를 승인해 실행한다. 로그인은 Runtime Center가 보여 주는 공식 명령을 사용한다.

## 실질 Ask 검증

단순 인사 대신 대상, 지표, 여러 기간이 있는 실제 질문을 사용한다.

```powershell
uv run python -X utf8 -m dartlab ask --runtime codex "삼성전자 005930 최근 5년 매출과 영업이익 추이"
```

완료 판정은 답변 문자열 유무가 아니다. 실행 결과에서 다음을 확인한다.

- `finalEvent=answer`
- `verificationStatus=evidenceCommitted`
- `answerQuality.passed=true`
- `requiredClaimCells`와 `coveredClaimCells`가 같음
- 최종 답변이 인용한 ref가 committed evidence에 존재함
- 첫 답변 보완이 필요했다면 같은 session과 outcome을 유지함
- `repairMode=deterministic`이면 추가 네이티브 턴 없이 정식 근거로 교정됐는지 확인함
- CLI 상태줄의 마지막 품질 판정이 `verify: ok`임

2026-08-03 로컬 실질 실행에서는 Codex와 Claude Code의 설치, 인증, MCP 연결을 확인했다. Codex로 삼성전자 최근 5개년 매출과 영업이익 질문을 실행해 같은 세션의 자동 보완 뒤 10개 claim cell을 모두 덮고 품질 점수 100으로 근거를 commit했다. 이어서 질문 계약을 최초 턴에 주입한 실행은 추가 보완 없이 한 번에 통과했다. 결정론 교정까지 연결한 최종 실행에서는 후보 품질 실패 뒤 네이티브 턴을 추가하지 않고 10개 exact value ref 표를 구성해 80.9초, 의미 도구 3개, `verify: ok`, 종료코드 0으로 끝났다.

## 장애 복구

- 여러 런타임이 준비됐는데 기본값이 없으면 Runtime Center에서 하나를 고른다.
- 인증 실패는 계정 정보나 명령 원문을 노출하지 않고 로그인 필요 상태로 낮춘다.
- MCP 연결이 오래된 설정이면 새 연결 계획을 적용하고 probe를 다시 실행한다.
- 브라우저 연결이 끊기면 서버 session event replay를 sequence 기준으로 사용한다.
- 소비자가 스트림을 닫으면 현재 네이티브 turn을 중단한다.
- 세션 종료 시 자식 프로세스를 종료한다.
