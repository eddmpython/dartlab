"""macro 엔진 메타데이터 — generateSpec.py 연동."""

from __future__ import annotations

SPEC = {
    "engine": "macro",
    "layer": "L2",
    "description": "시장 레벨 매크로 경제 분석. Company 불필요. 11축 + 40개 투자전략.",
    "entrypoint": "dartlab.macro()",
    "axes": {
        "cycle": {
            "label": "사이클",
            "description": "경제 사이클 4국면 판별 + 전환 시퀀스 감지",
            "when": "투자 의사결정의 출발점. 자산배분의 기본 뼈대",
            "key_output": "phase (expansion/slowdown/contraction/recovery)",
        },
        "rates": {
            "label": "금리",
            "description": "금리 방향 + 고용/물가 + DKW분해 + BEI/실질금리",
            "when": "금리 방향이 바뀌면 모든 자산 가격이 바뀐다",
            "key_output": "outlook.direction (cut/hold/hike)",
        },
        "assets": {
            "label": "자산",
            "description": "5대 자산 + 금 3요인 + Cu/Au ratio + BEI 4분면",
            "when": "자산 가격 자체가 경제의 투표",
            "key_output": "goldDrivers, copperGold, vixRegime",
        },
        "sentiment": {
            "label": "심리",
            "description": "공포탐욕 0-100 + ISM 자산배분 바로미터",
            "when": "극단적 심리는 역방향 신호",
            "key_output": "fearGreed.score (<25 매수, >75 경계)",
        },
        "liquidity": {
            "label": "유동성",
            "description": "M2 + 연준 B/S + 신용스프레드 + NFCI + 자체 FCI",
            "when": "유동성이 자산 가격의 최종 결정자",
            "key_output": "regime, nfci, fci",
        },
        "forecast": {
            "label": "예측",
            "description": "LEI + 침체확률 + Sahm Rule + Hamilton RS + GDP Nowcast",
            "when": "앞으로 어디로 가는가. 침체 확률을 정량화",
            "key_output": "recessionProb.probability, hamiltonRegime, nowcast",
        },
        "crisis": {
            "label": "위기",
            "description": "Credit-to-GDP gap + GHS + Minsky 5단계 + Koo BSR + Fisher",
            "when": "구조적 금융 불균형 감지. 사이클이 아닌 위기",
            "key_output": "creditGap.gap, minskyPhase, kooRecession.isBSR",
        },
        "inventory": {
            "label": "재고",
            "description": "ISM 재고순환 4국면 + 자산배분 바로미터",
            "when": "경기 전환의 가장 빠른 신호",
            "key_output": "inventoryPhase.phase, ismBarometer.rateImplication",
        },
        "corporate": {
            "label": "기업집계",
            "description": "전종목 이익사이클 + Ponzi비율 + 레버리지",
            "when": "거시경제는 결국 기업의 합. bottom-up 증거",
            "key_output": "earningsCycle, ponziRatio.currentRatio",
        },
        "trade": {
            "label": "교역",
            "description": "교역조건 + 대용치 + 수출이익 선행 (KR 전용)",
            "when": "한국 GDP 40%+ 수출. 교역조건이 최선행 지표",
            "key_output": "termsOfTrade, totProxy, exportProfit",
        },
        "summary": {
            "label": "종합",
            "description": "10축 종합 + 40전략 + 포트폴리오 매핑",
            "when": "전체 그림을 한 번에. 축별 기여도 + 자산배분 포함",
            "key_output": "overall, score, contributions, allocation, strategies",
        },
    },
    "markets": ["US", "KR"],
    "dataSources": {
        "FRED": "미국 경제 ~77개 시리즈",
        "ECOS": "한국 경제 ~53개 지표",
        "scan_parquet": "DART/EDGAR 전종목 재무제표 (기업집계용)",
    },
    "methods": {
        "Hamilton RS": "Hamilton(1989) — numpy EM+Kim smoother. 2-regime Markov Switching",
        "GDP Nowcasting": "Banbura(2011) — numpy Kalman+EM. Dynamic Factor Model",
        "Nelson-Siegel": "NS(1987) — numpy grid λ + OLS. 수익률곡선 Level/Slope/Curvature",
        "Cleveland Fed": "Estrella-Mishkin(1996) — 10Y-3M → Φ(α+βx) 침체확률",
        "Sahm Rule": "Sahm(2019) — 실업률 3M MA - 12M 최저. ≥0.5%p 침체",
        "BIS Credit Gap": "Borio-Drehmann(2014) — 단측 HP λ=400k. Basel III CCyB",
        "GHS Crisis": "Greenwood-Hanson-Shleifer(2022 JoF) — 3Y 신용+자산 → 위기확률",
        "Minsky": "Kindleberger-Minsky — 5단계 금융불안정 (displacement→revulsion)",
        "Koo BSR": "Koo(2009) — 민간 금융잉여 + 저금리 = 대차대조표 침체",
        "Fisher": "Fisher(1933) — DSR+CPI+NPL 부채디플레이션 악순환",
        "Cu/Au Ratio": "실증 — 구리(산업)/금(안전자산) 비율. 10Y 수익률 선행",
        "FCI": "Hatzius(2010) — 5변수 z-score 금융환경지수 (US+KR)",
    },
    "features": {
        "scenario": "overrides 파라미터 — 전체 11축 시나리오 시뮬레이션",
        "backtest": "as_of 파라미터 — 전체 11축 과거 시점 재현",
        "walkForward": "walkForwardBacktest() — NBER 침체 기준 precision/recall",
        "allocation": "regimeToAllocation() — regime×phase → 주식/채권/금/현금 %",
        "strategies40": "evaluateStrategies() — 40개 투자전략 활성/방향/강도/신뢰도",
    },
}
