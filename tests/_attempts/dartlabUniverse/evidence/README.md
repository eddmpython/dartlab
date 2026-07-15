# Evidence attempts

> 상태: U0-E01 resolver 계약 완료, live assertion evidence와 reviewed gold 차단
> 책임: filing, section, exact locator, source version, 이중 시간, entity direction을 한 pointer로 결속한다.

## 가설

검색 catalog의 section hit를 candidate로 유지하고 immutable source와 exact text 또는 table locator가 완비된 단일 후보만 승격하면, assertion evidence false accept를 구조적으로 차단할 수 있다.

## 실행

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/evidence/exactEvidenceProbe.py
uv run python -X utf8 tests/audit/docstring4Section.py tests/_attempts/dartlabUniverse/evidence --strict
uv run python -X utf8 tests/audit/docstring9Section.py tests/_attempts/dartlabUniverse/evidence --strict
```

Unit test는 repository test lock을 획득한 뒤 `testExactEvidenceProbe.py` 단일 파일만 실행한다.

## 계약

- Request는 exact `subjectId`, `predicate`, `objectId`, `direction`을 가진다.
- Document ID는 DART receipt 또는 SEC accession canonical filing ID다.
- Text evidence는 decoded section content의 `charStart`, `charEnd`, `snippetHash`를 함께 검증한다.
- Table evidence는 `rowIndex`, `headerHash`, `rowHash`를 함께 검증한다.
- Source version과 content hash는 `sha256:` digest만 수용한다. Adapter version은 source version이 아니다.
- `sourcePublishedAt`과 `availableAt`은 timezone-aware이고 publication이 availability보다 늦을 수 없다.
- Exact pointer가 여러 개면 첫 행을 고르지 않고 `ambiguousSource`로 남긴다.
- Missing 또는 mismatch는 `notFound`, `ambiguousEntity`, `directionUnknown`, `timeUnknown`, `sourceVersionMissing`, `sourceUnavailable`, `locatorInvalid`로 fail closed한다.

## U0-E01 결과

| 항목 | 실측 |
|---|---:|
| Search catalog snapshot | 3 |
| Catalog row | 381,149 |
| Document 및 section locator | 381,149/381,149 |
| SourceRef | 381,149/381,149 |
| Content hash | 381,149/381,149 |
| Source dataAsOf | 381,149/381,149 |
| Adapter version | 381,149/381,149 |
| Exact text span | 0 |
| Exact table row 및 header | 0 |
| SourcePublishedAt 및 availableAt | 0 |
| Row-level immutable source version | 0 |
| Predicate 및 direction | 0 |
| Assertion evidence ready | 0 |
| Reviewed positive | 0/100 |
| Reviewed hard negative | 0/100 |
| Synthetic regression | 8/8 PASS |
| Public transfer metrics | 미측정 |
| Live ready | false |

세 catalog는 section 검색과 다시 열기 후보로는 완전하다. 그러나 whole-section `sourceRef`와 `textHash`는 exact assertion evidence가 아니다. `sourceDataAsOf`는 availability timestamp가 아니며 `sourceAdapterVersion`은 source bytes의 immutable version이 아니다. Manifest의 file hash도 catalog row가 source file path와 결속되지 않아 row-level source version으로 승격하지 않는다.

판정은 `revise`다. Resolver contract는 완료했고 synthetic text, table positive와 entity, predicate, direction, time, source version, locator 변조, 다중 source negative는 모두 fail closed했다. Live source는 exact locator와 time, version, semantics가 0행이고 reviewed gold와 public transfer 측정이 없어 assertion admission을 계속 차단한다.

## 다음

U0-O01에서 relation과 assertion identity, revision, validAt, knownAt을 분리한다. Evidence가 없는 assertion은 candidate를 넘지 못하며 U0-E01 live gate가 닫힌 동안 observed 승격은 0으로 유지한다.

Production 코드는 이 경로를 import하지 않는다.
