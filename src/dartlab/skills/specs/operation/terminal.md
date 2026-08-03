---
id: operation.terminal
title: 터미널 사상 — 전문가 분석 계기판 (instrument, not document)
kind: curated
scope: builtin
status: observed
category: operation
purpose: DartLab 터미널(퍼블릭·로컬)의 기본 개념과 설계 사상 SSOT. 터미널은 전문가가 한눈에 읽는 살아있는 분석 계기판이며, 문서·리포트·뉴스판이 아니다. 터미널 surface 를 만들거나 평가할 때 기준으로 쓴다.
whenToUse:
  - 터미널
  - terminal
  - 퍼블릭 터미널 / 로컬 터미널
  - 매크로 렌즈 / 대시보드 / 패널 시각 설계
  - instrument vs document
  - 화면이 분석 계기판인지 판단
  - 시각화 채택 여부
inputs:
  - 작업 대상 surface (패널·다이얼로그·렌즈)
  - 실행 환경 (퍼블릭 / 로컬)
  - 시각화 후보
outputs:
  - 계기판 적합성 판단
  - 퍼블릭 바닥 호환 여부
  - 시각화 채택/제거 결정
procedure:
  - 이 화면이 읽는 계기인지, 해석할 문서인지 분류한다.
  - 퍼블릭 바닥(HF SSOT + 브라우저 연산, 로컬 백엔드 없음)에서 도는지 확인한다.
  - 판정 없음을 텍스트 축약이 아니라 시각(곡선·분포·국면·증거상태)으로 구현했는지 본다.
  - 각 시각화가 "무엇이 움직였나→어느 채널→증거상태→언제 다시 보나"를 강화하는지 게이트한다.
  - 완성 판정 전 실제 렌더 화면을 직접 확인한다.
examples:
  - 매크로 렌즈를 텍스트 카드가 아니라 시각 계기판으로 설계
  - 퍼블릭 터미널이 로컬 서버 없이 완전히 도는지 검증
  - 장식 스파크라인(축·기간 없음)을 제거할지 판단
expectedOutputs:
  - 계기판/문서 분류 결과
  - 퍼블릭-우선 호환 판단
  - 시각화 채택 게이트 통과 여부
requiredEvidence:
  - 대상 surface 경로
  - 실행 환경 (퍼블릭/로컬)
  - 렌더 확인 근거
failureModes:
  - 텍스트 카드 + 장식 스파크라인을 계기판으로 착각
  - 판정 없음을 시각 축소(체크리스트화)로 구현
  - 로컬 연산이 있어야 계기처럼 보이는 패널을 퍼블릭에 출시
  - 화면을 렌더해 보지 않고 완성 처리
forbidden:
  - 근거(축·기간·출처·모델 한계)를 숨기는 gauge·donut·단일 점수·출처 없는 heatmap·분포 없는 fan chart
  - 분석 방향을 색으로 단정 (색은 증거/데이터 상태 전용)
  - 매수·매도·수혜·피해 판정 노출
knowledgeRefs:
  - operation.philosophy
  - operation.ui
  - operation.dashboardDesign
sourceRefs:
  - dartlab://skills/operation.terminal
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
    notes: []
capabilityRefs: []
lastUpdated: '2026-06-21'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 터미널이란 — 계기판이지 문서가 아니다

DartLab 터미널은 전문가가 하루 종일 들여다보는 *살아있는 분석 계기판(instrument)* 이다. 블룸버그·아이코 같은 금융 터미널의 본질은 *읽고 덮는 리포트* 가 아니라, 분석을 시각 원시형(차트·곡선·플롯·게이지)으로 압축해 몇 초 안에 위치를 읽게 하는 계기판이다. 따라서 터미널 surface 의 정답은 긴 텍스트가 아니다. 표와 산문은 계기를 받치는 비계(scaffold)이지 제품의 본체가 아니다.

실패형은 명확하다 — 텍스트 카드의 나열 + 축도 기간도 없는 장식 스파크라인으로 채운 "정렬된 문서". 이것은 매크로 뉴스판이지 분석 계기판이 아니다.

## 5 원칙

