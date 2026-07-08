# 17. 전 엔진 작업대 지도 (개념 #1 = 모든 엔진의 데이터/분석을 하나의 시계열 작업대에)

> v1.0 (2026-07-07). 15개 엔진 전수 조사(wf_bb8128c2, 엔진당 1에이전트 + 종합)의 확정 지도.
> 계기: "8표면만 긁고 분석 엔진(analysis/credit/quant/industry/macro/edgar/scan)을 빠뜨렸다"는
> 운영자 지적. 이 문서 = 어느 엔진이 무엇을 어떤 포맷으로 작업대에 먹이나 + 벌크 안전 경계 + 갭.
> 척추 실장 정본 = simulate/table.py(현 8표면), 개념 = 16 §1(상태), 15(실행 계획).

---

## §1. 결론

작업대는 "8표면"이 아니라 **"9개 공급 엔진 x 축"**이다. 나머지 6개(company·data·dashboard·mappers·
story·viz)는 소비/유틸/뷰라 슬롯할 데이터가 원천적으로 0. 기존 8표면(prices·macro·finance·betas·
industry·priceSig·events·funding)은 **원천 프리미티브만** 담았고, 그 위 분석데이터(계산된 재무비율
시계열·복합 부실점수·11 팩터 알파·US 재무·산업분류·감성)를 통째로 빠뜨렸다. 빠진 분석데이터 중 벌크로
실제 슬롯 가능한 정본 경로는 대부분 **scan/edgar 소유**(analysis·credit 아님). 계산물(비율·점수·팩터)은 순수함수라 패널 벡터로 런타임 벌크 계산이 된다(§5.1 실증: 전종목 재무비율 87,209행 8.8초 1패스, Company 루프 0·사전빌드 0). 이전에 이를 per-company only·사전빌드라 한 것은 **틀렸다**. analysis/credit 엔진 facade 가 Company 객체 하나씩 받는 API 모양일 뿐 계산이 회사별이 아니다. 진짜 벌크 불가는 계산이 아니라 아직 벌크 창고에 없는 데이터(라이브 수급 등)뿐.

## §2. 분류: 공급 9 vs 소비/유틸 6

**(a) 작업대에 먹이는 엔진 9:**

| 엔진 | 먹이는 정본 축 | 포맷 | granularity | 벌크안전 |
|---|---|---|---|---|
| scan | account·ratio·note = (code x period) 시계열 | wide code+기간열 / note long | 분기·연 | O 단일 parquet streaming |
| scan | 17 분석축(profitability~salesByProduct) | code+지표+grade, period 키 없음 | 단면 t=latest | O |
| edgar | scan(account/ratio, market=us) = US 재무 시계열 | ticker x 기간 wide | 분기·연 | O glob+ThreadPool |
| edgar | scan 11축(us) | ticker+팩터+grade | 단면 최신 | O |
| gather | krx OHLCV/시총(반영됨), **krx 28+ 기술지표(미반영)** | code x date wide | 일 | O hfBulk |
| gather | macro observations(반영), **narrative score/pulse·krxIndex(미반영)** | date x factor / index x date | 일·월 | O |
| quant | 11 재무 알파(altman·piotroski·beneish·accruals·qfactor·qmj·bab·surprise·fundmom·순위) | dict{scores:{code:float}} | 최신 FY 단면 | O loadScanParquet 1회 |
| industry | 산업분류 정적차원(industryMap chainPosition)·theme·산업레벨 파생 6종 | code·공정·stream·confidence | 정적/연 | O nodes.json |
| macro | 15 시장축(cycle/rates/liquidity/sentiment/crisis/forecast/corporate...) | dict latest(asOf 리플레이) | 단면->시계열 | O **code 없음=환경 레인** |
| analysis | 재무비율/복합점수 시계열(개념상 여기 것이나 **벌크 로더 0**) | 회사당 nested dict | 연·분기 | X per-company(벌크는 scan 경유) |
| credit | grade/score/7축(형태 적합하나 벌크 패널 부재·희소) | dict evaluateCompany | 단면+history | X per-company |
| search | timeline·profile·dna(provider-internal, **공개계약 미노출**) | period x report / code 정적 / 114벡터 | 월·정적 | O 단 dartlab.* 미노출 |

