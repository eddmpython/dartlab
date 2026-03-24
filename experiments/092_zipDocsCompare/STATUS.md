# 092 — ZIP 원본 vs Collector 결과물 비교

## 목적

OpenDART `document.xml` API로 받은 ZIP 원본에서 현재 docs parquet 스키마를 재현할 수 있는지 확인.
성공하면 Company가 API 키 보유 시 직접 수집/갱신할 수 있는 투채널 구조의 근거가 된다.

## 실험 목록

| # | 파일 | 목적 | 상태 |
|---|------|------|------|
| 001 | zipStructure.py | ZIP 내부 구조 확인 | 완료 |
| 002 | xmlSectionParse.py | XML 내부 SECTION 태그 구조 파악 | 완료 |
| 003 | zipToParquetSchema.py | SECTION-1만 추출 (정규식 한계 확인) | 완료 |
| 004 | fullSectionParse.py | lxml으로 전체 SECTION 재귀 순회 (content 0자 문제 발견) | 완료 |
| 005 | contentExtract.py | content 추출 수정 + collector와 최종 비교 | 완료 |
| 006 | crossEraCompare.py | 시점/유형별 ZIP vs collector 완전 일치 비교 | 완료 |
| 007 | saveCompare.py | 동일 스키마 parquet 저장 + 눈으로 비교 | 완료 |
| 008 | sectionsQuality.py | section_content 질적 비교 (블록/heading/table) | 완료 |
| 009 | fullZipCollect.py | 2016~최신 40건 전체 ZIP 수집 | 완료 |
| 010 | sectionsCompare.py | sections 파이프라인 결과 비교 (topic×period) | 완료 |
| 011 | improvedXmlToText.py | XML→텍스트 변환 개선 (table-group 경계 + SPAN bold 줄바꿈) | 완료 |

## 핵심 결과

### Phase 1: ZIP 구조 + 기본 비교 (001-006)

- ZIP 안에 3개 XML: 본체(8MB) + 감사보고서 + 연결감사보고서
- `SECTION-1` > `SECTION-2` > `SECTION-3` 중첩 구조로 섹션 완벽 분리
- 모든 보고서(2015~2025)에 동일 구조 존재
- ZIP이 collector보다 더 완전한 섹션 포함 (공시내용변경, 전문가확인 등)

### Phase 2: Parquet + Sections 비교 (007-010)

- raw parquet 스키마: 10개 컬럼 완벽 재현 가능 (section_url만 빈 문자열)
- 소분류 content 유사도: 91.2% (줄바꿈/공백 미세 차이)
- sections 행 수: collector 8,599 vs ZIP_v1 15,047 (ZIP이 2배)
- 원인: ZIP의 `<table-group>` 내부에서 heading이 table에 묻혀 블록 분리 실패

### Phase 3: XML→텍스트 변환 개선 (011)

3가지 핵심 개선:
1. **table-group 경계 분리**: `<table-group>` 내 `<title>`을 text paragraph로 분리
2. **SECTION-1 title 포함**: 대분류 content 시작에 제목 텍스트 포함 (collector 동일 동작)
3. **SPAN bold 줄바꿈**: `<SPAN USERMARK="F-BT14 B">` 뒤에 줄바꿈 삽입

결과:
- 블록 분해: **완전 동일** (연결재무제표 주석 66=66, III장 211=211)
- 같은 보고서 fsSummary segmentKey 공통율: **91.3%** (v1 대비 +10.4%p)
- 텍스트 볼륨: collector 67.8M자 vs ZIP 68.4M자 (**+0.9%**)
- 2025 기간 채움: collector 1,633 vs ZIP 1,527 (diff -106, **-6.5%**)
- 2025 topic별 텍스트 볼륨: **±0.5% 이내** (대부분 ≤0.2%)

### 행 수 차이 잔여 원인

- sections 행: collector 8,599 vs ZIP_v2 14,515
- 주 원인: 대분류 content에 하위 전체 포함 → 동일 topic에서 대분류+소분류 이중 decompose
- 기간 간 segmentKey 일관성: collector HTML > ZIP XML (미세 줄바꿈 차이 누적)
- fsSummary +2,071, consolidatedNotes +1,165, financialNotes +1,334 (이 3개가 77%)

## 최종 결론

**ZIP 기반 수집기는 실현 가능하다.**

| 기준 | collector | ZIP_v2 | 판정 |
|------|-----------|--------|------|
| 텍스트 품질 | 기준 | ±0.2% | **동등** |
| 블록 분해 | 기준 | 완전 동일 | **동등** |
| 텍스트 볼륨 | 67.8M자 | 68.4M자 | **ZIP +0.9%** |
| 섹션 완전성 | 47개 | 51개 | **ZIP 우위** |
| 수집 속도 | 느림(크롤링) | 198초/40건 | **ZIP 우위** |
| 기간 채움률 | 기준 | -6.5% | collector 우위 |
| sections 행 수 | 8,599 | 14,515 | collector 효율적 |

처리 규칙 (확정):
1. SECTION-1: `_getFullContentV2` (하위 전체 포함 + 자기 title 포함)
2. SECTION-2: `_getOwnContentV2` (자기만, 하위 section 제외)
3. SECTION-3: 건너뜀 (collector와 동일)
4. `_xmlToTextV2`: table-group 경계 분리 + SPAN bold 줄바꿈
5. 【대표이사확인】, 【전문가확인】, 공시변경사항: 포함 (collector에 없던 추가 이점)
