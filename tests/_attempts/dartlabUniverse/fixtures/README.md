# Release gold attempts

> 상태: U0-G02 exact-locator machine review queue 600행 완료, reviewed gold 0/600으로 U1 차단
> 책임: human-reviewed positive 300건과 hard negative 300건의 exact evidence, 균형, precision, false acceptance를 release 자산으로 고정한다.

## 실행

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/fixtures/releaseGoldProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/fixtures/releaseGoldReviewQueueProbe.py
$env:DARTLAB_TEST_LOCKED='1'; uv run python -X utf8 -m pytest tests/_attempts/dartlabUniverse/fixtures/testReleaseGoldProbe.py -q --tb=short --no-cov
$env:DARTLAB_TEST_LOCKED='1'; uv run python -X utf8 -m pytest tests/_attempts/dartlabUniverse/fixtures/testReleaseGoldReviewQueueProbe.py -q --tb=short --no-cov
uv run python -X utf8 tests/audit/docstring4Section.py tests/_attempts/dartlabUniverse/fixtures --strict
uv run python -X utf8 tests/audit/docstring9Section.py tests/_attempts/dartlabUniverse/fixtures --strict
```

## Canonical asset 이름

- `reviewedPositive.jsonl`: 사람이 exact document를 열고 승인한 positive 300건
- `hardNegative.jsonl`: 사람이 candidate가 사실이 아님을 확인한 hard negative 300건
- `admissionPredictions.jsonl`: 같은 600 case에 대한 resolver 및 admission 결과
- `releaseGoldSamplingPlan.json`: count와 predicate, source, market, language, evidence class, negative type quota
- `releaseGoldReviewQueue.machine.jsonl`: exact catalog locator가 있는 미검토 positive 후보 300행과 hard-negative challenge 300행
- `releaseGoldReviewQueueReceipt.json`: graph, catalog, queue content hash와 coverage gap receipt

현재 앞의 세 JSONL은 존재하지 않는다. Missing file은 빈 gold로 간주하지 않고 0건 및 release blocker로 센서스한다. Sampling plan과 test fixture는 review 자산이 아니다.

Machine review queue는 사람 검토의 입력 자산일 뿐 gold가 아니다. 모든 600행은 `reviewState=unreviewed`, `goldEligible=false`, reviewer 및 receipt가 null이다. Positive와 challenge 모두 catalog `sourceRef`, exact `charStart`와 `charEnd`, evidence 및 context hash를 갖는다. 사람은 original document를 열어 locator를 이전하고 entity, predicate, direction, event 및 availability time을 확인해야 한다.

## U0-G02 live queue 실측

| 항목 | 실측 |
|---|---:|
| Graph version | 2026-04-14 |
| Graph node / link | 2,664 / 20,560 |
| DART catalog scan | 296,856행 |
| Exact mention before deduplication | 182,072 |
| Machine positive candidate | 300 |
| Machine hard-negative challenge | 300 |
| Positive predicate coverage | 3/6 |
| Hard-negative type coverage | 5/12 |
| Reviewed receipt | 0/600 |
| Gold eligible | 0/600 |

Positive는 `affiliatedWith`, `ownsStakeIn`, `suppliesTo` 각 100행이다. `sellsTo`, `classifiedIn`, `filed`는 현재 source 결합으로 채워지지 않았다. Challenge는 affiliate collision 87, reversed direction 87, self-loop 88, short English common word 35, table header drift 3행이다. 동일 회사명, industry peer, 정정 전후 충돌, 비상장 alias, section title-only, historical ticker, cross-market fuzzy 7개 유형은 별도 source와 사람이 구성해야 한다.

Queue hash는 `sha256:484321d3085209aa2df6de72ea63e749baee2a2a63e38ea62e235b49e075bb12`다. Graph와 catalog snapshot hash, file size 및 행 수는 receipt가 정본이다.

## Positive 필수 계약

- `caseId`, `subjectId`, `predicate`, `objectId`
- `docId`, `sectionPath`, `sourceRef`, `sourceVersion`, `contentHash`
- text의 `evidenceText`, `charStart`, `charEnd`, `snippetHash` 또는 table의 `rowIndex`, `headerHash`, `rowHash`
- `eventAt`, `validFrom`, optional `validTo`, `sourcePublishedAt`, `availableAt`
- `expectedStatus=fact`, `market`, `language`, `evidenceClass`, `sourceKind`
- `origin=humanReviewed`, `reviewMethod=documentOpened`, `reviewer`, timezone-aware `reviewedAt`, unique `reviewReceiptId`

## Hard negative 필수 계약

- Exact `caseId`, subject, predicate, object와 `expectedStatus=reject`
- 계획에 고정한 12개 `negativeType` 중 하나와 사람이 작성한 `reviewReason`
- market, language와 positive와 같은 human review receipt

## 균형

Positive는 KR 및 US, ko 및 en, A 및 B, DART 및 SEC를 각 150건으로 구성한다. `suppliesTo`, `sellsTo`, `ownsStakeIn`, `affiliatedWith`, `classifiedIn`, `filed`는 각 50건이다. Hard negative는 KR 및 US와 ko 및 en 각 150건, OCI형 짧은 영문, 동일 회사명, 계열사, self-loop, 방향 역전, peer 오인, 정정 충돌, 비상장 alias, title-only, table header drift, ticker 변경, cross-market fuzzy의 12개 type을 각 25건으로 구성한다.

## 합격

- Reviewed positive 300/300
- Reviewed hard negative 300/300
- Prediction 600/600
- Positive exact sourceRef precision 98% 이상
- Hard negative false acceptance 1% 이하
- Positive sourceRef coverage 100%
- Reviewer와 reviewedAt 누락 0
- Quota violation 0

## 현재 결과

| 항목 | 실측 |
|---|---:|
| Sampling plan positive | 300 |
| Sampling plan hard negative | 300 |
| Reviewed positive | 0/300 |
| Reviewed hard negative | 0/300 |
| Prediction | 0/600 |
| Positive precision | 미측정 |
| False acceptance | 미측정 |
| SourceRef coverage | 미측정 |
| Quota violation | 30 |
| Machine review queue | 600/600 |
| Machine regression | 27/27 PASS |
| Contract ready | true |
| Live ready | false |

실제 관계 assertion gold가 없으므로 판정은 `revise`다. 기존 `tests/fixtures/search/queryLogGold.real.jsonl` 106건은 search query review 자산이지만 Universe relation identity, exact locator, time, negative type을 갖지 않아 전용하지 않는다. 자동 생성 candidate나 test fixture를 human review로 승격하지 않는다.