**(b) 소비/유틸 6 (데이터 아님):** company(per-company 창, 200~500MB)·data(신선도 도구·verb 없음)·
dashboard(렌더, verb 없음)·mappers(이름 정규화 유틸)·story(L3 조합기, 자체 계산 0)·viz(표현 헬퍼, 렌더 사본).

## §3. 8표면 대비 빠뜨린 분석데이터 (정직한 답)

**A. 벌크안전인데 미materialize (즉시 채울 갭, 최우선):**
- scan account/ratio/note = **재무비율/계정 (code x period) 시계열 정본** (8표면 finance 는 raw BS/IS/CF 만, 계산된 ROE/부채비율 없음)
- scan 17 분석축 최신 단면 · edgar US 재무 + 11축(**8표면 전부 KR = US 통째 누락**)
- quant 11 재무 알파 · gather krx 28+ 기술지표(현재 손계산 4종만) · gather narrative/krxIndex · search timeline/profile/dna · industry theme/산업파생

**B. per-company only (요청 시 계산):** analysis 22축 리치 파생(DuPont·ROIC·Penman·EVA·valuation·forecast) · credit grade/7축 · quant 리스크/팩터(beta·거시베타·FF5·CVaR·GARCH)·기술판단.

**정직:** 8표면은 "이미 통합 parquet 이 있는 벌크 로더"만 직독. 분석데이터는 (A) scan/edgar 소유 벌크인데
호출 미배선 또는 (B) per-company 재계산이라 OOM 가드에 막혀 스킵. "모든 엔진"이라 해놓고 gather/scan
원천 로더 층만 긁었다.

## §4. 통일 포맷 (레인 계층)

출처별 딕셔너리 + (code, 시간) 공통 척추 + 3속도 + 환경 + 단면/정적 계층.

```
workbench = {
  spine:   { daily(code x date), weekly(code x week), period(code x period) },  # prices·krx지표 / flow / scan.account·ratio·edgar us
  derived: { ratios·accounts(scan) · alpha(quant) · us_ratios(edgar), source 태그 공존 },
  snapshot:{ code x metric : scan 17축 grade · quant 11 알파 · industry 백분위 (t=latest 1슬라이스) },
  dim:     { industry(id/stage/stream) · theme · search.profile/dna (code 라벨, 시간불변) },
  env:     { date: macro 15축·narrative·search.timeline / index: krxIndex (code 없음, broadcast) },
  events:  { filings·insider·orders·earningsFlash·calendar (code+date, dense 아님) },
  graph:   { industry.edges · scan.network (code쌍, 척추 아님) },
}
```

원천과 분석은 같은 (code, period) 격자 위에 spine(raw account)과 derived(계산 ratio)가 **source 태그로
나란히**. 이중계산 회피 = 원천은 spine 직독, 파생은 scan 계산본만. macro/narrative/timeline 은 code 없어
env 레인에서 date 조인 broadcast, 산업분류는 dim 에서 code 조인.

## §5. 벌크 안전 경계 (메모리 가드 존중)

- **전종목 벌크 로딩 가능 (작업대 후보)**: scan 전 축 · edgar scan account/ratio/11축 · gather 벌크
  로더 · quant 11 알파 · industry nodes/edges · search timeline/profile/dna · macro 환경(단 summary
  7632MB peak 중량 주의).
