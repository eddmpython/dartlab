# ipo-prospectus-summary

GitHub Discussion #70 — IPO 공모 신고서 분석(증권신고서 지분증권 6카테고리 구조화 + 원문근거).

- **[00-prd.md](00-prd.md)** — 전문가 토론 + 실측 + 5렌즈 우수성 평가 박제(v2). 결론·실측·D1-D5·phasing·운영자 결정 6건·스코어카드.

## 한 줄 요약
새 엔진 신설 없이 3곳 분산(providers 단건파서 `securitiesRegistration.py` · scan 횡단 `scan("ipo")` · story builder L3). 런타임-SSOT(allFilings content_raw) 직독 기본. `tests/_attempts/ipo/` 졸업 후 본진(order-flow-scan 동형).

## 실측 핵심
- 데이터 풍부(9개월 531건, 단일 XML, 6섹션 앵커 전부 검출). 테이블 구조파싱 필요(flat regex 실패).
- ★ **`corp_cls=="E" + stock_code==""` = 신규상장 IPO 기계 ground-truth**(사람 라벨 불필요). corp_cls Y/K(stock_code 보유)는 유상증자/DR — SK하이닉스·계양전기 자동 비-IPO. (우수성 평가가 인정한 유일한 "증명된 진짜 혁신".)

## 우수성 평가 (v1→v2)
- 스코어카드: 엔진혁신 66 · 속도성능 61 · 프로덕트시장 61 · UI/UX 52(최약) · 운영(평가 누락).
- ★치명결함 1건 정정: v1이 P4 블로커로 박은 "buildReportModel emitter 미존재"는 거짓 — `story/report.py:161`에 실재(044daf6dd), professional-report-engine P2 진행 중. 직접 검증 후 정정.
- v2 반영: 제품·시장 정의 + 이름 정정(수요예측 결과변수=카테고리7 후속트랙) · IPO 4대 시각 primitive · P2 카테고리별 항등식 truth 프레임워크 · 성능 척추(index-first·시의성 SLA) · 원문근거 deep-link.

## 상태
기획 확정·미착수(v2). 운영자 결정 6건 대기. professional-report-engine·order-flow-scan 동급 활성.
