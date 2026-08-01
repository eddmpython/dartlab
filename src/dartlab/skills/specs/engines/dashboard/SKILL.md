---
id: engines.dashboard
title: Dashboard (회사 종합 스냅샷)
kind: curated
scope: builtin
status: observed
category: engines
purpose: Dashboard 는 단일 회사를 한 페이지에 종합 시각화하는 *프론트엔드 SvelteKit 페이지* 다. python capability 가 아니라 landing 의 `/company/[code]` 라우트 — 빌드 시점에 5-tier 데이터 (finance · ratios · grades · ecosystem · narrative) 를 조합. 트리거 — '회사 페이지', '대시보드', 'dashboard'.
whenToUse:
  - dashboard
  - 대시보드
  - 회사 페이지
  - 종합 스냅샷
  - radar 차트
  - Altman Z
  - Beneish M
  - landing 빌드
inputs:
  - 종목코드
  - 빌드 시점 데이터 snapshot (finance · report · docs)
  - 5-tier tier 정의
outputs:
  - landing/static/company/{code}/*.json
  - 클라이언트 런타임 계산 (assembleCompany.ts)
  - SSR 페이지
capabilityRefs:
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.company
  - engines.analysis
  - engines.viz
sourceRefs:
  - dartlab://skills/engines.dashboard
requiredEvidence:
  - target
  - period
  - tableRef
  - dateRef
  - executionRef
  - sourceRef
expectedOutputs:
  - 회사 종합 페이지 (URL `/company/{code}`)
  - radar · Altman Z · Beneish M · ecosystem 위젯
  - 5-tier 데이터 bundle
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: limited
  webAi:
    status: limited
  pyodide:
    status: limited
failureModes:
  - python capability `c.dashboard()` 또는 `c.panel("dashboard")` 가 있다고 오해 (없음 — 프론트 페이지)
  - 빌드 산출물 (`landing/static/company/{code}/*.json`) 직접 인용 시 빌드 시점 dateRef 누락
  - radar grade 1-5 스케일 vs A-F 라벨 혼동
  - Altman Z 공식 항을 추측 (실제: 1.2A + 1.4B + 3.3C + 0.6D + 1.0E)
forbidden:
  - python `Company.dashboard()` 같은 존재하지 않는 capability 호출 안내 금지.
  - 빌드 산출 데이터에 기준일 없이 *현재* 로 답변 금지.
  - 5-tier 정의 또는 radar 축 가중치를 추측해 답변 금지 (운영자 정의 SSOT).
examples:
  - 005930 회사 페이지 빌드
  - radar 5 축 (grades A-F → 1-5)
  - Altman Z + Beneish M 위젯
  - ecosystem.links HHI + Top-N suppliers
  - landing 회사 페이지 SSR
procedure:
  - python 진입점은 `Company.view(port=8400)` — 브라우저 뷰어. 데이터 직접 호출 아님.
  - landing 빌드 산출물 위치는 `landing/static/company/{code}/*.json` — finance/ratios/grades/ecosystem/narrative tier.
  - 클라이언트 조합은 `landing/src/lib/company/assembleCompany.ts` 가 5-tier JSON 을 런타임 합성.
  - 빌드 명령 — `cd landing; npm run build`. CI matrix 로 종목 분산.
  - 데이터 갱신은 `scripts/build/buildCompanyTier{N}.py` (운영자 절차).
linkedSkills:
  - engines.company
  - engines.analysis
  - engines.viz
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

Dashboard 는 *프론트엔드 SvelteKit 페이지* 다. python API 가 아니다 — 회사 종합 스냅샷을 한 화면에 보여주는 landing 의 `/company/[code]` 라우트가 본체. python 측에서 실행할 일은 `Company.view(port=8400)` 으로 브라우저 뷰어를 켜거나, 빌드 파이프라인을 운영자 절차로 돌리는 것.

5-tier 데이터 구조:

| tier | 내용 | 빌드 스크립트 |
| --- | --- | --- |
| finance | BS · IS · CF · 비율 | `buildCompanyTier1.py` |
| ratios | 재무비율 + 등급 (A-F) | `buildCompanyTier2.py` |
| grades | radar 5 축 (1-5 스케일) + Altman Z + Beneish M | `buildCompanyTier3.py` |
| ecosystem | 공급망 links + HHI + Top-N | `buildCompanyTier4.py` |
| narrative | 한국어 인과 문장 (story 블록) | `buildCompanyTier5.py` |

클라이언트는 `assembleCompany.ts` 가 위 5 tier JSON 을 런타임에 합성해 페이지를 그린다.

## 공개 호출 방식

```python
import dartlab

# dashboard 는 python API 가 아니다. 공개 호출 계약도 아니다.
# 같은 데이터를 계약 호출로 직접 얻는다.
c = dartlab.Company("005930")
c.panel("IS")
c.analysis("financial", "종합평가")
```

```bash
# landing 빌드 (회사 페이지 SSR 포함)
cd landing
npm run build

# 회사 tier 데이터 갱신 (운영자 절차)
uv run python -X utf8 scripts/build/buildCompanyTier1.py 005930
```

## 강행 호출 룰 (agent 답변 품질 회귀 차단)

dashboard 는 *프론트엔드 정적 페이지* 라 ask LLM 의 EngineCall 대상이 아님. 다음 3 룰 강행:

1. **"회사 페이지" / "대시보드" 질문에 EngineCall 시도 금지** — `EngineCall(apiRef="dashboard")` 같은 호출 없음. 답변은 URL 안내 (`landing/static/company/{code}/index.html` 또는 `Company.view()`) 또는 동일 데이터의 원천 EngineCall (`Company.panel` / `Company.analysis`) 로 우회.
2. **dashboard 안 5 tier 데이터 (finance · ratios · grades · ecosystem · narrative) 인용 시 원천 ref 표기** — dashboard JSON 자체가 아니라 그 데이터가 유래한 `Company.panel`/`Company.analysis` 결과의 `[tableRef:...]`/`[valueRef:...]` inline 표기.
3. **빌드 미수행 종목은 "데이터 부재" 명시** — 빈 블록 페이지를 정상 응답으로 답변 금지.

## 호출 동작

`Company.view(port=8400)` — 로컬 SvelteKit dev 서버를 띄우고 기본 브라우저로 `/company/{code}` 를 연다. 빌드 산출 JSON 이 없으면 페이지가 빈 블록으로 렌더된다 (해당 tier 빌드 먼저 실행 필요).

빌드 파이프라인은 종목별로 5 tier JSON 을 `landing/static/company/{code}/` 에 떨어뜨린다. CI matrix 로 종목 분산 (전 상장사 단일 머신 빌드 시 OOM).

python 직접 데이터 조회는 본 skill 이 아니라 [engines.company](/skills/engines.company) (`c.panel("BS")` 등) 또는 [engines.analysis](/skills/engines.analysis) (`c.analysis(...)`) 를 통한다.

## 위젯별 계산 식

- **radar 5 축**: 수익성·성장성·안정성·효율성·현금흐름. grade A-F → 1-5 스케일 매핑.
- **Altman Z** (제조업): `1.2A + 1.4B + 3.3C + 0.6D + 1.0E`. 항 정의는 `finance.bs.totals` 기반.
- **Beneish M**: 원식 계정 계약 미충족으로 현재 비발행. simplified/proxy 점수 금지.
- **Ecosystem HHI + Top-N**: `ecosystem.links` 필터에서 매출 비중 집계.

## 대표 반환 형태

python 호출은 부수 효과 (브라우저 띄움) — 반환 없음. 데이터 형태는 빌드 산출 JSON:

```text
landing/static/company/{code}/finance.json
  bs · is · cf · period · dataAsOf

landing/static/company/{code}/grades.json
  radar : dict[axis, score]      # 1-5
  altmanZ : float
  beneishM : null   # canonical 공급자 입력 계약 전까지 비발행
  dataAsOf : str
```

## evidence 기준

빌드 산출 데이터를 답변에 인용할 때는 `dataAsOf` (빌드 시점) 를 반드시 포함. 빌드가 매일 갱신 안 되면 stale 가능성 명시. python 측 `Company.panel()` / `Company.analysis()` 결과는 본 skill 이 아니라 해당 엔진 skill 의 evidence 기준 따름.

## 기본 검증

dashboard 페이지의 위젯 값이 코드 계산과 어긋나면 — tier 빌드 스크립트가 stale. `cd landing; npm run build` 후 회사 tier 재빌드. python 측 SSOT 는 [engines.analysis](/skills/engines.analysis) · [engines.credit](/skills/engines.credit) 의 호출 결과.
