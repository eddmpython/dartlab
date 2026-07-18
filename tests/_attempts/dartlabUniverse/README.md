# DartLab Universe U0

상태: 읽기 전용 full census attempt. 3D, UI, route, 공개 버튼, RAG, 영속 index는 아직 없다.

이 디렉터리는 이전 Universe 실험을 전부 제거한 뒤 `mainPlan/dartlab-universe/`의 제품 계약에 맞춰 처음부터 다시 만든 데이터 엔진 경계다. 기존 `src/dartlab`, `ui`, `landing`, `blog`, `media`는 수정하지 않고 authority로 읽기만 한다.

## 현재 구현 범위

- `HF_REPO`, `HF_MEDIA_REPO`, 모든 `DATA_RELEASES[*].repo`의 동적 합집합
- private repo를 포함한 Hugging Face dataset revision, path, oid, byte, format 전수 census
- payload body 다운로드 0
- `dartlab.capabilities()`와 analysis, credit, industry, macro, quant, scan, story registry 병렬 census
- 블로그 post, companion, podcast 전수 parse
- 중앙 media catalog, HF object tree, 블로그 reference 양방향 reconciliation
- configured repo 누락, access denied, metadata 누락, 미분류 format, media 누락과 broken ref의 fail-closed G0
- canonical JSON과 같은 revision의 결정론적 snapshot digest
- 기존 시스템 보호 path byte digest 검사

## 정본 명령

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/census.py --all --strict --format json
```

명령은 token을 출력하지 않으며 canonical JSON만 stdout에 쓴다. 결과를 보존하려면 shell redirect나 CI artifact를 사용한다. repo 안에 census 산출물을 bake하지 않는다.

## 2026-07-18 live 인수 기록

아래 값은 제품 상수가 아니라 당시 live authority 관측값이다.

| 항목 | 관측값 |
|---|---:|
| configured HF repo | 4 |
| HF file | 77,875 |
| HF byte | 307,065,890,133 |
| runtime capability | 226 |
| registry record | 141 |
| blog post | 275 |
| companion | 353 |
| media object | 3,120 |
| podcast | 13 |
| terminal coverage | 100% |
| payload body read | 0 |
| wall clock | 36.95초 |
| Python peak memory | 184,231,482 bytes |
| G0 | PASS |

관측 snapshot digest는 `49673d54447f56ca7b67539ab88e90366275f8f13cd965e15a5eb8aecb17108e`다. 다음 실행은 설정과 remote revision을 다시 읽으므로 개수와 digest가 자동으로 달라질 수 있다.

## 다음 gate

U0가 검증되고 운영자가 계속 진행하도록 승인한 뒤에만 U1 identity, temporal, provenance를 같은 attempt 경계에 추가한다. 기존 runtime 승격, 독립 3D harness, UI 연결, 공개 route는 각각 후속 gate와 운영자 확인 전까지 금지한다.
