# Visual attempts

> 상태: U0-V01 및 V04 grammar, U0-V02 layout, U0-V03 density, U0-V05 accessibility, U0-V06 renderer contract 완료, reviewed comprehension과 외부 reader 수동 확인 차단
> 책임: semantic LOD, 상태 문법, layout 결정론, renderer 성능, 접근성, 3D uplift를 반증한다.

## 가설

의미 좌표와 representation 교체형 zoom을 쓰고 truth status를 color 외 중복 channel로 표현하면, force graph보다 상태, 시간, 근거, 결손을 빠르고 정확하게 읽을 수 있다.

## 실행 순서

1. U0-V01: fact, candidate, derived, disputed, retracted, scenario, unknown 문법 판독. Contract 완료, participant review 대기
2. U0-V02: 고정 anchor와 deterministic layout. Contract 완료
3. U0-V03: 250, 500, 1,000 node density와 omitted receipt. Contract 완료
4. U0-V04: validAt와 knownAt 이중 시간 comprehension. Grammar contract 완료, participant review 대기
5. U0-V05: keyboard, screen reader, reduced motion, high contrast, 200% zoom, mobile low GPU. Contract 완료, 외부 reader 수동 확인 대기
6. U0-V06: SVG, current Cosmos, DOM, Canvas 2D renderer bakeoff. Contract 완료, 새 외부 dependency 기각
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

## U0-V02 실행

```powershell
uv run python -X utf8 -m tests._attempts.dartlabUniverse.visual.liveLayoutFixture --compact
node --test tests/_attempts/dartlabUniverse/visual/testDeterministicLayoutProbe.mjs
node tests/_attempts/dartlabUniverse/visual/deterministicLayoutProbe.mjs --live
tests/_attempts/dartlabUniverse/visual/browserLayoutAudit.ps1
```

Python test는 repository test lock을 획득한 뒤 `testLiveLayoutFixture.py` 단일 파일만 실행한다. Browser audit은 같은 실행 시점에 고정한 live fixture를 local reference와 함께 제공하고 Chrome, Firefox, WebKit session을 종료한다.

## U0-V02 결과

| 항목 | 실측 |
|---|---:|
| Live scene | 3 |
| Atlas node | 18 |
| Industry node | 26 |
| Company node | 50 |
| Total node | 94 |
| Valid time known | 0/94 |
| Valid time unknown lane | 94/94 |
| Pure logical hash | 60/60 |
| Three-viewport anchor hash | 180/180 |
| Browser measurement | 180/180 |
| Browser logical hash | 180/180 |
| Browser anchor hash | 180/180 |
| Viewport and DPR match | 180/180 |
| Maximum anchor drift | 0px |
| Force iteration | 0 |
| Node regression | 10/10 PASS |
| Python regression | 2/2 PASS |
| Layout contract ready | true |

판정은 `promote`다. U0-P01의 live Atlas, 반도체 산업, 삼성전자 company scene을 새 graph 사본 없이 사용했고 input 순서를 20회 교란해도 scene별 logical hash와 viewport anchor가 같았다. Current artifact에는 node valid time이 없으므로 임의 순서를 만들지 않고 94개 전부를 unknown time lane으로 보냈으며 receipt에 known 0과 unknown 94를 남겼다. 이 계약은 deterministic layout만 졸업시키며 U0-V01 comprehension과 U0-V04 validAt 및 knownAt 판독을 대신하지 않는다.

## U0-V03 실행

```powershell
node --check tests/_attempts/dartlabUniverse/visual/densityOmissionProbe.mjs
node --test tests/_attempts/dartlabUniverse/visual/testDensityOmissionProbe.mjs
node tests/_attempts/dartlabUniverse/visual/densityOmissionProbe.mjs
```

실제 DOM audit은 `densityReference.html`을 1280x720 desktop과 390x844 mobile viewport에서 열고 250, 500, 1,000 node query를 각각 측정한다. Reference는 같은 pure projection 결과만 DOM mark와 고정 label box로 표시한다.

## U0-V03 결과

| 입력 | Target | Active node | Active edge | Visible label | Node omitted | Edge omitted | DOM collision |
|---:|---|---:|---:|---:|---:|---:|---:|
| 250 | desktop | 250/500 | 750/1,000 | 55/80 | 0 | 0 | 0% |
| 250 | mobile | 250/250 | 500/500 | 40/40 | 0 | 250 | 0% |
| 500 | desktop | 500/500 | 1,000/1,000 | 57/80 | 0 | 500 | 0% |
| 500 | mobile | 250/250 | 500/500 | 40/40 | 250 | 1,000 | 0% |
| 1,000 | desktop | 500/500 | 1,000/1,000 | 57/80 | 500 | 2,000 | 0% |
| 1,000 | mobile | 250/250 | 500/500 | 40/40 | 750 | 2,500 | 0% |

