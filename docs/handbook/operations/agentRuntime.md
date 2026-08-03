# Agent Runtime 운영

## 최초 1회 준비

일반 사용자는 설치, 공식 로그인, DartLab MCP 연결, 기본 런타임 선택을 각각 실행하지 않는다. 다음 명령 하나가 현재 상태를 확인하고 필요한 단계만 순서대로 수행한다.

```powershell
uv run python -X utf8 -m dartlab setup codex --yes
```

`--yes`를 빼면 변경 없이 전체 계획만 출력한다. GUI에서는 채팅의 Runtime Center에서 `분석 엔진 준비`를 누르고 표시된 계획을 한 번 승인한다. 이미 끝난 단계는 다시 설치하거나 다시 연결하지 않는다. 로그인은 해당 런타임의 공식 대화형 명령으로 열리며 DartLab은 계정 정보나 토큰을 저장하지 않는다.

지원 대상은 Codex와 Claude Code다. Cline은 상태 확인 계약을 유지하지만 투자분석 준비 자동화 대상에는 포함하지 않는다.

## 준비 상태 확인

```powershell
uv run python -X utf8 -m dartlab agent status --refresh
```

각 런타임에서 설치, 인증, 프로토콜, DartLab MCP 연결, 투자 계약이 모두 준비됐는지 확인한다. 정상 사용 가능 상태는 `investmentReady=true`다. 개별 설치와 연결 API는 복구용으로 유지하지만 일반 사용자 여정은 통합 setup을 사용한다.

## 투자분석 실행

종목 하나의 의사결정 브리프는 전용 명령을 사용한다.

```powershell
uv run python -X utf8 -m dartlab invest 005930 --runtime codex
uv run python -X utf8 -m dartlab invest 005930 --runtime codex --expert
```

기본 브리프는 중심논지, 가장 강한 반대논지, 실적 변곡, 산업과 거시 전파, 현재가에 반영된 기대, bear/base/bull 시나리오, 촉매, 리스크, 논지 훼손 조건, 다음 점검 시점을 요구한다. `--expert`는 WACC, reverse DCF, 시나리오 driver, 근거 계보와 결손까지 펼친다.

GUI와 CLI는 같은 Agent Runtime을 사용한다. GUI는 질문을 투자판단, 기업비교, 스크리닝, 공시검토, 실적추이, 일반 리서치 모드로 분류하고 분석 목표, 공개 진행 단계, 후속 질문을 표시한다. 내부 추론과 raw tool payload는 채팅 본문에 노출하지 않는다.

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

2026-08-03 로컬 실질 실행에서는 Codex와 Claude Code의 설치, 인증, MCP 연결을 확인했다. Codex로 삼성전자 최근 5개년 매출과 영업이익 질문을 실행해 10개 claim cell을 모두 덮고 품질 점수 100으로 근거를 commit했다. 결정론 교정 경로는 네이티브 턴을 추가하지 않고 exact value ref 표를 구성해 `verify: ok`, 종료코드 0으로 끝났다.

같은 날 설치된 Codex 런타임으로 `삼성전자 지금 투자할 만한지 핵심 논지와 반대논지를 같이 분석해줘`를 실행했다. 의미 도구 9개를 사용했고 첫 후보가 자동 수정 없이 `verify: ok`를 통과했다. 실행 결과에는 혼합 기준시점, 중심논지와 반대논지, 상대가치와 DCF, 촉매, 리스크, tripwire, 다음 확인 항목과 exact ref가 포함됐다. 내부 처리시간은 195.1초였다.

## 장애 복구

- 여러 런타임이 준비됐는데 기본값이 없으면 Runtime Center에서 하나를 고른다.
- 통합 setup이 중단되면 같은 명령을 다시 실행한다. 완료된 단계는 건너뛰고 실패한 단계부터 재개한다.
- 인증 실패는 계정 정보나 명령 원문을 노출하지 않고 로그인 필요 상태로 낮춘다.
- MCP 연결이 오래된 설정이면 새 연결 계획을 적용하고 probe를 다시 실행한다.
- 브라우저 연결이 끊기면 서버 session event replay를 sequence 기준으로 사용한다.
- 소비자가 스트림을 닫으면 현재 네이티브 turn을 중단한다.
- 세션 종료 시 자식 프로세스를 종료한다.
