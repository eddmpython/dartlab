# 00 · 제품 PRD

## 사용자 스토리 (한 문장, 선두)

DART·EDGAR·KRX·거시 데이터를 분석하려는 사람이 **dartlab 의 HuggingFace 데이터를 엑셀/구글시트에서 바로** 쓰고 싶다. 그러나 오늘 그 데이터는 **parquet** 으로만 공개돼(`huggingface.co/datasets/eddmpython/dartlab-data`) 일반인은 열지도 못한다. viewer 의 친화 다운로드는 **회사 1개 × 공시·재무 2종**뿐이고, "전체 데이터셋"은 사실상 parquet 폴더 링크 한 줄이다. 본 PRD 는 그 간극을 **카탈로그 전체를 친화 포맷으로 주는 다운로드 센터 + 시트가 라이브로 빨아들이는 데이터 API** 로 닫는다.

## 문제 정의

- HF 공개 데이터는 parquet — Excel·Google Sheets 가 **직접 못 읽는다**. 두 도구는 URL 에서 CSV/TSV/JSON 을 빨아들이는 방식이다.
- 현 viewer `DataDownloadMenu`(`ui/packages/surfaces/src/viewer/components/DataDownloadMenu.svelte`)는 보는 회사 1개의 공시 수평화 CSV·재무 `.xls` 만 친화 변환하고, 나머지 카탈로그(~20 dir)는 raw parquet 직링크 또는 HF 페이지로만 노출.
- "전체를 zip 한 방"은 해법이 아니다 — 벌크는 이미 HF 가 준다(운영자 확정 비범위). 필요한 건 **누구나 추측 가능한 URL 로 원하는 슬라이스를 친화 포맷으로** 받는 것.

## 사용자 시나리오

1. **다운로드** — 애널리스트가 데이터 센터에서 `dart/finance` → 삼성(005930) → 컬럼·주기 골라 `.xlsx` 다운로드. 열면 숫자가 진짜 Number 라 `SUM`/`AVERAGE` 즉시 작동.
2. **구글시트 라이브** — `=IMPORTDATA("https://{host}/v1/gov/prices/company/005930.csv?tail=250&cols=date,close")` 한 줄로 최근 250 거래일 종가를 셀 격자에 당김. ~1시간마다 자동 갱신.
3. **엑셀 라이브** — 데이터 → 웹에서 → `.tsv` URL → Power Query 표 로드 → "모두 새로 고침".
4. **추측** — `…/resolve/main/dart/finance/005930.parquet` 를 아는 사람이 docs 없이 `…/v1/dart/finance/005930.tsv` 를 맞힌다.

## 확정 제품 결정 (운영자, 재론 금지)

[README §운영자 확정 제품 결정](README.md) 5종을 본 PRD 의 불변 전제로 박는다. 추가로 본 PRD 의 설계 판정(전문 패널 토론·적대 교차검증):

- 보안 게이트 = **public allowlist 단일화**(deny-list 폐기). 근거 → [03 §보안](03-tier2-live-worker.md), [05](05-validation-and-rollback.md).
- 노출 대상 = `public:True` **⊋** 표형 downloadable 화이트리스트(전부 아님).
- 기본 포맷 = **TSV**(한국 Excel 로케일 중립) + CSV 병행(Sheets IMPORTDATA 친화).
- cap 단위 = **셀(cols×rows)**, 행 아님. silent 절단 0(HTTP 헤더 신호).

## 범위 (In — MVP)

- **Tier 1** 브라우저 다운로드: 노출 dir 전부의 모든 파일, cap 없음(로컬 메모리). 기존 writer 재사용. → [02](02-tier1-download.md).
- **Tier 2** 라이브 워커: **회사당 flat 파일·series 한정**. 4 파라미터(`cols`/`tail`/`head`/`freq`). → [03](03-tier2-live-worker.md).
- 자기기술 2 엔드포인트(`/v1/` 카탈로그·`schema.json` footer 프로브).
- 링크빌더 UX(셀수 미리계산으로 헤더 신호 한계 보완).

