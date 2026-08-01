---
id: recipes.meta.screen.distressEarlyWarning
title: Distress Early Warning — Altman 적용성 확인 + 회계 포렌식
category: recipes
kind: recipe
scope: builtin
status: blocked
purpose: Altman Z'' 부실위험 판별 점수와 회계 포렌식을 결합하는 조기경보 절차. Beneish 원식 입력 계약이 복구되기 전에는 M-score 교집합 스크린을 실행하지 않는다.
whenToUse:
  - 부실 경보
  - distress early warning
  - Altman Beneish
  - 회계 조작 의심
linkedSkills:
  - engines.scan
  - engines.quant
  - engines.credit
  - engines.company
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - executionRef
  - sourceRef
gap:
  primary:
    - quant
    - credit
falsifier:
  description: Beneish 결과 status가 ok가 아니면 두 점수의 교집합이나 red-flag 비율을 발행하지 않는다.
  pythonCheck: |
    assert beneish["status"] == "ok", beneish["reasonCode"]
expectedNovelty:
  - altmanZpp
  - modelCoverage
forbidden:
  - Altman 점수를 부도확률로 표현 X.
  - 금융사 또는 company type 결측 종목을 Altman universe에 포함 X.
  - Beneish unavailable을 clean, 0점, 0%로 표현 X.
  - proxy 계정으로 Beneish 1999 원식이라고 주장 X.
failureModes:
  - 회사 유형 분류 부재 시 Altman 적용 불가.
  - 연간 연결 필수 계정 결손 시 Altman 적용 불가.
  - Beneish canonical 계정 계약 미구현.
lastUpdated: '2026-08-01'
runtimeCompatibility:
  server:
    status: blocked
  localPython:
    status: blocked
  mcp:
    status: blocked
  webAi:
    status: blocked
  pyodide:
    status: blocked
---

## 현재 공개 호출 계약

```python
import dartlab

altman = dartlab.quant("altman", market="KR")
assert altman["status"] == "ok"
assert altman["variant"] == "zpp"

beneish = dartlab.quant("beneish", market="KR")
if beneish["status"] != "ok":
    raise RuntimeError(beneish["reasonCode"])
```

Altman 기본 호출은 비금융 적격 종목에 Z'' 한 모델만 적용한다. 반환된
`methodology.thresholds`, `coverage.excludedByReason`, `pointInTime`을 점수와 함께
인용한다. `variant="z"`는 제조업 상장사와 같은 회계연도 말 시가총액이 있을 때만
계산하며, 시총 결손을 Z'로 바꾸지 않는다.

Beneish 축은 현재 `canonical_inputs_unavailable`을 반환한다. LTD, current maturities,
income-tax payable, 순수 감가상각 등 원식 계정의 공급자 공통 의미와 공시 as-of가
보장되기 전에는 M-score, clean/red-flag, 교집합 universe를 만들지 않는다.

## 재활성화 게이트

1. 두 감사 연간 기간의 동일 연결 범위와 비금융 적용성을 확인한다.
2. 원식 계정의 XBRL/DART source, 단위, 보고기간, filed-at provenance를 보존한다.
3. 독립 oracle로 8개 성분과 최종 점수를 검증한다.
4. KR 표본의 임계 적용 한계를 공개하고 `분식 확정`, `회계 투명`을 사용하지 않는다.
5. 위 조건이 모두 통과한 뒤 recipe status와 runtimeCompatibility를 supported로 바꾼다.
