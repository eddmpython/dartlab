---
id: engines.story
title: Story (보고서 빌더)
kind: curated
scope: builtin
status: observed
category: engines
purpose: Story 는 6 막 인과 구조의 회사 보고서를 조립하는 **L3 조합기**다. 분석엔진 X. 다섯 공개 렌즈 (analysis · credit · industry · quant · macro) 의 대표 product와 scan 근거를 독립 상태로 모아 11 reportType × 7 기업유형 템플릿에 배치한다. 자체 계산과 통합점수는 0, 모든 숫자와 렌즈 결론은 하위 엔진 ref. 트리거는 '보고서', '기업 이야기', 'story', '6 막 인과'.
whenToUse:
  - Story
  - story
  - 보고서 생성
  - 6 막 인과
  - 기업 종합 분석
  - reportType
  - scorecard
  - creditScore
  - narrative 블록
inputs:
  - 종목코드 또는 Company
  - reportType (선택 - full · executive · credit · valuation · ...)
  - 자유 조립 시 Block 리스트
outputs:
  - Story 인스턴스 (sections · summaryCard)
  - 렌즈별 대표 product 원문 (lensProducts)
  - 렌즈 호출 또는 계약 결손 (lensGaps)
  - render 출력 (rich · html · markdown · json)
  - block list (scorecard · creditScore · narrative · valuationBand · ...)
capabilityRefs:
  - Story
  - Company.story
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.company
  - engines.analysis
  - engines.credit
  - engines.macro
sourceRefs:
  - dartlab://skills/engines.story
requiredEvidence:
  - target
  - reportType
  - sections
  - tableRef
  - executionRef
  - sourceRef
expectedOutputs:
  - 6 막 구조 보고서
  - block 별 evidence 묶음
  - thesis · evidenceBlocks · riskBlocks · limits
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
failureModes:
  - 하위 엔진 (analysis · credit) 결과 ref 없이 narrative 만 생성
  - reportType 미지정 + 기업유형 자동 감지 실패 시 fallback 없음
  - block 자유 조립 시 evidence 없는 빈 섹션 발급
  - story 가 직접 숫자 계산 - 모든 숫자는 하위 엔진 결과 ref 에 묶어야
forbidden:
  - story 에서 직접 숫자 계산 또는 추정 금지 - 하위 엔진 결과만 인용.
  - 다섯 렌즈를 하나의 종합점수나 단일 등급으로 합산 금지.
  - thesis · risk 문장에 source ref 없이 단정 금지.
  - 옛 단일 reportType (`thesis`) 으로 새 보고서 생성 금지 - 명시 reportType 또는 자동 감지.
examples:
  - 005930 전체 보고서
  - 신용분석 전용 보고서 (reportType="credit")
  - 5 영역 scorecard A~F 평가
  - 20 등급 신용평가 함께 보기
  - 자유 블록 조립 (Story([blocks]))
procedure:
  - dartlab.Company(code).story() 가 가장 단순한 진입 - 자동 reportType + 기업유형 감지.
  - 명시 호출은 c.story(reportType="credit") 또는 c.story(section_name).
  - 자유 조립은 from dartlab.story import blocks, Story; b = blocks(c); Story([b["growth"], b["margin"]]).
  - 출력 형식 - story.render("markdown") / toHtml() / toMarkdown().
  - 하위 엔진 (analysis · credit · macro · industry) 결과의 ref 가 자동 묶임.
linkedSkills:
  - engines.company
  - engines.analysis
  - engines.credit
  - engines.macro
  - engines.industry
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-05-08'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 엔진 역할

`story` 는 *해석하지 않고 다양한 관점의 근거를 배치* 하는 **L3 조합기**다. 분석엔진 X. L2 5 분석엔진 - analysis (재무 인과) · credit (신용 위험) · macro (시장 환경) · quant (정량 신호) · industry (밸류체인 위치) - 와 L1.5 scan (횡단 비교) 결과를 블록 단위로 조합해 6 막 구조 보고서를 만든다.

### story 가 L3 조합기인 이유 - 순환참조 방지

