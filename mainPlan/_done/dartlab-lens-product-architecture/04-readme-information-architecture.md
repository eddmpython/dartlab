# 04. README 제품 정보구조

## 1. 목표

README의 첫 독자가 내부 레이어, 패키지 역사, 모든 축을 배우지 않고도 다음 세 가지를 이해하게 한다.

1. DartLab이 어떤 문제를 해결하는가.
2. 어떤 대표 작업을 바로 수행할 수 있는가.
3. 더 깊은 분석과 아키텍처 문서는 어디에 있는가.

README는 제품 입구다. 내부 구조의 완전한 설명서는 별도 architecture 문서와 Skill OS가 담당한다.

## 2. 첫 문장

권장 문장:

> DartLab은 DART와 EDGAR 공시를 비교 가능한 기업 데이터로 바꾸고, 다섯 개의 분석 렌즈로 근거 있는 기업 판단을 만드는 오픈소스 리서치 시스템입니다.

보조 문장:

> Company와 Scan으로 데이터를 탐색하고, Analysis, Credit, Industry, Quant, Macro로 해석하며, Story, Simulate, Ask로 조사 결과를 조합합니다.

## 3. 목표 목차

### 1. Hero

- 한 문장 정의
- 설치 명령
- 60초 안에 실행할 대표 예제 하나
- Terminal과 Python 중 두 진입점

### 2. 60초 조사 흐름

예제는 여러 축을 나열하지 않는다.

1. Company 열기
2. 핵심 panel 확인
3. 대표 Analysis 결과 확인
4. Credit 또는 Industry drilldown
5. 여러 기업이면 Scan 실행

### 3. DartLab이 작동하는 방식

```text
공시 -> 비교 가능한 데이터 -> 다섯 렌즈 -> 판단 워크플로
```

각 단계는 구현 레이어가 아니라 사용자에게 주는 가치를 한 문단으로 설명한다.

### 4. 비교 가능한 기업 데이터

- DART와 EDGAR
- Company와 panel
- compare
- Scan과 Screener
- 데이터 기준시점과 근거

### 5. 다섯 분석 렌즈

각 렌즈마다 같은 형식을 사용한다.

- 답하는 질문 한 문장
- 대표 결과 이미지 또는 짧은 표
- 대표 호출 하나
- 세부 축 문서 링크

렌즈 순서는 다음으로 고정한다.

1. Analysis
2. Credit
3. Industry
4. Quant
5. Macro

### 6. 판단 워크플로

- Story와 Report
- Simulate
- Ask
- Screener 저장 및 감시

이 절은 새로운 사실 엔진이 아니라 다섯 렌즈를 조합한다는 점을 명시한다.

### 7. 사용하는 방법

- Python
- Terminal
- CLI
- MCP
- Notebook

채널별로 제품 설명을 반복하지 않고 같은 작업을 어떻게 실행하는지만 설명한다.

### 8. 증거와 데이터 한계

- sourceRef
- asOf와 dataAsOf
- DART와 EDGAR 범위 차이
- missing과 blocked
- 모델 및 시뮬레이션의 조건부 성격

### 9. 고급 문서

- API reference
- 데이터 구조
- 내부 architecture와 레이어
- Skill OS
- 기여와 테스트

## 4. 이동할 내용

| 현재 README 내용 | 새 위치 |
|---|---|
| L0, L1, L1.5, L2, L3, L4 설명 | 고급 architecture 문서 |
| Story가 순환 참조를 막는 이유 | operation.architecture 또는 개발자 문서 |
| 모든 축의 긴 목록 | 엔진별 reference와 guide |
| 세 채널에서 반복되는 같은 기능 설명 | 사용하는 방법 절의 짧은 예제 |
| 상세 데이터 빌드 및 배포 설명 | data 및 contributor 문서 |
| Skill OS 전체 설명 | 개발자 절과 링크 |

삭제가 아니라 적절한 독자와 문서로 이동한다.

## 5. 제품 명칭 규칙

### README에서 사용할 명칭

- 비교 가능한 데이터
- Company와 Panel
- Scan과 Screener
- 다섯 분석 렌즈
- Story, Simulate, Ask
- Python, Terminal, CLI, MCP, Notebook

### README 전면에서 사용하지 않을 명칭

- L0, L1, L1.5, L2, L2.5, L3, L4
- 내부 import 방향
- 엔진 폴더 mirror 규칙
- 동적 import debt
- facade callable-module 구현

이 용어들은 내부 문서에서 계속 사용한다.

## 6. 렌즈 소개 템플릿

```text
### Credit

이 회사는 빚을 감당할 수 있는가?

DartLab Credit은 등급만 보여주지 않고 등급 동인, 유동성,
만기, 하방 시나리오와 등급을 깨는 조건을 함께 보여줍니다.

[대표 호출]
[대표 결과]
[상세 축 보기]
```

다른 렌즈도 동일한 길이와 구조를 사용한다. 기능 수가 많은 엔진이 더 긴 소개를 차지하지 않는다.

## 7. README 완료 게이트

1. 첫 화면에서 제품 한 문장을 이해할 수 있다.
2. 첫 실행까지 내부 레이어 지식이 필요하지 않다.
3. 다섯 렌즈가 동일한 제품군으로 보인다.
4. 각 렌즈가 기능 목록이 아니라 질문과 결과로 설명된다.
5. Story, Simulate, Ask가 렌즈 조합임을 이해할 수 있다.
6. 데이터 근거, 시점, 한계가 숨겨지지 않는다.
7. 고급 사용자가 architecture와 전체 API 문서로 이동할 수 있다.
8. 기존 공개 호출 예제가 실제 실행 및 product smoke와 일치한다.

## 8. 권장 분량

메인 README는 약 300줄에서 400줄을 목표로 한다. 줄 수 자체를 게이트로 사용하지는 않지만, 동일 기능을 채널별로 반복하거나 내부 구조를 본문에 중복 설명하지 않는다.

