---
id: operation.philosophy
title: Philosophy — dartlab 사상 SSOT
kind: curated
scope: builtin
status: observed
category: operation
purpose: dartlab 의 존재 이유와 설계 원칙을 한 문서에 묶는 사상 정점 SSOT. 4 가지 비교 가능성 · 6 막 인과 · Company 편의성 3 원칙 · simple > complex · SSOT · 사람↔엔진↔AI 환류 흐름.
whenToUse:
  - dartlab 왜 이렇게 설계됐나
  - 새 기능 추가 전 사상 검증
  - 6 막 인과 구조 확인
  - 비교 가능성 4 종 (회사간 · 기간간 · 시장간 · 엔진간)
  - simple > complex 적용 판단
  - SSOT 위반 점검
  - 사람 ↔ AI 환류 흐름
  - 외부 기여자가 dartlab 사상을 한 번에 파악
inputs:
  - 새 기능 또는 변경
  - 적용 대상 (코드 · 문서 · skill)
outputs:
  - 사상 적용 결과
  - 검증 게이트 통과 여부
  - 단순화 또는 SSOT 통합 제안
toolRefs:
  - operation.code
  - operation.apiContract
  - operation.architecture
linkedSkills:
  - operation.coreloop
  - operation.opsAsSkills
  - operation.code
  - operation.architecture
  - operation.apiContract
sourceRefs:
  - dartlab://skills/operation.philosophy
requiredEvidence:
  - 사상 게이트 적용 결과
  - SSOT 통합 점검
  - executionRef
  - sourceRef
expectedOutputs:
  - 비교 가능성 분류
  - 6 막 인과 위치
  - simple > complex 적용
  - SSOT 정리
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: supported
procedure:
  - 작업이 4 가지 비교 가능성 (회사간 · 기간간 · 시장간 · 엔진간) 중 어디를 늘리는지 분류한다.
  - 6 막 인과 (경제 → 섹터 → 기업 → 재무 → 가치) 의 어느 단계에 위치하는지 잡는다.
  - simple > complex — 기존 함수 N 회 호출로 가능한지 자문한 뒤, 가능하면 새 모듈을 만들지 않는다.
  - SSOT — 같은 정보가 두 곳에 있는지 점검하고, 발견되면 한 곳으로 통합한다.
  - 환류 — 새로 발견한 패턴 · 반례 · 조합을 docstring · skill · 블로그 frontmatter 로 사람 자산에 돌린다.
failureModes:
  - 4 비교 축 외 차원을 추가해 카탈로그 부풀림
  - 분석을 6 막 안에 끼워 맞추지 않고 즉흥적으로 진행
  - 기존 함수 호출 가능한데 wrapper / adapter 신설
  - 같은 dict / 상수를 코드와 문서 양쪽에 중복 배치
  - 발견 패턴을 코멘트로만 남기고 사람 자산에 환류 안 함
forbidden:
  - dartlab 의 4 비교 축 외 차원을 즉흥 신설하지 않는다.
  - 6 막 외부 (예 — 종목 가격 단독 trick) 를 분석 본체로 삼지 않는다.
  - 하드코딩 dict 와 registry 를 동시에 두지 않는다.
  - 같은 사상 본문을 두 SSOT 에 중복 작성하지 않는다.
  - 미노출 API (호출처 0) 를 살려두지 않는다.
examples:
  - 새 분석 축 추가 전 사상 검증
  - 6 막 인과로 회사 분석 위치 잡기
  - simple > complex 어떻게 적용
  - dartlab 비교 가능성 4 종이 뭔가
  - 사람과 AI 환류 흐름 어떻게 설계됐나
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-05-06"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

dartlab 의 존재 이유 · 설계 원칙 · 검증 게이트를 한 문서에 묶는다. 새 기능 · 변경 · 분석 시작 전 본 사상 게이트를 통과시킨다.

## 1. 사상 한 줄 — AI ↔ 사람 상호 의존, 엔진이 다리

사람이 엔진 코드와 블로그로 자산을 만든다. 그 자산은 자동으로 AI 의 skill 이 된다 — 공개 함수 docstring 이 곧 AI tool schema, skill 본문이 사용 절차. AI 가 실행 중 발견한 반복 패턴 · 반례 · 새 조합은 엔진 docstring 또는 블로그 frontmatter 로 사람 자산에 환류한다.

**엔진이 다리** — 한 파일이 사람의 분석엔진이자 AI 의 skill 본문.

## 2. 존재 이유 — 비교 가능성

dartlab 은 **4 가지 비교 가능성** 을 늘리는 데 존재한다.

| 비교 축 | 의미 | 엔진 |
|---|---|---|
| **회사간** | 같은 시점에 다른 기업을 비교 | `engines.company`, `engines.scan` |
| **기간간** | 같은 회사를 다른 시점으로 비교 | `Company.panel`, `Company.diff` |
| **시장간** | 한국 DART vs 미국 EDGAR | `engines.edgar`, `Company("AAPL")` |
| **엔진간** | 다른 분석 축의 결과를 한 회사 위에서 합침 | `engines.analysis`, `engines.story` |

이 4 축 밖의 차원을 즉흥 신설하지 않는다. 새 기능이 **어떤 비교 가능성을 늘리는지** 가 첫 자문.