1. **계기판 ≠ 문서.** 각 패널은 *읽는* 차트·곡선·플롯이지 *해석할* 문단이 아니다. 분석을 시각으로 압축한다.
2. **밀도 + 속도 (전문가용).** 한눈에 위치를 읽는다. 정보 밀도는 높되 시각 *위계* 로 정렬한다(균일 카드 금지). 초보 온보딩이 아니라 반복 전문 사용 기준으로 설계한다.
3. **판정하지 않고 시각으로 보여준다.** 판정·점수·매수/매도를 내지 않는 원칙은, 곡선·국면·분포·증거상태를 *그려서 보여주고* 전문가가 판단하게 함으로 달성한다. 이는 시각의 축소가 아니다 — 시각을 체크리스트로 깎는 것은 판정 회피가 아니라 분석의 포기다.
4. **퍼블릭 바닥 = 로컬 상위집합.** 아래 별도 절.
5. **시각화는 자격을 증명해야 한다.** 아래 별도 절.

## 퍼블릭 바닥 = 로컬 상위집합

터미널은 두 타깃(퍼블릭·로컬)이 같은 계기다.

- **퍼블릭 터미널** = 모두가 받는 바닥(floor). HF=SSOT 공개 데이터 + 브라우저 연산만으로 *로컬 백엔드 없이* 완전히 돈다. 개발 기준(dev)도 퍼블릭이다.
- **로컬 터미널** = 같은 계기에 무거운/실시간/AI 연산을 로컬 전용 게이트(`/api`) 뒤에 더 얹는 상위집합(superset)이다.

두 타깃의 **계기 질·시각 수준은 동일** 하며, 설계는 퍼블릭-우선이다. 로컬 연산이 있어야만 계기처럼 보이는 패널은 퍼블릭 바닥을 통과하지 못한 것이다. 데이터층 배선 규칙(단일 작업대 SSOT, 오리진 레지스트리, 로컬 전용 게이트)은 [operation.ui](/skills/operation.ui) 가 SSOT 다.

## 판정하지 않고 시각으로

색은 분석 방향이 아니라 증거/데이터 상태를 나타낸다. 곡선·분포·국면 평면은 근거(축·기간·출처·모델 한계)를 함께 노출한 채로 보여주고, 결론은 사용자가 낸다. 매수/매도·수혜/피해·좋음/나쁨·단일 macro score 는 방향·확신·품질을 뒤섞으므로 쓰지 않는다. 이 원칙은 [operation.philosophy](/skills/operation.philosophy) 의 설계 사상과 일치하며, 화면을 *덜 시각적으로* 만들라는 뜻이 결코 아니다.

## 시각화 채택 게이트

시각화는 다음을 강화할 때만 채택한다.

```text
무엇이 움직였나  →  어느 재무 채널에 닿나  →  증거가 관측/prior/템플릿/잠금인가  →  언제 다시 확인하나
```

이 체인 중 하나를 강화하지 못하는 차트는 장식이므로 제거한다.

- **축·기간 없는 스파크라인 = 장식** (금지).
- gauge·donut·단일 점수·출처 없는 heatmap·모델 분포 없는 fan chart = 근거를 숨기므로 금지.
- 시각 문법과 금지 목록, 카드 배치, bento, 위계는 [operation.dashboardDesign](/skills/operation.dashboardDesign)을 따른다.

## 완성 판정

터미널/공유 surface 의 완성 판정에는 "이 화면이 퍼블릭 바닥에서 도는 분석 계기판인가"를 *실제 렌더 화면으로 직접 확인* 하는 단계를 포함한다. 타입 검사·구조 검사·텍스트 스캔은 시각·레이아웃을 보지 못한다(장식 스파크라인, grid 붕괴, 빈 렌더가 모두 통과한다). 픽셀을 확인하기 전에는 완성으로 처리하지 않는다.

## 다음 단계

- [operation.ui](/skills/operation.ui) — UI 표현 계층 + 데이터층 단일 작업대 SSOT.
- [operation.dashboardDesign](/skills/operation.dashboardDesign) — 카드 배치·bento·시각 위계·Playwright 검수 루프.
- [operation.philosophy](/skills/operation.philosophy) — 설계 사상 정점 SSOT.
