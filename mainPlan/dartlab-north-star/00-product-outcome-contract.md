# 00. Product Outcome Contract

## 1. 제품 결과

DartLab이 만드는 결과는 모델 응답이 아니다.

**사용자가 실제 기업, 시장, 공시, 산업, 거시 또는 데이터 universe에서 질문을 시작하고, DartLab 정식 엔진의 계산과 출처를 거쳐, 정확한 evidence 또는 artifact를 직접 확인할 수 있는 분석 결과를 얻는 것**이 제품 결과다.

AI, Python, CLI, terminal, report는 진입 표면이다. 북극성 수명주기는 표면과 모델 제공자에 독립적이어야 한다.

## 2. Verified analysis loop

하나의 loop는 다음 상태를 순서대로 통과한다.

```text
started -> scoped -> grounded -> delivered -> verified -> retained
```

| 상태 | 진입 조건 | 금지되는 대체 신호 |
|---|---|---|
| `started` | 사람이 질문이나 명시적 분석 호출을 시작하고 random `outcomeId`가 발급됨 | 추천 질문 노출, 자동 probe, fixture |
| `scoped` | 회사 코드, filing, 시장, 산업, macro series 또는 명시적 dataset/universe가 canonical subject로 해석됨 | 자유 산문만 있는 대화 |
| `grounded` | `_CONTRACT_ENGINES` 중 하나가 의미 있는 non-empty 결과와 `asOf` 또는 source identity를 반환 | Skill 읽기, 모델 텍스트, 도구 목록 조회 |
| `delivered` | 결과가 `responseStatus=ok`로 끝나고 evidence 또는 artifact가 하나 이상 있으며 필수 evidence gate가 통과 | partial, cancelled, error, missing evidence |
| `verified` | 같은 outcome의 exact evidence ref가 resolve되거나 artifact가 저장 후 다시 열림 | evidence chip 렌더, 링크 hover, generic download |
| `retained` | 28일 안에 같은 analysis capsule이 다시 열리거나 후속 분석의 입력으로 사용됨 | transcript 단순 열람, 자동 복원 |

북극성 분자는 `verified` 전이에 들어간 distinct `outcomeId`다. 한 outcome은 표면, artifact, evidence 수와 무관하게 최대 한 번만 센다. `retained`는 북극성의 후행 품질 지표다.

## 3. 완료 판정

`analysisOutcomeVerified`는 다음 조건이 모두 참일 때만 기록한다.

1. `origin=user`이고 test, health, install, auth, discovery가 아니다.
2. canonical subject 또는 explicit dataset/universe가 있다.
3. 적어도 한 번의 public contract engine 호출이 성공했다.
4. answer, table, chart, report 중 하나가 사용자 표면에 전달됐다.
5. 결과가 참조하는 exact evidence 또는 artifact를 같은 outcome token으로 resolve했다.
6. unresolved verification issue가 없다.
7. 이전 verified receipt와 중복되지 않는다.

로컬 agent runtime의 모델명, vendor, native transcript는 완료 요건이 아니다. 모델을 바꿔도 같은 규칙을 적용한다.

## 4. 제외 조건

다음은 구현돼 있고 유용해도 북극성으로 세지 않는다.

- CLI 설치, 로그인, MCP 등록 성공
- prompt 수, turn 수, token 수, tool call 수
- 페이지뷰, 체류시간, CTA 클릭
- 모델이 생성한 텍스트만 있는 답변
- evidence ref를 발급했지만 실제 resolve하지 않은 답변
- `SaveArtifact`가 경로만 만들고 다시 열지 못한 경우
- 테스트 fixture, golden trace, CI smoke가 만든 결과
- 동일 outcome의 재시도, stream reconnect, duplicate delivery
- API key 저장이나 provider 설정 완료
- 에러 뒤 fallback 텍스트만 반환한 경우

## 5. Product outcome goals

모든 이니셔티브는 아래 goal ID 중 정확히 하나를 primary로 고른다. supporting goal은 여러 개 허용한다. goal ID는 phase나 기능 카테고리가 아니다.

