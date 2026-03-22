# 081_scanAxes — scan 축 확장 실험

## 목표
- `signal`을 공식 scan 축으로 승격할 근거를 재검증한다
- `financing`을 신규 scan 축 후보로 검토하기 위해 coverage → feature extraction → classifier draft → cross validation 순으로 실험한다
- promotion gate를 수치로 판정한다

## 실험 목록

| # | 파일 | 주제 | 상태 | 핵심 결과 |
|---|------|------|------|-----------|
| 001 | financingCoverage | financing coverage | ✅ 완료 | 1,634사 usable coverage, capital universe 대비 61.5% |
| 002 | financingFeatures | feature extraction | ✅ 완료 | 사용근거 1,159 / 불일치 694 / 희석신호 1,291 |
| 003 | financingClassifier | classifier draft | ✅ 완료 | 불일치주의형 694, 최다 class 42.5% |
| 004 | financingCrossValidation | cross validation | ✅ 완료 | capital 최근증자 false인데 usage evidence true 328사, 수동 sample 10/10 설명 가능 |

## gate 판정

### signal
- 별도 재검증 실험: `experiments/076_marketLab/013_signalRevalidation.py`
- docs coverage 319사
- 시계열 1999~2026
- 대표 키워드 3개(AI, ESG, 2차전지) 모두 변곡 재현
- 판정: 통과

### financing
- usable coverage 1,634사 -> 1,500사 이상 + capital universe 2,655사 대비 61.5%
- 단일 class 최다 비중 42.5% -> 85% 미만
- capital/debt 추가 설명력:
  - capital `최근증자=False`인데 financing `사용근거=True` 328사
  - capital `중립`, debt `안전` 내부에서도 다섯 class로 분해
- explainability:
  - 분류별 2개씩 총 10개 sample 모두 raw column으로 설명 가능
- 판정: gate 충족, 엔진 승격 후보로 유지

## 결론
- 이번 배치에서 `signal`은 공식 scan 축으로 취급 가능하다
- `financing`은 실험 gate를 충족했지만, 아직 엔진/API 승격은 보류한다
- 따라서 `anomaly` 대체 트랙은 이번 세션에서 발동하지 않는다
