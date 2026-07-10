# 브라우저 노트북 레슨 (커리큘럼 SSOT)

레슨 한 편 = YAML 파일 한 개. 그 파일이 **유일한 진실**이다. 브라우저 노트북과 파이썬 게이트가
같은 파일을 읽는다.

```
lessons/
  content/{track}/{NN}-{slug}.yaml   레슨 원본 (여기만 만진다)
  registry.ts                        트랙 정의 + 로더 + 셀 투영
  types.ts                           스키마 타입
```

## 왜 YAML 인가

이 파일을 읽는 소비자가 둘이다.

- 브라우저: `registry.ts` 가 `import.meta.glob(?raw)` 로 원본을 그대로 싣고 런타임에 파싱한다.
  파생 산출물(구운 JSON·TS)이 없으므로 SSOT 가 그대로 배송된다.
- 파이썬: `tests/audit/notebookContract.py` (공개 계약) 와 `tests/audit/lessonSchema.py` (스키마)
  가 같은 파일을 읽는다.

TS 는 파이썬이 못 읽고, JSON 은 사람이 못 쓴다. YAML 이 그 교집합이다.
`landing/src/lib/blog` 와 Skill OS 카탈로그가 쓰는 로딩 패턴과 동형이다.

## 새 레슨 한 편 추가하기

1. 트랙과 순서를 정한다. 트랙은 `registry.ts` 의 `TRACKS` 에 등재된 것만 쓴다.
   새 트랙이면 거기 한 줄 + 폴더 하나를 만든다.
2. `content/{track}/{NN}-{slug}.yaml` 을 만든다. **사람이 만지는 파일은 이것 하나다.**
3. 검사한다.

```bash
uv run python -X utf8 tests/audit/lessonSchema.py       # 스키마 · 그래프 · 경계 · 규모
uv run python -X utf8 tests/audit/notebookContract.py   # 공개 호출 계약
```

4. 브라우저에서 눈으로 확인한다. `cd landing && npm run dev` 후 `/notebooks` 에서 레슨을 열고
   전체 실행한다. **실행해 보지 않은 코드는 레슨에 넣지 않는다.**

## 스키마

```yaml
meta:
  id: grab-company          # 필수. corpus 유일. 파일을 옮겨도 진도가 안 끊기게 여기 명시한다
  title: 회사 하나를 잡는 것에서 시작한다
  description: 카드에 뜨는 한 줄
  level: 기초                # 기초 | 중급 | 심화
  track: foundations        # registry.ts TRACKS 의 id
  order: 1                  # 트랙 안에서 유일
  tags: [company]
  company: "005930"         # 선택. 있으면 setup 셀(import + Company)을 자동으로 넣는다
  prerequisites: [...]      # 선택. 다른 레슨 id. 사이클 금지
  minutes: 8                # 선택

intro:
  goal: 한 줄 목표
  body: |
    레슨 첫 markdown 셀이 되는 본문

sections:
  - id: identity            # 레슨 안에서 유일. 진도 오버레이가 이 id 로 셀을 매칭한다
    title: 무엇을 잡았나       # 선택
    body: |                 # 선택. 코드 셀 위 설명
      설명
    code: |                 # 선택. 없으면 markdown 전용 섹션
      c.corpName
    runtime: pyodide        # 기본 pyodide. local 이면 브라우저에서 읽기 전용
    expectError: true       # 선택. 이 셀은 브라우저에서 예외가 나는 것이 정상(경계 수업)
```

## 기계가 막아 주는 것

- 필수 필드 누락, `level`/`runtime` 오타, 미등록 트랙
- 레슨 id 중복, 트랙 안 order 중복, 섹션 id 중복
- `prerequisites` 가 없는 레슨을 가리키거나 사이클을 만드는 것
- 코드 셀 문법 오류
- **경계 정합**: 브라우저에서 못 도는 호출(`c.gather("price")` 같은 수집, `scan("screen")` 등)을
  `runtime: pyodide` 로 태깅하면 차단. `runtime: local` 이나 `expectError: true` 를 붙여야 한다
- **공개 호출 계약**: `Company.{method}` 는 엔진 skill `capabilityRefs` 등재분만, 톱레벨은
  `dartlab.__all__` 만. `c.audit()` 같은 미등재 내부 메서드는 차단
- **규모**: 레슨 원본 총량이 임계(250KB)를 넘으면 실패한다. 그때 `registry.ts` 를 색인(경량 메타
  eager) + 본문(지연 청크)으로 분리하라는 신호다. 미리 나누지 않는다

## 브라우저에서 되는 것과 안 되는 것

실측 정본은 skill `runtime.pyodide` 다. 요약하면,

- 된다: `c.panel("IS"/"BS"/"CF")` · `c.select` · `c.analysis` · `c.credit` · `c.story` ·
  `c.trace` · 인자 없는 카탈로그 조회(`c.gather()` · `c.quant()` · `c.analysis()`) ·
  `dartlab.macro(...)` · `dartlab.scan(...)` 중 growth · profitability · liquidity · cashflow ·
  ratio · account · debt
- 안 된다: `c.gather("price")` 같은 실제 수집(브라우저는 스레드를 못 만든다) ·
  `scan("screen")`(KRX 목록 필요) · `scan("workforce")`(직원수 프리빌드 필요) ·
  `scan("quality")`(finance-lite 에 `total_assets` 부재)

안 되는 것을 가르치고 싶으면 `expectError: true` 로 경계 수업을 만든다.
`content/foundations/03-data-boundary.yaml` 이 그 예다.

## 레슨과 개인 노트북

- 레슨을 열면 `lesson:<레슨 id>` 라는 **안정 id** 로 IndexedDB 에 저장된다. 다시 열면 하던 곳에서
  이어진다. 저장 개수가 레슨 수를 넘지 않는다.
- 카드의 '초기화' 는 그 저장분을 지운다. 다음에 열면 원본이 다시 투영된다.
- 사용자가 직접 만든 노트북은 uuid 다. 허브의 '내 노트북' 과 사이드바 Files 패널은 `lesson:`
  접두를 걸러 낸다.
