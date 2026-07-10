---
id: engines.industry.lifecycle
title: Industry — 라이프사이클 (lifecycle)
category: engines
kind: curated
scope: builtin
status: observed
purpose: 산업 라이프사이클 5 phase (도입·성장·성숙·재도약·쇠퇴) 시계열 분류 — Vernon 1966 + 자체 재도약 phase. 산업 매출 YoY 임계로 phase 자동 라벨링, 단일 종목 industryBadge.phase 의 SSOT.
whenToUse:
  - 라이프사이클
  - lifecycle
  - 산업 phase
  - Vernon phase
  - 도입·성장·성숙·재도약·쇠퇴
  - 산업 단계 분류
  - 도입기·성장기·성숙기·쇠퇴기
sourceRefs:
  - dartlab://skills/engines.industry.lifecycle
capabilityRefs:
  - industry
knowledgeRefs:
  - engines.industry
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
    status: limited
linkedSkills:
  - engines.industry
  - engines.scan
  - engines.macro
---

## 엔진 역할

`industry` 엔진의 *라이프사이클 분류* sub-axis. 산업 단위 매출 YoY 시계열을 5 phase 로 자동 라벨링한다. 단일 종목 답변의 `industryBadge.phase` 가 본 분류 SSOT 를 인용한다. base SKILL `engines.industry` 의 `lifecycle=True` 모드를 본 spec 이 풀어 서술.

## 공개 호출 방식

```python
import dartlab

# 1. 산업 단위 phase 시계열
phases = dartlab.industry("semiconductor", lifecycle=True)
# → DataFrame: 연도 · 매출합계 · YoY · phase · phaseLabel

# 2. 단일 종목 phase (자동 부착)
c = dartlab.Company("005930")
result = c.panel("IS")
result.data.industryBadge.phase   # "재도약"
```

## 호출 동작

1. `dartlab.industry(industryId)` 의 종목·공정 매핑 + 각 종목 `select("IS")` 매출 합산 → 산업 매출 시계열.
2. 연도 단위 YoY 산출 + 임계 분류:
   - **도입** (introduction): YoY ≥ 30% (초기 급성장)
   - **성장** (growth): 10% ≤ YoY < 30%
   - **성숙** (maturity): 0% ≤ YoY < 10%
   - **쇠퇴** (decline): YoY < 0%
   - **재도약** (resurgence): 쇠퇴 후 반등 (YoY < 0 직후 ≥ 10% 진입)
3. 시계열 + 현재 phase 라벨 + confidence (sample size · 변동성 기반).

`Company.panel(...).data.industryBadge.phase` 는 자동 부착 — 별도 호출 불필요. 산업 단위 시계열은 명시 호출.

## 대표 반환 형태

```text
dartlab.industry("semiconductor", lifecycle=True)
→ DataFrame
   연도 : str               # "2020" / "2021" / ...
   매출합계 : float          # 산업 내 종목 매출 sum (원)
   YoY : float              # 전년대비 (-1.0 ~ +1.0+)
   phase : str              # "introduction" / "growth" / "maturity" / "decline" / "resurgence"
   phaseLabel : str         # 한글 ("도입" / "성장" / ...)
   confidence : float       # 0.0 ~ 1.0 (sample size + 변동성)
```

```text
Company("005930").industry()
→ dict
   industry / industryName / stage / stageName
   role / stream / confidence / source / peers
```

## 기본 실행 순서

1. **단일 종목 phase** — `Company.panel("IS").data.industryBadge.phase` 그대로 인용 (자동 부착).
2. **산업 단위 phase 시계열** — `dartlab.industry(industryId, lifecycle=True)` 명시 호출.
3. `phase` 답변에 `[conf:{confidence}]` 표기 (Vernon 3-phase 정의 기준 변동성).
4. cross-industry phase 비교는 한계 명시 — 산업별 매출 단위·peer 수 차이.

## 기본 검증

- 반환 DataFrame 의 `phase` 컬럼 값이 5 phase enum 안.
- YoY 임계 분류 일관성 — 같은 산업 같은 연도 재호출 시 phase 동일.
- 단일 종목 `industryBadge.phase` 와 산업 시계열 마지막 phase 일치 (같은 분류 SSOT).

본 spec 은 공개 실행 문서다. `lifecycle=True` 모드의 임계·반환 컬럼·5 phase enum 이 변경되면 본 파일을 같은 변경에서 갱신한다.

## 관련

- [engines.industry](/skills/engines.industry) — base SKILL (전체 모드 + industryBadge 자동 부착)
- [engines.scan](/skills/engines.scan) — phase 별 peer screen
- [engines.macro](/skills/engines.macro) — 산업 phase × 매크로 cycle 정합
