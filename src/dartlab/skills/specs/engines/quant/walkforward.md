---
id: engines.quant.walkforward
title: Quant Walk-forward Validation
category: engines
kind: curated
status: observed
purpose: ruleFactory refit walk-forward와 고정 룰 temporal stress를 구분한다.
sourceRefs:
  - dartlab://skills/engines.quant.walkforward
knowledgeRefs:
  - engines.quant
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
whenToUse:
  - 전략 walk-forward 검증
  - in-sample overfitting 회피
  - train/test window 슬라이딩
---

## 엔진 역할

quant 엔진의 워크포워드 축 응용 skill이다. ruleFactory 경로만 train-only refit OOS로 인증하고, 고정 Rule 또는 style 경로는 temporal stress로 표시한다. 단일 candidate API이므로 PBO는 산출하지 않는다. SSOT는 `_AXIS_REGISTRY` (`src/dartlab/quant/__init__.py`)다.

## 공개 호출 방식

```python
import dartlab

# 1. 문자열 호출
result = dartlab.quant("walkforward", "005930", style="trendFollow")

# 2. accessor 호출 (동등)
result = dartlab.quant.walkforward("005930", style="trendFollow")
```

## 호출 동작

종목 005930의 가격 시계열을 읽어 비중복 train/test 경로를 만든다. `step == test`만 허용하며 fold별 신호를 시간순으로 연결한 뒤 한 번의 체결 원장으로 계산한다. 고정 Rule은 `oos=False`, ruleFactory는 `oos=True`다. DSR은 실제 `nTrials`를 명시한 경우에만 계산하고 PBO는 `None`이다.

### ruleFactory 옵션 (forecast OOS 검증)

기본 style 호출은 정적 Rule temporal stress다. forecast 모델처럼 *IS fit + OOS predict* 패턴은 `walkForward(close, rule=None, ruleFactory=...)` 또는 공개 `ruleFactory=` 인자로 호출한다.

```python
from dartlab.quant.benchmark.forecast import forecastRuleFactory
from dartlab.quant.strategy.backtest import walkForward

factory = forecastRuleFactory(threshold=0.002, models=["ar1"])
bt = walkForward(close, rule=None, ruleFactory=factory, train=120, test=30, step=30, nTrials=4)
bt.validation["refit_count"]   # fold마다 재학습 횟수
bt.validation["oos_sharpes"]   # 단일 OOS 원장의 fold 구간 Sharpe
bt.validation["n_trials"]      # DSR에 사용한 실제 탐색 횟수
bt.pbo                           # None, 단일 candidate라 판정 불가
```

`ruleFactory(is_close, oos_len) -> Rule` 시그니처다. 반환 Rule 길이는 정확히 `train + test`여야 한다. test 영역의 첫 forecast는 첫 OOS 시가에 체결되고 마지막 forecast도 마지막 OOS 시가에 도달한다. 배경 호환을 위해 `cpcv`가 `validation`의 alias로 유지된다.

## 대표 반환 형태

strategy 그룹 표준에 따른 dict 또는 DataFrame 반환. 공통 키:

- `stockCode` / `corpName`: 대상 종목 (해당 시)
- `latestAsOf` / `priceDate`: 데이터 기준일
- 축 고유 metric / score / verdict / rank column (정확한 spec 은 `_AXIS_REGISTRY['walkforward'].fn` 함수 docstring 검산)
- `flags` / `assumptions`: 결손 · 가정

전체 키는 base SKILL `engines.quant` 표 + 함수 docstring 으로 검산.

## 기본 실행 순서

1. 대상 종목 (또는 종목 리스트), 기준일, benchmark 확정.
2. 위 공개 호출 그대로 실행.
3. `latestAsOf` / 결손 종목 / `flags` / `assumptions` 점검.
4. 숫자 claim 은 `valueRef` / `dateRef` / `executionRef` 에 묶음.
5. 다축 narrative 조립은 `engines.story` 또는 상위 recipe 가 담당.

## 기본 검증

이 skill 은 공개 실행 문서다. 본 axis 호출 방식, 반환 키, 오류 / 제한 동작이 변경되면 같은 변경에서 본 파일을 갱신한다. SSOT 는 `_AXIS_REGISTRY` (`src/dartlab/quant/__init__.py`) + 함수 docstring.
