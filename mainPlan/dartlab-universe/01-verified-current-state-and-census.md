# 01. 현재 상태 실측과 전체 census

## 1. 조사 기준

조사 시각: 2026-07-18 13:45:51 Asia/Seoul

로컬 기준 git HEAD: `4ea5a116779c9852c168e80dacbe206001d3c73d`

현재 worktree에는 사용자 작업이 있으므로 블로그 census는 HEAD만이 아니라 현재 파일 내용 기준이다. 미래 snapshot은 clean `gitCommit` 또는 당시 dirty byte를 보관한 local CAS `dirtyCaptureRefs`를 기록한다. digest만 남기고 재현 가능하다고 주장하지 않는다.

아래 숫자는 제품 상수가 아니다. 이번 조사로 관측한 기준선이다.

## 2. HF 전체 실측

### 2.1 접근 가능한 저장소

| repo | authority | revision | last modified UTC | 파일 | bytes |
|---|---|---|---|---:|---:|
| `eddmpython/dartlab-data` | 구조화 데이터와 발행 artifact | `fa2adde3f796a6b5db8ff57f8ea30f4a85d554f7` | 2026-07-18 04:41:49 | 68,673 | 282,630,004,707 |
| `eddmpython/dartlab-media` | 블로그·카드 media object SSOT | `efed37956583237a73bbbb67683a726e3e3e4bd8` | 2026-07-18 02:33:32 | 3,123 | 267,960,558 |
| `eddmpython/dartlab-dart-original` | 비공개 DART 원문 archive | `46c49eb22615b22b2947a5afee01257a554411a5` | 2026-07-16 21:13:47 | 2,933 | 20,884,615,624 |
| `eddmpython/dartlab-news-private` | 비공개 뉴스 metadata | `2093ed4ad0d422854402edb2e7cea5491d5785b4` | 2026-07-17 11:14:57 | 3,028 | 752,797,541 |
| 합계 | 현재 접근 가능한 전체 | 각 repo revision 묶음 | 관측 시점 | 77,757 | 304,535,378,430 |

configured authority repo set은 `HF_REPO`, `HF_MEDIA_REPO`, 모든 `DATA_RELEASES[*].repo`의 합집합이다. 현재 이 식의 결과가 위 4개와 정확히 일치한다. count 4나 repo ID 목록을 Universe expected 상수로 복사하지 않는다.

private repo 조회에는 로컬 `HF_TOKEN`이 필요하다. token 값은 log, snapshot, 문서, browser로 전달하지 않는다. 접근 권한이 없는 실행 환경에서는 해당 repo를 누락시키지 않고 `ACCESS_DENIED`로 등록하고 G0를 실패시킨다.

### 2.2 `dartlab-data` 형식 분포

| extension | 파일 수 |
|---|---:|
| parquet | 63,156 |
| json | 3,884 |
| arrow | 803 |
| bin | 780 |
| npz | 37 |
| png | 4 |
| etag | 4 |
| wheel | 3 |
| markdown | 1 |
| extension 없음 | 1 |

### 2.3 `dartlab-data` 주요 live path

| path prefix | 파일 수 | 1차 해석 |
|---|---:|---|
| `edgar/finance` | 9,997 | EDGAR company facts 계열 |
| `news/public` | 9,258 | 공개 뉴스 archive와 enrichment |
| `edgar/panel` | 7,450 | EDGAR 공시 수평 panel |
| `edgar/docs` | 7,003 | deprecated 표시가 있는 EDGAR 문서 계열 |
| `edgar/financeStmt` | 6,442 | DART finance 동형 EDGAR 재무 |
| `edgar/prices` | 4,123 | EDGAR 회사 가격 timeline |
| `gov/prices` | 3,715 | 공공데이터 가격 |
| `dart/report` | 3,251 | 정기보고서 정형 데이터 |
| `dart/finance` | 3,223 | DART 재무 |
| `dart/docs` | 3,141 | DART 문서 계열 |
| `dart/panel` | 2,932 | DART 공시 수평 panel |
| `landing/map` | 2,710 | 산업지도 artifact |
| `dart/contentIndex` | 2,352 | 검색 index artifact |
| `dart/allFilings` | 1,333 | 전체 공시 archive |
| `dart/sections` | 1,200 | section 계열 |
| `edgar/allFilingsContent` | 275 | EDGAR filing content |
| `edgar/panelCell` | 74 | panel cell 계열 |
| `dart/scan` | 65 | 전종목 scan artifact |
| `research/brokerage` | 25 | 리서치 metadata |
| `gov/indices` | 22 | 공공데이터 index |
| `edgar/scan` | 18 | EDGAR scan |
| `metadata/corpListVintage` | 10 | 법인 목록 vintage |
| `dart/searchCatalog` | 8 | 검색 catalog |
| `landing/dashboards` | 5 | dashboard artifact |
| `macro/ecos` | 4 | ECOS |
| `macro/fred` | 4 | FRED |
| 기타 | 34 | expectations, ticker, macro, IPO, wheel, metadata 등 |

