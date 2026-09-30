# `tests/_evals/` — dartlab.ai 에이전트 출력 회귀 (Track 3)

> 본 SSOT — [tests/POLICY.md](../POLICY.md) §5 Track 3.

## 목적

dartlab 정체성 = 자가개선 루프. 에이전트가 prompt/tool 바뀐 뒤에도 *같은 질문에 동등 품질의 답* 을 내는지 회귀 검증한다. syrupy 가 CLI 화면 회귀를 잡듯, 본 트랙은 에이전트 출력 회귀를 잡는다.

## 6 채점 신호

| 신호 | 의미 | 채점 방식 |
|---|---|---|
| `factual_correctness` | 기대 키워드 (회사명/숫자/항목) 등장 | 룰 (substring) |
| `evidence_citation` | Ref/source 인용 여부 | 룰 (`[ref:` 또는 `출처:` 패턴) |
| `tool_use_appropriate` | 기대 도구 호출 (search/analyze 등) | 룰 (tool log) |
| `format_compliance` | 응답 구조 (JSON/markdown/표) | 룰 (parser) |
| `reasoning_depth` | 단순 사실 ≠ 깊이 — 인과 사슬 길이 | 외부 모델 judge |
| `no_hallucination` | 환각 키워드 (`예상`, `아마도`, 미존재 회사) | 룰 + 외부 모델 cross-check |

룰 기반 4 신호는 CI Fast 안에서 무료 실행 가능. 외부 모델 judge 2 신호는 `eval` 마커 + 운영자 트리거.

## 디렉토리 구조

```
tests/_evals/
├── eval_set.jsonl       # 질문 + 기대 평가 (한 줄 = 한 case)
├── judge.py             # 6 신호 채점기 (룰 + 옵션 외부 모델)
├── runner.py            # 에이전트 실행 + judge 호출
├── test_eval_smoke.py   # CI Fast (룰 기반 mock case)
├── test_eval_live.py    # 운영자 트리거 (실 호출, 비용)
├── _runs/               # 결과 ledger (gitignored)
└── README.md (본 파일)
```

## eval_set.jsonl 스키마

```jsonc
{
  "id": "samsung_overview_v1",                              // 고유
  "question": "삼성전자 5 분기 매출 추세 알려줘",
  "expected_signals": {
    "factual_correctness": ["삼성전자", "005930", "분기", "매출"],
    "evidence_citation": true,
    "tool_use_appropriate": ["finance", "analyze"],
    "format_compliance": "markdown_with_table",
    "min_reasoning_depth": 2,                              // 외부 judge
    "forbidden_hallucinations": ["예상", "아마도"]
  },
  "tags": ["domain:finance", "level:basic"],
  "baseline_score": 0.85                                   // 회귀 임계
}
```

## 실행

### CI Fast (룰 기반, 무료)

```powershell
$env:DARTLAB_TEST_LOCKED="1"; $env:UV_NO_SYNC="1"
uv run python -X utf8 -m pytest tests/_evals/test_eval_smoke.py -v
```

### 운영자 트리거 (실 호출, $)

```powershell
$env:OPENAI_API_KEY="..."  # 또는 ANTHROPIC_API_KEY
$env:DARTLAB_EVAL_LIVE="1"
uv run python -X utf8 -m pytest tests/_evals/test_eval_live.py -m eval -v
```

비용 추정: case 당 $0.01~0.05 (judge 추가 호출 포함). 50 case ≈ $1~3 / run.

### 결과 비교

```powershell
$env:UV_NO_SYNC="1"
uv run python -X utf8 -m tests._evals.runner --compare-baseline
```

## 갱신 절차

1. **새 케이스 추가** — PR 에서 `eval_set.jsonl` 에 한 줄 추가. CI Fast 룰 채점 통과 확인.
2. **baseline 갱신** — 운영자 트리거 1 회 → 결과 ledger 의 평균 점수를 `baseline_score` 에 기록.
3. **회귀** — 다음 run 의 점수가 `baseline_score - 0.05` 이하면 fail.

## 의도적으로 안 하는 것

- **외부 평가 프레임워크 (inspect-ai 등) 의존** — dartlab 도메인 깊이가 깊어 자체 채점기가 적합. 외부 도구 추가는 비용 대비 가치 낮음.
- **CI Fast 에서 실 호출** — 비용 + flaky. 운영자 트리거 + nightly 한정.
- **judge 결과를 단일 점수로 함수 평균** — 6 신호 분리 보고. 한 신호 실패는 다른 신호 평균으로 상쇄되지 않음.

## 새 세션의 첫 사용 평가

`firstUseCases.csv`는 단일 수치, 전종목 조건 검색, 시계열, 공시 의미 검색, 관계, 데이터 부재를
포함하는 20개 질문이다. 기존 native ask 진입점과 동일한 세션 엔진을 사용한다.

