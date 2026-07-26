# 02. 목표 제품 아키텍처

## 1. 제품 흐름

```text
DART 및 EDGAR 공시와 시장 데이터
    -> 비교 가능한 데이터와 근거
    -> Company, Panel, Compare, Scan
    -> Analysis, Credit, Industry, Quant, Macro
    -> Story, Report, Simulate, Ask, Screener
    -> Python, Terminal, CLI, MCP, Notebook
```

이 흐름은 사용자 설명 구조다. 내부 import와 테스트에는 기존 레이어 규율을 계속 사용한다.

## 2. 내부 폴더 역할

| 역할 | 대표 폴더 | 공개 제품 위치 |
|---|---|---|
| 원천과 표준화 | core, providers, gather | Gather는 고급 API, 나머지는 기반 |
| 비교 가능한 프레임과 근거 | frame, synth, reference | 결과의 정합성 및 증거 기반 |
| 횡단 탐색 | company, scan, search | Company, Panel, Scan, Screener |
| 분석 렌즈 | analysis, credit, industry, quant, macro | 다섯 공개 렌즈 |
| 판단 조합 | story, simulate, ai | Story, Report, Simulate, Ask |
| 전달 표면 | server, mcp, viz, ui, landing | Terminal, Python, CLI, MCP, Notebook |

폴더 하나가 곧 독립 제품이라는 규칙은 없다. 폴더는 책임 경계이고 제품은 사용자 질문과 완료된 작업으로 정의한다.

## 3. 공개 제품 구조

### 3.1 시작 제품

사용자가 가장 먼저 접하는 시작점은 세 가지로 제한한다.

1. Company: 한 기업의 비교 가능한 정보와 렌즈 진입점
2. Scan과 Screener: 여러 기업을 조건과 상대 기준으로 선별
3. Ask: 자연어 질문을 Company, Scan, 렌즈 호출로 연결

Python, Terminal, CLI, MCP는 별도 제품 정체성이 아니라 같은 기능을 사용하는 채널이다.

### 3.2 다섯 렌즈 헌장

#### Analysis

대표 질문: 이 회사의 사업, 이익, 현금, 자본배분, 가치와 위험은 어떤 인과로 연결되는가.

대표 결과:

- 사업 및 수익 구조
- 수익성과 성장의 동인
- 이익 품질과 현금 전환
- 재무 안정성과 자본배분
- 가치평가와 시장 가정
- 핵심 위험과 반증 조건
- 상세 축으로 가는 drilldown

상세 축은 대표 결과의 근거와 추가 분석 수단이다. 22개 축을 첫 화면에 병렬 나열하지 않는다.

#### Credit

대표 질문: 이 회사는 현재와 하방 시나리오에서 채무를 감당할 수 있는가.

대표 결과:

- dCR 등급과 추세
- 등급 동인 워터폴
- 레버리지와 이자상환 능력
- 유동성, 현금, 만기
- 하방 시나리오와 등급 민감도
- 외부 등급과의 divergence
- tripwire와 결손

현재 무인자 Company 경험을 기준으로 다른 렌즈의 기본 제품 패턴을 설계한다.

#### Industry

대표 질문: 이 회사는 산업 가치사슬에서 어디에 있고 어떤 구조가 이익과 위험을 결정하는가.

대표 결과:

- 산업과 세부 분류
- 가치사슬 위치
- 제품, 고객, 공급자 관계
- 피어와 비교 근거
- 산업 단계와 profit pool
- 협상력, 집중도, 대체 위험
- 관계 근거의 최신성과 신뢰도

Industry는 독립 렌즈이면서 Analysis, Credit, Quant의 peer와 맥락을 제공하는 기반이다.

#### Quant

대표 질문: 시장가격과 펀더멘털 및 기대 사이에 어떤 불일치가 있는가.

대표 결과:

- 상대수익률과 위험
- 공시 및 실적 이벤트 반응
- 펀더멘털 변화 대비 가격 반응
- 가치, 품질, 모멘텀 등 핵심 팩터 노출
- 유동성 및 이상 신호
- 기대가 반영한 가정
- 판단의 유효 기간과 실패 조건

Quant는 범용 기술적 분석기보다 공시와 가격을 연결하는 DartLab 고유 역할에 집중한다.

#### Macro

대표 질문: 현재 거시환경은 산업을 거쳐 이 회사의 실적, 재무와 가치에 어떻게 전달되는가.

대표 결과:

- 현재 regime과 신뢰도
- 핵심 변수와 방향
- 산업 전달경로
- 매출, 비용, 운전자본, 할인율 영향
- 기업별 민감도
- 위기 및 전환 시나리오
- 데이터 지연, 결손, 반증 조건

Macro는 지표 카탈로그가 아니라 기업 전달경로를 대표 제품으로 삼는다.

## 4. 공통 결과 문법