## 비범위 (Out — KILL · 후속)

| 제외 | 이유 |
|---|---|
| zip 통짜 다운로드 | 벌크는 HF 가 줌(운영자 확정) |
| 날짜샤드(`gov/prices/date` ~326MB) Tier2 변환 | CF 128MB/CPU 한도 — 회사파일 라우팅 + Tier1 로 대체, 413 안내 |
| `filter`/`code` 파라미터 | `request.ts:33-34` 실측 = read 후 JS prune(진짜 prune 아님). 326MB 전량 디코드 OOM. 회사파일이 이미 존재 |
| `shape=wide`(pivot) | 전 행 메모리 적재 ↔ 셀cap·CF 충돌 |
| `from`/`to` 기간 필터 | `tail`/`head`/`freq` 로 충분, 날짜컬럼 자동감지 복잡도 후속 |
| pagination(offset/limit/next) | 시트 사용자 수동추적 비현실. 슬라이스·리샘플·회사파일이면 전량 케이스 희소 |
| JSON 봉투·`sep`/`format` 쿼리·passthrough `.parquet` | 군더더기 — 확장자가 포맷 단일결정, parquet 직독은 hfProxy `/hf/` 가 이미 줌 |
| `freq` OHLCV-aware 집계(o=first/h=max/…) | MVP=last-of-period 단일 규칙, 가격 특례 후속 |
| CSV 본문 주석행 truncated 신호 | IMPORTDATA 가 데이터로 파싱·오염 → HTTP 헤더 전용 |

## 성공 기준

- **추측가능** — `dart/finance/005930.parquet` 아는 사람이 docs 0으로 `.tsv` URL 을 맞힌다.
- **자동확장** — 새 public 카테고리가 `DATA_RELEASES` 한 줄로 양 티어 자동 노출, 새 private 은 미포함 자동 차단(404).
- **silent 절단 0** — cap 시 항상 HTTP 헤더 신호 + 넓히는 파라미터 안내.
- **한글 무깨짐** — UTF-8 BOM + en-US invariant 숫자로 한국 Excel·Sheets 정상.
- **도구 한도 안** — "첫 추측이 이미 가볍다"(셀cap·cols·tail·freq).
- **'라이브'≠실시간 셀함수** — 도구별 신선도(Sheets ~1h, Excel 새로고침) 기대관리 카피 동반.

## 개발자 평가 (비판적)

load-bearing 사실 전부 코드 재검증: hfProxy 워커는 순수 fetch(parquet 디코드 0, `worker.js:19`)라 Tier2 의 hyparquet 디코드는 *최대 비용 신규* — "형제 라우트 0줄 재사용"은 거짓, 재사용은 retry/CORS/path정규화뿐. `filter` 는 진짜 pushdown 아님(`request.ts:33-34`). private dir 6종(`allFilings`·`edgarScan`·`stemIndex`·`edinet`·`edinetDocs`·`aiKnowledge`)은 `repo` override 가 없어 **공개 dartlab-data 와 같은 repo** — 토큰 물리차단이 안 먹으므로 코드 allowlist 가 유일 방어. 이 셋이 PRD 의 척추 제약이다.

## PM 평가 (비판적)

운영자 실용주의(Tier1 우선·MVP·덕지덕지 거부)를 일관 반영. 11 killList 가 범위 재팽창을 막는 핵심 자산이다. Tier1 이 백엔드 0으로 즉시 가치를 내고, Tier2 는 CF 비용·한도 실측 게이트(CLAUDE.md 런타임-불가 실측→승인 규칙) 뒤로 정직하게 분리됐다. 공개 surface 라 push 는 스크린샷 눈검수 + 운영자 명시 승인. **결론: MVP=Tier1+flat Tier2 로 승인, 날짜샤드·wide·pagination 부풀림은 거부.**