### 2.4 media 실측

`dartlab-media`는 object 3,120개, manifest 2개, `.gitattributes` 1개다.

| extension | 파일 수 |
|---|---:|
| webp | 1,767 |
| svg | 1,322 |
| jpg | 24 |
| png | 6 |
| json | 2 |
| gif | 1 |
| extension 없음 | 1 |

### 2.5 private repo 실측

- `dartlab-dart-original`: `.gitattributes` 1개와 회사별 `docs/{code}.tar` 2,932개
- `dartlab-news-private`: `.gitattributes` 1개와 `news/private/naver` 3,027개

Universe는 private locator를 public response에 노출하지 않는다. 권한 없는 사용자는 resource 존재 여부까지 숨겨야 하는지 `visibility=PRIVATE` 정책으로 제어한다.

## 3. 선언 레지스트리와 live tree의 차이

`src/dartlab/core/dataConfig.py`의 `DATA_RELEASES`는 현재 dirty worktree byte 기준 42개 slot이다. 관측 source SHA-256은 `8f08a2c02578b92f123cb9fb8a2d72ce27c10a440038c34ec6d19be842a65d6d`이며 snapshot 상수가 아니라 이번 census evidence다.

- public 32개
- private 10개
- default data repo 39개
- news private repo 2개
- DART original repo 1개

그러나 live HF에는 `dart/docs`, `dart/sections`, `dart/searchCatalog`, `dart/embed`, `dart/queries`, `edgar/allFilingsContent`, `edgar/panelCell`처럼 `DATA_RELEASES`에 직접 대응하지 않는 path가 있다. 반대로 `DATA_RELEASES`에는 동결·미빌드 EDINET slot처럼 live file이 없는 선언도 있다.

따라서 전체성의 정본은 어느 한쪽이 아니다.

```text
discoveredSources = liveHfTree UNION declaredDataReleases UNION mediaRepo
reconciliation = declared_and_live
               | live_unregistered
               | declared_empty
               | deprecated_live
               | access_denied
               | unsupported_format
```

`live_unregistered`는 삭제 후보가 아니라 Universe에 그대로 존재하는 `ORPHAN_DECLARATION` 상태다. 별도 데이터 원천으로 승격하지 않고 authority mismatch를 보이는 것이다.

## 4. 실존 엔진과 capability 실측

`dartlab.capabilities()`는 현재 226개 항목을 반환한다. 이 값은 root function, Company method, engine axis, AI contract를 함께 포함하므로 종류를 구분해 저장해야 한다.

### 4.1 실제 axis registry

| engine | registry source | axis | hidden |
|---|---|---:|---:|
| analysis | `analysis/financial/_registry.py` | 22 | 0 |
| scan | `scan/router.py` | 27 | 0 |
| gather | `gather/entry/dispatch.py` | 18 | 2 |
| quant | `quant/_registry.py` | 48 | 0 |
| credit | `credit/__init__.py` | 8 | 0 |
| macro | `macro/__init__.py` | 15 | 0 |
| industry | `industry/__init__.py` | 9 | 0 |
| 합계 | live registry | 147 | 2 |

