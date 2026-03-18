# 068 newCompanyShowTest

## 목표

현재 `Company.show(topic, block)`의 docs table 경로를 바로 흡수하지 않고,
실험 폴더에서 먼저 `new show` 프로토타입을 완성도 있게 검증한다.

핵심 질문은 3개다.

1. block 하나 안에 섞인 여러 logical subtable을 분리해 낼 수 있는가
2. 현재 raw markdown fallback 블록을 wide DataFrame으로 더 많이 복구할 수 있는가
3. 흡수 시 `show(topic, block)`는 그대로 두고 내부 구현만 고도화할 수 있는가

## 실험 구조

```
068_newCompanyShowTest/
├── STATUS.md
├── 001_newCompanyShowPrototype.py
├── 002_sampleValidation.py
├── 003_readinessGate.py
└── 004_fullCoverage.py
```

## 파일 역할

### 001_newCompanyShowPrototype.py

- block 단위 multi-schema renderer
- 전 기간 동시 스캔
- canonical schema 생성
- schema별 wide / long DataFrame 렌더링
- `show(topic, block)` 내부 구현 후보를 코드로 검증

### 002_sampleValidation.py

- 대표 10종목 x 핵심 topic 표본 검증
- 현재 show() wide block 수 vs prototype wide block 수 비교
- recovered block / regression block 집계

### 003_readinessGate.py

- 표본 기준 흡수 전 gate
- recovered / regression / 핵심 topic 커버리지 기반 PASS/WARN/FAIL 판정

### 004_fullCoverage.py

- 로컬 docs 보유 **283종목 전체**
- 대표 10개 table-heavy topic 전수
- 현재 `_horizontalizeTableBlock()` vs prototype 비교

## 현재 판단

- `sections`를 바꿀 실험이 아니라 `show()` 레이어를 바꿀 실험이다
- 공개 `show()` 호출 형태를 바꿀 필요는 아직 없다
- 방향은 `sections 유지 + Company.show 내부 구현 고도화`다
- 단일 block -> 단일 DataFrame 강제는 약하고, 내부적으로는 multi-schema 인식이 유효하다

## 실행 결과

### 001 결과

- 삼성전자 `audit` block 1:
  - 현재 show는 raw fallback `(1, 40)`
  - prototype은 schema 10개를 분리했고 그중 6개가 wide로 렌더링됨
  - 대표 shape: `(56, 25)`, `(48, 25)`, `(27, 17)`, `(28, 5)`, `(20, 5)`
- 삼성전자 `salesOrder` block 1:
  - 현재 show는 raw fallback `(1, 18)`
  - prototype은 schema 1개를 wide `(123, 19)`로 렌더링

### 002 결과

- 대표 10종목 x 10 topic, 총 954 table block 검증
- 현재 show() wide: 633
- prototype wide: 884
- recovered: 271
- regression: 20

| topic | currentWide | protoWide | recovered | regression | protoRate |
|------|-------------|-----------|-----------|------------|-----------|
| boardOfDirectors | 72 | 131 | 59 | 0 | 0.936 |
| riskDerivative | 145 | 166 | 35 | 14 | 0.902 |
| executivePay | 85 | 115 | 33 | 3 | 0.885 |
| companyOverview | 57 | 83 | 26 | 0 | 0.912 |
| rawMaterial | 38 | 63 | 25 | 0 | 0.984 |
| audit | 37 | 62 | 25 | 0 | 0.939 |
| employee | 57 | 79 | 24 | 2 | 0.919 |
| majorHolder | 83 | 105 | 22 | 0 | 0.963 |
| salesOrder | 20 | 31 | 11 | 0 | 0.969 |
| dividend | 39 | 49 | 11 | 1 | 0.942 |

### 003 결과

- readiness summary:
  - tableBlocks 954
  - currentWideBlocks 633
  - protoWideBlocks 884
  - protoGain +251
  - recoveredBlocks 271
  - regressionBlocks 20
- gate:
  - overall PASS
  - audit PASS
  - salesOrder PASS
  - boardOfDirectors PASS
  - executivePay PASS

### 004 결과

- 범위: **로컬 docs 보유 283종목 x 대표 10개 table-heavy topic 전수**
- 총 22,001 table block
- 실행 시간: 746.7초
- currentWide: 16,050
- protoWide: 19,159
- recovered: 3,400
- regression: 291
- **net gain: +3,109**

| topic | blocks | currentWide | protoWide | recovered | regression | protoRate |
|------|--------|-------------|-----------|-----------|------------|-----------|
| boardOfDirectors | 3,173 | 2,071 | 2,863 | 800 | 8 | 0.902 |
| rawMaterial | 1,753 | 1,160 | 1,707 | 555 | 8 | 0.974 |
| riskDerivative | 2,246 | 1,913 | 2,121 | 297 | 89 | 0.944 |
| audit | 1,731 | 1,261 | 1,537 | 282 | 6 | 0.888 |
| companyOverview | 2,721 | 2,121 | 2,388 | 272 | 5 | 0.878 |
| majorHolder | 2,584 | 2,121 | 2,391 | 271 | 1 | 0.925 |
| salesOrder | 1,074 | 716 | 965 | 253 | 4 | 0.899 |
| employee | 2,226 | 1,716 | 1,914 | 243 | 45 | 0.860 |
| executivePay | 3,068 | 1,916 | 2,093 | 226 | 49 | 0.682 |
| dividend | 1,425 | 1,055 | 1,180 | 201 | 76 | 0.828 |

## 최종 판단

- **가능성은 충분히 확인됨**
- 표본이 아니라 전종목 기준으로도 `recovered 3,400 > regression 291`
- 가장 강한 개선축은 `boardOfDirectors`, `rawMaterial`, `riskDerivative`, `audit`, `salesOrder`
- 흡수 전 우선 정리 대상은 regression이 상대적으로 큰 `riskDerivative`, `dividend`, `executivePay`, `employee`
- 다음 단계는 API 설계가 아니라 **회귀 291건 축소 실험**이다

## 흡수 조건

아래가 충족되면 흡수 검토로 넘어간다.

1. regression 291건을 의미 있게 줄인다
2. `riskDerivative`, `dividend`, `executivePay`, `employee`의 회귀 패턴을 별도 실험으로 정리한다
3. prototype이 예외 없이 반복 실행된다
4. 공개 `show()` API는 유지하고 내부 구현만 교체 가능한 수준으로 정리된다