L2 5 분석엔진은 도메인 격리 (analysis ⊥ credit ⊥ macro ⊥ quant ⊥ industry) 가 import 단방향으로 강제돼 있다. L2 끼리 직접 import 하면 순환참조가 생긴다. 이 결합 책임을 story 가 단독으로 짊어져 6 막 보고서로 직조한다 - 자체 숫자 계산 0, 모든 숫자는 하위 엔진 결과 ref 에 묶이고, story 자체는 *thesis · evidence · risk · limit* 의 문장 골격만 제공.

이 구조 덕분에 새 L2 분석엔진을 추가해도 기존 L2 엔진은 수정 0 - story 의 블록 등록만 늘어난다.

## 공개 호출 방식

```python
import dartlab

# 1. Company-bound - 가장 단순한 진입점
c = dartlab.Company("005930")
story = c.story()                          # 자동 reportType + 기업유형 감지
print(story.render("markdown"))

# 2. reportType 명시
credit_report = c.story(reportType="credit")
valuation = c.story(reportType="valuation")
exec_brief = c.story(reportType="executive")

# 3. 단일 섹션
revenue = c.story("수익구조")               # 수익구조 블록만

# 4. 자유 조립 (블록 단위)
from dartlab.story import blocks, Story
b = blocks(c)
custom = Story([b["growth"], b["margin"], b["cashflow"]])

# 5. 출력 형식 변환
print(custom.toMarkdown())
print(custom.toHtml())
print(custom.render("rich"))               # 터미널 색상
print(custom.render("json"))               # AI 소비용
```

## 강행 호출 룰 (agent 답변 품질 회귀 차단)

story 는 L3 조합기 - *자체 계산 0*. 모든 숫자는 하위 엔진 (analysis/credit/macro/quant/industry/scan) ref 인용으로 들어와야 함.

1. **story 본문 안 모든 숫자에 하위 엔진 ref inline 표기 필수** - `[tableRef:...]`/`[valueRef:...]` 형식. ref 없는 숫자는 story 본문 진입 차단.
2. **story 안에서 직접 계산 금지** - RunPython 으로 ratio/forecast/score 산출 금지. 하위 엔진 호출 결과의 `items`/`flags`/`assumptions` 그대로 차용.
3. **블록 evidence 부족 시 빈 섹션 + `limits` 에 명시** - 임의로 채우거나 환각 금지. story 의 spec 가 "evidence 비면 빈 섹션" 정공.
4. **reportType 미명시 시 자동 감지 결과 본문에 노출** - "자동 선택: `executive` (이유: ...)" 한 줄.
5. **같은 `(stockCode, period)` 분기 데이터는 1 회 fetch 후 in-memory 재사용** - 같은 회사 같은 기간의 EngineCall 을 axis 만 바꿔 반복 호출 금지. story 가 L3 조합기로서 차입금·충당부채·부문정보 등 여러 블록을 만들 때, Company.panel 한 번으로 모든 stmt (BS/IS/CF) + 분기 시계열을 받아 in-memory 분기 후 각 블록에 분배한다. 회귀 사례 - Q3 hybrid 답변 137s + RSS 7.6GB 폭증 (같은 005930 분기 데이터 차입금/충당부채/부문정보 4 회 반복 load). CLAUDE.md 메모리 안전 강행규칙 (Company 1 개 ≈ 200~500MB) 직결.

## 호출 동작

`Company.story()` (인자 없음) → 자동 reportType 선택 + 기업유형 자동 감지 (template). reportType 후보: `full` · `executive` · `credit` · `valuation` · `governance` · `forecast` · `risk` 외 11 종.

기업유형 template: 일반 · 금융 · 지주 · 신생/성장 · 사이클 · 자원 · 플랫폼 7 종. analysis 의 `companyType` 함수로 판정.

`Story` 클래스 자체를 호출하면 `Story(itemsOrStockCode, *, stockCode=, corpName=, sections=, layout=)` - 자유 조립 또는 직접 종목코드. `dartlab.story` 가 클래스 자체이므로 *함수처럼 호출하지 않는다* (`dartlab.story(c)` 같은 호출은 `Story(c)` 가 되어 첫 인자 타입이 안 맞음).