hidden 두 축은 `gather.dartDoc`, `gather.calendar`다. catalog에서 삭제하지 않고 `HIDDEN_PREVIEW`로 분류한다. 호출 가능 여부, 안정성, 공개 가능 여부는 서로 다른 필드다.

### 4.2 프로젝트 계약 엔진 전체 census

2026-07-18 현재 worktree byte 기준이다. sha16은 관측 digest이며 제품 상수가 아니다. 다음 census는 full SHA-256을 기록한다.

| engine folder | folder | root facade 상태 | registry | axis | mirrored axis | gap state | current source sha16 |
|---|---|---|---|---:|---:|---|---|
| gather | 존재 | callable | `gather/entry/dispatch.py` | 18 | 18 | MATCHED | `369872489c39d391` |
| scan | 존재 | callable | `scan/router.py` | 27 | 27 | MATCHED | `8acb6cb95bfcaa4f` |
| frame | 존재 | module, non-callable | 없음 | 0 | 0 | CONTRACT_MODULE_NO_FACADE | `62986df7a5d2837f` |
| synth | 존재 | module, non-callable | 없음 | 0 | 0 | CONTRACT_MODULE_NO_FACADE | `941bba7f86c02817` |
| reference | 존재 | root symbol 없음 | 없음 | 0 | 0 | CONTRACT_MODULE_NO_ROOT | `de63c293e87c0314` |
| analysis | 존재 | callable | `analysis/financial/_registry.py` | 22 | 0 | CALLABLE_UNMIRRORED | `dc3273860f5e2911` |
| macro | 존재 | callable | `macro/__init__.py` | 15 | 15 | MATCHED | `69eed22f11b6c147` |
| quant | 존재 | callable | `quant/_registry.py` | 48 | 48 | MATCHED | `94f649ded432fb1f` |
| industry | 존재 | callable | `industry/__init__.py` | 9 | 9 | MATCHED | `6b85ca09f2714130` |
| credit | 존재 | callable | `credit/__init__.py` | 8 | 8 | MATCHED | `6c1e607a67a8104b` |
| story | 존재 | module, non-callable, `Story` class 별도 | 없음 | 0 | 0 | CONTRACT_MODULE_CLASS_SURFACE | `d140baf7a88c29cb` |

`frame`, `synth`, `reference`, `story`는 folder가 존재한다고 axis callable로 발명하지 않는다. 실행 후보가 아니라 contract engine module candidate로 catalog하고 현재 facade gap을 정직하게 표시한다.

### 4.3 전체 axis 기준선

- analysis: 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, 효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성, 가치평가, 지배구조, 공시변화, 비교분석, 매출전망, 예측신호, 매크로민감도, 밸류에이션밴드
- scan: governance, workforce, capital, debt, account, ratio, note, network, cashflow, audit, insider, quality, liquidity, growth, profitability, efficiency, valuation, dividendTrend, macroBeta, fields, screen, disclosureRisk, orders, ipo, salesByProduct, narrativeMetric, earningsFlash
- gather: price, flow, macro, news, sector, insider, ownership, peers, krx, krxIndex, narrative, research, naverTheme, naverIndustry, naverEtf, naverEtn, dartDoc, calendar
- quant: indicators, signals, verdict, momentum, volatility, forecast, marketContext, regime, pattern, chartPatterns, beta, benchmark, factor, tailrisk, residual, liquidity, flow, volume, divergence, quality, value, earnings, sentiment, toneChange, eventSignal, riskText, governanceQuant, ranking, pairs, screen, altman, piotroski, beneish, accruals, qfactor, qmj, bab, surprise, fundmom, meanvar, riskparity, allocation, strategy, backtest, style, entry, walkforward, multi
- credit: grade, repayment, leverage, liquidity, cashflow, business, reliability, disclosure
- macro: cycle, inventory, corporate, trade, transmission, rates, liquidity, crisis, assets, sentiment, narrative, forecast, scenario, simulate, summary
- industry: summary, timeline, lifecycle, concentration, dynamics, polarization, edges, map, theme