### Complete a verified analysis loop (`completeVerifiedAnalysisLoop`)

- 사용자 결과: 실제 질문이 검증 가능한 분석 결과로 끝난다.
- 측정: `analysisOutcomeVerified` distinct count.
- 초기 target: 모든 release acceptance에서 local fixture journey 1건과 해당 claim의 operator journey 1건이 정확히 한 completion을 만든다.
- disqualifier: 모델 응답, tool call, artifact 생성만 세는 것.

### Start from a real question (`startFromRealQuestion`)

- 사용자 결과: 사용자가 provider 설정을 배우기 전에 회사명, 종목코드, filing, 시장 질문으로 시작한다.
- 측정: `started -> scoped` 전환과 거부 이유.
- 초기 target: ready runtime이 있으면 chat 첫 화면에서 질문까지 1 intentional action, runtime이 없으면 진단과 단일 recovery action.
- disqualifier: 설치 완료나 로그인 완료를 분석 시작으로 세는 것.

### Reach first evidence (`reachFirstEvidence`)

- 사용자 결과: 첫 의미 있는 DartLab 근거를 빠르게 받는다.
- 측정: `timeToFirstEvidenceMs`, cache state와 runtime state를 분리한 분포.
- 초기 target: 먼저 4주 baseline을 수집한다. baseline 전 숫자 SLA를 만들지 않는다.
- disqualifier: 모델 첫 token이나 Skill 본문을 evidence로 세는 것.

### Verify the analysis result (`verifyAnalysisResult`)

- 사용자 결과: 답의 숫자, 표, 공시 근거 또는 artifact가 정확한 source로 열린다.
- 측정: `verified / delivered`, evidence resolve failure, artifact reopen failure.
- 초기 target: release acceptance에서 false positive 0, duplicate completion 0.
- disqualifier: 렌더된 chip 존재만으로 verify하는 것.

### Retain an analysis outcome (`retainAnalysisOutcome`)

- 사용자 결과: 이전 분석을 다시 열거나 다른 runtime에서 evidence capsule로 이어 쓴다.
- 측정: 28일 안 `retained / verified`.
- 초기 target: transcript 복사 없이 같은 capsule을 두 번째 세션에서 resolve하는 operator journey 1건.
- disqualifier: sidebar history 제목 클릭, provider transcript 복제.

### Protect research trust (`protectResearchTrust`)

- 사용자 결과: 분석 중 실패, 취소, runtime 교체가 secret, 원문, 기존 artifact를 손상시키지 않는다.
- 측정: secret leak, transcript copy, invalid evidence, partial artifact, unsafe permission acceptance.
- target: 알려진 breach 0.
- disqualifier: 오류를 성공으로 바꾸거나 provider token을 DartLab store에 저장.

### Keep analysis responsive (`keepAnalysisResponsive`)

- 사용자 결과: 긴 분석 중에도 cancel, reconnect, 다른 화면 작업이 가능하다.
- 측정: queue budget, first evidence, cancel settlement, orphan process, memory budget.
- 초기 target: blocking pipe wait 0, cancel 후 5초 안 process settlement, session queue 상한 준수.
- disqualifier: timeout 뒤 child process가 남는 것.

### Keep capability parity (`keepCapabilityParity`)

- 사용자 결과: AI, CLI, Python, UI가 같은 DartLab capability와 evidence 문법을 사용한다.
- 측정: public engine/capability registry와 MCP, UI action, generated contract의 drift.
- target: provider name branch 0, UI 독자 business rule 0, documented capability drift 0.
- disqualifier: 새 runtime마다 도구 목록이나 모델 목록을 별도 복사.

## 6. Guardrails

북극성 증가가 다음 중 하나를 악화시키면 그 window는 성장 근거로 무효다.

- evidence 정확성과 source identity
- 미래정보 누수와 as-of 정합성
- 외부 본문 untrusted 경계
- secret, 질문, 종목, 파일 경로의 외부 telemetry 유출
- runtime 취소와 child process 정리
- tool과 artifact의 원자성
- public contract와 UI parity
- 응답성, 메모리, event queue budget

repair가 growth보다 우선한다.