## 3. 6 막 인과 — 분석 범위

```
경제 → 섹터 → 기업 → 재무 → 가치 → 가격
```

종목 없이도 가능한 분석 (경제 · 섹터) 부터 종목이 있어야 가능한 분석 (기업 · 재무 · 가치) 까지. 가격은 결과지 본체가 아니다.

AI 는 적극적 분석가 — Company 분석 시에도 macro · scan · industry 를 엮어 해석한다. 6 막 외부 (예 — 종목 가격 단독 trick · 차트 해석만) 를 분석 본체로 삼지 않는다.

## 4. Company 편의성 3 원칙

| 원칙 | 의미 |
|---|---|
| **접근성** | 종목코드 하나, 추가 import 금지. `dartlab.Company("005930")`. |
| **속도** | 첫 호출 5 초 이내. HuggingFace 자동 다운로드, 캐시. |
| **신뢰성** | 숫자는 원본 그대로, 없으면 `None` (0 으로 채우지 않는다). |

에러 메시지는 해결책 포함:

- 안 됨 — "데이터 없음"
- 됨 — "데이터 없음 → `dartlab.gather('price', '005930')` 먼저 수집하세요"

API 키 필요 시 발급 URL + `.env` 설정법까지.

## 5. SSOT — 모든 지식 · 설정 · 룰은 단일 원천

같은 내용 두 곳 금지. 발견 시 즉시 통합 + 나머지는 포인터만.

- **문서 · 룰 (3층, 한 관심사 = 한 정본)**:
  - 공개 설계·운영 계약 → `skills/specs/**` (Skill OS).
  - 공개 진입·공통 안전 경계만 → 루트 `CLAUDE.md` (세부 복제 금지, Skill OS로 포인터).
  - 운영자↔AI 약속·행동 규약 → 로컬 memory 정본. 저장소 계약·CI 근거로 인용하지 않는다.
  - `feedback_*` 단건 파일 방식은 폐기. 새 교훈은 해당 층의 정본에 흡수한다.
- **코드**: 상수 · dict · 설정 · 매핑은 한 파일 · 한 심볼에만. 하드코딩 dict + registry 공존 금지. 다단 fallback 패치 금지 — 단일 진입점 재설계. 중복 formatter / validator 는 공통 util 통합.
- **skill 동기화**: 기능 개선 · API 변경 · 반환 형태 변경 시 `skills/specs/engines/{engine}/SKILL.md` 동시 갱신. **skill 동기화 없는 기능 개선은 미완료**.

## 6. Simple > Complex

새 모듈 추가 전 자문 — "기존 함수 호출 N 회로 가능한가?" 가능하면 만들지 않는다.

- wrapper · adapter · 중간 레이어 금지.
- 미노출 API (호출처 0) = 즉시 삭제.
- 하드코딩 dict 와 registry 공존 금지.
- 다단 fallback 보다 단일 진입점 재설계.

## 7. 환류 — 사람 ↔ 엔진 ↔ AI

```
사람: 엔진 코드 · 블로그 · 지식 → 자산
   ↓
엔진: 공개 함수 docstring = AI tool schema
   ↓
AI: 발견한 반복 패턴 · 반례 · 조합 → docstring · 블로그 frontmatter 로 환류
```

이 환류 고리가 깨지면:
- AI 가 발견한 패턴이 코멘트로만 남는다.
- 사람이 같은 발견을 다시 한다.
- skill 본문이 코드 변경에 뒤처진다.

환류는 작업 끝의 옵션이 아니라 작업 일부. **skill 동기화 없는 기능 개선은 미완료** 가 환류의 강행규칙.

## 사상 적용 검증 게이트 (실행 절차)

새 기능 · 변경 · 분석 시작 전 다음 5 가지를 자문한다:

1. **비교 가능성** — 어떤 비교 축 (회사간 · 기간간 · 시장간 · 엔진간) 을 늘리나? 4 축 밖이면 다시 생각.
2. **6 막 위치** — 경제 → 섹터 → 기업 → 재무 → 가치 → 가격 중 어디?
3. **simple > complex** — 기존 함수 호출로 가능한가? wrapper 신설 유혹은 없나?
4. **SSOT** — 이 내용이 다른 곳에 이미 있나? 통합 또는 포인터?
5. **환류** — 발견 패턴을 사람 자산 (docstring · skill · 블로그) 으로 돌리는 경로가 있나?

5 항목 통과 후 코드 / 문서 / skill 갱신.

## 다음 단계

- [operation.coreloop](/skills/operation.coreloop) — 자가개선 루프 운영 SSOT.
- [operation.opsAsSkills](/skills/operation.opsAsSkills) — 운영 문서가 skills 체계로 흡수된 흐름.
- [operation.code](/skills/operation.code) — 코드 품질 · 독스트링 · SSOT 3 종.
- [operation.architecture](/skills/operation.architecture) — 레이어 구조 · import 방향.
- [operation.apiContract](/skills/operation.apiContract) — 새 함수 추가 시 API 계약.
- [start.dartlabSkillOs](/skills/start.dartlabSkillOs) — Skill OS 첫 진입.
