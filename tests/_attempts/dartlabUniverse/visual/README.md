# Visual attempts

> 상태: U0-V01 grammar contract 완료, reviewed comprehension 차단
> 책임: semantic LOD, 상태 문법, layout 결정론, renderer 성능, 접근성, 3D uplift를 반증한다.

## 가설

의미 좌표와 representation 교체형 zoom을 쓰고 truth status를 color 외 중복 channel로 표현하면, force graph보다 상태, 시간, 근거, 결손을 빠르고 정확하게 읽을 수 있다.

## 실행 순서

1. U0-V01: fact, candidate, derived, disputed, retracted, scenario, unknown 문법 판독. Contract 완료, participant review 대기
2. U0-V02: 고정 anchor와 deterministic layout
3. U0-V03: 250, 500, 1,000 node density와 omitted receipt
4. U0-V04: validAt와 knownAt 이중 시간 comprehension
5. U0-V05: keyboard, screen reader, mobile low GPU
6. U0-V06: SVG, current Cosmos, DOM, 후보 renderer bakeoff
7. U5-X01: 2D 대비 2.5D 또는 3D uplift

## U0-V01 실행

```powershell
node --check tests/_attempts/dartlabUniverse/visual/visualGrammarProbe.mjs
node --test tests/_attempts/dartlabUniverse/visual/testVisualGrammarProbe.mjs
node tests/_attempts/dartlabUniverse/visual/visualGrammarProbe.mjs
node tests/_attempts/dartlabUniverse/visual/visualGrammarProbe.mjs --responses C:/review/universeVisualResponses.json
```

Test는 repository test lock을 획득한 뒤 `testVisualGrammarProbe.mjs` 단일 파일만 실행한다.

## 상태 문법

| 상태 | Stroke | Pattern | Glyph | Label | Evidence action |
|---|---|---|---|---|---|
| fact | solid | none | check-circle | 근거 확인 | openEvidence |
| candidate | dash | diagonal-open | search | 근거 탐색 중 | findEvidence |
| derived | double | horizontal | function | 계산 결과 | inspectDerivation |
| disputed | dash-dot | cross | split | 근거 충돌 | compareEvidence |
| retracted | strike | backslash | undo | 철회됨 | openRetraction |
| scenario | dot | wave | flask | 가정 시나리오 | inspectAssumptions |
| unknown | gap | empty | question | 판정 불가 | explainGap |

Color는 보조 channel이다. Confidence는 opacity를 바꾸지 않고 낮음, 중간, 높음 badge와 1/3, 2/3, 3/3 marker로만 표현한다.

## Reviewed response 계약

Response file은 participant 1명당 아래 record 하나를 가진 JSON array다.

```json
{
  "participantId": "participant-01",
  "reviewer": "operator-name",
  "reviewedAt": "2026-07-15T10:00:00+09:00",
  "origin": "humanReviewed",
  "responses": [
    {"cardId": "visual-card-01", "selectedStatus": "fact"}
  ]
}
```

각 participant는 30개 card를 중복 없이 모두 답해야 한다. Participant ID는 중복될 수 없다. `origin=humanReviewed`가 아니거나 reviewer, reviewedAt이 없으면 채점하지 않는다. Synthetic perfect response는 scoring contract test에만 사용하고 live 결과로 저장하지 않는다.

## U0-V01 결과

| 항목 | 실측 |
|---|---:|
| State | 7 |
| Deterministic card | 30 |
| Unique non-color signature | 7/7 |
| Color-only collision | 0 |
| Evidence affordance | 30/30 |
| ARIA description | 30/30 |
| DOM reference card | 30/30 |
| Confidence opacity usage | 0 |
| Machine regression | 8/8 PASS |
| Reviewed participant | 0/12 |
| Reviewed response | 0/360 |
| Comprehension accuracy | 미측정 |
| Grammar contract ready | true |
| Comprehension ready | false |
| Live ready | false |

판정은 `revise`다. Grammar token, DOM reference card, 30-card answer key, reviewed scoring contract는 완료했다. 그러나 실제 participant가 0명이므로 90% comprehension을 주장하지 않는다. U0-V01 production visual admission은 participant 12명과 360개 reviewed response를 채우기 전 차단한다.

## 합격

- 상태 판독 90% 이상
- label collision 2% 이하
- logical coordinate hash 일치, 같은 viewport와 DPR에서 고정 anchor 재실행 오차 1px 이하
- desktop 45fps, mobile 30fps 목표 또는 명시적 lower LOD
- table에서 핵심 task 100% 완료

## 기각

- unknown을 낮은 점수 색으로 표현
- opacity 하나로 confidence와 status를 표현
- 3D에서만 가능한 핵심 기능
- decorative starfield 또는 particle가 정보 수율을 낮춤
- 새 dependency가 task, frame, heap, bundle을 개선하지 못함

## 다음

U0-V02에서 renderer와 독립적인 logical coordinate와 viewport anchor contract를 만든다. Participant review가 필요한 U0-V01은 열어 둔 채 machine-only layout work를 진행할 수 있지만 production 이관은 불가하다.

Production dependency는 U0-V06 결론 전에 추가하지 않는다.
