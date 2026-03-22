# 086_auditTechniques — 세계적 감사 기법 적용

## 요약

PCAOB, ISA 570, SOX, Benford's Law 등 세계적 감사 기법을
dartlab 부실 예측 엔진에 적용. 기존 8개 탐지기 → 11개로 확장.
감사 데이터의 10% 미만만 활용하던 것을 전면 활용.

## 실험 현황

| # | 파일 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 001 | benfordLaw | **완료** | 대수정규 χ²=5.08 (PASS), 균등분포 χ²=224.99 (위반 탐지 PASS) |
| 002 | auditRedFlags | **완료** | 5개 프로필 전체 PASS. 정상→0건, 빈번교체→danger, 종합위험→5건 |
| 003 | revenueQuality | **완료** | 4개 프로필 전체 PASS. 건전→0건, OCF적자→danger, 연속하락→warning |

## 엔진 흡수

- `engines/analysis/insight/anomaly.py` — 3개 탐지기 추가 (auditRedFlags, benford, revenueQuality)
- `engines/analysis/insight/types.py` — AuditDataForAnomaly DTO 추가
- `engines/analysis/insight/grading.py` — analyzeGovernance 확장 (감사인안정성, 내부통제, 감사위원회)
- `engines/analysis/insight/distress.py` — 감사 축 ModelScore + _interpretAuditRedFlags 추가
- `engines/analysis/insight/spec.py` — 탐지기 3개 등록 (11개 총)
- `engines/analysis/insight/pipeline.py` — _extractAuditData + auditData 전달 경로
- `engines/analysis/insight/__init__.py` — AuditDataForAnomaly export

## 학술 근거

| 기법 | 근거 |
|------|------|
| Benford's Law | Nigrini (1996), AICPA 공식 감사 절차 |
| 감사인 교체 | PCAOB AS 3101 |
| 계속기업 | ISA 570, Geiger & Raghunandan (2002) |
| 내부통제 | SOX 302/404, PCAOB AS 2201 |
| KAM | ISA 701 |
| Revenue Quality | Dechow & Dichev (2002) |