다섯 렌즈를 하나의 범용 엔진으로 합치지 않는다. 대신 상위 소비자가 안정적으로 이해할 수 있는 공통 결과 문법을 둔다.

개념상 모든 대표 결과는 다음을 포함한다.

| 필드군 | 의미 |
|---|---|
| identity | target, market, engine, version |
| time | asOf, dataAsOf, period, knowledge boundary |
| status | usable, partial, blocked, notApplicable |
| conclusion | 렌즈의 대표 판단 |
| confidence | 판단 신뢰도와 산출 근거 |
| drivers | 결론을 만든 주요 동인 |
| evidence | sourceRef, valueRef, tableRef, 실행 근거 |
| assumptions | 추정과 가정, 적용 범위 |
| gaps | missing, blocked, stale, unsupported |
| scenarios | 조건 변화에 따른 결과 범위 |
| falsifiers | 결론을 깨는 조건과 tripwire |
| payload | 렌즈별 고유 결과 |

이 표는 구현 클래스나 새 공개 API 이름을 확정하지 않는다. 구현 착수 시 기존 결과 타입과 report contract를 먼저 재사용하고 새 SSOT 생성 여부를 별도 판정한다.

## 5. 조합 규칙

### Story와 Report

- 렌즈 결과를 다시 계산하지 않는다.
- 같은 target, asOf, dataAsOf 문맥을 유지한다.
- 렌즈 간 일치와 충돌을 논지로 조립한다.
- 결론마다 evidence와 falsifier를 보존한다.
- 11개 유형과 7개 템플릿 확장보다 대표 보고서 하나를 먼저 마감한다.

### Simulate

- Analysis의 사업 및 손익 동인, Credit의 하방 제약, Macro의 외생 경로, Quant의 시장 반응을 입력으로 사용한다.
- fact, estimate, hypothesis, scenario를 분리한다.
- 결과는 조건부 범위로 제시한다.
- 하위 렌즈와 별도의 사실 체계를 만들지 않는다.

### Ask

- 질문을 렌즈 또는 비교 작업으로 routing한다.
- 답을 직접 발명하기보다 구조화된 결과를 설명한다.
- 원문과 계산 근거로 돌아갈 수 있어야 한다.
- 답할 수 없는 경우 필요한 데이터와 차단 이유를 노출한다.

### Screener

- Scan의 선언형 spec과 동일한 의미를 소비한다.
- 렌즈의 대표 결과나 안정된 공개 필드만 조건으로 사용한다.
- UI와 Python이 동일한 screen 정의를 재구현하지 않는다.

## 6. API 전환 원칙

### 현재 호환 유지

- 기존 축 호출을 삭제하거나 이름을 즉시 바꾸지 않는다.
- 루트 facade와 Company 호출 계약을 구현 착수 없이 변경하지 않는다.
- 무인자 가이드 반환은 호환 기간 동안 유지한다.

### 제품 진입 개선

- README와 Terminal은 대표 질문과 대표 결과를 먼저 제시한다.
- 기존 축 중 종합 성격의 검증된 경로를 대표 진입으로 우선 사용한다.
- 적합한 기존 경로가 없을 때만 최소 공개 계약 추가를 검토한다.
- 무인자 기본값 변경은 실제 사용 자료, deprecation, 주요 버전 경계를 갖춘 뒤 결정한다.

### typed API

명시적 typed API는 장기적인 안정 경로 후보로 유지한다. callable-module 편의 API의 은퇴 여부는 대표 제품 계약이 안정된 후 별도 계획에서 결정한다.

## 7. 내부 아키텍처 불변조건

1. 기존 레이어별 import 방향을 유지한다.
2. L2 형제 엔진이 서로의 비공개 구현을 직접 소비하지 않는다.
3. 상위 조합은 공개 결과 또는 승인된 중립 계약을 사용한다.
4. sourceRef, asOf, dataAsOf, missing을 조합 과정에서 잃지 않는다.
5. public과 local 실행이 서로 다른 의미 계산을 만들지 않는다.
6. UI가 Python 엔진 의미를 재구현하지 않는다.
7. 동적 import로 구조 규칙을 우회하는 신규 부채를 만들지 않는다.
8. 엔진별 고유 schema를 공통 envelope 때문에 평탄화하지 않는다.

## 8. 제품 성숙도 단계

| 단계 | 정의 |
|---|---|
| M0 | 축과 코드가 존재함 |
| M1 | 공개 호출 가능하고 단위 테스트가 있음 |
| M2 | 상태, 시점, 증거, 결손을 포함한 의미 계약이 있음 |
| M3 | 축 지식 없이 대표 사용자 질문을 완료함 |
| M4 | Python, Terminal, Ask에서 동일 의미로 재현되고 저장 및 내보내기 가능 |
| M5 | 기준 기업 검증, calibration 또는 backtest, 실제 반복 사용 자료가 있음 |

새 축을 추가하기 전에 해당 렌즈의 대표 제품이 최소 M3인지 확인한다.

