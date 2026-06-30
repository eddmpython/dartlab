# 05 · 검증 · 롤백

## 1. 보안 회귀 가드 (핵심 — same-repo private 차단)

private dir 6종(`allFilings` · `edgar/scan` · `stemIndex` · `edinet` · `edinetDocs` · `aiKnowledge`)은 공개 `dartlab-data` 와 **같은 repo**라(→ [03](03-tier2-live-worker.md)) 토큰 차단이 안 먹는다. 따라서 코드 게이트의 404 강제를 *반드시 테스트로 박는다*:

- `GET /v1/dart/allFilings/…` · `/v1/edgar/scan/…` · `/v1/dart/stemIndex/…` · `/v1/edinet/…` · `/v1/ai/knowledge/…` · `/v1/original/…` → **전부 404**(존재 누설 0, private/미존재 응답 동일).
- `schema.json` 프로브도 동일 allowlist 게이트 통과(private 스키마 footer 누설 0).
- path 주입: `..` · 절대 URL · 비정규 `{id}` → 거부.
- **무게이트 `/hf` passthrough 복제 0** 확인(hfProxy 패턴을 그대로 복사하지 않았는지).

## 2. drift 가드 (blocking 권장)

`tests/audit/csvWorkerAllowlist`(가칭):

- Python `DATA_RELEASES` 의 `public` 플래그·표형 화이트리스트 ↔ 워커 emit 상수 동기화(drift 0).
- 새 public 카테고리 추가 시 화이트리스트 자동 반영 검증, 새 private 은 미포함 자동 차단 검증.
- `noScriptsDir` 처럼 **PR 차단(blocking)** — 보안 경계 SSOT 라 경고로 두지 않는다(운영자 결정 → [06](06-progress-ledger.md)).

## 3. Tier 2 CF 한도 실측 (push 전 게이트)

- 회사파일(예 `dart/finance/005930` · `macro/fred/DGS10` · `gov/prices/company/005930`) parquet 디코드 → CSV 변환이 CF 128MB/CPU 안에 드는지 실측. 무료(10ms CPU)/유료(50ms~30s) 비용 결과를 운영자에 보고 후 착수.
- 날짜샤드(`gov/prices/date/{year}`) URL → **413** + `tier1Url` 반환 확인(변환 시도 0).
- CLAUDE.md 런타임-불가 실측→승인 규칙 정합 — 실측 근거 없이 Tier2 워커 배포 금지.

## 4. 포맷·정합 검증

- **한글** — UTF-8 BOM 선두로 Excel·Sheets 에서 한글 컬럼·값 무깨짐.
- **숫자** — en-US invariant(점 소수·구분자 0) → `=SUM()` 등 수식 즉시 작동. 콤마 끼면 텍스트화 → 실패.
- **honest-gap** — 결손은 빈 셀, 0 대체 0(`buildWorkbook` null→`''` 규약 일치).
- **TSV/CSV** — 탭/RFC4180 인용 정확(`csvExport.ts escapeCell` 거울).
- **cap 신호** — 셀cap 초과 시 `X-DartLab-Capped`/`Total-Rows`/`Cells-Returned`/`Hint` 헤더 존재, 본문 주석행 0.

## 5. 실소비 눈검수 (공개 surface)

- Google Sheets 새 시트 → `=IMPORTDATA(…csv?tail=250&cols=…)` → 격자 정상·숫자 Number·한글 정상 스크린샷.
- Excel → 데이터→웹에서 `…tsv` → Power Query 표 로드·새로고침 스크린샷.
- Tier1 `.xlsx` 다운로드 → 열어서 수식(`=SUM`) 작동 스크린샷.
- 링크빌더 셀수 미리계산이 실제 응답과 일치.
- **푸시 전 스크린샷 전수 눈검수** — 정량 PASS 가 디자인 디테일을 못 본다(feedback_ui_rules). 공개 UI 변경은 **운영자 명시 push 승인** 후에만(자동 push 금지).

## 6. 롤백

- **Tier 2** — `VITE_DARTLAB_CSV_PROXY` env 제거 → `csvWorker.configured()=false` → Tier2 비활성, **Tier1 만 무중단**. 워커 자체는 정적 자산이라 트래픽 0이면 비용 0.
- **Tier 1** — `/data` 라우트(승격 완료, 옛 /lab/data-center). 회귀 시 git revert 로 라우트 롤백.
- **SSOT 무손상** — 어느 티어도 HF 에 사본을 굽지 않으므로 롤백 시 정리할 산출물 0.