| 계약 | 실측 |
|---|---:|
| Exact node, edge, label omission receipt | 6/6 |
| Reverse-input receipt hash | 6/6 |
| Budget compliant | 6/6 |
| Maximum calculated label collision | 0% |
| Maximum DOM label collision | 0% |
| Machine regression | 8/8 PASS |
| Density contract ready | true |

판정은 `promote`다. Active mark를 desktop 500 node 및 1,000 edge, mobile 250 node 및 500 edge로 제한하고 label은 80 및 40 이하에서 collision-free로 선택했다. 화면에 나오지 않은 node, edge, label은 각각 budget, omitted endpoint, label collision 또는 label budget reason으로 100% 설명한다. `기타 N개` aggregate receipt는 member와 status count, coverage, 변화 quantile, top changes를 보존한다. 이 계약은 renderer 성능 FPS나 접근성 동등성을 증명하지 않으며 U0-V05와 U0-V06을 우회하지 않는다.

## U0-V04 실행

```powershell
node --check tests/_attempts/dartlabUniverse/visual/bitemporalComprehensionProbe.mjs
node --test tests/_attempts/dartlabUniverse/visual/testBitemporalComprehensionProbe.mjs
node tests/_attempts/dartlabUniverse/visual/bitemporalComprehensionProbe.mjs
node tests/_attempts/dartlabUniverse/visual/bitemporalComprehensionProbe.mjs --responses C:/review/universeTimeResponses.json
```

## U0-V04 reviewed response 계약

Response file은 participant 1명당 아래 record 하나를 가진 JSON array다.

```json
{
  "participantId": "time-participant-01",
  "reviewer": "operator-name",
  "reviewedAt": "2026-07-16T10:00:00+09:00",
  "origin": "humanReviewed",
  "responses": [
    {"taskId": "time-task-01", "selectedValid": true, "selectedKnown": true}
  ]
}
```

각 participant는 12개 task에 validAt과 knownAt answer를 모두 boolean으로 답해야 한다. Participant ID와 task ID는 중복될 수 없다. `origin=humanReviewed`가 아니거나 reviewer, reviewedAt이 없으면 채점하지 않는다. Synthetic perfect response는 scoring contract test에만 사용하고 live 결과로 저장하지 않는다.

## U0-V04 결과

| 항목 | 실측 |
|---|---:|
| Deterministic revision task | 12 |
| Valid and known answer combination | 4/4 |
| Separate validAt and knownAt control | 12/12 |
| Combined slider usage | 0 |
| ARIA time summary | 12/12 |
| DOM reference task | 12/12 |
| Machine regression | 9/9 PASS |
| Reviewed participant | 0/12 |
| Reviewed task response | 0/144 |
| Reviewed axis answer | 0/288 |
| ValidAt accuracy | 미측정 |
| KnownAt accuracy | 미측정 |
| Combined accuracy | 미측정 |
| Time grammar contract ready | true |
| Comprehension ready | false |
| Live ready | false |

판정은 `revise`다. 미래 효력 선공시, 과거 사건 지연 공시, open interval, inclusive boundary와 source publication 및 availability 차이를 포함한 네 answer 조합을 모두 만들었다. Assertion identity에서 query validAt과 knownAt을 제외하고 reality와 knowledge control 및 DOM fieldset을 분리했다. 그러나 실제 participant가 0명이므로 두 축과 combined 90% 판독을 주장하지 않는다. U0-V04 production Time Lens admission은 participant 12명과 144개 reviewed task response를 채우기 전 차단한다.

## U0-V05 실행

```powershell
node --check tests/_attempts/dartlabUniverse/visual/accessibilityEquivalenceProbe.mjs
node --test tests/_attempts/dartlabUniverse/visual/testAccessibilityEquivalenceProbe.mjs
node tests/_attempts/dartlabUniverse/visual/accessibilityEquivalenceProbe.mjs
python -m http.server 8767 --bind 127.0.0.1 --directory tests/_attempts/dartlabUniverse/visual
```

실제 브라우저 audit은 `accessibilityReference.html`을 1280x720과 390x844에서 열어 native keyboard action, semantic accessibility tree, reduced motion, high contrast, 200% zoom reflow, mobile low GPU table fallback을 측정한다. Audit 뒤 viewport를 복원하고 browser session과 local server를 종료한다.

## U0-V05 결과

| 항목 | 실측 |
|---|---:|
| Core action | 6 |
| Equivalent surface | 2 |
| Accessibility profile | 6 |
| Spatial 및 table command parity | 6/6 |
| Unique focus ID | 12/12 |
| Native keyboard control | 12/12 |
| Screen reader summary 및 live region | 12/12 |
| Synthetic profile task | 36/36 |
| Spatial browser keyboard task | 6/6 |
| Table browser keyboard task | 6/6 |
| Reduced motion duration | 0s |
| High contrast non-color treatment | 6/6 |
| 200% zoom computed font / horizontal overflow | 32px / false |
| Mobile low GPU table task | 6/6 |
| Mobile low GPU spatial surface | 0 |
| Spatial-only core action | 0 |
| Machine regression | 11/11 PASS |
| Accessibility contract ready | true |
| External named screen reader manual session | 미실행 |
| Production ready | false |