블록 한 개의 evidence 가 비면 빈 섹션이 그대로 나간다 - story 는 채워주지 않음. 하위 엔진 호출 결과 부족 시 해당 블록 skip 또는 limits 에 명시.

## 2 축 체계 - reportType × template

```
reportType   (집중 시점)              template     (기업 유형 자동 감지)
────────────────────────────         ────────────────────────────────
full          종합                   일반          제조/서비스
executive     경영 요약              금융          은행/보험/카드
credit        신용 위험              지주          비순환 출자
valuation     적정가                 신생/성장     상장 5 년 이내
governance    지배구조               사이클        반도체/조선
forecast      매출 전망              자원          정유/철강/유틸
risk          리스크 점검            플랫폼        IT 서비스
disclosure    공시 변화
peer          peer 비교
sector        섹터 위치
custom        자유 조립
```

reportType × template = block list 결정. 각 block 은 하위 엔진 (analysis · credit · macro · industry · scan · quant) 호출 결과 ref 를 인용.

## 대표 반환 형태

```text
Story 인스턴스
   sections : list[Section]      # 6 막별 섹션
   summaryCard : SummaryCard     # 최상단 요약 (grade · 핵심 metrics)
   lensProducts : dict           # reportType에 필요한 렌즈별 product 원문
   lensGaps : list[dict]         # 호출 실패 또는 product 계약 결손
   reportType : str              # 선택된 보고서 관점
   render(fmt) : str             # "rich" / "html" / "markdown" / "json"
   toHtml() : str
   toMarkdown() : str
```

```text
section dict
   thesis : str                  # 한국어 인과 문장 (analysis narrative 인용)
   evidenceBlocks : list[dict]   # tableRef / valueRef / dateRef
   riskBlocks : list[dict]       # 리스크 요인 + ref
   limits : list[str]            # 데이터 부족 · 가정 한계
   sourceRefs : list[str]        # dartlab://... 출처
```

## evidence 기준

story 답변은 `target` · `reportType` · `template` · 모든 block 의 `tableRef` / `valueRef` 를 남긴다. evidence 없는 thesis 문장은 *허용 안 됨* - block 자체를 skip 또는 limits 에 명시.

## docstring ↔ story 환류

엔진 docstring 의 Guide 섹션이 audit 통과 → story 블록 템플릿에 반영 (같은 해석 규칙 · 같은 임계값). 반대로 story 블록 중 재현 가능 + 해석 규칙 명확한 것 → 공개 함수로 추출해 엔진 docstring Guide 로 명시. AI · story 공용 호출.

## ask 모드 5 단 답변 양식과 story block 의 매핑

대화형 ask (chat-native) 답변은 LLM 이 `Company.story()` 호출 없이 5 단 구조로 직접 작성하는 경우가 대부분. 그 5 단이 story block 의 단축형:

| ask 5 단 | story block 대응 | evidence |
| --- | --- | --- |
| 0. 헤더 chip (`📊 dCR · 🏭 산업·단계 · 📅 dataAsOf`) | `summaryCard` (grade · phase · asOf) | `dcrBadge` · `industryBadge` (auto-attach) |
| 1. 결론 (1 문장 정량) | `thesis` | valueRef · dateRef |
| 2. 핵심 근거 (표·시계열) | `evidenceBlocks` | tableRef · valueRef |
| 3. 메커니즘 (mermaid · 인과 chain) | `narrative` | 하위 엔진 결과 ref |
| 4. 반례·한계 | `riskBlocks` · `limits` | scenario ref · flags |
| 5. 후속 모니터링 (정량 임계) | `nextSignals` | 지표명 + 임계값 + 방향 |

호출 `Company.story()` 는 종합 보고서 / landing 페이지 / 자유 조립 시 사용. 단일 질문 답변은 LLM 자체 작성 + 본 양식 박혀있으면 충분.

## 기본 실행 순서

