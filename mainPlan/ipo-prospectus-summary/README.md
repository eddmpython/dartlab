# ipo-prospectus-summary

GitHub Discussion #70 — IPO 공모 신고서 분석(증권신고서 지분증권 6카테고리 구조화 + 원문근거).

- **[00-prd.md](00-prd.md)** — 전문가 토론 + 실측 + 5렌즈 우수성 평가 박제(v2). 결론·실측·D1-D5·phasing·운영자 결정 6건·스코어카드.

## 한 줄 요약
새 엔진 신설 없이 3곳 분산(providers 단건파서 `securitiesRegistration.py` · scan 횡단 `scan("ipo")` · story builder L3). 런타임-SSOT(allFilings content_raw) 직독 기본. `tests/_attempts/ipo/` 졸업 후 본진(order-flow-scan 동형).

## 실측 핵심
- 데이터 풍부(단일 XML, dart4.xsd `<TITLE>` 구조앵커). 테이블 구조파싱 필요(flat regex 실패).
- ★ **ground-truth = 3조건 `지분증권 subtype + corp_cls=="E" + stock_code==""`**(개념확립 정정 2026-06-29). 2조건(`E+sc=''`)만은 과대 — corp_cls=E 826건 중 783건이 펀드·채권·유동화. 정정 후 지분증권 43 전수 오분류 0. corp_cls Y/K는 상장사 유상증자. (판별 혁신 유효 — 3조건 형태.)
- 개념확립 완료(발행사 7곳 교차): P0 ✅ · P1 ✅(FULL 7곳 100%, 채무증권 negative=발행공시 클래스 공통) · P2 ✅ cat1·2·3·5·6 일반화+항등식 — **cat3 밸류 이중 항등식 6/6 real IPO EXACT(하드케이스 돌파, PER 10~47x 좌표화)**·cat5 자산=부채+자본 6/6. 잔여=cat4 보호예수·확정공모가 트랙. 상세 `tests/_attempts/ipo/README.md`, 정정 `00-prd.md §1 정정 1-b·P2`.

## 우수성 평가 (v1→v2)
- 스코어카드: 엔진혁신 66 · 속도성능 61 · 프로덕트시장 61 · UI/UX 52(최약) · 운영(평가 누락).
- ★치명결함 1건 정정: v1이 P4 블로커로 박은 "buildReportModel emitter 미존재"는 거짓 — `story/report.py:161`에 실재(044daf6dd), professional-report-engine P2 진행 중. 직접 검증 후 정정.
- v2 반영: 제품·시장 정의 + 이름 정정(수요예측 결과변수=카테고리7 후속트랙) · IPO 4대 시각 primitive · P2 카테고리별 항등식 truth 프레임워크 · 성능 척추(index-first·시의성 SLA) · 원문근거 deep-link.

## 상태
**구현 완료(2026-07-03)**: 본진 졸업(providers 파서 + scan("ipo") + story 리포트) + 로컬 런타임 서빙(`/api/dart/ipo/{report,scan}`, 베이크 0) + **터미널 IPO 공모 뷰**(IpoPort 계약·라이브 워커 `/ipo-filings` 발굴 공통배선·로컬 6카테고리 리포트 pane·`?ipo=1` 딥링크=왓처 newIpo 푸시 목적지). 실렌더 눈검수: 발굴 9개 발행사·확정가/정정 뱃지·에이치엘지노믹스 리포트(EV/EBITDA 이종기준 가드 포함).
운영자 잔여 2건: ① hfProxy 재배포(`wrangler deploy`, /ipo-filings 활성) ② landing/ui 커밋 눈검수 후 push.