판정은 접근성 동등 경로 계약 `promote`, production admission `revise`다. Spatial DOM과 relation table이 여섯 핵심 command를 같은 순서로 제공하고 keyboard로 각각 6/6을 완료했다. In-app accessibility tree에서 list, table caption, row header, independent time input, polite status를 확인했다. Reduced motion은 0s, high contrast는 double border와 underline, 200% zoom은 horizontal overflow 없음, 390x844 low GPU에서는 spatial surface 없이 table task 6/6을 완료했다. 다만 실제 NVDA, JAWS, VoiceOver 같은 named screen reader 수동 세션은 실행하지 않았으므로 public UI production 이관 전 별도 manual gate로 남긴다.

## U0-V06 실행

```powershell
node --check tests/_attempts/dartlabUniverse/visual/rendererBakeoffProbe.mjs
node --check tests/_attempts/dartlabUniverse/visual/rendererBakeoffBrowser.mjs
node --test tests/_attempts/dartlabUniverse/visual/testRendererBakeoffProbe.mjs
node tests/_attempts/dartlabUniverse/visual/rendererBakeoffProbe.mjs
npm install --prefix tests/_attempts/dartlabUniverse/visual/.renderer-bakeoff --no-package-lock --no-save --ignore-scripts @cosmograph/cosmos@1.6.1 esbuild@0.25.6
python -m http.server 8768 --bind 127.0.0.1 --directory tests/_attempts/dartlabUniverse/visual
```

Browser audit은 desktop 1280x720에서 500 node 및 1,000 edge, mobile 390x844에서 250 node 및 500 edge를 SVG, locked current Cosmos, DOM relation table, built-in Canvas 2D로 각각 3회 측정한다. Frame은 72개 selection frame의 trial별 P95 중 최악값, mount는 trial P95, heap은 task loop 뒤 `usedJSHeapSize` 최댓값이다. Bundle은 esbuild 0.25.6 minify와 gzip level 9로 재현한다. `.renderer-bakeoff` dependency와 bundle, browser session, local server는 측정 뒤 제거한다.

## U0-V06 결과

| Renderer | Desktop mount P95 | Desktop frame P95 | Desktop heap | Mobile mount P95 | Mobile frame P95 | Mobile heap | Task desktop/mobile |
|---|---:|---:|---:|---:|---:|---:|---:|
| SVG reference | 5.5ms | 140.845fps | 9,759,782B | 5.0ms | 140.845fps | 7,231,276B | 6/6, 6/6 |
| Current Cosmos 1.6.1 | 80.7ms | 140.845fps | 14,703,331B | 145.4ms | 140.845fps | 11,389,243B | 6/6, 6/6 |
| DOM relation table | 12.3ms | 138.889fps | 7,926,751B | 9.8ms | 138.889fps | 6,048,807B | 6/6, 6/6 |
| Canvas 2D candidate | 3.9ms | 140.845fps | 10,645,237B | 1.9ms | 135.135fps | 10,840,050B | 6/6, 6/6 |

| Bundle 및 결정 | 실측 |
|---|---:|
| Built-in portfolio raw / gzip | 17,438B / 5,770B |
| Cosmos incremental raw / gzip | 311,453B / 91,863B |
| Cosmos portfolio raw / gzip | 328,891B / 97,633B |
| Canvas 2D incremental external dependency | 0B |
| Desktop task 및 performance ready | 4/4, 4/4 |
| Mobile task 및 performance ready | 4/4, 4/4 |
| Current Cosmos license | CC-BY-NC-4.0 |
| Current Cosmos Universe production license ready | false |
| New external dependency required | false |
| Canvas 2D candidate promoted | true |
| Machine regression | 7/7 PASS |
| Renderer contract ready | true |
| Production ready | false |

판정은 renderer contract `promote`, production admission `revise`다. 네 renderer가 bounded fixture와 핵심 task를 전부 보존하고 desktop 45fps 및 512MB, mobile 30fps 및 250MB 예산을 통과했다. Canvas 2D는 Cosmos보다 desktop과 mobile의 최종 heap이 낮고 외부 dependency가 0이며 built-in 포트폴리오 bundle은 Cosmos 포함 포트폴리오의 약 5.3%다. 따라서 Universe L2 및 L3 bounded graph는 SVG, built-in Canvas 2D, DOM table 포트폴리오를 사용하고 새 renderer dependency는 추가하지 않는다. Current Cosmos는 비교 기준으로만 남기며 lockfile의 `CC-BY-NC-4.0` license 때문에 Universe production admission은 false다. 기존 map renderer는 이 attempt에서 변경하지 않는다.

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

U0-G01에서 reviewed positive 300개와 hard negative 300개 release gold를 구성하고 precision 98% 및 false accept 1% gate를 실행한다. U0-V01과 U0-V04 participant review 및 U0-V05 named screen reader 수동 확인 전 production 이관은 불가하다.

Universe production renderer에는 새 외부 dependency를 추가하지 않는다.