1. **ask 모드 단일 답변** - LLM 이 5 단 양식 직접 작성. Company.panel + 자동 부착 badge 인용. story() 호출 불필요.
2. **종합 보고서 / landing 페이지** - `Company(code).story()` 자동 reportType.
3. 신용 / 가치평가 / 거버넌스 등 집중 시점이면 `reportType=` 명시.
4. 자유 조립은 `blocks(c)` 로 block dict 받고 `Story([...])`.
5. 출력 형식 - markdown (텍스트 응답), html (landing 임베드), json (후속 처리).

## 기본 검증

`Story` 클래스 시그니처 · 11 reportType · 7 template · block list 가 바뀌면 본 skill + analysis · credit 응용 skill 동시 갱신. block 추가 시 evidence 묶음 helper (`tableRef` · `valueRef`) 계약 동기.


---

# 흡수된 sub-spec 본문 (Phase D, 2026-05-18)

## (흡수) engines.story.companyCausal 본문

## 절차

- 기업 식별과 사용 가능한 Company topic을 확인한다.
- macro, scan 또는 industry 맥락이 필요한지 reference에서 확인한다.
- Company.analysis와 원본 panel 결과를 실행해 수치 근거를 만든다.
- 판단 claim은 대상, 기간, metric, value ref에 묶는다.

## 공개 호출 방식

- `c = dartlab.Company("005930")`
- `c.story()`
- `dartlab.story(c)`

## 호출 동작

- analysis, credit, macro, scan, quant 결과를 thesis/evidence/risk/limit 구조로 조립한다. 숫자 계산은 하위 엔진 결과 ref에 묶는다.
- 실행 전에 target, period/date, metric, source 또는 universe를 확인한다.
- 데이터가 없거나 runtime 제한이 있으면 값을 추정하지 않고 한계와 필요한 다음 수집 경로를 말한다.

## 대표 반환 형태

- report dict 또는 block list를 반환한다. 핵심 키는 thesis, evidenceBlocks, riskBlocks, limits, sourceRefs다.
- 전체 세부 필드는 공개 docstring/capability와 동기화한다. 코드/API 변경으로 이 설명이 오래되면 skill 갱신 누락으로 본다.

## 기본 검증

- 실행 결과는 tableRef, valueRef, dateRef, executionRef 중 필요한 근거로 남긴다.
- 최종 판단의 숫자 claim은 해당 table/value ref에 직접 묶는다.
- 스킬과 실제 공개 API의 호출 방식, 대표 반환 형태, 오류/제한 동작이 다르면 같은 변경에서 스킬을 갱신한다.

## (흡수) engines.story.dartlabStory 본문

## 절차

- story capability가 제공하는 report type과 한계를 확인한다.
- 필요한 하위 엔진 근거를 실행 결과로 확보한다.
- narrative는 숫자/날짜 claim ref를 가진 상태에서만 작성한다.

## 공개 호출 방식

- `c = dartlab.Company("005930")`
- `c.story()`
- `dartlab.story(c)`

## 호출 동작

- analysis, credit, macro, scan, quant 결과를 thesis/evidence/risk/limit 구조로 조립한다. 숫자 계산은 하위 엔진 결과 ref에 묶는다.
- 실행 전에 target, period/date, metric, source 또는 universe를 확인한다.
- 데이터가 없거나 runtime 제한이 있으면 값을 추정하지 않고 한계와 필요한 다음 수집 경로를 말한다.

## 대표 반환 형태

- report dict 또는 block list를 반환한다. 핵심 키는 thesis, evidenceBlocks, riskBlocks, limits, sourceRefs다.
- 전체 세부 필드는 공개 docstring/capability와 동기화한다. 코드/API 변경으로 이 설명이 오래되면 skill 갱신 누락으로 본다.

## 기본 검증

- 실행 결과는 tableRef, valueRef, dateRef, executionRef 중 필요한 근거로 남긴다.
- 최종 판단의 숫자 claim은 해당 table/value ref에 직접 묶는다.
- 스킬과 실제 공개 API의 호출 방식, 대표 반환 형태, 오류/제한 동작이 다르면 같은 변경에서 스킬을 갱신한다.