`analysis` axis가 현재 capability builder의 prefix 목록에 자동 나타나지 않는 현상도 census finding으로 남긴다. Universe가 이를 임의 보정해 새 API를 만들지 않는다. live registry와 `dartlab.capabilities()`를 병렬 수집하고 drift로 표시한다.

### 4.4 axis가 아닌 callable

현재 capability 226개에는 Company method 63개, root callable, `OpenDart`, `OpenEdgar`, `Story`, AI contract 등이 있다. Universe는 모두 catalog하지만 실행 정책을 분리한다.

- `ENGINE_AXIS`: 기존 `dartlab.{engine}(axis, args)`로 호출
- `COMPANY_METHOD`: Company facade의 공개 method
- `ROOT_CALLABLE`: root public callable
- `AI_CONTRACT`: 실행 도구가 아니라 검증 규약
- `PREVIEW`: 호출 가능해도 안정 공개 계약 아님

상세 input/output schema를 소스 밖에서 발명하지 않는다. docstring live builder가 제공하지 못하는 schema는 `SCHEMA_INCOMPLETE`로 남기고 G2를 실패시킨다.

U0 engine candidate 집합은 다음 union이다.

```text
engineCandidates = dartlab.capabilities()
                 UNION actual axis registries
                 UNION contract engine folder census
                 UNION Company facade methods
                 UNION root facade presence
```

각 registry와 facade source의 full content digest를 snapshot에 포함한다. dirty worktree이면 digest만으로 재현됐다고 주장하지 않고 해당 byte의 local CAS `dirtyCaptureRef`를 함께 보존하거나 snapshot을 `NONREPLAYABLE`로 차단한다.

## 5. 블로그와 미디어 실측

현재 `blog/[0-9][0-9]-*/**/index.md` 기준:

| 항목 | 관측값 |
|---|---:|
| 글 | 275 |
| bytes | 9,635,116 |
| lines | 108,993 |
| heading | 7,318 |
| markdown table row | 15,688 |
| code block | 1,220 |
| paragraph block 근사 | 21,440 |
| image ref | 1,821 |
| 고유 image ref | 1,808 |
| link | 3,997 |
| `youtubeId` frontmatter 보유 글 | 156 |
| 비어 있지 않은 YouTube ID | 14 |

카테고리별 글 수:

- `01-reading-disclosures`: 43
- `02-dartlab-news`: 10
- `03-dartlab-stories`: 13
- `04-credit-reports`: 16
- `05-company-reports`: 167
- `06-data-reports`: 7
- `08-tech-story`: 14
- `09-investment-stories`: 5

모든 글에 이미지 ref가 하나 이상 있다. image ref 1,821개는 전부 `dartlab-media` URL을 가리키지만 media repo object 3,120개 전체와 같지 않다. 그러므로 census는 다음을 모두 보여야 한다.

- referenced media
- unreferenced media
- broken reference
- duplicate reference
- manifest-only object
- external video locator
- transcript absent/present
- license and credit status

`media/catalog.json` 현재 실측:

- object 3,120개
- file alias 2,808개
- post mapping 275개
- collection 4개
- manifest 2개

본문 외 companion artifact도 같은 블로그 source family의 서로 다른 resource kind로 전수 열거한다.

| companion pattern | 현재 관측 |
|---|---:|
| `brief.json` | 38 |
| `CREDITS.md` | 214 |
| `cards.plan.json` | 15 |
| `carousel.yaml` | 11 |
| `episode.yaml` | 13 |
| `published.json` | 13 |
| `youtube.md` | 9 |
| `imagegen-extract.json` | 12 |
| 추적된 `script.md` | 0 |

`blog/_podcasts/episodes`에는 현재 `episode.yaml` 13개와 `published.json` 13개가 있다. episode metadata와 발행 기록은 catalog 대상이지만 추적된 script나 transcript가 없으면 본문 지식이 있다고 주장하지 않는다. 위 수치는 현재 관측값이며 expected 상수가 아니다. U0는 blog tree를 pattern-independent하게 먼저 열거한 뒤 알려진 companion parser와 `UNCLASSIFIED_COMPANION` 상태를 적용한다.