```powershell
$env:UV_NO_SYNC="1"
uv run python -X utf8 tests/ai/runners/firstUseAudit.py --output <공유실행폴더> --native
```

질문별로 새 세션을 열고, 발견 응답과 실제 도구 호출, 최종 답변을 기록한다. `--cases size,revenue`
등으로 좁힐 수 있다. `--native`를 생략하면 발견 응답만 측정한다. 실행은 사용자의 기존 로그인과
런타임 설정을 사용한다. 세션 종료 시 계산 표와 실행 프로세스를 닫는다. 원문 로그와 세션 DB는
공유 실행 폴더에만 두고, 검토한 집계표만 저장소에 남긴다.

### 2026-09-30 관측

기준 revision은 `9f495b885b53eb51b38037e797cfc7a76e2697f6`이다. 변경 전후 동일한 질문을 각각
20개 실행했다. `firstUseResults.csv`의 `sourceHash`는 실행 시작 시 AI 소스의 SHA-256이며,
`candidate`는 전체 비교 실행, `followup`과 `eventFollowup`은 관측된 오류를 수정한 뒤의 별도
재실행이다. 후속 결과를 전체 비교 수치에 섞지 않는다.

| 지표 | 변경 전 | 전체 비교 실행 |
|---|---:|---:|
| ReadSkill 응답 문자 수 중앙값 | 54,783.5 | 13,738.5 |
| 개발·운영 Skill이 섞인 질문 | 8/20 | 0/20 |
| 첫 실제 자료 도달 중앙값 | 19.4초 | 20.4초 |
| 최종 답변까지 중앙값 | 56.7초 | 62.6초 |
| 도구 호출 중앙값 | 6 | 7.5 |
| 오류 반환 합계 | 31 | 33 |
| 완전한 답변 | 12 | 13 |
| 일부 답변 | 4 | 6 |
| 미완료 | 3 | 0 |
| 기대한 답변 보류(가상 회사) | 1 | 1 |

완전한 답변은 질문의 핵심 요구에 답하고 반환된 근거를 인용한 경우다. 일부 답변은 후보나
일부 수치를 얻었으나 요청한 비교·범위·사건 순서를 확정하지 못한 경우다. 이는 도구 원자료와
답변의 일관성을 검토한 결과이며, 외부 원공시와 모든 숫자를 독립 대조한 정확도 평가는 아니다.
가상 회사는 수치를 만들지 않은 기대 동작으로 따로 센다. 따라서 자료 질문 19개의 완료율은
12/19에서 13/19로 바뀌었다. 질문별 판정 이유는 CSV에 남긴다.

초기 runner가 API 설명을 실제 자료 도달로 세던 문제는 이벤트 timestamp로 보정했다.
첫 자료 시간은 데이터가 없는 가상 회사 질문을 제외한 중앙값이다. 양쪽 오류 중 각각 20건은
설치된 런타임이 전역 안내 파일을 다시 읽으려다 안전 경로 밖으로 차단된 경우다. 이 경계는
유지했다. 그 밖의 오류는 11건에서 13건으로 늘어, 호출 오류 감소 가설은 지지되지 않았다.

매출 증가·영업현금흐름 악화 질문은 미완료에서 연간 연결 수치를 확인한 답변으로 바뀌었다.
재고 증가 질문은 전체 계정 표를 join하고 연도 조건을 계산해 예비 후보를 얻었다. 규모 비교도
미리보기 대신 전체 매출 표에서 순위와 비율을 계산했다. 계산 결과는 SQL, 조회 인자, 표 hash,
원자료 ref로 추적한다. 수식 계산을 제외한 원천 수집과 지표 의미는 기존 데이터 owner가 맡는다.

실사용에서 발견한 없는 Skill 링크와 SQLite LIKE 차단은 수정했다. SQL 방언 혼동으로 나온
LEAST 호출에는 SQLite MIN/MAX 안내를 추가했다. 일반 Python 실행이나 별도 질의 언어,
고정 도구 순서를 추가하지 않았다. 긴 Skill 본문의 기본 확장과 중복 본문을 첫 응답에서 뺐다.

남은 실패는 연결·별도 조회의 값/ref 충돌, 미국 기업 통화 메타데이터, 스크리닝 표의 회계기간과
연결 기준 부재, 공시 사건 순서와 최신성 검증이다. 이들은 표 계산 기능으로 해결됐다고 볼 수
없으며 각 원자료 owner에서 별도로 검증해야 한다. 이번 실행은 Hugging Face 전체 수집 감사가
아니다.

각 질문 1회 관측이므로 속도 차이를 통계적 개선으로 해석하지 않는다. 로컬 캐시와 동시에 진행한
빌드의 영향은 통제하지 않았고, 실제 모델 식별자와 토큰 사용량은 측정하지 않았다. 후속 실행에서
‘정체’의 수치 기준이 달라 후보 수가 달라진 사례도 있어, 반복 비교에는 조건을 고정해야 한다.