- **facade 는 per-company 지만 계산은 벌크 가능**: analysis 22축·credit grade/7축·quant 팩터의 *숫자*는 순수함수라 패널 벡터로 전종목 계산 가능(scan.ratio 가 그 경로, §5.1 실증). Company facade API 만 하나씩 받을 뿐. **진짜 벌크 불가** = 아직 벌크 창고에 없는 라이브 외부 fetch(gather 수급 일별 등)뿐이고, 이는 계산이 아니라 데이터 커버리지 문제(gather 벌크화로 해소, 사전빌드 아님).
- 채울 수 있는 것 = scan/edgar/quant-alpha/gather-bulk/industry/search-internal/macro-env. **분석 파생(비율·점수·팩터)도 런타임 벡터 벌크 계산으로 채운다(사전빌드 아님, §5.1).** 사전빌드는 불필요할 뿐 아니라 런타임-SSOT 원칙상 기본 금지다.

### §5.1 정정 실증 (2026-07-07): 분석층도 런타임 벌크 (사전빌드 아님)

재무 패널(scan 벌크) 위 벡터 1패스로 ROE·ROA·마진·부채비율 + YoY 점수부품(fScore)을 **전종목
2,774사 x 전기간 87,209행, 8.8초, Company 루프 0·사전빌드 0**으로 계산 실증
(`tests/_attempts/workbench/derived_bulk.py`). 재무비율·점수·팩터는 순수함수 r = f(계정)이고 계정
패널은 이미 벌크라, 패널 위 벡터가 전종목 전기간을 한 방에 낸다. `scan.ratio`/`macroBetaByCodeWide`가
바로 이 벌크 경로(이미 존재). "per-company only / 사전빌드 필요"는 틀렸고, 사전빌드는 런타임-SSOT
원칙상 금지. 작업대 분석층 = 런타임 벡터 계산.

## §6. 정직한 갭 (아직 못 들어가는 것)

1. **시계열 vs 단면**: scan 진짜 (code x period) 시계열은 account/ratio/note 셋뿐. 17 분석축 + quant 11
   알파는 latest FY 로 collapse 된 단면(period 키 없음). 시간축 태우려면 account/ratio 원자에서 재조합
   재계산(순수함수라 가능하나 미구현).
2. **US 커버리지**: edgar 는 account/ratio/11축만. betas·priceSig·funding·events·insider·note·flow 는
   KR 전용. US 이벤트 스트림 미저장(skeleton).
3. **per-company 계산물**: analysis/credit/quant 리치 파생은 벡터화 벌크 경로 자체가 없음(빠뜨린 분석의 절반이 여기 갇힘).
4. **정성/텍스트**: 거버넌스·법적리스크·감사의견·note 서술은 수치 격자 아님(이벤트/카테고리로만).
5. **벌크지만 미배선**: flow(외국인/기관 일별) HF 벌크 부재·수급 레인 최대 갭 / dividends·splits 미구축(TR 수익률 없음) / revenueConsensus forward 레인 부재.
6. **공개계약 미노출**: search timeline/profile/dna 는 provider-internal(승격 토론 필요). naver 분류는 재배포 금지 로컬 전용.
7. **부수 발견(문서 불일치)**: macro SKILL 16축 vs 코드 15축(phantom 1) · dashboard SKILL 5-tier 빌드 파이프라인 현 트리 부재(stale).

## §7. 실행 우선순위

1. scan.account/ratio/note 벌크 시계열을 척추 period 레인에 배선 = 운영자 지목 "빠뜨린 재무비율" 정본.
2. edgar us scan = US 커버리지 개통.
3. gather krx 28+ 기술지표 materialize.
4. quant 11 알파 + scan 17 단면을 snapshot 레인에.
5. 분석 파생(비율·점수·팩터)은 런타임 벡터 벌크 계산(scan 경로·§5.1 실증). 사전빌드 아님. 진짜 벌크 불가 = 라이브 수급 등 미벌크 데이터뿐(gather 커버리지 문제).

## §8. 라우팅

- 엔진별 상세: `src/dartlab/skills/specs/engines/{scan,edgar,quant,gather,macro,industry,analysis,credit,search}/SKILL.md`.
- 조사 원문: wf_bb8128c2 워크플로 원장(엔진당 axes 전수 + 종합). 척추 현황: simulate/table.py 8표면.
- 개념: 16 §1(상태 = 작업대). 실행: 15. 진행: 04.