## 6. 로컬 시뮬레이터 실측

`src/dartlab/simulate/`는 현재 68개 Python 파일을 가진 큰 preview 묶음이다. 이전 AST 조사에서 top-level function 359개, class 181개가 관측됐다. 현재 결정론 경로는 존재하지만 filing-vintage PIT, UI, 공식 Skill OS 계약이 미완이다.

로컬 `data/`에는 현재 78,164개 파일이 관측되지만 이것을 곧바로 Universe 범위로 자동 수록하지 않는다. `_scratch_*`, cache, 임시 report, test artifact가 섞일 수 있기 때문이다. 사용자가 말한 로컬 simulator 데이터는 완전한 receipt envelope를 가진 명시 등록 artifact만 대상이다.

Universe는 simulator 내부를 canonical data source로 취급하지 않는다.

- simulator code는 수정하지 않는다.
- `dartlab.simulate`가 현재 callable이어도 `PREVIEW` 안정성으로 기록한다.
- result는 항상 `SIMULATED`다.
- 입력 assumption, as-of, source snapshot, seed, code revision, output digest가 없는 result는 받지 않는다.
- 초기 attempts에서는 저장된 result/receipt만 읽고 내부 helper를 직접 호출하지 않는다.

## 7. 기존 프론트 데이터 작업대 실측

공개 runtime의 데이터 게이트는 다음이다.

- `ui/packages/runtime/src/data/fetch/request.ts`
- `ui/packages/runtime/src/data/origins/registry.ts`
- `ui/packages/runtime/src/data/fetch/*`
- `ui/packages/runtime/src/adapters/local/api/localApi.ts`

`request.ts`는 request, parquet range/whole-file, bytes, cache, dedup을 조립한다. origin registry는 `hf`, `hfRange`, `hfMedia`, `localApi` 등 허용 origin을 한곳에서 관리한다. 로컬 `/api`는 `adapters/local/api/localApi.ts` 단일 게이트를 쓴다.

이 작업대는 transport와 cache SSOT이지 Universe의 semantic catalog가 아니다. Universe가 두 번째 fetch/cache 층을 만들 수 없고, UI가 나중에 연결될 때도 이 게이트를 경유해야 한다.

## 8. Source Authority Matrix

| source | authority | Universe가 읽는 것 | freshness | visibility | 금지 |
|---|---|---|---|---|---|
| HF data live tree | repo revision, path, blob metadata | 모든 파일, format, size, schema locator | repo revision | mixed | 복사 repo 생성 |
| HF media | content-addressed object path | 모든 object, manifest, media metadata | repo revision | public | 참조된 것만 등록 |
| DART original private | company tar locator | original archive 위치와 권한 | repo revision | private | browser에 path/token 노출 |
| news private | private parquet locator | metadata와 권한 상태 | repo revision | private | public index로 혼합 |
| `DATA_RELEASES` | 선언된 release 의미와 공개 정책 | slot, dir, label, nested, repo, public | code revision | mixed | live tree 정본으로 오인 |
| provider DART | DART identity와 공시 access | Company facade와 source ref | source-specific | mixed | 별도 DART 우주 |
| provider EDGAR | SEC identity와 공시 access | Company facade와 source ref | source-specific | public | DART의 보조로 강등 |
| capability catalog | live docstring and registry | callable kind, axis, schema, stability | code revision | local | 가짜 axis 보충 |
| blog git | markdown file content | frontmatter, AST block, link, claim, selector | git revision + digest | public | 본문을 관측 사실 처리 |
| simulator | preview execution receipt | scenario result와 assumptions | code + input snapshot | local | OBSERVED 승격 |
| UI data workbench | transport/cache contract | 승인된 origin과 request path | code revision | public/local | raw fetch, self cache |

## 9. 완전성 원장

source별로 다음 수치를 기록한다.

```text
discovered
registered
addressable
structured
identified
retrievable
ragEligible
excluded
failed
unresolved
revision
censusStartedAt
censusFinishedAt
```

계산식:

