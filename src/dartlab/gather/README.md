# gather/ — L1 외부 수집 엔진

> dartlab 의 *L1 raw 생산 owner* — 가격·수급·뉴스·거시지표·업종·내부자·지분·피어 등
> 외부/보조 시장 데이터를 한 콜러블 (`dartlab.gather`) 로 수집. providers/ (DART/EDGAR)
> 와 동급 L1. 공개 호출 계약은 Skill OS 가 정본 (아래 링크).

## 공개 진입점

```python
import dartlab

dartlab.gather()                       # 공개 축 가이드 DataFrame (정본)
dartlab.gather("price", "005930")      # KR OHLCV
dartlab.gather("macro", "FEDFUNDS")    # 거시지표 (시장 자동 감지)
print(dartlab.gather.formatStatus())   # 데이터 공급자 키 설정 상태 + 발급 링크 (첫 사용자)

g = dartlab.gather.getDefaultGather()  # Form B — 축이 아닌 고급 수집기
g.dividends("005930"); g.collect("005930")
```

- **Form A** (`dartlab.gather(axis, target, **kwargs)`) — 공개 13 축 + 베타 2 축(hidden). 축 정본 = `entry/dispatch.py` 의 `AXIS_REGISTRY`.
- **Form B** (`getDefaultGather()` → `Gather`) — dividends/splits/majorShareholders/collect 등 축 미등록 수집기.

## 모듈 지도 (실제 레이아웃)

| 경로 | 역할 |
|------|------|
| `entry/` | `dartlab.gather()` 콜러블 — `GatherEntry`(main) · `AXIS_REGISTRY`/dispatch · axis `handlers` |
| `engine.py` + `mixins/` | `Gather` 클래스 (Form B). mixin = price · info · news · macro · collect · context |
| `sources/` | L1 fetcher — `price.py` · `flow.py` · `news.py`(+ `naverNews`·`newsIo`·`newsSchema`·`newsSources`) · `history.py` · `insider.py` · `ownership.py` · `sector.py` · `naverGroups/`(테마·업종 `groups`, ETF/ETN `products` — 로컬용) · `gdelt.py` · `reader.py` · `search.py` |
| `domains/` | provider 도메인 — `fdr` · `fmp` · `krx` · `naver` · `naverGlobal` · `yahooChart` · `fallback` |
| `transforms/` | 수집 후 가공 — `adjustPrice`(수정주가) · `indicatorDispatch`(기술지표) · `corporateAction` · `pit` · `macro` |
| `original/` | DART 정기+비정기 document.xml zip 원본 백업 (gather 자체포함, `data/original/` 로컬, HF 미공개) |
| `fred/` · `ecos/` · `customs/` | 거시·무역 소스 facade (production — HF 벌크 sync + 테스트) |
| `ecb/` · `bis/` · `imf/` · `oecd/` | EU/GLOBAL 거시 SDMX facade (live, HF 캐시 없음 — `market="EU"`/`"GLOBAL"`) |
| `gov/` | 공공데이터포털 주가·지수 (KOGL) |
| `krx/` | KRX listing · 회사별/지수 wide |
| `dart/` · `edgar/` | DART/EDGAR accessor (listing · dartDoc) |
| `bulkData/` | HF 벌크 로더 (`macroHf` 등) |
| `mapping/` | 코드 매핑 (티커 ↔ 종목코드 · productIndicators) |
| `infra/` | http client · cache · `sdmxClient` · circuit breaker · telemetry |
| `credentials.py` | 자격증명 facade (`core/providers/dataCredentials.py` re-export) |
| `accessors.py` · `types.py` · `macroProvider.py` · `marketConfig.py` | 지원 모듈 |

## 자격증명 · env (단일 진입점)

키는 **공급자(provider) 단위** 로 관리 (`core/providers/dataCredentials.py` 레지스트리).

```python
dartlab.setup()                                  # ★ 단일 진입점 — 모든 키(추론+데이터) 현황
dartlab.setup("dataGoKr")                        # 특정 데이터 공급자 발급/설정 안내
print(dartlab.gather.formatStatus())             # 데이터 공급자만 ✓/✗ + 발급 링크
dartlab.gather.setCredential("dataGoKr", "<키>") # 암호화 저장 (.env 편집 불필요)
dartlab.gather.writeEnvExample()                 # .env.example 생성 (레지스트리 파생)
```

해석 우선순위: 명시 인자 → 환경변수 → SecretStore(암호화) → 안내 에러. 새 소스는
`os.environ.get` 직접 금지 — `from dartlab.gather.credentials import resolveKey` 경유.

## 룰

- L1 raw 생산 owner — 외부 API 호출은 본 폴더만 (gather ↛ providers 상호 import 금지)
- core 만 import
- 외부 본문 untrusted — `wrap_external_in_result` 마커 (T2-5 audit)
- prebuild 단계 import 금지 (offlineGuard, T7-2)

## 법적 고지 (데이터 출처)

네이버 등 외부 사이트에서 **라이브 직독**하는 축(`price`·`flow`·`ownership`·`sector`·`peers`·`naverTheme`·`naverIndustry`)은
dartlab 이 데이터를 호스팅·재배포하지 않고 호출 시점에 원본에서 직접 당겨온다 (라이브러리 클라이언트).

- **로컬 개인 사용까지는 문제되지 않는다** — 본인 컴퓨터에서 분석 용도로 라이브 수집해 쓰는 것은 무방하다.
- **재배포·공개는 DB권 문제가 발생할 수 있다** — 수집 결과를 HF 업로드·서비스 배포·제3자 공개하면
  데이터베이스제작자의 권리(저작권법 제4장)·저작권 문제가 발생할 수 있다. 이는 `naverTheme` 의 테마 분류·편입사유
  같은 편집저작물뿐 아니라 `price`(네이버 화면 시세) 등 네이버 출처 데이터 전반에 동일하게 적용된다.
- 따라서 이 축들의 산출물은 **HF SSOT 적재 대상이 아니며 공개 터미널 제품에 배선하지 않는다** — 라이브 직독
  라이브러리 verb 로만 노출한다.

## 관련

- [src/dartlab/skills/specs/engines/gather/SKILL.md](../skills/specs/engines/gather/SKILL.md) — 공개 호출 계약 정본
- [tests/gather/test_gatherAxisContract.py](../../../tests/gather/test_gatherAxisContract.py) — 축 registry 계약
- [tests/audit/untrustedWrapAudit.py](../../../tests/audit/untrustedWrapAudit.py) (T2-5)
- [.github/scripts/sync/](../../../.github/scripts/sync/) — sync workflow online 단계
