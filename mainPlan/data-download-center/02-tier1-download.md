# 02 · Tier 1 — 브라우저 parquet 직독 다운로드 (백엔드 0)

> 진짜 MVP 척추. 신규 작성기 0 — 전부 재사용. 운영자 "Tier1 우선" 정합.

## 정신

브라우저가 HF parquet 를 직접 range-fetch 해서 메모리에서 xlsx/CSV 로 변환·다운로드한다. **서버·API·CSV 사본 0**. 노출 dir 전부의 모든 파일을 대상으로 하며(날짜샤드 포함), 로컬 메모리라 **cap 없음**.

## 재사용 자산 (실재 — 신규 0)

| 자산 | 위치 | 용도 |
|---|---|---|
| `requestParquetRows` (`columns`/`filter`/`rowStart`/`rowEnd`) | `ui/packages/runtime/src/data/fetch/request.ts` | parquet 직독 + pushdown(컬럼·행범위) |
| `requestParquetWholeFile` | 동상 | 소형 통파일 직독(404→null) |
| `buildWorkbook(sheets)` → `Uint8Array` | `ui/packages/surfaces/src/viewer/lib/xlsx/buildWorkbook.ts` | 진짜 OOXML `.xlsx`(병합·Number coerce·honest-gap) |
| `toCsv(rows)` (BOM) | `ui/packages/surfaces/src/scan/csvExport.ts` + viewer `lib/dataExport.ts` | BOM CSV |
| `downloadBlob`/`downloadText` | viewer `lib/dataExport.ts` | 다운로드 트리거 |
| origins 레지스트리(`hf`/`hfRange`) | `ui/packages/runtime/src/data/origins/registry.ts` | HF URL 해소 SSOT |

**table-export writer 침범 0** — `buildWorkbook` 를 *읽어 호출*만 한다. ExportPort 계약(`ui/packages/contracts/src/export.ts`) 위에 새 surface 를 얹는다.

## 흐름

```
사용자: 카탈로그(/v1/index.json) → dir 선택 → id(회사·시리즈) 입력 → cols/freq 옵션
  → requestParquetRows(path={dir}/{id}.parquet, columns, rowStart/rowEnd)
  → (선택) freq 리샘플 last-of-period
  → buildWorkbook([{label, grid}]) → .xlsx   또는   toCsv(rows) → BOM CSV
  → downloadBlob / downloadText
```

- 숫자는 `coerceCell` 이 진짜 Number 로(콤마·괄호음수·△ 정규화) → 엑셀 수식 즉시 작동. 결손 빈셀.
- 큰 표도 로컬에서 감당 — `.xlsx` 는 STORE/Deflate ZIP 이라 텍스트 압축. 날짜샤드처럼 거대한 건 `cols`+`rowStart/rowEnd` 슬라이스 후 변환 권장.

## 링크빌더 UX (사실상 필수)

데이터 센터 surface 가 `/v1/index.json` 을 읽어 **dir → id → cols → freq** 를 고르게 한다. 동시에:

- **Tier 1 다운로드 버튼**(`.xlsx`/`.csv`) — 위 흐름.
- **Tier 2 라이브 URL** — 같은 선택으로 `=IMPORTDATA(...)` / Power Query URL 스니펫 생성·복사.
- **셀수 미리계산** — 받을 행×열, 전체 행수, 셀cap 초과 시 넓히는 파라미터를 화면에 표시(IMPORTDATA 가 HTTP 헤더 신호를 못 보는 한계를 surface 가 메움).

즉 링크빌더 한 화면에서 "다운로드"와 "라이브 링크"가 같은 슬라이스 선택을 공유한다.

## 위치·졸업

- 라우트 = `landing/src/routes/data/+page.svelte`(`/data` 승격 완료, 옛 lab/data-center).
- 졸업 = 운영자 "승격해라" 지시로 `/data` 승격 완료(`693d228be`). → [05](05-validation-and-rollback.md).

## SSOT 청결

- 모든 데이터 호출은 origins 레지스트리(`hf`/`hfRange`) 경유 — 직접 URL 조립·자체 캐시 Map 금지(`tests/audit/checkUiDataWiring` 준수).
- ⚠ 주의: 현 viewer `DataDownloadMenu` 와 `panelLoad.ts` 는 raw `hfUrl` passthrough 부채(TKT-EXP-1/2)가 있다 — **새 surface 는 그 패턴을 채택·복제하지 않는다**. `requestParquetRows`(레지스트리 경유)로만 읽어 부채를 *해소하며* 짓는다.
