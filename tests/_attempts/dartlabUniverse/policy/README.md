# Policy attempts

> 상태: U0-P02 및 U0-L01 contract 완료, live public gate 차단
> 책임: public source별 재배포와 lens 가용성을 fail-closed receipt로 검증한다.

## 가설

source별 `RedistributionReceipt`와 환경별 `LensAvailability`를 projection admission에 넣으면 dataset 또는 engine 전체를 뭉뚱그린 공개 판단을 피할 수 있다.

## 실행 순서

1. U0-P02: source별 allowedFields, attribution, policyVersion을 센서스한다. 완료.
2. U0-L01: scalar, series, table, ranking, distribution, scenario archetype과 public, local 가용성을 센서스한다. 완료.
3. public projection fixture에 unknown, localOnly, expired receipt를 주입한다. 완료.

## U0-P02 실행

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/policy/redistributionReceiptProbe.py
uv run python -X utf8 tests/audit/docstring4Section.py tests/_attempts/dartlabUniverse/policy --strict
uv run python -X utf8 tests/audit/docstring9Section.py tests/_attempts/dartlabUniverse/policy --strict
```

Unit test는 repository test lock을 획득한 뒤 `testRedistributionReceiptProbe.py` 단일 파일만 실행한다.

## U0-P02 결과

| 항목 | 실측 |
|---|---:|
| U0-S01 source | 10 |
| reviewed receipt | 0 |
| valid public 또는 metadataOnly receipt | 0 |
| missingReceipt 차단 | 10 |
| publicReady | false |
| synthetic regression | 12/12 PASS |
| negative false accept | 0 |

Contract는 다음을 검증했다.

- field 순서와 중복에 독립적인 canonical receiptId
- allowedFields와 prohibitedFields의 교집합 차단
- policyVersion, reviewer, reviewedAt, expiresAt, attribution 필수 검증
- unknown, localOnly, blocked, expired receipt fail-closed
- metadataOnly field를 derived content로 확대하지 않음
- 금지 upstream 하나가 섞인 derived output 전체 차단
- duplicate source receipt 차단

### 정책 근거 후보

| evidence | 관측 | 판정 |
|---|---|---|
| [immutable HF README](https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/c0260a60859f0ba5a30d452a7c05791d79e9bd1d/README.md) | dataset metadata는 CC BY 4.0 선언 | dataset 편집물 license evidence candidate. upstream field receipt 아님 |
| `.github/scripts/sync/uploadHfReadme.py` | 같은 CC BY 4.0 문구의 local generator | DartLab 표면 attribution 후보. upstream 권리 검토 대체 불가 |
| [OpenDART API 소개](https://opendart.fss.or.kr/intro/main.do) | 공시 원문 자유 추출과 활용 안내 | DART source 검토 evidence candidate |
| [OpenDART 이용약관](https://opendart.fss.or.kr/intro/terms.do) | 약관 변경, 제3자 권리, 정확성 면책 조건 | policyVersion과 정기 expiry review 필요 |

판정은 `revise`다. admission contract는 완료했지만 현재 reviewed receipt registry가 없고 map artifact field의 upstream policy lineage도 결속되지 않았다. 따라서 live source 10개를 자동 public 승인하지 않는다. 운영자 검토가 끝난 receipt만 후속 production registry 후보가 된다.

## U0-L01 실행

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/policy/lensAvailabilityProbe.py
```

## U0-L01 결과

| 항목 | 실측 |
|---|---:|
| live capability | 226 |
| return contract가 있는 capability | 83 |
| capability runtimeCompatibility | 0 |
| capability outputArchetype | 0 |
| capability unit | 0 |
| capability coveragePolicy | 0 |
| capability missingPolicy | 0 |
| Skill OS | 286 |
| Skill OS runtimeCompatibility | 286 |
| Skill OS publicBrowser declaration | 0 |
| current public lens ready | 0 |
| 6 archetype contract regression | 8/8 PASS |

Contract fixture는 scalar, series, table, ranking, distribution, scenario 6개와 publicBrowser, localPython, localServer 3환경을 모두 검증했다. `limited`와 `unavailable`은 loader를 호출하지 않고, available loader의 `None`은 `missing`으로 보존하며 0으로 바꾸지 않는다. public policy가 false이면 local 실행은 유지하고 publicBrowser만 차단한다.

판정은 `revise`다. capability 226개별 UI adapter를 만들지 않는다. capability와 Skill OS를 참조하는 작은 LensSpec registry가 output archetype, unit, coverage, missing, publicBrowser runtime, receipt를 명시해야 한다. 현재 catalog만으로 이 값을 추정할 수 없으므로 live public lens는 0개다.

## 합격

- public mark의 redistribution receipt coverage 100%
- unknown 및 localOnly false accept 0
- lens별 unit, coverage, missing policy 100%
- public에서 unavailable lens가 실행된 것처럼 보이는 사례 0

## 기각

- dataset card 하나로 모든 upstream field를 승인
- 금지 source에서 나온 파생값을 lineage 검사 없이 public 승격
- client에서 unavailable engine을 임의 재계산
- missing lens 결과를 0 또는 빈 성공으로 표시

## 산출물

- `redistributionReceiptProbe.py`, 완료
- `testRedistributionReceiptProbe.py`, 완료
- `lensAvailabilityProbe.py`, 완료
- `testLensAvailabilityProbe.py`, 완료
- source와 lens reviewed fixture, 운영자 검토 전 생성 금지

정책 결론은 법률 자문을 대체하지 않는다. 불명확하면 public에서 차단하고 운영자 검토 대상으로 남긴다.