```text
reconciliationCoverage = (registered + excluded + failed) / discovered
addressabilityCoverage  = addressable / discovered
structureCoverage       = structured / discovered
identityCoverage        = identified / identityEligible
evidenceCoverage        = statementsWithEvidenceOrDerivation / verifiedStatements
referenceIntegrity      = resolvedRefs / totalRefs
```

규칙:

- `registered + excluded + failed = discovered`가 아니면 census 자체 실패
- G0에서 reconciliationCoverage 100%, addressabilityCoverage 100%, failed 0
- excluded는 license, access policy, deprecated와 같이 코드화된 reason이 있어야 함
- excluded도 catalog에서 사라지지 않음
- `identityEligible=0`이면 identityCoverage를 100%로 속이지 않고 `NOT_APPLICABLE`로 기록
- current count를 기대값으로 hard-code한 테스트 금지

## 10. 재조사 명령 계약

Phase U0가 구현되면 단일 명령이 정본이다.

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/census.py --all --strict --format json
```

구현 전 현재 ground-truth 확인 명령:

```powershell
uv run python -X utf8 -c "from dotenv import load_dotenv; load_dotenv('.env'); from huggingface_hub import HfApi; a=HfApi(token=__import__('os').environ.get('HF_TOKEN')); print([(r, a.dataset_info(r, files_metadata=False).sha, len(a.list_repo_files(r, repo_type='dataset'))) for r in ['eddmpython/dartlab-data','eddmpython/dartlab-media','eddmpython/dartlab-dart-original','eddmpython/dartlab-news-private']])"
uv run python -X utf8 -c "import dartlab; c=dartlab.capabilities(); print(len(c), sorted(c))"
uv run python -X utf8 -c "from pathlib import Path; p=list(Path('blog').glob('[0-9][0-9]-*/**/index.md')); print(len(p))"
```

private repo 조사 전 `.env`를 안전하게 load해야 하며 token을 출력하지 않는다. CI의 public-only 실행은 전체 G0가 아니라 별도 `publicCensus` smoke로만 인정한다.

## 11. G0 인수 기준

- `HF_REPO`, `HF_MEDIA_REPO`, `DATA_RELEASES[*].repo` 합집합으로 configured authority repo 집합을 동적 조립하고 discoveredRepoIds와 100% 일치. 현재 관측 count 4는 상수가 아님
- configured HF authority repo의 repo, full revision, path, oid, byte, format을 metadata request만으로 100% 열거하는 C0, C1 census
- configured repo 누락 0, 설정되지 않은 repo를 DartLab authority로 사용 0
- G0에서 parquet나 Arrow payload body를 내려받거나 schema, row count를 강제하지 않음
- blog post, companion artifact와 media object 100% 열거
- blog media broken ref 0
- callable 226개 기준을 상수로 쓰지 않고 live catalog 100% reconcile
- registry axis 100% reconcile, invented axis 0
- `DATA_RELEASES`와 live tree drift 전량 분류
- access denied 0인 승인된 local 환경에서 failed 0
- 동일 source revision으로 두 번 실행한 census digest 일치
- 기존 source file diff 0

schema와 row count는 U3의 C2 descriptor crawl에서 format-aware lazy read로 채운다. C2는 각 structured candidate를 `DESCRIBED`, `UNSUPPORTED_FORMAT`, `DESCRIPTOR_BLOCKED_RANGE`, `PARSE_ERROR`, `ACCESS_DENIED` 중 하나로 100% 종결하고, 성공 항목에는 schema fingerprint와 row count 또는 row-count-unavailable reason을 남긴다. Parquet, Arrow, JSON, NPZ, Markdown, YAML과 image metadata처럼 format policy가 descriptor-eligible로 선언한 형식은 `DESCRIBED` 100%여야 하며 다른 terminal 상태는 reconciliation record일 뿐 U3 합격으로 세지 않는다. opaque `.bin`과 미인식 형식은 magic sniff, source meaning, exclusion reason 없이 `UNSUPPORTED_FORMAT`으로 도피할 수 없다. 따라서 60초 metadata census인 G0와 304.5GB payload 기술 검사는 서로 다른 gate다.
