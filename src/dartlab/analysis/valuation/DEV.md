# Valuation — 멀티소스 밸류에이션 합성

## 구조

```
valuation/
├── analyst.py       # Analyst 클래스 (public API) + forecast/simulation/valuation re-export
├── synthesizer.py   # DCF + consensus + peer → 목표가 + 투자의견
├── calibrator.py    # 모델 보정 (과거 예측 정확도 기반)
├── valuation.py     # DCF, DDM, 상대가치, 종합 밸류에이션
├── pricetarget.py   # 목표주가 합성 (core/finance에서 이전)
└── types.py         # AnalystReport, ValuationMethod
```

## 핵심 설계

- **3소스 합성**: DCF(내재가치) + 컨센서스(시장 전망) + Peer(상대가치)
- **가중 평균**: 각 소스의 신뢰도에 따라 동적 가중
- **보정**: 과거 예측 대비 실적으로 모델 편향 보정

## 의존성

- `dartlab.gather` — 시장 데이터 (주가, 컨센서스)
- `dartlab.core.finance` — 재무 유틸 (비율, 추출)
- **절대 import 사용**: `from dartlab.gather import ...`

## Company 부착

- 별도 `Analyst()` 클래스로 사용 (Company property 아님)
- `Analyst()` → `.report(company)` → AnalystReport

## 안정성

- Tier 2 (Beta): gather 데이터 가용성에 의존
